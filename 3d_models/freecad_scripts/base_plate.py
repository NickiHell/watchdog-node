"""
Нижняя платформа для WatchDog Robot
Создаёт базовую платформу с отверстиями для крепления моторов и шасси
"""

import FreeCAD as App
import Part
import Draft

# Импорт параметров
try:
    from parameters import *
except ImportError:
    # Значения по умолчанию если параметры не найдены (обновлены для Beelink Mini S)
    CASE_LENGTH = 320
    CASE_WIDTH = 280
    FLOOR_THICKNESS = 8
    SCREW_HOLE_DIAMETER = 3.2
    SCREW_HEAD_DIAMETER = 6
    SCREW_HEAD_DEPTH = 2
    GRID_SPACING = 20
    FILLET_RADIUS = 2

# Создание нового документа
doc = App.newDocument("WatchDog_BasePlate")

# Создание основной платформы с закругленными углами (более стильная форма)
corner_radius = 15  # Радиус скругления углов

# Создаём платформу через скругленный прямоугольник
base_box = Part.makeBox(CASE_LENGTH, CASE_WIDTH, FLOOR_THICKNESS)
base_box.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Скругляем все углы
try:
    # Находим вертикальные рёбра в углах
    corner_edges = []
    for edge in base_box.Edges:
        if len(edge.Vertexes) == 2:
            v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            # Вертикальные рёбра в углах
            if abs(v1.z - v2.z) > abs(v1.x - v2.x) and abs(v1.z - v2.z) > abs(v1.y - v2.y):
                if (v1.z == 0 or v2.z == 0) and (v1.z == FLOOR_THICKNESS or v2.z == FLOOR_THICKNESS):
                    if ((abs(v1.x) < 1 or abs(v1.x - CASE_LENGTH) < 1) or 
                        (abs(v2.x) < 1 or abs(v2.x - CASE_LENGTH) < 1)) and \
                       ((abs(v1.y) < 1 or abs(v1.y - CASE_WIDTH) < 1) or 
                        (abs(v2.y) < 1 or abs(v2.y - CASE_WIDTH) < 1)):
                        corner_edges.append(edge)
    
    if len(corner_edges) >= 4:
        base_box = base_box.makeFillet(corner_radius, corner_edges[:8])  # Все угловые рёбра
except Exception as e:
    pass  # Если не удалось скруглить, продолжаем

# Создание отверстий для крепления (сетка)
def create_screw_hole(x, y, counterbore=False):
    """Создаёт отверстие для винта с возможностью зенковки"""
    hole = Part.makeCylinder(SCREW_HOLE_DIAMETER/2, FLOOR_THICKNESS + 1)
    hole.Placement = App.Placement(
        App.Vector(x, y, -0.5),
        App.Rotation()
    )
    if counterbore:
        counterbore_hole = Part.makeCylinder(SCREW_HEAD_DIAMETER/2, SCREW_HEAD_DEPTH)
        counterbore_hole.Placement = App.Placement(
            App.Vector(x, y, FLOOR_THICKNESS - SCREW_HEAD_DEPTH),
            App.Rotation()
        )
        hole = hole.fuse(counterbore_hole)
    return hole

# Отверстия по углам (для крепления к шасси)
corner_holes = []
corner_offset = 15  # Отступ от края
corner_holes.append(create_screw_hole(corner_offset, corner_offset))
corner_holes.append(create_screw_hole(CASE_LENGTH - corner_offset, corner_offset))
corner_holes.append(create_screw_hole(corner_offset, CASE_WIDTH - corner_offset))
corner_holes.append(create_screw_hole(CASE_LENGTH - corner_offset, CASE_WIDTH - corner_offset))

# Параметры моторов
try:
    MOTOR_PLATFORM_SIZE
    MOTOR_PLATFORM_HEIGHT
    MOTOR_HOLE_SPACING
    MOTOR_DISTANCE_FROM_CENTER
except NameError:
    MOTOR_PLATFORM_SIZE = 50
    MOTOR_PLATFORM_HEIGHT = 5
    MOTOR_HOLE_SPACING = 30
    MOTOR_DISTANCE_FROM_CENTER = 60

motor_center_offset_x = CASE_LENGTH / 2
motor_center_offset_y = 40  # Отступ от края

# Создание стильных платформ для моторов (шестиугольные вместо квадратных)
import math

def create_hexagon_platform(size, height, center_x, center_y, z_pos):
    """Создаёт шестиугольную платформу для мотора"""
    # Создаём шестиугольник
    hex_points = []
    for i in range(6):
        angle = math.pi / 3 * i  # 60 градусов
        x = center_x + size * math.cos(angle) / 2
        y = center_y + size * math.sin(angle) / 2
        hex_points.append(App.Vector(x, y, z_pos))
    
    # Создаём нижнее основание
    hex_base = Part.makePolygon(hex_points + [hex_points[0]])
    hex_base = Part.Face(Part.Wire(hex_base.Edges))
    hex_platform = hex_base.extrude(App.Vector(0, 0, height))
    
    return hex_platform

# Левый мотор (шестиугольная платформа)
left_motor_platform = create_hexagon_platform(
    MOTOR_PLATFORM_SIZE * 1.1,  # Немного больше для стиля
    MOTOR_PLATFORM_HEIGHT,
    motor_center_offset_x - MOTOR_DISTANCE_FROM_CENTER,
    motor_center_offset_y,
    FLOOR_THICKNESS
)

# Правый мотор (шестиугольная платформа)
right_motor_platform = create_hexagon_platform(
    MOTOR_PLATFORM_SIZE * 1.1,
    MOTOR_PLATFORM_HEIGHT,
    motor_center_offset_x + MOTOR_DISTANCE_FROM_CENTER,
    motor_center_offset_y,
    FLOOR_THICKNESS
)

# Скругление верхних рёбер платформ
try:
    top_edges_left = [e for e in left_motor_platform.Edges 
                     if any(v.Z > FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT - 0.5 for v in e.Vertexes)]
    top_edges_right = [e for e in right_motor_platform.Edges 
                      if any(v.Z > FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT - 0.5 for v in e.Vertexes)]
    if top_edges_left:
        left_motor_platform = left_motor_platform.makeFillet(2, top_edges_left[:6])
    if top_edges_right:
        right_motor_platform = right_motor_platform.makeFillet(2, top_edges_right[:6])
except:
    pass

# Объединяем платформы с основной платформой
base_box = base_box.fuse(left_motor_platform)
base_box = base_box.fuse(right_motor_platform)

# Отверстия для крепления моторов на платформах
left_motor_holes = []
left_motor_center_x = motor_center_offset_x - MOTOR_DISTANCE_FROM_CENTER
left_motor_center_y = motor_center_offset_y

for dx in [-MOTOR_HOLE_SPACING/2, MOTOR_HOLE_SPACING/2]:
    for dy in [-MOTOR_HOLE_SPACING/2, MOTOR_HOLE_SPACING/2]:
        hole = create_screw_hole(
            left_motor_center_x + dx,
            left_motor_center_y + dy
        )
        # Увеличиваем глубину отверстия для платформы
        extended_hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER/2,
            FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 1,
            App.Vector(left_motor_center_x + dx, left_motor_center_y + dy, -0.5)
        )
        left_motor_holes.append(extended_hole)

# Правый мотор
right_motor_holes = []
right_motor_center_x = motor_center_offset_x + MOTOR_DISTANCE_FROM_CENTER
right_motor_center_y = motor_center_offset_y

for dx in [-MOTOR_HOLE_SPACING/2, MOTOR_HOLE_SPACING/2]:
    for dy in [-MOTOR_HOLE_SPACING/2, MOTOR_HOLE_SPACING/2]:
        hole = create_screw_hole(
            right_motor_center_x + dx,
            right_motor_center_y + dy
        )
        # Увеличиваем глубину отверстия для платформы
        extended_hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER/2,
            FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 1,
            App.Vector(right_motor_center_x + dx, right_motor_center_y + dy, -0.5)
        )
        right_motor_holes.append(extended_hole)

# Объединение всех отверстий
all_holes = corner_holes + left_motor_holes + right_motor_holes
for hole in all_holes:
    base_box = base_box.cut(hole)

# Добавляем декоративные канавки по краям (для стиля)
try:
    # Декоративные канавки на верхней поверхности
    groove_depth = 1
    groove_width = 3
    groove_offset = 20  # Отступ от края
    
    # Канавка спереди
    front_groove = Part.makeBox(
        CASE_LENGTH - 2 * groove_offset,
        groove_width,
        groove_depth,
        App.Vector(groove_offset, groove_offset, FLOOR_THICKNESS - groove_depth)
    )
    
    # Канавка сзади
    back_groove = Part.makeBox(
        CASE_LENGTH - 2 * groove_offset,
        groove_width,
        groove_depth,
        App.Vector(groove_offset, CASE_WIDTH - groove_offset - groove_width, FLOOR_THICKNESS - groove_depth)
    )
    
    # Канавки по бокам
    left_groove = Part.makeBox(
        groove_width,
        CASE_WIDTH - 2 * groove_offset,
        groove_depth,
        App.Vector(groove_offset, groove_offset, FLOOR_THICKNESS - groove_depth)
    )
    
    right_groove = Part.makeBox(
        groove_width,
        CASE_WIDTH - 2 * groove_offset,
        groove_depth,
        App.Vector(CASE_LENGTH - groove_offset - groove_width, groove_offset, FLOOR_THICKNESS - groove_depth)
    )
    
    # Вырезаем канавки
    base_box = base_box.cut(front_groove)
    base_box = base_box.cut(back_groove)
    base_box = base_box.cut(left_groove)
    base_box = base_box.cut(right_groove)
except:
    pass  # Если не удалось добавить канавки, продолжаем

# Создание объекта в документе
base_plate_obj = doc.addObject("Part::Feature", "BasePlate")
base_plate_obj.Shape = base_box

# Визуализация мест для колес (для понимания размещения)
try:
    WHEEL_DIAMETER
    WHEEL_WIDTH
except NameError:
    WHEEL_DIAMETER = 60
    WHEEL_WIDTH = 20

# Левое колесо (визуализация) - сбоку слева, вертикально (перпендикулярно оси мотора)
left_wheel_vis = doc.addObject("Part::Cylinder", "LeftWheel_Visualization")
left_wheel_vis.Radius = WHEEL_DIAMETER / 2
left_wheel_vis.Height = WHEEL_WIDTH
left_wheel_vis.Placement = App.Placement(
    App.Vector(
        motor_center_offset_x - MOTOR_DISTANCE_FROM_CENTER,
        -WHEEL_DIAMETER/2,  # Слева от корпуса (Y < 0, снаружи слева)
        FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 15  # На оси мотора
    ),
    App.Rotation(App.Vector(0, 1, 0), 90)  # Колесо вертикально, перпендикулярно оси мотора (поворот вокруг Y)
)
left_wheel_vis.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # Тёмно-серый
left_wheel_vis.ViewObject.Transparency = 50  # Полупрозрачный

# Правое колесо (визуализация) - сбоку справа, вертикально
right_wheel_vis = doc.addObject("Part::Cylinder", "RightWheel_Visualization")
right_wheel_vis.Radius = WHEEL_DIAMETER / 2
right_wheel_vis.Height = WHEEL_WIDTH
right_wheel_vis.Placement = App.Placement(
    App.Vector(
        motor_center_offset_x + MOTOR_DISTANCE_FROM_CENTER,
        CASE_WIDTH + WHEEL_DIAMETER/2,  # Справа от корпуса (Y > CASE_WIDTH, снаружи справа)
        FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 15  # На оси мотора
    ),
    App.Rotation(App.Vector(0, 1, 0), 90)  # Колесо вертикально, перпендикулярно оси мотора (поворот вокруг Y)
)
right_wheel_vis.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # Тёмно-серый
right_wheel_vis.ViewObject.Transparency = 50  # Полупрозрачный

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Нижняя платформа создана успешно!")
print(f"Размеры: {CASE_LENGTH}×{CASE_WIDTH}×{FLOOR_THICKNESS} мм")
print(f"Стильный дизайн:")
print(f"  • Закругленные углы (радиус {corner_radius} мм)")
print(f"  • Шестиугольные платформы для моторов")
print(f"  • Декоративные канавки по краям")
print(f"Платформы для моторов: шестиугольные, высота {MOTOR_PLATFORM_HEIGHT} мм")

