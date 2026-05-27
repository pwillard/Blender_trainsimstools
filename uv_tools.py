import bpy
from bpy.types import Operator


class TST_OT_FixUVSimple(Operator):
    bl_idname = "tst.fix_uv_simple"
    bl_label = "Fix UV Maps (Simple)"
    bl_description = "Ensure every mesh has a UVMap; create and name one if missing."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        fixed = 0
        for mesh in bpy.data.meshes:
            if len(mesh.uv_layers) == 0:
                mesh.uv_layers.new()
            if not mesh.uv_layers.get("UVMap"):
                mesh.uv_layers[0].name = "UVMap"
            fixed += 1

        self.report({"INFO"}, f"Checked {len(bpy.data.meshes)} meshes. Updated: {fixed}.")
        return {"FINISHED"}
