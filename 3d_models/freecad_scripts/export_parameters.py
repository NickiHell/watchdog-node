#!/usr/bin/env python3
"""
Скрипт для экспорта параметров из FreeCAD модели обратно в Python код
Помогает синхронизировать изменения, сделанные вручную в FreeCAD, с исходными скриптами

Использование:
1. Откройте нужный документ в FreeCAD
2. В Python консоли выполните:
   exec(open('/home/nickihell/Workspace/Projects/nickihell/watchdog-node/3d_models/freecad_scripts/export_parameters.py').read())
3. Вызовите функцию:
   export_document('WatchDog_BasePlate')
   или
   export_all_documents()
"""

import FreeCAD as App
import Part

def export_object_parameters(obj, indent=0):
    """Экспортирует параметры объекта в Python код"""
    indent_str = " " * indent
    
    code_lines = []
    code_lines.append(f"{indent_str}# ===== Объект: {obj.Name} ({obj.TypeId}) =====")
    
    # Базовые параметры формы
    if hasattr(obj, 'Shape'):
        shape = obj.Shape
        if hasattr(shape, 'BoundBox'):
            bbox = shape.BoundBox
            code_lines.append(f"{indent_str}# Размеры: {bbox.XLength:.2f}×{bbox.YLength:.2f}×{bbox.ZLength:.2f} мм")
            code_lines.append(f"{indent_str}# Позиция центра: ({bbox.XMin + bbox.XLength/2:.2f}, {bbox.YMin + bbox.YLength/2:.2f}, {bbox.ZMin + bbox.ZLength/2:.2f})")
            code_lines.append(f"{indent_str}# Минимум: ({bbox.XMin:.2f}, {bbox.YMin:.2f}, {bbox.ZMin:.2f})")
            code_lines.append(f"{indent_str}# Максимум: ({bbox.XMax:.2f}, {bbox.YMax:.2f}, {bbox.ZMax:.2f})")
    
    # Placement (позиция и поворот)
    if hasattr(obj, 'Placement'):
        pl = obj.Placement
        pos = pl.Base
        rot = pl.Rotation
        code_lines.append(f"{indent_str}# Placement:")
        code_lines.append(f"{indent_str}#   Position: App.Vector({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")
        if rot.Angle > 0.001:  # Только если есть поворот
            code_lines.append(f"{indent_str}#   Rotation: App.Rotation(App.Vector({rot.Axis.x:.6f}, {rot.Axis.y:.6f}, {rot.Axis.z:.6f}), {rot.Angle * 180 / 3.14159:.2f})")
        else:
            code_lines.append(f"{indent_str}#   Rotation: App.Rotation()  # Без поворота")
    
    # Специфичные параметры для разных типов объектов
    if hasattr(obj, 'Length') and hasattr(obj, 'Width') and hasattr(obj, 'Height'):
        # Box
        code_lines.append(f"{indent_str}# Box параметры:")
        code_lines.append(f"{indent_str}#   Length = {obj.Length:.2f}")
        code_lines.append(f"{indent_str}#   Width = {obj.Width:.2f}")
        code_lines.append(f"{indent_str}#   Height = {obj.Height:.2f}")
        code_lines.append(f"{indent_str}#   Код: Part.makeBox({obj.Length:.2f}, {obj.Width:.2f}, {obj.Height:.2f})")
    
    if hasattr(obj, 'Radius') and hasattr(obj, 'Height'):
        # Cylinder
        code_lines.append(f"{indent_str}# Cylinder параметры:")
        code_lines.append(f"{indent_str}#   Radius = {obj.Radius:.2f}")
        code_lines.append(f"{indent_str}#   Height = {obj.Height:.2f}")
        code_lines.append(f"{indent_str}#   Код: Part.makeCylinder({obj.Radius:.2f}, {obj.Height:.2f})")
    
    if hasattr(obj, 'Radius') and not hasattr(obj, 'Height'):
        # Sphere
        code_lines.append(f"{indent_str}# Sphere параметры:")
        code_lines.append(f"{indent_str}#   Radius = {obj.Radius:.2f}")
        code_lines.append(f"{indent_str}#   Код: Part.makeSphere({obj.Radius:.2f})")
    
    # Цвет объекта
    if hasattr(obj, 'ViewObject') and hasattr(obj.ViewObject, 'ShapeColor'):
        color = obj.ViewObject.ShapeColor
        code_lines.append(f"{indent_str}#   Color: ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
        code_lines.append(f"{indent_str}#   Код: obj.ViewObject.ShapeColor = ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
    
    # Прозрачность
    if hasattr(obj, 'ViewObject') and hasattr(obj.ViewObject, 'Transparency'):
        trans = obj.ViewObject.Transparency
        code_lines.append(f"{indent_str}#   Transparency: {trans}")
        code_lines.append(f"{indent_str}#   Код: obj.ViewObject.Transparency = {trans}")
    
    return "\n".join(code_lines)

def export_document(doc_name):
    """Экспортирует параметры всех объектов из документа"""
    try:
        doc = App.getDocument(doc_name)
    except:
        print(f"ОШИБКА: Документ '{doc_name}' не найден!")
        docs = App.listDocuments()
        if docs:
            print(f"\nДоступные документы:")
            for doc_name_avail in docs.keys():
                print(f"  • {doc_name_avail}")
            print(f"\nИспользуйте одно из имён выше")
        else:
            print(f"Нет открытых документов")
        return
    
    print(f"\n{'='*70}")
    print(f"Экспорт параметров из документа: {doc_name}")
    print(f"{'='*70}\n")
    
    if len(doc.Objects) == 0:
        print("ВНИМАНИЕ: Документ пуст!")
        return
    
    for i, obj in enumerate(doc.Objects, 1):
        print(f"\n{export_object_parameters(obj)}")
        print("-" * 70)
    
    print(f"\nЭкспортировано {len(doc.Objects)} объектов")
    print(f"\nСовет: Скопируйте нужные параметры в соответствующие скрипты")

def export_all_documents():
    """Экспортирует параметры из всех открытых документов"""
    docs = App.listDocuments()
    if not docs:
        print("ОШИБКА: Нет открытых документов!")
        return
    
    print(f"\nНайдено {len(docs)} документов\n")
    
    for doc_name in docs.keys():
        export_document(doc_name)
        print("\n")

def export_assembly_positions(assembly_doc_name=None):
    """Экспортирует позиции объектов из сборки (для assemble.py)"""
    # Если имя не указано, пытаемся найти документ сборки автоматически
    if assembly_doc_name is None:
        docs = App.listDocuments()
        # Ищем документ с "Assembly" в имени
        for doc_name in docs.keys():
            if 'Assembly' in doc_name or 'assembly' in doc_name.lower():
                assembly_doc_name = doc_name
                print(f"Найден документ сборки: '{assembly_doc_name}'")
                break
        
        # Если не нашли, используем первый доступный или показываем список
        if assembly_doc_name is None:
            if docs:
                print(f"ВНИМАНИЕ: Документ сборки не найден. Доступные документы:")
                for i, doc_name in enumerate(docs.keys(), 1):
                    print(f"  {i}. {doc_name}")
                print(f"\nИспользуйте: export_assembly_positions('имя_документа')")
                return
            else:
                print("ОШИБКА: Нет открытых документов!")
                print("Сначала запустите assemble.py для создания сборки")
                return
    
    try:
        doc = App.getDocument(assembly_doc_name)
    except:
        print(f"ОШИБКА: Документ '{assembly_doc_name}' не найден!")
        docs = App.listDocuments()
        if docs:
            print(f"\nДоступные документы:")
            for doc_name in docs.keys():
                print(f"  • {doc_name}")
            print(f"\nИспользуйте одно из имён выше")
        else:
            print(f"Нет открытых документов. Запустите assemble.py")
        return
    
    print(f"\n{'='*70}")
    print(f"Экспорт позиций из сборки: {assembly_doc_name}")
    print(f"{'='*70}\n")
    
    print("# Словарь позиций для assemble.py:")
    print("positions = {")
    
    for obj in doc.Objects:
        if hasattr(obj, 'Placement'):
            pl = obj.Placement
            pos = pl.Base
            rot = pl.Rotation
            
            # Формируем код для поворота
            if rot.Angle > 0.001:
                rot_code = f"App.Rotation(App.Vector({rot.Axis.x:.6f}, {rot.Axis.y:.6f}, {rot.Axis.z:.6f}), {rot.Angle * 180 / 3.14159:.2f})"
            else:
                rot_code = "App.Rotation()"
            
            print(f"    '{obj.Name}': {{")
            print(f"        'pos': App.Vector({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}),")
            print(f"        'rot': {rot_code},")
            print(f"    }},")
    
    print("}")
    print(f"\nЭкспортировано {len(doc.Objects)} позиций")

def export_parameters_to_file(doc_name, output_file=None):
    """Экспортирует параметры в текстовый файл"""
    import sys
    
    if output_file is None:
        output_file = f"/tmp/{doc_name}_export.txt"
    
    # Перенаправляем вывод в файл
    original_stdout = sys.stdout
    with open(output_file, 'w', encoding='utf-8') as f:
        sys.stdout = f
        export_document(doc_name)
    
    sys.stdout = original_stdout
    print(f"\nПараметры экспортированы в файл: {output_file}")

# Информация о скрипте
print("="*70)
print("Скрипт экспорта параметров из FreeCAD загружен!")
print("="*70)
print("\nДоступные функции:")
print("  • export_document('WatchDog_BasePlate')        - экспорт одного документа")
print("  • export_all_documents()                       - экспорт всех документов")
print("  • export_assembly_positions()                  - экспорт позиций сборки (автопоиск)")
print("  • export_parameters_to_file('WatchDog_BasePlate') - экспорт в файл")
print("\nПример использования:")
print("  export_document('WatchDog_BasePlate')")
print("  export_assembly_positions()  # Автоматически найдёт документ сборки")
print("\nСписок открытых документов:")
docs = App.listDocuments()
if docs:
    for doc_name in docs.keys():
        print(f"  • {doc_name}")
else:
    print("  (нет открытых документов)")
print("="*70)

