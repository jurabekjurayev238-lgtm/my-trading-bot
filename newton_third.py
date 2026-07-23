"""Nyutonning uchinchi qonuni — tushuntirish animatsiyasi (~3:50).

Manim Community. Har sahna alohida Scene klassi.

Render (bittalab):
    manim -pql newton_third.py S1Intro     # tez ko'rish
    manim -pqh newton_third.py S1Intro     # yakuniy render

Keyin barcha sahnalarni FFmpeg bilan ulang.
"""

from manim import *
import numpy as np

# ============================ CONSTANTS ==================================
FORCE_A = "#58C4DD"   # A jismga ta'sir qiluvchi kuch
FORCE_B = "#FF6B6B"   # B jismga ta'sir qiluvchi kuch
ACCENT = "#FFC857"    # ta'kidlash, formulalar
NEUTRAL = "#E8E8E8"   # matn, jismlar
BG = "#0E1116"        # qora fon

TITLE_SIZE = 48
BODY_SIZE = 32
SMALL_SIZE = 26

config.background_color = BG


# ========================= HELPER FUNCTIONS =============================
def force_arrow(start, end, color, label=None, label_dir=UP, label_scale=1.0):
    """Kuch strelkasi + ixtiyoriy formula belgisi (MathTex).

    start, end : strelka boshi va uchi (nuqtalar)
    color      : strelka rangi
    label      : LaTeX matn (masalan r"\\vec{F}_{AB}") yoki None
    label_dir  : belgining strelkaga nisbatan yo'nalishi
    """
    arrow = Arrow(
        start, end, color=color, buff=0,
        stroke_width=7, max_tip_length_to_length_ratio=0.28,
        max_stroke_width_to_length_ratio=12,
    )
    group = VGroup(arrow)
    if label is not None:
        tex = MathTex(label, color=color).scale(0.8 * label_scale)
        tex.next_to(arrow, label_dir, buff=0.15)
        group.add(tex)
    return group


def body_square(color=NEUTRAL, side=1.4, label=None):
    """Jism — kvadrat + ixtiyoriy harf belgisi."""
    sq = Square(side_length=side, color=color, fill_opacity=0.15)
    sq.set_stroke(color, width=3)
    grp = VGroup(sq)
    if label:
        t = Text(label, color=color, font_size=BODY_SIZE, weight=BOLD)
        t.move_to(sq.get_center())
        grp.add(t)
    return grp


def stick_figure(color=NEUTRAL, height=2.0):
    """Oddiy chiziqli odam figurasi (bosh, tana, qo'l, oyoq)."""
    head = Circle(radius=height * 0.13, color=color).set_stroke(color, 3)
    body = Line(ORIGIN, DOWN * height * 0.4, color=color, stroke_width=3)
    head.next_to(body, UP, buff=0)
    arms = Line(LEFT * height * 0.22, RIGHT * height * 0.22,
                color=color, stroke_width=3)
    arms.move_to(body.get_start() + DOWN * height * 0.13)
    leg_l = Line(body.get_end(), body.get_end() + DOWN * height * 0.35 + LEFT * height * 0.18,
                 color=color, stroke_width=3)
    leg_r = Line(body.get_end(), body.get_end() + DOWN * height * 0.35 + RIGHT * height * 0.18,
                 color=color, stroke_width=3)
    fig = VGroup(head, body, arms, leg_l, leg_r)
    return fig


def make_rocket(color=NEUTRAL, scale=1.0):
    """Oddiy raketa shakli."""
    body = RoundedRectangle(width=0.5, height=1.1, corner_radius=0.12,
                            color=color, fill_opacity=0.2).set_stroke(color, 3)
    nose = Triangle(color=color, fill_opacity=0.3).set_stroke(color, 3)
    nose.scale(0.35).next_to(body, UP, buff=-0.05)
    fin_l = Triangle(color=FORCE_B, fill_opacity=0.5).set_stroke(FORCE_B, 2)
    fin_l.scale(0.22).rotate(PI).next_to(body, DOWN, buff=-0.1).shift(LEFT * 0.22)
    fin_r = fin_l.copy().shift(RIGHT * 0.44)
    rocket = VGroup(body, nose, fin_l, fin_r).scale(scale)
    return rocket


# ============================== S1 — Ochilish ==========================
class S1Intro(MovingCameraScene):
    def construct(self):
        title = Text("Nyutonning uchinchi qonuni", color=NEUTRAL,
                     font_size=TITLE_SIZE, weight=BOLD)
        title.to_edge(UP, buff=0.6)

        rocket = make_rocket(color=NEUTRAL, scale=1.2)
        rocket.move_to(DOWN * 3.2)

        # gaz oqimi (raketa ortidan) — always_redraw bilan raketaga ergashadi
        flame_cols = [
            ManimColor(ACCENT).interpolate(ManimColor(FORCE_B), (k % 3) / 3)
            for k in range(6)
        ]
        flame = always_redraw(lambda: VGroup(*[
            Dot(radius=0.09, color=flame_cols[k], fill_opacity=0.7 - 0.1 * k)
            .move_to(rocket.get_bottom() + DOWN * (0.12 + 0.14 * k)
                     + RIGHT * ((k * 37 % 7) - 3) * 0.05)
            for k in range(6)
        ]))

        subtitle = Text("Ta'sir va aks ta'sir", color=ACCENT, font_size=BODY_SIZE)
        subtitle.next_to(title, DOWN, buff=0.4)

        self.add(rocket, flame)
        self.play(Write(title), run_time=2)
        self.wait(1)
        self.play(
            rocket.animate.move_to(UP * 1.0),
            self.camera.frame.animate.scale(1.25),
            run_time=4, rate_func=smooth,
        )
        self.wait(1)
        self.play(FadeIn(subtitle, shift=UP), run_time=1.5)
        self.wait(2.5)
        # raketa sekin yuqoriga suzadi
        self.play(rocket.animate.shift(UP * 0.6), run_time=2, rate_func=smooth)
        self.wait(1.5)


# ============================ S2 — Qonun bayoni ========================
class S2Statement(Scene):
    def construct(self):
        A = body_square(color=NEUTRAL, side=1.5, label="A").shift(LEFT * 0.85)
        B = body_square(color=NEUTRAL, side=1.5, label="B").shift(RIGHT * 0.85)
        bodies = VGroup(A, B).move_to(UP * 0.6)

        self.play(FadeIn(A, shift=RIGHT), FadeIn(B, shift=LEFT), run_time=1.5)
        self.wait(1)

        # A dan B ga (FORCE_B), B dan A ga (FORCE_A)
        a_right = A[0].get_right()
        b_left = B[0].get_left()
        mid = (a_right + b_left) / 2

        arrow_AB = force_arrow(mid, mid + RIGHT * 1.6, FORCE_B,
                               label=r"\vec{F}_{AB}", label_dir=UP).shift(UP * 0.0)
        arrow_BA = force_arrow(mid, mid + LEFT * 1.6, FORCE_A,
                               label=r"\vec{F}_{BA}", label_dir=DOWN)
        # ikkalasini biroz vertikal ajratamiz
        arrow_AB.shift(UP * 0.0)

        self.play(GrowArrow(arrow_AB[0]), FadeIn(arrow_AB[1]), run_time=1.5)
        self.wait(1)
        self.play(GrowArrow(arrow_BA[0]), FadeIn(arrow_BA[1]), run_time=1.5)
        self.wait(1.5)

        formula = MathTex(r"\vec{F}_{AB} = -\vec{F}_{BA}", color=ACCENT)
        formula.scale(1.3).to_edge(DOWN, buff=1.5)
        self.play(Write(formula), run_time=2)
        self.wait(2)

        caption = Text("Teng kattalik, qarama-qarshi yo'nalish",
                       color=NEUTRAL, font_size=BODY_SIZE)
        caption.next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(caption, shift=UP), run_time=1.5)
        self.wait(2)

        # strelkalar navbat bilan yonadi (ikki marta)
        for _ in range(2):
            self.play(Indicate(arrow_AB[0], color=ACCENT, scale_factor=1.15), run_time=1)
            self.play(Indicate(arrow_BA[0], color=ACCENT, scale_factor=1.15), run_time=1)
        self.wait(1.5)
        self.play(Indicate(formula, color=ACCENT, scale_factor=1.1), run_time=1.5)
        self.wait(2)


# ========================= S3 — Eng muhim nuqta ========================
class S3Different(Scene):
    def construct(self):
        divider = DashedLine(UP * 3.2, DOWN * 3.2, color=NEUTRAL, stroke_width=2)
        divider.set_opacity(0.4)

        title = Text("Kuchlar HAR XIL jismlarga ta'sir qiladi",
                     color=ACCENT, font_size=TITLE_SIZE - 4, weight=BOLD)
        title.to_edge(UP, buff=0.5)

        # Chapda: A jism + FORCE_A
        A = body_square(color=NEUTRAL, side=1.4, label="A").move_to(LEFT * 3.5 + DOWN * 0.3)
        force_on_A = force_arrow(A[0].get_right(), A[0].get_right() + RIGHT * 1.6,
                                 FORCE_A, label=r"\vec{F}_{BA}", label_dir=UP)
        left_lbl = Text("A jismga ta'sir", color=FORCE_A, font_size=SMALL_SIZE)
        left_lbl.next_to(A, DOWN, buff=0.6)

        # O'ngda: B jism + FORCE_B
        B = body_square(color=NEUTRAL, side=1.4, label="B").move_to(RIGHT * 3.5 + DOWN * 0.3)
        force_on_B = force_arrow(B[0].get_left(), B[0].get_left() + LEFT * 1.6,
                                 FORCE_B, label=r"\vec{F}_{AB}", label_dir=UP)
        right_lbl = Text("B jismga ta'sir", color=FORCE_B, font_size=SMALL_SIZE)
        right_lbl.next_to(B, DOWN, buff=0.6)

        self.play(Write(title), Create(divider), run_time=2)
        self.wait(1)
        self.play(FadeIn(A, shift=RIGHT), FadeIn(B, shift=LEFT), run_time=1.5)
        self.wait(1.5)
        self.play(
            GrowArrow(force_on_A[0]), FadeIn(force_on_A[1]),
            FadeIn(left_lbl, shift=UP),
            run_time=1.5,
        )
        self.wait(2)
        self.play(
            GrowArrow(force_on_B[0]), FadeIn(force_on_B[1]),
            FadeIn(right_lbl, shift=UP),
            run_time=1.5,
        )
        self.wait(2)
        # ta'kid — sekin, navbat bilan
        self.play(Indicate(A, color=FORCE_A, scale_factor=1.15), run_time=1.5)
        self.wait(1)
        self.play(Indicate(B, color=FORCE_B, scale_factor=1.15), run_time=1.5)
        self.wait(1.5)

        # eng muhim fikr — pastda ta'kidlangan holda
        key = Text("Bir kuch — A da, ikkinchisi — B da. Ular hech qachon "
                   "bir jismda emas.", color=NEUTRAL, font_size=SMALL_SIZE)
        key.to_edge(DOWN, buff=0.7)
        self.play(FadeIn(key, shift=UP), run_time=2)
        self.wait(2)
        self.play(
            Indicate(A, color=FORCE_A, scale_factor=1.1),
            Indicate(B, color=FORCE_B, scale_factor=1.1),
            run_time=2,
        )
        self.wait(2)


# ======================= S4 — Keng tarqalgan xato ======================
class S4Mistake(Scene):
    def construct(self):
        question = Text("Agar kuchlar teng bo'lsa, nega harakat bo'ladi?",
                        color=NEUTRAL, font_size=BODY_SIZE)
        question.to_edge(UP, buff=0.7)
        self.play(Write(question), run_time=2)
        self.wait(2)

        # NOTO'G'RI: ikki kuch bir jismda
        wrong_body = body_square(color=NEUTRAL, side=1.5, label="A").move_to(DOWN * 0.3)
        f1 = force_arrow(wrong_body[0].get_center(),
                         wrong_body[0].get_center() + RIGHT * 1.8, FORCE_B)
        f2 = force_arrow(wrong_body[0].get_center(),
                         wrong_body[0].get_center() + LEFT * 1.8, FORCE_A)
        wrong_label = Text("Bir jismda ikki kuch?", color=NEUTRAL, font_size=SMALL_SIZE)
        wrong_label.next_to(wrong_body, DOWN, buff=1.2)

        self.play(FadeIn(wrong_body), run_time=1)
        self.play(GrowArrow(f1[0]), GrowArrow(f2[0]),
                  FadeIn(wrong_label), run_time=1.3)
        self.wait(2)

        # qizil X
        cross = VGroup(
            Line(UL, DR, color=FORCE_B, stroke_width=10),
            Line(UR, DL, color=FORCE_B, stroke_width=10),
        ).scale(0.9).move_to(wrong_body)
        self.play(Create(cross), run_time=0.8)
        self.wait(2)
        self.play(FadeOut(VGroup(wrong_body, f1, f2, wrong_label, cross)),
                  run_time=1)
        self.wait(0.5)

        # TO'G'RI: har biri o'z jismida
        A = body_square(color=NEUTRAL, side=1.3, label="A").move_to(LEFT * 2.2 + DOWN * 0.3)
        B = body_square(color=NEUTRAL, side=1.3, label="B").move_to(RIGHT * 2.2 + DOWN * 0.3)
        fA = force_arrow(A[0].get_right(), A[0].get_right() + RIGHT * 1.3, FORCE_A)
        fB = force_arrow(B[0].get_left(), B[0].get_left() + LEFT * 1.3, FORCE_B)

        self.play(FadeIn(A, shift=RIGHT), FadeIn(B, shift=LEFT), run_time=1.2)
        self.wait(1)
        self.play(GrowArrow(fA[0]), GrowArrow(fB[0]), run_time=1.5)
        self.wait(1.5)

        check = VGroup(
            Line(ORIGIN, RIGHT * 0.3 + DOWN * 0.4, color=GREEN, stroke_width=10),
            Line(RIGHT * 0.3 + DOWN * 0.4, RIGHT * 0.9 + UP * 0.5, color=GREEN, stroke_width=10),
        ).move_to(UP * 1.2)
        self.play(Create(check), run_time=0.8)
        self.wait(1.5)

        answer = Text("Ular bir jismda emas — shuning uchun bir-birini yo'qotmaydi",
                      color=ACCENT, font_size=SMALL_SIZE)
        answer.to_edge(DOWN, buff=0.7)
        self.play(FadeIn(answer, shift=UP), run_time=2)
        self.wait(2.5)


# ========================= S5 — Misol 1: Yurish ========================
class S5Walking(MovingCameraScene):
    def construct(self):
        ground = Line(LEFT * 7, RIGHT * 7, color=NEUTRAL, stroke_width=3)
        ground.to_edge(DOWN, buff=1.2).set_opacity(0.6)

        person = stick_figure(color=NEUTRAL, height=2.2)
        person.next_to(ground, UP, buff=0).shift(LEFT * 2)

        title = Text("Misol 1: Yurish", color=ACCENT, font_size=TITLE_SIZE - 6,
                     weight=BOLD).to_edge(UP, buff=0.6)

        self.camera.frame.save_state()
        self.play(Write(title), Create(ground), run_time=2)
        self.play(FadeIn(person, shift=UP), run_time=1.2)
        self.wait(1.5)

        # qadam tashlash (biroz oldinga siljish)
        self.play(person.animate.shift(RIGHT * 1.2), run_time=1.5, rate_func=smooth)
        self.wait(1)

        # oyoq-yer kontakt nuqtasi
        contact = person[3].get_end()  # chap oyoq uchi

        # kamera zoom kontaktga
        self.play(
            self.camera.frame.animate.scale(0.5).move_to(contact + UP * 0.3),
            run_time=2,
        )
        self.wait(1.5)

        # oyoqdan yerga orqaga strelka, yerdan oyoqqa oldinga strelka
        back_arrow = force_arrow(contact, contact + LEFT * 0.9 + DOWN * 0.1,
                                 FORCE_B)
        fwd_arrow = force_arrow(contact + DOWN * 0.05,
                                contact + RIGHT * 0.9 + UP * 0.05, FORCE_A)
        self.play(GrowArrow(back_arrow[0]), run_time=1.2)
        self.wait(1.5)
        self.play(GrowArrow(fwd_arrow[0]), run_time=1.2)
        self.wait(1.5)

        caption = Text("Oyoq yerni orqaga itaradi → yer oyoqni oldinga itaradi",
                       color=NEUTRAL, font_size=18)
        caption.move_to(self.camera.frame.get_center() + UP * 1.3)
        self.play(FadeIn(caption), run_time=2)
        self.wait(2.5)

        # kamera qaytadi — odam bir necha qadam oldinga yuradi
        self.play(
            Restore(self.camera.frame),
            FadeOut(caption), FadeOut(back_arrow), FadeOut(fwd_arrow),
            run_time=2,
        )
        self.wait(1)
        for _ in range(2):
            self.play(person.animate.shift(RIGHT * 1.6), run_time=1.3,
                      rate_func=smooth)
            self.wait(0.5)
        self.wait(1.5)


# ========================= S6 — Misol 2: Raketa ========================
class S6Rocket(Scene):
    def construct(self):
        title = Text("Misol 2: Raketa", color=ACCENT, font_size=TITLE_SIZE - 6,
                     weight=BOLD).to_edge(UP, buff=0.6)

        rocket = make_rocket(color=NEUTRAL, scale=1.6).move_to(UP * 0.8)

        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(rocket, shift=DOWN), run_time=1.5)
        self.wait(1.5)

        # raketaga yuqoriga katta strelka
        up_arrow = force_arrow(rocket.get_center(), rocket.get_center() + UP * 2.0,
                               FORCE_A, label=r"\vec{F}_{\text{raketa}}", label_dir=RIGHT)
        self.play(GrowArrow(up_arrow[0]), FadeIn(up_arrow[1]), run_time=1.5)
        self.wait(1.5)

        # gaz zarrachalari pastga otiladi — ikki marta (takroriy burst)
        def gas_burst(run_time=1.8):
            particles = VGroup()
            for i in range(6):
                d = Dot(radius=0.1, color=ACCENT).move_to(
                    rocket.get_bottom() + RIGHT * (i - 2.5) * 0.18)
                particles.add(d)
            self.play(LaggedStart(*[FadeIn(p) for p in particles], lag_ratio=0.1),
                      run_time=0.8)
            down_arrows = VGroup(*[
                force_arrow(p.get_center(), p.get_center() + DOWN * 0.8, FORCE_B)[0]
                for p in particles
            ])
            self.play(
                LaggedStart(*[GrowArrow(a) for a in down_arrows], lag_ratio=0.08),
                *[p.animate.shift(DOWN * 2.5).set_opacity(0.15) for p in particles],
                run_time=run_time,
            )
            self.remove(particles, down_arrows)

        gas_burst()
        self.wait(1)
        gas_burst()
        self.wait(1)
        gas_burst()
        self.wait(1.5)

        caption = Text("Gaz pastga → raketa yuqoriga", color=NEUTRAL,
                       font_size=BODY_SIZE).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(caption, shift=UP), run_time=1.5)
        self.wait(1.5)
        # raketa yuqoriga ko'tariladi
        self.play(rocket.animate.shift(UP * 0.8), up_arrow.animate.shift(UP * 0.8),
                  run_time=2, rate_func=smooth)
        self.wait(1.5)


# ===================== S7 — Raqamli misol: konkichilar =================
class S7Skaters(Scene):
    def construct(self):
        ice = Line(LEFT * 7, RIGHT * 7, color=FORCE_A, stroke_width=3)
        ice.to_edge(DOWN, buff=1.0).set_opacity(0.4)

        A = stick_figure(color=NEUTRAL, height=1.8).next_to(ice, UP, buff=0).shift(LEFT * 2.0)
        B = stick_figure(color=NEUTRAL, height=2.1).next_to(ice, UP, buff=0).shift(RIGHT * 2.0)
        A_lbl = Text("A = 60 kg", color=FORCE_A, font_size=SMALL_SIZE).next_to(A, LEFT, buff=0.3)
        B_lbl = Text("B = 90 kg", color=FORCE_B, font_size=SMALL_SIZE).next_to(B, RIGHT, buff=0.3)

        self.play(Create(ice), FadeIn(A), FadeIn(B),
                  Write(A_lbl), Write(B_lbl), run_time=2)
        self.wait(1.5)

        # teng kuchlar (F = 180 N) — figuralar orasida, ko'krak balandligida
        mid = (A.get_top() + B.get_top()) / 2 + DOWN * 0.3
        fA = force_arrow(mid, mid + LEFT * 1.5, FORCE_A, label=r"180\,\text{N}", label_dir=UP)
        fB = force_arrow(mid, mid + RIGHT * 1.5, FORCE_B, label=r"180\,\text{N}", label_dir=UP)
        self.play(GrowArrow(fA[0]), FadeIn(fA[1]),
                  GrowArrow(fB[0]), FadeIn(fB[1]), run_time=1.5)
        self.wait(2)

        # hisob
        calc = VGroup(
            MathTex(r"a_A = \frac{180}{60} = 3\ \text{m/s}^2", color=FORCE_A),
            MathTex(r"a_B = \frac{180}{90} = 2\ \text{m/s}^2", color=FORCE_B),
        ).arrange(DOWN, buff=0.4).to_edge(UP, buff=0.7)
        self.play(Write(calc[0]), run_time=1.5)
        self.wait(1.5)
        self.play(Write(calc[1]), run_time=1.5)
        self.wait(2)

        # teskari yo'nalishda siljish — A tezroq
        self.play(
            VGroup(A, A_lbl).animate.shift(LEFT * 2.4),
            VGroup(B, B_lbl).animate.shift(RIGHT * 1.6),
            FadeOut(VGroup(fA, fB)),
            run_time=2.5, rate_func=smooth,
        )
        self.wait(2)

        # tezlanishlarni qayta ta'kidlash — A tezroq
        self.play(Indicate(calc[0], color=ACCENT, scale_factor=1.15), run_time=1.5)
        self.wait(1)
        self.play(Indicate(calc[1], color=ACCENT, scale_factor=1.15), run_time=1.5)
        self.wait(1.5)

        summary = Text("Kuch teng, lekin tezlanish massaga bog'liq",
                       color=ACCENT, font_size=BODY_SIZE).to_edge(DOWN, buff=0.6)
        self.play(FadeIn(summary, shift=UP), run_time=2)
        self.wait(2.5)


# ==================== S8 — Impuls bilan bog'lanish =====================
class S8Momentum(Scene):
    def construct(self):
        # bosqichma-bosqich: kuchdan impulsga
        step1 = MathTex(r"\vec{F}_{AB} = -\vec{F}_{BA}", color=NEUTRAL).scale(1.2)
        step1.to_edge(UP, buff=1.2)
        self.play(Write(step1), run_time=1.5)
        self.wait(2)

        step2 = MathTex(r"m_A \cdot \vec{a}_A = -\,m_B \cdot \vec{a}_B",
                        color=NEUTRAL).scale(1.2)
        step2.next_to(step1, DOWN, buff=0.7)
        self.play(TransformFromCopy(step1, step2), run_time=1.8)
        self.wait(2)

        formula = MathTex(r"m_A \cdot v_A = m_B \cdot v_B", color=ACCENT).scale(1.6)
        formula.next_to(step2, DOWN, buff=1.0)
        self.play(Write(formula), run_time=2)
        self.wait(2)

        caption = Text("Uchinchi qonundan impuls saqlanishi kelib chiqadi",
                       color=NEUTRAL, font_size=BODY_SIZE)
        caption.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(caption, shift=UP), run_time=1.5)
        self.wait(2)
        self.play(Indicate(formula, color=ACCENT, scale_factor=1.1), run_time=1.5)
        self.wait(2)


# ============================= S9 — Xulosa =============================
class S9Summary(MovingCameraScene):
    def construct(self):
        title = Text("Xulosa", color=ACCENT, font_size=TITLE_SIZE, weight=BOLD)
        title.to_edge(UP, buff=0.8)
        self.play(Write(title), run_time=1.2)

        points = [
            "1. Kuchlar har doim juft",
            "2. Kattaligi teng",
            "3. Yo'nalishi qarama-qarshi",
            "4. Har xil jismlarga ta'sir qiladi",
        ]
        colors = [NEUTRAL, FORCE_A, FORCE_B, ACCENT]
        items = VGroup(*[
            Text(p, color=c, font_size=BODY_SIZE)
            for p, c in zip(points, colors)
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to(DOWN * 0.3)

        for it in items:
            self.play(FadeIn(it, shift=RIGHT), run_time=0.8)
            self.wait(1.0)

        self.wait(2)
        # kamera zoom-out, fade to black
        everything = VGroup(title, items)
        self.play(
            self.camera.frame.animate.scale(1.3),
            run_time=2.5, rate_func=smooth,
        )
        self.play(FadeOut(everything), run_time=2)
        self.wait(0.5)
