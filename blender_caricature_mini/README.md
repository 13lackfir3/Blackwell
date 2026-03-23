# Caricature Mini Creator — Blender Plugin

A Blender addon for creating stylised caricature miniatures for tabletop RPGs
and board games, inspired by **HeroForge** and **Eldritch Foundry**.
Design fully customisable hero minis and export them as STL/OBJ files ready
for resin or FDM 3D printing.

---

## Features

| Category | Details |
|---|---|
| **Caricature proportions** | Big-head (≈¼ body height), chunky limbs, exaggerated facial features |
| **Body sliders** | Head size/width/depth, shoulder width, torso length, chest, belly, arm & leg length/thickness, hand & foot size |
| **Face sliders** | Brow ridge, jaw width, nose size, ear size, chin length |
| **Helmets** | None, Open Face, Great Helm, Horned, Crown, Hood, Wizard Hat, Pirate Hat |
| **Armour** | None, Cloth Robes, Leather, Chainmail, Plate, Mage Robes, Bard Tunic |
| **Weapons (R/L hand)** | Sword, Dagger, Axe, Mace, Wand, Staff, Bow, Crossbow, Torch, Round Shield, Tower Shield, Tome, Orb |
| **Cape / Cloak** | None, Short, Long, Tattered |
| **Extras** | Pauldrons, Belt & Pouches, Scabbard, Backpack / Quiver |
| **Base styles** | Flat Disc, Cobblestone, Grassy Ground, Rocky Ground, Ruins |
| **Poses** | Standing, Heroic Stance, Combat Ready, Casting, Kneeling, Mid-Stride |
| **14 presets** | Fighter, Paladin, Barbarian, Ranger, Rogue, Wizard, Sorcerer, Warlock, Cleric, Bard, Druid, Monk, Dwarf, Elf, Halfling, Undead Warrior |
| **Randomise** | One-click random character for inspiration |
| **Export** | STL (for 3D printing) and OBJ, with configurable scale (default 1000× = metres → mm) |

---

## Installation

1. Download or clone this repository.
2. Zip the `blender_caricature_mini/` folder:
   ```
   zip -r blender_caricature_mini.zip blender_caricature_mini/
   ```
3. In Blender: **Edit → Preferences → Add-ons → Install…**
4. Select `blender_caricature_mini.zip` and click **Install Add-on**.
5. Enable the addon by ticking the checkbox next to **"Caricature Mini Creator"**.

---

## Usage

1. Open the **3D Viewport** sidebar (`N` key) and select the **"Mini Creator"** tab.
2. Click **Create Mini** to generate your first caricature figure.
3. Adjust sliders in **Body Proportions** and **Face Features** — the mini
   rebuilds automatically.
4. Choose gear in **Gear & Equipment** and pick a pose.
5. Load a character archetype from **Archetypes & Presets** to instantly
   set a full character build.
6. When satisfied, go to **Export for 3D Printing**, set the output folder,
   and click **Export STL**.

### Tips

- **Scale**: The default export scale of `1000` converts Blender's internal
  metres to millimetres, which is what most slicers (Chitubox, Lychee,
  PrusaSlicer) expect. A 32 mm mini has `total_height = 0.032` m.
- **Subdivision**: A Subdivision Surface modifier (level 1) is added
  automatically. Increase it for smoother prints.
- **Sculpting**: After generating the base, use Blender's sculpt mode to add
  fine details like hair, wrinkles, or engravings.
- **Materials**: Assign materials to the auto-generated object for visual
  previews before printing.
- **Random seed**: Click **Randomise** multiple times for varied characters;
  each click chooses a new random configuration.

---

## File Structure

```
blender_caricature_mini/
├── __init__.py          # Addon entry-point & bl_info
├── properties.py        # All custom property groups (sliders, enums)
├── operators.py         # Create, Rebuild, Clear, Export, Randomise operators
├── panels.py            # Sidebar UI panels
├── mesh_generator.py    # Procedural bmesh geometry for every body part & item
└── presets.py           # 16 character archetype preset definitions
```

---

## Requirements

- Blender **3.6 LTS** or newer (tested up to 4.x)
- No external Python packages required

---

## Roadmap / Future Ideas

- [ ] Shape key system for pose blending without mesh rebuild
- [ ] Hair / beard mesh generator (braids, ponytail, mohawk…)
- [ ] Texture / material zone painting
- [ ] Custom insignia / emblem decal placement
- [ ] Race-specific bodies (orc tusks, tiefling horns/tail, dragonborn scales)
- [ ] Multi-piece sprue layout for batch printing
- [ ] Bone rig generation for animation / render previews
- [ ] Preset export/import (JSON)

---

## License

MIT — free for personal and commercial use.
