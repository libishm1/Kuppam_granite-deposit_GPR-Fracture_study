"""figs/ORIENTATION_evidence.png: the satellite view and four registered photographs with the reasoning under each
(see ORIENTATION.md). Inputs: dataset/site/satellite_google_maps_client_2026-09-11.jpg (client screenshot, north up)
and figs/REPROJ_<blk>_<photo>.jpg from scripts/verify_reproject.py."""
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, textwrap
from PIL import Image
OUT = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
panels = [(OUT + '/dataset/site/satellite_google_maps_client_2026-09-11.jpg', 'Satellite view (client, Google Maps, north up)',
           'The pit runs east-west. The ramp track leaves along the NORTH rim at the EAST end (top right); the large tan cut face is at the east end; the red dot marks the benches.'),
          (OUT + '/figs/REPROJ_B_20260819_181244.jpg', 'Block B, photo 181244: camera at grid (7.3, -1.6) looking along grid +y',
           'Pose from the registration; the drawn lattice fits the paint. The ramp climbs the LEFT wall; tan face and excavator ahead. Facing east, the left wall is north, so +y = EAST on B; B is right-handed, so +x is south and B0 is the north-western corner.'),
          (OUT + '/figs/REPROJ_B_20260819_180430.jpg', 'Block B, photo 180430: camera at grid (-0.8, 8.0) looking toward B0 (bearing 146 deg)',
           'The registered origin (yellow) is the far corner, the client\'s red dot. The painted B1 is by the camera; the tall sawn wall is at +x (south); the bench with the white lattice beyond B0 is Block A, to the west.'),
          (OUT + '/figs/REPROJ_A_20260819_113557.jpg', 'Block A, photo 113557: camera at grid (-3.1, 3.0) looking along grid +x',
           'The same ramp on the LEFT, the same tan face and excavator ahead, so +x = EAST on A. A is left-handed with z up, so +y is south and A0 is the north-western corner.'),
          (OUT + '/figs/REPROJ_C_20260819_182338.jpg', 'Block C, photo 182338: camera at grid (-2.4, 5.3) looking along grid +x',
           'Ramp on the LEFT, tan face ahead, so +x = EAST on C. C is left-handed, so +y is south and C0 is the north-western corner.')]
fig = plt.figure(figsize=(30, 11.5))
gs = fig.add_gridspec(2, 5, height_ratios=[8.2, 2.6], hspace=0.04, wspace=0.03, left=0.01, right=0.99, top=0.93, bottom=0.01)
for i, (p, head, body) in enumerate(panels):
    ax = fig.add_subplot(gs[0, i]); im = Image.open(p); im.thumbnail((1000, 1200)); ax.imshow(im); ax.axis('off')
    ax.set_title(textwrap.fill(head, 62), fontsize=10.5, loc='left', fontweight='bold')
    tx = fig.add_subplot(gs[1, i]); tx.axis('off')
    tx.text(0, 1, textwrap.fill(body, 66), fontsize=10, va='top', ha='left', transform=tx.transAxes, linespacing=1.35)
fig.suptitle('Grid orientation from the registered photographs and the satellite view: every origin is the north-western corner, every bench looks east; B has +y east, A and C have +x east', fontsize=14, y=0.985)
fig.savefig(OUT + '/figs/ORIENTATION_evidence.png', dpi=90); print('figure written')
