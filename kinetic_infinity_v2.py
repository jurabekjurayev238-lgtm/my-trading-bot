"""Kinetic Infinity v2 — Instagram Story (9:16, 720x1280, 15s).

Ikkita judayam zich kirishgan 3D helix. Uzluksiz neon chiziq effekti
segmentlangan porlovchi egri chiziqdan (keng xira + o'rta + ingichka
yorqin qatlam) olinadi; ko'p qirrali ikosaedr shakllar shu chiziq ustida
o'tiradi va shu tufayli har biri tayyor halo bilan chiqadi.

MUKAMMAL LOOP — helixning vint simmetriyasidan foydalanamiz:
  * z bo'yicha aynan PITCH ga (yoki uning butun karrasiga) siljitish
    helixni o'z-o'ziga aks ettiradi;
  * 2*pi ning butun karrasiga burish — ayniyat.
Shuning uchun t=0 va t=1 da kadr aynan bir xil bo'ladi.

Render:
    manim -pql kinetic_infinity_v2.py KineticInfinityV2      # tezkor
    manim -pqh kinetic_infinity_v2.py KineticInfinityV2      # sifatli
"""

from manim import *
import numpy as np

# ---------------- 9:16 VERTIKAL, 720x1280 ----------------
config.pixel_width = 720
config.pixel_height = 1280
config.frame_height = 11.0
config.frame_width = config.frame_height * 720 / 1280   # = 6.1875
config.frame_rate = 30

# ---------------- RANGLAR ----------------
NEON_PINK = "#FF2BD1"     # birinchi spiral
NEON_CYAN = "#00F5FF"     # ikkinchi spiral
BG_TOP = "#2A1160"        # to'q binafsha (yuqori)
BG_MID = "#150B36"        # ko'k-binafsha
BG_BOT = "#070516"        # deyarli qora navy (past)

# ---------------- HELIX PARAMETRLARI ----------------
R_HELIX      = 1.42       # spiral radiusi
PITCH        = 2.30       # bitta to'liq burilishdagi ko'tarilish
PTS_PER_TURN = 56         # burilishdagi nuqtalar (zichlik)
Z_LO, Z_HI   = -9.0, 9.0  # spiral uzunligi (ekran tashqarisiga chiqadi)

SEG_LEN      = 8          # egri chiziq segmentidagi nuqtalar (z-sort uchun)
SHAPE_EVERY  = 2          # har nechanchi nuqtaga ko'p qirrali shakl
R_SHAPE      = 0.190      # shakl radiusi (qo'shni bilan ustma-ust tushadi)

# porlash qatlamlari: (stroke width, opacity)
GLOW_STROKES = [(26, 0.055), (13, 0.13), (5.5, 0.40), (2.0, 0.95)]

ROT_TURNS    = 3          # loop davomida to'liq burilishlar (ayniyat)
FLOW_PITCHES = 3          # loop davomida necha PITCH yuqoriga siljish
LOOP_T       = 15         # sekund

DZ     = PITCH / PTS_PER_TURN
DTHETA = TAU / PTS_PER_TURN
N_PTS  = int((Z_HI - Z_LO) / DZ)


def rhythmic(t, m=3, a=0.65):
    """Ritmik ease_in_out: tezlik pulsatsiya qiladi, lekin hech to'xtamaydi.

    rf(0)=0, rf(1)=1; rf'(0)=rf'(1)=1-a  =>  loop ulanishi silliq.
    """
    return t - a * np.sin(TAU * m * t) / (TAU * m)


def helix_points(phase0):
    """Helix nuqtalari (pastdan yuqoriga)."""
    pts = []
    for i in range(N_PTS):
        a = phase0 + i * DTHETA
        z = Z_LO + i * DZ
        pts.append(np.array([R_HELIX * np.cos(a), R_HELIX * np.sin(a), z]))
    return pts


def facet_shape(c, r=R_SHAPE):
    """Ko'p qirrali shakl — ikosaedr (20 yuz), og'ir Graph qismisiz."""
    ico = Icosahedron(edge_length=r * 1.051)
    faces = ico.submobjects[0]
    faces.set_stroke(width=0)
    for j, f in enumerate(faces):
        # qirralar ajralib tursin: bir qismi oqroq
        f.set_fill(interpolate_color(ManimColor(c), WHITE, 0.10 + 0.16 * (j % 4)),
                   opacity=1)
    return faces


class KineticInfinityV2(ThreeDScene):
    def construct(self):
        # ============ 1. TO'Q GRADIENT FON ============
        strips = VGroup()
        n = 60
        h = config.frame_height / n
        for i in range(n):
            f = i / (n - 1)
            if f < 0.5:
                c = interpolate_color(ManimColor(BG_TOP), ManimColor(BG_MID), f / 0.5)
            else:
                c = interpolate_color(ManimColor(BG_MID), ManimColor(BG_BOT),
                                      (f - 0.5) / 0.5)
            r = Rectangle(width=config.frame_width * 1.06, height=h * 1.03,
                          stroke_width=0, fill_color=c, fill_opacity=1)
            r.move_to(UP * (config.frame_height / 2 - h * (i + 0.5)))
            strips.add(r)
        strips.set_z_index(-100)
        self.add_fixed_in_frame_mobjects(strips)

        # ============ 2. IKKI HELIX ============
        structure = VGroup()
        for base, phase0 in [(NEON_PINK, 0.0), (NEON_CYAN, PI)]:
            pts = helix_points(phase0)

            # --- uzluksiz neon chiziq: segmentlangan, ko'p qatlamli stroke ---
            for s in range(0, len(pts) - 1, SEG_LEN):
                seg = pts[s: s + SEG_LEN + 1]          # 1 nuqta ustma-ust => uzilish yo'q
                if len(seg) < 2:
                    continue
                for w, op in GLOW_STROKES:
                    line = VMobject()
                    line.set_points_as_corners(seg)
                    # eng ichki qatlam oqroq => neon "yadro"
                    col = interpolate_color(ManimColor(base), WHITE,
                                            0.55 if w <= 2.0 else 0.0)
                    line.set_stroke(col, width=w, opacity=op)
                    line.set_fill(opacity=0)
                    structure.add(line)

            # --- ko'p qirrali shakllar chiziq ustida ---
            for i in range(0, len(pts), SHAPE_EVERY):
                sh = facet_shape(base)
                sh.move_to(pts[i])
                structure.add(sh)

        self.add(structure)

        # ============ 3. HARAKAT (mukammal loop) ============
        phase = ValueTracker(0.0)
        state = {"ang": 0.0, "z": 0.0}

        rot_total = TAU * ROT_TURNS          # ayniyat
        z_total = PITCH * FLOW_PITCHES       # vint simmetriyasi => ayniyat

        def flow(m):
            t = phase.get_value()
            ang = rot_total * rhythmic(t)    # ritmik ease_in_out aylanish
            z = z_total * t                  # bir tekis cheksiz oqim
            m.rotate(ang - state["ang"], axis=OUT, about_point=ORIGIN)
            m.shift(OUT * (z - state["z"]))
            state["ang"], state["z"] = ang, z

        structure.add_updater(flow)

        # ============ 4. KAMERA — qat'iy diagonal ============
        self.set_camera_orientation(phi=70 * DEGREES, theta=-35 * DEGREES)

        self.play(phase.animate.set_value(1.0),
                  run_time=LOOP_T, rate_func=linear)
        structure.clear_updaters()
