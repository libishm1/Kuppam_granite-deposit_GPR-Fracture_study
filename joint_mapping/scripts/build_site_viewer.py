"""Build the standalone site-model viewer from site_data.json.

Writes a single HTML file with the point cloud embedded, for review as an artifact before any
decision about putting it on the public site.
"""
import json, os, io

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'

HTML = r"""<title>Kuppam Pit Model</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{
  --bg:#E4E8E5; --panel:#F2F4F2; --sunk:#DADFDB; --ink:#121A1D; --dim:#5B686B; --line:#C5CDC8;
  --ochre:#9A6C28; --ochre-soft:#B98F45; --steel:#4E7387; --moss:#5A7A60;
  --shadow:0 1px 2px rgba(18,26,29,.08),0 8px 24px rgba(18,26,29,.06);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0E1316; --panel:#151C20; --sunk:#0A0F11; --ink:#E2E8E4; --dim:#8B9A9C; --line:#233036;
    --ochre:#D6A254; --ochre-soft:#C08F3E; --steel:#7FA8BD; --moss:#7E9D83;
    --shadow:0 1px 2px rgba(0,0,0,.5),0 10px 30px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --bg:#0E1316; --panel:#151C20; --sunk:#0A0F11; --ink:#E2E8E4; --dim:#8B9A9C; --line:#233036;
  --ochre:#D6A254; --ochre-soft:#C08F3E; --steel:#7FA8BD; --moss:#7E9D83;
  --shadow:0 1px 2px rgba(0,0,0,.5),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  -webkit-font-smoothing:antialiased}
.topbar{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:9px 16px;
  background:var(--panel);border-bottom:1px solid var(--line)}
.brand{font-weight:600;font-size:14.5px;color:var(--ink);letter-spacing:-.01em}
.lang{margin-left:auto;flex:0 0 auto}
.back{color:var(--dim);text-decoration:none;font-size:12.5px;
  border-bottom:1px solid transparent;white-space:nowrap}
.back:hover{color:var(--ochre);border-bottom-color:var(--ochre)}
@media (max-width:560px){.brand{display:none}.topbar{gap:10px;padding:8px 12px}
  .jump a,.jump .here{padding:7px 11px}.back{display:none}}
.jump{display:flex;align-items:center;gap:6px;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px}
.jump .jl{color:var(--dim);letter-spacing:.08em;text-transform:uppercase;font-size:10px;margin-right:2px}
.jump a{color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:5px;
  padding:7px 14px;font-size:13px;font-weight:500;background:var(--bg)}
.jump a:hover,.jump a:focus-visible{color:var(--ochre);border-color:var(--ochre)}
.jump a:hover{color:var(--ochre);border-color:var(--ochre)}
.jump .here{color:var(--panel);background:var(--ochre);border:1px solid var(--ochre);
  border-radius:5px;padding:7px 14px;font-size:13px;font-weight:600}
.wrap{display:grid;grid-template-columns:330px 1fr;height:calc(100dvh - 47px);min-height:520px}
.rail{min-width:0;overflow-wrap:anywhere;background:var(--panel);border-right:1px solid var(--line);overflow-y:auto;
  padding-block:20px;padding-left:20px;padding-right:20px;display:flex;flex-direction:column;gap:20px}
.stage{position:relative;background:var(--sunk);overflow:hidden;min-width:0}
html,body{max-width:100%;overflow-x:hidden}
canvas{display:block;width:100%;height:100%;touch-action:none}
h1{font-size:19px;line-height:1.2;margin:0;font-weight:600;letter-spacing:-.01em;text-wrap:balance}
.sub{margin:6px 0 0;color:var(--dim);font-size:12.5px;line-height:1.5}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--dim);margin:0 0 9px}
.facts{display:grid;grid-template-columns:1fr auto;gap:7px 14px;font-size:12.5px;align-items:baseline}
.facts dt{color:var(--dim)}
.facts dd{margin:0;font-family:"IBM Plex Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;text-align:right}
.bench{display:grid;grid-template-columns:auto 1fr;gap:3px 11px;padding:10px 0;border-top:1px solid var(--line);
  align-items:baseline}
.bench:first-of-type{border-top:none}
.swatch{width:11px;height:11px;border-radius:2px;align-self:center}
.bname{font-weight:600;font-size:13px}
.bmeta{grid-column:2;color:var(--dim);font-size:11.5px;line-height:1.45;
  font-family:"IBM Plex Mono",ui-monospace,monospace}
.chip{display:inline-block;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  letter-spacing:.06em;text-transform:uppercase;padding:2px 6px;border-radius:3px;border:1px solid;margin-top:4px}
.chip.native{color:var(--ochre);border-color:var(--ochre)}
.chip.fitted{color:var(--steel);border-color:var(--steel)}
.ctl{display:flex;flex-direction:column;gap:11px}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:12.5px}
.seg{display:flex;border:1px solid var(--line);border-radius:5px;overflow:hidden}
.seg button{flex:1;appearance:none;border:0;background:transparent;color:var(--dim);cursor:pointer;
  font:500 11.5px/1 "IBM Plex Sans",sans-serif;padding:7px 9px}
.seg button[aria-pressed="true"]{background:var(--ochre);color:var(--panel)}
input[type=range]{width:130px;accent-color:var(--ochre)}
button.plain{appearance:none;border:1px solid var(--line);background:transparent;color:var(--ink);
  border-radius:5px;padding:7px 10px;font:500 11.5px/1 "IBM Plex Sans",sans-serif;cursor:pointer}
button.plain:hover{border-color:var(--ochre)}
:focus-visible{outline:2px solid var(--ochre);outline-offset:2px}
.pickout{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;line-height:1.6;
  color:var(--dim);background:var(--sunk);border:1px solid var(--line);border-radius:5px;padding:9px 10px}
.pickout b{color:var(--ink);font-weight:500}
.pickout .warn{color:var(--ochre)}
.copybox{width:100%;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;line-height:1.5;
  background:var(--sunk);color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:8px;
  resize:vertical;display:none}
.surf{display:grid;grid-template-columns:auto auto 1fr;gap:2px 9px;align-items:center;
  padding:6px 0;border-top:1px solid var(--line)}
.surf:first-child{border-top:none}
.surf .sw{width:10px;height:10px;border-radius:2px}
.surf .nm{font-size:12.5px}
.surf .dp{grid-column:3;color:var(--dim);font-size:11px;
  font-family:"IBM Plex Mono",ui-monospace,monospace}
.synced{margin:0;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;
  color:var(--dim);letter-spacing:.02em}
.synced.ok{color:var(--moss)}
.note{font-size:11.5px;line-height:1.55;color:var(--dim);border-top:1px solid var(--line);padding-top:14px}
.hint{position:absolute;left:14px;bottom:12px;font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:11px;color:var(--dim);background:color-mix(in srgb,var(--sunk) 80%,transparent);
  padding:6px 9px;border-radius:5px;pointer-events:none}
.lab{position:absolute;transform:translate(-50%,-50%);font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:11px;font-weight:500;padding:3px 7px;border-radius:4px;pointer-events:none;white-space:nowrap;
  background:color-mix(in srgb,var(--panel) 86%,transparent);border:1px solid var(--line)}
.axes{position:absolute;right:14px;bottom:12px;font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:10.5px;color:var(--dim);text-align:right;line-height:1.5;pointer-events:none}
.load{position:absolute;inset:0;display:grid;place-items:center;font-family:"IBM Plex Mono",monospace;
  font-size:12px;color:var(--dim)}
@media (max-width:760px){
  .wrap{grid-template-columns:1fr;grid-template-rows:56dvh auto;height:auto;min-height:0}
  .rail{border-right:none;border-top:1px solid var(--line);order:2}
  .stage{order:1;min-height:340px}
}
</style>

<div class="topbar">
  <span class="brand" data-i="brand"></span>
  <nav class="jump" aria-label="What you are looking at">
    <span class="jl" data-i="looking"></span>
    <a id="jA" href="__HOME__#block=A">A</a><a id="jB" href="__HOME__#block=B">B</a><a id="jC" href="__HOME__#block=C">C</a>
    <span class="here" aria-current="page" data-i="whole"></span>
  </nav>
  <a class="back" id="jhome" href="__HOME__" data-i="back"></a>
  <div class="seg lang" role="group" aria-label="Language">
    <button id="l-en" aria-pressed="true">EN</button>
    <button id="l-ta" aria-pressed="false" lang="ta">&#2980;&#2990;&#3007;&#2996;&#3021;</button>
  </div>
</div>

<div class="wrap">
  <aside class="rail">
    <div>
      <p class="eyebrow" data-i="place"></p>
      <h1 data-i="h1"></h1>
      <p class="sub" data-i="sub"></p>
    </div>

    <div>
      <p class="eyebrow" data-i="model_h"></p>
      <dl class="facts">
        <dt data-i="f_ext"></dt><dd id="f-ext">&mdash;</dd>
        <dt data-i="f_rel"></dt><dd id="f-rel">&mdash;</dd>
        <dt data-i="f_pts"></dt><dd id="f-pts">&mdash;</dd>
        <dt data-i="f_vox"></dt><dd id="f-vox">&mdash;</dd>
        <dt data-i="f_src"></dt><dd>21,561,110</dd>
      </dl>
    </div>

    <div>
      <p class="eyebrow" data-i="benches_h"></p>
      <div id="benches"></div>
    </div>

    <div>
      <p class="eyebrow" data-i="surf_h"></p>
      <div id="surflist"></div>
    </div>

    <div class="ctl">
      <p class="eyebrow" style="margin-bottom:0" data-i="view_h"></p>
      <div class="seg" role="group" aria-label="Colour">
        <button id="c-photo" aria-pressed="true" data-i="c_photo"></button>
        <button id="c-elev" aria-pressed="false" data-i="c_elev"></button>
      </div>
      <div class="row"><label for="rockop" data-i="rockop"></label>
        <input id="rockop" type="range" min="8" max="100" value="100"></div>
      <div class="row"><label for="ptsize" data-i="ptsize"></label>
        <input id="ptsize" type="range" min="4" max="26" value="11"></div>
      <div class="row"><label for="vex" data-i="vex"></label>
        <input id="vex" type="range" min="10" max="30" value="10"></div>
      <div class="row"><label for="rings" data-i="rings"></label>
        <input id="rings" type="checkbox" checked></div>
      <div class="row"><label for="boxes" data-i="boxes"></label>
        <input id="boxes" type="checkbox" checked></div>
      <div class="row"><label for="cutsOn" data-i="cutsOn"></label>
        <input id="cutsOn" type="checkbox"></div>
      <div class="row"><button class="plain" id="reset" data-i="reset"></button>
        <button class="plain" id="top" data-i="lookdown"></button></div>
    </div>

    <div id="cutnote" class="pickout" style="display:none"></div>

__PICKER_START__    <div class="ctl" style="border-top:1px solid var(--line);padding-top:16px">
      <p class="eyebrow" style="margin-bottom:0">Correct a bench</p>
      <p class="sub" style="margin:0">Pick a block, then click its four painted corners on the rock,
        starting at the origin mark (A0, B0, C0) and going round the edge. The fitted rectangle is
        checked against the surveyed size.</p>
      <div class="seg" role="group" aria-label="Which bench">
        <button id="p-A" aria-pressed="false">Block A</button>
        <button id="p-B" aria-pressed="false">Block B</button>
        <button id="p-C" aria-pressed="false">Block C</button>
      </div>
      <div class="row">
        <button class="plain" id="p-undo">Undo point</button>
        <button class="plain" id="p-clear">Clear block</button>
      </div>
      <div id="p-out" class="pickout">Choose a block, then click its corners in the model.</div>
      <textarea id="p-copy" class="copybox" readonly rows="7" aria-label="Picked corners"></textarea>
      <p id="p-sync" class="synced">Kept in this browser.</p>
    </div>__PICKER_END__

    <p class="note" data-i="note"></p>
    <p class="note" hidden>The coloured sheets are the six fracture surfaces the radar found, each drawn
      where it sits under its bench. A solid ring is the surveyed grid pinned to the corners picked
      on the rock:
      held at the picked origin, turned onto the picked first side, kept at its measured size and
      never stretched. Dashed is where the block's own frame file puts the same grid. Dots are the
      picks themselves. Outlines are the surveyed grids at their own painted origins and axes, taken
      from each block's frame file, not the model's axes. Block A and Block B are then brought into
      this frame by point matching, so they carry a few tens of centimetres of slop and are drawn
      dashed. Faint dots are corners picked by hand. Nothing here is georeferenced; east comes from
      the painted grid, confirmed on site, not from a compass.</p>
  </aside>

  <div class="stage" id="stage">
    <canvas id="gl"></canvas>
    <div class="load" id="load" data-i="loading"></div>
    <div class="hint" id="hint"></div>
    <div class="axes" id="axes"></div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){

  var T = {
    brand:['Kuppam Bench Model','\u0b95\u0bc1\u0baa\u0bcd\u0baa\u0bae\u0bcd \u0baa\u0bbe\u0bb1\u0bc8 \u0bae\u0bbe\u0b9f\u0bb2\u0bcd'],
    looking:['Looking at','\u0baa\u0bbe\u0b95\u0bcd\u0b95\u0bb1\u0ba4\u0bc1'],
    whole:['Whole pit','\u0bae\u0bca\u0ba4\u0bcd\u0ba4 \u0b95\u0bc1\u0bb5\u0bbe\u0bb0\u0bbf'],
    back:['\u2190 back to the benches','\u2190 \u0baa\u0bbe\u0bb1\u0bc8\u0b95\u0bb3\u0bc1\u0b95\u0bcd\u0b95\u0bc1'],
    place:['Kuppam, Chittoor district \u00b7 \u00a9 2026 Libish Murugesan \u00b7 GPL-3.0','\u0b95\u0bc1\u0baa\u0bcd\u0baa\u0bae\u0bcd, \u0b9a\u0bbf\u0ba4\u0bcd\u0ba4\u0bc2\u0bb0\u0bcd \u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd \u00b7 \u00a9 2026 \u0bb2\u0bbf\u0baa\u0bbf\u0bb7\u0bcd \u0bae\u0bc1\u0bb0\u0bc1\u0b95\u0bc7\u0b9a\u0ba9\u0bcd \u00b7 GPL-3.0'],
    h1:['The pit, from 21.5 million photogrammetry points','\u0bae\u0bca\u0ba4\u0bcd\u0ba4 \u0b95\u0bc1\u0bb5\u0bbe\u0bb0\u0bbf, 2.15 \u0b95\u0bcb\u0b9f\u0bbf \u0baa\u0bcb\u0b9f\u0bcd\u0b9f\u0bcb \u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf\u0b95\u0bb3\u0bcd\u0bb2 \u0b87\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1'],
    sub:['One dolerite quarry, surveyed 18 to 20 August 2026. Drag to turn, scroll to zoom, right-drag or two fingers to pan.','\u0b92\u0bb0\u0bc1 \u0b95\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bb2\u0bcd \u0b95\u0bc1\u0bb5\u0bbe\u0bb0\u0bbf, 18\u201320 \u0b86\u0b95\u0bb8\u0bcd\u0b9f\u0bcd 2026-\u0bb2 \u0b85\u0bb3\u0ba8\u0bcd\u0ba4\u0ba4\u0bc1. \u0b87\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4\u0bbe \u0ba4\u0bbf\u0bb0\u0bc1\u0bae\u0bcd\u0baa\u0bc1\u0bae\u0bcd, \u0bb8\u0bcd\u0b95\u0bcd\u0bb0\u0bcb\u0bb2\u0bcd \u0baa\u0ba3\u0bcd\u0ba3\u0bbe \u0b9c\u0bc2\u0bae\u0bcd, \u0bb0\u0bc6\u0ba3\u0bcd\u0b9f\u0bc1 \u0bb5\u0bbf\u0bb0\u0bb2\u0bcd\u0bb2 \u0ba8\u0b95\u0bb0\u0bcd\u0ba4\u0bcd\u0ba4\u0bb2\u0bbe\u0bae\u0bcd.'],
    model_h:['The model','\u0bae\u0bbe\u0b9f\u0bb2\u0bcd'],
    f_ext:['Pit extent','\u0b95\u0bc1\u0bb5\u0bbe\u0bb0\u0bbf \u0b85\u0bb3\u0bb5\u0bc1'],
    f_rel:['Relief, floor to rim','\u0ba4\u0bb0\u0bc8\u0baf\u0bbf\u0bb2\u0bbf\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1 \u0bae\u0bc7\u0bb2\u0bcd \u0bb5\u0bb0\u0bc8'],
    f_pts:['Points drawn','\u0bb5\u0bb0\u0bc8\u0b9e\u0bcd\u0b9a \u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf\u0b95\u0bb3\u0bcd'],
    f_vox:['Point spacing','\u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf \u0b87\u0b9f\u0bc8\u0bb5\u0bc6\u0bb3\u0bbf'],
    f_src:['Source vertices','\u0bae\u0bc2\u0bb2 \u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf\u0b95\u0bb3\u0bcd'],
    benches_h:['The three surveyed benches','\u0b85\u0bb3\u0ba8\u0bcd\u0ba4 \u0bae\u0bc2\u0ba3\u0bc1 \u0baa\u0bbe\u0bb1\u0bc8\u0b95\u0bb3\u0bcd'],
    surf_h:['Fracture surfaces from the radar','\u0bb0\u0bc7\u0b9f\u0bbe\u0bb0\u0bcd\u0bb2 \u0b95\u0bbf\u0b9f\u0bc8\u0b9a\u0bcd\u0b9a \u0bb5\u0bbf\u0bb0\u0bbf\u0b9a\u0bb2\u0bcd \u0ba4\u0bb3\u0b99\u0bcd\u0b95\u0bb3\u0bcd'],
    view_h:['View','\u0baa\u0bbe\u0bb0\u0bcd\u0bb5\u0bc8'],
    c_photo:['Photograph','\u0baa\u0bcb\u0b9f\u0bcd\u0b9f\u0bcb'],
    c_elev:['Elevation','\u0b89\u0baf\u0bb0\u0bae\u0bcd'],
    rockop:['Rock, see-through','\u0b95\u0bb2\u0bcd\u0bb2\u0bc1 \u0bae\u0bb1\u0bc8\u0baa\u0bcd\u0baa\u0bc1'],
    ptsize:['Point size','\u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf \u0b85\u0bb3\u0bb5\u0bc1'],
    vex:['Vertical scale','\u0b9a\u0bc6\u0b99\u0bcd\u0b95\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1 \u0baa\u0bc6\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bae\u0bcd'],
    rings:['Bench outlines','\u0baa\u0bbe\u0bb1\u0bc8 \u0b8e\u0bb2\u0bcd\u0bb2\u0bc8'],
    boxes:['Bench volume','\u0baa\u0bbe\u0bb1\u0bc8 \u0b95\u0ba9 \u0b85\u0bb3\u0bb5\u0bc1'],
    cutsOn:['Planned blocks','\u0ba4\u0bbf\u0b9f\u0bcd\u0b9f\u0bae\u0bbf\u0b9f\u0bcd\u0b9f \u0baa\u0bcd\u0bb3\u0bbe\u0b95\u0bcd'],
    reset:['Reset view','\u0baa\u0bbe\u0bb0\u0bcd\u0bb5\u0bc8\u0baf\u0bc8 \u0bae\u0bc0\u0b9f\u0bcd\u0b9f\u0bc1'],
    lookdown:['Look down','\u0bae\u0bc7\u0bb2\u0bbf\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1 \u0baa\u0bbe\u0bb0\u0bc1'],
    grid_of:['0.5 m painted grid','0.5 \u0bae\u0bc0 \u0bb5\u0bb0\u0bc8\u0b9e\u0bcd\u0b9a \u0b95\u0b9f\u0bcd\u0b9f\u0bae\u0bcd'],
    east_is:['east','\u0b95\u0bbf\u0bb4\u0b95\u0bcd\u0b95\u0bc1'],
    chip_pinned:['pinned to picks','\u0b95\u0bc1\u0bb1\u0bbf\u0b9a\u0bcd\u0b9a \u0bae\u0bc2\u0bb2\u0bc8\u0b95\u0bcd\u0b95\u0bc1'],
    chip_frame:['model frame','\u0bae\u0bbe\u0b9f\u0bb2\u0bcd \u0baa\u0bbf\u0bb0\u0bc7\u0bae\u0bcd'],
    deep:['deep','\u0b86\u0bb4\u0bae\u0bcd'],
    facets:['facets','\u0bae\u0bc1\u0b95\u0b99\u0bcd\u0b95\u0bb3\u0bcd'],
    to_:['to','\u2013'],
    blocks_w:['blocks','\u0baa\u0bcd\u0bb3\u0bbe\u0b95\u0bcd'],
    cut_h:['Planned blocks','\u0ba4\u0bbf\u0b9f\u0bcd\u0b9f\u0bae\u0bbf\u0b9f\u0bcd\u0b9f \u0baa\u0bcd\u0bb3\u0bbe\u0b95\u0bcd'],
    cut_scen:['straight-cut plan, chalked cracks assumed to reach 0.5 m, uncertainty-safe clearance','\u0ba8\u0bc7\u0bb0\u0bcd \u0bb5\u0bc6\u0b9f\u0bcd\u0b9f\u0bc1 \u0ba4\u0bbf\u0b9f\u0bcd\u0b9f\u0bae\u0bcd; \u0b9a\u0bbe\u0b95\u0bcd\u0baa\u0bc0\u0bb8\u0bcd \u0bb5\u0bbf\u0bb0\u0bbf\u0b9a\u0bb2\u0bcd 0.5 \u0bae\u0bc0 \u0b86\u0bb4\u0bae\u0bcd\u0ba9\u0bcd\u0bb1\u0bc1 \u0b8e\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0b9f\u0bcd\u0b9f\u0bc1, \u0baa\u0bbe\u0ba4\u0bc1\u0b95\u0bbe\u0baa\u0bcd\u0baa\u0bbe\u0ba9 \u0b87\u0b9f\u0bc8\u0bb5\u0bc6\u0bb3\u0bbf'],
    hint:['drag turn \u00b7 scroll zoom \u00b7 right-drag pan','\u0b87\u0bb4\u0bc1 = \u0ba4\u0bbf\u0bb0\u0bc1\u0bae\u0bcd\u0baa\u0bc1 \u00b7 \u0bb8\u0bcd\u0b95\u0bcd\u0bb0\u0bcb\u0bb2\u0bcd = \u0b9c\u0bc2\u0bae\u0bcd \u00b7 \u0bb0\u0bc8\u0b9f\u0bcd-\u0b87\u0bb4\u0bc1 = \u0ba8\u0b95\u0bb0\u0bcd\u0ba4\u0bcd\u0ba4\u0bc1'],
    ax_e:['grid +x \u2192 east','\u0b95\u0b9f\u0bcd\u0b9f\u0bae\u0bcd +x \u2192 \u0b95\u0bbf\u0bb4\u0b95\u0bcd\u0b95\u0bc1'],
    ax_s:['grid +y \u2192 south','\u0b95\u0b9f\u0bcd\u0b9f\u0bae\u0bcd +y \u2192 \u0ba4\u0bc6\u0bb1\u0bcd\u0b95\u0bc1'],
    ax_z:['z up, metres','z \u0bae\u0bc7\u0bb2\u0bc7, \u0bae\u0bc0\u0b9f\u0bcd\u0b9f\u0bb0\u0bcd'],
    loading:['unpacking the model','\u0bae\u0bbe\u0b9f\u0bb2\u0bc8 \u0ba4\u0baf\u0bbe\u0bb0\u0bcd \u0b9a\u0bc6\u0baf\u0bcd\u0bb1\u0bc7\u0ba9\u0bcd'],
    note:['The coloured sheets are the six fracture surfaces the radar found, each drawn where it sits under its bench. A solid ring is the surveyed grid pinned to the corners picked on the rock, kept at its measured size and never stretched; dashed is where the block frame file puts the same grid. Nothing here is georeferenced, and east comes from the painted grid, confirmed on site, not from a compass.','\u0bb5\u0ba3\u0bcd\u0ba3 \u0ba4\u0bb3\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0bb0\u0bc7\u0b9f\u0bbe\u0bb0\u0bcd\u0bb2 \u0b95\u0bbf\u0b9f\u0bc8\u0b9a\u0bcd\u0b9a \u0b86\u0bb1\u0bc1 \u0bb5\u0bbf\u0bb0\u0bbf\u0b9a\u0bb2\u0bcd \u0ba4\u0bb3\u0b99\u0bcd\u0b95\u0bb3\u0bcd; \u0b92\u0bb5\u0bcd\u0bb5\u0bca\u0ba9\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0b85\u0ba4\u0bcd\u0ba4 \u0baa\u0bbe\u0bb1\u0bc8\u0b95\u0bcd\u0b95\u0bc1 \u0b95\u0bc0\u0bb4 \u0b87\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0bb1 \u0b86\u0bb4\u0ba4\u0bcd\u0ba4\u0bc1\u0bb2. \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0b9a\u0bcd\u0b9a\u0bbf \u0b95\u0bcb\u0b9f\u0bc1 = \u0b95\u0bb2\u0bcd\u0bb2\u0bc1\u0bb2 \u0b95\u0bc1\u0bb1\u0bbf\u0b9a\u0bcd\u0b9a \u0bae\u0bc2\u0bb2\u0bc8\u0b95\u0bcd\u0b95\u0bc1 \u0bb5\u0b9a\u0bcd\u0b9a \u0b85\u0bb3\u0ba8\u0bcd\u0ba4 \u0b95\u0b9f\u0bcd\u0b9f\u0bae\u0bcd, \u0b85\u0bb3\u0bb5\u0bc1 \u0bae\u0bbe\u0bb1\u0bcd\u0bb1\u0bb2\u0bc8; \u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf \u0b95\u0bcb\u0b9f\u0bc1 = \u0baa\u0bbf\u0bb0\u0bc7\u0bae\u0bcd \u0b95\u0bcb\u0baa\u0bcd\u0baa\u0bc1 \u0b9a\u0bca\u0bb2\u0bcd\u0bb1 \u0b87\u0b9f\u0bae\u0bcd. \u0b87\u0ba4\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0b9c\u0bbf\u0baf\u0bcb \u0bb0\u0bc6\u0baa\u0bb0\u0ba9\u0bcd\u0bb8\u0bcd \u0b87\u0bb2\u0bcd\u0bb2; \u0b95\u0bbf\u0bb4\u0b95\u0bcd\u0b95\u0bc1 \u0bb5\u0bb0\u0bc8\u0b9e\u0bcd\u0b9a \u0b95\u0b9f\u0bcd\u0b9f\u0ba4\u0bcd\u0ba4\u0bbf\u0bb2\u0bbf\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1, \u0b95\u0bbe\u0bae\u0bcd\u0baa\u0bb8\u0bcd\u0bb2 \u0b87\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1 \u0b87\u0bb2\u0bcd\u0bb2.'],
    sn_A1:['A-1 dipping sheet','A-1 \u0b9a\u0bbe\u0baf\u0bcd\u0b9e\u0bcd\u0b9a \u0ba4\u0bb3\u0bae\u0bcd'],
    sn_A2:['A-2 inclined sheet','A-2 \u0b9a\u0bbe\u0baf\u0bcd\u0b9e\u0bcd\u0b9a \u0ba4\u0bb3\u0bae\u0bcd'],
    sn_B1:['B-1 shallow sheet','B-1 \u0bae\u0bc7\u0bb2\u0bc7 \u0b87\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0bb1 \u0ba4\u0bb3\u0bae\u0bcd'],
    sn_B2:['B-2 deep wedge','B-2 \u0b86\u0bb4\u0bae\u0bbe\u0ba9 \u0b86\u0baa\u0bcd\u0baa\u0bc1'],
    sn_C1:['C-1 shallow sheet','C-1 \u0bae\u0bc7\u0bb2\u0bc7 \u0b87\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0bb1 \u0ba4\u0bb3\u0bae\u0bcd'],
    sn_C2:['C-2 base cap','C-2 \u0b85\u0b9f\u0bbf\u0ba4\u0bcd \u0ba4\u0bb3\u0bae\u0bcd']
  };
  var lang = 'en';
  (function(){ var h=(location.hash||'').match(/lang=(en|ta)/);
    if(h){ lang=h[1]; } else { try{ var s=localStorage.getItem('kbm.lang');
      if(s==='en'||s==='ta') lang=s; }catch(e){} } })();
  function tr(k, v){ var s=(T[k]||[k,k])[lang==='ta'?1:0];
    if(v) for(var q in v) s=s.split('{'+q+'}').join(v[q]);
    return s; }
  function applyText(){
    document.documentElement.lang = (lang==='ta'?'ta':'en');
    document.querySelectorAll('[data-i]').forEach(function(el){ el.textContent = tr(el.dataset.i); });
    document.getElementById('l-en').setAttribute('aria-pressed', lang==='en');
    document.getElementById('l-ta').setAttribute('aria-pressed', lang==='ta');
    var hn=document.getElementById('hint'); if(hn) hn.textContent = tr('hint');
    var ax=document.getElementById('axes');
    if(ax) ax.innerHTML = tr('ax_e')+'<br>'+tr('ax_s')+'<br>'+tr('ax_z');
    ['A','B','C'].forEach(function(k){ var a=document.getElementById('j'+k);
      if(a) a.href = a.getAttribute('href').split('&lang=')[0] + '&lang=' + lang; });
    var hm=document.getElementById('jhome');
    if(hm) hm.href = hm.getAttribute('href').split('#')[0] + '#lang=' + lang;
  }
  function setLang(l){
    if(l===lang) return;
    try{ localStorage.setItem('kbm.lang', l); }catch(e){}
    location.hash = 'lang=' + l;
    location.reload();
  }
  document.getElementById('l-en').onclick=function(){ setLang('en'); };
  document.getElementById('l-ta').onclick=function(){ setLang('ta'); };
  applyText();

  var D = JSON.parse(document.getElementById('payload').textContent);
  function b64(s){ var raw = atob(s), n = raw.length, out = new Uint8Array(n);
    for (var i=0;i<n;i++) out[i] = raw.charCodeAt(i); return out; }

  var qbuf = b64(D.pos), q = new Uint16Array(qbuf.buffer, qbuf.byteOffset, qbuf.byteLength/2);
  var col = b64(D.col);
  var n = D.n, lo = D.lo, hi = D.hi;
  var span = [hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]];
  var mid = [(hi[0]+lo[0])/2, (hi[1]+lo[1])/2, (hi[2]+lo[2])/2];

  var pos = new Float32Array(n*3), photo = new Float32Array(n*3), elev = new Float32Array(n*3);
  // elevation ramp: pit floor slate, mid moss, rim laterite ochre, crest pale
  var stops = [[0.00,[0.12,0.17,0.20]],[0.35,[0.25,0.35,0.30]],[0.62,[0.55,0.44,0.22]],
               [0.84,[0.76,0.62,0.32]],[1.00,[0.90,0.88,0.82]]];
  function ramp(t){ for (var i=1;i<stops.length;i++){ if (t<=stops[i][0]){
      var a=stops[i-1], b=stops[i], u=(t-a[0])/(b[0]-a[0]);
      return [a[1][0]+(b[1][0]-a[1][0])*u, a[1][1]+(b[1][1]-a[1][1])*u, a[1][2]+(b[1][2]-a[1][2])*u]; } }
    return stops[stops.length-1][1]; }
  for (var i=0;i<n;i++){
    var x = lo[0] + q[i*3]  /65535*span[0];
    var y = lo[1] + q[i*3+1]/65535*span[1];
    var z = lo[2] + q[i*3+2]/65535*span[2];
    pos[i*3]=x-mid[0]; pos[i*3+1]=y-mid[1]; pos[i*3+2]=z-mid[2];
    photo[i*3]=col[i*3]/255; photo[i*3+1]=col[i*3+1]/255; photo[i*3+2]=col[i*3+2]/255;
    var c = ramp((z-lo[2])/span[2]); elev[i*3]=c[0]; elev[i*3+1]=c[1]; elev[i*3+2]=c[2];
  }

  var stage = document.getElementById('stage'), canvas = document.getElementById('gl');
  var renderer = new THREE.WebGLRenderer({canvas:canvas, antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(46, 1, 0.3, 900);
  camera.up.set(0,0,1);

  var geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos,3));
  geo.setAttribute('color', new THREE.BufferAttribute(photo.slice(),3));
  var mat = new THREE.PointsMaterial({size:0.11, vertexColors:true, sizeAttenuation:true,
                                      transparent:true, opacity:1.0, depthWrite:true});
  var cloud = new THREE.Points(geo, mat); scene.add(cloud);

  var ringGroup = new THREE.Group(); scene.add(ringGroup);
  var COLR = {C:0xB98F45, A:0x4E7387, B:0x4E7387};
  var labels = [];
  D.benches.forEach(function(b){
    var pts = b.ring.map(function(p){ return new THREE.Vector3(p[0]-mid[0], p[1]-mid[1], p[2]-mid[2]+0.06); });
    pts.push(pts[0].clone());
    var g = new THREE.BufferGeometry().setFromPoints(pts);
    var m = new THREE.LineBasicMaterial({color:COLR[b.block], depthTest:false, transparent:true});
    var line = new THREE.Line(g, m); line.renderOrder = 3;
    ringGroup.add(line);
    if (b.ring_frame){
      var fp = b.ring_frame.map(function(q){
        return new THREE.Vector3(q[0]-mid[0], q[1]-mid[1], q[2]-mid[2]+0.04); });
      fp.push(fp[0].clone());
      var fl = new THREE.Line(new THREE.BufferGeometry().setFromPoints(fp),
        new THREE.LineDashedMaterial({color:COLR[b.block], dashSize:0.45, gapSize:0.4,
                                      depthTest:false, transparent:true, opacity:0.4}));
      fl.computeLineDistances(); fl.renderOrder = 2;
      ringGroup.add(fl);
    }
    var el = document.createElement('div'); el.className='lab'; el.textContent='Block '+b.block;
    el.style.color = '#'+COLR[b.block].toString(16).padStart(6,'0');
    stage.appendChild(el);
    var c = new THREE.Vector3(); pts.slice(0,4).forEach(function(p){ c.add(p); }); c.multiplyScalar(0.25);
    labels.push({el:el, at:c, dy:({C:0, A:-19, B:19})[b.block] || 0});
  });

  // bench volume: the footprint carried down to the depth the plan works to
  var boxGroup = new THREE.Group(); scene.add(boxGroup);
  D.benches.forEach(function(b){
    var d = b.depth_m || 3.0;
    var z0 = (b.bench_z !== undefined ? b.bench_z : b.ring[0][2]);
    var top = b.ring.map(function(q){ return [q[0]-mid[0], q[1]-mid[1], z0-mid[2]]; });
    var pts = [];
    for (var i=0;i<4;i++){
      var p1 = top[i], p2 = top[(i+1)%4];
      pts.push(new THREE.Vector3(p1[0],p1[1],p1[2]-d), new THREE.Vector3(p2[0],p2[1],p2[2]-d));
      pts.push(new THREE.Vector3(p1[0],p1[1],p1[2]),   new THREE.Vector3(p1[0],p1[1],p1[2]-d));
    }
    var seg = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:COLR[b.block], transparent:true, opacity:0.45}));
    seg.renderOrder = 2;
    boxGroup.add(seg);
  });

  // the planned blocks, from the straight-cut plan
  var cutGroup = new THREE.Group(); scene.add(cutGroup);
  var CLS = {gangsaw_large:0xC98A2E, gangsaw_standard:0xB07C46,
             small_block:0x6E8FA6, cutter_block:0x6B8F72};
  (D.cuts||[]).forEach(function(c){
    var f = c.foot.map(function(q){ return [q[0]-mid[0], q[1]-mid[1]]; });
    var lo = c.z0-mid[2], hi = c.z1-mid[2];
    var v = [];
    f.forEach(function(q){ v.push(q[0],q[1],lo); });
    f.forEach(function(q){ v.push(q[0],q[1],hi); });
    var idx = [0,1,2, 0,2,3, 4,6,5, 4,7,6,
               0,4,5, 0,5,1, 1,5,6, 1,6,2, 2,6,7, 2,7,3, 3,7,4, 3,4,0];
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    var col = CLS[c.cls] || 0x6E8FA6;
    var mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({color:col, transparent:true, opacity:0.45}));
    mesh.renderOrder = 1;
    cutGroup.add(mesh);
    var eg = new THREE.LineSegments(new THREE.EdgesGeometry(g),
      new THREE.LineBasicMaterial({color:col, transparent:true, opacity:0.9}));
    eg.renderOrder = 2;
    cutGroup.add(eg);
  });

  // the radar fracture surfaces, each one its own object so it can be shown alone
  var surfGroup = new THREE.Group(); scene.add(surfGroup);
  var surfMesh = {};
  function b64f(s){ var r = atob(s), n = r.length, u = new Uint8Array(n);
    for (var i=0;i<n;i++) u[i] = r.charCodeAt(i); return u; }
  (D.surfaces||[]).forEach(function(s){
    var pb = b64f(s.pos), ib = b64f(s.idx);
    var pa = new Float32Array(pb.buffer, pb.byteOffset, pb.byteLength/4);
    var ia = new Uint32Array(ib.buffer, ib.byteOffset, ib.byteLength/4);
    var v = new Float32Array(pa.length);
    for (var i=0;i<pa.length;i+=3){
      v[i]=pa[i]-mid[0]; v[i+1]=pa[i+1]-mid[1]; v[i+2]=pa[i+2]-mid[2];
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(v,3));
    g.setIndex(new THREE.BufferAttribute(ia,1));
    g.computeVertexNormals();
    var col = new THREE.Color(s.colour);
    var grp = new THREE.Group();
    grp.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({color:col, transparent:true,
      opacity:0.62, side:THREE.DoubleSide, depthWrite:false})));
    var wire = new THREE.LineSegments(new THREE.WireframeGeometry(g),
      new THREE.LineBasicMaterial({color:col, transparent:true, opacity:0.16}));
    grp.add(wire);
    grp.renderOrder = 1;
    surfGroup.add(grp);
    surfMesh[s.id] = grp;
  });

  // orbit
  var tgt = new THREE.Vector3(0,0,0);
  var R = Math.max(span[0],span[1])*1.25, az = -0.65, po = 1.03, R0=R, az0=az, po0=po;
  function place(){
    var sp = Math.sin(po), cp = Math.cos(po);
    camera.position.set(tgt.x + R*sp*Math.cos(az), tgt.y + R*sp*Math.sin(az), tgt.z + R*cp);
    camera.lookAt(tgt);
  }
  var drag=null;
  canvas.addEventListener('pointerdown', function(e){
    canvas.setPointerCapture(e.pointerId);
    drag={x:e.clientX, y:e.clientY, pan:(e.button===2||e.shiftKey)};
  });
  canvas.addEventListener('contextmenu', function(e){ e.preventDefault(); });
  canvas.addEventListener('pointermove', function(e){
    if(!drag) return;
    var dx=e.clientX-drag.x, dy=e.clientY-drag.y; drag.x=e.clientX; drag.y=e.clientY;
    if(drag.pan){
      var right=new THREE.Vector3(), up=new THREE.Vector3();
      camera.getWorldDirection(right); right.cross(camera.up).normalize();
      up.copy(camera.up).normalize();
      var k=R*0.0016;
      tgt.addScaledVector(right, -dx*k); tgt.addScaledVector(up, dy*k);
    } else {
      az -= dx*0.006; po = Math.max(0.08, Math.min(Math.PI-0.08, po - dy*0.006));
    }
    place();
  });
  ['pointerup','pointercancel','pointerleave'].forEach(function(t){
    canvas.addEventListener(t, function(){ drag=null; }); });
  canvas.addEventListener('wheel', function(e){
    e.preventDefault(); R = Math.max(6, Math.min(340, R*(1+Math.sign(e.deltaY)*0.11))); place();
  }, {passive:false});
  var pinch=null;
  canvas.addEventListener('touchmove', function(e){
    if(e.touches.length!==2) return; e.preventDefault();
    var d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
    if(pinch) R = Math.max(6, Math.min(340, R*pinch/d));
    pinch=d;
  }, {passive:false});
  canvas.addEventListener('touchend', function(){ pinch=null; });

  function resize(){
    var w=stage.clientWidth, h=stage.clientHeight;
    renderer.setSize(w,h,false); camera.aspect=w/Math.max(h,1); camera.updateProjectionMatrix();
  }
  addEventListener('resize', resize);

  var v = new THREE.Vector3();
  function tick(){
    renderer.render(scene,camera);
    labels.forEach(function(L){
      v.copy(L.at); v.z *= cloud.scale.z; v.project(camera);
      var vis = v.z < 1;
      L.el.style.display = (vis && ringOn) ? 'block' : 'none';
      L.el.style.left = ((v.x*0.5+0.5)*stage.clientWidth)+'px';
      L.el.style.top  = ((-v.y*0.5+0.5)*stage.clientHeight + L.dy)+'px';
    });
    requestAnimationFrame(tick);
  }

  // controls
  var ringOn = true;
  function press(a,b,on){ a.setAttribute('aria-pressed', on?'true':'false');
                          b.setAttribute('aria-pressed', on?'false':'true'); }
  var cp=document.getElementById('c-photo'), ce=document.getElementById('c-elev');
  function setCol(which){
    geo.getAttribute('color').array.set(which==='photo'?photo:elev);
    geo.getAttribute('color').needsUpdate = true;
    press(cp,ce,which==='photo');
  }
  cp.onclick=function(){ setCol('photo'); }; ce.onclick=function(){ setCol('elev'); };
  document.getElementById('ptsize').oninput=function(e){ mat.size = e.target.value/100; };
  document.getElementById('rockop').oninput=function(e){
    var o = e.target.value/100; mat.opacity = o; mat.depthWrite = (o > 0.97);
  };
  document.getElementById('vex').oninput=function(e){
    var s=e.target.value/10; cloud.scale.z=s; ringGroup.scale.z=s; boxGroup.scale.z=s;
    cutGroup.scale.z=s; surfGroup.scale.z=s;
  };
  document.getElementById('rings').onchange=function(e){ ringOn=e.target.checked; ringGroup.visible=ringOn; };
  document.getElementById('boxes').onchange=function(e){ boxGroup.visible=e.target.checked; };
  document.getElementById('cutsOn').onchange=function(e){ cutGroup.visible=e.target.checked; };
  document.getElementById('reset').onclick=function(){ R=R0; az=az0; po=po0; tgt.set(0,0,0); place(); };
  document.getElementById('top').onclick=function(){ po=0.09; az=-Math.PI/2; place(); };

  if ((D.cuts||[]).length){
    var byb = {}, tot = 0, vol = 0;
    D.cuts.forEach(function(c){ byb[c.block] = (byb[c.block]||0) + 1; tot += c.t; vol += (c.m3||0); });
    var el = document.getElementById('cutnote');
    el.style.display = 'block';
    el.innerHTML = '<b>' + tr('cut_h') + '</b><br>' + D.cuts.length + ' ' + tr('blocks_w') + ' &middot; '
      + Math.round(vol) + ' m\u00b3 (' + Math.round(tot) + ' t)'
      + '<br>A ' + (byb.A||0) + ' &middot; B ' + (byb.B||0) + ' &middot; C ' + (byb.C||0)
      + '<br><span style="color:var(--dim)">' + tr('cut_scen') + '</span>';
  }

  (D.surfaces||[]).forEach(function(s){
    var row = document.createElement('label');
    row.className = 'surf';
    row.setAttribute('for', 'sf-'+s.id);
    row.innerHTML = '<input id="sf-'+s.id+'" type="checkbox" checked>'
      + '<span class="sw" style="background:'+s.colour+'"></span>'
      + '<span class="nm">'+tr('sn_'+s.id)+'</span>'
      + '<span class="dp">'+s.depth_range[0].toFixed(2)+' '+tr('to_')+' '+s.depth_range[1].toFixed(2)
      + ' m '+tr('deep')+' &middot; '+s.n_triangles.toLocaleString('en-GB')+' '+tr('facets')+'</span>';
    document.getElementById('surflist').appendChild(row);
    row.querySelector('input').onchange = function(e){
      surfMesh[s.id].visible = e.target.checked;
    };
  });

  // readouts
  var f=function(id,t){ document.getElementById(id).textContent=t; };
  f('f-ext', span[0].toFixed(1)+' \u00d7 '+span[1].toFixed(1)+' m');
  f('f-rel', span[2].toFixed(1)+' m');
  f('f-pts', n.toLocaleString('en-GB'));
  f('f-vox', D.vox_cm.toFixed(0)+' cm');
  var GRID={A:'5.5 \u00d7 5.5 m',B:'9.5 \u00d7 6.0 m',C:'7.0 \u00d7 8.0 m'};
  var host=document.getElementById('benches');
  D.benches.forEach(function(b){
    var d=document.createElement('div'); d.className='bench';
    var native = String(b.chip || '').indexOf('fitted') < 0;
    d.innerHTML = '<span class="swatch" style="background:#'+COLR[b.block].toString(16).padStart(6,'0')+'"></span>'
      + '<span class="bname">Block '+b.block+'</span>'
      + '<span class="bmeta">'+GRID[b.block]+' &middot; '+tr('grid_of')+' &middot; '+tr('east_is')+' '+b.east
      + '<br><span class="chip '+(native?'native':'fitted')+'">'
      + (b.chip==='pinned to picks'?tr('chip_pinned'):(b.chip==='model frame'?tr('chip_frame'):(b.chip||''))) + '</span></span>';
    host.appendChild(d);
  });

  // reference: the corners picked by hand, drawn hollow so the surveyed rectangles read on top
  if (D.picked){
    var REF = {A:0xE07A3C, B:0x3FA7CC, C:0x5FBE72};
    Object.keys(D.picked).forEach(function(k){
      (D.picked[k]||[]).slice(0, 1).forEach(function(p){       // the origin mark only
        var m = new THREE.MeshBasicMaterial({color:REF[k], depthTest:false, transparent:true, opacity:.8});
        var s = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 10), m);
        s.renderOrder = 4;
        s.position.set(p[0]-mid[0], p[1]-mid[1], p[2]-mid[2]);
        scene.add(s);
      });
    });
  }

  // ---- corner picking ------------------------------------------------------------------
  var PICKCOL = {A:0xE07A3C, B:0x3FA7CC, C:0x5FBE72};
  var SIZE = {A:[5.5,5.5], B:[9.5,6.0], C:[7.0,8.0]};
  var picks = {A:[], B:[], C:[]}, active = null;
  try { var sv = JSON.parse(localStorage.getItem('kuppam_picks') || 'null'); if (sv) picks = sv; }
  catch (e) {}
  var markers = new THREE.Group(); scene.add(markers);
  var fitted = new THREE.Group(); scene.add(fitted);
  var ray = new THREE.Raycaster(); ray.params.Points.threshold = 0.16;

  var store = null;
  function setSync(msg, ok){
    var el = document.getElementById('p-sync');
    if (el){ el.textContent = msg; el.className = 'synced' + (ok ? ' ok' : ''); }
  }
  // The surveyed rectangle placed on the picked origin, turned to the picked first side, kept at its
  // measured size. Rotation and translation only: the grid is never stretched to reach a corner.
  function anchored(k){
    var P = picks[k];
    if (!P || P.length < 2) return null;
    var W = SIZE[k][0], H = SIZE[k][1];
    var d = [P[1][0]-P[0][0], P[1][1]-P[0][1]];
    var L = Math.hypot(d[0], d[1]);
    if (L < 0.2) return null;
    var u = [d[0]/L, d[1]/L];
    var first = (Math.abs(L-H) <= Math.abs(L-W)) ? H : W;   // which surveyed side was walked first
    var other = (first === H) ? W : H;
    var v = [-u[1], u[0]];                                   // turn left off the first side
    if (P.length >= 3){                                      // unless the third corner says right
      var w = [P[2][0]-P[1][0], P[2][1]-P[1][1]];
      if (w[0]*v[0] + w[1]*v[1] < 0) v = [u[1], -u[0]];
    }
    var z = P.reduce(function(s,q){ return s+q[2]; }, 0) / P.length;
    var o = [P[0][0], P[0][1]];
    return [[o[0], o[1], z],
            [o[0]+u[0]*first, o[1]+u[1]*first, z],
            [o[0]+u[0]*first+v[0]*other, o[1]+u[1]*first+v[1]*other, z],
            [o[0]+v[0]*other, o[1]+v[1]*other, z]];
  }

  function save(){
    try { localStorage.setItem('kuppam_picks', JSON.stringify(picks)); } catch (e) {}
    if (store){
      store.doc('picks/blocks').set({A:picks.A, B:picks.B, C:picks.C, updated:new Date().toISOString()})
        .then(function(){ setSync('Saved where Claude can read it.', true); })
        .catch(function(){ setSync('Kept in this browser; the shared copy refused the write.', false); });
    }
  }
  function nPicks(o){ return (o && o.A ? o.A.length : 0) + (o && o.B ? o.B.length : 0)
                           + (o && o.C ? o.C.length : 0); }
  if (window.claude && claude.use) claude.use('db').then(function(db){
    if (!db) { setSync('Kept in this browser only.', false); return; }
    store = db;
    var ref = db.doc('picks/blocks');
    ref.get().then(function(doc){
      var remote = doc && doc.data ? doc.data : doc;
      if (nPicks(remote) === 0 && nPicks(picks) > 0){
        save();                                   // carry this browser's picks up to the shared copy
      } else if (nPicks(remote) > 0){
        picks = {A:remote.A||[], B:remote.B||[], C:remote.C||[]};
        try { localStorage.setItem('kuppam_picks', JSON.stringify(picks)); } catch (e) {}
        setSync('Saved where Claude can read it.', true);
        redraw();
      } else {
        setSync('Ready to save where Claude can read it.', false);
      }
    }).catch(function(){ setSync('Kept in this browser only.', false); });
  }).catch(function(){ setSync('Kept in this browser only.', false); });
  function hex(c){ return '#' + c.toString(16).padStart(6,'0'); }

  function redraw(){
    while (markers.children.length) markers.remove(markers.children[0]);
    while (fitted.children.length) fitted.remove(fitted.children[0]);
    ['A','B','C'].forEach(function(k){
      picks[k].forEach(function(p, i){
        if (i > 0 && active !== k) return;                      // only the origin unless picking
        var m = new THREE.MeshBasicMaterial({color:PICKCOL[k], depthTest:false, transparent:true,
                                             opacity: i === 0 ? 1 : 0.7});
        var s = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 10), m);
        s.renderOrder = 6;
        s.position.set(p[0]-mid[0], p[1]-mid[1], p[2]-mid[2]);
        markers.add(s);
      });
      if (picks[k].length >= 2 && active === k){
        var anc = anchored(k);
        if (anc){
          var ring = anc.map(function(p){
            return new THREE.Vector3(p[0]-mid[0], p[1]-mid[1], p[2]-mid[2]+0.05); });
          ring.push(ring[0].clone());
          var ln = new THREE.Line(new THREE.BufferGeometry().setFromPoints(ring),
            new THREE.LineBasicMaterial({color:PICKCOL[k], depthTest:false, transparent:true}));
          ln.renderOrder = 5;
          fitted.add(ln);
        }
      }
    });
    report();
  }

  function report(){
    var out = document.getElementById('p-out'), box = document.getElementById('p-copy');
    if (!out || !box) return;                    // the published copy carries no picking tool
    var lines = [], copy = [];
    ['A','B','C'].forEach(function(k){
      var P = picks[k];
      if (!P.length) return;
      lines.push('<b style="color:' + hex(PICKCOL[k]) + '">Block ' + k + '</b>  ' + P.length + ' of 4');
      copy.push('Block ' + k);
      P.forEach(function(p, i){
        copy.push('  ' + (i === 0 ? 'origin' : 'corner') + ' ' + (i+1) + ':  x ' + p[0].toFixed(2)
                  + '   y ' + p[1].toFixed(2) + '   z ' + p[2].toFixed(2));
      });
      if (P.length === 4){
        var e1 = Math.hypot(P[1][0]-P[0][0], P[1][1]-P[0][1]);
        var e2 = Math.hypot(P[3][0]-P[0][0], P[3][1]-P[0][1]);
        var e3 = Math.hypot(P[2][0]-P[1][0], P[2][1]-P[1][1]);
        var e4 = Math.hypot(P[3][0]-P[2][0], P[3][1]-P[2][1]);
        var w = SIZE[k];
        var gotL = Math.max(e1, e2), gotS = Math.min(e1, e2);
        var wantL = Math.max(w[0], w[1]), wantS = Math.min(w[0], w[1]);
        var dL = gotL - wantL, dS = gotS - wantS;
        var bad = Math.abs(dL) > 0.6 || Math.abs(dS) > 0.6;
        var ang = (Math.atan2(P[1][1]-P[0][1], P[1][0]-P[0][0]) * 180 / Math.PI + 360) % 360;
        lines.push('&nbsp; from the origin: ' + e1.toFixed(2) + ' m then ' + e2.toFixed(2) + ' m');
        lines.push('&nbsp; opposite sides: ' + e3.toFixed(2) + ' and ' + e4.toFixed(2) + ' m');
        lines.push('&nbsp; surveyed ' + w[0].toFixed(1) + ' \u00d7 ' + w[1].toFixed(1) + ' m &mdash; '
          + (bad ? '<span class="warn">off by ' + dL.toFixed(2) + ' and ' + dS.toFixed(2) + ' m</span>'
                 : 'fits inside 60 cm'));
        lines.push('&nbsp; first side bears ' + ang.toFixed(1) + '\u00b0 from model +x');
        copy.push('  side 1: ' + e1.toFixed(2) + ' m at ' + ang.toFixed(1) + ' deg from model +x');
        copy.push('  side 2: ' + e2.toFixed(2) + ' m   surveyed ' + w[0] + ' x ' + w[1] + ' m');
        var anc = anchored(k);
        if (anc){
          var errs = [1,2,3].map(function(i){
            return Math.hypot(anc[i][0]-P[i][0], anc[i][1]-P[i][1]); });
          lines.push('&nbsp; grid pinned to your origin: other corners land '
            + errs.map(function(v){ return v.toFixed(2); }).join(', ') + ' m away');
          copy.push('  grid pinned to origin, corner gaps: '
            + errs.map(function(v){ return v.toFixed(2); }).join(', ') + ' m');
        }
      }
      lines.push('');
    });
    out.innerHTML = lines.length ? lines.join('<br>')
      : 'Choose a block, then click its corners in the model.';
    box.value = copy.length
      ? 'Kuppam pit model, corners picked in the model frame, metres\n' + copy.join('\n') : '';
    box.style.display = copy.length ? 'block' : 'none';
  }

  function setActive(k){
    active = (active === k) ? null : k;
    ['A','B','C'].forEach(function(x){
      var b = document.getElementById('p-'+x);
      if (b) b.setAttribute('aria-pressed', x === active ? 'true' : 'false');
    });
    canvas.style.cursor = active ? 'crosshair' : '';
    if (active){
      document.getElementById('vex').value = 10;
      cloud.scale.z = 1; ringGroup.scale.z = 1; boxGroup.scale.z = 1; cutGroup.scale.z = 1;
      surfGroup.scale.z = 1;
    }
  }
  ['A','B','C'].forEach(function(k){
    var b = document.getElementById('p-'+k);
    if (b) b.onclick = function(){ setActive(k); };
  });
  {
    var u = document.getElementById('p-undo'), c = document.getElementById('p-clear');
    if (u) u.onclick = function(){ if (active && picks[active].length){ picks[active].pop(); save(); redraw(); } };
    if (c) c.onclick = function(){ if (active){ picks[active] = []; save(); redraw(); } };
  }

  var pdown = null;
  canvas.addEventListener('pointerdown', function(e){ pdown = {x:e.clientX, y:e.clientY}; });
  canvas.addEventListener('pointerup', function(e){
    var d = pdown; pdown = null;
    if (!active || !d) return;
    if (Math.hypot(e.clientX - d.x, e.clientY - d.y) > 4) return;
    var r = canvas.getBoundingClientRect();
    var nd = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1,
                               -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(nd, camera);
    var hit = ray.intersectObject(cloud, false);
    if (!hit.length) return;
    var q = hit[0].point;
    if (picks[active].length >= 4) picks[active] = [];
    picks[active].push([q.x + mid[0], q.y + mid[1], q.z + mid[2]]);
    save(); redraw();
  });

  redraw();
  applyText();
  resize(); place(); document.getElementById('load').remove(); tick();
})();
</script>
"""

if __name__ == '__main__':
    js = io.open(os.path.join(OUT, os.environ.get('SITE_IN_JSON', 'site_data.json')), encoding='utf-8').read()
    home = os.environ.get('SITE_HOME',
        'https://libishm1.github.io/Kuppam_granite-deposit_GPR-Fracture_study/index.html')
    keep = os.environ.get('SITE_PICKER', '1') == '1'
    html = HTML
    i = html.index('__PICKER_START__'); j = html.index('__PICKER_END__') + len('__PICKER_END__')
    html = (html[:i] + html[j:]) if not keep else html.replace('__PICKER_START__', '').replace('__PICKER_END__', '')
    html = html.replace('__HOME__', home).replace('__DATA__', js)
    p = os.path.join(OUT, os.environ.get('SITE_OUT_HTML', 'site_viewer.html'))
    io.open(p, 'w', encoding='utf-8').write(html)
    print('wrote %s  %.1f MB' % (p, len(html) / 1e6))
