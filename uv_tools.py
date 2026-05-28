import bpy
from bpy.types import Operator


class TST_OT_FixUVSimple(Operator):
    bl_idname = "tst.fix_uv_simple"
    bl_label = "Fix UV Maps (Simple)"
    bl_description = "Ensure selected meshes have a UVMap; falls back to all meshes if no meshes are selected."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meshes = target_meshes(context)
        fixed = 0
        for mesh in meshes:
            if mesh.library is not None:
                continue
            if len(mesh.uv_layers) == 0:
                mesh.uv_layers.new()
            if not mesh.uv_layers.get("UVMap"):
                mesh.uv_layers[0].name = "UVMap"
            fixed += 1

        self.report({"INFO"}, f"Checked {len(meshes)} meshes. Updated: {fixed}.")
        return {"FINISHED"}


def target_meshes(context):
    selected_meshes = []
    seen = set()

    for obj in context.selected_objects:
        if obj.type != "MESH" or obj.data is None:
            continue
        if obj.data.name in seen:
            continue
        selected_meshes.append(obj.data)
        seen.add(obj.data.name)

    return selected_meshes or list(bpy.data.meshes)
