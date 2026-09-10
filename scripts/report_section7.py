"""Regenerate REPORT.md section 7 (block yield, straight-cut plan, uncertainty) from the tables, so the report's
numbers are the pipeline's numbers. Replaces everything between '## 7. Block yield' and '## 8. Verification'."""
import io, json, os
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
G = json.load(open(os.path.join(OUT, 'tables', 'guillotine_packing.json')))
P = json.load(open(os.path.join(OUT, 'tables', 'block_packing.json')))
U = json.load(open(os.path.join(OUT, 'tables', 'uncertainty.json')))
SC = [('ignore_surface', 'ignored'), ('surface_0.5m', '0.5 m'), ('surface_1.0m', '1.0 m'), ('surface_full', 'full depth')]


def cls_row(r): c = r['classes']; return '%d | %d | %d | %d' % (c['gangsaw_large']['n'], c['gangsaw_standard']['n'], c['small_block']['n'], c['cutter_block']['n'])


def gtable(unc):
    s = '| block | chalked cracks assumed to reach | large | gangsaw | small | cutter | cuts | waste pieces | tonnes | of gross |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for b in 'ABC':
        for k, lab in SC:
            r = G[b][k + '__' + unc]; s += '| %s | %s | %s | %d | %d | %.0f | %.0f %% |\n' % (b, lab, cls_row(r), r['n_cuts'], r['n_waste'], r['packed_t'], 100 * r['recovery_ratio'])
    return s


def ftable(unc):
    s = '| block | chalked cracks assumed to reach | large | gangsaw | small | cutter | tonnes | of gross |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for b in 'ABC':
        for k, lab in SC:
            r = P[b][k + '__' + unc]; s += '| %s | %s | %s | %.0f | %.0f %% |\n' % (b, lab, cls_row(r), r['packed_t'], 100 * r['recovery_ratio'])
    return s


def utable():
    s = '| surface | mean depth | σ pick | σ velocity | σ registration | σ total (1σ) | 2σ max | dip modelled → migrated (elevation frame) | plan shift | migration offset, vertical |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for b in 'ABC':
        for F, u in U[b].items():
            s += '| %s | %.2f m | %.0f cm | %.0f cm | %.0f cm | %.0f cm | %.0f cm | %.1f° → %.1f° | %.2f m | %.2f to %.2f m |\n' % (F, u['mean_depth_m'], 100 * u['sigma_pick_m'], 100 * u['sigma_vel_m_at_mean_depth'], 100 * u['sigma_reg_m'], 100 * u['sigma_total_m_at_mean_depth'], 100 * u['two_sigma_m_max'], u['dip_modelled_deg'], u['dip_migrated_deg'], u['migration_plan_shift_median_m'], u['migration_vertical_offset_m']['min'], u['migration_vertical_offset_m']['max'])
    return s


g = lambda b, k, u='uncertain': G[b][k + '__' + u]
first = min(g('B', 'surface_1.0m')['boxes'], key=lambda q: q['remove_seq'])
sec7 = """## 7. Block yield

Two questions are kept apart here: how much rock lies between the surfaces (section
7.1, a heuristic), and what a wire saw could actually take out of it in straight cuts,
in what order, and how sure that is (7.2 and 7.3). Everything in this section is in
one physical frame, bench-frame absolute elevation on the painted grid (10 cm voxels):
rock exists below the photographed surface and above the floor; each GPR surface is a
forbidden band at its absolute elevation; the chalked cracks are vertical prisms from
the local surface down to an assumed depth. Density 2.95 t/m3, unmeasured. Classes:
gangsaw large >= 2.7 x 1.5 x 1.5 m, gangsaw >= 2.1 x 1.2 x 1.2, small >= 1.5 x 0.9 x
0.9, cutter >= 0.9 x 0.6 x 0.6, on the marked size; 5 cm kerf per dimension. Floor:
the C-2 cap for C; a flat floor 3.0 m below the median surface for A and B, where no
floor was surveyed.

Two clearance cases are run for every chalk assumption. **As drawn**: 15 cm clear of
each surface where the model draws it, 10 cm from a chalked crack. **With
uncertainty**: clear of each surface by twice its estimated positional error (section
7.3) and of its migrated position as well, 20 cm from a chalked crack. The uncertain
case is the one to plan on; the as-drawn case is the best case.

### 7.1 Rock between the surfaces: an unconstrained heuristic estimate

Greedy largest-box packing on the same domain pooled to 20 cm (a cell is free only if
all its 10 cm voxels are), no requirement that any cut can reach a block, classes on
finished size. It is not a proven upper bound on the straight-cut plan and nothing in
it can be cut as listed; it says roughly how much rock the surfaces leave. Earlier
versions of this table rounded A to 5.6 m and B to 9.6 m and let boxes leave the
footprint; the footprint is now exact. A pooled cell's nominal top can sit up to 5 cm
above the lowest surface point in it; the 5 cm kerf absorbs that, so no finished box
protrudes.

With uncertainty:

""" + ftable('uncertain') + """
As drawn:

""" + ftable('modelled') + """
### 7.2 A plan the saw can follow: straight cuts only

A wire saw makes through-planes. The cutting plan is a guillotine tree: the bench is
split by one vertical plane on a painted 0.5 m line or one horizontal plane at a
0.5 m level, each half is split again, until a piece is a clean block or waste.
`scripts/guillotine_pack.py` solves that tree exactly by dynamic programming over every
sub-box, maximising class-weighted tonnage (weights 1.0, 0.85, 0.55, 0.30). A leaf is a
block when it holds no forbidden voxel; its usable height runs from the cut below it up
to the lowest surface point over its footprint, so the top of a first-lift block is
the rough bench, not a cut (Block B has 0.41 m of relief). Every other leaf that holds
rock is a waste piece that still has to be lifted. Every block's clearance to every
surface is re-measured after the solve in the same frame: the minimum over all runs is
0.15 m, the as-drawn clearance.

With uncertainty (plan on this):

""" + gtable('uncertain') + """
As drawn (best case):

""" + gtable('modelled') + """
The difference between the two tables is what the survey does not know. On B at 1.0 m
it is %.0f against %.0f t; on C %.0f against %.0f t; on A %.0f against %.0f t.

**Order of cutting and removal.** Cuts are numbered in tree order, root first, the
east (larger x) sub-box before the west. Pieces, blocks and waste alike, are then
sequenced under one rule: nothing is lifted before every piece above it that overlaps
it in plan is out; among the pieces that are ready, east first, then top down. The
sequence is checked after the solve: no piece is scheduled before a piece above it in
any run. For every block the plan lists which pieces must be out first and which of its
faces are free when its turn comes. What the plan does not judge is access: whether the
wire can be threaded, whether the loader can reach, whether a face can be turned. Those
are site decisions; the page says so where it lists the order. Horizontal cuts need a
drilled hole at each end for the wire. On B at 1.0 m with uncertainty the plan has %d
cuts, %d blocks and %d waste pieces; the first block out is number %d, a %s at x %d to
%d cm, y %d to %d cm, %.2f to %.2f m below the mean surface, after %d piece(s) above it.

**East** is taken as grid +x, the sense PARSAN's report uses on Block B ("dipping toward
increasing X (east)"). No compass bearing of the grid was recorded; the crew should
confirm with a compass before marking, and if east is another grid direction the
removal order flips but the cuts do not change.

### 7.3 How far each surface may be from where it is drawn

The 15 cm clearance of the as-drawn case is the surfaces' fit residual, not their
positional uncertainty. `scripts/uncertainty.py` builds a one-sigma vertical error at
every node of every surface from three parts: pick scatter (the plane residual),
velocity (4.2 %% of depth, the largest alternative estimate in the record), and plan
registration (%.2f m on A and C, %.2f m on B, times tan dip). Migration is carried
separately: the picks are unmigrated normal-incidence distances, and for a planar
reflector at constant velocity the true reflection point lies up-dip of the antenna by
depth x sin(dip). The offset is taken plane to plane, migrated plane minus unmigrated
plane, both fitted in absolute elevation, so it is migration alone and not the misfit
of a plane to the gridded surface; the two dips in the table are in that same frame.
The modelled surface shifted by that offset is excluded alongside the drawn one in the
uncertain case. Migration proper of the sections is PARSAN's to do; this is the
geometric consequence for a planar reflector, used as an error, not as a correction.

""" % (g('B', 'surface_1.0m')['packed_t'], g('B', 'surface_1.0m', 'modelled')['packed_t'], g('C', 'surface_1.0m')['packed_t'], g('C', 'surface_1.0m', 'modelled')['packed_t'], g('A', 'surface_1.0m')['packed_t'], g('A', 'surface_1.0m', 'modelled')['packed_t'],
       g('B', 'surface_1.0m')['n_cuts'], len(g('B', 'surface_1.0m')['boxes']), g('B', 'surface_1.0m')['n_waste'],
       first['remove_seq'], first['cls'].replace('_', ' '), int(100 * first['x0']), int(100 * first['x1']), int(100 * first['y0']), int(100 * first['y1']), first['depth_top_m'], first['depth_bottom_m'], len(first['after']),
       U['A']['A1']['sig_xy_m'], U['B']['B1']['sig_xy_m']) + utable() + """
The two A sheets and B-2 move the most under migration; their as-drawn positions
should not be cut against. B-1, C-1 and C-2 are near flat and migration moves them by
millimetres; their uncertainty is pick scatter and velocity. The velocity term alone is
12 to 13 cm at 3 m.

![Straight-cut plan, Block B, with uncertainty](figs/WEB_v8_cut.png)

"""
p = os.path.join(OUT, 'REPORT.md'); t = io.open(p, encoding='utf-8').read()
i7, i8 = t.index('## 7. Block yield'), t.index('## 8. Verification')
t = t[:i7] + sec7 + t[i8:]
# section 1 headline follows the tables
import re
t = re.sub(r"\| candidate blocks in straight cuts, chalked cracks assumed 1 m deep, surfaces kept clear by their uncertainty \| A \d+ t, B \d+ t, C \d+ t; as drawn \(best case\) A \d+, B \d+, C \d+ t\. Not a promise: section 7 \|",
           "| candidate blocks in straight cuts, chalked cracks assumed 1 m deep, surfaces kept clear by their uncertainty | A %.0f t, B %.0f t, C %.0f t; as drawn (best case) A %.0f, B %.0f, C %.0f t. Not a promise: section 7 |" % (
               g('A', 'surface_1.0m')['packed_t'], g('B', 'surface_1.0m')['packed_t'], g('C', 'surface_1.0m')['packed_t'], g('A', 'surface_1.0m', 'modelled')['packed_t'], g('B', 'surface_1.0m', 'modelled')['packed_t'], g('C', 'surface_1.0m', 'modelled')['packed_t']), t)
io.open(p, 'w', encoding='utf-8').write(t)
print('REPORT.md section 7 regenerated; 1.0 m uncertain A %.0f B %.0f C %.0f t' % (g('A', 'surface_1.0m')['packed_t'], g('B', 'surface_1.0m')['packed_t'], g('C', 'surface_1.0m')['packed_t']))
