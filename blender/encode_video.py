"""PNG kadrlar ketma-ketligini bitta mp4 video faylga yig'adi.

Tizimda ffmpeg bo'lmasa ham ishlaydi - Blender o'zining ichki ffmpeg'ini
va Video Sequence Editor'ini ishlatadi.

    blender --background --factory-startup --python encode_video.py \
        -- --frames ./anim --out ./koinot.mp4 --fps 24
"""
import glob
import os
import sys

import bpy


def get_arg(name, default=None):
    if name in sys.argv:
        index = sys.argv.index(name)
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return default


FRAMES_DIR = get_arg("--frames")
OUT_FILE = get_arg("--out")
FPS = int(get_arg("--fps", "24"))

frame_files = sorted(glob.glob(os.path.join(FRAMES_DIR, "frame_*.png")))
if not frame_files:
    raise SystemExit(f"Kadrlar topilmadi: {FRAMES_DIR}/frame_*.png")

print(f"[encode] {len(frame_files)} kadr topildi, {FPS} fps")

scene = bpy.context.scene

# Kadrlar allaqachon 'Standard' view transform bilan sRGB PNG sifatida saqlangan.
# Qayta kodlashda ikkinchi marta rang o'zgarishi bo'lmasligi uchun bu yerda ham
# 'Standard' qo'yamiz - sRGB -> linear -> sRGB aylanishi o'zgarishsiz qaytadi
scene.view_settings.view_transform = 'Standard'
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.sequencer_colorspace_settings.name = 'sRGB'

scene.frame_start = 1
scene.frame_end = len(frame_files)
scene.render.fps = FPS
scene.render.fps_base = 1.0

# O'lchamni birinchi kadrdan olamiz
first_image = bpy.data.images.load(frame_files[0])
scene.render.resolution_x = first_image.size[0]
scene.render.resolution_y = first_image.size[1]
scene.render.resolution_percentage = 100
print(f"[encode] o'lcham: {first_image.size[0]}x{first_image.size[1]}")

scene.sequence_editor_create()
strip = scene.sequence_editor.sequences.new_image(
    name="koinot",
    filepath=frame_files[0],
    channel=1,
    frame_start=1,
)
for path in frame_files[1:]:
    strip.elements.append(os.path.basename(path))
strip.colorspace_settings.name = 'sRGB'

scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.ffmpeg.audio_codec = 'NONE'
scene.render.filepath = OUT_FILE

bpy.ops.render.render(animation=True)

# Blender kadr oralig'ini fayl nomiga qo'shib qo'yishi mumkin
if not os.path.isfile(OUT_FILE):
    base, ext = os.path.splitext(OUT_FILE)
    for candidate in glob.glob(f"{base}*{ext}"):
        os.replace(candidate, OUT_FILE)
        break

size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
print(f"[encode] tayyor: {OUT_FILE} ({size_mb:.1f} MB, "
      f"{len(frame_files) / FPS:.1f} soniya)")
