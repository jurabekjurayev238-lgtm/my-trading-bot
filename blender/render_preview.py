"""Koinot sahnasini konsoldan (headless) render qilish.

Bu fayl `solar_system.py` dan KEYIN ishga tushiriladi va sahna dizayniga tegmaydi -
faqat render sozlamalarini va vaqtinchalik ko'rish kameralarini qo'shadi.

Ishga tushirish:

    SOLAR_TEXTURE_FOLDER=/path/to/textures \\
    blender --background --factory-startup \\
        --python blender/solar_system.py \\
        --python blender/render_preview.py -- --out ./renders

Sozlamalar muhit o'zgaruvchilari orqali beriladi:

    RENDER_SAMPLES   Cycles namunalari soni (standart 128)
    RENDER_RES_X     Eni (standart 1920)
    RENDER_RES_Y     Bo'yi (standart 1080)
    RENDER_FRAME     Qaysi kadr (standart 200)
"""

import os
import sys
import time

import bpy


def get_output_dir():
    """`-- --out <papka>` argumentini o'qiydi, berilmasa ./renders ishlatiladi."""
    if "--out" in sys.argv:
        index = sys.argv.index("--out")
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return os.path.abspath("renders")


OUT_DIR = get_output_dir()
SAMPLES = int(os.environ.get("RENDER_SAMPLES", "128"))
RES_X = int(os.environ.get("RENDER_RES_X", "1920"))
RES_Y = int(os.environ.get("RENDER_RES_Y", "1080"))
# 200-kadrda sayyoralar orbitalari bo'ylab tarqalgan.
# 1-kadrda ularning hammasi bir chiziqda turadi, chunki barcha orbitalar 0 dan boshlanadi
FRAME = int(os.environ.get("RENDER_FRAME", "200"))

os.makedirs(OUT_DIR, exist_ok=True)
scene = bpy.context.scene

# Cycles CPU. Konsol rejimida OpenGL konteksti bo'lmagani uchun EEVEE ishga tushmaydi
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.transparent_max_bounces = 16  # Shaffof halqa orqali to'g'ri ko'rinish uchun

scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

# Blender 4.x standarti AgX koinot sahnasida ranglarni haddan tashqari yuvib yuboradi
scene.view_settings.view_transform = 'Standard'

scene.frame_set(FRAME)

earth = bpy.data.objects["Earth"]
saturn = bpy.data.objects["Saturn"]
sun = bpy.data.objects["Sun"]
main_camera = bpy.data.objects["Main_Camera"]


def add_tracking_camera(name, target, offset, parent_to_target, lens=50.0):
    """Nishonga qarab turuvchi vaqtinchalik ko'rish kamerasi."""
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
    "Render_Overview", sun, (6.0, -64.0, 40.0), parent_to_target=False, lens=45.0)

# Sayyoraning lokal +X o'qi Quyoshdan tashqariga qaraydi, demak -X yoritilgan tomon.
# Kamerani o'sha tomonga qo'ysak, Saturn va halqa yoritilgan holda ko'rinadi
saturn_camera = add_tracking_camera(
    "Render_Saturn", saturn, (-7.0, -7.0, 4.5), parent_to_target=True, lens=60.0)

# Ekspozitsiyani ko'tarish koinot fonini ham ko'taradi va u binafsha tusga kiradi.
# Fonni teskari koeffitsientga qisqartirib, barcha kadrlarda bir xil qora qoldiramiz.
# Yulduzlar Emission obyektlari, shuning uchun ular bundan ta'sirlanmaydi
background_node = scene.world.node_tree.nodes.get("Background")
base_background = tuple(background_node.inputs[0].default_value) if background_node else None


def apply_exposure(stops):
    scene.view_settings.exposure = stops
    if background_node and base_background:
        factor = 2.0 ** -stops
        background_node.inputs[0].default_value = (
            base_background[0] * factor,
            base_background[1] * factor,
            base_background[2] * factor,
            base_background[3],
        )


# (fayl nomi, kamera, ekspozitsiya stoplarda).
# Ekspozitsiya har xil, chunki Quyosh nuri masofa kvadratiga teskari kamayadi:
# Saturn (34 birlik) Yerdan (12 birlik) ~8 baravar qorong'iroq yoritiladi
shots = (
    ("01_main_camera", main_camera, 1.5),
    ("02_overview", overview_camera, 1.0),
    ("03_saturn_ring", saturn_camera, 4.0),
)

print(f"\n=== Render: {RES_X}x{RES_Y}, {SAMPLES} samples, {FRAME}-kadr -> {OUT_DIR} ===")
for file_name, camera, exposure in shots:
    scene.camera = camera
    apply_exposure(exposure)
    scene.render.filepath = os.path.join(OUT_DIR, file_name)
    started = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[render] {file_name}.png  ekspozitsiya +{exposure}  {time.time() - started:.1f}s")

print("=== Render tugadi ===")
