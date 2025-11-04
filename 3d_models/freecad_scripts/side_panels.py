"""
Боковые панели для WatchDog Robot
Создаёт левую и правую защитные панели с вентиляционными отверстиями
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
    CASE_HEIGHT = 220
    WALL_THICKNESS = 3
    SCREW_HOLE_DIAMETER = 3.2
    VENT_HOLE_DIAMETER = 5
    VENT_HOLE_SPACING = 15
    FILLET_RADIUS = 2

# Высота боковых панелей (только до верха отсека электроники, не до башни!)
# Высота отсека электроники (должна совпадать с electronics_compartment.py)
try:
    MINIPC_HEIGHT
    MINIPC_CLEARANCE
    STM32_HEIGHT
    STM32_CLEARANCE
    BATTERY_HEIGHT
    BATTERY_CLEARANCE
except NameError:
    MINIPC_HEIGHT = 41
    MINIPC_CLEARANCE = 5
    STM32_HEIGHT = 18
    STM32_CLEARANCE = 5
    BATTERY_HEIGHT = 35
    BATTERY_CLEARANCE = 5

electronics_height = max(
    MINIPC_HEIGHT + MINIPC_CLEARANCE,
    STM32_HEIGHT + STM32_CLEARANCE,
    BATTERY_HEIGHT + BATTERY_CLEARANCE
) + 10

panel_height = electronics_height  # Высота панели = высоте отсека электроники
panel_width = CASE_WIDTH
panel_thickness = WALL_THICKNESS

# Создание нового документа
doc = App.newDocument("WatchDog_SidePanels")

# Функция создания боковой панели
def create_side_panel(side="left"):
    """Создаёт боковую панель с вентиляционными отверстиями"""
    
    # Основная панель
    panel = Part.makeBox(
        panel_thickness,
        panel_width,
        panel_height
    )
    
    # Стильные вентиляционные отверстия (геометрический паттерн вместо простой решётки)
    vent_holes = []
    vent_start_y = 30
    vent_end_y = panel_width - 30
    vent_start_z = 30
    vent_end_z = panel_height - 30
    
    # Создаём паттерн из шестиугольников и кругов
    # Паттерн: чередуем круги и шестиугольники
    pattern_offset = 0
    for y in range(int(vent_start_y), int(vent_end_y), VENT_HOLE_SPACING * 2):
        for z in range(int(vent_start_z), int(vent_end_z), VENT_HOLE_SPACING * 2):
            # Круглые отверстия
            hole = Part.makeCylinder(
                VENT_HOLE_DIAMETER / 2,
                panel_thickness + 1,
                App.Vector(-0.5, y, z),
                App.Vector(1, 0, 0)
            )
            vent_holes.append(hole)
            
            # Шестиугольное отверстие рядом (смещённое)
            hex_size = VENT_HOLE_DIAMETER / 2
            hex_points = []
            for i in range(6):
                angle = math.pi / 3 * i
                hex_y = y + hex_size * math.cos(angle) / 2
                hex_z = z + VENT_HOLE_SPACING + hex_size * math.sin(angle) / 2
                hex_points.append(App.Vector(-0.5, hex_y, hex_z))
            
            # Создаём шестиугольное отверстие
            hex_wire = Part.makePolygon(hex_points + [hex_points[0]])
            hex_face = Part.Face(Part.Wire(hex_wire.Edges))
            hex_hole = hex_face.extrude(App.Vector(panel_thickness + 1, 0, 0))
            vent_holes.append(hex_hole)
    
    # Вырезаем вентиляционные отверстия
    for hole in vent_holes:
        panel = panel.cut(hole)
    
    # Отверстия для крепления (по углам и по центру)
    mount_holes = []
    corner_offset = 15
    
    # Угловые отверстия
    for y in [corner_offset, panel_width - corner_offset]:
        for z in [corner_offset, panel_height - corner_offset]:
            hole = Part.makeCylinder(
                SCREW_HOLE_DIAMETER / 2,
                panel_thickness + 1,
                App.Vector(-0.5, y, z),
                App.Vector(1, 0, 0)
            )
            mount_holes.append(hole)
    
    # Центральные отверстия (для дополнительного крепления)
    center_y = panel_width / 2
    center_z = panel_height / 2
    
    for z_offset in [-panel_height/4, 0, panel_height/4]:
        hole = Part.makeCylinder(
            SCREW_HOLE_DIAMETER / 2,
            panel_thickness + 1,
            App.Vector(-0.5, center_y, center_z + z_offset),
            App.Vector(1, 0, 0)
        )
        mount_holes.append(hole)
    
    for hole in mount_holes:
        panel = panel.cut(hole)
    
    # Скругление углов
    try:
        edges = [e for e in panel.Edges if len(e.Vertexes) == 2]
        if edges:
            panel = panel.makeFillet(FILLET_RADIUS, edges[:4])
    except:
        pass
    
    return panel

# Создание левой панели
left_panel = create_side_panel("left")
left_panel_obj = doc.addObject("Part::Feature", "LeftSidePanel")
left_panel_obj.Shape = left_panel
left_panel_obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Создание правой панели (зеркально)
right_panel = create_side_panel("right")
right_panel_obj = doc.addObject("Part::Feature", "RightSidePanel")
right_panel_obj.Shape = right_panel
right_panel_obj.Placement = App.Placement(
    App.Vector(CASE_LENGTH - panel_thickness, 0, 0),
    App.Rotation()
)

# Настройка вида
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Боковые панели созданы успешно!")
print(f"Стильный дизайн:")
print(f"  • Геометрический паттерн вентиляции (круги + шестиугольники)")
print(f"  • Закругленные углы")
print(f"Размеры каждой панели: {panel_thickness}×{panel_width}×{panel_height} мм")
print(f"ВНИМАНИЕ: Высота панелей ограничена высотой отсека электроники ({panel_height} мм), не доходят до башни!")

