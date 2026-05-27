import bpy
from bpy.props import EnumProperty
from bpy.types import Operator, PropertyGroup


def collection_items(self, context):
    items = [(coll.name, coll.name, "") for coll in bpy.data.collections]
    return items or [("None", "None", "No collections available")]


class SwapCollectionsProperties(PropertyGroup):
    collection_1: EnumProperty(
        name="Collection 1",
        description="First collection to swap",
        items=collection_items,
    )
    collection_2: EnumProperty(
        name="Collection 2",
        description="Second collection to swap",
        items=collection_items,
    )


class OBJECT_OT_SwapCollections(Operator):
    bl_idname = "object.swap_collections"
    bl_label = "Swap Collection Names"
    bl_description = "Swap the names of two selected collections"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.swap_collections_props
        name1 = props.collection_1
        name2 = props.collection_2

        if name1 == "None" or name2 == "None":
            self.report({"ERROR"}, "No valid collections selected.")
            return {"CANCELLED"}
        if name1 == name2:
            self.report({"ERROR"}, "Cannot swap a collection with itself.")
            return {"CANCELLED"}

        coll1 = bpy.data.collections.get(name1)
        coll2 = bpy.data.collections.get(name2)
        if not coll1 or not coll2:
            self.report({"ERROR"}, "One or both collections not found.")
            return {"CANCELLED"}

        temp_name = f"{coll1.name}_TEMP"
        coll1.name = temp_name
        coll2.name = name1
        coll1.name = name2

        self.report({"INFO"}, f"Swapped '{name1}' and '{name2}' successfully.")
        return {"FINISHED"}


class OBJECT_OT_CreateInitialCollections(Operator):
    bl_idname = "object.create_initial_collections"
    bl_label = "Create Initial Collection Setup"
    bl_description = "Create a default collection structure (MAIN & Scratchpad) at the top level"
    bl_options = {"REGISTER", "UNDO"}

    def create_collection(self, context, name, parent_collection=None):
        scene_root = context.scene.collection
        collection = bpy.data.collections.get(name)
        created = collection is None
        if created:
            collection = bpy.data.collections.new(name)

        target_parent = parent_collection or scene_root
        linked = collection.name not in target_parent.children
        if linked:
            target_parent.children.link(collection)

        return collection, created, linked

    def execute(self, context):
        created = []
        linked = []

        main, was_created, was_linked = self.create_collection(context, "MAIN")
        self._record("MAIN", was_created, was_linked, created, linked)

        for suffix in ("300", "600", "1000", "1500"):
            name = f"MAIN_{suffix}"
            _, was_created, was_linked = self.create_collection(context, name, parent_collection=main)
            self._record(name, was_created, was_linked, created, linked)

        scratchpad, was_created, was_linked = self.create_collection(context, "Scratchpad")
        self._record("Scratchpad", was_created, was_linked, created, linked)

        for suffix in ("300", "600", "1000", "1500"):
            name = f"Scratchpad_{suffix}"
            _, was_created, was_linked = self.create_collection(context, name, parent_collection=scratchpad)
            self._record(name, was_created, was_linked, created, linked)

        if not created and not linked:
            self.report({"INFO"}, "All collections already exist; nothing to do.")
        else:
            messages = []
            if created:
                messages.append(f"Created: {', '.join(created)}")
            if linked:
                messages.append(f"Linked: {', '.join(linked)}")
            self.report({"INFO"}, " | ".join(messages))

        tag_view3d_redraw()
        return {"FINISHED"}

    def _record(self, name, created, linked, created_names, linked_names):
        if created:
            created_names.append(name)
        elif linked:
            linked_names.append(name)


def tag_view3d_redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
