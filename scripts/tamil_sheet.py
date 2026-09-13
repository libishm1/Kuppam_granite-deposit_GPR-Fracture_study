# -*- coding: utf-8 -*-
"""Pull every translated string out of the interface into one sheet a Tamil speaker can mark up,
and push corrections back in from the same sheet.

    tamil_sheet.py out   writes TAMIL_review.md, one row per string, English beside Tamil
    tamil_sheet.py in    reads TAMIL_review.md back and applies whatever changed

The sheet is the thing you hand over. Nobody needs to open the code to fix the Tamil: they edit the
right-hand column, and the same script puts it back. The key column must not be touched, since that
is what the edits are matched on.
"""
import io, re, sys, os

P = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit/web/index.template.html'
SHEET = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit/TAMIL_review.md'
BOUND = chr(39) + '],'          # the end of one string and the start of the next key
OPEN = ":['"
PAT = re.compile(r"([A-Za-z_0-9]+):\['(.*?)','(.*?)'\](?=,|\n|\})", re.S)

# where each key shows up, so a reviewer can find it on screen
WHERE = [
    ('nav_', 'the tabs and the bottom bar'), ('role_', 'who is looking'),
    ('l_', 'the layer list on the left'), ('sn_', 'the names of the fracture surfaces'),
    ('chip_', 'the small badges on the layer list'), ('cut_', 'the Cutting tab'),
    ('y_', 'the Yield tab'), ('cls_', 'block size classes'), ('th_', 'table headings'),
    ('rd_', 'the Radar tab'), ('tr_', 'the How-sure tab'), ('unc_', 'the clearance choice'),
    ('scen_', 'the crack-depth choice'), ('clr_', 'what each clearance case means'),
    ('day_', 'the daylight check'), ('what_', 'what this is and is not'),
    ('site_', 'the whole-pit view'), ('compass_', 'the corner compass'),
    ('dl_', 'the depth limit'), ('sec_', 'the radar section'),
]


def where(k):
    for pre, name in WHERE:
        if k.startswith(pre):
            return name
    return 'elsewhere on the page'


def esc(s):
    return s.replace('|', '\\|').replace('\n', ' ')


def out():
    t = io.open(P, encoding='utf-8').read()
    rows = [(m.group(1), m.group(2), m.group(3)) for m in PAT.finditer(t)]
    groups = {}
    for k, en, ta in rows:
        groups.setdefault(where(k), []).append((k, en, ta))
    f = io.open(SHEET, 'w', encoding='utf-8')
    f.write('# The Tamil on the Kuppam page, for review\n\n'
            'Every line of Tamil the page can show, %d of them, beside the English it was written '
            'from. Change anything in the **Tamil** column that is wrong, awkward, or not what the '
            'crew would say. Leave the **key** column alone: that is how the corrections are put '
            'back.\n\n'
            'The page is at https://libishm1.github.io/Kuppam_granite-deposit_GPR-Fracture_study/ '
            'and the Tamil button is at the top right.\n\n'
            'Things worth watching for: the trade words (block, gang saw, cutter, bench, wire), '
            'whether the register sounds spoken rather than written, and anywhere a sentence '
            'promises more than it should.\n\n' % len(rows))
    for g in sorted(groups):
        f.write('\n## %s\n\n| key | English | Tamil |\n| --- | --- | --- |\n' % g)
        for k, en, ta in groups[g]:
            f.write('| `%s` | %s | %s |\n' % (k, esc(en), esc(ta)))
    f.close()
    print('wrote %s: %d strings in %d groups' % (os.path.basename(SHEET), len(rows), len(groups)))


def back():
    t = io.open(P, encoding='utf-8').read()
    sheet = io.open(SHEET, encoding='utf-8').read()
    new, skipped = {}, []
    for m in re.finditer(r'^\| `([A-Za-z_0-9]+)` \| (.*?) \| (.*?) \|$', sheet, re.M):
        k, en, ta = m.group(1), m.group(2), m.group(3).replace('\\|', '|')
        # a row that runs across a string boundary came from a bad extraction, and
        # writing it back would rewrite the neighbouring keys as well. An escaped
        # apostrophe inside one string is fine and must not trip this.
        if BOUND in ta or BOUND in en or OPEN in ta or OPEN in en:
            skipped.append(k)
            continue
        new[k] = ta
    if skipped:
        print('skipped %d malformed row(s): %s' % (len(skipped), ', '.join(skipped)))
    changed = 0
    def repl(m):
        global changed
        k, en, ta = m.group(1), m.group(2), m.group(3)
        if k in new and new[k] != ta.replace('\n', ' '):
            return "%s:['%s','%s']" % (k, en, new[k])
        return m.group(0)
    out_t, n = PAT.subn(lambda m: repl(m), t)
    diff = sum(1 for m in PAT.finditer(t)
               if m.group(1) in new and new[m.group(1)] != m.group(3).replace('\n', ' '))
    io.open(P, 'w', encoding='utf-8').write(out_t)
    print('%d strings updated from the sheet' % diff)
    if diff:
        print('now run: python scripts/web_bundle.py')


if __name__ == '__main__':
    (back if len(sys.argv) > 1 and sys.argv[1] == 'in' else out)()
