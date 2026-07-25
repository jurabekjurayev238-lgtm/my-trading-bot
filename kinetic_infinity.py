"""Kinetic Infinity — Variante 2  (Instagram Story, 9:16, 1080x1920, 15s).

Ikkita bir-biriga kirishgan 3D spiral (helix) neon sharchalardan tashkil
topgan; ular o'z vertikal o'qi atrofida ritmik aylanadi va butun
kompozitsiya pastdan yuqoriga cheksiz siljiydi. Kamera pastdan diagonal
ko'rinishga (phi=75) chiqib, to'liq 360° orbita yasaydi.

15 soniyada MUKAMMAL takrorlanadi (seamless loop):
  * aylanish  = K*dtheta + 2*pi*n  (butun burilishlar)
  * siljish   = K*dz               (aynan K ta sharcha qadami)
  * ranglar   = i mod K  ga bog'liq  => siljigach rang naqshi mos tushadi
  * kamera    : theta 360°, phi davriy (cos) => boshiga qaytadi

Render:
    manim -pqh kinetic_infinity.py KineticInfinity
"""

from manim import *
import numpy as np

# ---------------- 9:16 VERTIKAL KONFIGURATSIYA ----------------
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_height = 14.0
config.frame_width = config.frame_height * 1080 / 1920   # = 7.875

# ---------------- RANGLAR ----------------
NEON_PINK = "#FF2D95"     # birinchi spiral
NEON_CYAN = "#00F0FF"     # ikkinchi spiral
BG_TOP    = "#FFF0B0"     # och sariq (yuqori)
BG_MID    = "#FFC04A"     # oltin
BG_BOT    = "#FF6A13"     # yorqin apelsin (past)

# ---------------- SPIRAL PARAMETRLARI ----------------
N_TURN  = 12              # bitta to'liq burilishdagi sharchalar soni
DTHETA  = TAU / N_TURN    # sharchalar orasidagi burchak qadami
DZ      = 0.55            # sharchalar orasidagi vertikal qadam
M       = 44              # har spiraldagi sharchalar soni
Z0      = -12.5           # spiral pastki uchi (kadrdan ancha past)
R_HELIX = 1.45            # spiral radiusi
R_BALL  = 0.17            # sharcha radiusi

K       = 6               # loop davomida yuqoriga siljish qadamlari
N_SPIN  = 3               # qo'shimcha to'liq burilishlar soni
LOOP_T  = 15              # sekund

ANG_TOTAL = K * DTHETA + TAU * N_SPIN   # umumiy aylanish burchagi
Z_TOTAL   = K * DZ                      # umumiy yuqoriga siljish


def rhythmic(t, m=3, a=0.30):
    """Ritmik (pulsatsiyalanuvchi) rate function.

    rf(0)=0, rf(1)=1 va rf'(0)=rf'(1)=1-a  =>  loop ulanishi silliq.
    """
    return t - a * np.sin(TAU * m * t) / (TAU * m)


# --- neon porlash (glow) qatlamlari: (o'lcham, shaffoflik) ---
GLOW = [(1.85, 0.26), (2.85, 0.11)]


def _ico_faces(r, c, opacity, whiten):
    """Ikosaedr yuzlari (20 ta uchburchak) — og'ir Graph qismisiz."""
    ico = Icosahedron(edge_length=r * 1.051)   # circumradius ~= r
    faces = ico.submobjects[0]
    faces.set_stroke(width=0)
    col = interpolate_color(ManimColor(c), WHITE, whiten)
    faces.set_fill(col, opacity=opacity)
    return faces


def neon_ball(c, r=R_BALL):
    """Porlab turuvchi ko'p qirrali sharcha.

    Yadro (to'liq rang, qirralari turli soyada) + atrofida 2 ta kattaroq
    shaffof qatlam => neon halo. Post-processing bloom fon rangini ham
    ushlab qolgani uchun porlash aynan geometriya bilan beriladi.
    """
    grp = VGroup()
    # tashqi -> ichki (shaffoflari avval chizilsin)
    for scale, op in reversed(GLOW):
        grp.add(_ico_faces(r * scale, c, op, 0.45))
    core = _ico_faces(r, c, 1.0, 0.0)
    for j, f in enumerate(core):               # qirralarni ajratish uchun soya
        f.set_fill(interpolate_color(ManimColor(c), WHITE, 0.09 * (j % 4)),
                   opacity=1)
    grp.add(core)
    return grp


def helix_color(i, base, other):
    """Rang i mod K ga bog'liq => K qadam siljigach naqsh aynan mos tushadi.

    Har spiral o'z rangida bo'ladi, lekin ikkinchi rang bilan chatishadi.
    """
    u = 0.5 * (1 + np.sin(TAU * (i % K) / K))     # 0..1, davri = K
    return interpolate_color(ManimColor(base), ManimColor(other), 0.45 * u)


class KineticInfinity(ThreeDScene):
    def construct(self):
        # ============ 1. GRADIENT FON (fixed in frame) ============
        strips = VGroup()
        n_str = 48
        h = config.frame_height / n_str
        for i in range(n_str):
            f = i / (n_str - 1)                    # 0 = yuqori, 1 = past
            if f < 0.5:
                c = interpolate_color(ManimColor(BG_TOP), ManimColor(BG_MID), f / 0.5)
            else:
                c = interpolate_color(ManimColor(BG_MID), ManimColor(BG_BOT), (f - 0.5) / 0.5)
            r = Rectangle(width=config.frame_width * 1.05, height=h * 1.02,
                          stroke_width=0, fill_color=c, fill_opacity=1)
            r.move_to(UP * (config.frame_height / 2 - h * (i + 0.5)))
            strips.add(r)
        strips.set_z_index(-100)
        self.add_fixed_in_frame_mobjects(strips)

        # ============ 2. IKKI SPIRAL ============
        helix = VGroup()
        for hid, (base, other, phase0) in enumerate(
                [(NEON_PINK, NEON_CYAN, 0.0), (NEON_CYAN, NEON_PINK, PI)]):
            for i in range(M):
                ang = phase0 + i * DTHETA
                z = Z0 + i * DZ
                ball = neon_ball(helix_color(i, base, other))
                ball.move_to([R_HELIX * np.cos(ang), R_HELIX * np.sin(ang), z])
                helix.add(ball)
        self.add(helix)

        # ============ 3. HARAKAT (loop fazasi) ============
        phase = ValueTracker(0.0)
        state = {"ang": 0.0, "z": 0.0}

        def move_helix(m):
            t = phase.get_value()
            rf = rhythmic(t)
            ang = ANG_TOTAL * rf          # ritmik aylanish
            z = Z_TOTAL * t               # bir tekis yuqoriga siljish
            # farqni qo'llaymiz (in-place, tez)
            m.rotate(ang - state["ang"], axis=OUT, about_point=ORIGIN)
            m.shift(OUT * (z - state["z"]))
            state["ang"], state["z"] = ang, z

        helix.add_updater(move_helix)

        # ============ 4. KAMERA (pastdan -> diagonal, 360° orbita) ============
        # phi: 96° (pastdan) -> 75° (diagonal) -> 96°   [davriy => loop]
        # theta: -30° dan boshlab to'liq 360° aylanadi -> yana -30°
        self.set_camera_orientation(phi=96 * DEGREES, theta=-30 * DEGREES)

        cam = VectorizedPoint()

        def move_camera(m):
            t = phase.get_value()
            phi = 96 - 21 * (1 - np.cos(TAU * t)) / 2
            theta = -30 - 360 * t
            self.set_camera_orientation(phi=phi * DEGREES, theta=theta * DEGREES)

        cam.add_updater(move_camera)
        self.add(cam)

        # ============ 5. LOOP ============
        self.play(phase.animate.set_value(1.0),
                  run_time=LOOP_T, rate_func=linear)

        helix.clear_updaters()
        cam.clear_updaters()
