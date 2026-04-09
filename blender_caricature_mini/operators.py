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


def _add_remesh(obj, H):
    """Voxel remesh merges all overlapping primitives into one smooth surface."""
    mod = obj.modifiers.new(name="Remesh", type="REMESH")
    mod.mode = 'VOXEL'
    # ~4 % of total height gives ~25 voxels across the figure — good detail
    mod.voxel_size = max(H * 0.040, 0.0008)
    mod.adaptivity = 0.0
    mod.use_smooth_shade = True


def _add_subdivision(obj, levels=1):
    mod = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = levels + 1


def _add_smooth_shade(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def _hide_default_cube(context):
    """Hide the default Blender startup cube so the mini isn't obscured."""
    cube = bpy.data.objects.get("Cube")
    if cube is None:
        return
    # Only touch it if it's the unmodified default: a mesh with exactly
    # 8 verts and no custom properties or modifiers.
    if (cube.type == "MESH"
            and len(cube.data.vertices) == 8
            and not cube.keys()
            and not cube.modifiers):
        cube.hide_set(True)  # hide in viewport (recoverable via outliner)


def _zoom_to_mini(context):
    """Zoom every 3D viewport to frame the active selection."""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            # Find the region that handles 3D navigation
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region is None:
                continue
            try:
                with context.temp_override(window=window, area=area, region=region):
                    bpy.ops.view3d.view_selected(use_all_regions=False)
            except Exception:
                pass


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

        # Find any existing mini object
        col = bpy.data.collections.get(_COLLECTION_NAME)
        existing_obj = None
        if col:
            minis = [o for o in col.objects if o.get("caricature_mini")]
            existing_obj = minis[0] if minis else None

        # Build new geometry (returns a detached object not yet in any collection)
        new_obj = build_caricature_mini_v2(props.body, props.gear)
        new_mesh = new_obj.data
        char_name = props.character_name or "CaricatureMini"

        if existing_obj:
            # --- Swap mesh data in-place ---
            # The existing object keeps its modifiers, selection state, and
            # collection membership; only its mesh data is replaced.
            old_mesh = existing_obj.data
            existing_obj.data = new_mesh
            new_mesh.name = char_name
            existing_obj.name = char_name
            # Clean up the temporary object and the old mesh
            bpy.data.objects.remove(new_obj, do_unlink=True)
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)
            # Re-apply smooth shading to the new polygons
            _add_smooth_shade(existing_obj)
            obj = existing_obj
        else:
            # --- First creation: full setup ---
            new_obj["caricature_mini"] = True
            new_obj.name = char_name
            new_mesh.name = char_name
            col = _get_or_create_collection(_COLLECTION_NAME)
            _link_object(new_obj, col)
            _add_remesh(new_obj, props.body.total_height)
            _add_subdivision(new_obj, levels=1)
            _add_smooth_shade(new_obj)
            obj = new_obj
            # Select the new mini
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            # Hide the default Blender startup cube so the mini is visible
            _hide_default_cube(context)
            # Zoom the viewport to frame the mini
            _zoom_to_mini(context)

        # Force all 3D viewports to redraw
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()

        return {"FINISHED"}


class CARICATURE_OT_RebuildMini(Operator):
    bl_idname = "caricature.rebuild_mini"
    bl_label = "Rebuild Mini"
    bl_description = "Regenerate the mini with updated settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return bpy.ops.caricature.create_mini("EXEC_DEFAULT")


# ---------------------------------------------------------------------------
# Clear Mini
# ---------------------------------------------------------------------------

class CARICATURE_OT_ZoomToMini(Operator):
    bl_idname = "caricature.zoom_to_mini"
    bl_label = "Zoom to Mini"
    bl_description = "Frame the miniature in the 3D viewport (the mini is tiny — 32 mm)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        col = bpy.data.collections.get(_COLLECTION_NAME)
        if col is None:
            self.report({"WARNING"}, "No mini found. Click 'Create Mini' first.")
            return {"CANCELLED"}
        minis = [o for o in col.objects if o.get("caricature_mini")]
        if not minis:
            self.report({"WARNING"}, "No mini found. Click 'Create Mini' first.")
            return {"CANCELLED"}
        bpy.ops.object.select_all(action="DESELECT")
        for o in minis:
            o.select_set(True)
        context.view_layer.objects.active = minis[0]
        _zoom_to_mini(context)
        return {"FINISHED"}


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
                                  WEAPON_L_ITEMS, CAPE_ITEMS, BASE_ITEMS,
                                  POSE_ITEMS, BACK_ITEM_ITEMS)
        gear.helmet = random.choice([i[0] for i in HELMET_ITEMS])
        gear.armor = random.choice([i[0] for i in ARMOR_ITEMS])
        gear.weapon_right = random.choice([i[0] for i in WEAPON_R_ITEMS])
        gear.weapon_left = random.choice([i[0] for i in WEAPON_L_ITEMS])
        gear.cape = random.choice([i[0] for i in CAPE_ITEMS])
        gear.base_style = random.choice([i[0] for i in BASE_ITEMS])
        gear.pose = random.choice([i[0] for i in POSE_ITEMS])
        gear.back_item = random.choice([i[0] for i in BACK_ITEM_ITEMS])
        gear.add_pauldrons = random.random() > 0.6
        gear.add_belt = random.random() > 0.5
        gear.add_scabbard = random.random() > 0.6

        bpy.ops.caricature.create_mini("EXEC_DEFAULT")
        self.report({"INFO"}, "Character randomised!")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = [
    CARICATURE_OT_CreateMini,
    CARICATURE_OT_RebuildMini,
    CARICATURE_OT_ZoomToMini,
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
