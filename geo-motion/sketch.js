/* =====================================================================
   GEO MOTION  —  complex kaleidoscopic geometric loop  (p5.js)
   ---------------------------------------------------------------------
   A dense, colourful mandala: K-fold kaleidoscopic symmetry, rotating
   polygon rings, an animated spoke of morphing shapes, a glowing
   spirograph rose, and a rainbow (HSB) hue that cycles over the loop.

   Single sketch, no build step — open index.html in a browser.

   The animation is a SEAMLESS loop: every rotation/oscillation runs a
   whole number of cycles per loop and the hue advances a whole number of
   full rainbows, so it returns exactly to its start after LOOP_FRAMES.

   CONTROLS
     R  new arrangement (random seed)
     S  save the current frame as a PNG
     E  export the whole loop as a PNG sequence (see CONFIG.EXPORT)
     H  toggle a small seed / loop overlay

   Tunables live in CONFIG; colours are generated in HSB so the whole
   thing is "rang-barang" (multi-colour) by design.
   ===================================================================== */


/* ------------------------------------------------------------------ *
 *  CONFIG — every tunable value                                       *
 * ------------------------------------------------------------------ */
const CONFIG = {
  SEED: 21,
  WIDTH: 1920,
  HEIGHT: 1080,
  LOOP_FRAMES: 600,        // 10s at 60fps

  SYMMETRY: 12,            // K-fold kaleidoscope (try 6, 8, 10, 12, 16)
  MIRROR: true,            // mirror alternate segments (true kaleidoscope)

  HUE_CYCLES: 1,           // full rainbow cycles per loop (whole number)
  GLOBAL_SPIN: 1,          // turns the whole mandala makes per loop (whole number)

  // spoke of shapes drawn along one radius, then replicated by symmetry
  SPOKE_COUNT: 10,         // shapes per spoke
  SPOKE_R0: 70,            // inner radius
  SPOKE_R1: 560,           // outer radius

  // concentric polygon rings
  RINGS: 8,
  RING_R0: 110,
  RING_R1: 640,

  // spirograph rose overlay
  ROSE_PETALS: 7,          // number of lobes
  ROSE_R: 430,
  ROSE_SPIN: 2,            // turns per loop (whole number)
  ROSE_DOTS: 520,          // resolution

  // feature toggles
  SHOW_RINGS: true,
  SHOW_MANDALA: true,
  SHOW_ROSE: true,
  SHOW_CORE: true,         // pulsing centre core
  SHOW_VIGNETTE: true,

  BG_HUE: 245,             // background hue (deep indigo)
  BG_SAT: 55,
  BG_BRI: 7,

  EXPORT: { START: 0, END: 599, STEP: 1, PREFIX: 'geo_' },
};


/* ------------------------------------------------------------------ *
 *  State                                                              *
 * ------------------------------------------------------------------ */
let gLoopFrame = 0, phase = 0;
let spoke = [];      // shape descriptors along one radius
let rings = [];      // ring descriptors
let exporting = false, exportIndex = 0, showHUD = false;


/* ------------------------------------------------------------------ *
 *  Helpers                                                            *
 * ------------------------------------------------------------------ */
function hueWrap(h) { return ((h % 360) + 360) % 360; }
function th() { return TWO_PI * phase; }        // loop angle
// rainbow offset that advances a whole number of full turns per loop
function hueShift() { return 360 * CONFIG.HUE_CYCLES * phase; }

function polygon(x, y, r, sides, rot) {
  beginShape();
  for (let i = 0; i < sides; i++) {
    const a = rot + (TWO_PI * i) / sides;
    vertex(x + Math.cos(a) * r, y + Math.sin(a) * r);
  }
  endShape(CLOSE);
}


/* ================================================================== *
 *  SETUP                                                              *
 * ================================================================== */
function setup() {
  const cnv = createCanvas(CONFIG.WIDTH, CONFIG.HEIGHT);
  cnv.parent('stage');
  pixelDensity(1);
  frameRate(60);
  colorMode(HSB, 360, 100, 100, 100);
  generate();
}

function generate() {
  randomSeed(CONFIG.SEED);
  noiseSeed(CONFIG.SEED);
  buildSpoke();
  buildRings();
}

const KINDS = ['disc', 'ring', 'square', 'triangle', 'poly', 'star', 'plus'];

function buildSpoke() {
  spoke = [];
  for (let i = 0; i < CONFIG.SPOKE_COUNT; i++) {
    const t = i / (CONFIG.SPOKE_COUNT - 1);
    spoke.push({
      r: lerp(CONFIG.SPOKE_R0, CONFIG.SPOKE_R1, t),
      kind: random(KINDS),
      sides: floor(random(3, 8)),
      size: lerp(70, 26, t) * random(0.7, 1.3),   // smaller toward the rim
      spinCycles: floor(random(1, 5)) * (random() < 0.5 ? 1 : -1),
      oscCycles: floor(random(1, 4)),
      oscAmp: random(6, 26),
      pulseCycles: floor(random(1, 4)),
      hue0: random(360),
    });
  }
}

function buildRings() {
  rings = [];
  for (let i = 0; i < CONFIG.RINGS; i++) {
    const t = i / (CONFIG.RINGS - 1);
    rings.push({
      radius: lerp(CONFIG.RING_R0, CONFIG.RING_R1, t),
      sides: floor(random(3, 13)),
      spinCycles: floor(random(1, 4)) * (random() < 0.5 ? 1 : -1),
      hue0: random(360),
      weight: random(2, 6),
    });
  }
}


/* ================================================================== *
 *  DRAW                                                               *
 * ================================================================== */
function draw() {
  gLoopFrame = exporting ? exportIndex : (frameCount % CONFIG.LOOP_FRAMES);
  phase = gLoopFrame / CONFIG.LOOP_FRAMES;

  drawBackground();

  push();
  translate(width / 2, height / 2);
  rotate(TWO_PI * CONFIG.GLOBAL_SPIN * phase);   // whole-mandala slow spin

  if (CONFIG.SHOW_RINGS) drawRings();
  if (CONFIG.SHOW_MANDALA) drawMandala();
  if (CONFIG.SHOW_ROSE) drawRose();
  if (CONFIG.SHOW_CORE) drawCore();

  pop();

  if (CONFIG.SHOW_VIGNETTE) drawVignette();

  if (exporting) handleExport();
  if (showHUD && !exporting) drawHUD();
}


/* ---- background ---------------------------------------------------- */
function drawBackground() {
  const g = drawingContext.createRadialGradient(
    width / 2, height / 2, 60, width / 2, height / 2, height * 0.75);
  const c1 = color(CONFIG.BG_HUE, CONFIG.BG_SAT, CONFIG.BG_BRI + 6);
  const c2 = color(CONFIG.BG_HUE, CONFIG.BG_SAT, CONFIG.BG_BRI);
  g.addColorStop(0, c1.toString());
  g.addColorStop(1, c2.toString());
  drawingContext.fillStyle = g;
  drawingContext.fillRect(0, 0, width, height);
}


/* ---- concentric polygon rings ------------------------------------- */
function drawRings() {
  blendMode(ADD);
  noFill();
  for (const rg of rings) {
    const hue = hueWrap(rg.hue0 + hueShift());
    stroke(hue, 85, 100, 55);
    strokeWeight(rg.weight);
    polygon(0, 0, rg.radius, rg.sides, TWO_PI * rg.spinCycles * phase);
  }
  blendMode(BLEND);
}


/* ---- K-fold kaleidoscopic mandala --------------------------------- */
function drawMandala() {
  const K = CONFIG.SYMMETRY;
  for (let k = 0; k < K; k++) {
    push();
    rotate((TWO_PI * k) / K);
    if (CONFIG.MIRROR && (k % 2 === 1)) scale(1, -1);
    drawSpoke();
    pop();
  }
}

function drawSpoke() {
  // connecting spine
  blendMode(ADD);
  stroke(hueWrap(hueShift()), 40, 100, 18);
  strokeWeight(2);
  let prev = null;
  for (const e of spoke) {
    const r = e.r + Math.sin(TWO_PI * e.oscCycles * phase) * e.oscAmp;
    if (prev !== null) line(prev, 0, r, 0);
    prev = r;
  }
  blendMode(BLEND);

  for (const e of spoke) {
    const r = e.r + Math.sin(TWO_PI * e.oscCycles * phase) * e.oscAmp;
    const hue = hueWrap(e.hue0 + hueShift());
    const pulse = 1 + 0.22 * Math.sin(TWO_PI * e.pulseCycles * phase);
    const rot = TWO_PI * e.spinCycles * phase;
    push();
    translate(r, 0);
    rotate(rot);
    scale(pulse);
    drawShape(e, hue);
    pop();
  }
}

function drawShape(e, hue) {
  const s = e.size;
  blendMode(ADD);
  if (e.kind === 'disc') {
    noStroke(); fill(hue, 85, 100, 80); circle(0, 0, s);
    fill(hueWrap(hue + 40), 90, 100, 90); circle(0, 0, s * 0.5);
  } else if (e.kind === 'ring') {
    noFill(); stroke(hue, 85, 100, 85); strokeWeight(s * 0.16); circle(0, 0, s);
  } else if (e.kind === 'square') {
    noStroke(); fill(hue, 85, 100, 80); rectMode(CENTER); rect(0, 0, s * 0.9, s * 0.9);
  } else if (e.kind === 'triangle') {
    noStroke(); fill(hue, 90, 100, 82); polygon(0, 0, s * 0.62, 3, 0);
  } else if (e.kind === 'poly') {
    noStroke(); fill(hue, 85, 100, 78); polygon(0, 0, s * 0.6, e.sides, 0);
  } else if (e.kind === 'star') {
    noStroke(); fill(hue, 90, 100, 85); star(0, 0, s * 0.28, s * 0.6, e.sides);
  } else if (e.kind === 'plus') {
    noStroke(); fill(hue, 85, 100, 82); rectMode(CENTER);
    rect(0, 0, s, s * 0.3); rect(0, 0, s * 0.3, s);
  }
  blendMode(BLEND);
}

function star(x, y, r1, r2, pts) {
  beginShape();
  for (let i = 0; i < pts * 2; i++) {
    const rr = (i % 2 === 0) ? r2 : r1;
    const a = (PI * i) / pts;
    vertex(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  endShape(CLOSE);
}


/* ---- glowing spirograph rose overlay ------------------------------ */
function drawRose() {
  blendMode(ADD);
  noStroke();
  const N = CONFIG.ROSE_DOTS, k = CONFIG.ROSE_PETALS;
  const baseRot = TWO_PI * CONFIG.ROSE_SPIN * phase;
  for (let i = 0; i < N; i++) {
    const a = (TWO_PI * i) / N;
    const rr = CONFIG.ROSE_R * (0.55 + 0.45 * Math.cos(k * a));
    const x = Math.cos(a + baseRot) * rr;
    const y = Math.sin(a + baseRot) * rr;
    const hue = hueWrap((a / TWO_PI) * 360 + hueShift() * 2);
    fill(hue, 80, 100, 55);
    circle(x, y, 6);
  }
  blendMode(BLEND);
}


/* ---- pulsing centre core ------------------------------------------ */
function drawCore() {
  blendMode(ADD);
  noStroke();
  const p2 = 0.5 - 0.5 * Math.cos(TWO_PI * 2 * phase);
  for (let i = 6; i >= 1; i--) {
    const hue = hueWrap(hueShift() + i * 12);
    fill(hue, 70, 100, 12 + p2 * 8);
    circle(0, 0, (30 + i * 22) * (1 + p2 * 0.3));
  }
  blendMode(BLEND);
}


/* ---- vignette ------------------------------------------------------ */
function drawVignette() {
  const g = drawingContext.createRadialGradient(
    width / 2, height / 2, height * 0.28, width / 2, height / 2, height * 0.75);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.62)');
  drawingContext.fillStyle = g;
  drawingContext.fillRect(0, 0, width, height);
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
  push(); resetMatrix(); colorMode(RGB, 255); noStroke();
  fill(0, 0, 0, 150); rect(16, 16, 330, 92, 8);
  fill(240); textFont('monospace'); textAlign(LEFT, BASELINE); textSize(15);
  text(`seed ${CONFIG.SEED}  K=${CONFIG.SYMMETRY}`, 30, 42);
  text(`loop ${gLoopFrame}/${CONFIG.LOOP_FRAMES}  (${(CONFIG.LOOP_FRAMES/60).toFixed(1)}s)`, 30, 64);
  text(`R seed  S png  E export  H hide`, 30, 88);
  pop();
  colorMode(HSB, 360, 100, 100, 100);
}

function keyPressed() {
  if (key === 'r' || key === 'R') { CONFIG.SEED = floor(Math.random() * 1e9); generate(); }
  else if (key === 's' || key === 'S') { saveCanvas('geo_motion_' + CONFIG.SEED, 'png'); }
  else if (key === 'e' || key === 'E') { if (!exporting) { exporting = true; exportIndex = CONFIG.EXPORT.START; } }
  else if (key === 'h' || key === 'H') { showHUD = !showHUD; }
}
