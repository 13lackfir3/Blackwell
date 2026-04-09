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

_rebuild_scheduled = False


def _rebuild(self, context):
    """Debounced update callback — schedules a rebuild via timer so it works
    regardless of active object and avoids bpy.ops context restrictions."""
    global _rebuild_scheduled
    if _rebuild_scheduled:
        return  # already queued, don't pile up

    col = bpy.data.collections.get("Caricature Minis")
    if col is None or not any(o.get("caricature_mini") for o in col.objects):
        return  # no mini exists yet — nothing to rebuild

    _rebuild_scheduled = True

    def _do_rebuild():
        global _rebuild_scheduled
        _rebuild_scheduled = False
        bpy.ops.caricature.create_mini("EXEC_DEFAULT")
        return None  # returning None means don't repeat

    bpy.app.timers.register(_do_rebuild, first_interval=0.05)


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
    # ---- Unarmed / empty ----
    ("NONE",            "None",               "Empty hand"),
    # ---- Swords ----
    ("SWORD",           "Sword",              "One-handed arming sword"),
    ("LONGSWORD",       "Longsword",          "Longer hand-and-a-half sword"),
    ("GREATSWORD",      "Greatsword",         "Massive two-handed sword"),
    ("RAPIER",          "Rapier",             "Slender thrusting blade with swept guard"),
    ("SCIMITAR",        "Scimitar",           "Curved single-edged cavalry sword"),
    ("KATANA",          "Katana",             "Elegant curved eastern blade"),
    ("SHORTSWORD",      "Shortsword",         "Compact one-handed blade"),
    # ---- Axes ----
    ("AXE",             "Hand Axe",           "Single-bit hand axe"),
    ("BATTLEAXE",       "Battleaxe",          "Large two-handed double-headed axe"),
    ("HATCHET",         "Hatchet",            "Small lightweight hatchet"),
    # ---- Blunt ----
    ("MACE",            "Mace",               "Flanged mace"),
    ("WARHAMMER",       "Warhammer",          "Heavy war hammer with poll spike"),
    ("MAUL",            "Maul",               "Giant two-handed stone maul"),
    ("FLAIL",           "Flail",              "Handle, chain, and spiked ball"),
    ("MORNINGSTAR",     "Morning Star",       "Spiked metal ball on a short haft"),
    ("CLUB",            "Club",               "Simple wooden club"),
    # ---- Polearms ----
    ("SPEAR",           "Spear",              "Long shaft with leaf-shaped head"),
    ("HALBERD",         "Halberd",            "Polearm with axe blade and back-spike"),
    ("TRIDENT",         "Trident",            "Three-pronged sea weapon"),
    ("SCYTHE",          "Scythe",             "Curved reaping blade on long pole"),
    ("LANCE",           "Lance",              "Heavy cavalry lance"),
    ("GLAIVE",          "Glaive",             "Single-edged blade on a long haft"),
    # ---- Ranged ----
    ("BOW",             "Shortbow",           "Short recurve bow"),
    ("LONGBOW",         "Longbow",            "Tall war longbow"),
    ("CROSSBOW",        "Crossbow",           "Light one-handed crossbow"),
    ("HAND_CROSSBOW",   "Hand Crossbow",      "Compact pistol-grip crossbow"),
    ("SLING",           "Sling",              "Leather sling with stone"),
    ("JAVELIN",         "Javelin",            "Short throwing spear"),
    ("THROWING_KNIFE",  "Throwing Knife",     "Balanced throwing blade"),
    # ---- Arcane / utility ----
    ("WAND",            "Wand",               "Arcane focus wand"),
    ("STAFF",           "Staff",              "Quarterstaff / walking staff"),
    ("SCEPTRE",         "Sceptre",            "Ornate magical sceptre"),
    ("TORCH",           "Torch",              "Burning torch"),
    ("LANTERN",         "Lantern",            "Hooded oil lantern"),
    # ---- Exotic ----
    ("WHIP",            "Whip",               "Coiled leather whip"),
    ("SICKLE",          "Sickle",             "Small curved harvesting sickle"),
    ("NET",             "Net",                "Thrown weighted net"),
    ("PISTOL",          "Flintlock Pistol",   "Single-shot flintlock pistol"),
    ("RIFLE",           "Flintlock Rifle",    "Long-barrelled musket / rifle"),
    ("GUNBLADE",        "Gunblade",           "Sword with integrated flintlock"),
]

WEAPON_L_ITEMS = [
    # ---- Empty / Shields ----
    ("NONE",            "None",               "Empty off-hand"),
    ("SHIELD_ROUND",    "Round Shield",       "Round buckler"),
    ("SHIELD_TOWER",    "Tower Shield",       "Massive tower shield"),
    ("SHIELD_KITE",     "Kite Shield",        "Pointed heater / kite shield"),
    ("SHIELD_SPIKED",   "Spiked Shield",      "Round shield with central spike"),
    # ---- Off-hand weapons ----
    ("DAGGER",          "Dagger",             "Off-hand dagger"),
    ("SHORTSWORD",      "Shortsword",         "Off-hand short sword"),
    ("AXE",             "Hand Axe",           "Off-hand hand axe"),
    ("PARRYING_DAGGER", "Parrying Dagger",    "Wide-bladed duelling parry dagger"),
    # ---- Magical items ----
    ("TOME",            "Tome",               "Spell tome / grimoire"),
    ("ORB",             "Orb",                "Crystal scrying orb"),
    ("WAND",            "Wand",               "Off-hand wand"),
    ("SCROLL",          "Scroll",             "Unfurled magic scroll"),
    ("HOLY_SYMBOL",     "Holy Symbol",        "Religious amulet / sunburst symbol"),
    ("FOCUS_GEM",       "Arcane Focus",       "Faceted gem arcane focus"),
    # ---- Utility / flavour ----
    ("TORCH",           "Torch",              "Off-hand torch"),
    ("LANTERN",         "Lantern",            "Hooded lantern"),
    ("POTION",          "Potion Bottle",      "Drinking a potion"),
    ("SKULL",           "Skull",              "Grim skull trophy"),
    ("HORN",            "War Horn",           "Drinking / signal horn"),
    ("ROPE_COIL",       "Rope Coil",          "Coiled adventurer's rope"),
    ("SEVERED_HEAD",    "Severed Head",       "Grim trophy head"),
    ("COIN_PURSE",      "Coin Purse",         "Bulging coin purse"),
    ("HAND_CROSSBOW",   "Hand Crossbow",      "Off-hand compact crossbow"),
]

# ---------------------------------------------------------------------------
# Back / carried items  (replaces the old add_backpack boolean)
# ---------------------------------------------------------------------------

BACK_ITEM_ITEMS = [
    ("NONE",            "None",               "Nothing on the back"),
    # ---- Storage ----
    ("BACKPACK",        "Backpack",           "Classic adventurer's pack"),
    ("SATCHEL",         "Satchel",            "Messenger / shoulder satchel"),
    ("BEDROLL",         "Bedroll",            "Rolled bedroll strapped to pack"),
    ("BARREL",          "Ale Barrel",         "Small barrel (dwarf essential)"),
    # ---- Quivers / ammo ----
    ("QUIVER",          "Quiver",             "Arrow quiver"),
    ("BOLT_CASE",       "Bolt Case",          "Crossbow bolt case"),
    # ---- Weapons on back ----
    ("SWORD_BACK",      "Sword (Sheathed)",   "One-handed sword in back-scabbard"),
    ("GREATSWORD_BACK", "Greatsword (Back)",  "Greatsword strapped across the back"),
    ("AXES_CROSSED",    "Crossed Axes",       "Two axes crossed on the back"),
    ("SHIELD_BACK",     "Shield (Carried)",   "Shield strapped flat to the back"),
    ("SPEAR_BACK",      "Spear (Slung)",      "Spear slung diagonally"),
    # ---- Wings ----
    ("WINGS_FEATHER",   "Feathered Wings",    "Angel / aasimar feathered wings"),
    ("WINGS_BAT",       "Bat Wings",          "Demon / tiefling bat wings"),
    ("WINGS_FAIRY",     "Fairy Wings",        "Delicate fey insect wings"),
    ("WINGS_DRAGON",    "Dragon Wings",       "Large draconic leathery wings"),
    # ---- Magical / exotic ----
    ("MAGIC_AURA",      "Magic Aura",         "Swirling ethereal energy tendrils"),
    ("JETPACK",         "Gnomish Jetpack",    "Mechanical steam-powered thruster"),
    ("INSTRUMENT_LUTE", "Lute",               "Lute strapped to back (bard)"),
    ("CAULDRON",        "Cauldron",           "Witch's cauldron on the back"),
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
    back_item: EnumProperty(
        name="Back Item",
        description="Item carried or worn on the back",
        items=BACK_ITEM_ITEMS,
        default="NONE",
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
