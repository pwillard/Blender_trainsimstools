from bpy.types import Panel

from .constants import DOC_URL, VERSION_TEXT


class TXCH_PT_Panel(Panel):
    bl_label = "Texture Filename Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrainSimTools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.txch

        self.draw_path_tools(layout, props)
        self.draw_rename_tools(layout, props)
        self.draw_uv_tools(layout)
        self.draw_bounding_box_tools(layout)

    def draw_path_tools(self, layout, props):
        box = layout.box()
        box.label(text="Path Changes", icon="FILE_FOLDER")
        box.prop(props, "scope")
        box.prop(props, "strategy")

        if props.strategy == "SWAP_DIR":
            self.draw_swap_dir_strategy(box, props)
        elif props.strategy == "SEARCH_REPLACE":
            col = box.column(align=True)
            col.prop(props, "search_text")
            col.prop(props, "replace_text")
        elif props.strategy == "MAPPING":
            self.draw_mapping_strategy(box, props)
        elif props.strategy == "PREFIX_SUFFIX":
            self.draw_prefix_suffix_fields(box, props)

        options = layout.box()
        options.label(text="Options", icon="PREFERENCES")
        options.prop(props, "dry_run")
        options.prop(props, "make_relative")
        options.prop(props, "unpack_if_packed")
        options.prop(props, "only_if_exists")
        options.prop(props, "reload_after")

        layout.operator("txch.run", icon="FILE_REFRESH")

    def draw_swap_dir_strategy(self, box, props):
        col = box.column(align=True)
        col.prop(props, "new_dir")
        col.prop(props, "keep_basename")
        if not props.keep_basename:
            self.draw_prefix_suffix_fields(col, props)

    def draw_mapping_strategy(self, box, props):
        col = box.column(align=True)
        col.label(text="Pick existing texture for 'old' side:")
        col.prop(props, "mapping_choice")
        col.operator("txch.insert_mapping_line", icon="ADD", text="Insert as mapping line")
        col.separator()
        col.label(text="Mapping (one per line: old=>new)")
        col.prop(props, "mapping_text")
        col.prop(props, "mapping_file")
        col.operator("txch.load_mapping_file", icon="FILE_FOLDER")

    def draw_prefix_suffix_fields(self, parent, props):
        col = parent.column(align=True)
        col.prop(props, "add_prefix")
        col.prop(props, "add_suffix")
        col.prop(props, "change_ext")

    def draw_rename_tools(self, layout, props):
        layout.separator()
        box = layout.box()
        box.label(text="Batch Rename Image Datablocks", icon="SORTALPHA")
        box.prop(props, "rename_enable")
        if not props.rename_enable:
            return

        box.prop(props, "rename_scope")
        box.prop(props, "rename_strategy")
        if props.rename_strategy == "PREFIX_SUFFIX":
            col = box.column(align=True)
            col.prop(props, "rn_prefix")
            col.prop(props, "rn_suffix")
        elif props.rename_strategy == "SEARCH_REPLACE":
            col = box.column(align=True)
            col.prop(props, "rn_search")
            col.prop(props, "rn_replace")
        elif props.rename_strategy == "MAPPING":
            box.prop(props, "rn_mapping_text")

        box.prop(props, "rn_sanitize")
        box.prop(props, "rn_make_unique")
        box.prop(props, "rn_dry_run")
        box.operator("txch.rename_images", icon="SORTALPHA")

    def draw_uv_tools(self, layout):
        layout.separator()
        box = layout.box()
        box.label(text="UV Tools", icon="GROUP_UVS")
        box.operator("tst.fix_uv_simple", icon="UV")

    def draw_bounding_box_tools(self, layout):
        box = layout.box()
        box.label(text="Bounding Box Tools", icon="MESH_CUBE")
        box.label(text="Exports bbox_export.csv (3D Cursor origin, -Y forward).")
        box.operator("tst.export_bbox_csv", icon="FILE_TEXT")


class VIEW3D_PT_SwapCollections(Panel):
    bl_label = "Collection Tools"
    bl_idname = "VIEW3D_PT_swap_collections"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrainSimTools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.swap_collections_props

        layout.label(text="Initial Setup:")
        layout.operator("object.create_initial_collections", icon="OUTLINER_COLLECTION")
        layout.separator()
        layout.label(text="Swap Collection Names:")
        layout.prop(props, "collection_1")
        layout.prop(props, "collection_2")
        layout.operator("object.swap_collections", icon="ARROW_LEFTRIGHT")


class VIEW3D_PT_TrainSimToolsInfo(Panel):
    bl_label = "TrainSimTools Info"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrainSimTools"

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"TrainSimTools v{VERSION_TEXT}")
        layout.label(text="Combined utilities for texture + collections")
        layout.label(text="(c) Pete Willard")
        layout.operator("wm.url_open", text="Visit Documentation", icon="HELP").url = DOC_URL
