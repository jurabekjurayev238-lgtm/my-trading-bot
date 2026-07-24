/* =====================================================================
   GRAPHIC MOTION  —  kinetic typography / motion-graphics loop  (p5.js)
   ---------------------------------------------------------------------
   Swiss / Bauhaus flavoured animated poster. Bold type, primary shapes,
   a colour wave that rolls across the headline, an orbiting geometric
   cluster, a scrolling marquee and design details (grid, corner marks,
   loop-progress dial).

   Single sketch, no build step — open index.html in a browser.

   The animation is a SEAMLESS loop: everything is a function of the loop
   position and returns exactly to its start after CONFIG.LOOP_FRAMES.

   CONTROLS
     R  new random accent order / shape arrangement (new seed)
     S  save the current frame as a PNG
     E  export the whole loop as a PNG sequence (see CONFIG.EXPORT)
     H  toggle a small seed / loop overlay

   Everything you might tweak lives in CONFIG (numbers + text) and
   C (colours). Every field is commented.
   ===================================================================== */


/* ------------------------------------------------------------------ *
 *  CONFIG — every tunable value                                       *
 * ------------------------------------------------------------------ */
const CONFIG = {
  SEED: 7,                 // arrangement seed. Press R for a new one.
  WIDTH: 1920,
  HEIGHT: 1080,
  LOOP_FRAMES: 480,        // seamless loop length (480 = 8s at 60fps)

  // ---- text (change these!) ----
  HEADLINE: ['GRAFIK', 'DIZAYN'],          // the two big lines
  LABEL: 'MOTION REEL — 01',               // small label, top-left
  MARQUEE: 'MOTION  ·  DESIGN  ·  STUDIO  ·  ',  // scrolling strip (keep trailing spaces)

  // ---- layout ----
  MARGIN: 90,              // outer margin in px
  HEADLINE_SIZE: 250,      // max headline size (auto-shrinks to fit width)
  HEADLINE_MAXW: 0.60,     // headline max width as a fraction of the canvas

  // ---- motion ----
  SWEEP_SPEED: 1,          // colour-wave passes across the headline per loop (whole number)
  BOB_CYCLES: 2,           // letter bob cycles per loop (whole number)
  BOB_AMP: 10,             // letter bob height in px
  ORBIT_CYCLES: 1,         // shape cluster orbit turns per loop (whole number)
  MARQUEE_TILES: 1,        // marquee tiles scrolled per loop (whole number)

  // ---- feature toggles ----
  SHOW_SHAPES: true,
  SHOW_MARQUEE: true,
  SHOW_GRID: true,
  SHOW_CORNERS: true,
  SHOW_DIAL: true,

  // ---- frame export (press E) ----
  EXPORT: { START: 0, END: 479, STEP: 1, PREFIX: 'gm_' },
};


/* ------------------------------------------------------------------ *
 *  C — colours as [r, g, b]                                           *
 * ------------------------------------------------------------------ */
const C = {
  PAPER:  [242, 238, 227],   // background (warm off-white)
  INK:    [20, 18, 16],      // main type / marks
  RED:    [255, 68, 56],
  BLUE:   [42, 91, 255],
  YELLOW: [255, 194, 61],
  GREEN:  [0, 192, 139],
};
// the accent wave rolls smoothly through this list and back to the start
const ACCENTS = () => [C.RED, C.BLUE, C.YELLOW, C.GREEN, C.RED];


/* ------------------------------------------------------------------ *
 *  State                                                              *
 * ------------------------------------------------------------------ */
let gLoopFrame = 0;
let phase = 0;                 // loop position 0..1
let shapes = [];               // orbiting cluster, generated in setup
let exporting = false, exportIndex = 0, showHUD = false;


/* ------------------------------------------------------------------ *
 *  Helpers                                                            *
 * ------------------------------------------------------------------ */
function col(a, alpha) {
  return (alpha === undefined) ? color(a[0], a[1], a[2]) : color(a[0], a[1], a[2], alpha);
}
// smooth 0..1 ramp
function smoothstep(e0, e1, x) {
  const t = constrain((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
}
// colour somewhere along the accent list (t in 0..1, loops back to start)
function accentAt(t) {
  const list = ACCENTS();
  const f = (t % 1) * (list.length - 1);
  const i = Math.floor(f), fr = f - i;
  const a = list[i], b = list[Math.min(i + 1, list.length - 1)];
  return [lerp(a[0], b[0], fr), lerp(a[1], b[1], fr), lerp(a[2], b[2], fr)];
}


/* ================================================================== *
 *  SETUP                                                              *
 * ================================================================== */
function setup() {
  const cnv = createCanvas(CONFIG.WIDTH, CONFIG.HEIGHT);
  cnv.parent('stage');
  pixelDensity(1);
  frameRate(60);
  textFont('Arial');   // system sans (Helvetica-like). On Linux resolves to Liberation Sans.
  generate();
}

function generate() {
  randomSeed(CONFIG.SEED);
  noiseSeed(CONFIG.SEED);
  buildShapes();
}

// The orbiting geometric cluster on the right side of the composition.
function buildShapes() {
  shapes = [];
  const kinds = ['disc', 'ring', 'square', 'triangle', 'plus', 'arc'];
  const palette = [C.RED, C.BLUE, C.YELLOW, C.GREEN, C.INK];
  const n = 6;
  for (let i = 0; i < n; i++) {
    shapes.push({
      kind: random(kinds),
      color: random(palette),
      orbitR: random(70, 230),          // distance from cluster centre
      orbitA0: random(TWO_PI),           // starting angle
      orbitDir: random() < 0.5 ? 1 : -1, // orbit direction
      spinCycles: floor(random(1, 4)),   // whole spins per loop => seamless
      spinDir: random() < 0.5 ? 1 : -1,
      size: random(40, 120),
      pulseCycles: floor(random(1, 4)),
    });
  }
  // draw big things first
  shapes.sort((a, b) => b.size - a.size);
}


/* ================================================================== *
 *  DRAW                                                               *
 * ================================================================== */
function draw() {
  gLoopFrame = exporting ? exportIndex : (frameCount % CONFIG.LOOP_FRAMES);
  phase = gLoopFrame / CONFIG.LOOP_FRAMES;

  background(col(C.PAPER));
  if (CONFIG.SHOW_GRID) drawGrid();
  if (CONFIG.SHOW_SHAPES) drawShapes();
  drawHeadline();
  if (CONFIG.SHOW_MARQUEE) drawMarquee();
  drawLabel();
  if (CONFIG.SHOW_DIAL) drawDial();
  if (CONFIG.SHOW_CORNERS) drawCorners();

  if (exporting) handleExport();
  if (showHUD && !exporting) drawHUD();
}


/* ---- background grid dots ----------------------------------------- */
function drawGrid() {
  noStroke();
  fill(C.INK[0], C.INK[1], C.INK[2], 16);
  const g = 54;
  for (let x = CONFIG.MARGIN; x <= width - CONFIG.MARGIN; x += g)
    for (let y = CONFIG.MARGIN; y <= height - CONFIG.MARGIN; y += g)
      circle(x, y, 3);
}


/* ---- orbiting geometric cluster ----------------------------------- */
function drawShapes() {
  const cx = width * 0.76, cy = height * 0.44;
  const th = TWO_PI * phase;
  for (const s of shapes) {
    const a = s.orbitA0 + s.orbitDir * CONFIG.ORBIT_CYCLES * th;
    const x = cx + Math.cos(a) * s.orbitR;
    const y = cy + Math.sin(a) * s.orbitR * 0.72;   // slightly elliptical orbit
    const spin = s.spinDir * s.spinCycles * th;
    const pulse = 1 + 0.12 * Math.sin(s.pulseCycles * th);
    push();
    translate(x, y);
    rotate(spin);
    scale(pulse);
    drawOneShape(s);
    pop();
  }
}

function drawOneShape(s) {
  const c = col(s.color), sz = s.size;
  noStroke();
  if (s.kind === 'disc') {
    fill(c); circle(0, 0, sz);
  } else if (s.kind === 'ring') {
    noFill(); stroke(c); strokeWeight(sz * 0.14); circle(0, 0, sz);
  } else if (s.kind === 'square') {
    fill(c); rectMode(CENTER); rect(0, 0, sz * 0.9, sz * 0.9);
  } else if (s.kind === 'triangle') {
    fill(c); const r = sz * 0.6;
    triangle(0, -r, r * 0.87, r * 0.5, -r * 0.87, r * 0.5);
  } else if (s.kind === 'plus') {
    fill(c); rectMode(CENTER);
    rect(0, 0, sz, sz * 0.28); rect(0, 0, sz * 0.28, sz);
  } else if (s.kind === 'arc') {
    noFill(); stroke(c); strokeWeight(sz * 0.16);
    arc(0, 0, sz, sz, 0, PI * 1.35);
  }
}


/* ---- kinetic headline --------------------------------------------- */
function drawHeadline() {
  const lines = CONFIG.HEADLINE;
  const maxW = width * CONFIG.HEADLINE_MAXW;
  textStyle(BOLD);
  textAlign(LEFT, CENTER);

  // colour wave: an x position sweeping across the headline area once (× SWEEP_SPEED) per loop
  const sweepX = -maxW * 0.2 + (maxW * 1.4) * ((phase * CONFIG.SWEEP_SPEED) % 1);
  const waveW = maxW * 0.28;                 // width of the colour influence
  const accent = accentAt(phase);            // wave colour, cycling through the palette

  const lineH = CONFIG.HEADLINE_SIZE * 1.02;
  const blockH = lineH * lines.length;
  let baseY = height * 0.5 - blockH / 2 + lineH / 2;

  const th = TWO_PI * phase;

  for (let li = 0; li < lines.length; li++) {
    const word = lines[li];
    // fit this line to maxW
    textSize(CONFIG.HEADLINE_SIZE);
    let fit = 1;
    const tw = textWidth(word);
    if (tw > maxW) fit = maxW / tw;
    const size = CONFIG.HEADLINE_SIZE * fit;
    textSize(size);

    let x = CONFIG.MARGIN;
    const y = baseY + li * lineH;
    for (let ci = 0; ci < word.length; ci++) {
      const ch = word[ci];
      const cw = textWidth(ch);
      const cxLetter = x + cw / 2;
      // colour-wave influence (distance of this letter from the sweep)
      const infl = smoothstep(waveW, 0, Math.abs(cxLetter - (CONFIG.MARGIN + sweepX)));
      // letter bob (whole cycles per loop, staggered by index)
      const bob = Math.sin(CONFIG.BOB_CYCLES * th + ci * 0.55 + li * 0.9) * CONFIG.BOB_AMP;
      const popScale = 1 + 0.10 * infl;
      const cc = lerpColor(col(C.INK), col(accent), infl);
      push();
      translate(cxLetter, y + bob);
      scale(popScale);
      fill(cc);
      noStroke();
      text(ch, -cw / 2, 0);
      pop();
      x += cw;
    }
  }
  textStyle(NORMAL);
}


/* ---- scrolling marquee -------------------------------------------- */
function drawMarquee() {
  const barH = 88;
  const y = height - CONFIG.MARGIN - barH;
  noStroke();
  fill(col(C.INK));
  rect(0, y, width, barH);

  textStyle(BOLD);
  textAlign(LEFT, CENTER);
  textSize(46);
  const s = CONFIG.MARQUEE;
  const tileW = textWidth(s);
  // scroll exactly MARQUEE_TILES tiles per loop => seamless
  let off = -(phase * CONFIG.MARQUEE_TILES * tileW) % tileW;
  fill(col(C.PAPER));
  for (let x = off - tileW; x < width + tileW; x += tileW) {
    text(s, x, y + barH / 2 + 3);
  }
  // a little accent square that rides the bar
  fill(col(accentAt(phase)));
  const sq = barH * 0.5;
  rectMode(CENTER);
  rect(width - CONFIG.MARGIN - sq, y + barH / 2, sq, sq);
  rectMode(CORNER);
  textStyle(NORMAL);
}


/* ---- small top-left label ----------------------------------------- */
function drawLabel() {
  noStroke();
  textStyle(BOLD);
  textAlign(LEFT, CENTER);
  textSize(26);
  fill(col(C.INK));
  text(CONFIG.LABEL, CONFIG.MARGIN, CONFIG.MARGIN - 8);
  // an underline that grows/shrinks with the loop
  const w = textWidth(CONFIG.LABEL);
  fill(col(accentAt(phase)));
  const g = 0.5 - 0.5 * Math.cos(TWO_PI * phase);   // 0..1..0
  rect(CONFIG.MARGIN, CONFIG.MARGIN + 12, w * g, 5);
  textStyle(NORMAL);
}


/* ---- loop-progress dial (top-right) ------------------------------- */
function drawDial() {
  const r = 30, cx = width - CONFIG.MARGIN - r, cy = CONFIG.MARGIN + r - 6;
  noFill();
  stroke(C.INK[0], C.INK[1], C.INK[2], 60);
  strokeWeight(5);
  circle(cx, cy, r * 2);
  stroke(col(accentAt(phase)));
  strokeWeight(5);
  arc(cx, cy, r * 2, r * 2, -HALF_PI, -HALF_PI + TWO_PI * phase);
  noStroke();
}


/* ---- corner registration marks ------------------------------------ */
function drawCorners() {
  stroke(col(C.INK));
  strokeWeight(2);
  const m = CONFIG.MARGIN - 34, s = 16;
  const pts = [[m, m], [width - m, m], [m, height - m], [width - m, height - m]];
  for (const [x, y] of pts) {
    line(x - s, y, x + s, y);
    line(x, y - s, x, y + s);
  }
  noStroke();
}


/* ================================================================== *
 *  Export + input                                                     *
 * ================================================================== */
function handleExport() {
  saveCanvas(CONFIG.EXPORT.PREFIX + nf(exportIndex, 4), 'png');
  exportIndex += CONFIG.EXPORT.STEP;
  if (exportIndex > CONFIG.EXPORT.END) { exporting = false; console.log('Export finished.'); }
}

function drawHUD() {
  push(); resetMatrix(); noStroke();
  fill(0, 0, 0, 150); rect(16, 16, 330, 92, 8);
  fill(240); textFont('monospace'); textAlign(LEFT, BASELINE); textSize(15);
  text(`seed ${CONFIG.SEED}`, 30, 42);
  text(`loop ${gLoopFrame}/${CONFIG.LOOP_FRAMES}  (${(CONFIG.LOOP_FRAMES/60).toFixed(1)}s)`, 30, 64);
  text(`R seed  S png  E export  H hide`, 30, 88);
  pop();
  textFont('Arial');   // system sans (Helvetica-like). On Linux resolves to Liberation Sans.
}

function keyPressed() {
  if (key === 'r' || key === 'R') { CONFIG.SEED = floor(Math.random() * 1e9); generate(); }
  else if (key === 's' || key === 'S') { saveCanvas('graphic_motion_' + CONFIG.SEED, 'png'); }
  else if (key === 'e' || key === 'E') { if (!exporting) { exporting = true; exportIndex = CONFIG.EXPORT.START; } }
  else if (key === 'h' || key === 'H') { showHUD = !showHUD; }
}
