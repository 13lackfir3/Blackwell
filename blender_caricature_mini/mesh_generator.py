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
# Individual body-part builders
# ---------------------------------------------------------------------------

def _build_head(bm, props, origin_z):
    """Sphere-based head with mild caricature shaping."""
    H = props.total_height
    head_r = H * 0.135 * props.head_scale

    # Basic sphere
    sphere_verts = _add_uv_sphere(
        bm,
        radius=head_r,
        center=(0, 0, origin_z + head_r),
        segments=16,
        rings=10,
    )

    # Squash/stretch width and depth
    w = props.head_width
    d = props.head_depth
    for v in sphere_verts:
        v.co.x *= w
        v.co.y *= d

    # Jaw widening – push lower-hemisphere verts outward in X
    jw = props.jaw_width * head_r * 0.25
    for v in sphere_verts:
        local_z = v.co.z - (origin_z + head_r)
        if local_z < -head_r * 0.1:
            t = abs(local_z / head_r)
            v.co.x += math.copysign(jw * t, v.co.x) if abs(v.co.x) > 0.001 else 0

    # Brow ridge – push upper-front verts forward
    br = props.brow_ridge * head_r * 0.15
    for v in sphere_verts:
        local_z = v.co.z - (origin_z + head_r)
        if local_z > head_r * 0.1 and v.co.y > 0:
            t = local_z / head_r
            v.co.y += br * t

    # Nose bump (simple protrusion on front)
    ns = props.nose_size * head_r * 0.12
    nose_cx = 0
    nose_cy = head_r * d
    nose_cz = origin_z + head_r * 0.85
    _add_uv_sphere(
        bm,
        radius=head_r * 0.08 + ns,
        center=(nose_cx, nose_cy + ns * 0.5, nose_cz),
        segments=6,
        rings=4,
    )

    # Ears (small spheres on sides)
    ear_r = head_r * 0.08 + props.ear_size * head_r * 0.1
    for side in (-1, 1):
        _add_uv_sphere(
            bm,
            radius=ear_r,
            center=(side * head_r * w, 0, origin_z + head_r * 0.95),
            segments=6,
            rings=4,
        )

    # Chin point
    ch = props.chin_length * head_r * 0.15
    for v in sphere_verts:
        local_z = v.co.z - (origin_z + head_r)
        if local_z < -head_r * 0.4:
            t = (-local_z - head_r * 0.4) / (head_r * 0.6)
            v.co.z -= ch * t * t

    return origin_z + head_r * 2.0


def _build_neck(bm, props, origin_z):
    H = props.total_height
    neck_r = H * 0.038
    neck_h = H * 0.048
    _add_cylinder(bm, radius=neck_r, depth=neck_h,
                  center=(0, 0, origin_z + neck_h * 0.5), segments=8)
    return origin_z + neck_h


def _build_torso(bm, props, origin_z):
    H = props.total_height
    torso_h = H * 0.24 * props.torso_length
    sw = props.shoulder_width
    belly = props.belly
    chest = props.chest

    shoulder_w = H * 0.11 * sw
    hip_w = H * 0.085
    chest_d = H * 0.06 * (1.0 + chest * 0.6)
    belly_d = H * 0.055 * (1.0 + belly * 1.0)

    # Build torso as 3 stacked scaled cubes (shoulder, chest, hip)
    seg_h = torso_h / 3.0

    # Shoulder segment
    _add_scaled_cube(
        bm, shoulder_w, chest_d * 0.9, seg_h,
        center=(0, 0, origin_z + seg_h * 0.5),
    )
    # Chest/mid segment
    mid_w = (shoulder_w + hip_w) / 2
    _add_scaled_cube(
        bm, mid_w, (chest_d + belly_d) * 0.5, seg_h,
        center=(0, belly_d * 0.05, origin_z + seg_h * 1.5),
    )
    # Hip segment
    _add_scaled_cube(
        bm, hip_w, belly_d * 0.85, seg_h,
        center=(0, belly_d * 0.03, origin_z + seg_h * 2.5),
    )

    return origin_z + torso_h, shoulder_w, origin_z + torso_h * 0.9


def _build_arm(bm, props, origin_z, shoulder_z, shoulder_x, side):
    """Build one arm. side = +1 (right) or -1 (left)."""
    H = props.total_height
    upper_len = H * 0.13 * props.arm_length
    lower_len = H * 0.11 * props.arm_length
    arm_r = H * 0.022 * props.arm_thickness
    hand_r = H * 0.028 * props.hand_size

    arm_x = side * (shoulder_x + arm_r * 1.1)

    # Upper arm – slight downward angle
    ua_start_z = shoulder_z
    ua_end_z = shoulder_z - upper_len
    ua_mid_z = (ua_start_z + ua_end_z) / 2
    _add_cylinder(
        bm, radius=arm_r, depth=upper_len,
        center=(arm_x, 0, ua_mid_z), segments=6,
    )

    # Lower arm – slight forward angle
    la_mid_z = ua_end_z - lower_len * 0.5
    la_x = arm_x + side * lower_len * 0.08
    _add_cylinder(
        bm, radius=arm_r * 0.88, depth=lower_len,
        center=(la_x, lower_len * 0.04, la_mid_z), segments=6,
    )

    # Hand
    hand_z = ua_end_z - lower_len
    _add_uv_sphere(
        bm, radius=hand_r,
        center=(la_x + side * lower_len * 0.04, lower_len * 0.06, hand_z),
        segments=6, rings=4,
    )


def _build_leg(bm, props, origin_z, side):
    """Build one leg. side = +1 (right) or -1 (left)."""
    H = props.total_height
    upper_len = H * 0.22 * props.leg_length
    lower_len = H * 0.20 * props.leg_length
    leg_r = H * 0.038 * props.leg_thickness
    foot_r = H * 0.030 * props.foot_size

    hip_offset_x = side * H * 0.045

    # Upper leg (thigh) – slight outward then inward
    uth_z = origin_z - upper_len * 0.5
    _add_cylinder(
        bm, radius=leg_r, depth=upper_len,
        center=(hip_offset_x, 0, uth_z), segments=7,
    )

    knee_z = origin_z - upper_len

    # Lower leg (shin) – tapered
    shin_z = knee_z - lower_len * 0.5
    _add_cone(
        bm,
        radius_base=leg_r * 0.90,
        radius_tip=leg_r * 0.60,
        depth=lower_len,
        center=(hip_offset_x, 0, shin_z),
        segments=7,
    )

    ankle_z = knee_z - lower_len

    # Foot – flattened sphere
    foot_verts_before = set(bm.verts)
    _add_uv_sphere(
        bm, radius=foot_r,
        center=(hip_offset_x, foot_r * 0.8, ankle_z - foot_r * 0.3),
        segments=8, rings=5,
    )
    bm.verts.ensure_lookup_table()
    foot_verts = [v for v in bm.verts if v not in foot_verts_before]
    for v in foot_verts:
        v.co.z = min(v.co.z, ankle_z - foot_r * 0.1)  # flatten bottom


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

def build_caricature_mini(body_props, gear_props):
    """
    Build the full caricature mini mesh.
    Returns a new Blender mesh object (not yet linked to any collection).
    """
    bm = bmesh.new()

    H = body_props.total_height

    # --- Base ---
    base_z = 0.0
    _build_base(bm, gear_props.base_style, H, base_z)

    # --- Legs ---
    leg_top_z = H * 0.45 * body_props.leg_length + H * 0.028
    for side in (1, -1):
        _build_leg(bm, body_props, leg_top_z, side)

    # --- Torso ---
    torso_bottom_z = leg_top_z
    torso_top_z, shoulder_w, pauldron_z = _build_torso(bm, body_props, torso_bottom_z)

    # --- Armour layer ---
    _build_armor_layer(bm, body_props, gear_props, torso_bottom_z, torso_top_z)

    # --- Cape ---
    _build_cape(bm, body_props, gear_props, torso_top_z, torso_bottom_z)

    # --- Arms ---
    arm_z_base = torso_top_z
    arm_H = H * 0.13 * body_props.arm_length
    hand_z_r = arm_z_base - arm_H - H * 0.11 * body_props.arm_length
    hand_z_l = hand_z_r
    arm_x_r = shoulder_w + H * 0.022 * body_props.arm_thickness * 1.1
    arm_x_l = -arm_x_r

    _build_arm(bm, body_props, arm_z_base, arm_z_base, shoulder_w, 1)
    _build_arm(bm, body_props, arm_z_base, arm_z_base, shoulder_w, -1)

    # --- Weapons ---
    hand_y = H * 0.06
    _build_weapon(
        bm, gear_props.weapon_right,
        arm_x_r, hand_y, hand_z_r, 1, H,
    )
    _build_weapon(
        bm, gear_props.weapon_left,
        arm_x_l, hand_y, hand_z_l, -1, H,
    )

    # Scabbard on hip
    if gear_props.add_scabbard:
        scabbard_x = shoulder_w * 0.7
        _add_cone(bm, radius_base=H * 0.010, radius_tip=H * 0.007,
                  depth=H * 0.18,
                  center=(scabbard_x, H * 0.04, torso_bottom_z + H * 0.12),
                  segments=5)

    # Back item
    _build_back_item(bm, gear_props.back_item, torso_top_z, torso_bottom_z, H, shoulder_w)

    # --- Neck ---
    neck_bottom = torso_top_z
    neck_top = _build_neck(bm, body_props, neck_bottom)

    # --- Head ---
    head_r = H * 0.135 * body_props.head_scale
    _build_head(bm, body_props, neck_top)

    # --- Helmet ---
    head_center_z = neck_top + head_r
    _build_helmet(bm, gear_props, head_center_z + head_r * 0.6, head_r)

    # --- Pose deformation ---
    _apply_pose(bm, gear_props.pose, H)

    # --- Finalise ---
    _merge_close(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("CaricatureMini")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new("CaricatureMini", mesh)
    return obj


def build_caricature_mini_v2(body_props, gear_props):
    """
    Corrected entry-point that properly calls helmet with gear_props.
    Replaces build_caricature_mini.
    """
    bm = bmesh.new()

    H = body_props.total_height

    # Base
    base_z = 0.0
    _build_base(bm, gear_props.base_style, H, base_z)

    # Legs
    leg_top_z = H * 0.45 * body_props.leg_length + H * 0.028
    for side in (1, -1):
        _build_leg(bm, body_props, leg_top_z, side)

    # Torso
    torso_bottom_z = leg_top_z
    torso_top_z, shoulder_w, _ = _build_torso(bm, body_props, torso_bottom_z)

    # Armour
    _build_armor_layer(bm, body_props, gear_props, torso_bottom_z, torso_top_z)

    # Cape
    _build_cape(bm, body_props, gear_props, torso_top_z, torso_bottom_z)

    # Arms & weapons
    arm_x = shoulder_w + H * 0.022 * body_props.arm_thickness * 1.1
    arm_len = H * 0.13 * body_props.arm_length + H * 0.11 * body_props.arm_length
    hand_z = torso_top_z - arm_len
    hand_y = H * 0.06

    _build_arm(bm, body_props, torso_top_z, torso_top_z, shoulder_w, 1)
    _build_arm(bm, body_props, torso_top_z, torso_top_z, shoulder_w, -1)

    _build_weapon(bm, gear_props.weapon_right, arm_x, hand_y, hand_z, 1, H)
    _build_weapon(bm, gear_props.weapon_left, -arm_x, hand_y, hand_z, -1, H)

    if gear_props.add_scabbard:
        _add_cone(bm, H * 0.010, H * 0.007, H * 0.18,
                  (shoulder_w * 0.7, H * 0.04, torso_bottom_z + H * 0.12), 5)

    # Back item (replaces simple add_backpack bool)
    _build_back_item(bm, gear_props.back_item, torso_top_z, torso_bottom_z, H, shoulder_w)

    # Neck
    neck_top = _build_neck(bm, body_props, torso_top_z)

    # Head
    head_r = H * 0.135 * body_props.head_scale
    _build_head(bm, body_props, neck_top)

    # Helmet
    head_center_z = neck_top + head_r
    _build_helmet(bm, gear_props, head_center_z + head_r * 0.6, head_r)

    # Pose
    _apply_pose(bm, gear_props.pose, H)

    # Finalise
    _merge_close(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("CaricatureMini")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new("CaricatureMini", mesh)
    return obj
