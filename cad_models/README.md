# cad_models — 3D-модели Watchdog

Модели создаются вручную в Blender.
Физические параметры (размеры в мм) определены в `parameters.py`.

---

## Структура

```
cad_models/
├── parameters.py            ← все размеры дрона в мм (источник истины)
├── extract_model_data.py    ← Blender-скрипт: читает .blend → JSON + отчёт
├── watchdog.blend           ← Blender-модель (рядом со скриптами)
└── export/                  ← STL, OBJ, model_report.txt, model_data.json
```

---

## Рабочий процесс

### 1. Моделируешь в Blender

Сохраняй файл как `cad_models/watchdog.blend`.

### 2. Извлеки данные для AI-контекста

```bash
# Из командной строки:
cd watchdog-node
blender --background cad_models/watchdog.blend --python cad_models/extract_model_data.py

# Или прямо в Blender:
# Scripting → Open → extract_model_data.py → Run Script
```

Результат: `export/watchdog_data.json` + `export/watchdog_report.txt`

**Скопируй `watchdog_report.txt` в чат** — AI получит полный контекст
о всех объектах, их позициях, размерах и материалах.

---

## Ключевые размеры из parameters.py

```
CENTER_TO_MOTOR    282.8 мм   — центр дрона → мотор
ARM_LENGTH         200 мм     — длина луча (⌀16/14 мм карбон)
LEG_HEIGHT         190 мм     — высота посадочной ноги
PLATFORM_SIZE      160×160 мм — центральная плита
LIDAR_MAST_HEIGHT  120 мм     — мачта LiDAR над верхней платой
GPS_MAST_HEIGHT     60 мм     — мачта GPS (ниже LiDAR)
MOTOR_BELL_DIAMETER 50 мм    — колокол T-Motor MN4014
BATTERY (6S 30Ач)  ~280×75×55 мм
```

---

## Ось координат

```
  Z↑   Y (нос — перёд)
   │  ╱
   │ ╱
   └──────► X (правый борт)

  Z = 0: нижняя поверхность нижней плиты.
  Z > 0: вверх (моторы, плиты, мачты, батарея на крыше).
  Z < 0: вниз (подвес SIYI A8 mini).
```

---

## Шаблон именования объектов

Для корректной автогруппировки в отчёте:

| Компонент | Шаблон имени |
|---|---|
| Лучи | `Arm_FR`, `Arm_FL`, `Arm_BL`, `Arm_BR` |
| Шарниры | `Hinge_FR` … |
| Трубы лучей | `ArmTube_FR` … |
| Моторы | `Motor_FR_Bell`, `Motor_FR_Stator` … |
| Пропеллеры | `Prop_FR` … |
| Ноги | `Leg_FR`, `LegTip_FR` … |
| Корпус | `Plate_Bottom`, `Plate_Top`, `Standoff_*` |
| LiDAR | `LiDAR_*`, `RPLidar_*` |
| GPS | `GPS_*` |
| Подвес | `Gimbal_*`, `SIYI_*` |
| Батарея | `Battery_*` |
| Электроника | `RPI5`, `Pixhawk4`, `ELRS_*`, `VTX_*` |
