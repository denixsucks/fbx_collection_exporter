bl_info = {
    "name": "FBX Collection Exporter",
    "author": "denixsucks",
    "version": (1, 0, 0),
    "blender": (4, 5, 3),
    "location": "Properties > Scene",
    "description": "Batch exports collections into FBX files",
    "category": "Interface",
}

import bpy    # type: ignore
import os

# ------------------------------------------------------------------------
#  SETTINGS
# ------------------------------------------------------------------------
EXPORT_ROOT_NAME = "Export"
EXPORT_SUBSTANCE_FOLDER_NAME = "SUBSTANCE_FBX"
EXPORT_FOLDER_NAME = "FBX"

# ------------------------------------------------------------------------
#  HELPERS
# ------------------------------------------------------------------------
def apply_modifiers_and_transforms(obj, apply_modifiers=True, apply_transforms=True):
    """Apply all modifiers and/or transforms."""
    bpy.context.view_layer.objects.active = obj

    if apply_modifiers:
        for mod in obj.modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                print(f"Could not apply modifier {mod.name} on {obj.name}: {e}")

    if apply_transforms:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def find_collection_recursive(root_coll, found=None):
    """Recursively collect all subcollections."""
    if found is None:
        found = []
    found.append(root_coll)
    for child in root_coll.children:
        find_collection_recursive(child, found)
    return found

def export_collections(context):
    scene = context.scene

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    export_root = bpy.data.collections.get(EXPORT_ROOT_NAME)
    if not export_root:
        context.window_manager.popup_menu(lambda self, ctx: self.layout.label(text=f"Collection '{EXPORT_ROOT_NAME}' not found."), title="Error", icon='ERROR')
        return {'CANCELLED'}

    blend_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    parts = blend_name.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        blend_name = parts[0]

    base_path = os.path.join(os.path.dirname(bpy.data.filepath), EXPORT_SUBSTANCE_FOLDER_NAME if scene.export_for_substance_painter else EXPORT_FOLDER_NAME)
    os.makedirs(base_path, exist_ok=True)

    all_collections = find_collection_recursive(export_root)
    exported_count = 0

    for coll in all_collections:
        mesh_objects = [obj for obj in coll.objects if obj.type == 'MESH']
        if not mesh_objects:
            continue

        bpy.ops.object.select_all(action='DESELECT')
        for obj in mesh_objects:
            obj.select_set(True)
        bpy.ops.object.duplicate()
        duplicates = [obj for obj in bpy.context.selected_objects]

        for obj in duplicates:
            apply_modifiers_and_transforms(obj, apply_modifiers=scene.apply_modifiers, apply_transforms=scene.apply_transforms)

        if not scene.export_for_substance_painter and len(duplicates) > 1:
            bpy.context.view_layer.objects.active = duplicates[0]
            bpy.ops.object.join()
            export_obj = bpy.context.view_layer.objects.active
            obj = export_obj
            mesh = obj.data
            mesh.name = obj.name
        else:
            export_obj = duplicates

        if isinstance(export_obj, (list, tuple)):
            export_objs = export_obj
        else:
            export_objs = [export_obj]

        bpy.ops.object.select_all(action='DESELECT')
        for obj in export_objs:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = export_objs[0]

        fbx_name = f"{blend_name}_{coll.name}.fbx"
        fbx_path = os.path.join(base_path, fbx_name)

        bpy.ops.export_scene.fbx(
            filepath=fbx_path,
            use_selection=True,
            apply_unit_scale=True,
            bake_space_transform=True,
            mesh_smooth_type='FACE',
            use_triangles=scene.triangulate,
            add_leaf_bones=False
        )

        bpy.ops.object.delete()
        exported_count += 1
        print(f"Exported: {fbx_path}")

    print("All collections exported!")
    context.window_manager.popup_menu(lambda self, ctx: self.layout.label(text=f"Export finished! {exported_count} collections exported."),title="FBX Export Complete",icon='CHECKMARK')
    return {'FINISHED'}

# ------------------------------------------------------------------------
#  PROPERTIES
# ------------------------------------------------------------------------
def register_properties():
    bpy.types.Scene.triangulate = bpy.props.BoolProperty(
        name="Triangulate",
        description="Triangulate meshes before export",
        default=True
    )
    bpy.types.Scene.apply_modifiers = bpy.props.BoolProperty(
        name="Apply Modifiers",
        description="Apply all object modifiers before export",
        default=True
    )
    bpy.types.Scene.apply_transforms = bpy.props.BoolProperty(
        name="Apply Transforms",
        description="Apply location, rotation, and scale before export",
        default=True
    )
    bpy.types.Scene.export_for_substance_painter = bpy.props.BoolProperty(
        name="Export for Substance Painter",
        description="Disable mesh joining for Substance Painter workflow",
        default=False
    )


def unregister_properties():
    del bpy.types.Scene.triangulate
    del bpy.types.Scene.apply_modifiers
    del bpy.types.Scene.apply_transforms
    del bpy.types.Scene.export_for_substance_painter


# ------------------------------------------------------------------------
#  PANELS
# ------------------------------------------------------------------------
class ADDON_PT_Panel(bpy.types.Panel):
    bl_label = "FBX Collection Exporter"
    bl_idname = "ADDON_PT_fbx_exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_category = "Addon"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        export_exists = "Export" in bpy.data.collections
        row = layout.row()
        row.enabled = not export_exists
        row.operator("addon.create_export_collection", icon='OUTLINER_COLLECTION')

        layout.separator()
        layout.label(text="Export Settings:")
        layout.prop(scene, "triangulate")
        layout.prop(scene, "apply_modifiers")
        layout.prop(scene, "apply_transforms")
        layout.prop(scene, "export_for_substance_painter")
        layout.separator()
        layout.operator("addon.collection_export", icon='EXPORT')


# ------------------------------------------------------------------------
#  OPERATORS
# ------------------------------------------------------------------------
class ADDON_OT_CreateExportCollection(bpy.types.Operator):
    bl_idname = "addon.create_export_collection"
    bl_label = "Create Export Collection"
    bl_description = "Create a collection named 'Export' in the scene"

    def execute(self, context):
        if "Export" not in bpy.data.collections:
            new_coll = bpy.data.collections.new("Export")
            context.scene.collection.children.link(new_coll)
            self.report({'INFO'}, "Export collection created")
        else:
            self.report({'WARNING'}, "Export collection already exists")
        return {'FINISHED'}

class ADDON_OT_CollectionExport(bpy.types.Operator):
    bl_idname = "addon.collection_export"
    bl_label = "Export FBX Collections"
    bl_description = "Export all subcollections of the 'Export' collection as FBX files"

    def execute(self, context):
        return export_collections(context)

# ------------------------------------------------------------------------
#  REGISTRATION
# ------------------------------------------------------------------------
classes = (
    ADDON_PT_Panel,
    ADDON_OT_CollectionExport,
    ADDON_OT_CreateExportCollection
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_properties()

# run in script editor
if __name__ == "__main__":
    register()
