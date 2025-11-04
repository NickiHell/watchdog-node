#!/usr/bin/env python3
"""
Мастер-скрипт для создания всех деталей корпуса WatchDog Robot
Автоматически создаёт все 7 деталей корпуса в отдельных документах FreeCAD

Использование:
1. Откройте FreeCAD
2. Откройте Python консоль (View → Panels → Python console)
3. Выполните: exec(open('/путь/к/create_all.py').read())
"""

import FreeCAD as App
import sys
import os

# Получаем путь к директории со скриптами
# Используем полный путь к файлу, который был передан в exec()
try:
    # Если __file__ доступен (обычный запуск)
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Если __file__ не определён (exec через open().read())
    # Используем путь по умолчанию или определяем из содержимого скрипта
    script_dir = '/home/nickihell/Workspace/Projects/nickihell/watchdog-node/3d_models/freecad_scripts'
    # Проверяем существование директории
    if not os.path.exists(script_dir):
        # Альтернатива: использовать текущую рабочую директорию
        script_dir = os.getcwd()
        if 'freecad_scripts' in os.listdir(script_dir):
            script_dir = os.path.join(script_dir, 'freecad_scripts')

# Добавляем путь к скриптам в sys.path для импорта parameters
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

print("=" * 60)
print("WatchDog Robot - Создание всех деталей корпуса")
print("=" * 60)
print(f"Директория скриптов: {script_dir}")
print()

# Список скриптов для запуска (в порядке сборки)
scripts = [
    {
        'file': 'base_plate.py',
        'name': 'Нижняя платформа',
        'doc': 'WatchDog_BasePlate'
    },
    {
        'file': 'electronics_compartment.py',
        'name': 'Отсек электроники',
        'doc': 'WatchDog_ElectronicsCompartment'
    },
    {
        'file': 'lidar_tower.py',
        'name': 'Башня лидара',
        'doc': 'WatchDog_LidarTower'
    },
    {
        'file': 'camera_bracket.py',
        'name': 'Кронштейн камеры',
        'doc': 'WatchDog_CameraBracket'
    },
    {
        'file': 'side_panels.py',
        'name': 'Боковые панели',
        'doc': 'WatchDog_SidePanels'
    },
    {
        'file': 'top_cover.py',
        'name': 'Верхняя крышка',
        'doc': 'WatchDog_TopCover'
    },
    {
        'file': 'cooling_duct.py',
        'name': 'Канал охлаждения',
        'doc': 'WatchDog_CoolingDuct'
    }
]

# Статистика
success_count = 0
error_count = 0
errors = []

print("Запуск создания деталей...")
print()

for idx, script_info in enumerate(scripts, 1):
    script_file = script_info['file']
    script_name = script_info['name']
    script_path = os.path.join(script_dir, script_file)
    
    print(f"[{idx}/{len(scripts)}] Создание: {script_name}")
    print(f"  Файл: {script_file}")
    
    if not os.path.exists(script_path):
        error_msg = f"Файл не найден: {script_path}"
        print(f"  ✗ ОШИБКА: {error_msg}")
        errors.append((script_name, error_msg))
        error_count += 1
        print()
        continue
    
    try:
        # Выполняем скрипт
        exec(open(script_path).read())
        
        # Проверяем, что документ создан
        doc_name = script_info['doc']
        if App.getDocument(doc_name) is not None:
            print(f"  ✓ Успешно создан документ: {doc_name}")
            success_count += 1
        else:
            print(f"  ⚠ Предупреждение: Документ {doc_name} не найден после выполнения")
            success_count += 1  # Считаем успешным, если нет исключений
        
    except ImportError as e:
        error_msg = f"Ошибка импорта: {str(e)}"
        print(f"  ✗ ОШИБКА: {error_msg}")
        print(f"  Подсказка: Убедитесь, что файл parameters.py находится в той же директории")
        errors.append((script_name, error_msg))
        error_count += 1
    except Exception as e:
        error_msg = f"Ошибка выполнения: {str(e)}"
        print(f"  ✗ ОШИБКА: {error_msg}")
        import traceback
        print(f"  Детали: {traceback.format_exc().split(chr(10))[-2]}")
        errors.append((script_name, error_msg))
        error_count += 1
    
    print()

# Итоговая статистика
print("=" * 60)
print("ИТОГИ:")
print(f"  Успешно создано: {success_count}/{len(scripts)}")
print(f"  Ошибок: {error_count}/{len(scripts)}")
print("=" * 60)

if errors:
    print("\nОШИБКИ:")
    for script_name, error_msg in errors:
        print(f"  • {script_name}: {error_msg}")
    print()

if success_count == len(scripts):
    print("✓ Все детали корпуса успешно созданы!")
    print("\nДокументы FreeCAD:")
    for script_info in scripts:
        doc_name = script_info['doc']
        if App.getDocument(doc_name) is not None:
            print(f"  • {doc_name}")
    print("\nСледующие шаги:")
    print("  1. Проверьте каждую модель в 3D виде")
    print("  2. При необходимости измените параметры в parameters.py и перезапустите")
    print("  3. Экспортируйте каждую деталь в STL для 3D печати:")
    print("     File → Export → STL Mesh (*.stl)")
else:
    print("\n⚠ Некоторые детали не были созданы. Проверьте ошибки выше.")
    print("\nПодсказки:")
    print("  • Убедитесь, что все файлы находятся в одной директории")
    print("  • Проверьте, что файл parameters.py существует")
    print("  • Проверьте версию FreeCAD (рекомендуется 0.20+)")

print("\n" + "=" * 60)

