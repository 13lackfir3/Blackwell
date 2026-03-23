"""
Custom property groups for the Caricature Mini Creator.
All sliders that drive the procedural mesh live here.
"""

import bpy
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    StringProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup


# ---------------------------------------------------------------------------
# Callback helpers – rebuild the mini whenever a slider changes
# ---------------------------------------------------------------------------

def _rebuild(self, context):
    """Generic update callback: regenerate the active mini."""
    obj = context.active_object
    if obj and obj.get("caricature_mini"):
        bpy.ops.caricature.rebuild_mini("EXEC_DEFAULT")


# ---------------------------------------------------------------------------
# Body proportions
# ---------------------------------------------------------------------------

class CaricatureBodyProps(PropertyGroup):

    total_height: FloatProperty(
        name="Total Height (m)",
        description="Overall height of the miniature in metres (scale to taste)",
        default=0.032,
        min=0.015,
        max=0.100,
        precision=4,
        update=_rebuild,
    )

    # Head
    head_scale: FloatProperty(
        name="Head Scale",
        description="Relative size of the head (>1 = caricature big-head look)",
        default=1.45,
        min=0.8,
        max=2.5,
        update=_rebuild,
    )
    head_width: FloatProperty(
        name="Head Width",
        description="Horizontal squash/stretch of the head",
        default=1.0,
        min=0.5,
        max=1.8,
        update=_rebuild,
    )
    head_depth: FloatProperty(
        name="Head Depth",
        description="Front-to-back depth of the head",
        default=0.85,
        min=0.4,
        max=1.4,
        update=_rebuild,
    )

    # Face features
    brow_ridge: FloatProperty(
        name="Brow Ridge",
        description="Prominence of the brow / forehead overhang",
        default=0.0,
        min=-1.0,
        max=1.0,
        update=_rebuild,
    )
    jaw_width: FloatProperty(
        name="Jaw Width",
        description="Width of the lower jaw / chin",
        default=0.0,
        min=-1.0,
        max=1.0,
        update=_rebuild,
    )
    nose_size: FloatProperty(
        name="Nose Size",
        description="Size of the nose bulb",
        default=0.0,
        min=-1.0,
        max=1.0,
        update=_rebuild,
    )
    ear_size: FloatProperty(
        name="Ear Size",
        description="Size of the ears",
        default=0.0,
        min=-1.0,
        max=1.0,
        update=_rebuild,
    )
    chin_length: FloatProperty(
        name="Chin Length",
        description="Length / pointiness of the chin",
        default=0.0,
        min=-1.0,
        max=1.0,
        update=_rebuild,
    )

    # Torso
    shoulder_width: FloatProperty(
        name="Shoulder Width",
        description="Width across the shoulders",
        default=1.0,
        min=0.5,
        max=2.0,
        update=_rebuild,
    )
    torso_length: FloatProperty(
        name="Torso Length",
        description="Length of the torso relative to total height",
        default=1.0,
        min=0.5,
        max=1.8,
        update=_rebuild,
    )
    belly: FloatProperty(
        name="Belly",
        description="Belly / gut protrusion",
        default=0.0,
        min=-0.5,
        max=1.0,
        update=_rebuild,
    )
    chest: FloatProperty(
        name="Chest",
        description="Chest / pectoral depth",
        default=0.0,
        min=-0.5,
        max=1.0,
        update=_rebuild,
    )

    # Arms
    arm_length: FloatProperty(
        name="Arm Length",
        description="Length of upper + lower arm combined",
        default=1.0,
        min=0.4,
        max=1.6,
        update=_rebuild,
    )
    arm_thickness: FloatProperty(
        name="Arm Thickness",
        description="Girth of the arms",
        default=1.0,
        min=0.3,
        max=2.5,
        update=_rebuild,
    )
    hand_size: FloatProperty(
        name="Hand Size",
        description="Size of the hands",
        default=1.0,
        min=0.3,
        max=2.5,
        update=_rebuild,
    )

    # Legs
    leg_length: FloatProperty(
        name="Leg Length",
        description="Length of the legs",
        default=1.0,
        min=0.4,
        max=1.6,
        update=_rebuild,
    )
    leg_thickness: FloatProperty(
        name="Leg Thickness",
        description="Girth of the legs / thighs",
        default=1.0,
        min=0.3,
        max=2.5,
        update=_rebuild,
    )
    foot_size: FloatProperty(
        name="Foot Size",
        description="Size of the feet",
        default=1.0,
        min=0.3,
        max=2.5,
        update=_rebuild,
    )


# ---------------------------------------------------------------------------
# Gear / modular parts
# ---------------------------------------------------------------------------

HELMET_ITEMS = [
    ("NONE",         "None",            "No helmet"),
    ("OPEN_FACE",    "Open Face",       "Open-face helm / barbuta"),
    ("GREAT_HELM",   "Great Helm",      "Full enclosing great helm"),
    ("HORNED",       "Horned",          "Horned barbarian helm"),
    ("CROWN",        "Crown",           "Regal crown"),
    ("HOOD",         "Hood",            "Fabric hood"),
    ("WIZARD_HAT",   "Wizard Hat",      "Classic pointy wizard hat"),
    ("PIRATE_HAT",   "Pirate Hat",      "Three-cornered pirate hat"),
]

ARMOR_ITEMS = [
    ("NONE",         "None / Naked",    "No armour"),
    ("CLOTH",        "Cloth Robes",     "Simple cloth robes"),
    ("LEATHER",      "Leather",         "Leather armour"),
    ("CHAINMAIL",    "Chainmail",       "Interlocked rings"),
    ("PLATE",        "Plate",           "Full plate armour"),
    ("ROBE_MAGE",    "Mage Robes",      "Long flowing mage robes"),
    ("BARD_TUNIC",   "Bard Tunic",      "Light colourful tunic"),
]

WEAPON_R_ITEMS = [
    ("NONE",         "None",            "Empty hand"),
    ("SWORD",        "Sword",           "One-handed sword"),
    ("DAGGER",       "Dagger",          "Short dagger"),
    ("AXE",          "Axe",             "Hand axe"),
    ("MACE",         "Mace",            "Flanged mace"),
    ("WAND",         "Wand",            "Arcane wand"),
    ("STAFF",        "Staff",           "Quarterstaff (two-handed)"),
    ("BOW",          "Bow",             "Shortbow"),
    ("CROSSBOW",     "Crossbow",        "Light crossbow"),
    ("TORCH",        "Torch",           "Lit torch"),
]

WEAPON_L_ITEMS = [
    ("NONE",         "None",            "Empty hand"),
    ("SHIELD_ROUND", "Round Shield",    "Round buckler / shield"),
    ("SHIELD_TOWER", "Tower Shield",    "Large tower shield"),
    ("DAGGER",       "Dagger",          "Off-hand dagger"),
    ("TOME",         "Tome",            "Spell tome / book"),
    ("ORB",          "Orb",             "Crystal orb"),
]

CAPE_ITEMS = [
    ("NONE",         "None",            "No cape"),
    ("SHORT",        "Short Cape",      "Short flowing cape"),
    ("LONG",         "Long Cape",       "Full-length cloak"),
    ("TATTERED",     "Tattered",        "Tattered ragged cloak"),
]

BASE_ITEMS = [
    ("FLAT",         "Flat Disc",       "Plain flat circular base"),
    ("COBBLE",       "Cobblestone",     "Cobblestone floor base"),
    ("GRASS",        "Grassy Ground",   "Natural grassy terrain"),
    ("ROCK",         "Rocky Ground",    "Rocky/dungeon ground"),
    ("RUINS",        "Ruins",           "Crumbled ruin fragments"),
]

POSE_ITEMS = [
    ("STAND",        "Standing",        "Neutral standing pose"),
    ("HEROIC",       "Heroic Stance",   "Confident hero pose"),
    ("COMBAT",       "Combat Ready",    "Weapon raised stance"),
    ("CAST",         "Casting",         "Spellcasting gesture"),
    ("KNEEL",        "Kneeling",        "One knee down"),
    ("STRIDE",       "Mid-Stride",      "Walking/striding"),
]


class CaricatureGearProps(PropertyGroup):

    helmet: EnumProperty(
        name="Helmet",
        items=HELMET_ITEMS,
        default="NONE",
        update=_rebuild,
    )
    armor: EnumProperty(
        name="Armour",
        items=ARMOR_ITEMS,
        default="CLOTH",
        update=_rebuild,
    )
    weapon_right: EnumProperty(
        name="Right Hand",
        items=WEAPON_R_ITEMS,
        default="SWORD",
        update=_rebuild,
    )
    weapon_left: EnumProperty(
        name="Left Hand",
        items=WEAPON_L_ITEMS,
        default="SHIELD_ROUND",
        update=_rebuild,
    )
    cape: EnumProperty(
        name="Cape / Cloak",
        items=CAPE_ITEMS,
        default="NONE",
        update=_rebuild,
    )
    base_style: EnumProperty(
        name="Base Style",
        items=BASE_ITEMS,
        default="FLAT",
        update=_rebuild,
    )
    pose: EnumProperty(
        name="Pose",
        items=POSE_ITEMS,
        default="HEROIC",
        update=_rebuild,
    )

    # Armour embellishments
    add_pauldrons: BoolProperty(
        name="Pauldrons",
        description="Add shoulder pauldrons on top of armour",
        default=False,
        update=_rebuild,
    )
    add_belt: BoolProperty(
        name="Belt & Pouches",
        description="Add a belt with pouches / accessories",
        default=False,
        update=_rebuild,
    )
    add_scabbard: BoolProperty(
        name="Scabbard",
        description="Add a scabbard on the hip",
        default=False,
        update=_rebuild,
    )
    add_backpack: BoolProperty(
        name="Backpack / Quiver",
        description="Add a backpack or quiver on the back",
        default=False,
        update=_rebuild,
    )


# ---------------------------------------------------------------------------
# Export settings
# ---------------------------------------------------------------------------

class CaricatureExportProps(PropertyGroup):

    export_path: StringProperty(
        name="Export Path",
        description="Directory to save exported files",
        default="//",
        subtype="DIR_PATH",
    )
    export_name: StringProperty(
        name="File Name",
        description="Base file name (without extension)",
        default="caricature_mini",
    )
    export_scale: FloatProperty(
        name="Export Scale",
        description="Scale factor applied on export (1.0 = actual metres)",
        default=1000.0,   # converts metres → mm for most slicers
        min=0.001,
        max=10000.0,
    )
    merge_parts: BoolProperty(
        name="Merge All Parts",
        description="Join all mesh objects into one before exporting",
        default=True,
    )
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply subdivision and other modifiers before export",
        default=True,
    )
    add_support_base: BoolProperty(
        name="Thicken Base",
        description="Ensure the base is thick enough for FDM / resin printing",
        default=True,
    )


# ---------------------------------------------------------------------------
# Top-level scene property group
# ---------------------------------------------------------------------------

class CaricatureMiniProps(PropertyGroup):
    body: PointerProperty(type=CaricatureBodyProps)
    gear: PointerProperty(type=CaricatureGearProps)
    export: PointerProperty(type=CaricatureExportProps)

    character_name: StringProperty(
        name="Character Name",
        description="Name used to label the mini collection",
        default="My Hero",
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = [
    CaricatureBodyProps,
    CaricatureGearProps,
    CaricatureExportProps,
    CaricatureMiniProps,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.caricature_mini = PointerProperty(type=CaricatureMiniProps)


def unregister():
    del bpy.types.Scene.caricature_mini
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
