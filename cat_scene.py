from manim import *

# Stol yuzasi: markaz DOWN*1.5, balandlik 2 => ustki qirra y = -0.5
TABLE_TOP = -0.5
CAT_R = 0.8
CAT_Y = TABLE_TOP + CAT_R          # mushuk stol ustida tursin

# Qora mushuk qora fonda ko'rinmasligi uchun: to'q kulrang to'ldirish + oq kontur
CAT_BLACK_FILL = "#1E1E1E"


class CatAnimationScene(Scene):
    def construct(self):
        # 1. Sahna va stol elementlarini yaratish
        table = Rectangle(width=6, height=2, color=LIGHT_GRAY).shift(DOWN * 1.5)
        table_label = Text("Stol", font_size=24, color=LIGHT_GRAY)
        table_label.move_to(table.get_center())

        # Ikki mushuk. Yorliq doira bilan BIR GURUHDA => birga harakatlanadi.
        cat_black = Circle(radius=CAT_R, color=WHITE, fill_opacity=1)
        cat_black.set_fill(CAT_BLACK_FILL).set_stroke(WHITE, width=3)
        cat_black.move_to([-1.5, CAT_Y, 0])
        cat_black_label = Text("Qora\nmushuk", font_size=18, color=WHITE,
                               line_spacing=0.6)
        cat_black_label.move_to(cat_black.get_center())
        black_cat = VGroup(cat_black, cat_black_label)

        cat_orange = Circle(radius=CAT_R, color=ORANGE, fill_opacity=1)
        cat_orange.set_stroke(WHITE, width=3)
        cat_orange.move_to([1.5, CAT_Y, 0])
        cat_orange_label = Text("Sariq\nmushuk", font_size=18, color=BLACK,
                                line_spacing=0.6)
        cat_orange_label.move_to(cat_orange.get_center())
        orange_cat = VGroup(cat_orange, cat_orange_label)

        # Sahnaga qo'shish (yorliqlar ham!)
        self.play(Create(table), Write(table_label), run_time=1)
        self.play(FadeIn(black_cat), FadeIn(orange_cat), run_time=1)
        self.wait(1)

        # 2. Birgalikda turish holati — ikkalasi biroz ko'tariladi
        self.play(
            black_cat.animate.shift(UP * 0.2),
            orange_cat.animate.shift(UP * 0.2),
            run_time=1
        )
        self.wait(1)

        # 3. Urishib qolish va birining yiqilishi
        # Qora mushuk zarba beradi
        self.play(black_cat.animate.shift(RIGHT * 0.5),
                  run_time=0.3, rate_func=rate_functions.ease_in_quad)
        self.play(black_cat.animate.shift(LEFT * 0.25), run_time=0.15)

        # Sariq mushuk stoldan pastga uchib tushadi (aylanib).
        # DIQQAT: .animate.shift(...) va Rotate(...) ni BITTA play() ichida
        # bir xil obyektga qo'llash mumkin emas — ular bir-birini bekor qiladi
        # (Rotate g'olib chiqib, siljish yo'qoladi). Shuning uchun har kadrda
        # holatni noldan quramiz: bitta ValueTracker => ham siljish, ham burilish.
        fall = ValueTracker(0.0)
        base = orange_cat.copy()

        def fall_update(m):
            p = fall.get_value()
            m.become(base.copy())
            m.rotate(-PI * p)
            m.shift(RIGHT * 1.6 * p + DOWN * 3.4 * p)

        orange_cat.add_updater(fall_update)
        self.play(fall.animate.set_value(1.0),
                  run_time=0.9, rate_func=rate_functions.ease_in_quad)
        orange_cat.clear_updaters()

        self.wait(2)
