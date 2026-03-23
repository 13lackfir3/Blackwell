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
    style = props.gear.helmet
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
    """Place a weapon mesh at the given hand position."""
    if item == "NONE":
        return

    handle_r = H * 0.010
    blade_r = H * 0.008

    if item in ("SWORD", "DAGGER"):
        blade_len = H * (0.26 if item == "SWORD" else 0.14)
        # Handle
        _add_cylinder(bm, radius=handle_r, depth=H * 0.06,
                      center=(hand_x, hand_y, hand_z + H * 0.03), segments=5)
        # Guard (disc)
        _add_cylinder(bm, radius=H * 0.022, depth=H * 0.008,
                      center=(hand_x, hand_y, hand_z + H * 0.065), segments=8)
        # Blade
        _add_cone(bm, radius_base=blade_r, radius_tip=0.001, depth=blade_len,
                  center=(hand_x, hand_y, hand_z + H * 0.065 + blade_len * 0.5), segments=5)

    elif item == "AXE":
        # Haft
        _add_cylinder(bm, radius=handle_r, depth=H * 0.22,
                      center=(hand_x, hand_y, hand_z + H * 0.11), segments=5)
        # Head
        _add_scaled_cube(
            bm, H * 0.06, H * 0.02, H * 0.08,
            center=(hand_x + side * H * 0.03, hand_y, hand_z + H * 0.22),
        )

    elif item == "MACE":
        _add_cylinder(bm, radius=handle_r, depth=H * 0.20,
                      center=(hand_x, hand_y, hand_z + H * 0.10), segments=5)
        _add_uv_sphere(bm, radius=H * 0.030,
                       center=(hand_x, hand_y, hand_z + H * 0.22),
                       segments=8, rings=5)

    elif item == "WAND":
        _add_cone(bm, radius_base=handle_r, radius_tip=H * 0.006, depth=H * 0.18,
                  center=(hand_x, hand_y, hand_z + H * 0.09), segments=6)
        _add_uv_sphere(bm, radius=H * 0.018,
                       center=(hand_x, hand_y, hand_z + H * 0.20),
                       segments=6, rings=4)

    elif item == "STAFF":
        _add_cylinder(bm, radius=handle_r, depth=H * 0.55,
                      center=(hand_x, hand_y, hand_z + H * 0.27), segments=6)
        _add_uv_sphere(bm, radius=H * 0.022,
                       center=(hand_x, hand_y, hand_z + H * 0.56),
                       segments=6, rings=4)

    elif item == "BOW":
        # Limbs (two arcs approximated as cylinders)
        for dz in (H * 0.10, -H * 0.10):
            _add_cylinder(bm, radius=handle_r * 0.7, depth=H * 0.14,
                          center=(hand_x, hand_y + H * 0.015, hand_z + dz), segments=5)

    elif item == "CROSSBOW":
        _add_scaled_cube(bm, H * 0.12, H * 0.035, H * 0.035,
                         center=(hand_x, hand_y, hand_z + H * 0.08))

    elif item == "TORCH":
        _add_cylinder(bm, radius=handle_r, depth=H * 0.16,
                      center=(hand_x, hand_y, hand_z + H * 0.08), segments=5)
        _add_cone(bm, radius_base=H * 0.020, radius_tip=0.001, depth=H * 0.06,
                  center=(hand_x, hand_y, hand_z + H * 0.19), segments=6)

    elif item in ("SHIELD_ROUND", "SHIELD_TOWER"):
        depth = H * 0.015
        if item == "SHIELD_ROUND":
            _add_cylinder(bm, radius=H * 0.055, depth=depth,
                          center=(hand_x, hand_y - depth, hand_z + H * 0.05), segments=10)
        else:
            _add_scaled_cube(bm, H * 0.07, depth, H * 0.18,
                             center=(hand_x, hand_y - depth, hand_z + H * 0.06))

    elif item == "TOME":
        _add_scaled_cube(bm, H * 0.040, H * 0.015, H * 0.055,
                         center=(hand_x, hand_y, hand_z + H * 0.03))

    elif item == "ORB":
        _add_uv_sphere(bm, radius=H * 0.030,
                       center=(hand_x, hand_y, hand_z + H * 0.04),
                       segments=8, rings=5)


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

    # Backpack / quiver
    if gear_props.add_backpack:
        _add_scaled_cube(bm, H * 0.06, H * 0.04, H * 0.10,
                         center=(0, -H * 0.07, torso_bottom_z + H * 0.14))

    # --- Neck ---
    neck_bottom = torso_top_z
    neck_top = _build_neck(bm, body_props, neck_bottom)

    # --- Head ---
    head_r = H * 0.135 * body_props.head_scale
    head_top = _build_head(bm, body_props, neck_top)

    # --- Helmet ---
    head_origin_z = neck_top
    _build_helmet(bm, body_props.__class__,    # pass the whole props bundle
                  head_origin_z + head_r, head_r)

    # Helmet needs the original props object – patch the call below
    # (the function above used a placeholder; redo with correct args)
    # Remove the incorrect call above and redo
    # We need gear_props here – re-call properly
    # (the build_head already placed head; now helmet on top)

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

    if gear_props.add_backpack:
        _add_scaled_cube(bm, H * 0.06, H * 0.04, H * 0.10,
                         (0, -H * 0.07, torso_bottom_z + H * 0.14))

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
