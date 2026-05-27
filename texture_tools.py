import os
import re

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, PropertyGroup


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
    for node in node_tree.nodes:
        if hasattr(node, "image"):
            img = getattr(node, "image", None)
            if img is not None:
                yield node, img


def objects_in_scope(scope):
    if scope == "SELECTED":
        return list(bpy.context.selected_objects or [])
    return list(bpy.data.objects)


def rel_or_abs(path, make_relative=True):
    if not isinstance(path, str) or path == "":
        return ""
    try:
        if make_relative:
            return bpy.path.relpath(path)
        return bpy.path.abspath(path) if path.startswith("//") else path
    except Exception:
        return path or ""


def ext_with_dot(ext):
    if not ext:
        return ""
    return "." + ext.strip().lstrip(".")


def mapping_source_items(self, context):
    items = []
    seen = set()

    for img in bpy.data.images:
        path = img.filepath or img.filepath_raw or ""
        if not isinstance(path, str):
            continue

        key = path if path else img.name
        if key in seen:
            continue
        seen.add(key)

        label = os.path.basename(path) if path else img.name
        items.append((key, label, path if path else img.name))

    return items or [("__NONE__", "<no images found>", "No image filepaths available")]


def build_new_path_from_prefix_suffix(old_path, prefix, suffix, change_ext, base_dir=None):
    dirname = base_dir if base_dir is not None else os.path.dirname(old_path)
    basename = os.path.basename(old_path)
    name, ext = os.path.splitext(basename)
    if change_ext:
        ext = ext_with_dot(change_ext)
    return os.path.join(dirname, f"{prefix}{name}{suffix}{ext}")


def swap_dir(old_path, new_dir, keep_basename, prefix, suffix, change_ext):
    if not isinstance(new_dir, str) or new_dir == "":
        new_dir = "//"
    abs_new_dir = bpy.path.abspath(new_dir) if new_dir.startswith("//") else new_dir
    if not isinstance(old_path, str) or old_path == "":
        return os.path.join(abs_new_dir, "")
    if keep_basename:
        return os.path.join(abs_new_dir, os.path.basename(old_path))
    return build_new_path_from_prefix_suffix(old_path, prefix, suffix, change_ext, base_dir=abs_new_dir)


def search_replace(old_path, search_text, replace_text):
    candidate = old_path.replace(search_text, replace_text)
    try:
        bpy.path.abspath(candidate)
    except Exception:
        pass
    return candidate


def parse_mapping(multiline):
    mapping = {}
    for line in (multiline or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=>" not in stripped:
            continue
        old, new = stripped.split("=>", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def mapping_lookup(old_path, mapping):
    keys_to_try = [old_path]
    try:
        keys_to_try.append(bpy.path.abspath(old_path))
    except Exception:
        pass
    keys_to_try.append(os.path.basename(old_path))

    for key in keys_to_try:
        if key in mapping:
            return mapping[key]
    return None


def can_edit_image(img):
    return img.library is None


def maybe_unpack(img, unpack):
    if img.packed_file and unpack:
        try:
            img.unpack(method="WRITE_LOCAL")
            return True
        except Exception as exc:
            print(f"    ! Unpack failed for '{img.name}': {exc}")
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
        except Exception as exc:
            print(f"    ! Reload failed for '{img.name}': {exc}")


def collect_object_images(scope):
    images = set()
    seen_pairs = set()

    for obj in objects_in_scope(scope):
        for mat in iter_materials_used_by_object(obj):
            if not (mat and mat.use_nodes and mat.node_tree):
                continue
            for node, img in enumerate_image_nodes(mat.node_tree):
                key = (mat.name, node.name, img.name)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                images.add(img)

    return list(images)


class TXCH_Props(PropertyGroup):
    scope: EnumProperty(
        name="Scope",
        description="Which objects to scan",
        items=[("SELECTED", "Selected Objects", ""), ("ALL", "All Objects", "")],
        default="SELECTED",
    )
    strategy: EnumProperty(
        name="Path Strategy",
        items=[
            ("SWAP_DIR", "Swap Directory", "Move to a new folder"),
            ("SEARCH_REPLACE", "Search/Replace", "Replace substring in path"),
            ("MAPPING", "Mapping", "Explicit old=>new mapping"),
            ("PREFIX_SUFFIX", "Prefix/Suffix", "Rename keeping folder"),
        ],
        default="SWAP_DIR",
    )
    dry_run: BoolProperty(name="Dry Run (Paths)", default=True)
    make_relative: BoolProperty(name="Store Relative Paths", default=True)
    unpack_if_packed: BoolProperty(name="Unpack Packed Images", default=False)
    only_if_exists: BoolProperty(name="Only If New File Exists", default=False)
    reload_after: BoolProperty(name="Reload After Change", default=True)

    new_dir: StringProperty(name="New Dir", default="//textures", subtype="DIR_PATH")
    keep_basename: BoolProperty(name="Keep Basename", default=True)

    search_text: StringProperty(name="Search", default="OldTextures")
    replace_text: StringProperty(name="Replace", default="NewTextures")

    mapping_text: StringProperty(
        name="Mapping",
        description="Lines of 'old=>new' (old can be basename, relative //, or absolute)",
        default="",
        subtype="NONE",
    )
    mapping_file: StringProperty(
        name="Mapping File",
        description="Text file with lines: old=>new",
        default="",
        subtype="FILE_PATH",
    )
    mapping_choice: EnumProperty(
        name="Existing Texture",
        description="Pick an existing texture path/name to start a mapping line",
        items=mapping_source_items,
    )

    add_prefix: StringProperty(name="Prefix", default="")
    add_suffix: StringProperty(name="Suffix", default="")
    change_ext: StringProperty(name="Change Ext", default="", description="e.g. jpg; blank to keep")

    rename_enable: BoolProperty(name="Enable Image Datablock Rename", default=False)
    rename_scope: EnumProperty(
        name="Rename Scope",
        description="Which images to rename",
        items=[
            ("USED_IN_SCOPE", "Used by Objects in Scope", "Only rename images used by the chosen Scope"),
            ("ALL_IMAGES", "All Images in File", "Rename all image datablocks"),
        ],
        default="USED_IN_SCOPE",
    )
    rename_strategy: EnumProperty(
        name="Rename Strategy",
        items=[
            ("PREFIX_SUFFIX", "Prefix/Suffix", ""),
            ("SEARCH_REPLACE", "Search/Replace", ""),
            ("MAPPING", "Mapping", ""),
        ],
        default="PREFIX_SUFFIX",
    )
    rn_prefix: StringProperty(name="Name Prefix", default="")
    rn_suffix: StringProperty(name="Name Suffix", default="")
    rn_search: StringProperty(name="Name Search", default="")
    rn_replace: StringProperty(name="Name Replace", default="")
    rn_mapping_text: StringProperty(name="Name Map (old=>new)", default="")
    rn_sanitize: BoolProperty(
        name="Sanitize (A-Z,a-z,0-9,_-)",
        default=True,
        description="Replace invalid chars with '_'",
    )
    rn_make_unique: BoolProperty(
        name="Make Names Unique",
        default=True,
        description="Auto-append .001, .002 on collisions",
    )
    rn_dry_run: BoolProperty(name="Dry Run (Names)", default=True)


class TXCH_OT_Run(Operator):
    bl_idname = "txch.run"
    bl_label = "Apply Texture Filename Changes"
    bl_description = "Change texture image file paths based on selected strategy"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.txch
        target_images = collect_object_images(props.scope)
        if not target_images:
            self.report({"INFO"}, "No image textures found in scope.")
            return {"CANCELLED"}

        mapping = parse_mapping(props.mapping_text) if props.strategy == "MAPPING" else {}
        changed = 0
        skipped = 0

        print("\n=== TrainSimTools: PATHS ===")
        print(f"Scope            : {props.scope}")
        print(f"Strategy         : {props.strategy}")
        print(f"Dry Run          : {props.dry_run}")

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

            new_candidate = self._build_new_path(old, props, mapping)
            if not new_candidate:
                print(f"- SKIP (no map) : '{img.name}' ({old})")
                skipped += 1
                continue

            new_candidate = self._preserve_udim_token(img, old, new_candidate)
            abs_candidate = bpy.path.abspath(new_candidate)
            if props.only_if_exists and not os.path.exists(abs_candidate):
                print(f"- SKIP (missing): '{img.name}' -> {new_candidate}")
                skipped += 1
                continue

            if img.packed_file and not props.unpack_if_packed and not props.dry_run:
                print(f"- SKIP (packed) : '{img.name}' is packed; enable Unpack to change.")
                skipped += 1
                continue

            print(f"+ {'WOULD SET' if props.dry_run else 'SET'}: '{img.name}'")
            print(f"    From: {old}")
            print(f"    To  : {new_candidate}")

            if not props.dry_run:
                if not maybe_unpack(img, props.unpack_if_packed):
                    skipped += 1
                    continue
                apply_new_path(img, new_candidate, props.make_relative, props.reload_after)
            changed += 1

        self.report({"INFO"}, f"Paths {'planned' if props.dry_run else 'applied'}: {changed}, Skipped: {skipped}")
        return {"FINISHED"}

    def _build_new_path(self, old_path, props, mapping):
        if props.strategy == "SWAP_DIR":
            return swap_dir(
                old_path,
                props.new_dir,
                props.keep_basename,
                props.add_prefix,
                props.add_suffix,
                props.change_ext,
            )
        if props.strategy == "SEARCH_REPLACE":
            return search_replace(old_path, props.search_text, props.replace_text)
        if props.strategy == "MAPPING":
            return mapping_lookup(old_path, mapping)
        if props.strategy == "PREFIX_SUFFIX":
            return build_new_path_from_prefix_suffix(old_path, props.add_prefix, props.add_suffix, props.change_ext)
        return None

    def _preserve_udim_token(self, img, old_path, new_path):
        if img.source != "TILED":
            return new_path
        if "<UDIM>" in new_path or "<uvtile>" in new_path:
            return new_path

        for token in ("<UDIM>", "<uvtile>"):
            if token in old_path:
                new_dir = os.path.dirname(new_path)
                new_name, ext = os.path.splitext(os.path.basename(new_path))
                return os.path.join(new_dir, f"{new_name}{token}{ext}")
        return new_path


class TXCH_OT_RenameImages(Operator):
    bl_idname = "txch.rename_images"
    bl_label = "Batch Rename Image Datablocks"
    bl_description = "Rename bpy.data.images (names only; does not touch file paths)"
    bl_options = {"REGISTER", "UNDO"}

    def sanitize(self, name):
        return re.sub(r"[^A-Za-z0-9_\-. ]+", "_", name)

    def unique_name(self, base):
        if base not in bpy.data.images:
            return base

        index = 1
        while True:
            candidate = f"{base}.{index:03d}"
            if candidate not in bpy.data.images:
                return candidate
            index += 1

    def execute(self, context):
        props = context.scene.txch
        targets = list(bpy.data.images) if props.rename_scope == "ALL_IMAGES" else collect_object_images(props.scope)
        if not targets:
            self.report({"INFO"}, "No images to rename.")
            return {"CANCELLED"}

        name_map = parse_mapping(props.rn_mapping_text) if props.rename_strategy == "MAPPING" else {}
        changed = 0
        skipped = 0

        print("\n=== TrainSimTools: NAME RENAME ===")
        print(f"Targets: {len(targets)} | Strategy: {props.rename_strategy} | DryRun: {props.rn_dry_run}")

        for img in targets:
            if not can_edit_image(img):
                print(f"- SKIP (linked) : '{img.name}' from library '{img.library.filepath}'")
                skipped += 1
                continue

            old_name = img.name
            new_name = self._build_new_name(old_name, props, name_map)
            if not new_name:
                skipped += 1
                print(f"- SKIP (no change): '{old_name}'")
                continue

            if props.rn_sanitize:
                new_name = self.sanitize(new_name)
            if props.rn_make_unique:
                new_name = self.unique_name(new_name)

            print(f"+ {'WOULD RENAME' if props.rn_dry_run else 'RENAME'}: '{old_name}' -> '{new_name}'")
            if not props.rn_dry_run:
                try:
                    img.name = new_name
                except Exception as exc:
                    print(f"    ! Rename failed for '{old_name}': {exc}")
                    skipped += 1
                    continue
            changed += 1

        self.report({"INFO"}, f"Names {'planned' if props.rn_dry_run else 'renamed'}: {changed}, Skipped: {skipped}")
        return {"FINISHED"}

    def _build_new_name(self, old_name, props, name_map):
        if props.rename_strategy == "PREFIX_SUFFIX":
            return f"{props.rn_prefix}{old_name}{props.rn_suffix}"
        if props.rename_strategy == "SEARCH_REPLACE" and props.rn_search:
            return old_name.replace(props.rn_search, props.rn_replace)
        if props.rename_strategy == "MAPPING":
            return name_map.get(old_name)
        return None


class TXCH_OT_LoadMappingFromFile(Operator):
    bl_idname = "txch.load_mapping_file"
    bl_label = "Load Mapping From File"
    bl_description = "Load mapping rules from a text file into the Mapping field"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.txch
        if not props.mapping_file:
            self.report({"ERROR"}, "No mapping file specified.")
            return {"CANCELLED"}

        path = bpy.path.abspath(props.mapping_file)
        if not os.path.exists(path):
            self.report({"ERROR"}, f"Mapping file not found: {path}")
            return {"CANCELLED"}

        try:
            with open(path, "r", encoding="utf-8") as mapping_file:
                props.mapping_text = mapping_file.read()
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to read mapping file: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Mapping loaded from {path}")
        return {"FINISHED"}


class TXCH_OT_InsertMappingLine(Operator):
    bl_idname = "txch.insert_mapping_line"
    bl_label = "Insert Mapping Line"
    bl_description = "Insert an 'old => ' line for the selected texture into the mapping"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.txch
        key = props.mapping_choice
        if not key or key == "__NONE__":
            self.report({"ERROR"}, "No valid texture selected in dropdown.")
            return {"CANCELLED"}

        line = f"{key} => "
        props.mapping_text = props.mapping_text.rstrip() + "\n" + line if props.mapping_text.strip() else line
        self.report({"INFO"}, f"Inserted mapping line for: {key}")
        return {"FINISHED"}
