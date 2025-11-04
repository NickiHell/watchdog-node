#!/usr/bin/env python3
"""
Скрипт для сборки всех деталей корпуса WatchDog Robot в один документ
Создаёт полную сборку корпуса с компонентами для реалистичной визуализации

Включает:
- Все детали корпуса (платформы, отсеки, панели, крышки)
- Все компоненты (Beelink Mini S, STM32, батарея, моторы, колеса, лидар, камера)

Использование:
1. Сначала запустите create_all.py для создания всех деталей
2. Затем запустите этот скрипт:
   exec(open('/home/nickihell/Workspace/Projects/nickihell/watchdog-node/3d_models/freecad_scripts/assemble.py').read())
"""

import FreeCAD as App
import Part
import sys
import os

# Получаем путь к директории со скриптами
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = '/home/nickihell/Workspace/Projects/nickihell/watchdog-node/3d_models/freecad_scripts'

# Импорт параметров
sys.path.insert(0, script_dir)
try:
    from parameters import *
except ImportError:
    FLOOR_THICKNESS = 8
    CASE_LENGTH = 320
    CASE_WIDTH = 280
    CASE_HEIGHT = 220
    WALL_THICKNESS = 3
    LIDAR_TOWER_HEIGHT = 100
    LIDAR_TOWER_BASE_DIAMETER = 120

print("=" * 60)
print("WatchDog Robot - Сборка корпуса")
print("=" * 60)

# Проверяем, что все документы созданы
required_docs = [
    'WatchDog_BasePlate',
    'WatchDog_ElectronicsCompartment',
    'WatchDog_CoolingDuct',
    'WatchDog_TopCover',
    'WatchDog_LidarTower',
    'WatchDog_SidePanels',
    'WatchDog_CameraBracket'
]

missing_docs = []
for doc_name in required_docs:
    try:
        doc = App.getDocument(doc_name)
        if doc is None:
            missing_docs.append(doc_name)
    except:
        missing_docs.append(doc_name)

if missing_docs:
    print("\n⚠ ВНИМАНИЕ: Не найдены следующие документы:")
    for doc in missing_docs:
        print(f"  • {doc}")
    print("\nСначала запустите create_all.py для создания всех деталей!")
    print("=" * 60)
    # Создаём документ сборки в любом случае
else:
    print("\n✓ Все необходимые документы найдены")

# Создаём новый документ для сборки
assembly_doc = App.newDocument("WatchDog_Assembly")
App.setActiveDocument("WatchDog_Assembly")

# Импортируем параметры для правильных расчетов
try:
    from parameters import *
except ImportError:
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
    WALL_THICKNESS = 3
    FLOOR_THICKNESS = 8
    CASE_LENGTH = 320
    CASE_WIDTH = 280
    LIDAR_DIAMETER = 80
    LIDAR_HEIGHT = 50
    LIDAR_TOWER_HEIGHT = 70  # Соответствует parameters.py

# Высота отсека электроники (точный расчет, как в electronics_compartment.py)
electronics_height = max(
    MINIPC_HEIGHT + MINIPC_CLEARANCE,
    STM32_HEIGHT + STM32_CLEARANCE,
    BATTERY_HEIGHT + BATTERY_CLEARANCE
) + 10

# Высота верхней крышки
cover_height = WALL_THICKNESS

print(f"\n📐 Размеры для сборки:")
print(f"  • BasePlate: {CASE_LENGTH}×{CASE_WIDTH}×{FLOOR_THICKNESS} мм")
print(f"  • ElectronicsCompartment: {CASE_LENGTH}×{CASE_WIDTH}×{electronics_height} мм")
print(f"  • TopCover: {CASE_LENGTH}×{CASE_WIDTH}×{cover_height} мм")
print(f"  • Высота отсека: {electronics_height} мм")
print()

# Список деталей для сборки с их позициями
parts = [
    {
        'doc': 'WatchDog_BasePlate',
        'obj_name': 'BasePlate',
        'assembly_name': 'BasePlate',
        'pos': (0, 0, 0),
        'rot': (0, 0, 0),
        'color': (0.8, 0.8, 0.8)  # Серый
    },
    {
        'doc': 'WatchDog_ElectronicsCompartment',
        'obj_name': 'ElectronicsCompartment',
        'assembly_name': 'ElectronicsCompartment',
        'pos': (0, 0, FLOOR_THICKNESS),  # Точно на базовой платформе
        'rot': (0, 0, 0),
        'color': (0.2, 0.6, 0.8)  # Синий
    },
    {
        'doc': 'WatchDog_CoolingDuct',
        'obj_name': 'CoolingDuct',
        'assembly_name': 'CoolingDuct',
        # Cooling duct на боковой стенке задней части (X=большой, Y=справа или слева)
        # Размещаем справа в задней части для вентиляции
        'pos': (CASE_LENGTH - 160, CASE_WIDTH - 100, FLOOR_THICKNESS + electronics_height - 25),
        'rot': (0, 0, 0),
        'color': (0.7, 0.7, 0.9)  # Светло-синий
    },
    {
        'doc': 'WatchDog_TopCover',
        'obj_name': 'TopCover',
        'assembly_name': 'TopCover',
        # TopCover имеет бортики снизу (lip_height = 2), поэтому позиционируем с учётом этого
        # Бортики должны входить внутрь ElectronicsCompartment
        'pos': (0, 0, FLOOR_THICKNESS + electronics_height - 2),  # Бортики входят внутрь
        'rot': (0, 0, 0),
        'color': (0.8, 0.8, 0.8)  # Серый
    },
    {
        'doc': 'WatchDog_LidarTower',
        'obj_name': 'LidarTower',
        'assembly_name': 'LidarTower',
        # Башня в центре (X = CASE_LENGTH/2 = 160, Y = CASE_WIDTH/2 = 140) для попадания в паз top cover
        # Отверстие в top_cover.py на (CASE_LENGTH/2, CASE_WIDTH/2) = (160, 140)
        'pos': (CASE_LENGTH/2, CASE_WIDTH/2, FLOOR_THICKNESS + electronics_height - 2 + cover_height),
        'rot': (0, 0, 0),
        'color': (0.8, 0.2, 0.2)  # Красный
    },
    {
        'doc': 'WatchDog_SidePanels',
        'obj_name': 'LeftSidePanel',
        'assembly_name': 'LeftSidePanel',
        'pos': (0, 0, FLOOR_THICKNESS),  # Левая панель, от начала корпуса
        'rot': (0, 0, 0),
        'color': (0.6, 0.6, 0.6)  # Светло-серый
    },
    {
        'doc': 'WatchDog_SidePanels',
        'obj_name': 'RightSidePanel',
        'assembly_name': 'RightSidePanel',
        'pos': (CASE_LENGTH - WALL_THICKNESS, 0, FLOOR_THICKNESS),  # Правая панель, от правого края
        'rot': (0, 0, 0),
        'color': (0.6, 0.6, 0.6)  # Светло-серый
    },
]

print("\nКопирование деталей в сборку...")
print()

# Копируем детали из отдельных документов
copied_count = 0
failed_count = 0

for part in parts:
    doc_name = part['doc']
    obj_name = part['obj_name']
    assembly_name = part['assembly_name']
    
    try:
        # Проверяем существование документа
        source_doc = App.getDocument(doc_name)
        
        # Находим объект с деталью
        source_obj = None
        
        # Пытаемся найти объект по имени
        if hasattr(source_doc, 'getObject'):
            source_obj = source_doc.getObject(obj_name)
        
        # Если не нашли по имени, ищем первый объект типа Part::Feature
        if source_obj is None:
            for obj in source_doc.Objects:
                if hasattr(obj, 'Shape') and obj.Shape is not None:
                    # Проверяем, что это нужный объект (по имени или типу)
                    if obj_name in obj.Name or obj.Label:
                        source_obj = obj
                        break
        
        # Если всё ещё не нашли, берём первый объект с формой
        if source_obj is None:
            for obj in source_doc.Objects:
                if hasattr(obj, 'Shape') and obj.Shape is not None:
                    source_obj = obj
                    break
        
        if source_obj is None:
            print(f"  ⚠ {doc_name}: объект '{obj_name}' не найден")
            failed_count += 1
            continue
        
        # Копируем форму
        new_obj = assembly_doc.addObject("Part::Feature", assembly_name)
        
        # Проверяем, что форма валидна
        if source_obj.Shape is None:
            print(f"  ⚠ {doc_name}: объект '{obj_name}' не имеет формы")
            failed_count += 1
            continue
        
        new_obj.Shape = source_obj.Shape.copy()
        
        # Устанавливаем позицию
        pos = part['pos']
        rot = part['rot']
        new_obj.Placement = App.Placement(
            App.Vector(pos[0], pos[1], pos[2]),
            App.Rotation(*rot)
        )
        
        # Устанавливаем цвет
        try:
            if hasattr(new_obj, 'ViewObject') and new_obj.ViewObject:
                new_obj.ViewObject.ShapeColor = part['color']
                new_obj.ViewObject.LineColor = (0.0, 0.0, 0.0)  # Чёрные линии
        except Exception:
            pass
        
        print(f"  ✓ {assembly_name} скопирован из {doc_name}")
        copied_count += 1
        
    except Exception as e:
        print(f"  ✗ {doc_name}/{obj_name}: {str(e)}")
        failed_count += 1
        import traceback
        # Печатаем только последнюю строку ошибки для краткости
        error_lines = traceback.format_exc().split('\n')
        if len(error_lines) > 2:
            print(f"     {error_lines[-2]}")

# Обновляем документ перед добавлением компонентов
assembly_doc.recompute()

print("\n" + "=" * 60)
print("Добавление компонентов для визуализации...")
print("=" * 60)

# Добавляем визуализацию всех компонентов
components = []

# Электроника размещена без пересечений
# При виде СВЕРХУ: X - длина (малый X = перед, большой X = зад), Y - ширина (малый Y = слева, большой Y = справа)
# Моторы СЗАДИ (X=280), по бокам по Y (18 и 262)
# Электроника в передней части (малый X = 50-200)

# 1. Beelink Mini S (передняя левая часть, вид сверху)
minipc_x = WALL_THICKNESS + MINIPC_CLEARANCE  # 8 - передняя часть
minipc_y = WALL_THICKNESS + MINIPC_CLEARANCE  # 8 - левая часть
minipc_z = FLOOR_THICKNESS + WALL_THICKNESS + MINIPC_CLEARANCE  # 16

minipc_vis = assembly_doc.addObject("Part::Box", "MiniPC_BeelinkS")
minipc_vis.Length = MINIPC_LENGTH  # 115 (по X)
minipc_vis.Width = MINIPC_WIDTH     # 102 (по Y)
minipc_vis.Height = MINIPC_HEIGHT   # 41 (по Z)
minipc_vis.Placement = App.Placement(
    App.Vector(minipc_x, minipc_y, minipc_z),
    App.Rotation()
)
try:
    if hasattr(minipc_vis, 'ViewObject') and minipc_vis.ViewObject:
        minipc_vis.ViewObject.ShapeColor = (0.1, 0.1, 0.1)
except Exception:
    pass
components.append("Beelink Mini S (передняя левая часть)")

# 2. STM32 Nucleo (чуть правее MiniPC, вид сверху)
stm32_x = minipc_x  # Та же X (передняя часть)
stm32_y = minipc_y + MINIPC_WIDTH + 2 * MINIPC_CLEARANCE + 10  # 125 - правее MiniPC
stm32_z = FLOOR_THICKNESS + WALL_THICKNESS + STM32_CLEARANCE  # 16

stm32_vis = assembly_doc.addObject("Part::Box", "STM32_Nucleo")
stm32_vis.Length = STM32_LENGTH  # 70 (по X)
stm32_vis.Width = STM32_WIDTH    # 52 (по Y)
stm32_vis.Height = STM32_HEIGHT  # 18 (по Z)
stm32_vis.Placement = App.Placement(
    App.Vector(stm32_x, stm32_y, stm32_z),
    App.Rotation()
)
try:
    if hasattr(stm32_vis, 'ViewObject') and stm32_vis.ViewObject:
        stm32_vis.ViewObject.ShapeColor = (0.0, 0.5, 0.0)
except Exception:
    pass
components.append("STM32 Nucleo (правее MiniPC)")

# 3. Батарея Li-Po (справа в передней части, вид сверху)
battery_x = WALL_THICKNESS + BATTERY_CLEARANCE  # 8 - передняя часть
battery_y = CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE  # 217 - справа
battery_z = FLOOR_THICKNESS + WALL_THICKNESS + BATTERY_CLEARANCE  # 16

battery_vis = assembly_doc.addObject("Part::Box", "Battery_LiPo")
battery_vis.Length = BATTERY_LENGTH  # 110 (по X)
battery_vis.Width = BATTERY_WIDTH    # 55 (по Y)
battery_vis.Height = BATTERY_HEIGHT  # 35 (по Z)
battery_vis.Placement = App.Placement(
    App.Vector(battery_x, battery_y, battery_z),
    App.Rotation()
)
try:
    if hasattr(battery_vis, 'ViewObject') and battery_vis.ViewObject:
        battery_vis.ViewObject.ShapeColor = (0.9, 0.9, 0.1)
except Exception:
    pass
components.append("Батарея Li-Po (справа в передней части)")

# 4. Драйверы моторов (рядом с батареей, в передней части)
driver1_x = battery_x + BATTERY_LENGTH + 2 * BATTERY_CLEARANCE + 10  # 138
driver1_y = battery_y  # На той же Y что и батарея
driver1_z = FLOOR_THICKNESS + WALL_THICKNESS + DRIVER_CLEARANCE  # 14

driver1_vis = assembly_doc.addObject("Part::Box", "Driver_Motor1")
driver1_vis.Length = DRIVER_LENGTH  # 25
driver1_vis.Width = DRIVER_WIDTH    # 20
driver1_vis.Height = DRIVER_HEIGHT  # 6
driver1_vis.Placement = App.Placement(
    App.Vector(driver1_x, driver1_y, driver1_z),
    App.Rotation()
)
try:
    if hasattr(driver1_vis, 'ViewObject') and driver1_vis.ViewObject:
        driver1_vis.ViewObject.ShapeColor = (0.8, 0.4, 0.2)
except Exception:
    pass
components.append("Драйвер моторов 1")

driver2_x = driver1_x
driver2_y = driver1_y + DRIVER_WIDTH + 2 * DRIVER_CLEARANCE + 5  # 242
driver2_z = FLOOR_THICKNESS + WALL_THICKNESS + DRIVER_CLEARANCE  # 14

driver2_vis = assembly_doc.addObject("Part::Box", "Driver_Motor2")
driver2_vis.Length = DRIVER_LENGTH  # 25
driver2_vis.Width = DRIVER_WIDTH    # 20
driver2_vis.Height = DRIVER_HEIGHT  # 6
driver2_vis.Placement = App.Placement(
    App.Vector(driver2_x, driver2_y, driver2_z),
    App.Rotation()
)
try:
    if hasattr(driver2_vis, 'ViewObject') and driver2_vis.ViewObject:
        driver2_vis.ViewObject.ShapeColor = (0.8, 0.4, 0.2)
except Exception:
    pass
components.append("Драйвер моторов 2")

# 5. Моторы (на платформах сбоку корпуса)
# Позиции моторов должны совпадать с платформами на базовой плите (base_plate.py)
motor_center_offset_x = CASE_LENGTH / 2
motor_center_offset_y = 40

try:
    MOTOR_PLATFORM_SIZE
    MOTOR_PLATFORM_HEIGHT
    MOTOR_DISTANCE_FROM_CENTER
except NameError:
    MOTOR_PLATFORM_SIZE = 50
    MOTOR_PLATFORM_HEIGHT = 5
    MOTOR_DISTANCE_FROM_CENTER = 60

# Удаляем старые объекты моторов, если они существуют (для обновления позиций)
for obj_name in ['Motor_Left', 'Motor_Right']:
    try:
        old_obj = assembly_doc.getObject(obj_name)
        if old_obj:
            assembly_doc.removeObject(obj_name)
    except:
        pass

# Моторы размещены на платформах базовой плиты
# При виде СВЕРХУ в ортогональной проекции:
# X - длина корпуса (малый X = перед, большой X = зад)
# Y - ширина корпуса (малый Y = слева, большой Y = справа)
# Z - вверх
# Для дифференциального привода: колеса вращаются вперёд/назад (по оси X)
# Ось мотора параллельна Y (поперёк корпуса, вдоль боковых панелей)

# Позиции моторов соответствуют платформам на базовой плите:
# Левый мотор (слева, вид сверху): X = центр - расстояние, Y = отступ от края
# Правый мотор (справа, вид сверху): X = центр + расстояние, Y = отступ от края
left_motor_x = motor_center_offset_x - MOTOR_DISTANCE_FROM_CENTER  # 160 - 60 = 100
right_motor_x = motor_center_offset_x + MOTOR_DISTANCE_FROM_CENTER  # 160 + 60 = 220

# Моторы размещены на платформах, которые находятся на Y = 40 (отступ от края)
motor_y = motor_center_offset_y  # 40
motor_z_position = FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 15  # На оси колеса

# Левый мотор (слева, вид сверху) - ось мотора параллельна Y, выходит налево к левому колесу
left_motor_vis = assembly_doc.addObject("Part::Cylinder", "Motor_Left")
left_motor_vis.Radius = 20  # Диаметр мотора ~40мм
left_motor_vis.Height = 30  # Длина оси мотора (вдоль Y), выходит через левую стенку
left_motor_vis.Placement = App.Placement(
    App.Vector(left_motor_x, motor_y, motor_z_position),
    App.Rotation(App.Vector(1, 0, 0), 90.0)  # ось || Y
)
try:
    if hasattr(left_motor_vis, 'ViewObject') and left_motor_vis.ViewObject:
        left_motor_vis.ViewObject.ShapeColor = (0.5, 0.5, 0.5)
except Exception:
    pass
components.append("Мотор левый (слева на платформе, ось параллельна Y, выходит налево)")

# Правый мотор (справа, вид сверху) - ось мотора параллельна Y, выходит направо к правому колесу
right_motor_vis = assembly_doc.addObject("Part::Cylinder", "Motor_Right")
right_motor_vis.Radius = 20
right_motor_vis.Height = 30
right_motor_vis.Placement = App.Placement(
    App.Vector(right_motor_x, motor_y, motor_z_position),
    App.Rotation(App.Vector(1, 0, 0), 90.0)  # ось || Y
)
try:
    if hasattr(right_motor_vis, 'ViewObject') and right_motor_vis.ViewObject:
        right_motor_vis.ViewObject.ShapeColor = (0.5, 0.5, 0.5)
except Exception:
    pass
components.append("Мотор правый (справа на платформе, ось параллельна Y, выходит направо)")

# 6. Колеса (на осях моторов, сбоку корпуса)
try:
    WHEEL_DIAMETER
    WHEEL_WIDTH
except NameError:
    WHEEL_DIAMETER = 60
    WHEEL_WIDTH = 20

# Удаляем старые объекты колес, если они существуют (для обновления позиций)
for obj_name in ['Wheel_Left', 'Wheel_Right']:
    try:
        old_obj = assembly_doc.getObject(obj_name)
        if old_obj:
            assembly_doc.removeObject(obj_name)
    except:
        pass

# Колеса размещены СНАРУЖИ корпуса, на осях моторов
# Ось вращения параллельна Y (как в base_plate.py), колёса с отступом от стенки
wheel_z_position = motor_z_position
wheel_offset_from_wall = WALL_THICKNESS + 3

# Левое колесо (снаружи слева, на той же оси X что и левый мотор)
# Ось вращения параллельна Y (поворот вокруг Y, как в base_plate.py)
left_wheel_vis = assembly_doc.addObject("Part::Cylinder", "Wheel_Left")
left_wheel_vis.Radius = WHEEL_DIAMETER / 2
left_wheel_vis.Height = WHEEL_WIDTH
left_wheel_vis.Placement = App.Placement(
    App.Vector(left_motor_x, -wheel_offset_from_wall - WHEEL_DIAMETER/2, wheel_z_position),
    App.Rotation(App.Vector(0, 1, 0), 90.0)  # Колесо вертикально, перпендикулярно оси мотора (поворот вокруг Y)
)
try:
    if hasattr(left_wheel_vis, 'ViewObject') and left_wheel_vis.ViewObject:
        left_wheel_vis.ViewObject.ShapeColor = (0.2, 0.2, 0.2)
        left_wheel_vis.ViewObject.Transparency = 30
except Exception:
    pass
components.append("Колесо левое (снаружи слева, на оси левого мотора)")

# Правое колесо (снаружи справа, на той же оси X что и правый мотор)
# Ось вращения параллельна Y (поворот вокруг Y, как в base_plate.py)
right_wheel_vis = assembly_doc.addObject("Part::Cylinder", "Wheel_Right")
right_wheel_vis.Radius = WHEEL_DIAMETER / 2
right_wheel_vis.Height = WHEEL_WIDTH
right_wheel_vis.Placement = App.Placement(
    App.Vector(right_motor_x, CASE_WIDTH + wheel_offset_from_wall + WHEEL_DIAMETER/2, wheel_z_position),
    App.Rotation(App.Vector(0, 1, 0), 90.0)  # Колесо вертикально, перпендикулярно оси мотора (поворот вокруг Y)
)
try:
    if hasattr(right_wheel_vis, 'ViewObject') and right_wheel_vis.ViewObject:
        right_wheel_vis.ViewObject.ShapeColor = (0.2, 0.2, 0.2)
        right_wheel_vis.ViewObject.Transparency = 30
except Exception:
    pass
components.append("Колесо правое (снаружи справа, на оси правого мотора)")

# 7. Лидар MOP3 (на башне)
# Башня в центре (X=160, Y=140), лидар на той же позиции что и башня
lidar_vis = assembly_doc.addObject("Part::Cylinder", "Lidar_MOP3")
lidar_vis.Radius = LIDAR_DIAMETER / 2
lidar_vis.Height = LIDAR_HEIGHT
lidar_tower_base_z = FLOOR_THICKNESS + electronics_height - 2 + cover_height
lidar_vis.Placement = App.Placement(
    App.Vector(
        CASE_LENGTH / 2,   # Центр по X (посередине) = 160
        CASE_WIDTH / 2,    # Центр по Y (посередине) = 140
        lidar_tower_base_z + LIDAR_TOWER_HEIGHT
    ),
    App.Rotation()
)
try:
    if hasattr(lidar_vis, 'ViewObject') and lidar_vis.ViewObject:
        lidar_vis.ViewObject.ShapeColor = (0.3, 0.3, 0.3)
except Exception:
    pass
components.append("Лидар MOP3 (на башне, в центре)")

# 8. USB камера (на верхней крышке в переднем углу, направлена вперед)
# Камера в переднем правом углу на платформе top_cover
USB_CAMERA_SIZE = 40  # Типичный размер USB камеры
USB_CAMERA_HEIGHT = 25  # Высота USB камеры
USB_CAMERA_MOUNT_HEIGHT = 10  # Высота платформы для крепления (из top_cover.py)
camera_mount_offset = 15  # Отступ от краев (соответствует top_cover.py)
# Камера на платформе, которая находится на top_cover
camera_top_z = FLOOR_THICKNESS + electronics_height - 2 + cover_height + USB_CAMERA_MOUNT_HEIGHT

camera_vis = assembly_doc.addObject("Part::Box", "Camera_USB")
camera_vis.Length = USB_CAMERA_SIZE
camera_vis.Width = USB_CAMERA_SIZE
camera_vis.Height = USB_CAMERA_HEIGHT
# Камера в переднем правом углу (вид сверху: X малый = перед, Y большой = справа)
camera_vis.Placement = App.Placement(
    App.Vector(
        camera_mount_offset,  # ПЕРЕД (малый X), соответствует top_cover.py
        CASE_WIDTH - USB_CAMERA_SIZE - camera_mount_offset,  # ПРАВО (большой Y), соответствует top_cover.py
        camera_top_z
    ),
    App.Rotation(App.Vector(1, 0, 0), 90)
)
try:
    if hasattr(camera_vis, 'ViewObject') and camera_vis.ViewObject:
        camera_vis.ViewObject.ShapeColor = (0.1, 0.1, 0.1)
except Exception:
    pass
components.append("USB камера (на top cover в переднем правом углу, направлена вперед)")

# 9. Вентилятор для охлаждения (в канале охлаждения на боковой стенке задней части)
fan_vis = assembly_doc.addObject("Part::Box", "Fan_Cooling")
fan_vis.Length = 40  # FAN_SIZE
fan_vis.Width = 40   # FAN_SIZE
fan_vis.Height = 10  # FAN_THICKNESS
# Вентилятор в cooling duct, который на боковой стенке задней части
fan_vis.Placement = App.Placement(
    App.Vector(
        CASE_LENGTH - 160 + 135,  # Позиция в cooling duct (задняя часть, X=большой)
        CASE_WIDTH - 100 + 20,    # Позиция в cooling duct (справа, Y=большой)
        FLOOR_THICKNESS + electronics_height - 30
    ),
    App.Rotation()
)
try:
    if hasattr(fan_vis, 'ViewObject') and fan_vis.ViewObject:
        fan_vis.ViewObject.ShapeColor = (0.7, 0.7, 0.7)
except Exception:
    pass
components.append("Вентилятор охлаждения (на боковой стенке задней части)")

# 10. Опорное колесо (caster wheel) - СПЕРЕДИ под днищем, посередине по Y
# Механизм крепления: платформа с отверстием для винта M3, поворотный механизм
caster_mount_height = 8  # Высота платформы для крепления (увеличена для стабильности)
caster_radius = 15  # Радиус опорного колеса
caster_x = 30  # СПЕРЕДИ корпуса (малый X)
caster_y = CASE_WIDTH / 2  # По центру по Y (посередине) = 140

# Платформа для крепления кастера (круглая платформа под днищем с усилением)
caster_mount_base = assembly_doc.addObject("Part::Cylinder", "CasterMountBase")
caster_mount_base.Radius = caster_radius + 10  # Увеличенная платформа для стабильности
caster_mount_base.Height = caster_mount_height
caster_mount_base.Placement = App.Placement(
    App.Vector(caster_x, caster_y, FLOOR_THICKNESS - caster_mount_height),
    App.Rotation()
)
try:
    if hasattr(caster_mount_base, 'ViewObject') and caster_mount_base.ViewObject:
        caster_mount_base.ViewObject.ShapeColor = (0.6, 0.6, 0.6)
except Exception:
    pass

# Центральное отверстие для крепления кастера (M3 винт)
caster_mount_hole = assembly_doc.addObject("Part::Cylinder", "CasterMountHole")
caster_mount_hole.Radius = 3.2 / 2  # M3 винт
caster_mount_hole.Height = caster_mount_height + 1
caster_mount_hole.Placement = App.Placement(
    App.Vector(caster_x, caster_y, FLOOR_THICKNESS - caster_mount_height - 0.5),
    App.Rotation()
)
try:
    if hasattr(caster_mount_hole, 'ViewObject') and caster_mount_hole.ViewObject:
        caster_mount_hole.ViewObject.Transparency = 50
except Exception:
    pass

# Поворотный механизм (короткий цилиндр для шарнира)
caster_swivel = assembly_doc.addObject("Part::Cylinder", "CasterSwivel")
caster_swivel.Radius = 8  # Радиус шарнира
caster_swivel.Height = 5  # Высота шарнира
caster_swivel.Placement = App.Placement(
    App.Vector(caster_x, caster_y, FLOOR_THICKNESS - caster_mount_height),
    App.Rotation()
)
try:
    if hasattr(caster_swivel, 'ViewObject') and caster_swivel.ViewObject:
        caster_swivel.ViewObject.ShapeColor = (0.5, 0.5, 0.5)
except Exception:
    pass

# Кастер колесо (СПЕРЕДИ под днищем на платформе)
caster_vis = assembly_doc.addObject("Part::Sphere", "CasterWheel")
caster_vis.Radius = caster_radius
caster_vis.Placement = App.Placement(
    App.Vector(caster_x, caster_y, FLOOR_THICKNESS - caster_mount_height - caster_radius),
    App.Rotation()
)
try:
    if hasattr(caster_vis, 'ViewObject') and caster_vis.ViewObject:
        caster_vis.ViewObject.ShapeColor = (0.4, 0.4, 0.4)
except Exception:
    pass
components.append("Опорное колесо (caster, СПЕРЕДИ под днищем, с механизмом крепления)")

print(f"\n✓ Добавлено {len(components)} компонентов:")
for comp in components:
    print(f"  • {comp}")

# Обновляем документ
assembly_doc.recompute()

print()
print("=" * 60)
print(f"Результаты сборки:")
print(f"  ✓ Успешно скопировано: {copied_count}")
print(f"  ✓ Добавлено компонентов: {len(components)}")
print(f"  ✗ Ошибок: {failed_count}")
print("=" * 60)

if copied_count > 0:
    print("\n✓ Сборка создана: WatchDog_Assembly")
    print("\n📊 Структура сборки (по высоте Z):")
    print(f"  • BasePlate: z = 0 до {FLOOR_THICKNESS} мм")
    print(f"  • ElectronicsCompartment: z = {FLOOR_THICKNESS} до {FLOOR_THICKNESS + electronics_height} мм")
    print(f"  • SidePanels: z = {FLOOR_THICKNESS} до {FLOOR_THICKNESS + electronics_height} мм (высота {electronics_height} мм)")
    print(f"  • TopCover: z = {FLOOR_THICKNESS + electronics_height - 2} до {FLOOR_THICKNESS + electronics_height - 2 + cover_height + 2} мм")
    print(f"    (бортики входят внутрь ElectronicsCompartment на 2 мм)")
    print(f"  • LidarTower: z = {FLOOR_THICKNESS + electronics_height - 2 + cover_height} мм (основание на TopCover)")
    print("\nУправление видом:")
    print("  • Вращение: средняя кнопка мыши")
    print("  • Масштаб: колесо мыши")
    print("  • Панорамирование: Shift + средняя кнопка мыши")
    print("  • Подогнать вид: клавиша '0' или View → Standard views → Fit all")
    print("\nЦвета деталей корпуса:")
    print("  • Серый - BasePlate, TopCover")
    print("  • Синий - ElectronicsCompartment")
    print("  • Светло-синий - CoolingDuct")
    print("  • Красный - LidarTower")
    print("  • Зелёный - CameraBracket")
    print("  • Светло-серый - SidePanels")
    print("\nЦвета компонентов:")
    print("  • Чёрный - Beelink Mini S, Камера")
    print("  • Зелёный - STM32 Nucleo")
    print("  • Жёлтый - Батарея Li-Po")
    print("  • Коричневый - Драйверы моторов")
    print("  • Серый - Моторы, Колеса, Лидар")
    print("  • Светло-серый - Вентилятор")
    
    # Подгоняем вид
    try:
        Gui.SendMsgToActiveView("ViewFit")
    except:
        pass
    
    print("\n💡 Советы:")
    print("   • Вы можете скрыть отдельные детали, сняв галочку")
    print("     рядом с объектом в дереве проекта (Tree View)")
    print("   • Компоненты можно скрыть для лучшего вида корпуса")
    print("   • Все компоненты размещены в соответствии с отсеками корпуса")
else:
    print("\n⚠ Не удалось скопировать ни одной детали!")
    print("   Убедитесь, что вы сначала запустили create_all.py")

print("\n" + "=" * 60)

