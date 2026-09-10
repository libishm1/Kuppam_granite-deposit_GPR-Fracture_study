import fitz, sys, os, re, json
src = sys.argv[1]; tag = sys.argv[2]
d = fitz.open(src)
os.makedirs('report_%s/images' % tag, exist_ok=True)
txt = []
meta = []
for pi, p in enumerate(d):
    t = p.get_text('text')
    txt.append('\n\n<!-- ===== PAGE %d ===== -->\n\n' % (pi + 1) + t)
    imgs = p.get_images(full=True)
    for k, im in enumerate(imgs):
        xref = im[0]
        try:
            pix = fitz.Pixmap(d, xref)
            if pix.n - pix.alpha >= 4: pix = fitz.Pixmap(fitz.csRGB, pix)
            fn = 'report_%s/images/p%02d_i%d.png' % (tag, pi + 1, k)
            pix.save(fn)
            meta.append(dict(page=pi + 1, idx=k, xref=xref, w=pix.width, h=pix.height, file=fn))
        except Exception as e:
            meta.append(dict(page=pi + 1, idx=k, xref=xref, err=str(e)))
open('report_%s/TEXT.md' % tag, 'w', encoding='utf-8').write(''.join(txt))
json.dump(meta, open('report_%s/images.json' % tag, 'w'), indent=1)
print(tag, 'pages', len(d), 'images', len(meta), 'chars', sum(len(x) for x in txt))
