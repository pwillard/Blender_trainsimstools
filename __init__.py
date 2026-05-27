bl_info = {
    "name": "TrainSimTools",
    "author": "Pete Willard",
    "version": (1, 3, 10),
    "blender": (4, 3, 0),
    "location": "3D Viewport > N-Panel > TrainSimTools",
    "description": "Utilities for train-sim content: texture filename changer (with batch rename) and collection management tools.",
    "category": "3D View",
}


from .bbox_tools import TST_OT_ExportBoundingBoxCSV
from .collection_tools import (
    OBJECT_OT_CreateInitialCollections,
    OBJECT_OT_SwapCollections,
    SwapCollectionsProperties,
)
from .panels import TXCH_PT_Panel, VIEW3D_PT_SwapCollections, VIEW3D_PT_TrainSimToolsInfo
from .texture_tools import (
    TXCH_OT_InsertMappingLine,
    TXCH_OT_LoadMappingFromFile,
    TXCH_OT_RenameImages,
    TXCH_OT_Run,
    TXCH_Props,
)
from .uv_tools import TST_OT_FixUVSimple

import bpy
from bpy.props import PointerProperty


classes = (
    TXCH_Props,
    TXCH_OT_Run,
    TXCH_OT_RenameImages,
    TXCH_OT_LoadMappingFromFile,
    TXCH_OT_InsertMappingLine,
    TXCH_PT_Panel,
    SwapCollectionsProperties,
    OBJECT_OT_SwapCollections,
    OBJECT_OT_CreateInitialCollections,
    VIEW3D_PT_SwapCollections,
    TST_OT_FixUVSimple,
    VIEW3D_PT_TrainSimToolsInfo,
    TST_OT_ExportBoundingBoxCSV,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.txch = PointerProperty(type=TXCH_Props)
    bpy.types.Scene.swap_collections_props = PointerProperty(type=SwapCollectionsProperties)


def unregister():
    if hasattr(bpy.types.Scene, "txch"):
        del bpy.types.Scene.txch
    if hasattr(bpy.types.Scene, "swap_collections_props"):
        del bpy.types.Scene.swap_collections_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
