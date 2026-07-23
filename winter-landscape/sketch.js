/* =====================================================================
   ATMOSPHERIC WINTER NIGHT  —  procedural p5.js scene
   ---------------------------------------------------------------------
   Single sketch, no build step. Open index.html in a browser.

   The whole scene is a SEAMLESS 30-second loop: every moving element
   returns exactly to its starting state after CONFIG.LOOP_FRAMES frames,
   so the video can be looped or exported as a PNG sequence with no jump.

   CONTROLS
     R  regenerate the scene with a new random seed
     S  save the current frame as a PNG
     E  export the whole loop as a PNG sequence (see CONFIG.EXPORT)
     H  toggle the little help / seed overlay

   Everything you might want to tweak lives in CONFIG (numbers) and
   C (colours) right at the top. Every field is commented.
   ===================================================================== */


/* ------------------------------------------------------------------ *
 *  CONFIG — every tunable number lives here                           *
 * ------------------------------------------------------------------ */
const CONFIG = {
  SEED: 1337,              // scene seed. Same seed => same mountains/trees/stars. Press R for a new one.
  WIDTH: 1920,             // canvas buffer width  (don't change unless you know why)
  HEIGHT: 1080,            // canvas buffer height
  LOOP_FRAMES: 1800,       // length of the seamless loop in frames (1800 = 30s at 60fps)
  HORIZON: 0.62,           // horizon height as a fraction of the canvas (0 = top, 1 = bottom)

  EXPOSURE: 1.0,           // overall brightness of the COLD elements (sky/stars/moon/aurora).
                           //   Lower = darker night. The warm window is deliberately NOT affected.

  // ---- feature toggles (true/false) ----
  STARS: true,
  AURORA: true,
  AURORA_REFLECTION: true, // faint aurora glow reflected on the snow near the horizon
  SMOKE: true,             // chimney smoke
  BIRDS: true,             // distant birds crossing the sky
  VIGNETTE: true,

  STAR_COUNT: 260,         // number of stars (they cluster toward the top)

  WIND: 0.9,              // global horizontal wind, px/frame. NEGATIVE blows to the LEFT.

  // ---- snowfall, three parallax layers: FAR (small/slow/dim) .. NEAR (big/fast/bright) ----
  SNOW: {
    FAR:  { count: 320, sizeMin: 1.0, sizeMax: 2.2, fall: 0.55, windMul: 0.45, alpha: 90,  wiggle: 10 },
    MID:  { count: 180, sizeMin: 2.0, sizeMax: 3.6, fall: 1.10, windMul: 0.80, alpha: 150, wiggle: 18 },
    NEAR: { count: 90,  sizeMin: 3.4, sizeMax: 6.2, fall: 2.00, windMul: 1.20, alpha: 225, wiggle: 30 },
  },
  SNOW_MARGIN: 70,         // off-screen wrap margin so flakes fade in/out past the edges

  // ---- aurora ----
  AURORA_RIBBONS: 3,       // number of ribbons
  AURORA_DRIFT: 0.6,       // how far the aurora slides over one loop (bigger = more movement)
  AURORA_AMP: 95,          // vertical wave height in px
  AURORA_ALPHA: 14,        // per-band opacity — keep LOW, additive blending stacks it up

  // ---- moon ----
  MOON_X: 0.76, MOON_Y: 0.21, // position as fractions of width/height
  MOON_R: 46,                 // radius in px
  MOON_HALO: 7,               // number of soft halo layers

  // ---- cabin ----
  CABIN_X: 0.45,           // cabin centre as a fraction of width (kept off the exact centre)
  CABIN_SCALE: 1.0,        // overall cabin size

  // ---- chimney smoke ----
  SMOKE_EMIT: 8,           // emit one puff every N frames. MUST divide LOOP_FRAMES for a clean loop.
  SMOKE_LIFE: 150,         // how long a puff lives, in frames
  SMOKE_RISE: 0.75,        // upward speed px/frame
  SMOKE_EXPAND: 0.20,      // how fast a puff grows
  SMOKE_ALPHA: 26,         // puff opacity

  // ---- distant birds ----
  BIRD_COUNT: 6,           // 5–6 looks best
  BIRD_Y_MIN: 0.15,        // top of the band they fly in (fraction of height)
  BIRD_Y_MAX: 0.34,        // bottom of that band
  BIRD_SIZE: 11,           // wingspan px (small = reads as far away)
  BIRD_ALPHA: 65,          // opacity (subtle)
  BIRD_FLAPS: 44,          // wing flaps per loop

  // ---- PNG-sequence export (press E) ----
  EXPORT: {
    START: 0,              // first loop-frame to export
    END: 1799,             // last loop-frame (LOOP_FRAMES - 1 gives the full loop)
    STEP: 1,               // export every Nth frame (2 = half as many files)
    PREFIX: 'winter_',     // file name prefix -> winter_0000.png, winter_0001.png ...
  },
};


/* ------------------------------------------------------------------ *
 *  C — every colour as [r, g, b]                                      *
 * ------------------------------------------------------------------ */
const C = {
  SKY_TOP:     [10, 17, 40],    // sky at the very top
  SKY_MID:     [28, 53, 87],    // sky middle
  SKY_HORIZON: [46, 82, 102],   // sky at the horizon

  SNOW_LIT:    [232, 238, 247], // lit snow
  SNOW_SHADE:  [143, 166, 196], // blue snow shadow

  MTN: [ [58, 84, 118],         // mountains far  (lightest, lowest contrast)
         [40, 62, 94],          // mountains mid
         [26, 42, 70] ],        // mountains near (darkest)

  PINE_FAR:  [30, 50, 74],      // distant treeline
  PINE_NEAR: [14, 26, 44],      // foreground pines (near-black)

  WARM:  [255, 180, 84],        // the lit window — the ONLY warm element
  EMBER: [255, 138, 61],        // warm light spilling onto the snow

  AUR_A: [95, 232, 176],        // aurora green
  AUR_B: [122, 111, 232],       // aurora violet

  STAR: [235, 242, 255],
  MOON: [240, 244, 255],
  BIRD: [8, 12, 22],            // bird silhouette (near-black, cold)
  SMOKE: [206, 216, 232],       // cool smoke
};


/* ------------------------------------------------------------------ *
 *  State (generated once, never rebuilt per frame unless R pressed)   *
 * ------------------------------------------------------------------ */
let stars = [];
let ridges = [];         // 3 mountain ridges, each an array of y values
let drifts = [];         // 2 snow-drift curves
let treeline = [];       // distant pines
let forePines = [];      // big foreground pines
let snowFar = [], snowMid = [], snowNear = [];
let birds = [];
let cabin = {};          // computed geometry incl. chimney mouth

let gLoopFrame = 0;      // current position within the loop (0 .. LOOP_FRAMES)
let exporting = false;
let exportIndex = 0;
let showHUD = false;


/* ------------------------------------------------------------------ *
 *  Small helpers                                                      *
 * ------------------------------------------------------------------ */
function horizonY() { return CONFIG.HEIGHT * CONFIG.HORIZON; }

// colour from a [r,g,b] array, optional alpha
function col(a, alpha) {
  return (alpha === undefined) ? color(a[0], a[1], a[2]) : color(a[0], a[1], a[2], alpha);
}
// cold colour dimmed by EXPOSURE (used for sky/stars/moon/aurora; NOT the warm window)
function dim(a) {
  const e = CONFIG.EXPOSURE;
  return [a[0] * e, a[1] * e, a[2] * e];
}
function rgbStr(a) { return `rgb(${a[0] | 0},${a[1] | 0},${a[2] | 0})`; }

// Time as an angle around the loop — the key to seamless looping.
function tAngle() { return TWO_PI * gLoopFrame / CONFIG.LOOP_FRAMES; }
function tCos() { return Math.cos(tAngle()); }
function tSin() { return Math.sin(tAngle()); }

// Wrap v into the interval [lo, lo+size)
function wrap(v, lo, size) { return lo + (((v - lo) % size) + size) % size; }

// Quantise a per-frame displacement so that (disp * LOOP_FRAMES) is an exact
// whole number of `span` units. That makes modular motion loop seamlessly.
function quantDisp(perFrame, span) {
  const loop = CONFIG.LOOP_FRAMES;
  let cells = Math.max(1, Math.round(Math.abs(perFrame) * loop / span));
  let mag = cells * span / loop;
  return perFrame < 0 ? -mag : mag;
}

// deterministic pseudo-random from an integer (for per-smoke-puff jitter)
function hash1(n) {
  let s = Math.sin(n * 127.1 + CONFIG.SEED * 0.013) * 43758.5453;
  return s - Math.floor(s);
}


/* ================================================================== *
 *  SETUP                                                              *
 * ================================================================== */
function setup() {
  const cnv = createCanvas(CONFIG.WIDTH, CONFIG.HEIGHT);
  cnv.parent('stage');
  pixelDensity(1);         // keep a true 1920x1080 buffer (matters for export + perf)
  frameRate(60);
  generate();              // build every persistent array from the seed
}

// Rebuild the whole scene from CONFIG.SEED. Called at start and on R.
function generate() {
  randomSeed(CONFIG.SEED);
  noiseSeed(CONFIG.SEED);

  buildStars();
  buildMountains();
  buildDrifts();
  buildTreeline();
  buildCabin();            // must come before pines/smoke (defines chimney)
  buildForePines();
  buildBirds();

  snowFar  = buildSnowLayer(CONFIG.SNOW.FAR);
  snowMid  = buildSnowLayer(CONFIG.SNOW.MID);
  snowNear = buildSnowLayer(CONFIG.SNOW.NEAR);
}


/* ---- generators ---------------------------------------------------- */

function buildStars() {
  stars = [];
  const hY = horizonY();
  for (let i = 0; i < CONFIG.STAR_COUNT; i++) {
    // density weighted toward the top: random()^1.8 pushes points upward
    const y = Math.pow(random(), 1.8) * hY * 0.97;
    stars.push({
      x: random(width),
      y: y,
      r: random(0.6, 1.8),
      phase: random(TWO_PI),
      cycles: floor(random(1, 6)),   // whole cycles per loop => seamless twinkle
      base: random(0.35, 0.9),       // baseline brightness
    });
  }
}

function buildMountains() {
  // three ridges; farther = shorter + hazier, drawn back-to-front
  const hY = horizonY();
  const params = [
    { amp: 70,  base: hY - 4,  freq: 0.0016, off: 0 },
    { amp: 115, base: hY + 6,  freq: 0.0021, off: 55 },
    { amp: 165, base: hY + 16, freq: 0.0027, off: 120 },
  ];
  ridges = params.map(p => {
    const pts = [];
    for (let x = 0; x <= width; x += 6) {
      const n = noise(x * p.freq + p.off, p.off * 0.1);
      pts.push(p.base - n * p.amp);
    }
    return { pts, step: 6 };
  });
}

function buildDrifts() {
  // two snow-bank curves that undulate across the ground
  const hY = horizonY();
  const specs = [
    { base: hY + 95,  amp: 34, freq: 0.0022, off: 10 },
    { base: hY + 165, amp: 46, freq: 0.0028, off: 90 },
  ];
  drifts = specs.map(s => {
    const pts = [];
    for (let x = 0; x <= width; x += 8) {
      pts.push(s.base - noise(x * s.freq + s.off) * s.amp);
    }
    return { pts, step: 8 };
  });
}

function buildTreeline() {
  // small distant pines strung along the horizon
  treeline = [];
  const hY = horizonY();
  for (let x = 10; x < width; x += random(16, 34)) {
    treeline.push({ x, h: random(14, 30), y: hY + random(-4, 8) });
  }
}

function buildCabin() {
  const s = CONFIG.CABIN_SCALE;
  const bx = width * CONFIG.CABIN_X;
  const by = horizonY() + 150 * s;   // sits on the snow, a little below the horizon
  const bw = 168 * s, bh = 116 * s;
  cabin = {
    x: bx, y: by, w: bw, h: bh, s: s,
    // window centre (warm light source)
    winX: bx - bw * 0.18, winY: by - bh * 0.52, winW: 40 * s, winH: 46 * s,
    // chimney mouth (smoke origin)
    chimX: bx + bw * 0.30, chimY: by - bh - 78 * s,
  };
}

function buildForePines() {
  // big near-black pines clustered at the LEFT and RIGHT edges, centre kept open
  forePines = [];
  const hY = horizonY();
  const clusters = [
    { x0: -0.02, x1: 0.20 },   // left edge
    { x0: 0.80,  x1: 1.03 },   // right edge
  ];
  clusters.forEach(cl => {
    const n = floor(random(3, 5));
    for (let i = 0; i < n; i++) {
      forePines.push({
        x: width * random(cl.x0, cl.x1),
        baseY: hY + random(150, 320),
        h: random(360, 620),
        w: random(150, 240),
      });
    }
  });
  // draw the shortest last so tall ones don't get buried — sort tall→short
  forePines.sort((a, b) => b.h - a.h);
}

function buildBirds() {
  birds = [];
  for (let i = 0; i < CONFIG.BIRD_COUNT; i++) {
    birds.push({
      phase: random(),                       // start offset around the loop (0..1)
      yFrac: random(CONFIG.BIRD_Y_MIN, CONFIG.BIRD_Y_MAX),
      size: CONFIG.BIRD_SIZE * random(0.8, 1.25),
      dir: random() < 0.5 ? 1 : -1,          // fly left→right or right→left
      bob: random(4, 10),                    // gentle vertical bob amplitude
      bobCycles: floor(random(2, 4)),        // whole bobs per loop => seamless
      flapPhase: random(TWO_PI),
    });
  }
}

function buildSnowLayer(cfgLayer) {
  const M = CONFIG.SNOW_MARGIN;
  const spanW = width + 2 * M;
  const spanH = height + 2 * M;
  const arr = [];
  for (let i = 0; i < cfgLayer.count; i++) {
    // per-flake fall + wind, each individually quantised so the layer loops
    const fall = quantDisp(cfgLayer.fall * random(0.75, 1.3), spanH);
    const wind = quantDisp(CONFIG.WIND * cfgLayer.windMul * random(0.85, 1.15), spanW);
    arr.push({
      x0: random(-M, width + M),
      y0: random(-M, height + M),
      size: random(cfgLayer.sizeMin, cfgLayer.sizeMax),
      fall, wind,
      nseed: random(1000),      // its own noise lane for horizontal wobble
    });
  }
  return arr;
}


/* ================================================================== *
 *  DRAW                                                               *
 * ================================================================== */
function draw() {
  // Establish the loop position for this frame.
  if (exporting) {
    gLoopFrame = exportIndex;
  } else {
    gLoopFrame = frameCount % CONFIG.LOOP_FRAMES;
  }

  drawScene();

  if (exporting) handleExport();
  if (showHUD && !exporting) drawHUD();
}

// The full stack of layers, back to front.
function drawScene() {
  drawSky();                                  // 1
  if (CONFIG.STARS) drawStars();              // 2
  if (CONFIG.AURORA) drawAurora();            // 3
  drawMoon();                                 // 4
  if (CONFIG.BIRDS) drawBirds();              // (far, behind the mountains)
  drawMountains();                            // 5
  drawSnowGround();                           // 6
  if (CONFIG.AURORA && CONFIG.AURORA_REFLECTION) drawAuroraReflection(); // aurora on the snow
  drawTreeline();                             // 7
  drawCabin();                                // 8
  if (CONFIG.SMOKE) drawSmoke();              // 9
  drawForePines();                            // 10
  drawSnow();                                 // 11
  if (CONFIG.VIGNETTE) drawVignette();        // 12
}


/* ---- 1. sky -------------------------------------------------------- */
function drawSky() {
  const hY = horizonY();
  const g = drawingContext.createLinearGradient(0, 0, 0, hY);
  g.addColorStop(0.0, rgbStr(dim(C.SKY_TOP)));
  g.addColorStop(0.5, rgbStr(dim(C.SKY_MID)));
  g.addColorStop(1.0, rgbStr(dim(C.SKY_HORIZON)));
  drawingContext.fillStyle = g;
  drawingContext.fillRect(0, 0, width, hY);
  // below the horizon, base fill (the snow ground paints over this)
  noStroke();
  fill(col(dim(C.SKY_HORIZON)));
  rect(0, hY, width, height - hY);
}

/* ---- 2. stars ------------------------------------------------------ */
function drawStars() {
  noStroke();
  const th = tAngle();
  for (const s of stars) {
    // each star twinkles on its own whole number of cycles per loop
    const tw = s.base + 0.35 * Math.sin(s.phase + s.cycles * th);
    const a = constrain(tw, 0, 1) * 255 * CONFIG.EXPOSURE;
    fill(C.STAR[0], C.STAR[1], C.STAR[2], a);
    circle(s.x, s.y, s.r * 2);
  }
}

/* ---- 3. aurora ----------------------------------------------------- */
// Centreline of ribbon `r` at horizontal position `x`. Loops in time via
// the (cos,sin) circle fed into 3D noise.
function auroraShapeY(r, x) {
  const f = 0.0016;
  const R = CONFIG.AURORA_DRIFT;
  const n = noise(x * f + r * 10.5, 20 + r * 3.1 + R * tCos(), 40 + R * tSin());
  const baseY = height * (0.15 + r * 0.06);
  return baseY + (n - 0.5) * 2 * CONFIG.AURORA_AMP;
}

function drawAurora() {
  blendMode(ADD);
  noStroke();
  const nR = Math.max(1, CONFIG.AURORA_RIBBONS - 1);
  for (let r = 0; r < CONFIG.AURORA_RIBBONS; r++) {
    const cc = lerpColor(col(C.AUR_A), col(C.AUR_B), r / nR);
    const cr = red(cc), cg = green(cc), cb = blue(cc);
    // three stacked passes = soft vertical glow
    const bands = [200, 118, 56];
    const mult = [0.5, 0.9, 1.5];
    for (let p = 0; p < 3; p++) {
      const h2 = bands[p] / 2;
      fill(cr, cg, cb, CONFIG.AURORA_ALPHA * mult[p] * CONFIG.EXPOSURE);
      beginShape(TRIANGLE_STRIP);
      for (let x = 0; x <= width; x += 8) {
        const cy = auroraShapeY(r, x);
        vertex(x, cy - h2);
        vertex(x, cy + h2);
      }
      endShape();
    }
  }
  blendMode(BLEND);
}

// faint aurora reflected on the snow, only in a band just below the horizon
function drawAuroraReflection() {
  const hY = horizonY();
  const depth = 120;               // how far down the reflection reaches
  const nR = Math.max(1, CONFIG.AURORA_RIBBONS - 1);
  blendMode(ADD);
  noStroke();
  for (let x = 0; x <= width; x += 12) {
    // mix the ribbon colours, weighted by how close each ribbon sits to the horizon
    let rr = 0, gg = 0, bb = 0, w = 0;
    for (let r = 0; r < CONFIG.AURORA_RIBBONS; r++) {
      const cy = auroraShapeY(r, x);
      const inten = constrain(map(cy, hY - 300, hY - 40, 0, 1), 0, 1);
      const cc = lerpColor(col(C.AUR_A), col(C.AUR_B), r / nR);
      rr += red(cc) * inten; gg += green(cc) * inten; bb += blue(cc) * inten; w += inten;
    }
    if (w <= 0.001) continue;
    rr /= w; gg /= w; bb /= w;
    const strength = constrain(w / CONFIG.AURORA_RIBBONS, 0, 1);
    // vertical fade: brightest at the horizon, gone by `depth`
    for (let s = 0; s < 3; s++) {
      const yy = hY + (depth * s) / 3;
      const fade = 1 - s / 3;
      fill(rr, gg, bb, CONFIG.AURORA_ALPHA * 0.30 * strength * fade * CONFIG.EXPOSURE);
      rect(x, yy, 12, depth / 3 + 1);
    }
  }
  blendMode(BLEND);
}

/* ---- 4. moon ------------------------------------------------------- */
function drawMoon() {
  const mx = width * CONFIG.MOON_X, my = height * CONFIG.MOON_Y, R = CONFIG.MOON_R;
  blendMode(ADD);
  noStroke();
  for (let i = CONFIG.MOON_HALO; i >= 1; i--) {
    const rad = R * (1 + i * 0.9);
    const a = (10 * CONFIG.EXPOSURE) * (1 - i / (CONFIG.MOON_HALO + 1));
    fill(C.MOON[0], C.MOON[1], C.MOON[2], a);
    circle(mx, my, rad * 2);
  }
  blendMode(BLEND);
  fill(col(dim(C.MOON)));
  circle(mx, my, R * 2);
}

/* ---- 5. mountains -------------------------------------------------- */
function drawMountains() {
  noStroke();
  for (let r = 0; r < ridges.length; r++) {
    fill(col(dim(C.MTN[r])));
    beginShape();
    vertex(0, height);
    const rg = ridges[r];
    for (let i = 0; i < rg.pts.length; i++) vertex(i * rg.step, rg.pts[i]);
    vertex(width, height);
    endShape(CLOSE);
  }
}

/* ---- 6. snow ground + drifts -------------------------------------- */
function drawSnowGround() {
  const hY = horizonY();
  noStroke();
  fill(col(C.SNOW_LIT));
  rect(0, hY, width, height - hY);

  // drift 1 (back) — blue shadow band
  fill(C.SNOW_SHADE[0], C.SNOW_SHADE[1], C.SNOW_SHADE[2], 120);
  driftShape(drifts[0]);
  // drift 2 (front) — deeper shadow
  fill(C.SNOW_SHADE[0], C.SNOW_SHADE[1], C.SNOW_SHADE[2], 170);
  driftShape(drifts[1]);
  // a soft lit crest to catch the moonlight on the front drift
  fill(C.SNOW_LIT[0], C.SNOW_LIT[1], C.SNOW_LIT[2], 90);
  driftShape(drifts[1], -10);
}

function driftShape(d, yOffset = 0) {
  beginShape();
  vertex(0, height);
  for (let i = 0; i < d.pts.length; i++) vertex(i * d.step, d.pts[i] + yOffset);
  vertex(width, height);
  endShape(CLOSE);
}

/* ---- 7. distant treeline ------------------------------------------ */
function drawTreeline() {
  noStroke();
  // low-contrast: blend the distant-pine colour toward the horizon sky
  const c = lerpColor(col(dim(C.PINE_FAR)), col(dim(C.SKY_HORIZON)), 0.35);
  fill(c);
  for (const t of treeline) {
    triangle(t.x - t.h * 0.4, t.y, t.x + t.h * 0.4, t.y, t.x, t.y - t.h);
  }
}

/* ---- 8. cabin ------------------------------------------------------ */
function drawCabin() {
  const cb = cabin, s = cb.s;
  noStroke();

  // warm light spilling onto the snow (drawn first, under the cabin)
  drawWindowSpill();

  // body
  fill(24, 36, 56);
  rect(cb.x - cb.w / 2, cb.y - cb.h, cb.w, cb.h);

  // roof
  fill(16, 26, 42);
  triangle(cb.x - cb.w / 2 - 14 * s, cb.y - cb.h,
           cb.x + cb.w / 2 + 14 * s, cb.y - cb.h,
           cb.x, cb.y - cb.h - 74 * s);
  // snow on the roof
  fill(col(C.SNOW_LIT));
  triangle(cb.x - cb.w / 2 - 14 * s, cb.y - cb.h,
           cb.x + cb.w / 2 + 14 * s, cb.y - cb.h,
           cb.x, cb.y - cb.h - 74 * s);
  fill(16, 26, 42);
  triangle(cb.x - cb.w / 2 - 2 * s, cb.y - cb.h - 6 * s,
           cb.x + cb.w / 2 + 2 * s, cb.y - cb.h - 6 * s,
           cb.x, cb.y - cb.h - 60 * s);

  // chimney + its snow cap
  fill(20, 30, 48);
  rect(cb.chimX - 10 * s, cb.chimY, 20 * s, 46 * s);
  fill(col(C.SNOW_LIT));
  rect(cb.chimX - 12 * s, cb.chimY - 6 * s, 24 * s, 8 * s);

  // window — the ONLY warm element, with a subtle flicker
  const flick = map(noise(500 + CONFIG.AURORA_DRIFT * tCos(), 500 + CONFIG.AURORA_DRIFT * tSin()),
                    0, 1, 0.86, 1.0);
  // glow around the window (additive)
  blendMode(ADD);
  for (let i = 4; i >= 1; i--) {
    fill(C.WARM[0], C.WARM[1], C.WARM[2], 30 * flick * (1 - i / 5));
    circle(cb.winX, cb.winY, cb.winW * (2 + i * 1.1));
  }
  blendMode(BLEND);
  // frame + pane
  fill(10, 16, 28);
  rect(cb.winX - cb.winW / 2 - 3, cb.winY - cb.winH / 2 - 3, cb.winW + 6, cb.winH + 6);
  fill(C.WARM[0] * flick, C.WARM[1] * flick, C.WARM[2] * flick);
  rect(cb.winX - cb.winW / 2, cb.winY - cb.winH / 2, cb.winW, cb.winH);
  // muntins
  stroke(10, 16, 28); strokeWeight(2.5 * s);
  line(cb.winX, cb.winY - cb.winH / 2, cb.winX, cb.winY + cb.winH / 2);
  line(cb.winX - cb.winW / 2, cb.winY, cb.winX + cb.winW / 2, cb.winY);
  noStroke();
}

// warm pool of light thrown from the window onto the snow in front of the cabin
function drawWindowSpill() {
  const cb = cabin;
  const gx = cb.winX, gy = cb.y + 8;
  blendMode(ADD);
  // long soft trapezoid of light reaching toward the viewer
  const grad = drawingContext.createRadialGradient(gx, gy, 4, gx, gy + 60, 260 * cb.s);
  grad.addColorStop(0, `rgba(${C.EMBER[0]},${C.EMBER[1]},${C.EMBER[2]},0.34)`);
  grad.addColorStop(0.5, `rgba(${C.WARM[0]},${C.WARM[1]},${C.WARM[2]},0.12)`);
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  drawingContext.fillStyle = grad;
  drawingContext.beginPath();
  drawingContext.moveTo(gx - 30, cb.y - 20);
  drawingContext.lineTo(gx + 30, cb.y - 20);
  drawingContext.lineTo(gx + 190 * cb.s, cb.y + 220 * cb.s);
  drawingContext.lineTo(gx - 190 * cb.s, cb.y + 220 * cb.s);
  drawingContext.closePath();
  drawingContext.fill();
  blendMode(BLEND);
}

/* ---- 9. chimney smoke (procedural + seamless) --------------------- */
function drawSmoke() {
  const cb = cabin;
  const LOOP = CONFIG.LOOP_FRAMES, EM = CONFIG.SMOKE_EMIT, LIFE = CONFIG.SMOKE_LIFE;
  const puffsPerLoop = LOOP / EM;
  noStroke();

  // Consider every puff whose lifetime overlaps the current frame, including
  // puffs emitted in the previous loop (negative k) — that makes it seamless.
  const kStart = Math.floor((gLoopFrame - LIFE) / EM);
  const kEnd = Math.floor(gLoopFrame / EM);
  for (let k = kStart; k <= kEnd; k++) {
    const e = k * EM;
    const age = gLoopFrame - e;
    if (age < 0 || age >= LIFE) continue;
    // stable id so each puff always jitters the same way within the loop
    const id = ((k % puffsPerLoop) + puffsPerLoop) % puffsPerLoop;
    const jx = (hash1(id) - 0.5);
    const t = age / LIFE;
    const x = cb.chimX + jx * 10 + Math.sin(age * 0.05 + id) * 8 + CONFIG.WIND * age * 0.25;
    const y = cb.chimY - age * CONFIG.SMOKE_RISE;
    const rad = (6 + age * CONFIG.SMOKE_EXPAND) * (0.8 + 0.5 * hash1(id + 7));
    // fade in quickly, then out
    const fadeIn = t < 0.12 ? t / 0.12 : 1;
    const a = CONFIG.SMOKE_ALPHA * fadeIn * (1 - t) * (1 - t);
    fill(C.SMOKE[0], C.SMOKE[1], C.SMOKE[2], a);
    circle(x, y, rad * 2);
  }
}

/* ---- 10. foreground pines ----------------------------------------- */
function drawForePines() {
  noStroke();
  fill(col(C.PINE_NEAR));
  for (const p of forePines) pineSilhouette(p.x, p.baseY, p.h, p.w);
}

function pineSilhouette(x, baseY, h, w) {
  // trunk
  rect(x - w * 0.04, baseY - h * 0.18, w * 0.08, h * 0.18);
  // 4 stacked tiers
  const tiers = 4;
  for (let i = 0; i < tiers; i++) {
    const f = i / tiers;
    const ty = baseY - h * 0.12 - f * h * 0.82;
    const tw = w * (1 - f * 0.62);
    const th = h * 0.30;
    triangle(x - tw / 2, ty, x + tw / 2, ty, x, ty - th);
  }
}

/* ---- 11. snowfall -------------------------------------------------- */
function drawSnow() {
  drawSnowLayer(snowFar, CONFIG.SNOW.FAR);
  drawSnowLayer(snowMid, CONFIG.SNOW.MID);
  drawSnowLayer(snowNear, CONFIG.SNOW.NEAR);
}

function drawSnowLayer(layer, cfgLayer) {
  const M = CONFIG.SNOW_MARGIN;
  const spanW = width + 2 * M, spanH = height + 2 * M;
  const R = 0.7; // wobble drift radius (looping)
  noStroke();
  fill(C.SNOW_LIT[0], C.SNOW_LIT[1], C.SNOW_LIT[2], cfgLayer.alpha);
  for (const f of layer) {
    const y = wrap(f.y0 + f.fall * gLoopFrame, -M, spanH);
    // horizontal wobble from looping noise (returns to start each loop)
    const wob = (noise(f.nseed + R * tCos(), R * tSin()) - 0.5) * 2 * cfgLayer.wiggle;
    const x = wrap(f.x0 + f.wind * gLoopFrame + wob, -M, spanW);
    circle(x, y, f.size);
  }
}

/* ---- birds --------------------------------------------------------- */
function drawBirds() {
  const th = tAngle();
  stroke(C.BIRD[0], C.BIRD[1], C.BIRD[2], CONFIG.BIRD_ALPHA);
  noFill();
  const M = 120;
  const span = width + 2 * M;
  for (const b of birds) {
    // fraction around the loop; one crossing per loop (wrap happens off-screen)
    let frac = (gLoopFrame / CONFIG.LOOP_FRAMES) * b.dir + b.phase;
    frac = frac - Math.floor(frac);
    const x = -M + span * frac;
    const y = height * b.yFrac + Math.sin(b.bobCycles * th) * b.bob;
    // wing flap angle (whole flaps per loop => seamless)
    const flap = Math.sin(CONFIG.BIRD_FLAPS * (gLoopFrame / CONFIG.LOOP_FRAMES) * TWO_PI + b.flapPhase);
    const s = b.size;
    const wingY = -Math.abs(flap) * s * 0.5;   // wings rise/fall
    strokeWeight(Math.max(1, s * 0.14));
    // a simple V/M silhouette
    line(x - s, y - wingY, x, y);
    line(x, y, x + s, y - wingY);
  }
  noStroke();
}

/* ---- 12. vignette -------------------------------------------------- */
function drawVignette() {
  const g = drawingContext.createRadialGradient(
    width / 2, height * 0.52, height * 0.22,
    width / 2, height * 0.52, height * 0.92);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.55)');
  drawingContext.fillStyle = g;
  drawingContext.fillRect(0, 0, width, height);
}


/* ================================================================== *
 *  Export + input                                                     *
 * ================================================================== */
function handleExport() {
  // save the frame we just drew, then step forward
  saveCanvas(CONFIG.EXPORT.PREFIX + nf(exportIndex, 4), 'png');
  exportIndex += CONFIG.EXPORT.STEP;
  if (exportIndex > CONFIG.EXPORT.END) {
    exporting = false;
    console.log('Export finished.');
  }
}

function drawHUD() {
  push();
  resetMatrix();
  noStroke();
  fill(0, 0, 0, 150);
  rect(16, 16, 360, 108, 8);
  fill(235);
  textFont('monospace');
  textSize(16);
  text(`seed: ${CONFIG.SEED}`, 30, 44);
  text(`loop: ${gLoopFrame} / ${CONFIG.LOOP_FRAMES}  (${(CONFIG.LOOP_FRAMES/60).toFixed(0)}s)`, 30, 68);
  text(`R new seed   S save PNG`, 30, 92);
  text(`E export sequence   H hide`, 30, 112);
  pop();
}

function keyPressed() {
  if (key === 'r' || key === 'R') {
    CONFIG.SEED = floor(Math.random() * 1e9);   // Math.random (not seeded) => genuinely new
    generate();
  } else if (key === 's' || key === 'S') {
    saveCanvas('winter_night_' + CONFIG.SEED, 'png');
  } else if (key === 'e' || key === 'E') {
    if (!exporting) { exporting = true; exportIndex = CONFIG.EXPORT.START; }
  } else if (key === 'h' || key === 'H') {
    showHUD = !showHUD;
  }
}
