"""Artificial Intelligence — a 10-second Manim animation.

Render with:
    manim -pql ai_animation.py

A neural network of three layers lights up as signal pulses travel from
the input layer to the output layer, then all nodes collapse into a
glowing "AI CORE" surrounded by a rotating luminous ring.
"""

from manim import *
import numpy as np

# Layer colors
INPUT_COLOR = BLUE_B       # Kirish qatlami — ko'k
HIDDEN_COLOR = PURPLE_B    # Yashirin qatlam — binafsha
OUTPUT_COLOR = GOLD        # Chiqish qatlami — oltin
EDGE_COLOR = GREY_B
PULSE_COLOR = WHITE


class ArtificialIntelligence(Scene):
    def construct(self):
        self.camera.background_color = "#0b0b0f"  # deep dark background

        # -- Build the three layers of nodes ---------------------------------
        layer_specs = [
            (-4.5, 3, INPUT_COLOR),   # x, count, color
            (0.0, 4, HIDDEN_COLOR),
            (4.5, 2, OUTPUT_COLOR),
        ]

        layers = []  # list of lists of node dots
        for x, count, color in layer_specs:
            ys = np.linspace(2.2, -2.2, count) if count > 1 else [0.0]
            nodes = VGroup()
            for y in ys:
                node = Dot(point=[x, y, 0], radius=0.22, color=color)
                node.set_sheen(0.4, UL)
                node.set_stroke(color, width=2, opacity=0.9)
                # soft glow halo behind each node
                glow = Dot(point=[x, y, 0], radius=0.42, color=color)
                glow.set_opacity(0.18)
                node.glow = glow
                nodes.add(node)
            layers.append(nodes)

        all_nodes = VGroup(*[n for layer in layers for n in layer])
        all_glows = VGroup(*[n.glow for layer in layers for n in layer])

        # -- Build edges between consecutive layers --------------------------
        edges = VGroup()
        edge_pairs = []  # (start_node, end_node, line)
        for a, b in [(0, 1), (1, 2)]:
            for na in layers[a]:
                for nb in layers[b]:
                    line = Line(
                        na.get_center(), nb.get_center(),
                        stroke_width=1.6, color=EDGE_COLOR,
                    )
                    line.set_opacity(0.35)
                    edges.add(line)
                    edge_pairs.append((na, nb, line))

        # === 1. Nodes appear =================================================
        self.play(
            LaggedStart(
                *[AnimationGroup(
                    GrowFromCenter(node.glow),
                    GrowFromCenter(node),
                ) for node in all_nodes],
                lag_ratio=0.08,
            ),
            run_time=1.6,
        )

        # === 2. Edges are drawn ==============================================
        self.play(
            LaggedStart(
                *[Create(line) for line in edges],
                lag_ratio=0.015,
            ),
            run_time=1.3,
        )

        # === 3. Signal pulses travel left -> right ===========================
        def pulse_wave(pairs, base_delay=0.0):
            anims = []
            for na, nb, line in pairs:
                pulse = Dot(radius=0.09, color=PULSE_COLOR)
                pulse.set_glow_factor(1.0) if hasattr(pulse, "set_glow_factor") else None
                pulse.move_to(na.get_center())
                anims.append(
                    Succession(
                        Wait(base_delay),
                        AnimationGroup(
                            MoveAlongPath(pulse, line),
                            line.animate.set_stroke(PULSE_COLOR, opacity=0.9),
                            rate_func=rate_functions.ease_in_out_sine,
                        ),
                        line.animate.set_stroke(EDGE_COLOR, opacity=0.35),
                        FadeOut(pulse, run_time=0.1),
                    )
                )
            return anims

        input_hidden = [p for p in edge_pairs if p[0] in layers[0]]
        hidden_output = [p for p in edge_pairs if p[0] in layers[1]]

        # first hop: input -> hidden, then flash the hidden nodes
        self.play(*pulse_wave(input_hidden), run_time=1.5)
        self.play(
            *[Flash(n, color=HIDDEN_COLOR, flash_radius=0.5, line_length=0.2)
              for n in layers[1]],
            run_time=0.5,
        )
        # second hop: hidden -> output, then flash the output nodes
        self.play(*pulse_wave(hidden_output), run_time=1.5)
        self.play(
            *[Flash(n, color=OUTPUT_COLOR, flash_radius=0.55, line_length=0.25)
              for n in layers[2]],
            run_time=0.5,
        )

        # === 4. Everything collapses into the AI CORE =======================
        core_point = ORIGIN
        network = VGroup(all_nodes, all_glows, edges)

        self.play(
            edges.animate.set_opacity(0),
            *[n.animate.move_to(core_point).scale(0.3) for n in all_nodes],
            *[g.animate.move_to(core_point).scale(0.3) for g in all_glows],
            run_time=1.2,
            rate_func=rate_functions.ease_in_expo,
        )

        # bright flash at the moment of collapse
        core_flash = Dot(core_point, radius=0.1, color=WHITE)
        self.add(core_flash)
        self.play(
            core_flash.animate.scale(30).set_opacity(0),
            FadeOut(all_nodes),
            FadeOut(all_glows),
            run_time=0.6,
        )
        self.remove(core_flash, network)

        # === 5. AI CORE text + rotating luminous ring =======================
        title = Text("AI CORE", weight=BOLD, font_size=60)
        title.set_color_by_gradient(BLUE_B, PURPLE_B, GOLD)

        ring = Circle(radius=1.6, color=BLUE_B, stroke_width=4)
        ring.set_stroke(opacity=0.9)
        ring2 = Circle(radius=2.0, color=PURPLE_B, stroke_width=2)
        ring2.set_stroke(opacity=0.6)

        # luminous arc that sweeps around the ring
        beam = Arc(radius=1.6, start_angle=0, angle=PI / 3,
                   color=WHITE, stroke_width=8)
        beam.set_stroke(opacity=0.95)

        self.play(
            Write(title),
            Create(ring),
            Create(ring2),
            run_time=0.8,
        )
        self.add(beam)
        self.play(
            Rotate(beam, angle=2 * PI, about_point=ORIGIN),
            Rotate(ring2, angle=-PI, about_point=ORIGIN),
            title.animate.scale(1.05),
            run_time=1.6,
            rate_func=linear,
        )
        self.wait(0.2)
