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
    LIDAR_TOWER_HEIGHT = 100

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
        'pos': (CASE_LENGTH/2 - 60, CASE_WIDTH/2 - 50, FLOOR_THICKNESS + electronics_height - 25),
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
        # Башня стоит на верхней крышке, с учётом бортиков крышки
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
        new_obj.ViewObject.ShapeColor = part['color']
        new_obj.ViewObject.LineColor = (0.0, 0.0, 0.0)  # Чёрные линии
        
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

# 1. Beelink Mini S (в отсеке электроники)
minipc_x = WALL_THICKNESS + MINIPC_CLEARANCE
minipc_y = WALL_THICKNESS + MINIPC_CLEARANCE
minipc_z = FLOOR_THICKNESS + WALL_THICKNESS + MINIPC_CLEARANCE

minipc_vis = assembly_doc.addObject("Part::Box", "MiniPC_BeelinkS")
minipc_vis.Length = MINIPC_LENGTH
minipc_vis.Width = MINIPC_WIDTH
minipc_vis.Height = MINIPC_HEIGHT
minipc_vis.Placement = App.Placement(
    App.Vector(minipc_x, minipc_y, minipc_z),
    App.Rotation()
)
minipc_vis.ViewObject.ShapeColor = (0.1, 0.1, 0.1)  # Почти чёрный
components.append("Beelink Mini S")

# 2. STM32 Nucleo (рядом с Beelink Mini S)
stm32_x = minipc_x + MINIPC_LENGTH + 2 * MINIPC_CLEARANCE + 10
stm32_y = FLOOR_THICKNESS + WALL_THICKNESS + STM32_CLEARANCE
stm32_z = FLOOR_THICKNESS + WALL_THICKNESS + STM32_CLEARANCE

stm32_vis = assembly_doc.addObject("Part::Box", "STM32_Nucleo")
stm32_vis.Length = STM32_LENGTH
stm32_vis.Width = STM32_WIDTH
stm32_vis.Height = STM32_HEIGHT
stm32_vis.Placement = App.Placement(
    App.Vector(stm32_x, stm32_y, stm32_z),
    App.Rotation()
)
stm32_vis.ViewObject.ShapeColor = (0.0, 0.5, 0.0)  # Зелёный (Nucleo)
components.append("STM32 Nucleo")

# 3. Батарея Li-Po (с другой стороны)
battery_x = WALL_THICKNESS + BATTERY_CLEARANCE
battery_y = CASE_WIDTH - WALL_THICKNESS - BATTERY_WIDTH - BATTERY_CLEARANCE
battery_z = FLOOR_THICKNESS + WALL_THICKNESS + BATTERY_CLEARANCE

battery_vis = assembly_doc.addObject("Part::Box", "Battery_LiPo")
battery_vis.Length = BATTERY_LENGTH
battery_vis.Width = BATTERY_WIDTH
battery_vis.Height = BATTERY_HEIGHT
battery_vis.Placement = App.Placement(
    App.Vector(battery_x, battery_y, battery_z),
    App.Rotation()
)
battery_vis.ViewObject.ShapeColor = (0.9, 0.9, 0.1)  # Жёлтый (батарея)
components.append("Батарея Li-Po")

# 4. Драйверы моторов (2 шт, рядом с батареей)
driver1_x = battery_x + BATTERY_LENGTH + 2 * BATTERY_CLEARANCE + 10
driver1_y = battery_y
driver1_z = FLOOR_THICKNESS + WALL_THICKNESS + DRIVER_CLEARANCE

driver1_vis = assembly_doc.addObject("Part::Box", "Driver_Motor1")
driver1_vis.Length = DRIVER_LENGTH
driver1_vis.Width = DRIVER_WIDTH
driver1_vis.Height = DRIVER_HEIGHT
driver1_vis.Placement = App.Placement(
    App.Vector(driver1_x, driver1_y, driver1_z),
    App.Rotation()
)
driver1_vis.ViewObject.ShapeColor = (0.8, 0.4, 0.2)  # Коричневый
components.append("Драйвер моторов 1")

driver2_x = driver1_x
driver2_y = driver1_y + DRIVER_WIDTH + 2 * DRIVER_CLEARANCE + 5
driver2_z = FLOOR_THICKNESS + WALL_THICKNESS + DRIVER_CLEARANCE

driver2_vis = assembly_doc.addObject("Part::Box", "Driver_Motor2")
driver2_vis.Length = DRIVER_LENGTH
driver2_vis.Width = DRIVER_WIDTH
driver2_vis.Height = DRIVER_HEIGHT
driver2_vis.Placement = App.Placement(
    App.Vector(driver2_x, driver2_y, driver2_z),
    App.Rotation()
)
driver2_vis.ViewObject.ShapeColor = (0.8, 0.4, 0.2)  # Коричневый
components.append("Драйвер моторов 2")

# 5. Моторы (на платформах сбоку корпуса)
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

# Левый мотор (сбоку слева, ось мотора параллельна оси X)
# Мотор внутри корпуса, но ось продолжается к колесу слева
left_motor_vis = assembly_doc.addObject("Part::Cylinder", "Motor_Left")
left_motor_vis.Radius = 20  # Диаметр мотора ~40мм
left_motor_vis.Height = 30  # Высота мотора (длина оси)
left_motor_vis.Placement = App.Placement(
    App.Vector(
        motor_center_offset_x - MOTOR_DISTANCE_FROM_CENTER,
        WALL_THICKNESS + 10,  # Внутри корпуса, но близко к левому краю
        FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 15  # На оси колеса
    ),
    App.Rotation(App.Vector(0, 1, 0), 90)  # Ось мотора параллельна X (горизонтально)
)
left_motor_vis.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Серый
components.append("Мотор левый (внутри, слева)")

# Правый мотор (сбоку справа)
# Мотор внутри корпуса, но ось продолжается к колесу справа
right_motor_vis = assembly_doc.addObject("Part::Cylinder", "Motor_Right")
right_motor_vis.Radius = 20
right_motor_vis.Height = 30
right_motor_vis.Placement = App.Placement(
    App.Vector(
        motor_center_offset_x + MOTOR_DISTANCE_FROM_CENTER,
        CASE_WIDTH - WALL_THICKNESS - 10,  # Внутри корпуса, но близко к правому краю
        FLOOR_THICKNESS + MOTOR_PLATFORM_HEIGHT + 15
    ),
    App.Rotation(App.Vector(0, 1, 0), 90)  # Ось мотора параллельна X (горизонтально)
)
right_motor_vis.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Серый
components.append("Мотор правый (внутри, справа)")

# 6. Колеса (на осях моторов, сбоку корпуса)
try:
    WHEEL_DIAMETER
    WHEEL_WIDTH
except NameError:
    WHEEL_DIAMETER = 60
    WHEEL_WIDTH = 20

# Левое колесо (сбоку слева, перпендикулярно оси мотора)
left_wheel_vis = assembly_doc.addObject("Part::Cylinder", "Wheel_Left")
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
left_wheel_vis.ViewObject.ShapeColor = (0.2, 0.2, 0.2)  # Тёмно-серый
left_wheel_vis.ViewObject.Transparency = 30
components.append("Колесо левое (слева)")

# Правое колесо (сбоку справа)
right_wheel_vis = assembly_doc.addObject("Part::Cylinder", "Wheel_Right")
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
right_wheel_vis.ViewObject.ShapeColor = (0.2, 0.2, 0.2)  # Тёмно-серый
right_wheel_vis.ViewObject.Transparency = 30
components.append("Колесо правое (справа)")

# 7. Лидар MOP3 (на башне)
lidar_vis = assembly_doc.addObject("Part::Cylinder", "Lidar_MOP3")
lidar_vis.Radius = LIDAR_DIAMETER / 2
lidar_vis.Height = LIDAR_HEIGHT
lidar_tower_base_z = FLOOR_THICKNESS + electronics_height - 2 + cover_height
lidar_vis.Placement = App.Placement(
    App.Vector(
        CASE_LENGTH / 2,
        CASE_WIDTH / 2,
        lidar_tower_base_z + LIDAR_TOWER_HEIGHT
    ),
    App.Rotation()
)
lidar_vis.ViewObject.ShapeColor = (0.3, 0.3, 0.3)  # Тёмно-серый
components.append("Лидар MOP3")

# 8. USB камера (на верхней крышке в углу справа спереди)
# USB камера крепится на платформу на top cover
USB_CAMERA_SIZE = 40  # Типичный размер USB камеры
USB_CAMERA_HEIGHT = 25  # Высота USB камеры
USB_CAMERA_MOUNT_HEIGHT = 10  # Высота платформы для крепления
camera_mount_offset = 15  # Отступ от края

# Высота top cover с учётом платформы для камеры
try:
    cover_height
except NameError:
    cover_height = WALL_THICKNESS

camera_vis = assembly_doc.addObject("Part::Box", "Camera_USB")
camera_vis.Length = USB_CAMERA_SIZE
camera_vis.Width = USB_CAMERA_SIZE
camera_vis.Height = USB_CAMERA_HEIGHT
# Камера на платформе в углу top cover (справа спереди)
camera_vis.Placement = App.Placement(
    App.Vector(
        CASE_LENGTH - USB_CAMERA_SIZE - camera_mount_offset,  # Справа
        CASE_WIDTH - USB_CAMERA_SIZE - camera_mount_offset,    # Спереди
        FLOOR_THICKNESS + electronics_height - 2 + cover_height + USB_CAMERA_MOUNT_HEIGHT  # На платформе
    ),
    App.Rotation()  # Камера смотрит вверх/вперёд
)
camera_vis.ViewObject.ShapeColor = (0.1, 0.1, 0.1)  # Чёрный
components.append("USB камера (на top cover в углу)")

# 9. Вентилятор для охлаждения (в канале охлаждения)
fan_vis = assembly_doc.addObject("Part::Box", "Fan_Cooling")
fan_vis.Length = 40  # FAN_SIZE
fan_vis.Width = 40   # FAN_SIZE
fan_vis.Height = 10  # FAN_THICKNESS
fan_vis.Placement = App.Placement(
    App.Vector(
        CASE_LENGTH/2 - 20,
        CASE_WIDTH/2 - 20,
        FLOOR_THICKNESS + electronics_height - 30
    ),
    App.Rotation()
)
fan_vis.ViewObject.ShapeColor = (0.7, 0.7, 0.7)  # Светло-серый
components.append("Вентилятор охлаждения")

# 10. Опорное колесо (caster wheel) - спереди под днищем
# Опорное колесо должно быть спереди корпуса (большое X), под днищем (низкое Z), по центру по Y
caster_vis = assembly_doc.addObject("Part::Sphere", "CasterWheel")
caster_vis.Radius = 15  # Радиус опорного колеса
# Опорное колесо спереди корпуса, под днищем (ниже FLOOR_THICKNESS), по центру по Y
caster_vis.Placement = App.Placement(
    App.Vector(
        CASE_LENGTH - 30,  # Спереди корпуса (большое X)
        CASE_WIDTH / 2,    # По центру по Y
        FLOOR_THICKNESS - 10  # Под днищем (ниже уровня днища)
    ),
    App.Rotation()
)
caster_vis.ViewObject.ShapeColor = (0.4, 0.4, 0.4)  # Серый
components.append("Опорное колесо (caster, спереди под днищем)")

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

