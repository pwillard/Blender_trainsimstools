from bpy.types import Panel

from .constants import DOC_URL, VERSION_TEXT


class VIEW3D_PT_TrainSimToolsMain(Panel):
    bl_label = "TrainSimTools"
    bl_idname = "VIEW3D_PT_train_sim_tools_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrainSimTools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.operator("object.create_initial_collections", icon="OUTLINER_COLLECTION")
        col.operator("tst.fix_uv_simple", icon="UV")
        col.operator("tst.export_bbox_csv", icon="FILE_TEXT")


class TrainSimToolsPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrainSimTools"
    bl_parent_id = "VIEW3D_PT_train_sim_tools_main"


class TXCH_PT_Panel(TrainSimToolsPanel, Panel):
    bl_label = "Texture Paths"
    bl_idname = "TXCH_PT_texture_paths"

    def draw(self, context):
        layout = self.layout
        props = context.scene.txch

        layout.prop(props, "scope")
        layout.prop(props, "strategy")

        if props.strategy == "SWAP_DIR":
            self.draw_swap_dir_strategy(layout, props)
        elif props.strategy == "SEARCH_REPLACE":
            col = layout.column(align=True)
            col.prop(props, "search_text")
            col.prop(props, "replace_text")
        elif props.strategy == "MAPPING":
            self.draw_mapping_strategy(layout, props)
        elif props.strategy == "PREFIX_SUFFIX":
            self.draw_prefix_suffix_fields(layout, props)

        layout.separator()
        row = layout.row(align=True)
        row.operator("txch.run", icon="FILE_REFRESH")

    def draw_swap_dir_strategy(self, layout, props):
        col = layout.column(align=True)
        col.prop(props, "new_dir")
        col.prop(props, "keep_basename")
        if not props.keep_basename:
            self.draw_prefix_suffix_fields(col, props)

    def draw_mapping_strategy(self, layout, props):
        col = layout.column(align=True)
        col.prop(props, "mapping_choice")
        col.operator("txch.insert_mapping_line", icon="ADD", text="Insert Mapping Line")
        col.separator()
        col.prop(props, "mapping_text")
        col.prop(props, "mapping_file")
        col.operator("txch.load_mapping_file", icon="FILE_FOLDER")

    def draw_prefix_suffix_fields(self, parent, props):
        col = parent.column(align=True)
        col.prop(props, "add_prefix")
        col.prop(props, "add_suffix")
        col.prop(props, "change_ext")


class TXCH_PT_PathOptions(TrainSimToolsPanel, Panel):
    bl_label = "Texture Path Options"
    bl_idname = "TXCH_PT_texture_path_options"
    bl_parent_id = "TXCH_PT_texture_paths"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = context.scene.txch

        col = layout.column(align=True)
        col.prop(props, "dry_run")
        col.prop(props, "make_relative")
        col.prop(props, "unpack_if_packed")
        col.prop(props, "only_if_exists")
        col.prop(props, "reload_after")


class TXCH_PT_RenameImages(TrainSimToolsPanel, Panel):
    bl_label = "Image Names"
    bl_idname = "TXCH_PT_image_names"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = context.scene.txch

        layout.prop(props, "rename_scope")
        layout.prop(props, "rename_strategy")
        if props.rename_strategy == "PREFIX_SUFFIX":
            col = layout.column(align=True)
            col.prop(props, "rn_prefix")
            col.prop(props, "rn_suffix")
        elif props.rename_strategy == "SEARCH_REPLACE":
            col = layout.column(align=True)
            col.prop(props, "rn_search")
            col.prop(props, "rn_replace")
        elif props.rename_strategy == "MAPPING":
            layout.prop(props, "rn_mapping_text")

        layout.separator()
        col = layout.column(align=True)
        col.prop(props, "rn_sanitize")
        col.prop(props, "rn_make_unique")
        col.prop(props, "rn_dry_run")
        layout.operator("txch.rename_images", icon="SORTALPHA")


class VIEW3D_PT_SwapCollections(TrainSimToolsPanel, Panel):
    bl_label = "Collections"
    bl_idname = "VIEW3D_PT_swap_collections"

    def draw(self, context):
        layout = self.layout
        props = context.scene.swap_collections_props

        layout.operator("object.create_initial_collections", icon="OUTLINER_COLLECTION")
        layout.separator()
        layout.prop(props, "collection_1")
        layout.prop(props, "collection_2")
        layout.operator("object.swap_collections", icon="ARROW_LEFTRIGHT", text="Swap Contents")


class VIEW3D_PT_UVTools(TrainSimToolsPanel, Panel):
    bl_label = "UV"
    bl_idname = "VIEW3D_PT_train_sim_tools_uv"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        self.layout.operator("tst.fix_uv_simple", icon="UV")


class VIEW3D_PT_BoundingBoxTools(TrainSimToolsPanel, Panel):
    bl_label = "Bounding Boxes"
    bl_idname = "VIEW3D_PT_train_sim_tools_bounding_boxes"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Exports bbox_export.csv beside the blend file.")
        layout.operator("tst.export_bbox_csv", icon="FILE_TEXT")


class VIEW3D_PT_TrainSimToolsInfo(TrainSimToolsPanel, Panel):
    bl_label = "Info"
    bl_idname = "VIEW3D_PT_train_sim_tools_info"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"TrainSimTools v{VERSION_TEXT}")
        layout.label(text="Texture, collection, UV, and bbox utilities")
        layout.label(text="(c) Pete Willard")
        layout.operator("wm.url_open", text="Visit Documentation", icon="HELP").url = DOC_URL
