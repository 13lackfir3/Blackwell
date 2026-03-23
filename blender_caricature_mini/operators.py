"""
Blender operators for the Caricature Mini Creator.
"""

import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from .mesh_generator import build_caricature_mini_v2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COLLECTION_NAME = "Caricature Minis"


def _get_or_create_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _link_object(obj, collection):
    if obj.name not in collection.objects:
        collection.objects.link(obj)


def _remove_old_mini(context):
    """Delete any previously generated mini objects tagged with caricature_mini."""
    col = bpy.data.collections.get(_COLLECTION_NAME)
    if col is None:
        return
    to_remove = [o for o in col.objects if o.get("caricature_mini")]
    for obj in to_remove:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(mesh, bpy.types.Mesh) and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def _add_subdivision(obj, levels=1):
    mod = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = levels + 1


def _add_smooth_shade(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


# ---------------------------------------------------------------------------
# Create / Rebuild Mini
# ---------------------------------------------------------------------------

class CARICATURE_OT_CreateMini(Operator):
    bl_idname = "caricature.create_mini"
    bl_label = "Create Mini"
    bl_description = "Generate a new caricature miniature from current settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.caricature_mini
        _remove_old_mini(context)

        obj = build_caricature_mini_v2(props.body, props.gear)
        obj["caricature_mini"] = True
        obj.name = props.character_name or "CaricatureMini"

        col = _get_or_create_collection(_COLLECTION_NAME)
        _link_object(obj, col)

        _add_subdivision(obj, levels=1)
        _add_smooth_shade(obj)

        # Select and make active
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({"INFO"}, f"Mini '{obj.name}' created.")
        return {"FINISHED"}


class CARICATURE_OT_RebuildMini(Operator):
    bl_idname = "caricature.rebuild_mini"
    bl_label = "Rebuild Mini"
    bl_description = "Regenerate the mini with updated settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Reuse the create operator
        return bpy.ops.caricature.create_mini("EXEC_DEFAULT")


# ---------------------------------------------------------------------------
# Clear Mini
# ---------------------------------------------------------------------------

class CARICATURE_OT_ClearMini(Operator):
    bl_idname = "caricature.clear_mini"
    bl_label = "Clear Mini"
    bl_description = "Remove the generated miniature from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        _remove_old_mini(context)
        self.report({"INFO"}, "Caricature mini removed.")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Apply Preset
# ---------------------------------------------------------------------------

class CARICATURE_OT_ApplyPreset(Operator):
    bl_idname = "caricature.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply a character archetype preset"
    bl_options = {"REGISTER", "UNDO"}

    preset_id: StringProperty(name="Preset ID", default="fighter")

    def execute(self, context):
        from .presets import PRESETS
        data = PRESETS.get(self.preset_id)
        if data is None:
            self.report({"WARNING"}, f"Unknown preset '{self.preset_id}'")
            return {"CANCELLED"}

        props = context.scene.caricature_mini
        body = props.body
        gear = props.gear

        for key, val in data.get("body", {}).items():
            if hasattr(body, key):
                setattr(body, key, val)
        for key, val in data.get("gear", {}).items():
            if hasattr(gear, key):
                setattr(gear, key, val)
        if "name" in data:
            props.character_name = data["name"]

        bpy.ops.caricature.create_mini("EXEC_DEFAULT")
        self.report({"INFO"}, f"Preset '{self.preset_id}' applied.")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Export to STL
# ---------------------------------------------------------------------------

class CARICATURE_OT_ExportSTL(Operator):
    bl_idname = "caricature.export_stl"
    bl_label = "Export STL"
    bl_description = "Export the miniature as an STL file ready for 3D printing"
    bl_options = {"REGISTER"}

    def execute(self, context):
        export_props = context.scene.caricature_mini.export
        name = context.scene.caricature_mini.character_name or "caricature_mini"
        safe_name = "".join(c if c.isalnum() or c in "_- " else "_" for c in name).strip()
        filename = (export_props.export_name or safe_name) + ".stl"

        raw_path = bpy.path.abspath(export_props.export_path)
        filepath = os.path.join(raw_path, filename)

        # Collect mini objects
        col = bpy.data.collections.get(_COLLECTION_NAME)
        if col is None:
            self.report({"ERROR"}, "No Caricature Minis collection found. Create a mini first.")
            return {"CANCELLED"}

        mini_objects = [o for o in col.objects if o.get("caricature_mini")]
        if not mini_objects:
            self.report({"ERROR"}, "No mini found. Use 'Create Mini' first.")
            return {"CANCELLED"}

        # Select only mini objects
        bpy.ops.object.select_all(action="DESELECT")
        for obj in mini_objects:
            obj.select_set(True)
        context.view_layer.objects.active = mini_objects[0]

        # Apply scale for printing (metres → mm)
        scale = export_props.export_scale

        try:
            bpy.ops.export_mesh.stl(
                filepath=filepath,
                use_selection=True,
                global_scale=scale,
                use_mesh_modifiers=export_props.apply_modifiers,
                ascii=False,
            )
            self.report({"INFO"}, f"Exported to: {filepath}")
        except Exception as exc:
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Export to OBJ
# ---------------------------------------------------------------------------

class CARICATURE_OT_ExportOBJ(Operator):
    bl_idname = "caricature.export_obj"
    bl_label = "Export OBJ"
    bl_description = "Export the miniature as a Wavefront OBJ file"
    bl_options = {"REGISTER"}

    def execute(self, context):
        export_props = context.scene.caricature_mini.export
        name = context.scene.caricature_mini.character_name or "caricature_mini"
        safe_name = "".join(c if c.isalnum() or c in "_- " else "_" for c in name).strip()
        filename = (export_props.export_name or safe_name) + ".obj"

        raw_path = bpy.path.abspath(export_props.export_path)
        filepath = os.path.join(raw_path, filename)

        col = bpy.data.collections.get(_COLLECTION_NAME)
        if col is None:
            self.report({"ERROR"}, "No Caricature Minis collection found.")
            return {"CANCELLED"}

        mini_objects = [o for o in col.objects if o.get("caricature_mini")]
        if not mini_objects:
            self.report({"ERROR"}, "No mini found. Use 'Create Mini' first.")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        for obj in mini_objects:
            obj.select_set(True)
        context.view_layer.objects.active = mini_objects[0]

        scale = export_props.export_scale

        try:
            # Blender 3.x OBJ exporter
            bpy.ops.wm.obj_export(
                filepath=filepath,
                export_selected_objects=True,
                global_scale=scale,
                apply_modifiers=export_props.apply_modifiers,
            )
            self.report({"INFO"}, f"Exported to: {filepath}")
        except AttributeError:
            # Fallback for older Blender builds
            bpy.ops.export_scene.obj(
                filepath=filepath,
                use_selection=True,
                global_scale=scale,
                use_mesh_modifiers=export_props.apply_modifiers,
            )
            self.report({"INFO"}, f"Exported (legacy) to: {filepath}")
        except Exception as exc:
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Randomise character
# ---------------------------------------------------------------------------

class CARICATURE_OT_Randomise(Operator):
    bl_idname = "caricature.randomise"
    bl_label = "Randomise Character"
    bl_description = "Randomly set all body sliders and gear choices for inspiration"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        import random
        props = context.scene.caricature_mini
        body = props.body
        gear = props.gear

        def rf(lo, hi):
            return random.uniform(lo, hi)

        body.head_scale = rf(1.1, 2.0)
        body.head_width = rf(0.7, 1.4)
        body.head_depth = rf(0.7, 1.2)
        body.brow_ridge = rf(-0.3, 0.8)
        body.jaw_width = rf(-0.5, 0.8)
        body.nose_size = rf(-0.3, 0.8)
        body.ear_size = rf(-0.2, 0.8)
        body.chin_length = rf(-0.4, 0.7)
        body.shoulder_width = rf(0.6, 1.6)
        body.torso_length = rf(0.7, 1.4)
        body.belly = rf(0.0, 0.6)
        body.chest = rf(0.0, 0.6)
        body.arm_length = rf(0.7, 1.3)
        body.arm_thickness = rf(0.5, 1.8)
        body.hand_size = rf(0.6, 1.8)
        body.leg_length = rf(0.7, 1.3)
        body.leg_thickness = rf(0.6, 1.8)
        body.foot_size = rf(0.6, 1.6)

        from .properties import (HELMET_ITEMS, ARMOR_ITEMS, WEAPON_R_ITEMS,
                                  WEAPON_L_ITEMS, CAPE_ITEMS, BASE_ITEMS, POSE_ITEMS)
        gear.helmet = random.choice([i[0] for i in HELMET_ITEMS])
        gear.armor = random.choice([i[0] for i in ARMOR_ITEMS])
        gear.weapon_right = random.choice([i[0] for i in WEAPON_R_ITEMS])
        gear.weapon_left = random.choice([i[0] for i in WEAPON_L_ITEMS])
        gear.cape = random.choice([i[0] for i in CAPE_ITEMS])
        gear.base_style = random.choice([i[0] for i in BASE_ITEMS])
        gear.pose = random.choice([i[0] for i in POSE_ITEMS])
        gear.add_pauldrons = random.random() > 0.6
        gear.add_belt = random.random() > 0.5
        gear.add_scabbard = random.random() > 0.6
        gear.add_backpack = random.random() > 0.7

        bpy.ops.caricature.create_mini("EXEC_DEFAULT")
        self.report({"INFO"}, "Character randomised!")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = [
    CARICATURE_OT_CreateMini,
    CARICATURE_OT_RebuildMini,
    CARICATURE_OT_ClearMini,
    CARICATURE_OT_ApplyPreset,
    CARICATURE_OT_ExportSTL,
    CARICATURE_OT_ExportOBJ,
    CARICATURE_OT_Randomise,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
