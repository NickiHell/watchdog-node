# Watchdog — План рефакторинга проекта

> Документ фиксирует все принятые решения по аппаратной части и программной архитектуре.
> Обновляется по мере реализации.

---

## Концепция

**Дрон-разведчик/картограф** на базе 13" квадрокоптера. Без внешней полезной нагрузки —
камера с 3-осевым подвесом является штатным компонентом системы. Управление через
Mission Planner (основное) и RC-пульт TX16 ELRS (резервное). Автономные миссии,
слежение за объектами через YOLOv8n + ByteTrack.

---

## Аппаратные спецификации

### Геометрия рамы

| Параметр | Значение |
|---|---|
| Пропеллеры | 13" (330 мм), True-X конфигурация |
| Мотор-мотор (соседние) | 400 мм |
| Диагональ рамы | ~570 мм |
| Длина луча (плита → мотор) | ~200 мм |
| Складывание | Mavic-style: 2 луча вперёд, 2 назад |
| Ноги | Складываются вместе с лучом (pivot кронштейн) |

> **Рама:** возможна коммерческая готовая рама 13" с последующей модификацией (≤1 кг).
> PETG-CF печать используется для кастомных кронштейнов, мачт и мест крепления.

### Компонентная база

| Компонент | Модель | Масса | Примечание |
|---|---|---|---|
| Моторы | T-Motor MN4014 330KV | 4× ~115 г | 6S, под 13" пропы |
| Пропеллеры | T-Motor P13×4.4 Carbon | 4 шт | 2 CW + 2 CCW |
| ESC | Hobbywing XRotor 40A BLHeli32 | 4× ~40 г | 6S |
| Полётный контроллер | Pixhawk 4 | ~65 г | MAVLink ↔ ROS2 |
| Компьютер | Raspberry Pi 5, 8 ГБ | ~85 г | ROS2 Humble |
| Подвес + камера | SIYI A8 mini | **56 г** | 4K, 3-ось, MAVLink Gimbal v2, $200-250 |
| LiDAR | RPLidar S2 | 190 г | UART 1 000 000 бод, 30 м |
| Батарея | 6S 22 000 мАч LiPo (Gens Ace Soaring / HRB) | ~2 400 г | Одна, ~$110-150 |
| RC приёмник | ELRS 900 МГц (SBUS → Pixhawk 4) | ~15 г | TX16 на земле |
| VTX | 5.8 ГГц видеопередатчик | ~30 г | HDMI ← SIYI A8 mini |
| GPS | M8N/M9N с компасом | ~30 г | На мачте +60 мм |

### Энергетика

| Параметр | Значение |
|---|---|
| Сухой вес (без батареи) | ~2 300 г |
| Батарея | ~2 400 г (6S 22Ач) |
| MTOW | ~4 700 г |
| Суммарная тяга | ~11 200 г (TWR 2,38:1) |
| Эффективность пропульсии | ~11 г/Вт (DIY реалистичная оценка) |
| Мощность зависания | ~427 Вт |
| Полезная энергия батареи | ~390 Вт·ч (80% разряд, 488 Вт·ч полная) |
| **Расчётное время полёта** | **~55 мин** |
| Пиковый ток | ~65 А (22Ач × 25C = 550А пик, реальный < 100А) |
| Основная шина | 10 AWG, разъёмы XT90/AS150 |

> ⚠️ Агро-серия (Tattu/Grepow 30Ач) не нужна — это сертификация для опрыскивателей.
> Gens Ace Soaring / HRB 22Ач — обычная UAV-серия, компактнее (~175×87×75 мм) и дешевле.
> Для DIY сборки реалистичный КПД 10–12 г/Вт → **~55 мин** на 22Ач.

### Размещение LiDAR

RPLidar S2 установлен на PETG-мачте **+120 мм над верхней платой**.
Плоскость скана выше всех компонентов (лучи, ноги, GPS, VTX — всё ниже).
Программная маска: 2–3 угловых сектора стоек мачты.

> Рабочий диапазон RPLidar S2: 0°C...+40°C.
> Нагреватель 3 Вт внутри кожуха мачты (термостат DS18B20) при < 0°C.

### Термосистема — диапазон −5...+30°C

| Компонент | Решение |
|---|---|
| LiPo при −5°C | Потеря ёмкости ~10%, допустимо без предогрева |
| RPI 5 | Конформное покрытие (Plastik 70) от конденсата |
| RPLidar S2 | Нагреватель 3 Вт на мачте, DS18B20, < 0°C |
| Корпус | PETG-кожух IPX4, 40 мм IP67 вентилятор (термостат 35°C) |
| **Масса термосистемы** | **~90 г** |

---

## Программная архитектура

### Архитектура системы

```
Наземная станция                        Дрон Watchdog
─────────────────                       ─────────────────────────────────────
Mission Planner ──WiFi/UDP──────────► MAVProxy (RPI 5)
                                              │
TX16 пульт ──ELRS 900МГц──► SBUS──► Pixhawk 4 ◄──UART MAVLink──► watchdog_pixhawk_interface
                                     │   │
                             ESC×4   │   └──► watchdog_gimbal ──MAVLink──► SIYI A8 mini
                             Моторы  │
                                     └──► watchdog_navigation
                                              │
RPLidar S2 ──UART──► watchdog_lidar ──────────┘

SIYI A8 mini ──HDMI──► VTX 5.8 ГГц ──► RC монитор оператора
             └──USB──► watchdog_camera ──► watchdog_detection (YOLOv8n + ByteTrack)
                                              │
                                         /detection/tracks
                                              │
                                     watchdog_gimbal (автослежение)

RPI 5 GPIO ──1-Wire──► DS18B20 (×2)
           ──PWM──────► вентилятор 40мм
           ──MOSFET───► нагреватель мачты LiDAR
                        watchdog_thermal
```

### Детекция + трекинг (RPI 5, YOLOv8n)

```
Каждый кадр 30 FPS:
  кадр % 3 == 0 → YOLOv8n (~80 мс) → ByteTrack.update() → публикация /detection/tracks
  кадр % 3 != 0 → ByteTrack.predict() (~2 мс)           → публикация /detection/tracks

watchdog_gimbal подписывается на /detection/tracks → плавное наведение 30 FPS
```

Опционально (если нужно больше FPS): Hailo-8L HAT для RPI 5 (~$70, 30–40 FPS без изменений в коде).

### ROS2 пакеты

| Пакет | Статус | Изменения |
|---|---|---|
| `watchdog_controller` | Существует | Обновить state machine (gimbal states) |
| `watchdog_navigation` | Существует | max_height 200м, max_velocity 5 м/с, use_slam: false |
| `watchdog_pixhawk_interface` | Существует | Pixhawk 4, TX16 ELRS 8 каналов |
| `watchdog_camera` | Существует | SIYI A8 mini HDMI/USB |
| `watchdog_detection` | Переименовать из `watchdog_face_detection` | YOLOv8n + ByteTrack (boxmot) |
| `watchdog_lidar` | Существует | RPLidar S2: baudrate 1 000 000, express scan |
| `watchdog_msgs` | Существует | Добавить GimbalCommand.msg, DetectionTrack.msg |
| `watchdog_common` | Существует | Без изменений |
| `watchdog_gimbal` | **Создать** | SIYI A8 mini MAVLink Gimbal v2 + автослежение |
| `watchdog_thermal` | **Создать** | DS18B20 + вентилятор + нагреватель мачты |

### Удаляется

- `web_interface/` — полностью (FastAPI + static). Заменяется MAVProxy → Mission Planner.

---

## Коммуникации

| Канал | Назначение | Дистанция |
|---|---|---|
| ELRS 900 МГц (TX16) | RC управление + телеметрия Pixhawk | ~5–10 км |
| VTX 5.8 ГГц | FPV видео с SIYI A8 mini | ~1–3 км |
| WiFi / 4G | MAVProxy → Mission Planner (планирование миссий) | Сеть |

---

## CAD параметры (cad_models/parameters.py)

| Параметр | Было | Стало |
|---|---|---|
| FRAME_DIAGONAL | 480 мм | **570 мм** |
| MOTOR_TO_MOTOR_DISTANCE | 440 мм | **400 мм** (соседние) |
| ARM_LENGTH | 120 мм | **200 мм** |
| ARM_TYPE | пластина | **труба ⌀16×14** |
| Крепление мотора | 16×19 мм (MN2216) | **19×19 мм (MN4014)** |
| Батарея | 155×50×40 мм | **обновить под 30Ач агро** |
| LiDAR мачта | — | **+120 мм над верхней платой** |
| GPS мачта | — | **+60 мм над верхней платой** |

---

## Задачи реализации

- [ ] `delete-web-interface` — Удалить web_interface/ полностью
- [ ] `update-drone-config` — config/drone_config.yaml: LiDAR S2, высота 200м, ELRS TX16, gimbal SIYI A8 mini, mavproxy, термосистема
- [ ] `update-pixhawk-config` — config/pixhawk_config.yaml: Pixhawk 4, геозабор 200м, MAVProxy GCS URL
- [ ] `update-launch` — drone_full.launch.py: убрать web_interface, добавить gimbal_node + thermal_node
- [ ] `update-lidar-driver` — rplidar_driver.py: baudrate 1 000 000, express scan, маска мачты
- [ ] `update-rc-interface` — rc_interface.py: TX16 ELRS 8 каналов, ARM/FlightMode/GimbalTilt/GimbalPan
- [ ] `update-navigation` — navigation_node.py: max_height 200м, max_velocity 5 м/с, use_slam: false
- [ ] `update-detection` — watchdog_face_detection → watchdog_detection: YOLOv8n + ByteTrack (boxmot), /detection/tracks
- [ ] `create-gimbal-package` — watchdog_gimbal: MAVLink Gimbal v2 + автослежение по /detection/tracks
- [ ] `create-thermal-package` — watchdog_thermal: DS18B20 GPIO, вентилятор PWM, нагреватель мачты MOSFET
- [ ] `create-mavproxy-setup` — scripts/setup_mavproxy.sh + config/mavproxy_config.yaml
- [ ] `update-cad-params` — cad_models/parameters.py: 570мм рама 13", MN4014 mount, ноги с fold
- [ ] `update-readme` — README.md: полный рерайт

---

## История решений

| Дата | Решение | Обоснование |
|---|---|---|
| — | 15" → 13" рама | Проще для pet-project, +PETG-CF 3D печать, ~те же 60 мин |
| — | SIYI A8 mini (56г) vs ZR30 (478г) | Вес, цена; 4× цифровой зум достаточно с 200м |
| — | 1× 6S 30Ач LiPo агро vs 2× 16Ач | Одна батарея, проще логистика |
| — | web_interface удалён | Mission Planner через MAVProxy — профессиональнее |
| — | YOLOv8n + ByteTrack vs апгрейд железа | 10 FPS детекция + 30 FPS трекер — достаточно для 200м |
| — | RPI 5 без MCU | DS18B20 через GPIO 1-Wire, вентилятор hardware PWM |
| — | Потолок снижен 300м → 200м | Надёжная YOLO детекция с 4× зумом |
| — | ~60 мин (не 89 мин) | Корректировка: DIY КПД 11 г/Вт, не 14–16 г/Вт DJI-уровня |
