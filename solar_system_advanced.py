from manim import *
import numpy as np

# Kadrni kengaytiramiz: standart kadr 14.22 x 8 birlik, ya'ni Y o'qi faqat ±4.0 —
# Mars orbitasi (radius 5) unga sig'maydi. 11.0 balandlikda Y o'qi ±5.5 bo'ladi va
# Mars (5 + 0.18 = 5.18) chekkagacha 0.32 birlik zaxira bilan kadr ichida qoladi.
# config Scene yaratilishida bir marta o'qiladi, shuning uchun modul darajasida.
config.frame_height = 11.0
config.frame_width = 11.0 * config.aspect_ratio  # ≈ 19.56 (16:9)

# Yulduzlar tasodifiy joylashadi. Render uzilib qayta ishga tushsa, manim tugallangan
# animatsiyalarni keshdan oladi — seedsiz yangi yulduzlar chiqib, ulangan joyda sakrash
# ko'rinardi.
np.random.seed(42)


class SolarSystemAdvanced(Scene):
    def construct(self):
        # 1. Fazo foni (Orqa fonni haqiqiy koinotdek to'q ko'k-qora qilish)
        self.camera.background_color = "#050510"

        # 2. Yulduzlar (kengaytirilgan kadr bo'ylab, zichlik saqlanishi uchun 280 ta)
        x_max = config.frame_width / 2
        y_max = config.frame_height / 2
        stars = VGroup(*[
            Dot(
                radius=np.random.uniform(0.01, 0.03),
                color=WHITE,
                fill_opacity=np.random.uniform(0.3, 1)
            ).move_to([
                np.random.uniform(-x_max, x_max),
                np.random.uniform(-y_max, y_max),
                0,
            ])
            for _ in range(280)
        ])
        self.add(stars)

        # 3. Markaziy jism: Quyosh (0, 0, 0 koordinatasida qotirilgan)
        sun = Circle(radius=0.7, color="#FFD700", fill_opacity=1)
        sun_glow = Circle(radius=1.3, color="#FFA500", fill_opacity=0.2, stroke_width=0)
        self.play(FadeIn(sun), FadeIn(sun_glow), run_time=1.5)

        # 4. Yer va uning orbitasi (Radius = 3)
        earth_orbit = DashedVMobject(Circle(radius=3, color=BLUE_B, stroke_width=1.5), num_dashes=60)
        earth = Circle(radius=0.22, color=BLUE, fill_opacity=1)
        # t=0 dagi orbital nuqtaga qo'yamiz, aks holda Quyosh ichida paydo bo'lib,
        # animatsiya boshlanganda o'z joyiga sakrab o'tadi.
        earth.move_to([3, 0, 0])

        self.play(Create(earth_orbit), run_time=1.5)
        self.play(FadeIn(earth))

        # 5. Oy (Radius = 0.08) - Yerdan 0.6 masofada, t=0 holatida
        moon = Circle(radius=0.08, color=LIGHT_GREY, fill_opacity=1)
        moon.move_to([3.6, 0, 0])
        self.add(moon)

        # 6. Mars va uning orbitasi (Radius = 5, kengaytirilgan kadrga sig'adi)
        mars_orbit = DashedVMobject(Circle(radius=5, color=RED_D, stroke_width=1.5), num_dashes=80)
        mars = Circle(radius=0.18, color=RED, fill_opacity=1)
        mars.move_to([5, 0, 0])

        self.play(Create(mars_orbit), run_time=1.5)
        self.play(FadeIn(mars))

        # 7. VAQT TREKKERI (Animatsiyaning yuragi - barcha harakat shunga bog'lanadi)
        time_tracker = ValueTracker(0)

        # === HARAKAT QOIDALARI (UPDATERS) ===

        # Yer orbitasi bo'ylab harakatlanadi (Tezlik koeffitsiyenti: 0.5)
        def update_earth(mob):
            angle = time_tracker.get_value() * 0.5
            mob.move_to(np.array([3 * np.cos(angle), 3 * np.sin(angle), 0]))

        # Oy har doim Yerga bog'lanadi va uning atrofida aylanadi (Tezlik: 2.0, masofa: 0.6)
        # Manim mobjectlarni sahnaga qo'shilish tartibida yangilaydi — earth moon'dan
        # oldin qo'shilgani uchun bu yerda Yerning yangilangan pozitsiyasi o'qiladi.
        def update_moon(mob):
            earth_pos = earth.get_center()
            angle = time_tracker.get_value() * 2
            mob.move_to(earth_pos + np.array([0.6 * np.cos(angle), 0.6 * np.sin(angle), 0]))

        # Mars o'z orbitasida sekinroq aylanadi (Tezlik: 0.3)
        def update_mars(mob):
            angle = time_tracker.get_value() * 0.3
            mob.move_to(np.array([5 * np.cos(angle), 5 * np.sin(angle), 0]))

        # Qoidalarni jismlarga biriktiramiz
        earth.add_updater(update_earth)
        moon.add_updater(update_moon)
        mars.add_updater(update_mars)

        # 8. ASOSIY ANIMATSIYA (12 soniya davomida silliq harakatlanish)
        self.play(
            time_tracker.animate.set_value(20),
            run_time=12,
            rate_func=linear
        )

        # 9. TOZALASH (Keyingi kadrlar xato bermasligi uchun bog'lanishlarni uzamiz)
        earth.clear_updaters()
        moon.clear_updaters()
        mars.clear_updaters()

        # Videoni chiroyli yakunlash
        self.play(
            FadeOut(VGroup(sun, sun_glow, earth, earth_orbit, moon, mars, mars_orbit, stars)),
            run_time=2
        )
