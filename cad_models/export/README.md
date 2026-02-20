# Export Directory

Эта директория содержит экспортированные 3D-модели рамы квадрокоптера.

## Генерация файлов

Для генерации моделей запустите:

```bash
cd ..
blender --background --python blender_frame.py
```

Или с GUI:

```bash
cd ..
blender --python blender_frame.py
```

## Файлы после генерации

- `drone_frame.blend` - Blender файл (можно редактировать)
- `drone_frame.stl` - Для 3D-печати
- `drone_frame.obj` - Универсальный формат (импорт в CAD/CAM)

## Формат STL

STL (.stl) - стандартный формат для 3D-печати.

Можно использовать в:
- Cura
- PrusaSlicer
- Simplify3D
- И других слайсерах

## Формат OBJ

OBJ (.obj) - универсальный 3D формат.

Можно импортировать в:
- Fusion 360
- SolidWorks
- FreeCAD
- Rhino
- Maya/3ds Max
- И другие CAD/3D программы

## Открыть в Blender

Сначала сгенерируйте модель:

```bash
cd ..
blender --background --python blender_frame.py
```

Затем откройте результат:

```bash
blender drone_frame.blend
```

Или напрямую из корневой директории проекта:

```bash
blender cad_models/export/drone_frame.blend
```

## Экспорт в другие форматы

Откройте модель в Blender и используйте File → Export:

- **STL** - для 3D-печати (уже создан)
- **FBX** - для Unity/Unreal Engine
- **glTF** - для веб-визуализации
- **X3D** - для веб 3D
- **Collada (DAE)** - для игровых движков
- **SVG** - для 2D чертежей (проекции)

## Примечание

Файлы в этой директории генерируются автоматически и не коммитятся в git.
