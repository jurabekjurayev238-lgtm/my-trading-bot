"""Free Kick Goal Trajectory — jarima zarbasi tahlili (~15s, 1080p).

Render:
    manim -pqh freekick_tactic.py FreeKickGoal

Sahna: to'q yashil maydon, 7-raqamli hujumchi (ko'k), 4 kishilik jonli
devor (qizil), darvozabon. To'p devor ustidan aylanma traektoriya bilan
o'tib, darvozaning yuqori o'ng burchagiga tushadi; orqasida harakat
chizig'i (trace) qoladi. Darvozabon sakraydi, lekin yetolmaydi.
"""

from manim import *
import numpy as np

# ---------------- ranglar ----------------
PITCH_DARK   = "#0B3D14"   # to'q yashil maydon
PITCH_LIGHT  = "#10501C"   # och yashil zolak
LINE_WHITE   = "#DFF0DF"   # maydon chiziqlari
ATTACK_BLUE  = "#2E7BFF"   # 7-raqamli hujumchi
WALL_RED     = "#E03131"   # jonli devor
KEEPER_GOLD  = "#FFD43B"   # darvozabon
TRACE_GOLD   = "#FFD166"   # to'p izi
GOAL_MINT    = "#38D9A9"   # GOL! yozuvi
STAT_GOLD    = "#FFC857"   # statistika

# ---------------- maydon geometriyasi ----------------
GROUND_Y  = -3.05          # yer chizig'i
POST_L    = 4.55           # chap ustun
POST_R    = 6.95           # o'ng ustun
CROSSBAR  = 0.30           # to'sin balandligi
WALL_X    = 1.05           # jonli devor markazi
BALL_START = np.array([-3.35, GROUND_Y + 0.22, 0])
BALL_END   = np.array([6.48, CROSSBAR - 0.42, 0])   # yuqori o'ng burchak


def player(color, number=None, r=0.30):
    """Oddiy o'yinchi belgisi: rangli doira + ixtiyoriy raqam."""
    body = Circle(radius=r, color=color, fill_opacity=1)
    body.set_stroke(WHITE, width=2.5)
    grp = VGroup(body)
    if number is not None:
        t = Text(str(number), font_size=24, weight=BOLD, color=WHITE)
        t.move_to(body.get_center())
        grp.add(t)
    # yer soyasi
    shadow = Ellipse(width=r * 2.1, height=r * 0.5, color=BLACK,
                     fill_opacity=0.28, stroke_width=0)
    shadow.move_to(body.get_center() + DOWN * (r + 0.06))
    grp.add_to_back(shadow)
    return grp


def make_ball(r=0.13):
    """To'p: oq doira + qora panellar (aylanishi ko'rinsin)."""
    core = Circle(radius=r, color=WHITE, fill_opacity=1).set_stroke(GREY_D, 1.5)
    panels = VGroup()
    for a in [0, TAU / 3, 2 * TAU / 3]:
        p = RegularPolygon(5, radius=r * 0.42, color=BLACK, fill_opacity=1,
                           stroke_width=0)
        p.move_to(core.get_center() + np.array([np.cos(a), np.sin(a), 0]) * r * 0.5)
        panels.add(p)
    return VGroup(core, panels)


class FreeKickGoal(Scene):
    def construct(self):
        self.camera.background_color = PITCH_DARK

        # ============ 1. MAYDON (fon) ============
        stripes = VGroup()
        n = 9
        w = config.frame_width / n
        for i in range(n):
            r = Rectangle(width=w, height=config.frame_height, stroke_width=0,
                          fill_color=PITCH_LIGHT if i % 2 == 0 else PITCH_DARK,
                          fill_opacity=1)
            r.move_to(LEFT * config.frame_width / 2 + RIGHT * w * (i + 0.5))
            stripes.add(r)

        ground = Line([-8, GROUND_Y, 0], [8, GROUND_Y, 0],
                      color=LINE_WHITE, stroke_width=3).set_opacity(0.55)
        # jarima maydonchasi chizig'i
        box = Line([2.1, GROUND_Y, 0], [2.1, GROUND_Y + 1.5, 0],
                   color=LINE_WHITE, stroke_width=2.5).set_opacity(0.30)
        spot = Dot([-3.35, GROUND_Y + 0.02, 0], radius=0.05,
                   color=LINE_WHITE).set_opacity(0.6)

        pitch = VGroup(stripes, ground, box, spot)
        self.add(pitch)

        # ============ 2. DARVOZA ============
        post_l = Line([POST_L, GROUND_Y, 0], [POST_L, CROSSBAR, 0],
                      color=WHITE, stroke_width=9)
        post_r = Line([POST_R, GROUND_Y, 0], [POST_R, CROSSBAR, 0],
                      color=WHITE, stroke_width=9)
        bar = Line([POST_L, CROSSBAR, 0], [POST_R, CROSSBAR, 0],
                   color=WHITE, stroke_width=9)
        net = VGroup()
        for x in np.linspace(POST_L, POST_R, 9):
            net.add(Line([x, GROUND_Y, 0], [x, CROSSBAR, 0],
                         color=WHITE, stroke_width=1).set_opacity(0.22))
        for y in np.linspace(GROUND_Y, CROSSBAR, 7):
            net.add(Line([POST_L, y, 0], [POST_R, y, 0],
                         color=WHITE, stroke_width=1).set_opacity(0.22))
        goal = VGroup(net, post_l, post_r, bar)

        self.play(FadeIn(goal, shift=LEFT * 0.4), run_time=1.0)

        # ============ 3. SARLAVHA ============
        title = Text("JARIMA ZARBASI TAHLILI", font_size=46, weight=BOLD)
        title.set_color_by_gradient(WHITE, STAT_GOLD)
        title.to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=1.2)
        self.wait(0.4)
        self.play(title.animate.scale(0.55).to_corner(UL, buff=0.45).set_opacity(0.75),
                  run_time=0.6)

        # ============ 4. O'YINCHILAR ============
        attacker = player(ATTACK_BLUE, 7, r=0.32)
        attacker.move_to([-4.55, GROUND_Y + 0.38, 0])

        wall = VGroup()
        for i in range(4):                      # 4 kishilik jonli devor
            d = player(WALL_RED, r=0.29)
            d.move_to([WALL_X + (i - 1.5) * 0.62, GROUND_Y + 0.35, 0])
            wall.add(d)

        keeper = player(KEEPER_GOLD, r=0.30)
        keeper.move_to([5.75, GROUND_Y + 0.36, 0])

        ball = make_ball()
        ball.move_to(BALL_START)

        self.play(
            LaggedStart(
                FadeIn(attacker, shift=UP * 0.3),
                LaggedStart(*[FadeIn(d, shift=UP * 0.25) for d in wall],
                            lag_ratio=0.12),
                FadeIn(keeper, shift=UP * 0.3),
                GrowFromCenter(ball),
                lag_ratio=0.35,
            ),
            run_time=1.6,
        )

        # yorliqlar
        lbl_wall = Text("JONLI DEVOR", font_size=20, color=WALL_RED, weight=BOLD)
        lbl_wall.next_to(wall, DOWN, buff=0.18)
        lbl_keep = Text("DARVOZABON", font_size=20, color=KEEPER_GOLD, weight=BOLD)
        lbl_keep.next_to(keeper, DOWN, buff=0.18)
        # masofa ko'rsatkichi
        dist = DoubleArrow([BALL_START[0], GROUND_Y - 0.40, 0],
                           [POST_L, GROUND_Y - 0.40, 0],
                           buff=0, color=LINE_WHITE, stroke_width=3,
                           tip_length=0.18).set_opacity(0.75)
        dist_t = Text("27 m", font_size=22, color=LINE_WHITE, weight=BOLD)
        dist_t.next_to(dist, DOWN, buff=0.08)

        self.play(FadeIn(lbl_wall), FadeIn(lbl_keep), run_time=0.45)
        self.play(FadeIn(dist), FadeIn(dist_t), run_time=0.5)
        self.wait(0.25)

        # ============ 5. TRAEKTORIYA (aylanma yo'l) ============
        path = VMobject()
        path.set_points_smoothly([
            BALL_START,
            [-1.85, GROUND_Y + 1.55, 0],
            [0.30, 0.95, 0],
            [WALL_X + 0.35, 1.62, 0],      # devor ustidan baland
            [3.30, 1.48, 0],
            [5.30, 0.70, 0],
            BALL_END,                      # yuqori o'ng burchak
        ])
        path.set_stroke(width=0)

        # iz (trace): qalin xira + ingichka yorqin
        trace_glow = path.copy().set_stroke(TRACE_GOLD, width=13, opacity=0.22)
        trace_line = path.copy().set_stroke(TRACE_GOLD, width=4.5, opacity=0.95)

        # ============ 6. YUGURIB KELISH VA ZARBA ============
        self.play(attacker.animate.move_to([-3.95, GROUND_Y + 0.38, 0]),
                  run_time=0.7, rate_func=rate_functions.ease_in_quad)
        self.play(
            Flash(ball.get_center(), color=WHITE, flash_radius=0.55,
                  line_length=0.28, num_lines=14),
            attacker.animate.scale(1.12),
            run_time=0.35,
        )
        self.play(attacker.animate.scale(1 / 1.12), run_time=0.2)

        # ============ 7. TO'P UCHISHI + DARVOZABON SAKRASHI ============
        ball.add_updater(lambda m, dt: m.rotate(-0.30))   # aylanish (spin)

        keeper_top = np.array([5.62, GROUND_Y + 1.48, 0])   # sakrash cho'qqisi
        keeper_mid = np.array([5.55, GROUND_Y + 0.95, 0])   # yetolmay tusha boshlaydi

        # MUHIM: rate_func'ni har animatsiyaga alohida beramiz. Global rate_func
        # Succession'ning ichki vaqtini buzadi (darvozabon erta tushib qoladi).
        self.play(
            MoveAlongPath(ball, path, rate_func=rate_functions.ease_out_sine),
            Create(trace_glow, rate_func=rate_functions.ease_out_sine),
            Create(trace_line, rate_func=rate_functions.ease_out_sine),
            Succession(
                Wait(1.45),                      # to'p yaqinlashguncha kutadi
                keeper.animate(run_time=0.75,
                               rate_func=rate_functions.ease_out_quad
                               ).move_to(keeper_top).rotate(-0.35),
                keeper.animate(run_time=0.40,
                               rate_func=rate_functions.ease_in_quad
                               ).move_to(keeper_mid),
                rate_func=linear,
            ),
            run_time=2.6,
        )
        ball.clear_updaters()

        # ============ 8. GOL! ============
        net_flash = Rectangle(width=POST_R - POST_L, height=CROSSBAR - GROUND_Y,
                              stroke_width=0, fill_color=GOAL_MINT, fill_opacity=0.0)
        net_flash.move_to([(POST_L + POST_R) / 2, (CROSSBAR + GROUND_Y) / 2, 0])
        self.add(net_flash)

        goal_t = Text("GOL!", font_size=86, weight=BOLD)
        goal_t.set_color_by_gradient(GOAL_MINT, WHITE)
        goal_t.move_to([0.2, 2.15, 0])

        self.play(
            Flash(BALL_END, color=GOAL_MINT, flash_radius=0.9,
                  line_length=0.45, num_lines=18),
            net_flash.animate.set_fill(opacity=0.30),
            FadeIn(goal_t, scale=1.5),
            # darvozabon yetolmay yerga tushib bo'ladi
            keeper.animate(rate_func=rate_functions.ease_in_quad
                           ).move_to([5.48, GROUND_Y + 0.30, 0]).rotate(0.35),
            run_time=0.75,
        )
        self.play(net_flash.animate.set_fill(opacity=0.0), run_time=0.5)

        # ============ 9. STATISTIKA ============
        panel = RoundedRectangle(width=7.5, height=2.05, corner_radius=0.22,
                                 stroke_color=STAT_GOLD, stroke_width=3,
                                 fill_color=BLACK, fill_opacity=0.72)
        panel.move_to([0.0, -0.85, 0])

        s1 = Text("Zarba tezligi:  112 km/soat", font_size=36, weight=BOLD,
                  color=STAT_GOLD)
        s2 = Text("Masofa:  27 metr", font_size=36, weight=BOLD, color=WHITE)
        stats = VGroup(s1, s2).arrange(DOWN, buff=0.34, aligned_edge=LEFT)
        stats.move_to(panel.get_center())

        self.play(FadeOut(dist), FadeOut(dist_t),
                  FadeOut(lbl_wall), FadeOut(lbl_keep), run_time=0.4)
        self.play(DrawBorderThenFill(panel), run_time=0.6)
        self.play(FadeIn(s1, shift=RIGHT * 0.3), run_time=0.5)
        self.play(FadeIn(s2, shift=RIGHT * 0.3), run_time=0.5)
        self.play(Indicate(s1, color=WHITE, scale_factor=1.06), run_time=0.6)
        self.wait(1.0)
