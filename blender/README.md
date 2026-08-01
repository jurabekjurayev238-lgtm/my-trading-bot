# Blender koinot tizimi

`solar_system.py` — Blender ichida ishga tushiriladigan bitta skript. U quyidagilarni yaratadi:

- **Quyosh** — Emission materiali + markazda haqiqiy Point Light (real soyalar uchun)
- **Sayyoralar** — Yer, Mars, Yupiter, halqali **Saturn**; Yer atrofida aylanuvchi **Oy**
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
├── jupiter.jpg
├── saturn.jpg
└── saturn_ring.png      <- alfa kanali bilan (halqadagi bo'shliqlar uchun)
```

Saturn halqasi teksturasi boshqacha: u sayyora xaritasi emas, balki **radial chiziq** —
rasmning chap chekkasi halqaning ichki qismi, o'ng chekkasi tashqi qismi.
solarsystemscope.com da bu `saturnringcolor` nomi bilan turadi. Halqadagi bo'shliqlar
(masalan Kassini bo'shlig'i) ko'rinishi uchun alfa kanalli `.png` afzal — `.jpg` da
alfa bo'lmagani uchun halqa yaxlit disk bo'lib chiqadi.

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
>
> Saturn halqasi uchun teksturasiz holatda zaxira variant oddiy rang emas —
> ColorRamp orqali protsedural qatlamlar chiziladi (bo'shliqlari bilan), shuning uchun
> halqa rasmsiz ham halqaga o'xshab ko'rinadi.

## 3. Ishga tushirish

1. Blender'ni oching → yuqoridagi **Scripting** yorlig'iga o'ting
2. **Open** → `solar_system.py` ni tanlang
3. **Run Script** (yoki `Alt + P`)

Skript birinchi navbatda sahnadagi hamma narsani o'chiradi, shuning uchun uni
istalgan vaqtda qayta ishga tushirish mumkin — keraksiz nusxalar to'planmaydi.

## 4. Tekshirish

| Qadam | Kutilayotgan natija |
|---|---|
| Konsol | `Koinot tizimi tayyor: ... halqali Saturn, 3000 yulduz...` |
| `Numpad 0` | Kamera Yerning orqasida, Yerga qaragan |
| `Spacebar` | Sayyoralar aylanadi, kamera Yer bilan birga uchadi |
| `Z` → `8` (Rendered) | Fonda yulduzlar, Quyoshdan tushayotgan real soyalar |
| Saturn'ga yaqinlashing | Halqa qiyshaygan (26.7°), bo'shliqlari orqali fon ko'rinadi |

Halqa shaffofligi faqat **Rendered** yoki **Material Preview** rejimida ko'rinadi —
Solid rejimda u yaxlit disk bo'lib turadi, bu normal holat.

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
neptune, _ = create_planet(
    "Neptune", radius=0.9, distance=42, color=(0.25, 0.4, 0.85, 1), speed=0.002,
    texture_path=texture("neptune.jpg"))
```

Yo'ldosh (oy) qo'shish uchun `parent_obj` ni bering — orbitasi o'sha sayyoraga bog'lanadi:

```python
create_planet("Io", radius=0.2, distance=2.5, color=(0.9, 0.9, 0.5, 1),
              speed=0.05, parent_obj=jupiter, texture_path=texture("io.jpg"))
```

`speed` — kadr (frame) boshiga radian: qiymat qancha kichik bo'lsa, orbita shuncha sekin.

## Halqa qo'shish

`create_ring()` istalgan sayyoraga halqa qo'shadi. Radiuslar **sayyora birligida**,
uning markazidan hisoblanadi — ichki radius sayyora radiusidan katta bo'lishi kerak:

```python
uranus, _ = create_planet("Uranus", radius=1.0, distance=48,
                          color=(0.6, 0.85, 0.88, 1), speed=0.0015)

# O'q og'ishi: halqa sayyoraga bog'langani uchun sayyorani qiyshaytirish kifoya
uranus.rotation_euler = (math.radians(97.8), 0.0, 0.0)

create_ring(uranus, inner_radius=1.4, outer_radius=2.0)
```

`texture_path` berilmasa protsedural halqa chiziladi. `segments` (standart `128`)
halqa aylanasining silliqligini belgilaydi.
