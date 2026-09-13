"""Create (or refresh) a Zenodo DRAFT deposition from deposit_v1.0.0/ and upload its files.

Never publishes.  Publishing is a click on the Zenodo record page, by the owner, after reading the draft.

Token: read from the environment, never from a file in the repository.
    ZENODO_SANDBOX_TOKEN   used by default            (https://sandbox.zenodo.org, throwaway DOIs)
    ZENODO_TOKEN           used only with --production (https://zenodo.org, real DOIs on publish)
Make the token at  <host>/account/settings/applications/tokens/new/  with scopes deposit:write and deposit:actions.

Usage:
    python zenodo_upload.py                     sandbox: new draft, upload everything, print URL + reserved DOI
    python zenodo_upload.py --dry-run           list what would be sent, touch nothing
    python zenodo_upload.py --deposition 12345  reuse an existing draft: replace files of the same name, update metadata
    python zenodo_upload.py --production        same on zenodo.org (asks for a typed confirmation)

Every uploaded file is verified against Zenodo's returned MD5 before the script moves on.
When Zenodo is slow or shedding load (403/429/5xx, timeouts) each call waits and retries, up to about 16 minutes
per call; re-running with --deposition <id> resumes, skipping files whose checksum already matches.
"""
import argparse, hashlib, io, json, os, sys, time

try:
    import requests
except ImportError:
    sys.exit('pip install requests')

HERE = os.path.dirname(os.path.abspath(__file__))
DEPOSIT = os.path.join(os.path.dirname(HERE), 'deposit_v1.0.0')
SKIP = {'MANIFEST_sha256.txt'}          # regenerated from the uploaded checksums; the manifest travels inside the README instead


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--production', action='store_true', help='zenodo.org instead of the sandbox')
    ap.add_argument('--deposition', type=int, help='existing draft deposition id to refresh')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    host = 'https://zenodo.org' if a.production else 'https://sandbox.zenodo.org'
    tok = os.environ.get('ZENODO_TOKEN' if a.production else 'ZENODO_SANDBOX_TOKEN')
    meta = json.load(io.open(os.path.join(DEPOSIT, '.zenodo.json'), encoding='utf-8'))
    meta['prereserve_doi'] = True
    files = sorted(f for f in os.listdir(DEPOSIT) if f not in SKIP and not f.startswith('.'))
    total = sum(os.path.getsize(os.path.join(DEPOSIT, f)) for f in files)
    print('deposit : %s\nhost    : %s\nfiles   : %d, %.1f MB\ntitle   : %s' % (DEPOSIT, host, len(files), total / 1e6, meta['title']))
    for f in files:
        print('   %8.1f MB  %s' % (os.path.getsize(os.path.join(DEPOSIT, f)) / 1e6, f))
    if a.dry_run:
        print('\n--dry-run: nothing sent.'); return
    if not tok:
        sys.exit('\nno token in the environment (%s). Nothing sent.' % ('ZENODO_TOKEN' if a.production else 'ZENODO_SANDBOX_TOKEN'))
    if a.production:
        if input('\nThis creates a DRAFT on zenodo.org (not published). Type  draft  to continue: ').strip() != 'draft':
            sys.exit('aborted')

    s = requests.Session(); s.headers['Authorization'] = 'Bearer ' + tok
    s.headers['User-Agent'] = 'kuppam-deposit-uploader/1.0 (python-requests)'
    api = host + '/api/deposit/depositions'
    WAIT = (10, 30, 60, 120, 240, 480)          # seconds between attempts when Zenodo is slow or shedding load

    def call(method, url, **kw):
        """one API call with patient retries on 403/429/5xx and on timeouts; a file body is reopened per attempt"""
        body = kw.pop('body', None)
        for i, w in enumerate(WAIT + (None,)):
            try:
                if body: kw['data'] = open(body, 'rb')
                r = s.request(method, url, timeout=600, **kw)
                if body: kw['data'].close()
                if r.status_code not in (403, 429, 500, 502, 503, 504): return r
                why = 'HTTP %d' % r.status_code
            except (requests.ConnectionError, requests.Timeout) as e:
                why = type(e).__name__
            if w is None: sys.exit('gave up on %s %s after %d attempts (%s)' % (method, url, len(WAIT) + 1, why))
            print('   %s on %s %s; waiting %d s before attempt %d' % (why, method, url.split('/api/')[-1][:50], w, i + 2)); time.sleep(w)

    if a.deposition:
        r = call('GET', '%s/%d' % (api, a.deposition)); r.raise_for_status(); dep = r.json()
        if dep.get('submitted'):
            sys.exit('deposition %d is already published; a new version needs the web UI ("New version") first.' % a.deposition)
        print('\nrefreshing draft %d' % a.deposition)
    else:
        r = call('POST', api, json={}); r.raise_for_status(); dep = r.json()
        print('\ncreated draft %d' % dep['id'])

    # metadata
    r = call('PUT', '%s/%d' % (api, dep['id']), json={'metadata': meta})
    if r.status_code >= 400:
        print('metadata rejected:', r.status_code, r.text[:2000]); sys.exit(1)
    dep = r.json()
    bucket = dep['links']['bucket']

    # files: replace by name
    existing = {f['filename']: f for f in call('GET', '%s/%d/files' % (api, dep['id'])).json()}
    for f in files:
        p = os.path.join(DEPOSIT, f); local = md5(p)
        if f in existing:
            if existing[f].get('checksum', '').replace('md5:', '') == local:
                print('   unchanged  %s' % f); continue
            call('DELETE', existing[f]['links']['self']).raise_for_status()
        t0 = time.time()
        r = call('PUT', '%s/%s' % (bucket, f), body=p)
        if r.status_code >= 400:
            print('upload failed:', f, r.status_code, r.text[:500]); sys.exit(1)
        remote = r.json().get('checksum', '').replace('md5:', '')
        ok = remote == local
        print('   %s  %-40s %7.1f MB  %5.0f s  md5 %s' % ('ok ' if ok else 'BAD', f, os.path.getsize(p) / 1e6, time.time() - t0, remote[:12]))
        if not ok:
            sys.exit('checksum mismatch on %s: local %s, zenodo %s' % (f, local, remote))

    dep = call('GET', '%s/%d' % (api, dep['id'])).json()
    doi = dep.get('metadata', {}).get('prereserve_doi', {}).get('doi', '(none reserved)')
    print('\nDRAFT ready, not published.\n  edit/preview : %s\n  reserved DOI : %s\n' % (dep['links'].get('html', host + '/deposit/%d' % dep['id']), doi))
    print('Publish from that page after reading it. Nothing here publishes.')


if __name__ == '__main__':
    main()
