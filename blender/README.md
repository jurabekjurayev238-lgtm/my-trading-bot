# Blender koinot tizimi

`solar_system.py` — Blender ichida ishga tushiriladigan bitta skript. U quyidagilarni yaratadi:

- **Quyosh** — Emission materiali + markazda haqiqiy Point Light (real soyalar uchun)
- **Sayyoralar** — Yer, Mars, Yupiter; Yer atrofida aylanuvchi **Oy**
- **Orbitalar** — Empty ierarxiyasi + driverlar (`frame * speed`), shuning uchun
  obyektlar hech qachon orbitadan chiqib ketmaydi
- **Yulduzli fon** — 3000 ta kichik Icosphere zarrachasi
- **Kuzatuv kamerasi** — Yerga ulangan, doim unga qarab turadi

## 1. Teksturalarni yuklab olish

Sayyoralarning yoyilgan (equirectangular) xaritalarini bepul yuklab olish mumkin:

- https://www.solarsystemscope.com/textures/
- NASA 3D Resources

2K yoki 4K `.jpg` yetarli. Fayllarni bitta papkaga saqlang va quyidagicha nomlang:

```
C:/textures/
├── earth.jpg
├── moon.jpg
├── mars.jpg
└── jupiter.jpg
```

## 2. Papka manzilini ko'rsatish

`solar_system.py` faylining boshidagi bitta qatorni o'zgartiring:

```python
TEXTURE_FOLDER = "C:/textures/"        # Windows
# TEXTURE_FOLDER = "/home/user/textures/"   # Linux / Mac
```

Boshqa fayl nomlaridan foydalanmoqchi bo'lsangiz, sayyora yaratilayotgan joyda
`texture("earth.jpg")` qismini o'zgartiring.

> **Eslatma:** rasm topilmasa skript **to'xtamaydi** — sayyora zaxira rangda chiziladi
> va konsolga `[Earth] Tekstura topilmadi: ...` xabari chiqadi. Ya'ni skriptni
> teksturalarsiz ham bemalol ishga tushirsa bo'ladi.

## 3. Ishga tushirish

1. Blender'ni oching → yuqoridagi **Scripting** yorlig'iga o'ting
2. **Open** → `solar_system.py` ni tanlang
3. **Run Script** (yoki `Alt + P`)

Skript birinchi navbatda sahnadagi hamma narsani o'chiradi, shuning uchun uni
istalgan vaqtda qayta ishga tushirish mumkin — keraksiz nusxalar to'planmaydi.

## 4. Tekshirish

| Qadam | Kutilayotgan natija |
|---|---|
| Konsol | `Koinot tizimi tayyor: Quyosh, Yer, Oy, Mars, Yupiter, 3000 yulduz...` |
| `Numpad 0` | Kamera Yerning orqasida, Yerga qaragan |
| `Spacebar` | Sayyoralar aylanadi, kamera Yer bilan birga uchadi |
| `Z` → `8` (Rendered) | Fonda yulduzlar, Quyoshdan tushayotgan real soyalar |

## Sozlamalar

Fayl boshidagi konstantalar:

| Konstanta | Vazifasi | Standart |
|---|---|---|
| `TEXTURE_FOLDER` | Tekstura rasmlari papkasi | `"C:/textures/"` |
| `STAR_COUNT` | Yulduzlar soni | `3000` |
| `STAR_INNER_RADIUS` / `STAR_OUTER_RADIUS` | Yulduz sferasi qalinligi | `120` / `200` |
| `STAR_BASE_SIZE` | Bitta yulduzning o'lchami | `0.12` |

Kompyuteringiz sekin bo'lsa `STAR_COUNT` ni 1000 ga tushiring.

## Yangi sayyora qo'shish

Barcha sayyoralar bitta `create_planet()` funksiyasi orqali yaratiladi:

```python
saturn, _ = create_planet(
    "Saturn", radius=1.1, distance=34, color=(0.9, 0.8, 0.6, 1), speed=0.003,
    texture_path=texture("saturn.jpg"))
```

Yo'ldosh (oy) qo'shish uchun `parent_obj` ni bering — orbitasi o'sha sayyoraga bog'lanadi:

```python
create_planet("Io", radius=0.2, distance=2.5, color=(0.9, 0.9, 0.5, 1),
              speed=0.05, parent_obj=jupiter, texture_path=texture("io.jpg"))
```

`speed` — kadr (frame) boshiga radian: qiymat qancha kichik bo'lsa, orbita shuncha sekin.
