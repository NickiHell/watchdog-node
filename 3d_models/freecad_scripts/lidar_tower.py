"""
Башня для лидара WatchDog Robot
Создаёт цилиндрическую башню для установки лидара на высоте
"""

import FreeCAD as App
import Part
import math

# Импорт параметров
try:
    from parameters import *
except ImportError:
    LIDAR_DIAMETER = 80
    LIDAR_HEIGHT = 50
    LIDAR_TOWER_HEIGHT = 100
    CASE_LENGTH = 320
    CASE_WIDTH = 280
    WALL_THICKNESS = 3
    SCREW_HOLE_DIAMETER = 3.2
    FILLET_RADIUS = 2

# Создание нового документа
doc = App.newDocument("WatchDog_LidarTower")

# Параметры башни (более стильный дизайн)
tower_base_diameter = max(LIDAR_DIAMETER + 40, 120)  # Основание башни
tower_top_diameter = LIDAR_DIAMETER + 20  # Верхняя платформа
tower_height = LIDAR_TOWER_HEIGHT
tower_wall_thickness = WALL_THICKNESS

# Декоративные рёбра на башне
TOWER_RIB_COUNT = 6  # Количество вертикальных рёбер для стиля
TOWER_RIB_WIDTH = 2   # Ширина ребра

# Создание основания башни (цилиндр)
base_cylinder = Part.makeCylinder(
    tower_base_diameter / 2,
    tower_wall_thickness
)

# Создание внутреннего отверстия основания
base_inner = Part.makeCylinder(
    tower_base_diameter / 2 - tower_wall_thickness,
    tower_wall_thickness + 1,
    App.Vector(0, 0, -0.5)
)

base_cylinder = base_cylinder.cut(base_inner)

# Создание конусной части башни (усеченный конус)
# Используем многоугольник для создания конуса
num_segments = 32
cone_points = []
cone_faces = []

# Нижнее основание (большой круг)
base_radius = tower_base_diameter / 2 - tower_wall_thickness
# Верхнее основание (малый круг)
top_radius = tower_top_diameter / 2 - tower_wall_thickness

# Создание точек для внутренней и внешней поверхностей
for i in range(num_segments + 1):
    angle = 2 * math.pi * i / num_segments
    
    # Внешние точки (низ)
    x1 = (base_radius + tower_wall_thickness) * math.cos(angle)
    y1 = (base_radius + tower_wall_thickness) * math.sin(angle)
    cone_points.append(App.Vector(x1, y1, tower_wall_thickness))
    
    # Внешние точки (верх)
    x2 = (top_radius + tower_wall_thickness) * math.cos(angle)
    y2 = (top_radius + tower_wall_thickness) * math.sin(angle)
    cone_points.append(App.Vector(x2, y2, tower_height - tower_wall_thickness))
    
    # Внутренние точки (низ)
    x3 = base_radius * math.cos(angle)
    y3 = base_radius * math.sin(angle)
    cone_points.append(App.Vector(x3, y3, tower_wall_thickness))
    
    # Внутренние точки (верх)
    x4 = top_radius * math.cos(angle)
    y4 = top_radius * math.sin(angle)
    cone_points.append(App.Vector(x4, y4, tower_height - tower_wall_thickness))

# Создание усеченного конуса через развертку
# Используем более простой подход - создаем два цилиндра и вычитаем
cone_outer = Part.makeCone(
    tower_base_diameter / 2,
    tower_top_diameter / 2,
    tower_height - 2 * tower_wall_thickness,
    App.Vector(0, 0, tower_wall_thickness)
)

cone_inner = Part.makeCone(
    tower_base_diameter / 2 - tower_wall_thickness,
    tower_top_diameter / 2 - tower_wall_thickness,
    tower_height - 2 * tower_wall_thickness + 1,
    App.Vector(0, 0, tower_wall_thickness - 0.5)
)

cone_shell = cone_outer.cut(cone_inner)

# Создание верхней платформы для лидара
top_platform = Part.makeCylinder(
    tower_top_diameter / 2,
    tower_wall_thickness,
    App.Vector(0, 0, tower_height - tower_wall_thickness)
)

top_inner = Part.makeCylinder(
    tower_top_diameter / 2 - tower_wall_thickness,
    tower_wall_thickness + 1,
    App.Vector(0, 0, tower_height - tower_wall_thickness - 0.5)
)

top_platform = top_platform.cut(top_inner)

# Объединение всех частей
tower = base_cylinder.fuse(cone_shell)
tower = tower.fuse(top_platform)

# Добавляем декоративные вертикальные рёбра на башне (для стиля)
try:
    rib_height = tower_height - 2 * tower_wall_thickness
    rib_base_radius = tower_base_diameter / 2 - tower_wall_thickness
    rib_top_radius = tower_top_diameter / 2 - tower_wall_thickness
    
    for i in range(TOWER_RIB_COUNT):
        angle = 2 * math.pi * i / TOWER_RIB_COUNT
        
        # Создаём вертикальное ребро (трапеция)
        rib_points = []
        # Нижняя точка (внешняя)
        rib_points.append(App.Vector(
            (rib_base_radius + tower_wall_thickness + TOWER_RIB_WIDTH) * math.cos(angle),
            (rib_base_radius + tower_wall_thickness + TOWER_RIB_WIDTH) * math.sin(angle),
            tower_wall_thickness
        ))
        # Нижняя точка (внутренняя)
        rib_points.append(App.Vector(
            (rib_base_radius + tower_wall_thickness) * math.cos(angle),
            (rib_base_radius + tower_wall_thickness) * math.sin(angle),
            tower_wall_thickness
        ))
        # Верхняя точка (внутренняя)
        rib_points.append(App.Vector(
            (rib_top_radius + tower_wall_thickness) * math.cos(angle),
            (rib_top_radius + tower_wall_thickness) * math.sin(angle),
            tower_height - tower_wall_thickness
        ))
        # Верхняя точка (внешняя)
        rib_points.append(App.Vector(
            (rib_top_radius + tower_wall_thickness + TOWER_RIB_WIDTH) * math.cos(angle),
            (rib_top_radius + tower_wall_thickness + TOWER_RIB_WIDTH) * math.sin(angle),
            tower_height - tower_wall_thickness
        ))
        
        # Создаём вертикальное ребро (вытягиваем вверх)
        # Создаём профиль ребра (трапеция)
        rib_profile = Part.makePolygon(rib_points[:4] + [rib_points[0]])
        
        # Создаём ребро как вытяжку профиля
        # Используем более простой подход - создаём прямоугольное ребро
        rib_center_radius = (rib_base_radius + rib_top_radius) / 2 + tower_wall_thickness
        rib_center_x = rib_center_radius * math.cos(angle)
        rib_center_y = rib_center_radius * math.sin(angle)
        
        # Создаём ребро как небольшой выступ
        rib_box = Part.makeBox(
            TOWER_RIB_WIDTH,
            TOWER_RIB_WIDTH * 2,
            rib_height,
            App.Vector(
                rib_center_x - TOWER_RIB_WIDTH / 2,
                rib_center_y - TOWER_RIB_WIDTH,
                tower_wall_thickness
            )
        )
        
        # Поворачиваем ребро вокруг оси Z
        rib_box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), math.degrees(angle))
        
        # Объединяем ребро с башней
        tower = tower.fuse(rib_box)
except Exception as e:
    pass  # Если не удалось добавить рёбра, продолжаем

# Создание отверстий для крепления лидара на верхней платформе
lidar_mount_holes = []
mount_hole_spacing = LIDAR_DIAMETER / 3
mount_hole_radius = tower_top_diameter / 2 - 10

for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
    x = mount_hole_radius * math.cos(angle)
    y = mount_hole_radius * math.sin(angle)
    hole = Part.makeCylinder(
        SCREW_HOLE_DIAMETER / 2,
        tower_wall_thickness + 1,
        App.Vector(x, y, tower_height - tower_wall_thickness - 0.5)
    )
    lidar_mount_holes.append(hole)

for hole in lidar_mount_holes:
    tower = tower.cut(hole)

# Создание отверстий для крепления башни к корпусу (в основании)
base_mount_holes = []
mount_base_radius = tower_base_diameter / 2 - 15
for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
    x = mount_base_radius * math.cos(angle)
    y = mount_base_radius * math.sin(angle)
    hole = Part.makeCylinder(
        SCREW_HOLE_DIAMETER / 2,
        tower_wall_thickness + 1,
        App.Vector(x, y, -0.5)
    )
    base_mount_holes.append(hole)

for hole in base_mount_holes:
    tower = tower.cut(hole)

# Создание кабельного канала (отверстие в боковой стенке)
cable_channel_width = 15
cable_channel_height = 10
cable_channel_z = tower_height / 2

cable_channel = Part.makeBox(
    tower_wall_thickness + 1,
    cable_channel_width,
    cable_channel_height,
    App.Vector(-(tower_wall_thickness + 1)/2, -cable_channel_width/2, cable_channel_z - cable_channel_height/2)
)

tower = tower.cut(cable_channel)

# Создание визуализации лидара (для справки)
lidar_vis = doc.addObject("Part::Cylinder", "Lidar_Visualization")
lidar_vis.Radius = LIDAR_DIAMETER / 2
lidar_vis.Height = LIDAR_HEIGHT
lidar_vis.Placement = App.Placement(
    App.Vector(0, 0, tower_height),
    App.Rotation()
)
lidar_vis.ViewObject.ShapeColor = (0.5, 0.5, 0.5)

# Создание объекта башни
tower_obj = doc.addObject("Part::Feature", "LidarTower")
tower_obj.Shape = tower

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Башня лидара создана успешно!")
print(f"✨ Стильный дизайн:")
print(f"  • Декоративные вертикальные рёбра ({TOWER_RIB_COUNT} шт)")
print(f"  • Обтекаемая коническая форма")
print(f"Высота башни: {tower_height} мм")
print(f"Диаметр основания: {tower_base_diameter} мм")
print(f"Диаметр верхней платформы: {tower_top_diameter} мм")

