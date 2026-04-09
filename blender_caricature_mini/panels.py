"""
UI panels for the Caricature Mini Creator.
All panels live in the View3D sidebar under the "Mini Creator" tab.
"""

import bpy
from bpy.types import Panel

from .presets import PRESETS


# ---------------------------------------------------------------------------
# Base mix-in
# ---------------------------------------------------------------------------

class CaricaturePanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mini Creator"


# ---------------------------------------------------------------------------
# Main / Quick-start panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Main(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Main"
    bl_label = "Caricature Mini Creator"

    def draw(self, context):
        layout = self.layout
        props = context.scene.caricature_mini

        # Character name
        row = layout.row(align=True)
        row.prop(props, "character_name", text="", icon="ARMATURE_DATA")

        layout.separator()

        # Primary action buttons
        col = layout.column(align=True)
        col.scale_y = 1.6
        col.operator("caricature.create_mini", icon="MESH_MONKEY")
        col.operator("caricature.randomise", icon="FILE_REFRESH")
        col.operator("caricature.zoom_to_mini", icon="ZOOM_SELECTED")
        col.operator("caricature.clear_mini", icon="TRASH")


# ---------------------------------------------------------------------------
# Presets panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Presets(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Presets"
    bl_label = "Archetypes & Presets"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Load a character archetype:")

        grid = layout.grid_flow(row_major=True, columns=2, align=True)
        for pid, data in PRESETS.items():
            op = grid.operator(
                "caricature.apply_preset",
                text=data.get("label", pid.title()),
                icon=data.get("icon", "PERSON"),
            )
            op.preset_id = pid


# ---------------------------------------------------------------------------
# Body proportions panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Body(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Body"
    bl_label = "Body Proportions"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        body = context.scene.caricature_mini.body

        layout.prop(body, "total_height")

        box = layout.box()
        box.label(text="Head", icon="MESH_UVSPHERE")
        col = box.column(align=True)
        col.prop(body, "head_scale", slider=True)
        col.prop(body, "head_width", slider=True)
        col.prop(body, "head_depth", slider=True)

        box = layout.box()
        box.label(text="Torso", icon="MESH_CUBE")
        col = box.column(align=True)
        col.prop(body, "shoulder_width", slider=True)
        col.prop(body, "torso_length", slider=True)
        col.prop(body, "chest", slider=True)
        col.prop(body, "belly", slider=True)

        box = layout.box()
        box.label(text="Arms & Hands", icon="OUTLINER_OB_ARMATURE")
        col = box.column(align=True)
        col.prop(body, "arm_length", slider=True)
        col.prop(body, "arm_thickness", slider=True)
        col.prop(body, "hand_size", slider=True)

        box = layout.box()
        box.label(text="Legs & Feet", icon="MOD_WAVE")
        col = box.column(align=True)
        col.prop(body, "leg_length", slider=True)
        col.prop(body, "leg_thickness", slider=True)
        col.prop(body, "foot_size", slider=True)


# ---------------------------------------------------------------------------
# Face features panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Face(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Face"
    bl_label = "Face Features"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        body = context.scene.caricature_mini.body

        col = layout.column(align=True)
        col.prop(body, "brow_ridge", slider=True)
        col.prop(body, "jaw_width", slider=True)
        col.prop(body, "nose_size", slider=True)
        col.prop(body, "ear_size", slider=True)
        col.prop(body, "chin_length", slider=True)


# ---------------------------------------------------------------------------
# Gear panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Gear(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Gear"
    bl_label = "Gear & Equipment"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        gear = context.scene.caricature_mini.gear

        layout.prop(gear, "pose", icon="POSE_HLT")
        layout.separator()

        box = layout.box()
        box.label(text="Worn Equipment", icon="ARMATURE_DATA")
        col = box.column(align=True)
        col.prop(gear, "helmet")
        col.prop(gear, "armor")
        col.prop(gear, "cape")

        box = layout.box()
        box.label(text="Hand Weapons & Items", icon="ORIENTATION_GIMBAL")
        col = box.column(align=True)
        col.prop(gear, "weapon_right", text="Right Hand")
        col.prop(gear, "weapon_left", text="Left Hand")

        box = layout.box()
        box.label(text="Back Item", icon="PACKAGE")
        box.prop(gear, "back_item", text="")

        box = layout.box()
        box.label(text="Extras", icon="PLUS")
        col = box.column(align=False)
        col.prop(gear, "add_pauldrons")
        col.prop(gear, "add_belt")
        col.prop(gear, "add_scabbard")

        layout.separator()
        layout.prop(gear, "base_style", icon="MESH_CIRCLE")


# ---------------------------------------------------------------------------
# Export panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Export(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Export"
    bl_label = "Export for 3D Printing"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        exp = context.scene.caricature_mini.export

        box = layout.box()
        box.label(text="Output Settings", icon="FILE_FOLDER")
        col = box.column(align=True)
        col.prop(exp, "export_path", text="")
        col.prop(exp, "export_name")
        col.prop(exp, "export_scale")

        box = layout.box()
        box.label(text="Options", icon="SETTINGS")
        col = box.column(align=False)
        col.prop(exp, "merge_parts")
        col.prop(exp, "apply_modifiers")
        col.prop(exp, "add_support_base")

        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.4
        row.operator("caricature.export_stl", icon="EXPORT", text="Export STL")
        row.operator("caricature.export_obj", icon="EXPORT", text="Export OBJ")


# ---------------------------------------------------------------------------
# Tips / Help panel
# ---------------------------------------------------------------------------

class CARICATURE_PT_Help(CaricaturePanel, Panel):
    bl_idname = "CARICATURE_PT_Help"
    bl_label = "Tips & Help"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        tips = [
            "Press 'Create Mini' to generate your character.",
            "Sliders auto-rebuild when changed.",
            "Use 'Randomise' for quick inspiration.",
            "Archetypes pre-fill all settings.",
            "Right Hand: 40+ weapons including guns, polearms, and exotic items.",
            "Left Hand: 25+ items – shields, spell foci, potions, skulls…",
            "Back Item: 22 options – wings, quivers, packs, sheathed weapons.",
            "Export scale 1000 = metres → mm (most slicers).",
            "Enable 'Thicken Base' for resin printing.",
            "Sub-division modifier adds surface detail.",
            "Combine with Blender sculpt for fine details.",
        ]
        for tip in tips:
            row = col.row()
            row.label(text=tip, icon="DOT")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = [
    CARICATURE_PT_Main,
    CARICATURE_PT_Presets,
    CARICATURE_PT_Body,
    CARICATURE_PT_Face,
    CARICATURE_PT_Gear,
    CARICATURE_PT_Export,
    CARICATURE_PT_Help,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
