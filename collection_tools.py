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
    bl_label = "Swap Collection Contents"
    bl_description = "Swap the direct objects and child collections between two selected collections"
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
        if collection_contains(coll1, coll2) or collection_contains(coll2, coll1):
            self.report({"ERROR"}, "Cannot swap contents between nested collections.")
            return {"CANCELLED"}

        objects1 = list(coll1.objects)
        objects2 = list(coll2.objects)
        children1 = list(coll1.children)
        children2 = list(coll2.children)

        set_direct_objects(coll1, objects2)
        set_direct_objects(coll2, objects1)
        set_direct_children(coll1, children2)
        set_direct_children(coll2, children1)

        self.report(
            {"INFO"},
            f"Swapped contents of '{name1}' and '{name2}' successfully.",
        )
        tag_view3d_redraw()
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


def collection_contains(parent, child):
    for nested in parent.children:
        if nested == child or collection_contains(nested, child):
            return True
    return False


def set_direct_objects(collection, target_objects):
    target_names = {obj.name for obj in target_objects}

    for obj in list(collection.objects):
        if obj.name not in target_names:
            collection.objects.unlink(obj)

    for obj in target_objects:
        if obj.name not in collection.objects:
            collection.objects.link(obj)


def set_direct_children(collection, target_children):
    target_names = {child.name for child in target_children}

    for child in list(collection.children):
        if child.name not in target_names:
            collection.children.unlink(child)

    for child in target_children:
        if child.name not in collection.children:
            collection.children.link(child)
