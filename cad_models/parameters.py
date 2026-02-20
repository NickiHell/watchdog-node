"""Параметры рамы квадрокоптера Watchdog 13".

Все размеры в миллиметрах.
Конструкция: PETG-CF 3D-печать + карбоновые трубы (лучи ⌀16×14, ноги ⌀10×8).
Складывание: Mavic-style (2 луча вперёд, 2 назад + ноги складываются с лучами).
"""

import math

# ============================================================================
# ОСНОВНЫЕ РАЗМЕРЫ РАМЫ (True-X 13", 6S)
# ============================================================================

# Диагональ рамы (мм) — противоположные моторы
FRAME_DIAGONAL = 566.0  # sqrt(400^2 + 400^2) ≈ 566 мм

# Расстояние между соседними моторами (мм)
MOTOR_TO_MOTOR_DISTANCE = 400.0

# Расстояние центр → мотор (мм) = MOTOR_TO_MOTOR_DISTANCE / sqrt(2)
CENTER_TO_MOTOR = MOTOR_TO_MOTOR_DISTANCE / math.sqrt(2)  # ≈ 283 мм

# Длина луча от края центральной плиты до мотора (мм)
ARM_LENGTH = 200.0  # от торца центральной плиты

# Диаметр карбоновых трубок лучей
ARM_TUBE_OD = 16.0  # внешний ⌀ мм
ARM_TUBE_ID = 14.0  # внутренний ⌀ мм
ARM_TUBE_WALL = 1.0  # толщина стенки мм

# Конфигурация True-X
ARM_ANGLE = 45.0  # угол от продольной оси, градусы

# ============================================================================
# ЦЕНТРАЛЬНЫЙ КОРПУС (PETG-CF)
# ============================================================================

# Размер центральной плиты (квадратная)
PLATFORM_SIZE = 160.0  # мм (достаточно для RPI5 + Pixhawk4 бок о бок)

# Толщина плит (PETG-CF 3-мм стенки)
PLATFORM_THICKNESS = 3.0  # верхняя и нижняя плита
CENTER_PLATFORM_THICKNESS = 3.0

# Высота стоек между ярусами (алюминиевые M4)
STANDOFF_HEIGHT_BOTTOM = 45.0  # нижняя плита → средний ярус (батарея)
STANDOFF_HEIGHT_MIDDLE = 40.0  # средний → верхний (электроника)

# Диаметр стоек
STANDOFF_DIAMETER = 8.0  # M4 внешний
STANDOFF_HOLE_DIAMETER = 4.2  # M4 внутренний

# ============================================================================
# ШАРНИРНЫЙ БЛОК СКЛАДЫВАНИЯ ЛУЧЕЙ (Mavic-style, PETG-CF)
# ============================================================================

# Размер шарнирного блока
FOLD_HINGE_WIDTH = 30.0  # ширина PETG-CF зажима
FOLD_HINGE_LENGTH = 40.0  # длина блока (сторона центра)
FOLD_HINGE_THICKNESS = 14.0  # высота = OD трубы
FOLD_HINGE_BOLT_DIAMETER = 5.0  # ось поворота M5 (титановый болт)
# Угол сложения: 2 передних луча сворачиваются назад (180°), 2 задних — вперёд
FOLD_FORWARD_ANGLE = 0.0  # рабочее положение (от центральной оси)
FOLD_TRANSPORT_ANGLE = 180.0  # транспортное положение

# ============================================================================
# ПОСАДОЧНЫЕ НОГИ (карбон ⌀10×8мм, складываются с лучом)
# ============================================================================

LEG_TUBE_OD = 10.0  # мм
LEG_TUBE_ID = 8.0  # мм
LEG_HEIGHT = 190.0  # высота в рабочем положении (≥180 мм для SIYI A8 mini снизу)
LEG_SPREAD_ANGLE = 15.0  # угол наклона ног от вертикали (распор)
LEG_TIP_DIAMETER = 20.0  # резиновая лапка (виброгашение)
LEG_BRACKET_OD_CLAMP = ARM_TUBE_OD  # кронштейн крепится на луч

# ============================================================================
# КРЕПЛЕНИЕ МОТОРОВ (T-Motor MN4014 330KV)
# ============================================================================

# T-Motor MN4014: стандарт крепления 19×19 мм
MOTOR_MOUNT_HOLE_SPACING_X = 19.0  # мм
MOTOR_MOUNT_HOLE_SPACING_Y = 19.0  # мм
MOTOR_MOUNT_HOLE_DIAMETER = 3.2  # M3 (чуть больше для лёгкой установки)
MOTOR_SHAFT_HOLE_DIAMETER = 12.0  # мм (вал MN4014 = 8мм + люфт)
MOTOR_BELL_DIAMETER = 50.0  # диаметр колокола мотора (T-Motor MN4014)

# ============================================================================
# КОМПОНЕНТЫ НА ПЛАТФОРМЕ
# ============================================================================

# Raspberry Pi 5
RPI5_LENGTH = 85.0
RPI5_WIDTH = 56.0
RPI5_HOLE_DIAMETER = 2.7  # M2.5
RPI5_HOLE_OFFSET_X = 3.5
RPI5_HOLE_OFFSET_Y = 3.5

# Pixhawk 4
PIXHAWK_LENGTH = 68.0
PIXHAWK_WIDTH = 44.0
PIXHAWK_HOLE_SPACING = 63.0  # мм (стандарт Pixhawk 4)
PIXHAWK_HOLE_DIAMETER = 3.2  # M3

# ============================================================================
# RPLIDAR S2 — МАЧТА
# ============================================================================

# Корпус RPLidar S2 (аналогичен A2)
LIDAR_DIAMETER = 76.0
LIDAR_MOUNT_HOLE_SPACING = 64.0  # мм
LIDAR_MOUNT_HOLE_DIAMETER = 3.2  # M3

# Мачта для RPLidar S2: карбоновая труба ⌀10мм на PETG-CF кронштейне
# Высота: +120 мм над верхней платой (плоскость скана выше всех компонентов)
LIDAR_MAST_HEIGHT = 120.0  # мм над верхней платой
LIDAR_MAST_TUBE_OD = 10.0
LIDAR_MAST_TUBE_ID = 8.0

# ============================================================================
# GPS МАЧТА
# ============================================================================

# GPS антенна на карбоновой мачте ⌀10мм
# Высота +60 мм над верхней платой — НИЖЕ плоскости скана LiDAR
GPS_MAST_HEIGHT = 60.0  # мм над верхней платой
GPS_MAST_TUBE_OD = 10.0

# ============================================================================
# ПОДВЕС SIYI A8 MINI (снизу дрона)
# ============================================================================

GIMBAL_CLEARANCE = LEG_HEIGHT  # пространство между подвесом и землёй
SIYI_A8_WEIGHT = 56.0  # г
SIYI_A8_WIDTH = 45.0  # мм
SIYI_A8_LENGTH = 55.0
SIYI_A8_HEIGHT = 60.0  # высота с объективом
GIMBAL_MOUNT_HOLE_SPACING = 30.0  # мм (SIYI A8 mini стандарт крепления)

# ============================================================================
# БАТАРЕЯ (6S 30 000 мАч агро-серия LiPo, Tattu/Grepow)
# ============================================================================

# Примерные габариты 6S 30Ач (ориентир по аналогам, уточнить по выбранной батарее)
BATTERY_LENGTH = 280.0  # мм
BATTERY_WIDTH = 75.0  # мм
BATTERY_HEIGHT = 55.0  # мм

# ============================================================================
# КОЖУХ КОРПУСА (PETG-CF 3мм стенки, IPX4)
# ============================================================================

ENCLOSURE_WALL = 3.0  # мм
ENCLOSURE_VENT_HOLE_DIAMETER = 8.0  # мм (вентиляционные отверстия)
ENCLOSURE_FAN_DIAMETER = 40.0  # мм (IP67 вентилятор на выдув сзади)

# ============================================================================
# ДОП. ПАРАМЕТРЫ
# ============================================================================

FILLET_RADIUS = 3.0  # радиус скругления углов
WIRE_HOLE_DIAMETER = 10.0  # отверстия проводки
VENTILATION_HOLES = 8
VENTILATION_HOLE_DIAMETER = 6.0

EXPORT_DIR = "export"
ASSEMBLY_NAME = "watchdog_13in_assembly"
ARM_PREFIX = "arm"
PLATFORM_PREFIX = "platform"

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ВЫЧИСЛЕНИЯ
# ============================================================================


def get_arm_positions():
    """Возвращает позиции 4 лучей: [(x, y, angle_deg), ...].

    True-X: лучи под ±45° и ±135° от продольной оси.
    """
    positions = []
    for i in range(4):
        angle = i * 90 + ARM_ANGLE  # 45, 135, 225, 315
        angle_rad = math.radians(angle)
        x = CENTER_TO_MOTOR * math.cos(angle_rad)
        y = CENTER_TO_MOTOR * math.sin(angle_rad)
        positions.append((x, y, angle))
    return positions


def get_motor_positions():
    """Возвращает 3D позиции моторов [(x, y, z), ...]."""
    arm_pos = get_arm_positions()
    z = STANDOFF_HEIGHT_BOTTOM + STANDOFF_HEIGHT_MIDDLE + PLATFORM_THICKNESS
    return [(x, y, z) for x, y, _ in arm_pos]


def validate_parameters():
    """Проверяет корректность ключевых параметров."""
    errors = []

    if ARM_LENGTH < 150:
        errors.append(f'ARM_LENGTH={ARM_LENGTH}мм мала для 13" пропов (рекомендуется >180мм)')

    if LEG_HEIGHT < 180:
        errors.append(f"LEG_HEIGHT={LEG_HEIGHT}мм мала — подвес SIYI A8 mini требует >180мм")

    if MOTOR_TO_MOTOR_DISTANCE < 380:
        errors.append(f'MOTOR_TO_MOTOR_DISTANCE={MOTOR_TO_MOTOR_DISTANCE}мм мало для 13" пропов')

    if PLATFORM_SIZE > 200:
        errors.append(f"PLATFORM_SIZE={PLATFORM_SIZE}мм больше допустимого")

    if LIDAR_MAST_HEIGHT < 100:
        errors.append(f"LIDAR_MAST_HEIGHT={LIDAR_MAST_HEIGHT}мм мала — LiDAR может видеть компоненты дрона")

    if GPS_MAST_HEIGHT >= LIDAR_MAST_HEIGHT:
        errors.append("GPS_MAST_HEIGHT >= LIDAR_MAST_HEIGHT — GPS попадёт в плоскость скана LiDAR!")

    return errors


if __name__ == "__main__":
    print('=== Watchdog 13" | Параметры рамы ===\n')
    print(f"Диагональ рамы:          {FRAME_DIAGONAL:.0f} мм")
    print(f"Мотор-мотор (соседние):  {MOTOR_TO_MOTOR_DISTANCE:.0f} мм")
    print(f"Центр → мотор:           {CENTER_TO_MOTOR:.1f} мм")
    print(f"Длина луча:              {ARM_LENGTH:.0f} мм (⌀{ARM_TUBE_OD:.0f}/{ARM_TUBE_ID:.0f}мм)")
    print(f"Ноги:                    {LEG_HEIGHT:.0f} мм высота (⌀{LEG_TUBE_OD:.0f}/{LEG_TUBE_ID:.0f}мм)")
    print(f"Платформа:               {PLATFORM_SIZE:.0f}×{PLATFORM_SIZE:.0f} мм")
    print(f"LiDAR мачта:             +{LIDAR_MAST_HEIGHT:.0f} мм над верхней платой")
    print(f"GPS мачта:               +{GPS_MAST_HEIGHT:.0f} мм над верхней платой")
    print(f"\nКрепление мотора T-Motor MN4014: {MOTOR_MOUNT_HOLE_SPACING_X}×{MOTOR_MOUNT_HOLE_SPACING_Y} мм")

    errors = validate_parameters()
    if errors:
        print("\n[!] ПРЕДУПРЕЖДЕНИЯ:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("\n[OK] Все параметры корректны.")

    print("\nПозиции моторов (True-X):")
    for i, (x, y, angle) in enumerate(get_arm_positions(), 1):
        print(f"  Мотор {i}: угол {angle:.0f}°, ({x:.1f}, {y:.1f}) мм от центра")
