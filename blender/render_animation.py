"""Koinot sahnasidan animatsiya kadrlarini render qiladi (3 rakurs, uzluksiz vaqt).

`solar_system.py` dan keyin ishga tushiriladi va sahna dizayniga tegmaydi -
faqat render sozlamalarini va vaqtinchalik kameralarni qo'shadi.

Kadrlar bitta raqamlangan ketma-ketlikka yoziladi: frame_0001.png, frame_0002.png ...
Keyin `encode_video.py` ularni bitta mp4 ga yig'adi:

    SOLAR_TEXTURE_FOLDER=/path/to/textures \\
    blender --background --factory-startup \\
        --python blender/solar_system.py \\
        --python blender/render_animation.py -- --out ./anim

    blender --background --factory-startup \\
        --python blender/encode_video.py -- --frames ./anim --out ./koinot.mp4

Sozlamalar muhit o'zgaruvchilari orqali:

    ANIM_SHOT_FRAMES   Har bir rakursdagi kadrlar soni (standart 72 = 24 fps da 3 soniya)
    ANIM_FRAME_STEP    Sahna vaqtining qadami (standart 3 - harakatni tezlashtiradi)
    ANIM_SAMPLES       Cycles namunalari (standart 24)
    ANIM_RES_X/Y       O'lcham (standart 1280x720)

Diqqat: bu Cycles CPU renderi. 216 kadr 4 yadroli mashinada ~40 daqiqa oladi.
Sinash uchun avval ANIM_SHOT_FRAMES=2 bilan ishga tushiring.
"""
import os
import sys
import math
import time

import bpy

OUT_DIR = sys.argv[sys.argv.index("--out") + 1]
SHOT_FRAMES = int(os.environ.get("ANIM_SHOT_FRAMES", "72"))
# Har bir renderlangan kadr uchun sahna vaqti necha kadrga suriladi.
# 1 dan katta qiymat harakatni tezlashtiradi - kamroq kadr renderlab, ko'proq harakat
FRAME_STEP = int(os.environ.get("ANIM_FRAME_STEP", "3"))
SAMPLES = int(os.environ.get("ANIM_SAMPLES", "24"))
RES_X = int(os.environ.get("ANIM_RES_X", "1280"))
RES_Y = int(os.environ.get("ANIM_RES_Y", "720"))

os.makedirs(OUT_DIR, exist_ok=True)
scene = bpy.context.scene

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.transparent_max_bounces = 4

scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'

saturn = bpy.data.objects["Saturn"]
sun = bpy.data.objects["Sun"]
main_camera = bpy.data.objects["Main_Camera"]


def add_tracking_camera(name, target, offset, parent_to_target, lens=50.0):
    camera_data = bpy.data.cameras.new(name)
    camera_data.lens = lens
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    if parent_to_target:
        camera.parent = target
        camera.matrix_parent_inverse.identity()
    camera.location = offset
    track = camera.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    return camera


overview_camera = add_tracking_camera(
    "Anim_Overview", sun, (6.0, -64.0, 40.0), parent_to_target=False, lens=45.0)
saturn_camera = add_tracking_camera(
    "Anim_Saturn", saturn, (-7.0, -7.0, 4.5), parent_to_target=True, lens=60.0)

background_node = scene.world.node_tree.nodes.get("Background")
base_background = tuple(background_node.inputs[0].default_value) if background_node else None


def apply_exposure(stops):
    scene.view_settings.exposure = stops
    if background_node and base_background:
        factor = 2.0 ** -stops
        background_node.inputs[0].default_value = (
            base_background[0] * factor, base_background[1] * factor,
            base_background[2] * factor, base_background[3])


def move_saturn_camera(progress):
    """Saturn atrofida yoritilgan tomonda yoy bo'ylab aylanadi (reveal kadri).

    Sayyoraning lokal -X o'qi (180 gradus) Quyoshga qaraydi, shuning uchun
    190-260 gradus oralig'i halqani yoritilgan holda ko'rsatadi.
    """
    angle = math.radians(190.0 + 70.0 * progress)
    radius = 9.9
    height = 3.5 + 2.0 * progress
    saturn_camera.location = (radius * math.cos(angle), radius * math.sin(angle), height)


# (nom, kamera, ekspozitsiya, kamera harakati)
shots = (
    ("Umumiy ko'rinish", overview_camera, 1.0, None),
    ("Yer kuzatuv kamerasi", main_camera, 1.5, None),
    ("Saturn halqasi", saturn_camera, 4.0, move_saturn_camera),
)

total_frames = SHOT_FRAMES * len(shots)
print(f"\n=== Animatsiya: {RES_X}x{RES_Y}, {SAMPLES} samples, "
      f"{len(shots)} rakurs x {SHOT_FRAMES} kadr = {total_frames} kadr ===")

output_index = 0
scene_frame = 1
run_started = time.time()

for shot_name, camera, exposure, camera_motion in shots:
    scene.camera = camera
    apply_exposure(exposure)
    for step in range(SHOT_FRAMES):
        output_index += 1
        scene.frame_set(scene_frame)
        if camera_motion:
            # Kadr ichidagi 0..1 oralig'idagi joylashuv
            camera_motion(step / max(1, SHOT_FRAMES - 1))
        scene.render.filepath = os.path.join(OUT_DIR, f"frame_{output_index:04d}")
        frame_started = time.time()
        bpy.ops.render.render(write_still=True)
        elapsed = time.time() - run_started
        per_frame = elapsed / output_index
        remaining = (total_frames - output_index) * per_frame
        print(f"[{output_index:4d}/{total_frames}] {shot_name}  "
              f"{time.time() - frame_started:.1f}s  "
              f"(o'rtacha {per_frame:.1f}s, qolgan ~{remaining / 60:.1f} daq)",
              flush=True)
        scene_frame += FRAME_STEP

print(f"=== {total_frames} kadr tayyor, jami {(time.time() - run_started) / 60:.1f} daqiqa ===")
