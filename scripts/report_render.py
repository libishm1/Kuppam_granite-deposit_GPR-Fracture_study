"""REPORT.md -> REPORT.html (self-contained styling) -> REPORT.pdf via headless Chrome.
Usage: python scripts/report_render.py [REPORT]   (also works for GEOLOGIST_AUDIT etc.)"""
import sys, os, subprocess, markdown
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
name = sys.argv[1] if len(sys.argv) > 1 else 'REPORT'
CHROME = r'C:/Program Files/Google/Chrome/Application/chrome.exe'
CSS = """
@page{size:A4;margin:16mm 15mm}
body{font:10.5pt/1.45 "IBM Plex Sans","Segoe UI",Arial,sans-serif;color:#161B22;max-width:100%}
h1{font:600 20pt/1.15 "IBM Plex Sans Condensed","Segoe UI",Arial,sans-serif;margin:0 0 6pt}
h2{font:600 13pt/1.2 "IBM Plex Sans Condensed","Segoe UI",Arial,sans-serif;margin:16pt 0 6pt;border-bottom:1px solid #CFD5DC;padding-bottom:3pt;page-break-after:avoid}
h3{font:600 11pt/1.2 "IBM Plex Sans Condensed","Segoe UI",Arial,sans-serif;margin:12pt 0 4pt;page-break-after:avoid}
p{margin:5pt 0} table{border-collapse:collapse;width:100%;margin:6pt 0;font-size:9pt;page-break-inside:avoid}
th{text-align:left;font-weight:600;border-bottom:1px solid #161B22;padding:3pt 4pt;font-size:8.5pt;text-transform:uppercase;letter-spacing:.04em;color:#5B6570}
td{border-bottom:1px solid #E2E6EB;padding:3pt 4pt;vertical-align:top}
img{max-width:100%;display:block;margin:8pt auto;page-break-inside:avoid}
code{font:9pt "IBM Plex Mono",Consolas,monospace;background:#F1F3F5;padding:0 3px}
a{color:#C8452B;text-decoration:none} hr{border:0;border-top:1px solid #CFD5DC;margin:12pt 0}
ol,ul{margin:4pt 0 4pt 18pt} li{margin:2pt 0}
blockquote{margin:6pt 0 6pt 12pt;padding-left:8pt;border-left:2px solid #CFD5DC;color:#5B6570}
"""
md = open(os.path.join(OUT, name + '.md'), encoding='utf-8').read()
title = md.splitlines()[0].lstrip('# ').strip()
body = markdown.markdown(md, extensions=['tables', 'fenced_code'])
html = ('<!doctype html><html><head><meta charset="utf-8"><title>%s</title>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono&display=swap">'
        '<style>%s</style></head><body>%s</body></html>') % (title, CSS, body)
hp = os.path.join(OUT, name + '.html'); open(hp, 'w', encoding='utf-8').write(html)
pp = os.path.join(OUT, name + '.pdf')
subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--print-to-pdf=' + pp, '--virtual-time-budget=8000', 'file:///' + hp.replace('\\', '/')], capture_output=True, timeout=180)
print(name + '.html %.0f kB, %s.pdf %.1f MB' % (os.path.getsize(hp) / 1e3, name, os.path.getsize(pp) / 1e6))
