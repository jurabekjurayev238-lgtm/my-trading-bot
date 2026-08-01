"""
Blender (bpy) koinot tizimi: Quyosh, sayyoralar, Oy, yulduzlar va kuzatuvchi kamera.

Ishga tushirish: Blender -> Scripting -> Open -> Run Script.

Teksturalar: TEXTURE_FOLDER manzilini o'zingizdagi papkaga o'zgartiring.
Rasm topilmasa, sayyora avtomatik ravishda oddiy rangda chiziladi (skript to'xtamaydi).
"""

import bpy
import math
import os
import random

# === SOZLAMALAR ===
# Teksturalar saqlangan papka. Windows: "C:/textures/", Mac/Linux: "/home/user/textures/"
TEXTURE_FOLDER = "C:/textures/"

STAR_COUNT = 3000        # Fondagi yulduzlar soni
STAR_INNER_RADIUS = 120  # Yulduzlar sferasining ichki chegarasi
STAR_OUTER_RADIUS = 200  # Yulduzlar sferasining tashqi chegarasi
STAR_BASE_SIZE = 0.12    # Bitta yulduzning asosiy o'lchami

random.seed(2024)  # Har safar bir xil yulduz manzarasi chiqishi uchun


def texture(file_name):
    """Papka manzili bilan fayl nomini birlashtiradi."""
    return os.path.join(TEXTURE_FOLDER, file_name)


# 1. SAHNANI TOZALASH (Eski obyektlarni o'chirish)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Skript qayta ishga tushirilganda "Material.001" kabi keraksiz nusxalar
# to'planib qolmasligi uchun egasiz ma'lumotlarni tozalaymiz
for data_block in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                   bpy.data.lights, bpy.data.cameras):
    for item in list(data_block):
        # "Render Result" va "Viewer Node" - Blender'ning ichki rasmlari, tegilmaydi
        if getattr(item, "type", None) in {'RENDER_RESULT', 'COMPOSITING'}:
            continue
        if item.users == 0:
            data_block.remove(item)

# 2. ORQA FONNI TO'Q KOINOT RANGIGA O'TKAZISH
world = bpy.context.scene.world
if world:
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.01, 0.01, 0.02, 1)  # To'q ko'k-qora bo'shliq


# === YORDAMCHI FUNKSIYA: SAYYORA VA ORBITA YARATISH ===
def create_planet(name, radius, distance, color, speed, parent_obj=None, texture_path=None):
    # a) Orbita markazi (Empty - ko'rinmas o'q)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    orbit = bpy.context.active_object
    orbit.name = f"{name}_Orbit"

    # Agar bu Oy bo'lsa, u markaziy sayyoraga (Yerga) bog'lanadi
    if parent_obj:
        orbit.parent = parent_obj
        orbit.location = (0, 0, 0)

    # b) Aylanish harakatini vaqtga bog'lash (Driver)
    driver = orbit.driver_add('rotation_euler', 2).driver  # Z o'qi bo'yicha
    driver.expression = f"frame * {speed}"

    # c) Sayyora modelini yaratish (Sfera)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(distance, 0, 0))
    planet = bpy.context.active_object
    planet.name = name
    bpy.ops.object.shade_smooth()  # Yuzasini silliqlash
    planet.parent = orbit

    # d) Material va rang berish
    mat = bpy.data.materials.new(name=f"{name}_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Roughness'].default_value = 0.8

        # Tekstura (rasm) berilgan bo'lsa - uni Base Color ga ulaymiz
        image = None
        if texture_path and os.path.isfile(bpy.path.abspath(texture_path)):
            try:
                image = bpy.data.images.load(texture_path, check_existing=True)
            except RuntimeError as error:
                print(f"[{name}] Rasmni yuklab bo'lmadi: {texture_path} -> {error}")

        if image:
            tex_node = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
            tex_node.image = image
            tex_node.location = (-400, 300)
            tex_node.label = f"{name} Texture"
            mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        else:
            # Rasm topilmadi yoki ko'rsatilmadi - zaxira variant sifatida oddiy rang
            bsdf.inputs['Base Color'].default_value = color
            if texture_path:
                print(f"[{name}] Tekstura topilmadi: {texture_path} (oddiy rang qo'llanildi)")

    planet.data.materials.append(mat)

    return planet, orbit


# 3. QUYOSH VA YORUG'LIK MANBAI
# Quyosh sferasi
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.5, location=(0, 0, 0))
sun = bpy.context.active_object
sun.name = "Sun"
bpy.ops.object.shade_smooth()

# Quyosh nuri materiali (Nur taratuvchi)
sun_mat = bpy.data.materials.new(name="Sun_Emission")
sun_mat.use_nodes = True
nodes = sun_mat.node_tree.nodes
nodes.clear()
emission = nodes.new(type='ShaderNodeEmission')
emission.inputs['Color'].default_value = (1.0, 0.8, 0.1, 1.0)
emission.inputs['Strength'].default_value = 15.0  # Yorqinlik
output = nodes.new(type='ShaderNodeOutputMaterial')
sun_mat.node_tree.links.new(emission.outputs[0], output.inputs[0])
sun.data.materials.append(sun_mat)

# Haqiqiy yorug'lik manbai (Point light) - sayyoralarga to'g'ri soya tushirish uchun
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
light = bpy.context.active_object
light.data.energy = 50000  # Yorug'lik quvvati
light.data.shadow_soft_size = 2.0  # Soyalarni reallikka yaqinlashtirish
light.name = "Sun_Light"

# 4. SAYYORALARNI YARATISH (Nom, radius, masofa, RGBA rang, tezlik, tekstura)
earth, _ = create_planet(
    "Earth", radius=0.6, distance=12, color=(0.1, 0.4, 0.8, 1), speed=0.015,
    texture_path=texture("earth.jpg"))

moon, _ = create_planet(
    "Moon", radius=0.15, distance=1.5, color=(0.7, 0.7, 0.7, 1), speed=0.08,
    parent_obj=earth, texture_path=texture("moon.jpg"))

mars, _ = create_planet(
    "Mars", radius=0.4, distance=18, color=(0.8, 0.3, 0.1, 1), speed=0.008,
    texture_path=texture("mars.jpg"))

# Yupiter - tizimning eng yirik sayyorasi, sekinroq aylanadi
jupiter, _ = create_planet(
    "Jupiter", radius=1.4, distance=26, color=(0.78, 0.65, 0.45, 1), speed=0.004,
    texture_path=texture("jupiter.jpg"))


# 5. YULDUZLI KOINOT FONI (minglab kichik Icosphere zarrachalari)
def create_starfield(count, inner_radius, outer_radius, base_size):
    """Sahnani o'rab turuvchi sferik qatlamda minglab kichik yulduz yaratadi.

    Tezlik uchun barcha yulduzlar bir nechta umumiy mesh ma'lumotini bo'lishadi
    (linked duplicates), shuning uchun 3000 ta obyekt ham xotirani band qilmaydi.
    """
    # Bitta past poligonli icosphere namunasini yaratamiz
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=base_size, location=(0, 0, 0))
    template = bpy.context.active_object
    base_mesh = template.data

    # Yulduz turlari: (nom, RGBA rang, yorqinlik)
    star_types = [
        ("White", (1.0, 1.0, 1.0, 1.0), 12.0),
        ("Blue", (0.65, 0.78, 1.0, 1.0), 9.0),
        ("Warm", (1.0, 0.85, 0.6, 1.0), 7.0),
    ]

    star_meshes = []
    for type_name, color, strength in star_types:
        star_mat = bpy.data.materials.new(name=f"Star_{type_name}_Emission")
        star_mat.use_nodes = True
        star_nodes = star_mat.node_tree.nodes
        star_nodes.clear()
        star_emission = star_nodes.new(type='ShaderNodeEmission')
        star_emission.inputs['Color'].default_value = color
        star_emission.inputs['Strength'].default_value = strength
        star_output = star_nodes.new(type='ShaderNodeOutputMaterial')
        star_mat.node_tree.links.new(star_emission.outputs[0], star_output.inputs[0])

        mesh_copy = base_mesh.copy()
        mesh_copy.name = f"Star_Mesh_{type_name}"
        mesh_copy.materials.append(star_mat)
        star_meshes.append(mesh_copy)

    # Namuna obyekt va uning asl meshi endi kerak emas
    bpy.data.objects.remove(template, do_unlink=True)
    bpy.data.meshes.remove(base_mesh)

    # Yulduzlarni alohida kolleksiyaga joylaymiz (Outliner toza qolishi uchun)
    star_collection = bpy.data.collections.new("Starfield")
    bpy.context.scene.collection.children.link(star_collection)

    for index in range(count):
        # Sfera yuzasi bo'ylab bir tekis taqsimlash
        z = random.uniform(-1.0, 1.0)
        theta = random.uniform(0.0, 2.0 * math.pi)
        ring_radius = math.sqrt(max(0.0, 1.0 - z * z))
        distance = random.uniform(inner_radius, outer_radius)

        star = bpy.data.objects.new(f"Star_{index:04d}", random.choice(star_meshes))
        star.location = (
            distance * ring_radius * math.cos(theta),
            distance * ring_radius * math.sin(theta),
            distance * z,
        )

        scale = random.uniform(0.4, 1.6)
        star.scale = (scale, scale, scale)

        # Yulduzlar soya tashlamasin - ular faqat fon vazifasini bajaradi
        if hasattr(star, "visible_shadow"):
            star.visible_shadow = False

        star_collection.objects.link(star)

    return star_collection


create_starfield(STAR_COUNT, STAR_INNER_RADIUS, STAR_OUTER_RADIUS, STAR_BASE_SIZE)


# 6. KAMERANI JOYLASHTIRISH (Yer orqasidan uchuvchi kuzatuv kamerasi)
bpy.ops.object.camera_add(location=(0, 0, 0))
camera = bpy.context.active_object
camera.name = "Main_Camera"
bpy.context.scene.camera = camera

# a) Kamerani Yerga ulaymiz (Parenting) - Yer qayerga uchsa, kamera ham u bilan
camera.parent = earth
camera.matrix_parent_inverse.identity()  # Joylashuv Yerning markaziga nisbatan hisoblansin

# b) Yerdan 4 birlik orqada va 1.5 birlik tepada suzib yuradi
camera.location = (0, -4, 1.5)

# c) Nigohni Yerga qadash (Track To) - kamera doim Yerga qarab turadi
track_constraint = camera.constraints.new(type='TRACK_TO')
track_constraint.target = earth
track_constraint.track_axis = 'TRACK_NEGATIVE_Z'  # Kamera oldinga qaraydi
track_constraint.up_axis = 'UP_Y'                 # Kameraning tepa qismi

# Animatsiya uzunligi (driverlar 'frame' ga bog'langani uchun)
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 2000

print("Koinot tizimi tayyor: Quyosh, Yer, Oy, Mars, Yupiter, "
      f"{STAR_COUNT} yulduz va Yerni kuzatuvchi kamera.")
