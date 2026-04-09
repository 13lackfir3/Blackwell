"""
Character archetype presets for the Caricature Mini Creator.

Each preset is a dict with:
  label  – display name in the UI
  icon   – Blender icon string
  name   – default character name
  body   – overrides for CaricatureBodyProps fields
  gear   – overrides for CaricatureGearProps fields
"""

import bpy

# ---------------------------------------------------------------------------
# Preset definitions
# ---------------------------------------------------------------------------

PRESETS = {
    # ---- Martial classes -----------------------------------------------
    "fighter": {
        "label": "Fighter",
        "icon": "OUTLINER_OB_ARMATURE",
        "name": "Sir Ironwall",
        "body": {
            "head_scale": 1.5,
            "shoulder_width": 1.4,
            "torso_length": 1.0,
            "chest": 0.5,
            "belly": 0.0,
            "arm_thickness": 1.6,
            "leg_thickness": 1.4,
        },
        "gear": {
            "helmet": "OPEN_FACE",
            "armor": "PLATE",
            "weapon_right": "LONGSWORD",
            "weapon_left": "SHIELD_KITE",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "HEROIC",
            "back_item": "SWORD_BACK",
            "add_pauldrons": True,
            "add_belt": True,
            "add_scabbard": True,
        },
    },

    "paladin": {
        "label": "Paladin",
        "icon": "LIGHT_SUN",
        "name": "Lady Dawnbright",
        "body": {
            "head_scale": 1.4,
            "shoulder_width": 1.35,
            "torso_length": 1.0,
            "chest": 0.4,
            "arm_thickness": 1.4,
            "leg_thickness": 1.3,
        },
        "gear": {
            "helmet": "GREAT_HELM",
            "armor": "PLATE",
            "weapon_right": "WARHAMMER",
            "weapon_left": "SHIELD_TOWER",
            "cape": "LONG",
            "base_style": "COBBLE",
            "pose": "STAND",
            "back_item": "NONE",
            "add_pauldrons": True,
            "add_belt": False,
            "add_scabbard": False,
        },
    },

    "barbarian": {
        "label": "Barbarian",
        "icon": "MESH_MONKEY",
        "name": "Krug Skullsmasher",
        "body": {
            "head_scale": 1.6,
            "shoulder_width": 1.7,
            "torso_length": 1.1,
            "chest": 0.7,
            "belly": 0.3,
            "arm_thickness": 2.0,
            "leg_thickness": 1.7,
            "brow_ridge": 0.7,
            "jaw_width": 0.6,
            "nose_size": 0.4,
        },
        "gear": {
            "helmet": "HORNED",
            "armor": "LEATHER",
            "weapon_right": "BATTLEAXE",
            "weapon_left": "SKULL",
            "cape": "TATTERED",
            "base_style": "ROCK",
            "pose": "COMBAT",
            "back_item": "AXES_CROSSED",
            "add_pauldrons": False,
            "add_belt": True,
        },
    },

    "ranger": {
        "label": "Ranger",
        "icon": "FOREST",
        "name": "Sylva Swiftarrow",
        "body": {
            "head_scale": 1.35,
            "shoulder_width": 1.1,
            "torso_length": 1.0,
            "arm_length": 1.1,
            "leg_length": 1.1,
        },
        "gear": {
            "helmet": "HOOD",
            "armor": "LEATHER",
            "weapon_right": "LONGBOW",
            "weapon_left": "NONE",
            "cape": "SHORT",
            "base_style": "GRASS",
            "pose": "STRIDE",
            "back_item": "QUIVER",
            "add_belt": True,
        },
    },

    "rogue": {
        "label": "Rogue",
        "icon": "HIDE_OFF",
        "name": "Nix Shadowstep",
        "body": {
            "head_scale": 1.3,
            "shoulder_width": 0.95,
            "torso_length": 0.95,
            "arm_length": 1.05,
        },
        "gear": {
            "helmet": "HOOD",
            "armor": "LEATHER",
            "weapon_right": "RAPIER",
            "weapon_left": "PARRYING_DAGGER",
            "cape": "NONE",
            "base_style": "COBBLE",
            "pose": "COMBAT",
            "back_item": "SATCHEL",
            "add_belt": True,
            "add_scabbard": True,
        },
    },

    # ---- Spellcasters ---------------------------------------------------
    "wizard": {
        "label": "Wizard",
        "icon": "MODIFIER_ON",
        "name": "Archmage Zelvin",
        "body": {
            "head_scale": 1.7,
            "shoulder_width": 0.85,
            "torso_length": 1.1,
            "belly": 0.2,
            "arm_length": 1.05,
            "arm_thickness": 0.7,
            "brow_ridge": 0.5,
            "nose_size": 0.5,
            "chin_length": 0.4,
        },
        "gear": {
            "helmet": "WIZARD_HAT",
            "armor": "ROBE_MAGE",
            "weapon_right": "STAFF",
            "weapon_left": "TOME",
            "cape": "LONG",
            "base_style": "COBBLE",
            "pose": "CAST",
            "back_item": "NONE",
            "add_belt": True,
        },
    },

    "sorcerer": {
        "label": "Sorcerer",
        "icon": "PARTICLES",
        "name": "Draconis",
        "body": {
            "head_scale": 1.5,
            "shoulder_width": 1.0,
            "torso_length": 1.0,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "CLOTH",
            "weapon_right": "SCEPTRE",
            "weapon_left": "FOCUS_GEM",
            "cape": "LONG",
            "base_style": "COBBLE",
            "pose": "CAST",
            "back_item": "WINGS_DRAGON",
        },
    },

    "warlock": {
        "label": "Warlock",
        "icon": "GHOST_ENABLED",
        "name": "Malachar",
        "body": {
            "head_scale": 1.55,
            "shoulder_width": 1.05,
            "brow_ridge": 0.4,
            "chin_length": 0.3,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "ROBE_MAGE",
            "weapon_right": "WAND",
            "weapon_left": "SKULL",
            "cape": "TATTERED",
            "base_style": "RUINS",
            "pose": "CAST",
            "back_item": "WINGS_BAT",
        },
    },

    "cleric": {
        "label": "Cleric",
        "icon": "OUTLINER_OB_LIGHT",
        "name": "Brother Aldric",
        "body": {
            "head_scale": 1.45,
            "shoulder_width": 1.15,
            "torso_length": 1.05,
            "chest": 0.25,
        },
        "gear": {
            "helmet": "OPEN_FACE",
            "armor": "CHAINMAIL",
            "weapon_right": "MACE",
            "weapon_left": "HOLY_SYMBOL",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "STAND",
            "back_item": "SHIELD_BACK",
            "add_pauldrons": False,
            "add_belt": True,
        },
    },

    # ---- Support / Other -----------------------------------------------
    "bard": {
        "label": "Bard",
        "icon": "SOUND",
        "name": "Finnly Strumsworth",
        "body": {
            "head_scale": 1.4,
            "shoulder_width": 0.9,
            "torso_length": 0.95,
            "arm_length": 1.1,
        },
        "gear": {
            "helmet": "PIRATE_HAT",
            "armor": "BARD_TUNIC",
            "weapon_right": "TORCH",
            "weapon_left": "HORN",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "STRIDE",
            "back_item": "INSTRUMENT_LUTE",
            "add_belt": True,
        },
    },

    "druid": {
        "label": "Druid",
        "icon": "OUTLINER_OB_FORCE_FIELD",
        "name": "Mossbark",
        "body": {
            "head_scale": 1.5,
            "shoulder_width": 1.0,
            "belly": 0.15,
            "ear_size": 0.3,
        },
        "gear": {
            "helmet": "HOOD",
            "armor": "CLOTH",
            "weapon_right": "STAFF",
            "weapon_left": "NONE",
            "cape": "LONG",
            "base_style": "GRASS",
            "pose": "CAST",
            "back_item": "BACKPACK",
            "add_belt": True,
        },
    },

    "monk": {
        "label": "Monk",
        "icon": "CANCEL",
        "name": "Brother Katsuro",
        "body": {
            "head_scale": 1.3,
            "shoulder_width": 1.1,
            "torso_length": 1.0,
            "arm_length": 1.05,
            "leg_length": 1.1,
            "arm_thickness": 1.2,
            "leg_thickness": 1.2,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "CLOTH",
            "weapon_right": "NONE",
            "weapon_left": "NONE",
            "cape": "NONE",
            "base_style": "FLAT",
            "pose": "COMBAT",
            "back_item": "NONE",
        },
    },

    # ---- Fantasy races / specials --------------------------------------
    "dwarf": {
        "label": "Dwarf",
        "icon": "MESH_TORUS",
        "name": "Throdin Ironbeard",
        "body": {
            "total_height": 0.025,
            "head_scale": 1.8,
            "shoulder_width": 1.5,
            "torso_length": 0.75,
            "belly": 0.4,
            "chest": 0.5,
            "leg_length": 0.65,
            "leg_thickness": 1.6,
            "arm_thickness": 1.7,
            "brow_ridge": 0.6,
            "jaw_width": 0.5,
            "nose_size": 0.5,
        },
        "gear": {
            "helmet": "HORNED",
            "armor": "PLATE",
            "weapon_right": "BATTLEAXE",
            "weapon_left": "SHIELD_ROUND",
            "cape": "NONE",
            "base_style": "ROCK",
            "pose": "COMBAT",
            "back_item": "BARREL",
            "add_pauldrons": True,
            "add_belt": True,
            "add_scabbard": True,
        },
    },

    "elf": {
        "label": "Elf",
        "icon": "MESH_CAPSULE",
        "name": "Aelindra Moonwhisper",
        "body": {
            "total_height": 0.035,
            "head_scale": 1.3,
            "shoulder_width": 0.85,
            "torso_length": 1.1,
            "ear_size": 0.8,
            "head_depth": 0.75,
            "jaw_width": -0.3,
            "chin_length": 0.2,
            "arm_length": 1.2,
            "leg_length": 1.15,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "LEATHER",
            "weapon_right": "LONGBOW",
            "weapon_left": "NONE",
            "cape": "LONG",
            "base_style": "GRASS",
            "pose": "HEROIC",
            "back_item": "QUIVER",
        },
    },

    "halfling": {
        "label": "Halfling",
        "icon": "PMARKER",
        "name": "Pipwick Goodbarrel",
        "body": {
            "total_height": 0.022,
            "head_scale": 1.9,
            "shoulder_width": 0.85,
            "torso_length": 0.85,
            "belly": 0.25,
            "leg_length": 0.7,
            "foot_size": 1.8,
            "nose_size": 0.3,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "BARD_TUNIC",
            "weapon_right": "DAGGER",
            "weapon_left": "ROPE_COIL",
            "cape": "SHORT",
            "base_style": "GRASS",
            "pose": "STRIDE",
            "back_item": "BACKPACK",
            "add_belt": True,
        },
    },

    "undead": {
        "label": "Undead Warrior",
        "icon": "GHOST_DISABLED",
        "name": "Lord Vexar",
        "body": {
            "head_scale": 1.6,
            "shoulder_width": 1.2,
            "torso_length": 1.0,
            "belly": -0.2,
            "arm_thickness": 0.7,
            "leg_thickness": 0.65,
            "brow_ridge": 0.8,
            "jaw_width": 0.4,
            "nose_size": -0.5,
        },
        "gear": {
            "helmet": "GREAT_HELM",
            "armor": "PLATE",
            "weapon_right": "SWORD",
            "weapon_left": "SHIELD_TOWER",
            "cape": "TATTERED",
            "base_style": "RUINS",
            "pose": "COMBAT",
            "back_item": "GREATSWORD_BACK",
        },
    },

    # ---- New archetypes showcasing new gear ----------------------------
    "gunslinger": {
        "label": "Gunslinger",
        "icon": "SNAP_FACE_CENTER",
        "name": "Crack McGee",
        "body": {
            "head_scale": 1.4,
            "shoulder_width": 1.1,
            "torso_length": 1.0,
            "arm_length": 1.05,
        },
        "gear": {
            "helmet": "PIRATE_HAT",
            "armor": "LEATHER",
            "weapon_right": "PISTOL",
            "weapon_left": "HAND_CROSSBOW",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "COMBAT",
            "back_item": "BOLT_CASE",
            "add_belt": True,
            "add_scabbard": False,
        },
    },

    "aasimar": {
        "label": "Aasimar",
        "icon": "LIGHT_AREA",
        "name": "Seraphel Goldenlight",
        "body": {
            "head_scale": 1.4,
            "shoulder_width": 1.1,
            "torso_length": 1.05,
            "jaw_width": -0.2,
            "chin_length": 0.15,
        },
        "gear": {
            "helmet": "CROWN",
            "armor": "PLATE",
            "weapon_right": "LONGSWORD",
            "weapon_left": "HOLY_SYMBOL",
            "cape": "LONG",
            "base_style": "COBBLE",
            "pose": "HEROIC",
            "back_item": "WINGS_FEATHER",
            "add_pauldrons": True,
        },
    },

    "tiefling": {
        "label": "Tiefling",
        "icon": "GHOST_ENABLED",
        "name": "Zaryn Ashveil",
        "body": {
            "head_scale": 1.45,
            "shoulder_width": 1.05,
            "brow_ridge": 0.5,
            "ear_size": 0.3,
            "chin_length": 0.2,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "ROBE_MAGE",
            "weapon_right": "RAPIER",
            "weapon_left": "FOCUS_GEM",
            "cape": "TATTERED",
            "base_style": "RUINS",
            "pose": "HEROIC",
            "back_item": "WINGS_BAT",
        },
    },

    "fairy": {
        "label": "Fairy",
        "icon": "SHADERFX",
        "name": "Thistlewick",
        "body": {
            "total_height": 0.018,
            "head_scale": 1.9,
            "shoulder_width": 0.7,
            "torso_length": 0.85,
            "arm_length": 0.9,
            "leg_length": 0.8,
            "ear_size": 0.6,
            "jaw_width": -0.4,
        },
        "gear": {
            "helmet": "NONE",
            "armor": "CLOTH",
            "weapon_right": "WAND",
            "weapon_left": "NONE",
            "cape": "NONE",
            "base_style": "GRASS",
            "pose": "CAST",
            "back_item": "WINGS_FAIRY",
        },
    },

    "witch": {
        "label": "Witch",
        "icon": "MODIFIER_OFF",
        "name": "Griselda Blackthorn",
        "body": {
            "head_scale": 1.65,
            "shoulder_width": 0.8,
            "torso_length": 1.05,
            "belly": 0.1,
            "brow_ridge": 0.6,
            "nose_size": 0.8,
            "chin_length": 0.6,
        },
        "gear": {
            "helmet": "WIZARD_HAT",
            "armor": "ROBE_MAGE",
            "weapon_right": "STAFF",
            "weapon_left": "POTION",
            "cape": "TATTERED",
            "base_style": "RUINS",
            "pose": "CAST",
            "back_item": "CAULDRON",
        },
    },

    "pirate": {
        "label": "Pirate",
        "icon": "SORTBYEXT",
        "name": "Cap'n Brackwater",
        "body": {
            "head_scale": 1.5,
            "shoulder_width": 1.2,
            "torso_length": 1.0,
            "belly": 0.2,
            "brow_ridge": 0.3,
        },
        "gear": {
            "helmet": "PIRATE_HAT",
            "armor": "LEATHER",
            "weapon_right": "SCIMITAR",
            "weapon_left": "PISTOL",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "HEROIC",
            "back_item": "NONE",
            "add_belt": True,
            "add_scabbard": True,
        },
    },

    "knight_dragon": {
        "label": "Dragon Knight",
        "icon": "MESH_ICOSPHERE",
        "name": "Ignarax the Scaled",
        "body": {
            "head_scale": 1.55,
            "shoulder_width": 1.5,
            "torso_length": 1.05,
            "chest": 0.6,
            "arm_thickness": 1.7,
            "leg_thickness": 1.5,
            "brow_ridge": 0.5,
        },
        "gear": {
            "helmet": "HORNED",
            "armor": "PLATE",
            "weapon_right": "GREATSWORD",
            "weapon_left": "NONE",
            "cape": "LONG",
            "base_style": "ROCK",
            "pose": "COMBAT",
            "back_item": "WINGS_DRAGON",
            "add_pauldrons": True,
            "add_belt": True,
        },
    },
}


# ---------------------------------------------------------------------------
# Registration (no classes to register, but keep module consistent)
# ---------------------------------------------------------------------------

def register():
    pass


def unregister():
    pass
