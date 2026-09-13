"""Assemble the Zenodo deposit for the Kuppam GPR pilot from the corrected local state (13 September 2026).

Everything included is derived data, the model, its verification, the standalone interactive model and
the code that produced them: the perimeter the public GitHub repository already carries, brought up to
the 13 September state, plus the joint-mapping results that were never pushed.  What is excluded, and
why, is in PUBLIC_AUDIT.md next to this script; it is copied into the deposit.

Usage:
    python build_deposit.py                  -> ../deposit_v1.0.0/  one zip per component, README.md,
                                                PUBLIC_AUDIT.md, licences, .zenodo.json, CITATION.cff,
                                                FILELIST.txt, DUPLICATES.txt, MANIFEST_sha256.txt
    python build_deposit.py --with-optional  -> also the two OPTIONAL zips (raw survey records, films),
                                                for the owner to decide on; never built by default

Nothing here uploads or publishes.  Read-only on the sources.  The build refuses to finish if a hard
private term (money, phone, e-mail) turns up in any text file it is about to pack.
"""
import glob, hashlib, io, json, os, re, shutil, sys, zipfile
from datetime import date

WS = 'D:/code_ws'
G = os.path.join(WS, 'outputs/2026-09-09/gpr_raw_audit')
J = os.path.join(WS, 'outputs/2026-09-11/joint_mapping')
S = os.path.join(WS, 'outputs/2026-09-11/story_video')
RAW = os.path.join(WS, 'reference/parsans/report/raw/GPR Raw data_Kuppam')
HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
ROOT = os.path.join(TOP, 'deposit_v1.0.0')
VERSION = '1.0.0'
TITLE = 'Kuppam dolerite benches: ground-penetrating radar fracture model, verification and block yield - pilot dataset'
REPO = 'https://github.com/libishm1/Kuppam_granite-deposit_GPR-Fracture_study'
SITE = 'https://libishm1.github.io/Kuppam_granite-deposit_GPR-Fracture_study/'

# ------------------------------------------------------------------ what goes in, by component
# (source directory or file, subpath inside the zip, substrings that exclude a path within this entry)
SCRATCH = ['_ORIGINAL', '_BEFORE', '_backup_', '__pycache__', '.pyc', 'Thumbs.db', '.DS_Store']
COMPONENTS = {
    '01_survey_lines': [
        (os.path.join(G, 'dataset/picks/line_inventory.csv'), 'line_inventory.csv', []),
        (os.path.join(G, 'tables/GEOMETRY_resolved.csv'), 'GEOMETRY_resolved.csv', []),
    ],
    '02_picks_surfaces_frames': [
        (os.path.join(G, 'dataset'), 'dataset', ['dataset/site/']),          # site/ = the client's Google Maps screenshot: out
        (os.path.join(G, 'model'), 'model', []),
    ],
    '03_model_tables': [
        (os.path.join(G, 'tables'), 'gpr_raw_audit_tables', ['/redness_', '/paint_raster_']),   # photo-derived raster caches, 76 MB: out
        (os.path.join(J, 'tables'), 'joint_mapping_tables', []),
        (os.path.join(J, 'site_data.json'), 'joint_mapping_site_data_8cm.json', []),
        (os.path.join(J, 'site_data_12.json'), 'joint_mapping_site_data_12cm.json', []),
    ],
    '04_radargram_panels': [
        (os.path.join(G, 'web/panels'), 'panels', []),
    ],
    '05_figures': [
        (os.path.join(G, 'figs'), 'gpr_raw_audit_figs',
         ['/rpt_p',                      # pages of the contractor's report, rendered: out
          '/sketch_A_p1', '/sketch_B_p1', '/sketch_C_p1', '/sketch_A_grid', '/sketch_diag_', '/A_TECHNICIAN_SKETCH',   # contractor's field sheets: optional bucket
          '/photo_', '/photos_',         # raw photographs and contact sheets (people in frame): out
          '/WEB_v',                      # interface development screenshots: out
          '/_zoom_', '/_view_sketch_']),
        (os.path.join(J, 'figs'), 'joint_mapping_figs', []),
    ],
    '06_documents': [
        (os.path.join(G, 'REPORT.md'), 'REPORT.md', []),
        (os.path.join(G, 'REPORT.pdf'), 'REPORT.pdf', []),
        (os.path.join(G, 'MODEL.md'), 'MODEL.md', []),
        (os.path.join(G, 'UNCERTAINTY.md'), 'UNCERTAINTY.md', []),
        (os.path.join(G, 'ORIENTATION.md'), 'ORIENTATION.md', []),
        (os.path.join(G, 'VERIFICATION.md'), 'VERIFICATION.md', []),
        (os.path.join(G, 'AUDIT.md'), 'AUDIT.md', []),
        (os.path.join(G, 'AUDIT_RESPONSE.md'), 'AUDIT_RESPONSE.md', []),
        (os.path.join(G, 'GEOLOGIST_AUDIT.md'), 'GEOLOGIST_AUDIT.md', []),
        (os.path.join(J, 'STUDY.md'), 'joint_mapping_STUDY.md', []),
    ],
    '07_interactive_model': [
        (os.path.join(G, 'web/site'), 'site', ['clouds_ORIGINAL']),
    ],
    '08_code': [
        (os.path.join(G, 'scripts'), 'gpr_raw_audit_scripts', []),
        (os.path.join(J, 'scripts'), 'joint_mapping_scripts', []),
        (os.path.join(S, 'scripts/numbers_check.py'), 'audit/numbers_check.py', []),
        (os.path.join(HERE, 'build_deposit.py'), 'deposit/build_deposit.py', []),
        (os.path.join(HERE, 'zenodo_upload.py'), 'deposit/zenodo_upload.py', []),
    ],
}
# built only with --with-optional; the owner decides whether they go up at all
OPTIONAL = {
    'OPTIONAL_raw_survey_records': [
        (RAW, 'GPR_raw_data_Kuppam', []),          # 178 SEG-Y, 89 instrument CSVs, 6 preview JPGs, 3 field sheets (PDF)
    ],
    'OPTIONAL_films': [(f, os.path.basename(f), []) for f in sorted(glob.glob(os.path.join(S, '*_upload.mp4')))],
}
# never, whatever the component
NEVER = ['EMAIL_', 'MESSAGES_before_posting', 'WHATSAPP', 'HANDOFF', 'REVIEW_before', 'TAMIL_review', 'report_new', 'report_old', 'logs/'] + SCRATCH
# hard private terms: the build stops if one appears in a text file about to be packed
HARD = re.compile(r'(\u20b9|\bRs\.? ?[0-9]|\blakhs?\b|\bINR\b|\+91[ -]?[0-9]|\bcrore\b|\brupees?\b|@gmail\.|@parsan|@yahoo|@outlook|[Qq]uotation)')
TEXT = ('.md', '.py', '.json', '.csv', '.txt', '.js', '.webmanifest', '.cff', '.html')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def norm(p):
    return p.replace(os.sep, '/')


def excluded(path, extra):
    s = norm(path)
    return any(x in s for x in NEVER) or any(norm(x) in s for x in extra)


def collect(entries):
    """(absolute source path, arcname inside the zip) for every file of a component"""
    out = []
    for src, sub, extra in entries:
        if not os.path.exists(src):
            print('  [missing, skipped] %s' % src); continue
        if os.path.isfile(src):
            if not excluded(src, extra): out.append((src, sub))
            continue
        for dp, dn, fn in os.walk(src):
            dn[:] = [d for d in dn if not excluded(os.path.join(dp, d) + '/', extra)]
            for f in sorted(fn):
                p = os.path.join(dp, f)
                if excluded(p, extra): continue
                out.append((p, norm(os.path.join(sub, os.path.relpath(p, src)))))
    return out


def scan_text(p):
    """hard private terms in a text file; html pages are scanned outside their base64 blobs"""
    if not p.lower().endswith(TEXT) or os.path.getsize(p) > 8e6: return []
    if os.path.basename(p) == 'build_deposit.py': return []          # this file: the pattern itself would match
    try: t = io.open(p, encoding='utf-8').read()
    except Exception: return []
    t = re.sub(r'[A-Za-z0-9+/=]{200,}', ' ', t)              # embedded base64 binary data (html pages, site JSON), not prose
    return [t[max(0, m.start() - 50):m.end() + 50].replace('\n', ' ') for m in HARD.finditer(t)]


def build(components, manifest, seen, dup, filelist):
    total = 0
    for comp, entries in components.items():
        files = collect(entries)
        zp = os.path.join(ROOT, comp + '.zip'); n = 0; raw = 0; hits = []
        filelist.append('\n== %s.zip' % comp)
        with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for src, arc in files:
                if any(x in arc for x in NEVER):
                    sys.exit('refusing: excluded name reached the zip: %s' % arc)
                h = sha256(src)
                if h in seen and os.path.getsize(src) > 0:
                    dup.append('%s/%s  <- identical to  %s' % (comp, arc, seen[h])); continue
                seen[h] = '%s/%s' % (comp, arc)
                for c in scan_text(src): hits.append('%s | %s' % (arc, c))
                z.write(src, arc); n += 1; raw += os.path.getsize(src)
                filelist.append('%12d  %s' % (os.path.getsize(src), arc))
        if hits:
            print('\n'.join(hits)); sys.exit('refusing: %d hard private term(s) in %s' % (len(hits), comp))
        zs = os.path.getsize(zp); total += zs
        manifest.append((comp + '.zip', zs, sha256(zp)))
        print('%-30s %5d files  %7.1f MB raw  ->  %7.1f MB zip' % (comp, n, raw / 1e6, zs / 1e6))
    return total


def main():
    with_opt = '--with-optional' in sys.argv
    if os.path.exists(ROOT): shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    manifest = []; seen = {}; dup = []; filelist = []
    total = build(COMPONENTS, manifest, seen, dup, filelist)
    if with_opt:
        total += build(OPTIONAL, manifest, seen, dup, filelist)
    # root files
    root_files = {
        'README.md': os.path.join(TOP, 'README_deposit.md'),
        'PUBLIC_AUDIT.md': os.path.join(TOP, 'PUBLIC_AUDIT.md'),
        'NOTICE.md': os.path.join(TOP, 'NOTICE.md'),
        'LICENSE-data-CC-BY-4.0.txt': os.path.join(TOP, 'LICENSE-data-CC-BY-4.0.txt'),
        'LICENSE-code-GPL-3.0.txt': os.path.join(TOP, 'LICENSE-code-GPL-3.0.txt'),
    }
    for dst, src in root_files.items():
        if not os.path.exists(src): sys.exit('missing root file %s' % src)
        for c in scan_text(src): sys.exit('refusing: hard private term in %s: %s' % (dst, c))
        shutil.copy(src, os.path.join(ROOT, dst)); manifest.append((dst, os.path.getsize(src), sha256(src)))
    io.open(os.path.join(ROOT, 'FILELIST.txt'), 'w', encoding='utf-8').write('\n'.join(filelist) + '\n')
    io.open(os.path.join(ROOT, 'DUPLICATES.txt'), 'w', encoding='utf-8').write(
        'Files identical in content to one already packed were left out once; the kept copy is on the right.\n\n' + '\n'.join(dup) + '\n')
    # metadata
    desc = io.open(os.path.join(TOP, 'DESCRIPTION.html'), encoding='utf-8').read()
    meta = {
        "title": TITLE,
        "upload_type": "dataset",
        "publication_date": date.today().isoformat(),
        "version": VERSION,
        "language": "eng",
        "access_right": "open",
        "license": "cc-by-4.0",
        "creators": [{"name": "Murugesan, Libish", "orcid": "0009-0004-3238-4202"}],
        "contributors": [
            {"name": "PARSAN Overseas Pvt Ltd", "type": "DataCollector"},
            {"name": "Rana, Sanjay", "type": "DataCollector", "affiliation": "PARSAN Overseas Pvt Ltd"},
            {"name": "Dahiya, Ronak", "type": "DataCollector", "affiliation": "PARSAN Overseas Pvt Ltd"},
            {"name": "Mangala Rocks", "type": "Other"},
            {"name": "Viswa Minerals", "type": "Other"},
        ],
        "description": desc,
        "keywords": ["ground-penetrating radar", "GPR", "dimension stone", "dolerite", "black granite", "fracture mapping",
                     "joint sets", "quarry", "block planning", "wire saw", "photogrammetry", "uncertainty",
                     "Kuppam", "Andhra Pradesh", "India"],
        "related_identifiers": [
            {"identifier": REPO, "relation": "isSupplementTo", "resource_type": "software"},
            {"identifier": SITE, "relation": "isDocumentedBy"},
            {"identifier": "10.5281/zenodo.20608279", "relation": "references", "resource_type": "publication-article"},
            {"identifier": "10.5281/zenodo.21228269", "relation": "references", "resource_type": "software"},
        ],
        "dates": [{"start": "2026-08-18", "end": "2026-08-20", "type": "Collected", "description": "GPR survey and photogrammetry on site"}],
        "locations": [{"place": "Kuppam, Chittoor district, Andhra Pradesh, India",
                       "description": "Nearest town. The quarry's position is withheld at the owner's discretion."}],
        "notes": ("Data licence CC BY 4.0. The code in 08_code.zip is GPL-3.0-only, as in the linked repository. "
                  "The contractor's report, the raw SEG-Y records, the full photogrammetry meshes, photographs of people, "
                  "correspondence and commercial figures are not part of this deposit; see PUBLIC_AUDIT.md."),
    }
    json.dump(meta, io.open(os.path.join(ROOT, '.zenodo.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    cff = ('cff-version: 1.2.0\ntitle: "%s"\nmessage: "If you use this dataset, please cite it using this metadata."\n'
           'type: dataset\nauthors:\n  - given-names: Libish\n    family-names: Murugesan\n'
           '    orcid: "https://orcid.org/0009-0004-3238-4202"\nversion: "%s"\ndate-released: "%s"\nlicense: CC-BY-4.0\n'
           'repository-code: "%s"\nurl: "%s"\nkeywords:\n  - ground-penetrating radar\n  - dimension stone\n  - dolerite\n'
           '  - fracture mapping\n  - block planning\n') % (TITLE, VERSION, date.today().isoformat(), REPO, SITE)
    io.open(os.path.join(ROOT, 'CITATION.cff'), 'w', encoding='utf-8').write(cff)
    for f in ('.zenodo.json', 'CITATION.cff', 'FILELIST.txt', 'DUPLICATES.txt'):
        manifest.append((f, os.path.getsize(os.path.join(ROOT, f)), sha256(os.path.join(ROOT, f))))
    with io.open(os.path.join(ROOT, 'MANIFEST_sha256.txt'), 'w', encoding='utf-8') as m:
        for name, size, h in manifest:
            m.write('%s  %12d  %s\n' % (h, size, name))
    print('\n%d duplicate file(s) left out (DUPLICATES.txt)' % len(dup))
    print('deposit at %s\n  %d files, %.1f MB in zips%s' % (ROOT, len(manifest) + 1, total / 1e6, '' if with_opt else '  (optional zips not built)'))


if __name__ == '__main__':
    main()
