bl_info = {
    "name": "TrainSimTools",
    "author": "Pete Willard",
    "version": (1, 3, 2),
    "blender": (3, 0, 0),
    "location": "3D Viewport > N-Panel > TrainSimTools",
    "description": "Utilities for train-sim content: texture filename changer (with batch rename) and collection management tools.",
    "category": "3D View",
}

import bpy
import os
import re
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, StringProperty, PointerProperty

# =============================
# Helpers (Texture tools)
# =============================

def iter_materials_used_by_object(obj):
    mats = set()
    for slot in getattr(obj.data, "materials", []):
        if slot:
            mats.add(slot)
    for slot in obj.material_slots:
        if slot.material:
            mats.add(slot.material)
    return mats


def enumerate_image_nodes(node_tree):
    for n in node_tree.nodes:
        if hasattr(n, "image"):
            img = getattr(n, "image", None)
            if img is not None:
                yield n, img


def objects_in_scope(scope):
    if scope == 'SELECTED':
        return [o for o in (bpy.context.selected_objects or [])]
    return list(bpy.data.objects)


def rel_or_abs(path, make_relative=True):
    # Be defensive: Blender paths might be None or non-strings from bad props
    if not isinstance(path, str) or path == "":
        return ""
    try:
        if make_relative:
            return bpy.path.relpath(path)
        return bpy.path.abspath(path) if isinstance(path, str) and path.startswith("//") else path
    except Exception:
        return path or ""


def ext_with_dot(ext):
    if not ext:
        return ""
    ext = ext.strip().lstrip(".")
    return "." + ext


def build_new_path_from_prefix_suffix(old_path, prefix, suffix, change_ext, base_dir=None):
    dirname = base_dir if base_dir is not None else os.path.dirname(old_path)
    basename = os.path.basename(old_path)
    name, ext = os.path.splitext(basename)
    if change_ext:
        ext = ext_with_dot(change_ext)
    new_base = f"{prefix}{name}{suffix}{ext}"
    return os.path.join(dirname, new_base)


def swap_dir(old_path, new_dir, keep_basename, prefix, suffix, change_ext):
    if not isinstance(new_dir, str) or new_dir == "":
        new_dir = "//"
    abs_new_dir = bpy.path.abspath(new_dir) if isinstance(new_dir, str) and new_dir.startswith("//") else new_dir
    if not isinstance(old_path, str) or old_path == "":
        return os.path.join(abs_new_dir, "")
    if keep_basename:
        return os.path.join(abs_new_dir, os.path.basename(old_path))
    return build_new_path_from_prefix_suffix(old_path, prefix, suffix, change_ext, base_dir=abs_new_dir)


def search_replace(old_path, search_text, replace_text):
    candidate = old_path.replace(search_text, replace_text)
    try:
        _ = bpy.path.abspath(candidate)
    except Exception:
        pass
    return candidate


def parse_mapping(multiline):
    mp = {}
    for line in (multiline or "").splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if '=>' not in s:
            continue
        old, new = s.split('=>', 1)
        mp[old.strip()] = new.strip()
    return mp


def mapping_lookup(old_path, mapping):
    keys_to_try = [old_path]
    try:
        keys_to_try.append(bpy.path.abspath(old_path))
    except Exception:
        pass
    keys_to_try.append(os.path.basename(old_path))
    for k in keys_to_try:
        if k in mapping:
            return mapping[k]
    return None


def can_edit_image(img):
    return img.library is None


def maybe_unpack(img, unpack):
    if img.packed_file and unpack:
        try:
            img.unpack(method='WRITE_LOCAL')
            return True
        except Exception as e:
            print(f"    ! Unpack failed for '{img.name}': {e}")
            return False
    return True


def apply_new_path(img, new_path, make_relative, reload_after):
    final = rel_or_abs(new_path, make_relative=make_relative)
    try:
        img.filepath = final
    except Exception:
        pass
    try:
        img.filepath_raw = final
    except Exception:
        pass
    if reload_after:
        try:
            img.reload()
        except Exception as e:
            print(f"    ! Reload failed for '{img.name}': {e}")


def collect_object_images(scope):
    images = set()
    seen_pairs = set()
    for obj in objects_in_scope(scope):
        mats = iter_materials_used_by_object(obj)
        for mat in mats:
            if not (mat and mat.use_nodes and mat.node_tree):
                continue
            for node, img in enumerate_image_nodes(mat.node_tree):
                key = (mat.name, node.name, img.name)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                images.add(img)
    return list(images)

# =============================
# Properties (UI state)
# =============================

class TXCH_Props(PropertyGroup):
    # Path change section
    scope: EnumProperty(
        name="Scope",
        description="Which objects to scan",
        items=[('SELECTED', 'Selected Objects', ''), ('ALL', 'All Objects', '')],
        default='SELECTED',
    )

    strategy: EnumProperty(
        name="Path Strategy",
        items=[
            ('SWAP_DIR', 'Swap Directory', 'Move to a new folder'),
            ('SEARCH_REPLACE', 'Search/Replace', 'Replace substring in path'),
            ('MAPPING', 'Mapping', 'Explicit old=>new mapping'),
            ('PREFIX_SUFFIX', 'Prefix/Suffix', 'Rename keeping folder'),
        ],
        default='SWAP_DIR',
    )

    dry_run: BoolProperty(name="Dry Run (Paths)", default=True)
    make_relative: BoolProperty(name="Store Relative Paths", default=True)
    unpack_if_packed: BoolProperty(name="Unpack Packed Images", default=False)
    only_if_exists: BoolProperty(name="Only If New File Exists", default=False)
    reload_after: BoolProperty(name="Reload After Change", default=True)

    # SWAP_DIR
    new_dir: StringProperty(name="New Dir", default="//textures", subtype='DIR_PATH')
    keep_basename: BoolProperty(name="Keep Basename", default=True)

    # SEARCH/REPLACE
    search_text: StringProperty(name="Search", default="OldTextures")
    replace_text: StringProperty(name="Replace", default="NewTextures")

    # MAPPING
    mapping_text: StringProperty(
        name="Mapping",
        description="Lines of 'old=>new' (old can be basename, relative //, or absolute)",
        default="",
        subtype='NONE',
    )

    # PREFIX/SUFFIX
    add_prefix: StringProperty(name="Prefix", default="")
    add_suffix: StringProperty(name="Suffix", default="")
    change_ext: StringProperty(name="Change Ext", default="", description="e.g. jpg; blank to keep")

    # --- Batch rename (datablocks) ---
    rename_enable: BoolProperty(name="Enable Image Datablock Rename", default=False)

    rename_scope: EnumProperty(
        name="Rename Scope",
        description="Which images to rename",
        items=[
            ('USED_IN_SCOPE', 'Used by Objects in Scope', 'Only rename images used by the chosen Scope'),
            ('ALL_IMAGES', 'All Images in File', 'Rename all image datablocks'),
        ],
        default='USED_IN_SCOPE',
    )

    rename_strategy: EnumProperty(
        name="Rename Strategy",
        items=[
            ('PREFIX_SUFFIX', 'Prefix/Suffix', ''),
            ('SEARCH_REPLACE', 'Search/Replace', ''),
            ('MAPPING', 'Mapping', ''),
        ],
        default='PREFIX_SUFFIX',
    )

    rn_prefix: StringProperty(name="Name Prefix", default="")
    rn_suffix: StringProperty(name="Name Suffix", default="")
    rn_search: StringProperty(name="Name Search", default="")
    rn_replace: StringProperty(name="Name Replace", default="")
    rn_mapping_text: StringProperty(name="Name Map (old=>new)", default="")

    rn_sanitize: BoolProperty(
        name="Sanitize (A–Z,a–z,0–9,_-)", default=True,
        description="Replace invalid chars with '_'",
    )
    rn_make_unique: BoolProperty(
        name="Make Names Unique", default=True,
        description="Auto-append .001, .002 on collisions",
    )
    rn_dry_run: BoolProperty(name="Dry Run (Names)", default=True)

# =============================
# Operators (Texture tools)
# =============================

class TXCH_OT_Run(Operator):
    bl_idname = "txch.run"
    bl_label = "Apply Texture Filename Changes"
    bl_description = "Change texture image file paths based on selected strategy"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        p = context.scene.txch

        target_images = collect_object_images(p.scope)
        if not target_images:
            self.report({'INFO'}, "No image textures found in scope.")
            return {'CANCELLED'}

        mapping = parse_mapping(p.mapping_text) if p.strategy == 'MAPPING' else {}

        changed = 0
        skipped = 0

        print("\n=== TrainSimTools: PATHS ===")
        print(f"Scope            : {p.scope}")
        print(f"Strategy         : {p.strategy}")
        print(f"Dry Run          : {p.dry_run}")

        for img in target_images:
            if not can_edit_image(img):
                print(f"- SKIP (linked) : '{img.name}' from library '{img.library.filepath}'")
                skipped += 1
                continue

            old = (img.filepath_raw or img.filepath) if isinstance((img.filepath_raw or img.filepath), str) else ""
            if not isinstance(old, str) or old == "":
                
                print(f"- SKIP (no path): '{img.name}'")
                skipped += 1
                continue

            blender_path = old

            new_candidate = None
            if p.strategy == 'SWAP_DIR':
                new_candidate = swap_dir(
                    blender_path, p.new_dir, p.keep_basename, p.add_prefix, p.add_suffix, p.change_ext
                )
            elif p.strategy == 'SEARCH_REPLACE':
                new_candidate = search_replace(blender_path, p.search_text, p.replace_text)
            elif p.strategy == 'MAPPING':
                new_candidate = mapping_lookup(blender_path, mapping)
            elif p.strategy == 'PREFIX_SUFFIX':
                new_candidate = build_new_path_from_prefix_suffix(
                    blender_path, p.add_prefix, p.add_suffix, p.change_ext
                )

            if not new_candidate:
                print(f"- SKIP (no map) : '{img.name}' ({blender_path})")
                skipped += 1
                continue

            if img.source == 'TILED':
                if ("<UDIM>" not in new_candidate) and ("<uvtile>" not in new_candidate):
                    for tok in ("<UDIM>", "<uvtile>"):
                        if tok in blender_path:
                            new_dir = os.path.dirname(new_candidate)
                            new_bn = os.path.basename(new_candidate)
                            name, ext = os.path.splitext(new_bn)
                            new_bn = f"{name}{tok}{ext}"
                            new_candidate = os.path.join(new_dir, new_bn)
                            break

            abs_candidate = bpy.path.abspath(new_candidate)
            if p.only_if_exists and not os.path.exists(abs_candidate):
                print(f"- SKIP (missing): '{img.name}' -> {new_candidate}")
                skipped += 1
                continue

            if img.packed_file and not p.unpack_if_packed and not p.dry_run:
                print(f"- SKIP (packed) : '{img.name}' is packed; enable Unpack to change.")
                skipped += 1
                continue

            print(f"+ {'WOULD SET' if p.dry_run else 'SET'}: '{img.name}'")
            print(f"    From: {blender_path}")
            print(f"    To  : {new_candidate}")

            if not p.dry_run:
                if not maybe_unpack(img, p.unpack_if_packed):
                    skipped += 1
                    continue
                apply_new_path(img, new_candidate, p.make_relative, p.reload_after)
            changed += 1

        self.report({'INFO'}, f"Paths {'planned' if p.dry_run else 'applied'}: {changed}, Skipped: {skipped}")
        return {'FINISHED'}


class TXCH_OT_RenameImages(Operator):
    bl_idname = "txch.rename_images"
    bl_label = "Batch Rename Image Datablocks"
    bl_description = "Rename bpy.data.images (names only; does not touch file paths)"
    bl_options = {'REGISTER', 'UNDO'}

    def sanitize(self, name):
        return re.sub(r"[^A-Za-z0-9_\-\. ]+", "_", name)

    def unique_name(self, base):
        if base not in bpy.data.images:
            return base
        i = 1
        while True:
            candidate = f"{base}.{i:03d}"
            if candidate not in bpy.data.images:
                return candidate
            i += 1

    def execute(self, context):
        p = context.scene.txch

        if p.rename_scope == 'ALL_IMAGES':
            targets = list(bpy.data.images)
        else:
            targets = collect_object_images(p.scope)

        if not targets:
            self.report({'INFO'}, "No images to rename.")
            return {'CANCELLED'}

        name_map = parse_mapping(p.rn_mapping_text) if p.rename_strategy == 'MAPPING' else {}

        changed = 0
        skipped = 0

        print("\n=== TrainSimTools: NAME RENAME ===")
        print(f"Targets: {len(targets)} | Strategy: {p.rename_strategy} | DryRun: {p.rn_dry_run}")

        for img in targets:
            if not can_edit_image(img):
                print(f"- SKIP (linked) : '{img.name}' from library '{img.library.filepath}'")
                skipped += 1
                continue

            old_name = img.name

            new_name = None
            if p.rename_strategy == 'PREFIX_SUFFIX':
                new_name = f"{p.rn_prefix}{old_name}{p.rn_suffix}"
            elif p.rn_search and p.rename_strategy == 'SEARCH_REPLACE':
                new_name = old_name.replace(p.rn_search, p.rn_replace)
            elif p.rename_strategy == 'MAPPING':
                new_name = name_map.get(old_name)

            if not new_name:
                skipped += 1
                print(f"- SKIP (no change): '{old_name}'")
                continue

            if p.rn_sanitize:
                new_name = self.sanitize(new_name)

            if p.rn_make_unique:
                new_name = self.unique_name(new_name)

            print(f"+ {'WOULD RENAME' if p.rn_dry_run else 'RENAME'}: '{old_name}' -> '{new_name}'")

            if not p.rn_dry_run:
                try:
                    img.name = new_name
                except Exception as e:
                    print(f"    ! Rename failed for '{old_name}': {e}")
                    skipped += 1
                    continue
            changed += 1

        self.report({'INFO'}, f"Names {'planned' if p.rn_dry_run else 'renamed'}: {changed}, Skipped: {skipped}")
        return {'FINISHED'}

# =============================
# Collections tools (merged ORTSCollection features)
# =============================

def _get_collections(self, context):
    items = [(coll.name, coll.name, "") for coll in bpy.data.collections]
    if not items:
        items = [("None", "None", "No collections available")]
    return items


class SwapCollectionsProperties(PropertyGroup):
    collection_1: EnumProperty(
        name="Collection 1",
        description="First collection to swap",
        items=_get_collections,
    )
    collection_2: EnumProperty(
        name="Collection 2",
        description="Second collection to swap",
        items=_get_collections,
    )


class OBJECT_OT_SwapCollections(Operator):
    bl_idname = "object.swap_collections"
    bl_label = "Swap Collection Names"
    bl_description = "Swap the names of two selected collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.swap_collections_props
        name1 = props.collection_1
        name2 = props.collection_2

        if name1 == "None" or name2 == "None":
            self.report({'ERROR'}, "No valid collections selected.")
            return {'CANCELLED'}

        if name1 == name2:
            self.report({'ERROR'}, "Cannot swap a collection with itself!")
            return {'CANCELLED'}

        coll1 = bpy.data.collections.get(name1)
        coll2 = bpy.data.collections.get(name2)

        if not coll1 or not coll2:
            self.report({'ERROR'}, "One or both collections not found.")
            return {'CANCELLED'}

        temp_name = coll1.name + "_TEMP"
        coll1.name = temp_name
        coll2.name = name1
        coll1.name = name2

        self.report({'INFO'}, f"Swapped '{name1}' ? '{name2}' successfully!")
        return {'FINISHED'}


class OBJECT_OT_CreateInitialCollections(Operator):
    bl_idname = "object.create_initial_collections"
    bl_label = "Create Initial Collection Setup"
    bl_description = "Create a default collection structure (MAIN & Scratchpad)"
    bl_options = {'REGISTER', 'UNDO'}

    def create_collection(self, name, parent_collection=None):
        if name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(name)
            if parent_collection:
                parent_collection.children.link(new_collection)
            else:
                bpy.context.scene.collection.children.link(new_collection)
            return new_collection, True
        else:
            return bpy.data.collections[name], False

    def execute(self, context):
        created = []
        linked = []

        main, main_created = self.create_collection("MAIN")
        if main_created:
            created.append("MAIN")

        main_300, c1 = self.create_collection("MAIN_300", parent_collection=main)
        if c1:
            created.append("MAIN_300")
        main_600, c2 = self.create_collection("MAIN_600", parent_collection=main)
        if c2:
            created.append("MAIN_600")
        main_1000, c3 = self.create_collection("MAIN_1000", parent_collection=main)
        if c3:
            created.append("MAIN_1000")
        main_1500, c4 = self.create_collection("MAIN_1500", parent_collection=main)
        if c4:
            created.append("MAIN_1500")

        scratchpad, s_created = self.create_collection("Scratchpad")
        if s_created:
            created.append("Scratchpad")

        for sub in [main_300, main_600, main_1000, main_1500]:
            if not sub:
                continue
            # Blender's bpy_prop_collection uses name-based membership; avoid `sub in children`
            already_child = any(child == sub or child.name == sub.name for child in scratchpad.children)
            if not already_child:
                try:
                    scratchpad.children.link(sub)
                    linked.append(sub.name)
                except Exception:
                    pass

        if not created and not linked:
            self.report({'INFO'}, "All collections already exist — nothing to do.")
        else:
            msg = []
            if created:
                msg.append(f"Created: {', '.join(created)}")
            if linked:
                msg.append(f"Linked to Scratchpad: {', '.join(linked)}")
            self.report({'INFO'}, " | ".join(msg))

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        return {'FINISHED'}


class TXCH_PT_Panel(Panel):
    bl_label = "Texture Filename Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TrainSimTools'

    def draw(self, context):
        layout = self.layout
        p = context.scene.txch

        # Path section
        box = layout.box()
        box.label(text="Path Changes", icon='FILE_FOLDER')
        box.prop(p, "scope")
        box.prop(p, "strategy")

        if p.strategy == 'SWAP_DIR':
            col = box.column(align=True)
            col.prop(p, "new_dir")
            col.prop(p, "keep_basename")
            if not p.keep_basename:
                col.prop(p, "add_prefix")
                col.prop(p, "add_suffix")
                col.prop(p, "change_ext")
        elif p.strategy == 'SEARCH_REPLACE':
            col = box.column(align=True)
            col.prop(p, "search_text")
            col.prop(p, "replace_text")
        elif p.strategy == 'MAPPING':
            col = box.column(align=True)
            col.label(text="Mapping (one per line: old=>new)")
            col.prop(p, "mapping_text")
        elif p.strategy == 'PREFIX_SUFFIX':
            col = box.column(align=True)
            col.prop(p, "add_prefix")
            col.prop(p, "add_suffix")
            col.prop(p, "change_ext")

        col2 = layout.box()
        col2.label(text="Options", icon='PREFERENCES')
        col2.prop(p, "dry_run")
        col2.prop(p, "make_relative")
        col2.prop(p, "unpack_if_packed")
        col2.prop(p, "only_if_exists")
        col2.prop(p, "reload_after")

        layout.operator("txch.run", icon='FILE_REFRESH')

        # Batch rename section
        layout.separator()
        rbox = layout.box()
        rbox.label(text="Batch Rename Image Datablocks", icon='SORTALPHA')
        rbox.prop(p, "rename_enable")
        if p.rename_enable:
            rbox.prop(p, "rename_scope")
            rbox.prop(p, "rename_strategy")
            if p.rename_strategy == 'PREFIX_SUFFIX':
                rcol = rbox.column(align=True)
                rcol.prop(p, "rn_prefix")
                rcol.prop(p, "rn_suffix")
            elif p.rename_strategy == 'SEARCH_REPLACE':
                rcol = rbox.column(align=True)
                rcol.prop(p, "rn_search")
                rcol.prop(p, "rn_replace")
            elif p.rename_strategy == 'MAPPING':
                rcol = rbox.column(align=True)
                rcol.prop(p, "rn_mapping_text")
            rbox.prop(p, "rn_sanitize")
            rbox.prop(p, "rn_make_unique")
            rbox.prop(p, "rn_dry_run")
            rbox.operator("txch.rename_images", icon='SORTALPHA')

        # UV tools (simple)
        layout.separator()
        uvbox = layout.box()
        uvbox.label(text="UV Tools", icon='GROUP_UVS')
        uvbox.operator("tst.fix_uv_simple", icon='UV')



class VIEW3D_PT_SwapCollections(Panel):
    bl_label = "Collection Tools"
    bl_idname = "VIEW3D_PT_swap_collections"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TrainSimTools'

    def draw(self, context):
        layout = self.layout
        props = context.scene.swap_collections_props

        layout.label(text="Initial Setup:")
        layout.operator("object.create_initial_collections", icon='OUTLINER_COLLECTION')

        layout.separator()
        layout.label(text="Swap Collection Names:")
        layout.prop(props, "collection_1")
        layout.prop(props, "collection_2")
        layout.operator("object.swap_collections", icon='ARROW_LEFTRIGHT')


 # =============================
# Simple UV Fix Operator

class TST_OT_FixUVSimple(bpy.types.Operator):
    bl_idname = "tst.fix_uv_simple"
    bl_label = "Fix UV Maps (Simple)"
    bl_description = "Ensure every mesh has a UVMap; create and name one if missing."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fixed = 0
        for mesh in bpy.data.meshes:
            if len(mesh.uv_layers) == 0:
                mesh.uv_layers.new()
            if not mesh.uv_layers.get('UVMap'):
                firstmap = mesh.uv_layers[0]
                firstmap.name = 'UVMap'
            fixed += 1
        self.report({'INFO'}, f"Checked {len(bpy.data.meshes)} meshes. Updated: {fixed}.")
        return {'FINISHED'}



# =============================
# Version Info Panel
# =============================

class VIEW3D_PT_TrainSimToolsInfo(Panel):
    bl_label = "TrainSimTools Info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TrainSimTools'

    def draw(self, context):
        layout = self.layout
        layout.label(text="TrainSimTools v1.3.2")
        layout.label(text="Combined utilities for texture + collections")
        layout.label(text="© Pete Willard")
        layout.operator('wm.url_open', text='Visit Documentation', icon='HELP').url = 'https://github.com/pwillard/trainsimstools'

# =============================
# =============================

classes = (
    # Texture tools
    TXCH_Props,
    TXCH_OT_Run,
    TXCH_OT_RenameImages,
    TXCH_PT_Panel,
    # Collection tools
    SwapCollectionsProperties,
    OBJECT_OT_SwapCollections,
    OBJECT_OT_CreateInitialCollections,
    VIEW3D_PT_SwapCollections,
    # UV simple operator
    TST_OT_FixUVSimple,
    # Info panel
    VIEW3D_PT_TrainSimToolsInfo,
    )


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.txch = PointerProperty(type=TXCH_Props)
    bpy.types.Scene.swap_collections_props = PointerProperty(type=SwapCollectionsProperties)


def unregister():
    # remove scene properties
    if hasattr(bpy.types.Scene, 'txch'):
        del bpy.types.Scene.txch
    if hasattr(bpy.types.Scene, 'swap_collections_props'):
        del bpy.types.Scene.swap_collections_props
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
