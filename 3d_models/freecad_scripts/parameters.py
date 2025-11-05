# Параметры корпуса WatchDog Robot
# Измените эти значения для настройки размеров под ваши компоненты

# Общие размеры корпуса (мм)
# Размеры для выбранных компонентов:
# - Beelink Mini PC: ~115×102×41мм
# - STM32 Nucleo F411RE: ~70×52×18мм
# - Моторы 25GA370 + энкодеры E6B2-CWZ6C
# - Аккумулятор LiPo 3S (2200-5000mAh)
CASE_LENGTH = 320      # Длина корпуса
CASE_WIDTH = 280       # Ширина корпуса
CASE_HEIGHT = 200      # Высота корпуса (без лидара)
WALL_THICKNESS = 3     # Толщина стенок
FLOOR_THICKNESS = 8    # Толщина нижней платформы

# Beelink Mini PC (размеры зависят от модели, обычно ~115×102×41 мм)
MINIPC_LENGTH = 115
MINIPC_WIDTH = 102
MINIPC_HEIGHT = 41
MINIPC_CLEARANCE = 10     # Зазор для вентиляции (увеличено)

# STM32 Nucleo F411RE (≈70×52×18 мм)
STM32_LENGTH = 70
STM32_WIDTH = 52
STM32_HEIGHT = 18
STM32_CLEARANCE = 5

# Аккумулятор LiPo 3S
# 2200mAh: ~90×45×25 мм
# 5000mAh: ~110×55×35 мм (рекомендуется)
BATTERY_LENGTH = 110      # Для 5000mAh (или 90 для 2200mAh)
BATTERY_WIDTH = 55        # Для 5000mAh (или 45 для 2200mAh)
BATTERY_HEIGHT = 35       # Для 5000mAh (или 25 для 2200mAh)
BATTERY_CLEARANCE = 5

# Драйверы DRV8833 (≈20×15×4 мм)
DRIVER_LENGTH = 25
DRIVER_WIDTH = 20
DRIVER_HEIGHT = 6
DRIVER_CLEARANCE = 3

# Лидар RPLiDAR ToF C1 (цилиндрический, размеры зависят от модели)
LIDAR_DIAMETER = 80    # Диаметр лидара (примерно, уточнить у модели)
LIDAR_HEIGHT = 50      # Высота лидара (примерно, уточнить у модели)
LIDAR_TOWER_HEIGHT = 70  # Высота башни для лидара от верха корпуса

# Камера Raspberry Pi Camera v3
CAMERA_BRACKET_WIDTH = 30
CAMERA_BRACKET_HEIGHT = 25
CAMERA_BRACKET_DEPTH = 15

# Крепежные отверстия
SCREW_HOLE_DIAMETER = 3.2  # M3 винт
SCREW_HEAD_DIAMETER = 6    # Головка M3 винта
SCREW_HEAD_DEPTH = 2

# Вентиляционные отверстия
VENT_HOLE_DIAMETER = 5
VENT_HOLE_SPACING = 15

# Зазоры и допуски
CLEARANCE = 1          # Общий зазор для посадки
FILLET_RADIUS = 2      # Радиус скругления углов

# Шаг сетки для отверстий
GRID_SPACING = 20      # Расстояние между отверстиями

# Параметры моторов (Pololu 37D или аналогичные)
MOTOR_PLATFORM_SIZE = 50    # Размер платформы для мотора (квадрат)
MOTOR_PLATFORM_HEIGHT = 5  # Высота платформы для мотора
MOTOR_HOLE_SPACING = 30    # Расстояние между отверстиями крепления мотора
MOTOR_DISTANCE_FROM_CENTER = 60  # Расстояние моторов от центра по X
WHEEL_DIAMETER = 60        # Диаметр колеса (для визуализации)
WHEEL_WIDTH = 20          # Ширина колеса

