"""
Верхняя крышка для WatchDog Robot
Создаёт защитную крышку с отверстиями для кабелей и креплением башни лидара
"""

import FreeCAD as App
import Part
import math

# Импорт параметров
try:
    from parameters import *
except ImportError:
    CASE_LENGTH = 320
    CASE_WIDTH = 280
    WALL_THICKNESS = 3
    SCREW_HOLE_DIAMETER = 3.2
    SCREW_HEAD_DIAMETER = 6
    SCREW_HEAD_DEPTH = 2
    FILLET_RADIUS = 2

# Диаметр основания башни лидара
LIDAR_TOWER_BASE_DIAMETER = 120

# Создание нового документа
doc = App.newDocument("WatchDog_TopCover")

# Толщина крышки
cover_thickness = WALL_THICKNESS

# Создание основной крышки с закругленными углами
corner_radius = 12  # Радиус скругления углов

top_cover = Part.makeBox(
    CASE_LENGTH,
    CASE_WIDTH,
    cover_thickness
)

# Скругляем углы крышки
try:
    top_corner_edges = []
    for edge in top_cover.Edges:
        if len(edge.Vertexes) == 2:
            v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            if abs(v1.z - v2.z) > abs(v1.x - v2.x) and abs(v1.z - v2.z) > abs(v1.y - v2.y):
                if (v1.z == 0 or v2.z == 0) and (v1.z == cover_thickness or v2.z == cover_thickness):
                    if ((abs(v1.x) < 1 or abs(v1.x - CASE_LENGTH) < 1) or 
                        (abs(v2.x) < 1 or abs(v2.x - CASE_LENGTH) < 1)) and \
                       ((abs(v1.y) < 1 or abs(v1.y - CASE_WIDTH) < 1) or 
                        (abs(v2.y) < 1 or abs(v2.y - CASE_WIDTH) < 1)):
                        top_corner_edges.append(edge)
    
    if len(top_corner_edges) >= 4:
        top_cover = top_cover.makeFillet(corner_radius, top_corner_edges[:8])
except:
    pass

# Создание отверстия для башни лидара (в центре)
tower_hole = Part.makeCylinder(
    LIDAR_TOWER_BASE_DIAMETER / 2 + 2,  # Зазор 2мм
    cover_thickness + 1,
    App.Vector(CASE_LENGTH / 2, CASE_WIDTH / 2, -0.5)
)

top_cover = top_cover.cut(tower_hole)

# Отверстия для крепления крышки (по углам и по краям)
mount_holes = []
corner_offset = 15
edge_spacing = 40

# Угловые отверстия
for x in [corner_offset, CASE_LENGTH - corner_offset]:
    for y in [corner_offset, CASE_WIDTH - corner_offset]:
        hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER / 2,
            cover_thickness + 1,
            App.Vector(x, y, -0.5)
        )
        # Зенковка для головки винта
        counterbore = Part.makeCylinder(
            SCREW_HEAD_DIAMETER / 2,
            SCREW_HEAD_DEPTH,
            App.Vector(x, y, cover_thickness - SCREW_HEAD_DEPTH)
        )
        hole = hole.fuse(counterbore)
        mount_holes.append(hole)

# Отверстия по краям (для дополнительного крепления)
# Верхний и нижний края
for x in range(int(corner_offset + edge_spacing), 
               int(CASE_LENGTH - corner_offset), 
               int(edge_spacing)):
    for y in [corner_offset, CASE_WIDTH - corner_offset]:
        hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER / 2,
            cover_thickness + 1,
            App.Vector(x, y, -0.5)
        )
        counterbore = Part.makeCylinder(
            SCREW_HEAD_DIAMETER / 2,
            SCREW_HEAD_DEPTH,
            App.Vector(x, y, cover_thickness - SCREW_HEAD_DEPTH)
        )
        hole = hole.fuse(counterbore)
        mount_holes.append(hole)

# Левый и правый края
for y in range(int(corner_offset + edge_spacing),
               int(CASE_WIDTH - corner_offset),
               int(edge_spacing)):
    for x in [corner_offset, CASE_LENGTH - corner_offset]:
        hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER / 2,
            cover_thickness + 1,
            App.Vector(x, y, -0.5)
        )
        counterbore = Part.makeCylinder(
            SCREW_HEAD_DIAMETER / 2,
            SCREW_HEAD_DEPTH,
            App.Vector(x, y, cover_thickness - SCREW_HEAD_DEPTH)
        )
        hole = hole.fuse(counterbore)
        mount_holes.append(hole)

# Вырезаем все отверстия
for hole in mount_holes:
    top_cover = top_cover.cut(hole)

# Отверстие для кабелей (одно большое отверстие сзади, вместо множества маленьких)
cable_hole_width = 40
cable_hole_height = 15
tower_center_x = CASE_LENGTH / 2
tower_center_y = CASE_WIDTH / 2

# Одно большое отверстие для кабелей сзади корпуса
cable_hole = Part.makeBox(
    cable_hole_width,
    cover_thickness + 1,
    cable_hole_height,
    App.Vector(
        CASE_LENGTH / 2 - cable_hole_width / 2,
        CASE_WIDTH - 10,  # Отступ от заднего края
        (cover_thickness - cable_hole_height) / 2
    )
)

top_cover = top_cover.cut(cable_hole)

# Крепление для USB камеры в углу (справа спереди)
# Система координат: X малый = перед, X большой = зад, Y малый = слева, Y большой = справа
# Создаём платформу для крепления USB камеры
USB_CAMERA_SIZE = 40  # Типичный размер USB камеры (примерно)
USB_CAMERA_MOUNT_HEIGHT = 10  # Высота платформы для крепления
camera_mount_offset = 15  # Отступ от края

# Платформа для USB камеры (выступает вверх)
# Камера в переднем правом углу: X малый (перед), Y большой (справа)
camera_mount_platform = Part.makeBox(
    USB_CAMERA_SIZE,
    USB_CAMERA_SIZE,
    USB_CAMERA_MOUNT_HEIGHT,
    App.Vector(
        camera_mount_offset,  # ПЕРЕД (малый X)
        CASE_WIDTH - USB_CAMERA_SIZE - camera_mount_offset,  # СПРАВА (большой Y)
        cover_thickness  # На верхней поверхности крышки
    )
)

# Отверстия для крепления USB камеры (стандартные отверстия для большинства USB камер)
camera_mount_holes = []
hole_spacing = 25  # Расстояние между отверстиями
hole_diameter = 3.2  # M3 винт
for x_offset in [-hole_spacing/2, hole_spacing/2]:
    for y_offset in [-hole_spacing/2, hole_spacing/2]:
        hole = Part.makeCylinder(
            hole_diameter / 2,
            USB_CAMERA_MOUNT_HEIGHT + 1,
            App.Vector(
                camera_mount_offset + USB_CAMERA_SIZE/2 + x_offset,  # ПЕРЕД (малый X)
                CASE_WIDTH - USB_CAMERA_SIZE/2 - camera_mount_offset + y_offset,  # СПРАВА (большой Y)
                cover_thickness - 0.5
            )
        )
        camera_mount_holes.append(hole)

# Вырезаем отверстия
for hole in camera_mount_holes:
    camera_mount_platform = camera_mount_platform.cut(hole)

# Отверстие для USB кабеля (снизу платформы)
usb_cable_hole = Part.makeBox(
    12,  # Ширина отверстия для USB кабеля
    USB_CAMERA_SIZE + 2,
    5,
    App.Vector(
        camera_mount_offset + USB_CAMERA_SIZE/2 - 6,  # ПЕРЕД (малый X)
        CASE_WIDTH - USB_CAMERA_SIZE - camera_mount_offset - 1,  # СПРАВА (большой Y)
        cover_thickness - 5
    )
)
camera_mount_platform = camera_mount_platform.cut(usb_cable_hole)

# Объединяем платформу с крышкой
top_cover = top_cover.fuse(camera_mount_platform)

# Скругляем углы платформы
try:
    platform_top_edges = [e for e in camera_mount_platform.Edges 
                          if any(v.Z > cover_thickness + USB_CAMERA_MOUNT_HEIGHT - 1 for v in e.Vertexes)]
    if platform_top_edges:
        top_cover = top_cover.makeFillet(3, platform_top_edges[:4])
except:
    pass

# Скругление углов
try:
    import math
    top_edges = [e for e in top_cover.Edges 
                 if any(v.Z > cover_thickness - 0.5 for v in e.Vertexes)]
    if top_edges:
        top_cover = top_cover.makeFillet(FILLET_RADIUS, top_edges[:4])
except:
    pass

# Создание бортиков по краям (для лучшей посадки)
lip_height = 2
lip_thickness = 1

lip_inner = Part.makeBox(
    CASE_LENGTH - 2 * lip_thickness,
    CASE_WIDTH - 2 * lip_thickness,
    lip_height,
    App.Vector(lip_thickness, lip_thickness, -lip_height)
)

lip_outer = Part.makeBox(
    CASE_LENGTH,
    CASE_WIDTH,
    lip_height,
    App.Vector(0, 0, -lip_height)
)

lip = lip_outer.cut(lip_inner)
top_cover = top_cover.fuse(lip)

# Создание объекта
top_cover_obj = doc.addObject("Part::Feature", "TopCover")
top_cover_obj.Shape = top_cover

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Верхняя крышка создана успешно!")
print(f"Размеры: {CASE_LENGTH}×{CASE_WIDTH}×{cover_thickness} мм")
print(f"Отверстие для башни лидара: {LIDAR_TOWER_BASE_DIAMETER} мм")
print(f"Отверстие для кабелей: {cable_hole_width}×{cable_hole_height} мм (сзади корпуса)")
print(f"Платформа для USB камеры: {USB_CAMERA_SIZE}×{USB_CAMERA_SIZE}×{USB_CAMERA_MOUNT_HEIGHT} мм (в углу справа спереди)")
print(f"  • Отверстия для крепления: 4×M3")
print(f"  • Отверстие для USB кабеля: 12 мм")
print(f"Количество крепёжных отверстий: {len(mount_holes)}")
print(f"Закругленные углы: радиус {corner_radius} мм")

