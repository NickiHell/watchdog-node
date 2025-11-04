"""
Канал охлаждения для Beelink Mini S
Создаёт воздуховод для активного охлаждения Beelink Mini S
"""

import FreeCAD as App
import Part

# Импорт параметров
try:
    from parameters import *
except ImportError:
    MINIPC_LENGTH = 115
    MINIPC_WIDTH = 102
    MINIPC_HEIGHT = 41
    WALL_THICKNESS = 2
    FILLET_RADIUS = 2

# Размеры вентилятора 40×40 мм
FAN_SIZE = 40
FAN_THICKNESS = 10
FAN_MOUNT_HOLE_SPACING = 32  # Стандартное расстояние между отверстиями
FAN_MOUNT_HOLE_DIAMETER = 3.2

# Создание нового документа
doc = App.newDocument("WatchDog_CoolingDuct")

# Основной канал охлаждения
duct_height = FAN_THICKNESS + 10
duct_width = max(FAN_SIZE, MINIPC_WIDTH + 10)
duct_length = MINIPC_LENGTH + 20

# Внешний корпус
duct_outer = Part.makeBox(
    duct_length,
    duct_width,
    duct_height
)

# Внутренний канал
duct_inner = Part.makeBox(
    duct_length - 2 * WALL_THICKNESS,
    duct_width - 2 * WALL_THICKNESS,
    duct_height - WALL_THICKNESS,
    App.Vector(WALL_THICKNESS, WALL_THICKNESS, WALL_THICKNESS)
)

cooling_duct = duct_outer.cut(duct_inner)

# Отверстие для вентилятора (в передней части)
fan_mount = Part.makeBox(
    FAN_SIZE + 4,
    FAN_SIZE + 4,
    WALL_THICKNESS + 1,
    App.Vector(
        duct_length - FAN_SIZE - 4 - 5,
        (duct_width - FAN_SIZE - 4) / 2,
        -0.5
    )
)

fan_mount_inner = Part.makeBox(
    FAN_SIZE,
    FAN_SIZE,
    WALL_THICKNESS + 2,
    App.Vector(
        duct_length - FAN_SIZE - 5,
        (duct_width - FAN_SIZE) / 2,
        -1
    )
)

fan_mount = fan_mount.cut(fan_mount_inner)
cooling_duct = cooling_duct.cut(fan_mount)

# Отверстия для крепления вентилятора
fan_mount_holes = []
fan_center_x = duct_length - FAN_SIZE - 5 - FAN_SIZE / 2
fan_center_y = duct_width / 2

for dx in [-FAN_MOUNT_HOLE_SPACING/2, FAN_MOUNT_HOLE_SPACING/2]:
    for dy in [-FAN_MOUNT_HOLE_SPACING/2, FAN_MOUNT_HOLE_SPACING/2]:
        hole = Part.makeCylinder(
            FAN_MOUNT_HOLE_DIAMETER / 2,
            WALL_THICKNESS + 1,
            App.Vector(fan_center_x + dx, fan_center_y + dy, -0.5)
        )
        fan_mount_holes.append(hole)

for hole in fan_mount_holes:
    cooling_duct = cooling_duct.cut(hole)

# Выходное отверстие для воздуха (над Beelink Mini S)
air_outlet = Part.makeBox(
    MINIPC_LENGTH,
    MINIPC_WIDTH,
    WALL_THICKNESS + 1,
    App.Vector(5, (duct_width - MINIPC_WIDTH) / 2, duct_height - WALL_THICKNESS - 0.5)
)

cooling_duct = cooling_duct.cut(air_outlet)

# Направляющие лопатки для лучшего потока воздуха
def create_guide_vanes():
    """Создаёт направляющие лопатки внутри канала"""
    vanes = []
    num_vanes = 3
    vane_thickness = 1
    vane_height = duct_height - 2 * WALL_THICKNESS - 5
    
    for i in range(1, num_vanes + 1):
        x_pos = 10 + i * (duct_length - 20) / (num_vanes + 1)
        vane = Part.makeBox(
            vane_thickness,
            duct_width - 2 * WALL_THICKNESS - 5,
            vane_height,
            App.Vector(x_pos, WALL_THICKNESS + 2.5, WALL_THICKNESS + 2.5)
        )
        vanes.append(vane)
    
    return vanes

guide_vanes = create_guide_vanes()
for vane in guide_vanes:
    cooling_duct = cooling_duct.fuse(vane)

# Отверстия для крепления к отсеку электроники
mount_holes = []
mount_hole_spacing_x = duct_length - 20
mount_hole_spacing_y = duct_width - 20

for x in [10, duct_length - 10]:
    for y in [10, duct_width - 10]:
        hole = Part.makeCylinder(
            3.2 / 2,  # M3 винт
            duct_height + 1,
            App.Vector(x, y, -0.5)
        )
        mount_holes.append(hole)

for hole in mount_holes:
    cooling_duct = cooling_duct.cut(hole)

# Скругление углов
try:
    edges = [e for e in cooling_duct.Edges 
             if any(v.Z > duct_height - 1 for v in e.Vertexes)]
    if edges:
        cooling_duct = cooling_duct.makeFillet(FILLET_RADIUS, edges[:4])
except:
    pass

# Создание объекта
cooling_duct_obj = doc.addObject("Part::Feature", "CoolingDuct")
cooling_duct_obj.Shape = cooling_duct

# Визуализация вентилятора
fan_vis = doc.addObject("Part::Box", "Fan_Visualization")
fan_vis.Length = FAN_SIZE
fan_vis.Width = FAN_SIZE
fan_vis.Height = FAN_THICKNESS
fan_vis.Placement = App.Placement(
    App.Vector(
        duct_length - FAN_SIZE - 5,
        (duct_width - FAN_SIZE) / 2,
        -FAN_THICKNESS
    ),
    App.Rotation()
)
fan_vis.ViewObject.ShapeColor = (0.7, 0.7, 0.7)

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Канал охлаждения создан успешно!")
print(f"Размеры: {duct_length}×{duct_width}×{duct_height} мм")
print(f"Размер вентилятора: {FAN_SIZE}×{FAN_SIZE}×{FAN_THICKNESS} мм")
print(f"Для Beelink Mini S: {MINIPC_LENGTH}×{MINIPC_WIDTH}×{MINIPC_HEIGHT} мм")
print("Канал включает направляющие лопатки для оптимизации потока воздуха")

