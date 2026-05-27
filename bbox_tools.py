import csv
import os

import bpy
from bpy.types import Operator


class TST_OT_ExportBoundingBoxCSV(Operator):
    bl_idname = "tst.export_bbox_csv"
    bl_label = "Export Bounding Box CSV"
    bl_description = (
        "Export bounding box offsets (relative to 3D cursor) for selected "
        "mesh objects to bbox_export.csv. Uses -Y as forward."
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        filepath = os.path.join(output_directory(), "bbox_export.csv")

        try:
            write_bounding_box_csv(filepath, context)
        except PermissionError:
            self.report(
                {"ERROR"},
                f"Permission denied writing to '{filepath}'. "
                "Try a different save location or check folder permissions.",
            )
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to export bounding boxes: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Bounding boxes exported to {filepath}")
        return {"FINISHED"}


def output_directory():
    if bpy.data.filepath:
        return os.path.dirname(bpy.data.filepath)
    return bpy.app.tempdir or os.path.expanduser("~")


def write_bounding_box_csv(filepath, context):
    scene = context.scene
    cursor = scene.cursor.location
    depsgraph = context.evaluated_depsgraph_get()

    with open(filepath, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "object_name",
                "left_x_from_cursor",
                "bottom_z_from_cursor",
                "rear_y_from_cursor",
                "right_x_from_cursor",
                "top_z_from_cursor",
                "front_neg_y_from_cursor",
            ]
        )

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            obj_eval = obj.evaluated_get(depsgraph)
            mesh = obj_eval.to_mesh()
            try:
                if not mesh or not mesh.vertices:
                    continue
                writer.writerow(bounding_box_row(obj, mesh, cursor))
            finally:
                if mesh:
                    obj_eval.to_mesh_clear()


def bounding_box_row(obj, mesh, cursor):
    verts_world = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]

    min_x = min(vertex.x for vertex in verts_world)
    max_x = max(vertex.x for vertex in verts_world)
    min_y = min(vertex.y for vertex in verts_world)
    max_y = max(vertex.y for vertex in verts_world)
    min_z = min(vertex.z for vertex in verts_world)
    max_z = max(vertex.z for vertex in verts_world)

    return [
        obj.name,
        round(min_x - cursor.x, 3),
        round(min_z - cursor.z, 3),
        round(max_y - cursor.y, 3),
        round(max_x - cursor.x, 3),
        round(max_z - cursor.z, 3),
        round(cursor.y - min_y, 3),
    ]
