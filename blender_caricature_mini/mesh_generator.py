"""
Procedural mesh generation for the Caricature Mini Creator.

All geometry is built with bmesh so there are no external dependencies.
Caricature proportions follow a "4-head-tall" rule:
  - head  ≈ 1/4 total height  (vs ~1/7 for realistic figures)
  - torso ≈ 1/4 total height
  - legs  ≈ 1/2 total height  (shorter than realistic)

All sizes are expressed in metres; scale on export.
"""

import math
import bmesh
import bpy
from mathutils import Vector, Matrix


# ---------------------------------------------------------------------------
# Low-level bmesh helpers
# ---------------------------------------------------------------------------

def _add_uv_sphere(bm, radius=1.0, center=(0, 0, 0), segments=12, rings=8):
    """Add a UV sphere to bm and return the new verts."""
    cx, cy, cz = center
    mat = Matrix.Translation((cx, cy, cz))
    verts_before = set(bm.verts)
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=segments,
        v_segments=rings,
        radius=radius,
        matrix=mat,
        calc_uvs=False,
    )
    bm.verts.ensure_lookup_table()
    return [v for v in bm.verts if v not in verts_before]


def _add_cylinder(bm, radius=0.5, depth=1.0, center=(0, 0, 0),
                  segments=8, cap_ends=True):
    """Add a capped cylinder aligned to Z."""
    cx, cy, cz = center
    mat = Matrix.Translation((cx, cy, cz))
    bmesh.ops.create_cone(
        bm,
        cap_ends=cap_ends,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth,
        matrix=mat,
        calc_uvs=False,
    )


def _add_cone(bm, radius_base=0.5, radius_tip=0.05, depth=1.0,
              center=(0, 0, 0), segments=8):
    cx, cy, cz = center
    mat = Matrix.Translation((cx, cy, cz))
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius_base,
        radius2=radius_tip,
        depth=depth,
        matrix=mat,
        calc_uvs=False,
    )


def _add_box(bm, size_x=1.0, size_y=1.0, size_z=1.0, center=(0, 0, 0)):
    cx, cy, cz = center
    mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Scale(1, 4)
    # Use bmesh box via create_cube + scale
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat, calc_uvs=False)
    # Scale the most-recently added verts
    # Simpler: just use create_cone with matching radii (box-like)
    # Actually we'll use a scaled cube approach via the matrix
    # This is a no-op hack; just rebuild with proper matrix
    pass


def _add_scaled_cube(bm, sx, sy, sz, center=(0, 0, 0)):
    cx, cy, cz = center
    mat = (
        Matrix.Translation((cx, cy, cz))
        @ Matrix.Scale(sx, 4, (1, 0, 0))
        @ Matrix.Scale(sy, 4, (0, 1, 0))
        @ Matrix.Scale(sz, 4, (0, 0, 1))
    )
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat, calc_uvs=False)


def _merge_close(bm, dist=0.0001):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)


# ---------------------------------------------------------------------------
# Skin-modifier body builder
# ---------------------------------------------------------------------------

def _build_skin_body(body_props):
    """Build the character body using Blender's Skin modifier for a smooth,
    connected mesh — similar to how professional mini creators work with a
    base mesh + morph targets.

    Creates a skeleton of vertices with edges connecting them at anatomical
    joints, sets per-vertex radii via the Skin vertex layer, then bakes the
    Skin + Subdivision modifiers via the depsgraph to produce a smooth mesh.

    Returns (bpy.types.Object, dict) — the baked body object and a landmark
    dict with Z/X positions needed for gear placement.
    """
    H = body_props.total_height

    # -- Proportions derived from sliders --------------------------------
    head_r    = H * 0.135 * body_props.head_scale
    head_w    = body_props.head_width
    head_d    = body_props.head_depth
    neck_r    = H * 0.038
    neck_h    = H * 0.048
    torso_h   = H * 0.24 * body_props.torso_length
    sw        = body_props.shoulder_width
    shoulder_w = H * 0.115 * sw
    hip_w     = H * 0.090
    belly     = max(body_props.belly, 0)
    chest     = max(body_props.chest, 0)
    arm_len_u = H * 0.13 * body_props.arm_length
    arm_len_l = H * 0.11 * body_props.arm_length
    arm_r     = H * 0.024 * body_props.arm_thickness
    hand_r_s  = H * 0.030 * body_props.hand_size
    leg_len_u = H * 0.22 * body_props.leg_length
    leg_len_l = H * 0.20 * body_props.leg_length
    leg_r     = H * 0.040 * body_props.leg_thickness
    foot_r    = H * 0.032 * body_props.foot_size

    # -- Key Z positions -------------------------------------------------
    base_z       = 0.0
    foot_z       = base_z + H * 0.01
    ankle_z      = foot_z + foot_r * 1.2
    knee_z       = ankle_z + leg_len_l
    hip_z        = knee_z + leg_len_u
    torso_bot_z  = hip_z
    waist_z      = torso_bot_z + torso_h * 0.44
    chest_z      = torso_bot_z + torso_h * 0.78
    shoulder_z   = torso_bot_z + torso_h
    neck_bot_z   = shoulder_z
    neck_top_z   = neck_bot_z + neck_h
    head_ctr_z   = neck_top_z + head_r
    head_top_z   = neck_top_z + head_r * 2.0

    # -- Build skeleton mesh with bmesh ----------------------------------
    bm = bmesh.new()

    # Ensure skin data layer exists
    if not bm.verts.layers.skin:
        bm.verts.layers.skin.new()
    skin_layer = bm.verts.layers.skin[0]

    verts = {}  # name → BMVert

    def add_vert(name, co, rx, ry):
        """Add a vertex and set its skin radii."""
        v = bm.verts.new(co)
        sd = v[skin_layer]
        sd.radius = (rx, ry)
        verts[name] = v
        return v

    def connect(a, b):
        bm.edges.new((verts[a], verts[b]))

    # --- Spine (bottom→top) ---
    pelvis_rx = hip_w * 0.9
    pelvis_ry = hip_w * 0.65 + belly * H * 0.012
    add_vert("pelvis", (0, 0, hip_z), pelvis_rx, pelvis_ry)

    waist_rx = hip_w * 0.7
    waist_ry = hip_w * 0.55 + belly * H * 0.016
    add_vert("waist", (0, belly * H * 0.003, waist_z), waist_rx, waist_ry)
    connect("pelvis", "waist")

    chest_rx = shoulder_w * 0.85
    chest_ry = hip_w * 0.65 + chest * H * 0.014
    add_vert("chest", (0, chest * H * 0.002, chest_z), chest_rx, chest_ry)
    connect("waist", "chest")

    shoulder_rx = shoulder_w * 0.80
    shoulder_ry = hip_w * 0.50
    add_vert("shoulders", (0, 0, shoulder_z), shoulder_rx, shoulder_ry)
    connect("chest", "shoulders")

    # Neck
    add_vert("neck_bot", (0, 0, neck_bot_z), neck_r, neck_r)
    connect("shoulders", "neck_bot")
    add_vert("neck_top", (0, 0, neck_top_z), neck_r * 0.9, neck_r * 0.9)
    connect("neck_bot", "neck_top")

    # Head
    head_rx = head_r * head_w
    head_ry = head_r * head_d
    add_vert("head_center", (0, 0, head_ctr_z), head_rx, head_ry)
    connect("neck_top", "head_center")
    add_vert("head_top", (0, 0, head_top_z), head_rx * 0.7, head_ry * 0.7)
    connect("head_center", "head_top")

    # Jaw / chin branch
    chin_len = body_props.chin_length * head_r * 0.2
    jaw_w = body_props.jaw_width
    chin_rx = head_rx * (0.35 + jaw_w * 0.15)
    chin_ry = head_ry * 0.30
    add_vert("chin", (0, head_ry * 0.15, head_ctr_z - head_r * 0.7 - chin_len),
             chin_rx, chin_ry)
    connect("head_center", "chin")

    # Brow ridge branch
    brow = body_props.brow_ridge
    brow_y = head_ry * 0.85 + brow * head_r * 0.12
    add_vert("brow", (0, brow_y, head_ctr_z + head_r * 0.35),
             head_rx * 0.65, head_r * 0.15)
    connect("head_center", "brow")

    # Nose branch
    ns = body_props.nose_size
    nose_r = head_r * 0.08 + ns * head_r * 0.10
    add_vert("nose", (0, head_ry + nose_r * 0.6, head_ctr_z - head_r * 0.15),
             nose_r, nose_r)
    connect("head_center", "nose")

    # Ear branches
    ear_s = body_props.ear_size
    ear_r = head_r * 0.06 + ear_s * head_r * 0.08
    for side_name, sx in (("ear_L", -1), ("ear_R", 1)):
        add_vert(side_name, (sx * (head_rx + ear_r * 0.3), 0, head_ctr_z),
                 ear_r, ear_r * 0.5)
        connect("head_center", side_name)

    # --- Arms (both sides) ---
    for side_name, sx in (("R", 1), ("L", -1)):
        s_x = sx * shoulder_w
        add_vert(f"shoulder_{side_name}", (s_x, 0, shoulder_z),
                 arm_r * 1.4, arm_r * 1.4)
        connect("shoulders", f"shoulder_{side_name}")

        elbow_z = shoulder_z - arm_len_u
        elbow_x = sx * (shoulder_w + arm_r * 0.5)
        add_vert(f"elbow_{side_name}", (elbow_x, 0, elbow_z),
                 arm_r * 0.9, arm_r * 0.9)
        connect(f"shoulder_{side_name}", f"elbow_{side_name}")

        wrist_z = elbow_z - arm_len_l
        wrist_x = elbow_x + sx * arm_len_l * 0.06
        add_vert(f"wrist_{side_name}", (wrist_x, arm_len_l * 0.03, wrist_z),
                 arm_r * 0.7, arm_r * 0.7)
        connect(f"elbow_{side_name}", f"wrist_{side_name}")

        hand_x = wrist_x + sx * hand_r_s * 0.3
        hand_z = wrist_z - hand_r_s * 0.8
        add_vert(f"hand_{side_name}", (hand_x, arm_len_l * 0.05, hand_z),
                 hand_r_s, hand_r_s * 0.7)
        connect(f"wrist_{side_name}", f"hand_{side_name}")

    # --- Legs (both sides) ---
    for side_name, sx in (("R", 1), ("L", -1)):
        hip_x = sx * hip_w * 0.55
        add_vert(f"hip_{side_name}", (hip_x, 0, hip_z),
                 leg_r * 1.1, leg_r * 1.1)
        connect("pelvis", f"hip_{side_name}")

        add_vert(f"knee_{side_name}", (hip_x, 0, knee_z),
                 leg_r * 0.85, leg_r * 0.85)
        connect(f"hip_{side_name}", f"knee_{side_name}")

        add_vert(f"ankle_{side_name}", (hip_x, 0, ankle_z),
                 leg_r * 0.55, leg_r * 0.55)
        connect(f"knee_{side_name}", f"ankle_{side_name}")

        # Foot — forward-pointing
        add_vert(f"toe_{side_name}", (hip_x, foot_r * 1.6, foot_z),
                 foot_r * 0.6, foot_r * 0.35)
        connect(f"ankle_{side_name}", f"toe_{side_name}")

    # Mark the pelvis as the root of the skin skeleton
    verts["pelvis"][skin_layer].use_root = True

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    # --- Write skeleton to a temporary mesh object ----------------------
    skel_mesh = bpy.data.meshes.new("_SkinBody_skeleton")
    bm.to_mesh(skel_mesh)
    bm.free()
    skel_mesh.update()

    skel_obj = bpy.data.objects.new("_SkinBody", skel_mesh)

    # Add Skin modifier
    skin_mod = skel_obj.modifiers.new(name="Skin", type="SKIN")

    # Add Subdivision for smoothness
    sub_mod = skel_obj.modifiers.new(name="Subdivision", type="SUBSURF")
    sub_mod.levels = 2
    sub_mod.render_levels = 2

    # --- Bake modifiers via depsgraph -----------------------------------
    # Temporarily link to scene so depsgraph can evaluate
    scene_col = bpy.context.scene.collection
    scene_col.objects.link(skel_obj)
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = skel_obj.evaluated_get(depsgraph)
    baked_mesh = bpy.data.meshes.new_from_object(eval_obj)

    # Clean up the temporary skeleton object
    scene_col.objects.unlink(skel_obj)
    bpy.data.objects.remove(skel_obj, do_unlink=True)
    bpy.data.meshes.remove(skel_mesh)

    # Create the final body object with the baked mesh
    body_obj = bpy.data.objects.new("_SkinBody_baked", baked_mesh)

    # Build landmarks dict for gear placement
    arm_x = shoulder_w + arm_r * 0.5
    arm_total = arm_len_u + arm_len_l
    hand_z_val = shoulder_z - arm_total
    landmarks = {
        "H": H,
        "head_r": head_r,
        "head_top_z": head_top_z,
        "head_center_z": head_ctr_z,
        "neck_top_z": neck_top_z,
        "shoulder_z": shoulder_z,
        "shoulder_w": shoulder_w,
        "torso_top_z": shoulder_z,
        "torso_bottom_z": torso_bot_z,
        "hand_z": hand_z_val,
        "hand_y": arm_len_l * 0.05,
        "arm_x": arm_x,
        "hip_z": hip_z,
        "base_z": base_z,
    }

    return body_obj, landmarks


# ---------------------------------------------------------------------------
# Gear / accessory builders
# ---------------------------------------------------------------------------

def _build_helmet(bm, props, head_top_z, head_r):
    style = props.helmet
    if style == "NONE":
        return

    helmet_z = head_top_z - head_r * 0.3

    if style == "OPEN_FACE":
        _add_uv_sphere(
            bm, radius=head_r * 1.08,
            center=(0, 0, helmet_z),
            segments=12, rings=7,
        )

    elif style == "GREAT_HELM":
        _add_cylinder(
            bm, radius=head_r * 1.1, depth=head_r * 1.5,
            center=(0, 0, helmet_z + head_r * 0.5), segments=10,
        )

    elif style == "HORNED":
        # Base helm
        _add_uv_sphere(
            bm, radius=head_r * 1.07,
            center=(0, 0, helmet_z),
            segments=12, rings=7,
        )
        # Horns
        for side in (-1, 1):
            _add_cone(
                bm,
                radius_base=head_r * 0.12,
                radius_tip=0.001,
                depth=head_r * 0.9,
                center=(side * head_r * 0.7, 0, helmet_z + head_r * 0.5),
                segments=6,
            )

    elif style == "CROWN":
        # Band
        _add_cylinder(
            bm, radius=head_r * 1.07, depth=head_r * 0.22,
            center=(0, 0, helmet_z + head_r * 0.5), segments=10,
        )
        # Crown points (5 small cones around top)
        for i in range(5):
            angle = i * (2 * math.pi / 5)
            cx = math.cos(angle) * head_r * 0.95
            cy = math.sin(angle) * head_r * 0.95
            _add_cone(
                bm,
                radius_base=head_r * 0.09,
                radius_tip=0.001,
                depth=head_r * 0.35,
                center=(cx, cy, helmet_z + head_r * 0.65),
                segments=5,
            )

    elif style == "HOOD":
        # Soft dome with fabric tuck at sides
        _add_uv_sphere(
            bm, radius=head_r * 1.06,
            center=(0, 0, helmet_z),
            segments=12, rings=8,
        )

    elif style == "WIZARD_HAT":
        _add_cone(
            bm,
            radius_base=head_r * 1.15,
            radius_tip=0.002,
            depth=head_r * 2.2,
            center=(0, 0, helmet_z + head_r * 1.0),
            segments=10,
        )

    elif style == "PIRATE_HAT":
        # Brim + raised crown
        _add_cylinder(
            bm, radius=head_r * 1.4, depth=head_r * 0.1,
            center=(0, 0, helmet_z + head_r * 0.4), segments=12,
        )
        _add_scaled_cube(
            bm, head_r * 0.7, head_r * 1.3, head_r * 0.6,
            center=(0, 0, helmet_z + head_r * 0.75),
        )


def _build_armor_layer(bm, props_body, props_gear, torso_bottom_z, torso_top_z):
    style = props_gear.armor
    if style == "NONE":
        return

    H = props_body.total_height
    sw = props_body.shoulder_width
    torso_h = torso_top_z - torso_bottom_z
    hw = H * 0.085  # hip width
    shw = H * 0.11 * sw  # shoulder width

    if style in ("LEATHER", "CHAINMAIL", "PLATE"):
        # Chest piece: scaled cube slightly larger than torso
        scale = 1.05 if style == "LEATHER" else 1.08 if style == "CHAINMAIL" else 1.12
        _add_scaled_cube(
            bm,
            shw * scale, H * 0.065 * scale, torso_h * 0.85,
            center=(0, 0, torso_bottom_z + torso_h * 0.5),
        )
        if style == "PLATE":
            # Shoulder pauldrons (large)
            pauldron_r = H * 0.045
            for side in (-1, 1):
                _add_uv_sphere(
                    bm, radius=pauldron_r,
                    center=(side * (shw + pauldron_r * 0.6), 0, torso_top_z - pauldron_r * 0.2),
                    segments=8, rings=5,
                )

    elif style in ("CLOTH", "ROBE_MAGE", "BARD_TUNIC"):
        # Flowing robe – wider tapered cone from waist to feet
        robe_len = torso_h * (2.5 if style == "ROBE_MAGE" else 1.8)
        _add_cone(
            bm,
            radius_base=hw * (2.0 if style == "ROBE_MAGE" else 1.5),
            radius_tip=shw * 0.95,
            depth=robe_len,
            center=(0, 0, torso_bottom_z - robe_len * 0.3),
            segments=12,
        )

    # Optional pauldrons toggle
    if props_gear.add_pauldrons:
        pauldron_r = H * 0.038
        for side in (-1, 1):
            _add_uv_sphere(
                bm, radius=pauldron_r,
                center=(side * (shw + pauldron_r * 0.5), 0, torso_top_z - pauldron_r * 0.3),
                segments=8, rings=5,
            )

    # Belt
    if props_gear.add_belt:
        belt_z = torso_bottom_z + torso_h * 0.1
        _add_cylinder(
            bm, radius=hw * 1.12, depth=H * 0.018,
            center=(0, 0, belt_z), segments=12,
        )
        # Pouches
        for angle in (0.4, -0.4, 1.0):
            px = math.sin(angle) * hw * 1.1
            py = math.cos(angle) * hw * 1.1
            _add_scaled_cube(
                bm, H * 0.018, H * 0.012, H * 0.025,
                center=(px, py, belt_z),
            )


def _build_cape(bm, props_body, props_gear, torso_top_z, torso_bottom_z):
    style = props_gear.cape
    if style == "NONE":
        return

    H = props_body.total_height
    sw = props_body.shoulder_width
    shw = H * 0.11 * sw
    cape_w = shw * 1.2

    lengths = {"SHORT": H * 0.22, "LONG": H * 0.48, "TATTERED": H * 0.44}
    cape_len = lengths.get(style, H * 0.3)

    # Simple tapered panel behind the figure
    _add_cone(
        bm,
        radius_base=cape_w * 0.55,
        radius_tip=cape_w * (0.3 if style != "TATTERED" else 0.05),
        depth=cape_len,
        center=(0, -H * 0.05, torso_top_z - cape_len * 0.5),
        segments=10,
    )


def _build_weapon(bm, item, hand_x, hand_y, hand_z, side, H):
    """Place a weapon / held-item mesh at the given hand position."""
    if item == "NONE":
        return

    hx, hy, hz = hand_x, hand_y, hand_z
    hr = H * 0.010   # handle radius
    br = H * 0.008   # blade radius

    # ------------------------------------------------------------------ Swords
    if item in ("SWORD", "SHORTSWORD"):
        blade_len = H * (0.26 if item == "SWORD" else 0.18)
        _add_cylinder(bm, radius=hr, depth=H * 0.06, center=(hx, hy, hz + H * 0.03), segments=5)
        _add_cylinder(bm, radius=H * 0.022, depth=H * 0.008, center=(hx, hy, hz + H * 0.065), segments=8)
        _add_cone(bm, radius_base=br, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.065 + blade_len * 0.5), segments=5)

    elif item == "LONGSWORD":
        blade_len = H * 0.36
        _add_cylinder(bm, radius=hr * 1.1, depth=H * 0.09, center=(hx, hy, hz + H * 0.045), segments=5)
        _add_cylinder(bm, radius=H * 0.028, depth=H * 0.009, center=(hx, hy, hz + H * 0.095), segments=8)
        _add_cone(bm, radius_base=br * 1.1, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.095 + blade_len * 0.5), segments=5)

    elif item == "GREATSWORD":
        blade_len = H * 0.54
        _add_cylinder(bm, radius=hr * 1.3, depth=H * 0.12, center=(hx, hy, hz + H * 0.06), segments=5)
        # Long crossguard
        _add_scaled_cube(bm, H * 0.10, H * 0.010, H * 0.012, center=(hx, hy, hz + H * 0.130))
        _add_cone(bm, radius_base=br * 1.4, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.130 + blade_len * 0.5), segments=5)

    elif item == "RAPIER":
        blade_len = H * 0.35
        _add_cylinder(bm, radius=hr * 0.8, depth=H * 0.07, center=(hx, hy, hz + H * 0.035), segments=5)
        # Swept guard – ring disc
        _add_cylinder(bm, radius=H * 0.030, depth=H * 0.005, center=(hx, hy, hz + H * 0.075), segments=12)
        _add_cone(bm, radius_base=br * 0.5, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.075 + blade_len * 0.5), segments=5)

    elif item == "SCIMITAR":
        blade_len = H * 0.28
        _add_cylinder(bm, radius=hr, depth=H * 0.06, center=(hx, hy, hz + H * 0.03), segments=5)
        _add_cylinder(bm, radius=H * 0.018, depth=H * 0.008, center=(hx, hy, hz + H * 0.065), segments=6)
        # Curved blade: two overlapping angled cones
        _add_cone(bm, radius_base=br * 1.3, radius_tip=0.001, depth=blade_len,
                  center=(hx + side * H * 0.018, hy, hz + H * 0.065 + blade_len * 0.5), segments=5)

    elif item == "KATANA":
        blade_len = H * 0.38
        _add_cylinder(bm, radius=hr * 0.9, depth=H * 0.10, center=(hx, hy, hz + H * 0.05), segments=5)
        # Round tsuba guard
        _add_cylinder(bm, radius=H * 0.020, depth=H * 0.007, center=(hx, hy, hz + H * 0.105), segments=10)
        _add_cone(bm, radius_base=br * 0.9, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.105 + blade_len * 0.5), segments=5)

    elif item == "DAGGER":
        blade_len = H * 0.14
        _add_cylinder(bm, radius=hr, depth=H * 0.05, center=(hx, hy, hz + H * 0.025), segments=5)
        _add_cylinder(bm, radius=H * 0.016, depth=H * 0.007, center=(hx, hy, hz + H * 0.055), segments=6)
        _add_cone(bm, radius_base=br, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.055 + blade_len * 0.5), segments=5)

    elif item == "PARRYING_DAGGER":
        blade_len = H * 0.16
        _add_cylinder(bm, radius=hr, depth=H * 0.055, center=(hx, hy, hz + H * 0.027), segments=5)
        # Wide parrying prongs
        _add_scaled_cube(bm, H * 0.06, H * 0.008, H * 0.010, center=(hx, hy, hz + H * 0.060))
        _add_cone(bm, radius_base=br, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.065 + blade_len * 0.5), segments=5)

    # ------------------------------------------------------------------ Axes
    elif item in ("AXE", "HATCHET"):
        shaft_len = H * (0.22 if item == "AXE" else 0.16)
        head_w = H * (0.06 if item == "AXE" else 0.045)
        _add_cylinder(bm, radius=hr, depth=shaft_len, center=(hx, hy, hz + shaft_len * 0.5), segments=5)
        _add_scaled_cube(bm, head_w, H * 0.020, H * 0.08, center=(hx + side * head_w * 0.5, hy, hz + shaft_len))

    elif item == "BATTLEAXE":
        _add_cylinder(bm, radius=hr * 1.2, depth=H * 0.30, center=(hx, hy, hz + H * 0.15), segments=5)
        # Double-headed: two mirrored axe heads
        for s in (-1, 1):
            _add_scaled_cube(bm, H * 0.075, H * 0.022, H * 0.12,
                             center=(hx + s * H * 0.038, hy, hz + H * 0.30))

    # ------------------------------------------------------------------ Blunt
    elif item == "MACE":
        _add_cylinder(bm, radius=hr, depth=H * 0.20, center=(hx, hy, hz + H * 0.10), segments=5)
        _add_uv_sphere(bm, radius=H * 0.030, center=(hx, hy, hz + H * 0.22), segments=8, rings=5)
        # Flanges: 6 small fins
        for i in range(6):
            angle = i * (math.pi / 3)
            fx = math.cos(angle) * H * 0.022
            fy = math.sin(angle) * H * 0.022
            _add_scaled_cube(bm, H * 0.006, H * 0.020, H * 0.022,
                             center=(hx + fx, hy + fy, hz + H * 0.22))

    elif item == "WARHAMMER":
        _add_cylinder(bm, radius=hr * 1.1, depth=H * 0.26, center=(hx, hy, hz + H * 0.13), segments=5)
        # Hammer head + poll spike
        _add_scaled_cube(bm, H * 0.045, H * 0.035, H * 0.065, center=(hx, hy, hz + H * 0.27))
        _add_cone(bm, radius_base=H * 0.010, radius_tip=0.001, depth=H * 0.040,
                  center=(hx, hy, hz + H * 0.310), segments=5)

    elif item == "MAUL":
        _add_cylinder(bm, radius=hr * 1.3, depth=H * 0.35, center=(hx, hy, hz + H * 0.175), segments=5)
        _add_scaled_cube(bm, H * 0.060, H * 0.050, H * 0.085, center=(hx, hy, hz + H * 0.39))

    elif item == "FLAIL":
        # Handle
        _add_cylinder(bm, radius=hr, depth=H * 0.16, center=(hx, hy, hz + H * 0.08), segments=5)
        # Chain link cylinders
        for i in range(4):
            link_z = hz + H * 0.16 + i * H * 0.032
            _add_cylinder(bm, radius=H * 0.006, depth=H * 0.025, center=(hx, hy, link_z), segments=5)
        # Spiked ball
        ball_z = hz + H * 0.16 + 4 * H * 0.032 + H * 0.018
        _add_uv_sphere(bm, radius=H * 0.025, center=(hx, hy, ball_z), segments=7, rings=5)
        for i in range(8):
            angle = i * (math.pi / 4)
            sx = math.cos(angle) * H * 0.018
            sy = math.sin(angle) * H * 0.018
            _add_cone(bm, radius_base=H * 0.004, radius_tip=0.001, depth=H * 0.018,
                      center=(hx + sx, hy + sy, ball_z), segments=4)

    elif item == "MORNINGSTAR":
        _add_cylinder(bm, radius=hr, depth=H * 0.20, center=(hx, hy, hz + H * 0.10), segments=5)
        _add_uv_sphere(bm, radius=H * 0.026, center=(hx, hy, hz + H * 0.22), segments=7, rings=5)
        for i in range(6):
            angle = i * (math.pi / 3)
            sx = math.cos(angle) * H * 0.018
            sy = math.sin(angle) * H * 0.018
            _add_cone(bm, radius_base=H * 0.005, radius_tip=0.001, depth=H * 0.022,
                      center=(hx + sx, hy + sy, hz + H * 0.22), segments=4)

    elif item == "CLUB":
        _add_cone(bm, radius_base=H * 0.022, radius_tip=hr, depth=H * 0.25,
                  center=(hx, hy, hz + H * 0.125), segments=6)

    # ------------------------------------------------------------------ Polearms
    elif item == "SPEAR":
        _add_cylinder(bm, radius=hr * 0.8, depth=H * 0.55, center=(hx, hy, hz + H * 0.275), segments=6)
        _add_cone(bm, radius_base=br * 1.1, radius_tip=0.001, depth=H * 0.12,
                  center=(hx, hy, hz + H * 0.55 + H * 0.06), segments=5)

    elif item == "HALBERD":
        _add_cylinder(bm, radius=hr * 0.9, depth=H * 0.55, center=(hx, hy, hz + H * 0.275), segments=6)
        # Axe blade
        _add_scaled_cube(bm, H * 0.07, H * 0.018, H * 0.10,
                         center=(hx + side * H * 0.035, hy, hz + H * 0.55))
        # Top spike
        _add_cone(bm, radius_base=br, radius_tip=0.001, depth=H * 0.10,
                  center=(hx, hy, hz + H * 0.60), segments=5)
        # Back hook
        _add_cone(bm, radius_base=H * 0.008, radius_tip=0.001, depth=H * 0.045,
                  center=(hx - side * H * 0.020, hy, hz + H * 0.56), segments=4)

    elif item == "TRIDENT":
        _add_cylinder(bm, radius=hr * 0.9, depth=H * 0.46, center=(hx, hy, hz + H * 0.23), segments=6)
        for dx in (-H * 0.025, 0, H * 0.025):
            prong_len = H * (0.12 if dx == 0 else 0.10)
            _add_cone(bm, radius_base=br * 0.8, radius_tip=0.001, depth=prong_len,
                      center=(hx + dx, hy, hz + H * 0.46 + prong_len * 0.5), segments=4)

    elif item == "SCYTHE":
        # Long pole
        _add_cylinder(bm, radius=hr * 0.9, depth=H * 0.55, center=(hx, hy, hz + H * 0.275), segments=6)
        # Curved blade approximated with a rotated/offset cone
        _add_cone(bm, radius_base=br * 1.5, radius_tip=0.001, depth=H * 0.30,
                  center=(hx + side * H * 0.06, hy, hz + H * 0.56 + H * 0.12),
                  segments=5)

    elif item == "LANCE":
        _add_cone(bm, radius_base=hr * 1.5, radius_tip=H * 0.005, depth=H * 0.65,
                  center=(hx, hy, hz + H * 0.325), segments=8)

    elif item == "GLAIVE":
        _add_cylinder(bm, radius=hr * 0.9, depth=H * 0.52, center=(hx, hy, hz + H * 0.26), segments=6)
        _add_cone(bm, radius_base=br * 1.6, radius_tip=0.001, depth=H * 0.22,
                  center=(hx + side * H * 0.02, hy, hz + H * 0.52 + H * 0.11), segments=5)

    elif item == "JAVELIN":
        _add_cylinder(bm, radius=hr * 0.7, depth=H * 0.40, center=(hx, hy, hz + H * 0.20), segments=5)
        _add_cone(bm, radius_base=br, radius_tip=0.001, depth=H * 0.08,
                  center=(hx, hy, hz + H * 0.44), segments=5)

    # ------------------------------------------------------------------ Ranged
    elif item in ("BOW", "LONGBOW"):
        bow_half = H * (0.18 if item == "LONGBOW" else 0.13)
        bow_r = hr * (0.7 if item == "LONGBOW" else 0.6)
        # Upper + lower limb
        for dz in (bow_half, -bow_half):
            _add_cylinder(bm, radius=bow_r, depth=bow_half * 1.5,
                          center=(hx, hy + H * 0.012, hz + dz * 0.5), segments=5)
        # Bowstring
        _add_cylinder(bm, radius=H * 0.002, depth=bow_half * 3.2,
                      center=(hx, hy - H * 0.018, hz), segments=4)

    elif item in ("CROSSBOW", "HAND_CROSSBOW"):
        stock_w = H * (0.11 if item == "CROSSBOW" else 0.07)
        _add_scaled_cube(bm, stock_w, H * 0.030, H * 0.030, center=(hx, hy, hz + H * 0.06))
        # Prod / bow arms
        arm_len = stock_w * 0.8
        for dx in (-arm_len, arm_len):
            _add_cylinder(bm, radius=H * 0.005, depth=arm_len,
                          center=(hx + dx * 0.5, hy - H * 0.010, hz + H * 0.07), segments=4)

    elif item == "SLING":
        # Leather pouch and two cords
        _add_uv_sphere(bm, radius=H * 0.016, center=(hx, hy, hz + H * 0.04), segments=6, rings=4)
        for dx in (-H * 0.008, H * 0.008):
            _add_cylinder(bm, radius=H * 0.003, depth=H * 0.18,
                          center=(hx + dx, hy, hz + H * 0.13), segments=4)

    elif item == "THROWING_KNIFE":
        _add_cone(bm, radius_base=br * 0.8, radius_tip=0.001, depth=H * 0.12,
                  center=(hx, hy, hz + H * 0.06), segments=5)

    # ------------------------------------------------------------------ Arcane / utility
    elif item == "WAND":
        _add_cone(bm, radius_base=hr, radius_tip=H * 0.006, depth=H * 0.18,
                  center=(hx, hy, hz + H * 0.09), segments=6)
        _add_uv_sphere(bm, radius=H * 0.018, center=(hx, hy, hz + H * 0.20), segments=6, rings=4)

    elif item == "STAFF":
        _add_cylinder(bm, radius=hr * 1.1, depth=H * 0.55, center=(hx, hy, hz + H * 0.275), segments=6)
        _add_uv_sphere(bm, radius=H * 0.025, center=(hx, hy, hz + H * 0.565), segments=8, rings=5)

    elif item == "SCEPTRE":
        _add_cylinder(bm, radius=hr * 1.1, depth=H * 0.24, center=(hx, hy, hz + H * 0.12), segments=6)
        _add_uv_sphere(bm, radius=H * 0.028, center=(hx, hy, hz + H * 0.255), segments=8, rings=5)
        # Crown ring around gem
        _add_cylinder(bm, radius=H * 0.032, depth=H * 0.010,
                      center=(hx, hy, hz + H * 0.255), segments=10)

    elif item == "TORCH":
        _add_cylinder(bm, radius=hr, depth=H * 0.16, center=(hx, hy, hz + H * 0.08), segments=5)
        _add_cone(bm, radius_base=H * 0.020, radius_tip=0.001, depth=H * 0.06,
                  center=(hx, hy, hz + H * 0.19), segments=6)

    elif item == "LANTERN":
        # Handle rod
        _add_cylinder(bm, radius=H * 0.006, depth=H * 0.08, center=(hx, hy, hz + H * 0.04), segments=5)
        # Lantern body (hexagonal cage approx with scaled cube)
        _add_scaled_cube(bm, H * 0.030, H * 0.030, H * 0.045, center=(hx, hy, hz + H * 0.11))
        # Top cap
        _add_cone(bm, radius_base=H * 0.018, radius_tip=H * 0.006, depth=H * 0.025,
                  center=(hx, hy, hz + H * 0.138), segments=6)

    # ------------------------------------------------------------------ Exotic
    elif item == "WHIP":
        # Handle
        _add_cylinder(bm, radius=hr, depth=H * 0.10, center=(hx, hy, hz + H * 0.05), segments=5)
        # Coiled portion (ring torus approximated as stacked small spheres)
        for i in range(6):
            angle = i * (math.pi / 3)
            cx = math.cos(angle) * H * 0.025
            cy = math.sin(angle) * H * 0.025
            _add_uv_sphere(bm, radius=H * 0.008, center=(hx + cx, hy + cy, hz + H * 0.14),
                           segments=5, rings=3)
        # Tip trailing down
        _add_cylinder(bm, radius=H * 0.003, depth=H * 0.09, center=(hx, hy, hz + H * 0.20), segments=4)

    elif item == "SICKLE":
        _add_cylinder(bm, radius=hr, depth=H * 0.12, center=(hx, hy, hz + H * 0.06), segments=5)
        _add_cylinder(bm, radius=H * 0.016, depth=H * 0.007, center=(hx, hy, hz + H * 0.125), segments=6)
        _add_cone(bm, radius_base=br * 1.2, radius_tip=0.001, depth=H * 0.14,
                  center=(hx + side * H * 0.025, hy, hz + H * 0.175), segments=5)

    elif item == "NET":
        # Bunched-up net ball in hand
        _add_uv_sphere(bm, radius=H * 0.030, center=(hx, hy, hz + H * 0.035), segments=8, rings=5)
        # A few rope strands dangling
        for dx in (-H * 0.012, 0, H * 0.012):
            _add_cylinder(bm, radius=H * 0.003, depth=H * 0.06,
                          center=(hx + dx, hy, hz + H * 0.06 + H * 0.03), segments=4)

    elif item == "PISTOL":
        # Barrel
        _add_cylinder(bm, radius=H * 0.008, depth=H * 0.12, center=(hx, hy + H * 0.04, hz + H * 0.06), segments=6)
        # Grip
        _add_scaled_cube(bm, H * 0.018, H * 0.012, H * 0.06, center=(hx, hy, hz + H * 0.03))
        # Hammer / flintlock
        _add_scaled_cube(bm, H * 0.010, H * 0.020, H * 0.018, center=(hx, hy + H * 0.010, hz + H * 0.07))

    elif item == "RIFLE":
        # Long barrel
        _add_cylinder(bm, radius=H * 0.008, depth=H * 0.42, center=(hx, hy + H * 0.06, hz + H * 0.12), segments=6)
        # Stock
        _add_scaled_cube(bm, H * 0.020, H * 0.015, H * 0.18, center=(hx, hy, hz + H * 0.09))
        # Lock mechanism
        _add_scaled_cube(bm, H * 0.012, H * 0.022, H * 0.022, center=(hx, hy + H * 0.012, hz + H * 0.12))

    elif item == "GUNBLADE":
        # Sword blade + pistol integrated
        blade_len = H * 0.30
        _add_cylinder(bm, radius=hr * 1.1, depth=H * 0.08, center=(hx, hy, hz + H * 0.04), segments=5)
        _add_cylinder(bm, radius=H * 0.024, depth=H * 0.009, center=(hx, hy, hz + H * 0.085), segments=8)
        _add_cone(bm, radius_base=br * 1.3, radius_tip=0.001, depth=blade_len,
                  center=(hx, hy, hz + H * 0.085 + blade_len * 0.5), segments=5)
        # Pistol barrel under the guard
        _add_cylinder(bm, radius=H * 0.007, depth=H * 0.10,
                      center=(hx + side * H * 0.010, hy + H * 0.008, hz + H * 0.085 + H * 0.05), segments=5)

    # ------------------------------------------------------------------ Shields / off-hand
    elif item in ("SHIELD_ROUND", "SHIELD_KITE", "SHIELD_SPIKED"):
        depth = H * 0.015
        if item == "SHIELD_ROUND":
            _add_cylinder(bm, radius=H * 0.055, depth=depth,
                          center=(hx, hy - depth, hz + H * 0.05), segments=10)
            # Boss
            _add_uv_sphere(bm, radius=H * 0.014, center=(hx, hy - depth * 2, hz + H * 0.05),
                           segments=6, rings=4)
        elif item == "SHIELD_KITE":
            # Tapered heater shape (wider top, pointed bottom)
            _add_cone(bm, radius_base=H * 0.055, radius_tip=H * 0.010, depth=H * 0.18,
                      center=(hx, hy - depth, hz + H * 0.06), segments=8)
        elif item == "SHIELD_SPIKED":
            _add_cylinder(bm, radius=H * 0.055, depth=depth,
                          center=(hx, hy - depth, hz + H * 0.05), segments=10)
            _add_cone(bm, radius_base=H * 0.010, radius_tip=0.001, depth=H * 0.040,
                      center=(hx, hy - depth * 3, hz + H * 0.05), segments=5)

    elif item == "SHIELD_TOWER":
        depth = H * 0.015
        _add_scaled_cube(bm, H * 0.07, depth, H * 0.18, center=(hx, hy - depth, hz + H * 0.06))

    # ------------------------------------------------------------------ Held items
    elif item == "TOME":
        _add_scaled_cube(bm, H * 0.040, H * 0.015, H * 0.055, center=(hx, hy, hz + H * 0.03))
        # Spine and clasp
        _add_scaled_cube(bm, H * 0.005, H * 0.017, H * 0.057, center=(hx - H * 0.022, hy, hz + H * 0.03))
        _add_cylinder(bm, radius=H * 0.005, depth=H * 0.005,
                      center=(hx + H * 0.022, hy, hz + H * 0.03), segments=5)

    elif item == "ORB":
        _add_uv_sphere(bm, radius=H * 0.030, center=(hx, hy, hz + H * 0.04), segments=8, rings=5)

    elif item == "SCROLL":
        _add_cylinder(bm, radius=H * 0.010, depth=H * 0.07, center=(hx - H * 0.020, hy, hz + H * 0.035), segments=6)
        _add_cylinder(bm, radius=H * 0.010, depth=H * 0.07, center=(hx + H * 0.020, hy, hz + H * 0.035), segments=6)
        _add_scaled_cube(bm, H * 0.040, H * 0.004, H * 0.050, center=(hx, hy + H * 0.004, hz + H * 0.035))

    elif item == "HOLY_SYMBOL":
        # Sunburst disc
        _add_cylinder(bm, radius=H * 0.025, depth=H * 0.008, center=(hx, hy, hz + H * 0.04), segments=12)
        for i in range(8):
            angle = i * (math.pi / 4)
            rx = math.cos(angle) * H * 0.032
            ry = math.sin(angle) * H * 0.032
            _add_cone(bm, radius_base=H * 0.005, radius_tip=0.001, depth=H * 0.018,
                      center=(hx + rx, hy + ry, hz + H * 0.04), segments=4)

    elif item == "FOCUS_GEM":
        _add_uv_sphere(bm, radius=H * 0.022, center=(hx, hy, hz + H * 0.035), segments=8, rings=5)

    elif item == "POTION":
        # Bottle body
        _add_cylinder(bm, radius=H * 0.016, depth=H * 0.045, center=(hx, hy, hz + H * 0.025), segments=8)
        # Neck
        _add_cylinder(bm, radius=H * 0.007, depth=H * 0.020, center=(hx, hy, hz + H * 0.058), segments=6)
        # Cork
        _add_cylinder(bm, radius=H * 0.008, depth=H * 0.010, center=(hx, hy, hz + H * 0.072), segments=6)

    elif item == "SKULL":
        _add_uv_sphere(bm, radius=H * 0.026, center=(hx, hy, hz + H * 0.035), segments=8, rings=6)

    elif item == "HORN":
        _add_cone(bm, radius_base=H * 0.028, radius_tip=H * 0.006, depth=H * 0.12,
                  center=(hx, hy, hz + H * 0.06), segments=8)

    elif item == "ROPE_COIL":
        for i in range(5):
            ring_r = H * (0.025 + i * 0.004)
            angle_step = math.pi / 4
            for j in range(8):
                angle = j * angle_step
                rx = math.cos(angle) * ring_r
                ry = math.sin(angle) * ring_r
                _add_uv_sphere(bm, radius=H * 0.006, center=(hx + rx, hy + ry, hz + H * 0.025 + i * H * 0.008),
                               segments=4, rings=3)

    elif item == "SEVERED_HEAD":
        _add_uv_sphere(bm, radius=H * 0.030, center=(hx, hy, hz + H * 0.04), segments=10, rings=7)
        # Hair tuft
        for i in range(4):
            angle = i * (math.pi / 2)
            hfx = math.cos(angle) * H * 0.018
            hfy = math.sin(angle) * H * 0.018
            _add_cone(bm, radius_base=H * 0.007, radius_tip=0.001, depth=H * 0.022,
                      center=(hx + hfx, hy + hfy, hz + H * 0.072), segments=4)

    elif item == "COIN_PURSE":
        _add_uv_sphere(bm, radius=H * 0.022, center=(hx, hy, hz + H * 0.025), segments=7, rings=5)
        # Drawstring tie at top
        _add_cylinder(bm, radius=H * 0.009, depth=H * 0.010, center=(hx, hy, hz + H * 0.048), segments=6)


def _build_back_item(bm, item, torso_top_z, torso_bottom_z, H, shoulder_w):
    """Attach an item to the back of the character."""
    if item == "NONE":
        return

    back_y = -H * 0.07   # behind the torso centre
    mid_z = (torso_top_z + torso_bottom_z) * 0.5

    # ---------------------------------------------------------------- Storage
    if item == "BACKPACK":
        # Main body
        _add_scaled_cube(bm, H * 0.08, H * 0.05, H * 0.12, center=(0, back_y - H * 0.025, mid_z))
        # Top flap
        _add_scaled_cube(bm, H * 0.08, H * 0.020, H * 0.030,
                         center=(0, back_y - H * 0.018, mid_z + H * 0.075))
        # Side pockets
        for side in (-1, 1):
            _add_scaled_cube(bm, H * 0.025, H * 0.030, H * 0.065,
                             center=(side * H * 0.053, back_y - H * 0.015, mid_z - H * 0.01))
        # Straps (thin cylinders)
        for side in (-1, 1):
            _add_cylinder(bm, radius=H * 0.006, depth=H * 0.22,
                          center=(side * H * 0.028, back_y + H * 0.012, mid_z + H * 0.02), segments=4)

    elif item == "SATCHEL":
        _add_scaled_cube(bm, H * 0.07, H * 0.025, H * 0.07, center=(H * 0.04, back_y - H * 0.010, mid_z))
        # Shoulder strap
        _add_cylinder(bm, radius=H * 0.005, depth=H * 0.30,
                      center=(-H * 0.01, back_y + H * 0.008, mid_z + H * 0.05), segments=4)

    elif item == "BEDROLL":
        _add_cylinder(bm, radius=H * 0.022, depth=H * 0.16,
                      center=(0, back_y - H * 0.015, torso_bottom_z - H * 0.02), segments=8)
        # Binding straps
        for dz in (-H * 0.04, H * 0.04):
            _add_cylinder(bm, radius=H * 0.024, depth=H * 0.006,
                          center=(0, back_y - H * 0.015, torso_bottom_z - H * 0.02 + dz), segments=8)

    elif item == "BARREL":
        _add_cylinder(bm, radius=H * 0.040, depth=H * 0.08,
                      center=(0, back_y - H * 0.030, mid_z), segments=10)
        # Barrel hoops
        for dz in (-H * 0.025, 0, H * 0.025):
            _add_cylinder(bm, radius=H * 0.042, depth=H * 0.006,
                          center=(0, back_y - H * 0.030, mid_z + dz), segments=10)

    # ---------------------------------------------------------------- Quivers
    elif item == "QUIVER":
        _add_cylinder(bm, radius=H * 0.018, depth=H * 0.14,
                      center=(H * 0.045, back_y - H * 0.010, mid_z + H * 0.03), segments=7)
        # Arrow shafts peeking out
        for i in range(5):
            ax = H * 0.040 + i * H * 0.005
            _add_cylinder(bm, radius=H * 0.003, depth=H * 0.06,
                          center=(ax, back_y - H * 0.008, mid_z + H * 0.11), segments=4)

    elif item == "BOLT_CASE":
        _add_scaled_cube(bm, H * 0.060, H * 0.025, H * 0.10,
                         center=(H * 0.045, back_y - H * 0.010, mid_z))
        for i in range(4):
            _add_cylinder(bm, radius=H * 0.004, depth=H * 0.04,
                          center=(H * 0.035 + i * H * 0.008, back_y - H * 0.010, mid_z + H * 0.065), segments=4)

    # ---------------------------------------------------------------- Sheathed weapons
    elif item == "SWORD_BACK":
        # Scabbard
        _add_cylinder(bm, radius=H * 0.012, depth=H * 0.34,
                      center=(H * 0.025, back_y - H * 0.010, mid_z + H * 0.08), segments=6)
        # Pommel
        _add_uv_sphere(bm, radius=H * 0.016,
                       center=(H * 0.025, back_y - H * 0.010, mid_z + H * 0.08 - H * 0.20),
                       segments=5, rings=4)

    elif item == "GREATSWORD_BACK":
        _add_cylinder(bm, radius=H * 0.014, depth=H * 0.55,
                      center=(0, back_y - H * 0.020, mid_z + H * 0.10), segments=6)
        # Crossguard peeking above shoulder
        _add_scaled_cube(bm, H * 0.095, H * 0.012, H * 0.013,
                         center=(0, back_y - H * 0.020, mid_z + H * 0.10 + H * 0.275))
        _add_uv_sphere(bm, radius=H * 0.018,
                       center=(0, back_y - H * 0.020, mid_z + H * 0.10 - H * 0.295),
                       segments=5, rings=4)

    elif item == "AXES_CROSSED":
        for side, tilt in ((1, 0.25), (-1, -0.25)):
            # Haft
            _add_cylinder(bm, radius=H * 0.010, depth=H * 0.28,
                          center=(side * H * 0.020, back_y - H * 0.015, mid_z + H * 0.04), segments=5)
            # Head
            _add_scaled_cube(bm, H * 0.050, H * 0.016, H * 0.065,
                             center=(side * H * 0.045, back_y - H * 0.010, mid_z + H * 0.155))

    elif item == "SHIELD_BACK":
        _add_cylinder(bm, radius=H * 0.065, depth=H * 0.016,
                      center=(0, back_y - H * 0.006, mid_z), segments=12)

    elif item == "SPEAR_BACK":
        _add_cylinder(bm, radius=H * 0.008, depth=H * 0.65,
                      center=(-H * 0.030, back_y - H * 0.012, mid_z + H * 0.10), segments=5)
        _add_cone(bm, radius_base=H * 0.009, radius_tip=0.001, depth=H * 0.10,
                  center=(-H * 0.030, back_y - H * 0.012, mid_z + H * 0.10 + H * 0.375), segments=5)

    # ---------------------------------------------------------------- Wings
    elif item == "WINGS_FEATHER":
        for side in (-1, 1):
            # Main wing arm (long swept cylinder)
            wx = side * H * 0.05
            _add_cylinder(bm, radius=H * 0.012, depth=H * 0.38,
                          center=(side * (H * 0.05 + H * 0.19 * 0.5), back_y - H * 0.008, torso_top_z - H * 0.04),
                          segments=6)
            # Secondary feather layer
            _add_cone(bm, radius_base=H * 0.055, radius_tip=H * 0.010, depth=H * 0.30,
                      center=(side * H * 0.17, back_y - H * 0.030, torso_top_z - H * 0.14), segments=8)
            # Feather tips (5 small cones along the trailing edge)
            for i in range(5):
                fz = torso_top_z - H * 0.04 - i * H * 0.06
                fx = side * (H * 0.20 + i * H * 0.020)
                _add_cone(bm, radius_base=H * 0.008, radius_tip=0.001, depth=H * 0.055,
                          center=(fx, back_y - H * 0.035, fz), segments=4)

    elif item == "WINGS_BAT":
        for side in (-1, 1):
            # Main membrane: wide flat cone
            _add_cone(bm, radius_base=H * 0.25, radius_tip=H * 0.006, depth=H * 0.010,
                      center=(side * H * 0.22, back_y - H * 0.025, torso_top_z - H * 0.12), segments=6)
            # Arm spar
            _add_cylinder(bm, radius=H * 0.008, depth=H * 0.32,
                          center=(side * (H * 0.04 + H * 0.16 * 0.5), back_y - H * 0.018, torso_top_z - H * 0.05),
                          segments=5)
            # Finger spars
            for i in range(3):
                fz = torso_top_z - H * 0.06 - i * H * 0.04
                fx = side * (H * 0.20 + i * H * 0.025)
                _add_cylinder(bm, radius=H * 0.005, depth=H * 0.16,
                               center=(fx, back_y - H * 0.028, fz - H * 0.08), segments=4)

    elif item == "WINGS_FAIRY":
        for side in (-1, 1):
            for pair in range(2):
                pz_off = torso_top_z - H * 0.06 - pair * H * 0.10
                _add_cone(bm, radius_base=H * 0.10, radius_tip=H * 0.004, depth=H * 0.008,
                          center=(side * H * 0.12, back_y - H * 0.018, pz_off), segments=8)
                # Veins
                for i in range(3):
                    vangle = i * (math.pi / 6) * side
                    vx = math.cos(vangle) * H * 0.07
                    vz = math.sin(abs(vangle)) * H * 0.07
                    _add_cylinder(bm, radius=H * 0.002, depth=H * 0.09,
                                  center=(side * H * 0.07 + vx * 0.5, back_y - H * 0.014, pz_off + vz * 0.5),
                                  segments=3)

    elif item == "WINGS_DRAGON":
        for side in (-1, 1):
            # Thick main spar
            _add_cylinder(bm, radius=H * 0.018, depth=H * 0.42,
                          center=(side * (H * 0.05 + H * 0.21), back_y - H * 0.022, torso_top_z - H * 0.08),
                          segments=6)
            # Membrane (two large cones)
            _add_cone(bm, radius_base=H * 0.28, radius_tip=H * 0.010, depth=H * 0.015,
                      center=(side * H * 0.24, back_y - H * 0.035, torso_top_z - H * 0.18), segments=6)
            _add_cone(bm, radius_base=H * 0.18, radius_tip=H * 0.008, depth=H * 0.012,
                      center=(side * H * 0.22, back_y - H * 0.030, torso_top_z - H * 0.34), segments=6)
            # Claw spurs at wingtip
            for i in range(3):
                _add_cone(bm, radius_base=H * 0.009, radius_tip=0.001, depth=H * 0.042,
                          center=(side * (H * 0.42 + i * H * 0.010), back_y - H * 0.018,
                                  torso_top_z - H * 0.06 - i * H * 0.035), segments=4)

    # ---------------------------------------------------------------- Magical / exotic
    elif item == "MAGIC_AURA":
        # Swirling energy tendrils: 8 thin curling cylinders around the back
        for i in range(8):
            angle = i * (math.pi / 4)
            ex = math.cos(angle) * H * 0.06
            ey = back_y + math.sin(angle) * H * 0.025
            _add_cone(bm, radius_base=H * 0.007, radius_tip=0.001, depth=H * 0.18,
                      center=(ex, ey, mid_z + i * H * 0.015), segments=4)

    elif item == "JETPACK":
        # Two thruster cylinders
        for side in (-1, 1):
            _add_cylinder(bm, radius=H * 0.028, depth=H * 0.10,
                          center=(side * H * 0.034, back_y - H * 0.030, mid_z), segments=8)
            _add_cone(bm, radius_base=H * 0.032, radius_tip=H * 0.018, depth=H * 0.025,
                      center=(side * H * 0.034, back_y - H * 0.030, mid_z - H * 0.065), segments=8)
        # Frame / harness plate
        _add_scaled_cube(bm, H * 0.09, H * 0.025, H * 0.12, center=(0, back_y - H * 0.010, mid_z))
        # Exhaust flare
        for side in (-1, 1):
            _add_cone(bm, radius_base=H * 0.026, radius_tip=H * 0.012, depth=H * 0.06,
                      center=(side * H * 0.034, back_y - H * 0.030, mid_z - H * 0.08), segments=8)

    elif item == "INSTRUMENT_LUTE":
        # Body (rounded pear shape: two spheres)
        _add_uv_sphere(bm, radius=H * 0.045, center=(0, back_y - H * 0.030, mid_z - H * 0.02),
                       segments=8, rings=6)
        _add_uv_sphere(bm, radius=H * 0.030, center=(0, back_y - H * 0.025, mid_z + H * 0.055),
                       segments=7, rings=5)
        # Neck
        _add_cylinder(bm, radius=H * 0.010, depth=H * 0.18,
                      center=(0, back_y - H * 0.018, mid_z + H * 0.16), segments=5)
        # Pegbox + tuning pegs
        _add_scaled_cube(bm, H * 0.020, H * 0.018, H * 0.030,
                         center=(0, back_y - H * 0.016, mid_z + H * 0.265))
        for px in (-H * 0.010, H * 0.010):
            for pz in (mid_z + H * 0.252, mid_z + H * 0.267, mid_z + H * 0.280):
                _add_cylinder(bm, radius=H * 0.004, depth=H * 0.022,
                              center=(px, back_y - H * 0.006, pz), segments=4)

    elif item == "CAULDRON":
        _add_cylinder(bm, radius=H * 0.040, depth=H * 0.045,
                      center=(0, back_y - H * 0.035, torso_bottom_z + H * 0.025), segments=10)
        # Rim
        _add_cylinder(bm, radius=H * 0.043, depth=H * 0.008,
                      center=(0, back_y - H * 0.035, torso_bottom_z + H * 0.052), segments=10)
        # Legs
        for side in (-1, 1):
            _add_cylinder(bm, radius=H * 0.006, depth=H * 0.022,
                          center=(side * H * 0.030, back_y - H * 0.035, torso_bottom_z + H * 0.001), segments=5)
        # Handle arch
        _add_cylinder(bm, radius=H * 0.005, depth=H * 0.084,
                      center=(0, back_y - H * 0.035, torso_bottom_z + H * 0.068), segments=5)


def _build_base(bm, style, H, base_z):
    r = H * 0.25
    thickness = H * 0.04 if style != "FLAT" else H * 0.025

    _add_cylinder(bm, radius=r, depth=thickness,
                  center=(0, 0, base_z - thickness * 0.5), segments=24)

    if style == "COBBLE":
        # Scatter small box stones on top
        import random
        rng = random.Random(42)
        for _ in range(18):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(0, r * 0.85)
            cx = math.cos(angle) * dist
            cy = math.sin(angle) * dist
            sw = rng.uniform(H * 0.015, H * 0.035)
            sd = rng.uniform(H * 0.012, H * 0.028)
            sh = rng.uniform(H * 0.003, H * 0.010)
            _add_scaled_cube(bm, sw, sd, sh, center=(cx, cy, base_z + sh * 0.5))

    elif style == "GRASS":
        # Random grass tufts (thin cones)
        import random
        rng = random.Random(7)
        for _ in range(20):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(0, r * 0.9)
            cx = math.cos(angle) * dist
            cy = math.sin(angle) * dist
            gh = rng.uniform(H * 0.012, H * 0.030)
            _add_cone(bm, radius_base=H * 0.003, radius_tip=0.001, depth=gh,
                      center=(cx, cy, base_z + gh * 0.5), segments=4)

    elif style == "ROCK":
        # A few irregular rock lumps
        for angle, dist, scale in [
            (0.5, r * 0.5, 0.9),
            (2.3, r * 0.4, 0.7),
            (4.1, r * 0.6, 1.1),
        ]:
            cx = math.cos(angle) * dist
            cy = math.sin(angle) * dist
            _add_uv_sphere(bm, radius=H * 0.04 * scale,
                           center=(cx, cy, base_z + H * 0.02 * scale),
                           segments=6, rings=4)

    elif style == "RUINS":
        # Broken column stumps
        for angle in (0.8, 3.0):
            cx = math.cos(angle) * r * 0.55
            cy = math.sin(angle) * r * 0.55
            col_h = H * rng_sample(0.05, 0.14) if False else H * 0.09
            _add_cylinder(bm, radius=H * 0.030, depth=col_h,
                          center=(cx, cy, base_z + col_h * 0.5), segments=8)


def rng_sample(a, b):  # tiny helper to avoid an import-time random
    return (a + b) / 2


# ---------------------------------------------------------------------------
# Apply a simple pose offset to the overall mesh
# ---------------------------------------------------------------------------

def _apply_pose(bm, pose, H):
    """Very simple pose: rotate / shift arm/leg verts by splitting on X."""
    if pose == "STAND":
        return  # default

    if pose == "HEROIC":
        # Slightly spread legs, one arm raised
        for v in bm.verts:
            if v.co.x > H * 0.04 and v.co.z < H * 0.30:
                v.co.x += H * 0.012
            elif v.co.x < -H * 0.04 and v.co.z < H * 0.30:
                v.co.x -= H * 0.012
            # Raise right arm
            if v.co.x > H * 0.14 and H * 0.50 < v.co.z < H * 0.78:
                v.co.z += H * 0.04
                v.co.y += H * 0.02

    elif pose == "COMBAT":
        for v in bm.verts:
            # Crouch torso slightly forward
            if H * 0.30 < v.co.z < H * 0.70:
                v.co.y += H * 0.02
                v.co.z -= H * 0.01

    elif pose == "CAST":
        for v in bm.verts:
            # Both arms raised and outward
            if abs(v.co.x) > H * 0.14 and H * 0.50 < v.co.z < H * 0.78:
                v.co.z += H * 0.06
                v.co.y -= H * 0.01

    elif pose == "KNEEL":
        for v in bm.verts:
            # Lower legs bent – shift lower-leg verts rearward and down
            if v.co.z < H * 0.28:
                v.co.y -= H * 0.04
                v.co.z *= 0.72

    elif pose == "STRIDE":
        for v in bm.verts:
            # Push legs into a stride: right leg forward, left back
            if v.co.x > H * 0.02 and v.co.z < H * 0.50:
                v.co.y += H * 0.05
            elif v.co.x < -H * 0.02 and v.co.z < H * 0.50:
                v.co.y -= H * 0.05


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_caricature_mini_v2(body_props, gear_props):
    """
    Build a caricature mini using the Skin modifier for a smooth, connected
    body mesh, then add gear primitives on top.

    Pipeline:
      1. Build body skeleton → Skin + Subdiv → depsgraph bake → smooth body mesh
      2. Load baked body into bmesh
      3. Add gear primitives (weapons, helmet, armor, cape, back item, base)
      4. Apply pose, merge, finalize
      5. Return detached Blender object
    """
    # --- Step 1: Build the skin-modifier body ---------------------------
    body_obj, lm = _build_skin_body(body_props)

    # --- Step 2: Load baked body mesh into bmesh for gear additions -----
    bm = bmesh.new()
    bm.from_mesh(body_obj.data)

    # Clean up the temporary body object (keep the mesh, it's in bm now)
    body_mesh = body_obj.data
    bpy.data.objects.remove(body_obj, do_unlink=True)
    bpy.data.meshes.remove(body_mesh)

    H            = lm["H"]
    head_r       = lm["head_r"]
    head_top_z   = lm["head_top_z"]
    shoulder_z   = lm["shoulder_z"]
    shoulder_w   = lm["shoulder_w"]
    torso_top_z  = lm["torso_top_z"]
    torso_bot_z  = lm["torso_bottom_z"]
    hand_z       = lm["hand_z"]
    hand_y       = lm["hand_y"]
    arm_x        = lm["arm_x"]
    base_z       = lm["base_z"]

    # --- Step 3: Add gear primitives ------------------------------------

    # Base
    _build_base(bm, gear_props.base_style, H, base_z)

    # Armour layer
    _build_armor_layer(bm, body_props, gear_props, torso_bot_z, torso_top_z)

    # Cape
    _build_cape(bm, body_props, gear_props, torso_top_z, torso_bot_z)

    # Weapons
    _build_weapon(bm, gear_props.weapon_right, arm_x, hand_y, hand_z, 1, H)
    _build_weapon(bm, gear_props.weapon_left, -arm_x, hand_y, hand_z, -1, H)

    # Scabbard
    if gear_props.add_scabbard:
        _add_cone(bm, H * 0.010, H * 0.007, H * 0.18,
                  (shoulder_w * 0.7, H * 0.04, torso_bot_z + H * 0.12), 5)

    # Back item
    _build_back_item(bm, gear_props.back_item, torso_top_z, torso_bot_z, H, shoulder_w)

    # Helmet (body already includes head from skin modifier)
    _build_helmet(bm, gear_props, head_top_z - head_r * 0.4, head_r)

    # --- Step 4: Pose, merge, finalize ----------------------------------
    _apply_pose(bm, gear_props.pose, H)

    _merge_close(bm, dist=H * 0.002)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("CaricatureMini")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new("CaricatureMini", mesh)
    return obj
