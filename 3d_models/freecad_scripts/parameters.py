# Параметры корпуса WatchDog Robot
# Измените эти значения для настройки размеров под ваши компоненты

# Общие размеры корпуса (мм)
# Увеличены для размещения Beelink Mini S (115×102×41 мм)
CASE_LENGTH = 320      # Длина корпуса (увеличено для Beelink Mini S)
CASE_WIDTH = 280       # Ширина корпуса (увеличено для Beelink Mini S)
CASE_HEIGHT = 220      # Высота корпуса (без лидара, увеличено для Beelink Mini S)
WALL_THICKNESS = 3     # Толщина стенок
FLOOR_THICKNESS = 8    # Толщина нижней платформы

# Beelink Mini S (115×102×41 мм)
MINIPC_LENGTH = 115
MINIPC_WIDTH = 102
MINIPC_HEIGHT = 41
MINIPC_CLEARANCE = 5      # Зазор вокруг устройства

# STM32F407 Nucleo (≈70×52×15 мм)
STM32_LENGTH = 70
STM32_WIDTH = 52
STM32_HEIGHT = 18
STM32_CLEARANCE = 5

# Аккумулятор Li-Po 12V 5000mAh (примерно 100×50×30 мм)
BATTERY_LENGTH = 110
BATTERY_WIDTH = 55
BATTERY_HEIGHT = 35
BATTERY_CLEARANCE = 5

# Драйверы DRV8833 (≈20×15×4 мм)
DRIVER_LENGTH = 25
DRIVER_WIDTH = 20
DRIVER_HEIGHT = 6
DRIVER_CLEARANCE = 3

# Лидар MOP3 (цилиндрический, диаметр зависит от модели)
LIDAR_DIAMETER = 80    # Диаметр лидара
LIDAR_HEIGHT = 50      # Высота лидара
LIDAR_TOWER_HEIGHT = 100  # Высота башни для лидара

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

