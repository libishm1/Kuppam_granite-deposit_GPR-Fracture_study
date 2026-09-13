"""Create (or refresh) a figshare DRAFT dataset from deposit_v1.0.0/, reserve its DOI and upload the files.

Publishing is a separate, explicit step (--publish, typed confirmation), off by default: read the private
link first.  Metadata comes from the deposit's .zenodo.json (title, creators, description, keywords, related
links, version) mapped onto figshare's fields.

Token: figshare.com -> profile -> Applications -> Personal tokens -> create.  Read from the environment only:
    FIGSHARE_TOKEN

Usage:
    python figshare_upload.py --dry-run           list what would be sent, touch nothing
    python figshare_upload.py                     new draft: metadata, reserved DOI, every file, private link
    python figshare_upload.py --article 12345678  refresh an existing draft: replace changed files, update metadata
    python figshare_upload.py --article 12345678 --publish     publish that draft (asks you to type  publish)

Every file is uploaded in figshare's parts and verified against the MD5 figshare computes.  Calls retry
patiently on 429/5xx and timeouts; re-running with --article resumes, skipping files whose MD5 already matches.
"""
import argparse, hashlib, io, json, os, sys, time

try:
    import requests
except ImportError:
    sys.exit('pip install requests')

HERE = os.path.dirname(os.path.abspath(__file__))
DEPOSIT = os.path.join(os.path.dirname(HERE), 'deposit_v1.0.0')
API = 'https://api.figshare.com/v2'
SKIP = {'MANIFEST_sha256.txt', '.zenodo.json'}
LICENSE_CC_BY_40 = 1                              # figshare licence id (GET /licenses)
CATEGORIES = [25846, 25834, 26833, 26635]         # Applied geophysics; Structural geology and tectonics; Mining engineering; Photogrammetry and remote sensing
WAIT = (10, 30, 60, 120, 240, 480)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def figshare_metadata(meta):
    """map the deposit's Zenodo-style metadata onto figshare's article fields"""
    contributors = ', '.join(c['name'] for c in meta.get('contributors', []))
    desc = meta['description'].strip()
    if contributors:
        desc += '<p>Survey by PARSAN Overseas Pvt Ltd (Dr Sanjay Rana, Ronak Dahiya); site access Mangala Rocks; introduction Viswa Minerals. Data collected 18 to 20 August 2026 near Kuppam, Chittoor district, Andhra Pradesh, India; the quarry\'s position is withheld.</p>'
    refs = []
    for r in meta.get('related_identifiers', []):
        i = r['identifier']; refs.append(i if i.startswith('http') else 'https://doi.org/' + i)
    m = dict(title=meta['title'], description=desc, defined_type='dataset',
             authors=[dict(name='Libish Murugesan', orcid_id=c.get('orcid', '')) for c in meta['creators']],
             categories=CATEGORIES, keywords=meta['keywords'], license=LICENSE_CC_BY_40, references=refs)
    rel = {'isSupplementTo': 'IsSupplementTo', 'isDocumentedBy': 'IsDocumentedBy', 'references': 'References'}
    m['related_materials'] = [dict(identifier=r['identifier'], title=r['identifier'], relation=rel.get(r['relation'], 'References'),
                                   identifier_type='URL' if r['identifier'].startswith('http') else 'DOI', is_linkout=False)
                              for r in meta.get('related_identifiers', [])]      # DOIs bare, URLs whole: figshare validates by identifier_type
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--article', type=int, help='existing draft article id to refresh')
    ap.add_argument('--publish', action='store_true', help='publish the draft named by --article (typed confirmation)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    tok = os.environ.get('FIGSHARE_TOKEN')
    meta = json.load(io.open(os.path.join(DEPOSIT, '.zenodo.json'), encoding='utf-8'))
    fm = figshare_metadata(meta)
    files = sorted(f for f in os.listdir(DEPOSIT) if f not in SKIP and not f.startswith('.'))
    total = sum(os.path.getsize(os.path.join(DEPOSIT, f)) for f in files)
    print('deposit : %s\nfiles   : %d, %.1f MB\ntitle   : %s\nlicence : CC BY 4.0 (id %d)\ncategories: %s\nkeywords: %d\nreferences: %d' %
          (DEPOSIT, len(files), total / 1e6, fm['title'], LICENSE_CC_BY_40, CATEGORIES, len(fm['keywords']), len(fm['references'])))
    for f in files:
        print('   %8.1f MB  %s' % (os.path.getsize(os.path.join(DEPOSIT, f)) / 1e6, f))
    if a.dry_run:
        print('\n--dry-run: nothing sent.'); return
    if not tok:
        sys.exit('\nno FIGSHARE_TOKEN in the environment. Nothing sent.')

    s = requests.Session(); s.headers['Authorization'] = 'token ' + tok
    s.headers['User-Agent'] = 'kuppam-deposit-uploader/1.0 (python-requests)'

    def call(method, url, **kw):
        body = kw.pop('body', None)
        for i, w in enumerate(WAIT + (None,)):
            try:
                r = s.request(method, url, timeout=600, data=body, **kw) if body is not None else s.request(method, url, timeout=600, **kw)
                if r.status_code not in (429, 500, 502, 503, 504): return r
                why = 'HTTP %d' % r.status_code
            except (requests.ConnectionError, requests.Timeout) as e:
                why = type(e).__name__
            if w is None: sys.exit('gave up on %s %s after %d attempts (%s)' % (method, url, len(WAIT) + 1, why))
            print('   %s on %s %s; waiting %d s before attempt %d' % (why, method, url.replace(API, '')[:50], w, i + 2)); time.sleep(w)

    # ---- publish only
    if a.publish:
        if not a.article: sys.exit('--publish needs --article <id>')
        art = call('GET', '%s/account/articles/%d' % (API, a.article)); art.raise_for_status(); art = art.json()
        print('\nabout to PUBLISH article %d: "%s"\n  files: %d\n  reserved DOI: %s' % (a.article, art['title'], len(art.get('files', [])), art.get('doi') or '(none)'))
        if input('This is public and permanent. Type  publish  to continue: ').strip() != 'publish': sys.exit('aborted')
        r = call('POST', '%s/account/articles/%d/publish' % (API, a.article))
        if r.status_code >= 400: sys.exit('publish failed: %d %s' % (r.status_code, r.text[:500]))
        print('published:', r.json().get('location'))
        art = call('GET', '%s/articles/%d' % (API, a.article)).json()
        print('  public page : %s\n  DOI         : https://doi.org/%s' % (art.get('url_public_html'), art.get('doi'))); return

    # ---- draft
    if a.article:
        r = call('GET', '%s/account/articles/%d' % (API, a.article)); r.raise_for_status(); art = r.json()
        if art.get('is_public'):
            sys.exit('article %d is already published; make a new version from the web page first.' % a.article)
        aid = a.article; print('\nrefreshing draft %d' % aid)
        r = call('PUT', '%s/account/articles/%d' % (API, aid), json=fm)
        if r.status_code == 400 and 'related_materials' in fm:
            print('   400 %s; retrying without related_materials' % r.text[:120])
            fm.pop('related_materials'); r = call('PUT', '%s/account/articles/%d' % (API, aid), json=fm)
        if r.status_code >= 400: sys.exit('metadata rejected: %d %s' % (r.status_code, r.text[:1500]))
    else:
        r = call('POST', '%s/account/articles' % API, json=fm)
        if r.status_code == 400 and 'related_materials' in fm:
            print('   400 %s; retrying without related_materials' % r.text[:120])
            fm.pop('related_materials'); r = call('POST', '%s/account/articles' % API, json=fm)
        if r.status_code >= 400: sys.exit('create rejected: %d %s' % (r.status_code, r.text[:1500]))
        aid = r.json()['entity_id']; print('\ncreated draft article %d' % aid)

    # ---- figshare adds the account holder as an author on creation; keep one entry, the one with the ORCID
    art = call('GET', '%s/account/articles/%d' % (API, aid)).json()
    au = art.get('authors', [])
    if len(au) > 1:
        keep = [x for x in au if x.get('orcid_id')] or au[:1]
        r = call('PUT', '%s/account/articles/%d' % (API, aid), json={'authors': [{'id': keep[0]['id']}]})
        au = call('GET', '%s/account/articles/%d' % (API, aid)).json().get('authors', [])
        print('authors      : %s' % ', '.join('%s (%s)' % (x['full_name'], x.get('orcid_id') or 'no ORCID') for x in au))
    # ---- DOI reserved before publishing, so it can be written into the files
    doi = art.get('doi')
    if not doi:
        r = call('POST', '%s/account/articles/%d/reserve_doi' % (API, aid))
        if r.status_code >= 400: print('reserve_doi failed: %d %s' % (r.status_code, r.text[:300]))
        else: doi = r.json().get('doi')
    print('reserved DOI : %s' % (doi or '(none)'))

    # ---- files, replaced by name when the MD5 differs
    existing = {f['name']: f for f in call('GET', '%s/account/articles/%d/files?page_size=1000' % (API, aid)).json()}   # the list endpoint pages at 10 by default
    for f in files:
        p = os.path.join(DEPOSIT, f); local = md5(p); size = os.path.getsize(p)
        if f in existing:
            if existing[f].get('computed_md5') == local or existing[f].get('supplied_md5') == local:
                print('   unchanged  %s' % f); continue
            rd = call('DELETE', '%s/account/articles/%d/files/%d' % (API, aid, existing[f]['id']))
            if rd.status_code >= 400: sys.exit('could not delete the old %s (HTTP %d %s); a duplicate would result' % (f, rd.status_code, rd.text[:200]))
        t0 = time.time()
        r = call('POST', '%s/account/articles/%d/files' % (API, aid), json=dict(name=f, md5=local, size=size))
        if r.status_code >= 400: sys.exit('file create failed: %s %d %s' % (f, r.status_code, r.text[:300]))
        finfo = call('GET', r.json()['location']).json()
        up = call('GET', finfo['upload_url']).json()
        with open(p, 'rb') as fh:
            for part in up['parts']:
                fh.seek(part['startOffset']); chunk = fh.read(part['endOffset'] - part['startOffset'] + 1)
                rr = call('PUT', '%s/%d' % (finfo['upload_url'], part['partNo']), body=chunk)
                if rr.status_code >= 400: sys.exit('part %d of %s failed: %d %s' % (part['partNo'], f, rr.status_code, rr.text[:300]))
        r = call('POST', '%s/account/articles/%d/files/%d' % (API, aid, finfo['id']))   # complete
        if r.status_code >= 400: sys.exit('complete failed: %s %d %s' % (f, r.status_code, r.text[:300]))
        for _ in range(30):
            finfo = call('GET', '%s/account/articles/%d/files/%d' % (API, aid, finfo['id'])).json()
            if finfo.get('status') == 'available' or finfo.get('computed_md5'): break
            time.sleep(2)
        remote = finfo.get('computed_md5') or ''
        ok = remote == local
        print('   %s  %-40s %7.1f MB  %5.0f s  %d parts  md5 %s' % ('ok ' if ok else 'BAD', f, size / 1e6, time.time() - t0, len(up['parts']), remote[:12]))
        if not ok: sys.exit('checksum mismatch on %s: local %s, figshare %s' % (f, local, remote))

    art = call('GET', '%s/account/articles/%d' % (API, aid)).json()
    print('\nDRAFT ready, not published.\n  article id   : %d\n  private link : %s\n  reserved DOI : %s  (resolves only after publishing)\n'
          % (aid, art.get('url_private_html'), doi or '(none)'))
    print('Read it at the private link, put the DOI into the files, re-run with --article %d to replace them, then\n'
          'python figshare_upload.py --article %d --publish' % (aid, aid))


if __name__ == '__main__':
    main()
