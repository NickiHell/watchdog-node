# Watchdog — Дрон-разведчик 13"
[![CI](https://github.com/nickihell/watchdog-node/actions/workflows/ci.yml/badge.svg)](https://github.com/nickihell/watchdog-node/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/nickihell/watchdog-node/branch/main/graph/badge.svg)](https://codecov.io/gh/nickihell/watchdog-node)
[![Docker](https://github.com/nickihell/watchdog-node/actions/workflows/docker.yml/badge.svg)](https://github.com/nickihell/watchdog-node/actions/workflows/docker.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Ruff](https://img.shields.io/badge/ruff-checked-blue.svg)
![MyPy](https://img.shields.io/badge/mypy-checked-blue.svg)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen.svg)



Автономный квадрокоптер-разведчик/картограф. 13" True-X рама, Pixhawk 4, Raspberry Pi 5, ROS2 Humble.
Управление через Mission Planner (автономные миссии) и TX16 ELRS (ручное RC).
Объектная детекция YOLOv8n + ByteTrack, 3-осевой подвес SIYI A8 mini 4K.

---

## Характеристики

| Параметр | Значение |
|---|---|
| Класс | 13" True-X квадрокоптер |
| Диагональ рамы | ~570 мм (мотор-мотор соседние: 400 мм) |
| Рама | Коммерческая готовая 13" ≤1 кг + 3D-печать PETG-CF (кронштейны, мачты) |
| Моторы | T-Motor MN4014 330KV × 4 |
| Пропеллеры | T-Motor P13×4.4 Carbon (2 CW + 2 CCW) |
| ESC | Hobbywing XRotor 40A BLHeli32 × 4 |
| Полётный контроллер | Pixhawk 4 |
| Компьютер | Raspberry Pi 5, 8 ГБ |
| Подвес | SIYI A8 mini (3-ось, 4K, 4× zoom, MAVLink Gimbal v2, 56 г) |
| LiDAR | RPLidar S2 (30 м, 32 000 pts/sec, мачта +120 мм) |
| Батарея | 6S 22 000 мАч LiPo (Gens Ace Soaring / HRB), ~$110-150 |
| Сухой вес | ~2 300 г |
| MTOW | ~4 700 г |
| TWR | 2,38:1 |
| Время полёта | ~55 мин (DIY, 11 г/Вт КПД) |
| Потолок | 200 м (геозабор) |
| RC | RadioMaster TX16 + ELRS 900 МГц |
| Видеолинк | VTX 5.8 ГГц ← SIYI A8 mini HDMI |
| GCS | Mission Planner / QGroundControl (MAVProxy UDP) |
| Детекция | YOLOv8n + ByteTrack (~30 FPS треков) |
| Температурный диапазон | −5...+30°C |

---

## Архитектура рамы

```
Вид сверху (рабочее положение):
         [M1] ← луч ↗
          |
[M3] ← луч ← [ЦЕНТР] → луч → [M2]
                  |
                [M4] → луч ↘

True-X: все 4 мотора на одинаковом расстоянии от центра (283 мм).

Конструкция:
  Рама:  коммерческая готовая 13" складная (≤1 кг) с Mavic-style шарнирами
  Мачты: PETG-CF 3D-печать (LiDAR +120 мм, GPS +60 мм)
  Ноги:  карбон ⌀10×8 мм × 190 мм (если нет в комплекте рамы)
  Кожух: PETG-CF 3D-печать, IPX4, для электроники

Складывание (Mavic-style):
  2 передних луча → назад (поверх задних лучей)
  2 задних луча  → вперёд (под передними)
  Ноги складываются вместе с лучом
  Транспортный размер: ~300×200×120 мм
```

---

## Энергетика

```
Сухой вес (без батареи):
  Рама коммерческая 13":             ~900 г
  T-Motor MN4014 × 4:                460 г
  ESC 40A × 4:                       160 г
  Pixhawk 4 + GPS:                    95 г
  RPI 5 + кулер:                     120 г
  RPLidar S2 + мачта:                210 г
  SIYI A8 mini:                       56 г
  VTX + ELRS RX:                      50 г
  Проводка + PDB + разъёмы:          150 г
  Термосистема (−5..+30°C):           90 г
  ─────────────────────────────────────────
  ИТОГО сухой вес:                ~2 300 г

Батарея 6S 22 000 мАч LiPo:       2 400 г
MTOW:                             ~4 700 г

Тяга:
  T-Motor MN4014 330KV + P13×4.4 @ 6S: ~2,8 кг/мотор
  Суммарная тяга: 4 × 2,8 = ~11,2 кг
  TWR: 11,2 / 4,7 = 2,38:1 ✓

Полётное время:
  КПД DIY 13": ~11 г/Вт
  Потребляемая мощность (зависание): ~427 Вт
  Энергия батареи (80% разряд): 390 Вт·ч  (полная: 488 Вт·ч)
  Расчётное время: ~55 мин

  > Агро-серия (Tattu/Grepow 30Ач ~$250) не нужна — это сертификация
  > для опрыскивателей. Gens Ace Soaring / HRB 22Ач (~$130) компактнее
  > и даёт те же ~55 мин с лучшим TWR.

Пиковый ток (старт/маневр):
  ~65 А реальный (22Ач × 25C = 550А пик → запас огромный)
  Шина: 10 AWG, разъёмы XT90/AS150
```

---

## Компоненты системы

### Аппаратная часть

| Компонент | Модель | Стоимость |
|---|---|---|
| Моторы × 4 | T-Motor MN4014 330KV | ~$220 |
| Пропеллеры × 4 пары | T-Motor P13×4.4 Carbon | ~$60 |
| ESC × 4 | Hobbywing XRotor 40A | ~$80 |
| Полётный контроллер | Pixhawk 4 | ~$150 |
| Компьютер | Raspberry Pi 5, 8 ГБ | ~$80 |
| Подвес + камера | SIYI A8 mini | ~$230 |
| LiDAR | RPLidar S2 | ~$180 |
| Батарея | 6S 22Ач LiPo (Gens Ace Soaring / HRB) | ~$130 |
| RC пульт | RadioMaster TX16 + ELRS | ~$160 |
| RC приёмник | ELRS 900 МГц | ~$15 |
| VTX | 5.8 ГГц 600-1000 мВт | ~$40 |
| GPS | M9N + компас | ~$40 |
| Рама коммерческая 13" | Складная, Mavic-style | ~$80-120 |
| PDB, провода 10 AWG, разъёмы XT90 | — | ~$40 |
| Расходники 3D-печать PETG-CF (мачты, кожух) | ~300 г | ~$30 |
| **Итого** | | **~$1 335** |

---

## Программное обеспечение

### ROS2 пакеты

| Пакет | Назначение |
|---|---|
| `watchdog_controller` | Главный state machine |
| `watchdog_navigation` | Навигационный стек (max 200м, 5 м/с) |
| `watchdog_pixhawk_interface` | MAVLink ↔ ROS2 мост |
| `watchdog_camera` | Захват видео с SIYI A8 mini |
| `watchdog_detection` | YOLOv8n + ByteTrack (публикует `/detection/tracks`) |
| `watchdog_gimbal` | MAVLink Gimbal v2 + автослежение |
| `watchdog_lidar` | RPLidar S2 драйвер (1 000 000 бод, Express Scan) |
| `watchdog_thermal` | Термоуправление (DS18B20, вентилятор, нагреватель) |
| `watchdog_msgs` | Кастомные ROS2 сообщения (Detection, DetectionArray) |
| `watchdog_common` | Общие утилиты |

### Каналы RC (TX16 ELRS)

| Канал | Функция |
|---|---|
| 1 | Roll (крен) |
| 2 | Pitch (тангаж) |
| 3 | Throttle (газ) |
| 4 | Yaw (рыскание) |
| 5 | ARM (>1800 PWM = ARM) |
| 6 | Flight Mode (Stabilize/Loiter/Auto) |
| 7 | Gimbal Tilt (наклон подвеса) |
| 8 | Gimbal Pan (поворот подвеса) |

### Детекция и трекинг

```
Каждый кадр 30 FPS:
  N % 3 == 0:  YOLOv8n (~80 мс на RPI5 CPU) → ByteTrack.update()
  N % 3 != 0:  ByteTrack.predict() (~2 мс)
  Результат:   30 FPS треков при 10 FPS детекции

Дальность:  человек в 92×24 px @ 200м с 4× зумом SIYI A8 mini
Классы:     person, car, motorcycle, bus, truck
Публикация: /detection/tracks → watchdog_gimbal (автослежение)
```

### Термосистема

| Компонент | GPIO | Логика |
|---|---|---|
| DS18B20 (корпус) | GPIO4, 1-Wire | Датчик t°C корпуса |
| DS18B20 (мачта LiDAR) | GPIO4, 1-Wire | Датчик t°C мачты |
| Вентилятор 40 мм IP67 | GPIO18, Hardware PWM | ВКЛ > 35°C, ВЫКЛ < 28°C |
| Нагреватель мачты 3 Вт | GPIO17, MOSFET | ВКЛ < 0°C, ВЫКЛ > 5°C |

---

## Размещение компонентов

```
Вид сбоку:

┌────────────────────────────┐  ← RPLidar S2 мачта (+120 мм)
│                            │  ← GPS мачта (+60 мм)
├────────────────────────────┤  ← Верхняя плита рамы
│  PETG-CF кожух (IPX4)      │
│  ┌──────────┐ ┌──────────┐ │
│  │  RPI 5   │ │Pixhawk 4 │ │
│  └──────────┘ └──────────┘ │
│         Средний ярус        │
│     VTX   ELRS RX   PDB    │
├────────────────────────────┤  ← Нижняя плита рамы
│         Батарея 6S          │
│    6S 22 000 мАч LiPo       │
│   175×87×75 мм, ~2400 г     │
└────────────────────────────┘
           │
     [SIYI A8 mini]          ← подвес снизу центра
           │
    ════════════════         ← земля
     |    |    |    |
   Ноги (190 мм, карбон)
```

---

## Коммуникации

```
ELRS 900 МГц ── RC+телеметрия ──► TX16 пульт оператора
                                  (до 5-10 км)

VTX 5.8 ГГц ── FPV видео ──────► Монитор/очки оператора
                                  (до 1-3 км)

WiFi / 4G ───── MAVProxy UDP ───► Mission Planner на ноутбуке
  └─ порт 14550: широковещательный
  └─ порт 14551: QGroundControl

SIYI A8 mini ── HDMI ──────────► VTX (FPV)
              ─ USB ───────────► RPI 5 (OpenCV, запись)
              ─ MAVLink ────────► RPI 5 / Pixhawk (управление подвесом)
```

---

## Установка

### 1. ROS2 Humble (Raspberry Pi 5)

```bash
# Следовать официальной документации ROS2:
# https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html

sudo apt install ros-humble-mavros ros-humble-mavros-extras
sudo /opt/ros/humble/lib/mavros/install_geographiclib_datasets.sh
```

### 2. Python зависимости (через uv)

```bash
# Установить uv: https://docs.astral.sh/uv/
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установить все зависимости
uv sync --group ml --group hardware

# Только для разработки (без torch/ultralytics)
uv sync --group dev
```

### 3. Зависимости GPIO (только на Raspberry Pi 5)

```bash
sudo apt install python3-pigpio pigpiod python3-rpi.gpio
sudo systemctl enable pigpiod && sudo systemctl start pigpiod
```

### 4. Сборка ROS2 workspace

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### 5. MAVProxy (форвардинг на Mission Planner)

```bash
sudo ./scripts/setup_mavproxy.sh
# Статус: systemctl status mavproxy
```

### 6. Включить 1-Wire и Hardware PWM на RPI 5

Добавить в `/boot/firmware/config.txt`:

```
dtoverlay=w1-gpio          # DS18B20 (GPIO4)
dtoverlay=pwm,pin=18,func=2  # Hardware PWM (вентилятор)
```

### 7. Запуск системы

```bash
# Полный запуск:
ros2 launch config/launch/drone_full.launch.py

# Только навигация без детекции:
ros2 launch config/launch/drone_full.launch.py enable_detection:=false

# Без термосистемы (симуляция / стенд):
ros2 launch config/launch/drone_full.launch.py enable_thermal:=false
```

---

## Сборка

### Последовательность

1. **Рама**: собрать коммерческую 13" складную раму по инструкции производителя
2. **3D-печать PETG-CF**: мачта LiDAR (⌀10 × 120 мм), мачта GPS (⌀10 × 60 мм), PETG-кожух для электроники, крепление SIYI A8 mini
3. **Моторы + ESC**: T-Motor MN4014 на торцы лучей (19×19 мм, болты M3), ESC под лучом или на луче
4. **Электроника**: PDB → нижний ярус, батарея → снизу/на нижней плите (лента Velcro + ремни), RPI5 + Pixhawk → средний ярус
5. **Мачты**: LiDAR S2 (+120 мм), GPS (+60 мм) на PETG-CF кронштейнах верхней платы
6. **Подвес SIYI A8 mini**: снизу центральной плиты (PETG-CF крепление 30 мм)
7. **Кожух**: PETG-CF секции надеваются на корпус + вентилятор 40 мм + конформное покрытие PCB

---

## Разработка

```bash
# Линтинг и форматирование
uv run ruff check .
uv run ruff format .

# Типизация
uv run mypy ros2_ws/src --ignore-missing-imports

# Тесты (без железа и ROS2)
uv run pytest -m "not hardware and not ros"

# Установить pre-commit хуки
uv run pre-commit install

# Создать коммит (Conventional Commits)
uv run cz commit
```
