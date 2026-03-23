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
            "weapon_right": "SWORD",
            "weapon_left": "SHIELD_ROUND",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "HEROIC",
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
            "weapon_right": "MACE",
            "weapon_left": "SHIELD_TOWER",
            "cape": "LONG",
            "base_style": "COBBLE",
            "pose": "STAND",
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
            "weapon_right": "AXE",
            "weapon_left": "NONE",
            "cape": "TATTERED",
            "base_style": "ROCK",
            "pose": "COMBAT",
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
            "weapon_right": "BOW",
            "weapon_left": "NONE",
            "cape": "SHORT",
            "base_style": "GRASS",
            "pose": "STRIDE",
            "add_backpack": True,
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
            "weapon_right": "DAGGER",
            "weapon_left": "DAGGER",
            "cape": "NONE",
            "base_style": "COBBLE",
            "pose": "COMBAT",
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
            "weapon_right": "ORB",
            "weapon_left": "NONE",
            "cape": "LONG",
            "base_style": "COBBLE",
            "pose": "CAST",
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
            "weapon_left": "TOME",
            "cape": "TATTERED",
            "base_style": "RUINS",
            "pose": "CAST",
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
            "weapon_left": "SHIELD_ROUND",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "STAND",
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
            "weapon_left": "ORB",
            "cape": "SHORT",
            "base_style": "COBBLE",
            "pose": "STRIDE",
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
            "add_belt": True,
            "add_backpack": True,
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
            "weapon_right": "AXE",
            "weapon_left": "SHIELD_ROUND",
            "cape": "NONE",
            "base_style": "ROCK",
            "pose": "COMBAT",
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
            "weapon_right": "BOW",
            "weapon_left": "NONE",
            "cape": "LONG",
            "base_style": "GRASS",
            "pose": "HEROIC",
            "add_backpack": True,
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
            "weapon_left": "NONE",
            "cape": "SHORT",
            "base_style": "GRASS",
            "pose": "STRIDE",
            "add_belt": True,
            "add_backpack": True,
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
