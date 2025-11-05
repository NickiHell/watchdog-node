"""
Кронштейн для камеры WatchDog Robot
Создаёт регулируемый кронштейн для Raspberry Pi Camera v3
"""

import FreeCAD as App
import Part

# Импорт параметров
try:
    from parameters import *
except ImportError:
    CAMERA_BRACKET_WIDTH = 30
    CAMERA_BRACKET_HEIGHT = 25
    CAMERA_BRACKET_DEPTH = 15
    SCREW_HOLE_DIAMETER = 3.2
    WALL_THICKNESS = 3
    FILLET_RADIUS = 2

# Размеры Raspberry Pi Camera v3 (примерно 25×24×9 мм)
CAMERA_PCB_LENGTH = 25
CAMERA_PCB_WIDTH = 24
CAMERA_PCB_HEIGHT = 9
CAMERA_CABLE_WIDTH = 15

# Создание нового документа
doc = App.newDocument("WatchDog_CameraBracket")

# Основной кронштейн
bracket_base = Part.makeBox(
    CAMERA_BRACKET_WIDTH,
    CAMERA_BRACKET_DEPTH,
    CAMERA_BRACKET_HEIGHT
)

# Отсек для камеры
camera_compartment = Part.makeBox(
    CAMERA_PCB_LENGTH + 4,
    CAMERA_PCB_WIDTH + 4,
    CAMERA_PCB_HEIGHT + 2,
    App.Vector(
        (CAMERA_BRACKET_WIDTH - CAMERA_PCB_LENGTH - 4) / 2,
        CAMERA_BRACKET_DEPTH - CAMERA_PCB_WIDTH - 4,
        2
    )
)

bracket_base = bracket_base.fuse(camera_compartment)

# Вырез для кабеля камеры
cable_slot = Part.makeBox(
    CAMERA_CABLE_WIDTH,
    CAMERA_BRACKET_DEPTH + 1,
    5,
    App.Vector(
        (CAMERA_BRACKET_WIDTH - CAMERA_CABLE_WIDTH) / 2,
        -0.5,
        CAMERA_BRACKET_HEIGHT - 7
    )
)

bracket_base = bracket_base.cut(cable_slot)

# Отверстия для крепления камеры (M2 винты)
camera_screw_holes = []
camera_hole_spacing_x = CAMERA_PCB_LENGTH / 3
camera_hole_spacing_y = CAMERA_PCB_WIDTH / 3
camera_center_x = CAMERA_BRACKET_WIDTH / 2
camera_center_y = CAMERA_BRACKET_DEPTH - (CAMERA_PCB_WIDTH + 4) / 2

for dx in [-camera_hole_spacing_x, camera_hole_spacing_x]:
    for dy in [-camera_hole_spacing_y, camera_hole_spacing_y]:
        hole = Part.makeCylinder(
            2.2 / 2,  # M2 винт
            CAMERA_BRACKET_HEIGHT + 1,
            App.Vector(camera_center_x + dx, camera_center_y + dy, -0.5)
        )
        camera_screw_holes.append(hole)

for hole in camera_screw_holes:
    bracket_base = bracket_base.cut(hole)

# Отверстия для крепления кронштейна к корпусу (M3 винты)
mount_holes = []
mount_hole_spacing = CAMERA_BRACKET_WIDTH - 10
for x in [(CAMERA_BRACKET_WIDTH - mount_hole_spacing) / 2,
          (CAMERA_BRACKET_WIDTH + mount_hole_spacing) / 2]:
    hole = Part.makeCylinder(
        SCREW_HOLE_DIAMETER / 2,
        CAMERA_BRACKET_HEIGHT + 1,
        App.Vector(x, CAMERA_BRACKET_DEPTH / 2, -0.5)
    )
    mount_holes.append(hole)

for hole in mount_holes:
    bracket_base = bracket_base.cut(hole)

# Скругление углов
try:
    top_edges = [e for e in bracket_base.Edges 
                 if any(v.Z > CAMERA_BRACKET_HEIGHT - 1 for v in e.Vertexes)]
    if top_edges:
        bracket_base = bracket_base.makeFillet(FILLET_RADIUS, top_edges[:4])
except:
    pass

# Создание опорной стойки (для регулировки угла наклона)
support_post_height = 20
support_post_width = 10
support_post_depth = 5

support_post = Part.makeBox(
    support_post_width,
    support_post_depth,
    support_post_height,
    App.Vector(
        (CAMERA_BRACKET_WIDTH - support_post_width) / 2,
        CAMERA_BRACKET_DEPTH - support_post_depth,
        -support_post_height
    )
)

# Отверстие в опорной стойке для регулировки
adjustment_hole = Part.makeCylinder(
    4 / 2,  # M4 для регулировочного винта
    support_post_depth + 1,
    App.Vector(
        CAMERA_BRACKET_WIDTH / 2,
        CAMERA_BRACKET_DEPTH - support_post_depth / 2,
        -support_post_height / 2
    ),
    App.Vector(0, 1, 0)  # Направление перпендикулярно
)

support_post = support_post.cut(adjustment_hole)

# Объединение кронштейна и опорной стойки
camera_bracket = bracket_base.fuse(support_post)

# Создание объекта
camera_bracket_obj = doc.addObject("Part::Feature", "CameraBracket")
camera_bracket_obj.Shape = camera_bracket

# Визуализация камеры
camera_vis = doc.addObject("Part::Box", "Camera_Visualization")
camera_vis.Length = CAMERA_PCB_LENGTH
camera_vis.Width = CAMERA_PCB_WIDTH
camera_vis.Height = CAMERA_PCB_HEIGHT
camera_vis.Placement = App.Placement(
    App.Vector(
        (CAMERA_BRACKET_WIDTH - CAMERA_PCB_LENGTH) / 2,
        CAMERA_BRACKET_DEPTH - CAMERA_PCB_WIDTH - 2,
        2 + 1
    ),
    App.Rotation()
)
camera_vis.ViewObject.ShapeColor = (0.3, 0.3, 0.3)

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Кронштейн камеры создан успешно!")
print(f"Размеры: {CAMERA_BRACKET_WIDTH}×{CAMERA_BRACKET_DEPTH}×{CAMERA_BRACKET_HEIGHT} мм")
print("Кронштейн поддерживает регулировку угла наклона")

