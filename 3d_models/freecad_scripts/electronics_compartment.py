"""
Отсек для электроники WatchDog Robot
Содержит отсеки для Beelink Mini S, STM32, батареи и драйверов моторов
"""

import FreeCAD as App
import Part

# Импорт параметров
try:
    from parameters import *
except ImportError:
    CASE_LENGTH = 320
    CASE_WIDTH = 280
    CASE_HEIGHT = 220
    WALL_THICKNESS = 3
    MINIPC_LENGTH = 115
    MINIPC_WIDTH = 102
    MINIPC_HEIGHT = 41
    MINIPC_CLEARANCE = 5
    STM32_LENGTH = 70
    STM32_WIDTH = 52
    STM32_HEIGHT = 18
    STM32_CLEARANCE = 5
    BATTERY_LENGTH = 110
    BATTERY_WIDTH = 55
    BATTERY_HEIGHT = 35
    BATTERY_CLEARANCE = 5
    DRIVER_LENGTH = 25
    DRIVER_WIDTH = 20
    DRIVER_HEIGHT = 6
    DRIVER_CLEARANCE = 3
    SCREW_HOLE_DIAMETER = 3.2
    VENT_HOLE_DIAMETER = 5
    VENT_HOLE_SPACING = 15
    FILLET_RADIUS = 2

# Создание нового документа
doc = App.newDocument("WatchDog_ElectronicsCompartment")

# Высота отсека электроники
electronics_height = max(
    MINIPC_HEIGHT + MINIPC_CLEARANCE,
    STM32_HEIGHT + STM32_CLEARANCE,
    BATTERY_HEIGHT + BATTERY_CLEARANCE
) + 10

# Создание внешних стенок с закругленными углами
corner_radius = 12  # Радиус скругления углов

# Внешний корпус
outer_box = Part.makeBox(
    CASE_LENGTH,
    CASE_WIDTH,
    electronics_height
)

# Внутренний корпус (с зазорами)
inner_box = Part.makeBox(
    CASE_LENGTH - 2 * WALL_THICKNESS,
    CASE_WIDTH - 2 * WALL_THICKNESS,
    electronics_height - WALL_THICKNESS,
    App.Vector(WALL_THICKNESS, WALL_THICKNESS, WALL_THICKNESS)
)

# Скругляем углы внешнего корпуса
try:
    # Находим вертикальные рёбра в углах
    outer_corner_edges = []
    for edge in outer_box.Edges:
        if len(edge.Vertexes) == 2:
            v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            if abs(v1.z - v2.z) > abs(v1.x - v2.x) and abs(v1.z - v2.z) > abs(v1.y - v2.y):
                if (v1.z == 0 or v2.z == 0) and (v1.z == electronics_height or v2.z == electronics_height):
                    if ((abs(v1.x) < 1 or abs(v1.x - CASE_LENGTH) < 1) or 
                        (abs(v2.x) < 1 or abs(v2.x - CASE_LENGTH) < 1)) and \
                       ((abs(v1.y) < 1 or abs(v1.y - CASE_WIDTH) < 1) or 
                        (abs(v2.y) < 1 or abs(v2.y - CASE_WIDTH) < 1)):
                        outer_corner_edges.append(edge)
    
    if len(outer_corner_edges) >= 4:
        outer_box = outer_box.makeFillet(corner_radius, outer_corner_edges[:8])
except:
    pass

electronics_box = outer_box.cut(inner_box)

# Позиции отсеков обновлены: электроника размещена без пересечений
# При виде СВЕРХУ: X - длина (малый X = перед, большой X = зад), Y - ширина (малый Y = слева, большой Y = справа)
# MiniPC и STM32 в передней части (малый X = 8-123)
# Battery и Drivers в передней части справа (малый X = 8-138, большой Y = 217-242)
# Моторы СЗАДИ (X=280), по бокам по Y (18 и 262)

# Отсек для Beelink Mini S (передняя левая часть)
# Компонент в assemble.py: (8, 8, 16), отсек: (8 - MINIPC_CLEARANCE, 8 - MINIPC_CLEARANCE, WALL_THICKNESS)
minipc_x = WALL_THICKNESS + MINIPC_CLEARANCE - MINIPC_CLEARANCE  # 3
minipc_y = WALL_THICKNESS + MINIPC_CLEARANCE - MINIPC_CLEARANCE  # 3
minipc_z = WALL_THICKNESS  # 3

minipc_compartment = Part.makeBox(
    MINIPC_LENGTH + 2 * MINIPC_CLEARANCE,
    MINIPC_WIDTH + 2 * MINIPC_CLEARANCE,
    MINIPC_HEIGHT + MINIPC_CLEARANCE,
    App.Vector(minipc_x, minipc_y, minipc_z)
)

# Отсек для STM32 (правее MiniPC, передняя часть)
# Компонент в assemble.py: (8, 125, 16), отсек: (8 - STM32_CLEARANCE, 125 - STM32_CLEARANCE, WALL_THICKNESS)
stm32_x = WALL_THICKNESS + MINIPC_CLEARANCE - STM32_CLEARANCE  # 3
stm32_y = WALL_THICKNESS + MINIPC_CLEARANCE + MINIPC_WIDTH + 2 * MINIPC_CLEARANCE + 10 - STM32_CLEARANCE  # 120
stm32_z = WALL_THICKNESS  # 3

stm32_compartment = Part.makeBox(
    STM32_LENGTH + 2 * STM32_CLEARANCE,
    STM32_WIDTH + 2 * STM32_CLEARANCE,
    STM32_HEIGHT + STM32_CLEARANCE,
    App.Vector(stm32_x, stm32_y, stm32_z)
)

# Отсек для батареи (справа в передней части)
# Компонент в assemble.py: (8, 217, 16), отсек: (8 - BATTERY_CLEARANCE, 217 - BATTERY_CLEARANCE, WALL_THICKNESS)
battery_x = WALL_THICKNESS + BATTERY_CLEARANCE - BATTERY_CLEARANCE  # 3
battery_y = CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE - BATTERY_CLEARANCE  # 212
battery_z = WALL_THICKNESS  # 3

battery_compartment = Part.makeBox(
    BATTERY_LENGTH + 2 * BATTERY_CLEARANCE,
    BATTERY_WIDTH + 2 * BATTERY_CLEARANCE,
    BATTERY_HEIGHT + BATTERY_CLEARANCE,
    App.Vector(battery_x, battery_y, battery_z)
)

# Отсеки для драйверов (рядом с батареей)
# Driver1 в assemble.py: (138, 217, 14), отсек: (138 - DRIVER_CLEARANCE, 217 - DRIVER_CLEARANCE, WALL_THICKNESS)
driver1_x = WALL_THICKNESS + BATTERY_CLEARANCE + BATTERY_LENGTH + 2 * BATTERY_CLEARANCE + 10 - DRIVER_CLEARANCE  # 133
driver1_y = CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE - DRIVER_CLEARANCE  # 212
driver1_z = WALL_THICKNESS  # 3

driver1_compartment = Part.makeBox(
    DRIVER_LENGTH + 2 * DRIVER_CLEARANCE,
    DRIVER_WIDTH + 2 * DRIVER_CLEARANCE,
    DRIVER_HEIGHT + DRIVER_CLEARANCE,
    App.Vector(driver1_x, driver1_y, driver1_z)
)

# Driver2 в assemble.py: (138, 242, 14), отсек: (138 - DRIVER_CLEARANCE, 242 - DRIVER_CLEARANCE, WALL_THICKNESS)
driver2_x = driver1_x  # 133
driver2_y = driver1_y + DRIVER_WIDTH + 2 * DRIVER_CLEARANCE + 5 - DRIVER_CLEARANCE  # 237
driver2_z = WALL_THICKNESS  # 3

driver2_compartment = Part.makeBox(
    DRIVER_LENGTH + 2 * DRIVER_CLEARANCE,
    DRIVER_WIDTH + 2 * DRIVER_CLEARANCE,
    DRIVER_HEIGHT + DRIVER_CLEARANCE,
    App.Vector(driver2_x, driver2_y, driver2_z)
)

# Объединение всех отсеков
electronics_box = electronics_box.fuse(minipc_compartment)
electronics_box = electronics_box.fuse(stm32_compartment)
electronics_box = electronics_box.fuse(battery_compartment)
electronics_box = electronics_box.fuse(driver1_compartment)
electronics_box = electronics_box.fuse(driver2_compartment)

# Создание отверстий для вентиляции (на боковых стенках)
def create_vent_holes(side="left"):
    """Создаёт вентиляционные отверстия на боковой стенке"""
    holes = []
    if side == "left":
        x = 0
        y_start = WALL_THICKNESS + 20
        y_end = CASE_WIDTH - WALL_THICKNESS - 20
    else:  # right
        x = CASE_LENGTH - WALL_THICKNESS
        y_start = WALL_THICKNESS + 20
        y_end = CASE_WIDTH - WALL_THICKNESS - 20
    
    z_center = electronics_height / 2
    
    for y in range(int(y_start), int(y_end), VENT_HOLE_SPACING):
        for z_offset in [-VENT_HOLE_SPACING/2, 0, VENT_HOLE_SPACING/2]:
            z = z_center + z_offset
            if WALL_THICKNESS < z < electronics_height - WALL_THICKNESS:
                hole = Part.makeCylinder(
                    VENT_HOLE_DIAMETER / 2,
                    WALL_THICKNESS + 1,
                    App.Vector(x, y, z - (WALL_THICKNESS + 1) / 2),
                    App.Vector(0, 1, 0)  # Направление перпендикулярно стенке
                )
                holes.append(hole)
    
    return holes

vent_holes_left = create_vent_holes("left")
vent_holes_right = create_vent_holes("right")

for hole in vent_holes_left + vent_holes_right:
    electronics_box = electronics_box.cut(hole)

# Создание отверстий для кабелей (в задней стенке)
cable_hole_width = 30
cable_hole_height = 15
cable_hole_x = CASE_LENGTH / 2 - cable_hole_width / 2
cable_hole_y = CASE_WIDTH - WALL_THICKNESS
cable_hole_z = electronics_height / 2 - cable_hole_height / 2

cable_hole = Part.makeBox(
    cable_hole_width,
    WALL_THICKNESS + 1,
    cable_hole_height,
    App.Vector(cable_hole_x, cable_hole_y, cable_hole_z)
)
electronics_box = electronics_box.cut(cable_hole)

# Создание отверстий для крепления (в углах)
screw_holes = []
corner_offset = 15
for x in [corner_offset, CASE_LENGTH - corner_offset]:
    for y in [corner_offset, CASE_WIDTH - corner_offset]:
        hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER / 2,
            electronics_height + 1,
            App.Vector(x, y, -0.5)
        )
        screw_holes.append(hole)

for hole in screw_holes:
    electronics_box = electronics_box.cut(hole)

# Скругление верхних углов
try:
    top_edges = [e for e in electronics_box.Edges 
                 if any(v.Z > electronics_height - 1 for v in e.Vertexes)]
    if top_edges:
        electronics_box = electronics_box.makeFillet(FILLET_RADIUS, top_edges[:8])
except:
    pass

# Создание объекта в документе
electronics_obj = doc.addObject("Part::Feature", "ElectronicsCompartment")
electronics_obj.Shape = electronics_box

# Создание вспомогательных объектов для визуализации компонентов
# Позиции соответствуют assemble.py (компоненты на z=16, но в отсеке это z=WALL_THICKNESS + CLEARANCE)
# В assemble.py компоненты на z=16 относительно корпуса, в отсеке это z=WALL_THICKNESS + CLEARANCE = 8
try:
    FLOOR_THICKNESS
except NameError:
    FLOOR_THICKNESS = 8

minipc_vis = doc.addObject("Part::Box", "MiniPC_Visualization")
minipc_vis.Length = MINIPC_LENGTH
minipc_vis.Width = MINIPC_WIDTH
minipc_vis.Height = MINIPC_HEIGHT
# В assemble.py компонент на (8, 8, 16), где 16 = FLOOR_THICKNESS + WALL_THICKNESS + CLEARANCE
# В отсеке это z = WALL_THICKNESS + CLEARANCE = 3 + 5 = 8
minipc_vis.Placement = App.Placement(
    App.Vector(WALL_THICKNESS + MINIPC_CLEARANCE, WALL_THICKNESS + MINIPC_CLEARANCE, WALL_THICKNESS + MINIPC_CLEARANCE),
    App.Rotation()
)
minipc_vis.ViewObject.ShapeColor = (0.8, 0.2, 0.2)

stm32_vis = doc.addObject("Part::Box", "STM32_Visualization")
stm32_vis.Length = STM32_LENGTH
stm32_vis.Width = STM32_WIDTH
stm32_vis.Height = STM32_HEIGHT
stm32_vis.Placement = App.Placement(
    App.Vector(WALL_THICKNESS + MINIPC_CLEARANCE, WALL_THICKNESS + MINIPC_CLEARANCE + MINIPC_WIDTH + 2 * MINIPC_CLEARANCE + 10, WALL_THICKNESS + STM32_CLEARANCE),
    App.Rotation()
)
stm32_vis.ViewObject.ShapeColor = (0.2, 0.8, 0.2)

battery_vis = doc.addObject("Part::Box", "Battery_Visualization")
battery_vis.Length = BATTERY_LENGTH
battery_vis.Width = BATTERY_WIDTH
battery_vis.Height = BATTERY_HEIGHT
battery_vis.Placement = App.Placement(
    App.Vector(WALL_THICKNESS + BATTERY_CLEARANCE, CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE, WALL_THICKNESS + BATTERY_CLEARANCE),
    App.Rotation()
)
battery_vis.ViewObject.ShapeColor = (0.2, 0.2, 0.8)

driver1_vis = doc.addObject("Part::Box", "Driver1_Visualization")
driver1_vis.Length = DRIVER_LENGTH
driver1_vis.Width = DRIVER_WIDTH
driver1_vis.Height = DRIVER_HEIGHT
driver1_vis.Placement = App.Placement(
    App.Vector(WALL_THICKNESS + BATTERY_CLEARANCE + BATTERY_LENGTH + 2 * BATTERY_CLEARANCE + 10, CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE, WALL_THICKNESS + DRIVER_CLEARANCE),
    App.Rotation()
)
driver1_vis.ViewObject.ShapeColor = (0.8, 0.6, 0.2)

driver2_vis = doc.addObject("Part::Box", "Driver2_Visualization")
driver2_vis.Length = DRIVER_LENGTH
driver2_vis.Width = DRIVER_WIDTH
driver2_vis.Height = DRIVER_HEIGHT
driver2_vis.Placement = App.Placement(
    App.Vector(WALL_THICKNESS + BATTERY_CLEARANCE + BATTERY_LENGTH + 2 * BATTERY_CLEARANCE + 10, CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE + DRIVER_WIDTH + 2 * DRIVER_CLEARANCE + 5, WALL_THICKNESS + DRIVER_CLEARANCE),
    App.Rotation()
)
driver2_vis.ViewObject.ShapeColor = (0.8, 0.6, 0.2)

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Отсек электроники создан успешно!")
print(f"Размеры: {CASE_LENGTH}×{CASE_WIDTH}×{electronics_height} мм")
print("Компоненты размещены в отсеках")
print(f"Beelink Mini S: {MINIPC_LENGTH}×{MINIPC_WIDTH}×{MINIPC_HEIGHT} мм")

