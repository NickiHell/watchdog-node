#!/usr/bin/env blender --python
"""Экстрактор данных из Blender-модели для контекста AI-ассистента.

Извлекает из .blend файла всю структурную информацию:
объекты, размеры, позиции, иерархию, материалы —
и сохраняет в JSON + читаемый текстовый отчёт.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Использование:
  Из командной строки (headless):
    blender --background your_model.blend --python extract_model_data.py

  Из редактора скриптов Blender (Script Editor → Run Script):
    Открыть файл → Run Script

  Вывод:
    cad_models/export/model_data.json
    cad_models/export/model_report.txt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import json
import math

try:
    import bpy
    from mathutils import Vector
except ImportError:
    print("Запускать через Blender: blender --background model.blend --python extract_model_data.py")
    sys.exit(1)


# ─── Вспомогательные функции ───────────────────────────────────────────────


def v3_mm(vec):
    """Вектор метры → словарь мм, округлённый до 0.1."""
    return {
        "x": round(vec.x * 1000, 1),
        "y": round(vec.y * 1000, 1),
        "z": round(vec.z * 1000, 1),
    }


def v3_deg(euler):
    """Euler радианы → словарь градусов."""
    return {
        "x": round(math.degrees(euler.x), 2),
        "y": round(math.degrees(euler.y), 2),
        "z": round(math.degrees(euler.z), 2),
    }


def get_world_bbox(obj):
    """Возвращает min/max мировых координат (мм) и размеры объекта."""
    if obj.type != "MESH" or not obj.data.vertices:
        return None
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return {
        "min_mm": {"x": round(min(xs) * 1000, 1), "y": round(min(ys) * 1000, 1), "z": round(min(zs) * 1000, 1)},
        "max_mm": {"x": round(max(xs) * 1000, 1), "y": round(max(ys) * 1000, 1), "z": round(max(zs) * 1000, 1)},
        "size_mm": {
            "x": round((max(xs) - min(xs)) * 1000, 1),
            "y": round((max(ys) - min(ys)) * 1000, 1),
            "z": round((max(zs) - min(zs)) * 1000, 1),
        },
    }


def get_material_info(obj):
    """Информация о материалах объекта."""
    mats = []
    for slot in obj.material_slots:
        m = slot.material
        if not m:
            continue
        info = {"name": m.name}
        if m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                c = bsdf.inputs["Base Color"].default_value
                info["color_rgba"] = [round(c[0], 3), round(c[1], 3), round(c[2], 3), round(c[3], 3)]
                info["metallic"] = round(bsdf.inputs["Metallic"].default_value, 3)
                info["roughness"] = round(bsdf.inputs["Roughness"].default_value, 3)
                alpha_inp = bsdf.inputs.get("Alpha")
                if alpha_inp:
                    info["alpha"] = round(alpha_inp.default_value, 3)
        mats.append(info)
    return mats


def collection_path(obj):
    """Возвращает путь коллекций объекта типа 'Root/Sub/...'"""
    paths = []
    for col in bpy.data.collections:
        if obj.name in col.objects:
            paths.append(col.name)
    return paths


def get_all_collections_tree():
    """Строит дерево коллекций {name: [children_names]}."""
    tree = {}
    for col in bpy.data.collections:
        tree[col.name] = [c.name for c in col.children]
    return tree


def scene_bounding_box(objects):
    """Общий ограничивающий параллелепипед сцены (мм)."""
    all_x, all_y, all_z = [], [], []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for c in obj.bound_box:
            wc = obj.matrix_world @ Vector(c)
            all_x.append(wc.x)
            all_y.append(wc.y)
            all_z.append(wc.z)
    if not all_x:
        return None
    return {
        "min_mm": {
            "x": round(min(all_x) * 1000, 1),
            "y": round(min(all_y) * 1000, 1),
            "z": round(min(all_z) * 1000, 1),
        },
        "max_mm": {
            "x": round(max(all_x) * 1000, 1),
            "y": round(max(all_y) * 1000, 1),
            "z": round(max(all_z) * 1000, 1),
        },
        "size_mm": {
            "x": round((max(all_x) - min(all_x)) * 1000, 1),
            "y": round((max(all_y) - min(all_y)) * 1000, 1),
            "z": round((max(all_z) - min(all_z)) * 1000, 1),
        },
    }


# ─── Основная функция ──────────────────────────────────────────────────────


def extract():
    scene = bpy.context.scene
    all_objects = list(scene.objects)
    meshes = [o for o in all_objects if o.type == "MESH"]
    empties = [o for o in all_objects if o.type == "EMPTY"]
    cameras = [o for o in all_objects if o.type == "CAMERA"]
    lights = [o for o in all_objects if o.type == "LIGHT"]

    objects_data = []
    for obj in sorted(all_objects, key=lambda o: o.name):
        entry = {
            "name": obj.name,
            "type": obj.type,
            "collections": collection_path(obj),
            "parent": obj.parent.name if obj.parent else None,
            "location_mm": v3_mm(obj.location),
            "rotation_deg": v3_deg(obj.rotation_euler),
            "scale": {
                "x": round(obj.scale.x, 4),
                "y": round(obj.scale.y, 4),
                "z": round(obj.scale.z, 4),
            },
        }

        if obj.type == "MESH":
            bbox = get_world_bbox(obj)
            entry["world_bbox"] = bbox
            entry["dimensions_mm"] = v3_mm(obj.dimensions)
            entry["vertex_count"] = len(obj.data.vertices)
            entry["face_count"] = len(obj.data.polygons)
            entry["materials"] = get_material_info(obj)

        elif obj.type == "LIGHT":
            entry["light_type"] = obj.data.type
            entry["light_energy"] = round(obj.data.energy, 2)

        objects_data.append(entry)

    # Сводка по группам объектов (ищем по ключевым словам в имени)
    def find_objs(keywords):
        kw = [k.lower() for k in keywords]
        return [o["name"] for o in objects_data if any(k in o["name"].lower() for k in kw)]

    data = {
        "meta": {
            "blend_file": bpy.data.filepath or "<не сохранён>",
            "scene_name": scene.name,
            "total_objects": len(all_objects),
            "mesh_count": len(meshes),
            "empty_count": len(empties),
            "camera_count": len(cameras),
            "light_count": len(lights),
        },
        "scene_bounding_box": scene_bounding_box(meshes),
        "collections_tree": get_all_collections_tree(),
        "object_groups": {
            "arms": find_objs(["arm", "tube", "hinge", "fold"]),
            "motors": find_objs(["motor", "bell", "stator", "shaft"]),
            "propellers": find_objs(["prop", "propeller"]),
            "legs": find_objs(["leg", "landing"]),
            "body": find_objs(["plate", "body", "standoff", "frame"]),
            "lidar": find_objs(["lidar", "rplidar", "laser"]),
            "gps": find_objs(["gps", "antenna"]),
            "gimbal": find_objs(["gimbal", "siyi", "lens", "camera"]),
            "battery": find_objs(["battery", "batt", "lipo"]),
            "electronics": find_objs(["rpi", "raspberry", "pixhawk", "elrs", "vtx"]),
        },
        "objects": objects_data,
    }

    return data


def generate_text_report(data):
    """Читаемый текстовый отчёт для AI-контекста."""
    lines = []
    m = data["meta"]

    lines += [
        "=" * 60,
        "  WATCHDOG DRONE — Blender Model Report",
        f"  Файл: {m['blend_file']}",
        f"  Сцена: {m['scene_name']}",
        "=" * 60,
        "",
        f"Объектов всего: {m['total_objects']} (меши: {m['mesh_count']}, "
        f"пусто: {m['empty_count']}, камер: {m['camera_count']}, "
        f"огней: {m['light_count']})",
        "",
    ]

    bbox = data.get("scene_bounding_box")
    if bbox:
        s = bbox["size_mm"]
        mn = bbox["min_mm"]
        mx = bbox["max_mm"]
        lines += [
            "ГАБАРИТЫ МОДЕЛИ (world bounding box):",
            f"  X: {mn['x']} → {mx['x']} мм  ({s['x']} мм)",
            f"  Y: {mn['y']} → {mx['y']} мм  ({s['y']} мм)",
            f"  Z: {mn['z']} → {mx['z']} мм  ({s['z']} мм)",
            "",
        ]

    lines.append("ИЕРАРХИЯ КОЛЛЕКЦИЙ:")
    tree = data.get("collections_tree", {})
    for col, children in tree.items():
        lines.append(f"  {col}/")
        for ch in children:
            lines.append(f"    {ch}/")
    lines.append("")

    lines.append("ГРУППЫ ОБЪЕКТОВ (по имени):")
    for group, names in data.get("object_groups", {}).items():
        if names:
            lines.append(f"  {group:12s}: {', '.join(names)}")
    lines.append("")

    lines.append("─" * 60)
    lines.append("ОБЪЕКТЫ (Mesh) — позиция, размеры, материал:")
    lines.append("─" * 60)

    for obj in data["objects"]:
        if obj["type"] != "MESH":
            continue
        loc = obj["location_mm"]
        dim = obj.get("dimensions_mm", {})
        rot = obj["rotation_deg"]
        lines.append(f"\n[{obj['name']}]")
        col_str = "/".join(obj["collections"]) if obj["collections"] else "—"
        lines.append(f"  Коллекции : {col_str}")
        if obj["parent"]:
            lines.append(f"  Родитель  : {obj['parent']}")
        lines.append(f"  Позиция   : X={loc['x']:8.1f}  Y={loc['y']:8.1f}  Z={loc['z']:8.1f}  мм")
        lines.append(f"  Размеры   : X={dim.get('x', 0):8.1f}  Y={dim.get('y', 0):8.1f}  Z={dim.get('z', 0):8.1f}  мм")
        rot_nonzero = any(abs(v) > 0.01 for v in [rot["x"], rot["y"], rot["z"]])
        if rot_nonzero:
            lines.append(f"  Поворот°  : X={rot['x']:7.2f}  Y={rot['y']:7.2f}  Z={rot['z']:7.2f}")
        bbox = obj.get("world_bbox")
        if bbox:
            mn, mx_ = bbox["min_mm"], bbox["max_mm"]
            lines.append(f"  World min : X={mn['x']:8.1f}  Y={mn['y']:8.1f}  Z={mn['z']:8.1f}  мм")
            lines.append(f"  World max : X={mx_['x']:8.1f}  Y={mx_['y']:8.1f}  Z={mx_['z']:8.1f}  мм")
        lines.append(f"  Поли/Верт : {obj.get('face_count', 0)} / {obj.get('vertex_count', 0)}")
        mats = obj.get("materials", [])
        for mat in mats:
            c = mat.get("color_rgba", [0, 0, 0, 1])
            lines.append(
                f"  Материал  : {mat['name']}  "
                f"RGB({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})  "
                f"metal={mat.get('metallic', 0):.2f}  "
                f"rough={mat.get('roughness', 0):.2f}"
                + (f"  alpha={mat.get('alpha', 1):.2f}" if mat.get("alpha", 1) < 1.0 else "")
            )

    return "\n".join(lines)


# ─── Запуск ────────────────────────────────────────────────────────────────


def main():
    print("\n  Watchdog: извлечение данных из Blender-модели...\n")

    data = extract()
    report = generate_text_report(data)

    # Отчёты сохраняются в export/ рядом со скриптом
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(script_dir, "export")
    os.makedirs(out_dir, exist_ok=True)

    # Имя отчёта берём из имени blend-файла (если открыт)
    blend_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0] if bpy.data.filepath else "model"
    json_path = os.path.join(out_dir, f"{blend_name}_data.json")
    report_path = os.path.join(out_dir, f"{blend_name}_report.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print("\n  Данные сохранены:")
    print(f"    JSON   → {json_path}")
    print(f"    Отчёт  → {report_path}")
    print()
    print(f"  Скопируй содержимое {os.path.basename(report_path)} в чат с AI для полного контекста.")


if __name__ == "__main__":
    main()
