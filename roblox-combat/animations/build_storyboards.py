"""Solve, bake, validate and render the M1 combo.

    python3 build_storyboards.py            # everything
    python3 build_storyboards.py M1_1 M1_4  # only some attacks (sheets + report)

Outputs (next to this file):
    m1_combo.json                  machine-readable spec (keyframes + every baked frame)
    storyboards/<id>_keyframes.png 3-view keyframe sheet
    storyboards/<id>_allframes.png every 60 fps frame, 2 views
    storyboards/combo_overview.png the whole combo at a glance
    storyboards/combo_preview.gif  slow-motion loop of the full combo
"""

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import combo_data as D
import render
import rig

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "storyboards")

# R6 Motor6D C0/C1 rotation parts (row-major 3x3), straight from the default rig.
BASE_ROT = {
    "Root": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "Neck": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "RightShoulder": [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],
    "LeftShoulder": [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
    "RightHip": [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],
    "LeftHip": [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
}
# joint -> (parent part, child part, C0 position, C1 position)
JOINT_FRAMES = {
    "Root": ("HumanoidRootPart", "Torso", (0, 0, 0), (0, 0, 0)),
    "Neck": ("Torso", "Head", (0, 1, 0), (0, -0.5, 0)),
    "RightShoulder": ("Torso", "RightArm", (1, 0.5, 0), (-0.5, 0.5, 0)),
    "LeftShoulder": ("Torso", "LeftArm", (-1, 0.5, 0), (0.5, 0.5, 0)),
    "RightHip": ("Torso", "RightLeg", (1, -1, 0), (0.5, 1, 0)),
    "LeftHip": ("Torso", "LeftLeg", (-1, -1, 0), (-0.5, 1, 0)),
}
LIMB_AXIS = {"RightArm": (0, -1, 0), "LeftArm": (0, -1, 0), "RightLeg": (0, -1, 0), "LeftLeg": (0, -1, 0), "Head": (0, 0, -1)}
CHILD_OF = {"Root": "Torso", "Neck": "Head", "RightShoulder": "RightArm", "LeftShoulder": "LeftArm", "RightHip": "RightLeg", "LeftHip": "LeftLeg"}


def lunge_at(frame):
    return min(D.LUNGE_SPEED * frame / D.FPS, D.LUNGE_SPEED * D.LUNGE_TIME)


def r4(x):
    return round(float(x), 4)


def vec(v):
    return [r4(x) for x in v]


# --------------------------------------------------------------------------
# bake + validate
# --------------------------------------------------------------------------
def solve_attack(atk):
    for kf in atk["keyframes"]:
        kf["sol"] = rig.solve_pose(kf)


def bake(atk):
    kfs = atk["keyframes"]
    out = []
    for a, b in zip(kfs, kfs[1:]):
        for f in range(a["frame"], b["frame"]):
            rot, off = rig.interpolate(a, b, f)
            out.append((f, rot, np.array(off), a, b))
    last = kfs[-1]
    out.append((last["frame"], last["sol"]["rot"], np.array(last["sol"]["off"]), last, last))
    baked = []
    for f, rot, off, a, b in out:
        world = (0.0, 0.0, -lunge_at(f))
        fk = rig.forward_kinematics_mats(rot, off, world)
        baked.append(dict(frame=f, rot=rot, off=off, world=world, fk=fk, kf_a=a, kf_b=b))
    return baked


def planted_target(baked_frame, side):
    """Interpolated planted footprint (x, z) for this frame, or None if the foot is free."""
    a, b = baked_frame["kf_a"], baked_frame["kf_b"]
    la, lb = a["legs"][side], b["legs"][side]
    if not (isinstance(la, dict) and "plant" in la and isinstance(lb, dict) and "plant" in lb):
        return None
    if a is b:
        return np.array(la["plant"], dtype=float)
    t = (baked_frame["frame"] - a["frame"]) / (b["frame"] - a["frame"])
    return (1 - t) * np.array(la["plant"], dtype=float) + t * np.array(lb["plant"], dtype=float)


def metrics(atk, baked):
    m = {}
    cf = atk["contact_frame"]
    b = next(x for x in baked if x["frame"] == cf)
    tip = np.array(b["fk"]["tips"][atk["strike_tip"]])
    m["contact_tip_world"] = vec(tip)
    m["contact_vs_dummy_z"] = r4(tip[2] - D.DUMMY_FRONT_Z)
    worst_pen, worst_slide, worst_float = 0.0, 0.0, 0.0
    for x in baked:
        fk = x["fk"]
        for side, name in (("L", "Left"), ("R", "Right")):
            low = rig.foot_low(fk, name) - rig.GROUND_Y
            tgt = planted_target(x, side)
            if tgt is not None:
                foot = fk["tips"][name + "Foot"]
                slide = float(np.linalg.norm(np.array([foot[0] - x['world'][0], foot[2] - x['world'][2]]) - tgt))
                worst_slide = max(worst_slide, slide)
                worst_float = max(worst_float, low)
            worst_pen = min(worst_pen, low)
    m["max_floor_penetration"] = r4(-worst_pen)
    m["max_planted_foot_slide"] = r4(worst_slide)
    m["max_planted_foot_float"] = r4(worst_float)
    return m


def roblox_check(baked, tol=1e-6):
    """Rebuild every part with Roblox's own Part1 = Part0 * C0 * Transform * C1^-1 and compare."""

    def cf(pos, rot):
        m = np.eye(4)
        m[:3, :3] = rot
        m[:3, 3] = pos
        return m

    worst = 0.0
    for x in baked:
        fk = x["fk"]
        t = rig.forward_kinematics_mats  # noqa
        hrp = cf(x["world"], np.eye(3))
        tf = {}
        for j in rig.JOINTS:
            base = np.array(BASE_ROT[j], dtype=float)
            T_rot = base.T @ x["rot"][j] @ base
            T_pos = base.T @ x["off"] if j == "Root" else np.zeros(3)
            tf[j] = cf(T_pos, T_rot)
        parts_cf = {}
        for j, (parent, child, c0p, c1p) in JOINT_FRAMES.items():
            base = np.array(BASE_ROT[j], dtype=float)
            C0, C1 = cf(c0p, base), cf(c1p, base)
            parent_cf = hrp if parent == "HumanoidRootPart" else parts_cf[parent]
            parts_cf[child] = parent_cf @ C0 @ tf[j] @ np.linalg.inv(C1)
        for name, (center, r, _s) in fk["parts"].items():
            got = parts_cf[name]
            worst = max(worst, float(np.abs(got[:3, 3] - center).max()), float(np.abs(got[:3, :3] - r).max()))
    return worst


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------
def joint_export(rot_local, prev_euler, off, j, fk):
    base = np.array(BASE_ROT[j], dtype=float)
    euler = rig.mat_to_euler_deg(rot_local, near=prev_euler)
    q = rig.mat_to_quat(rot_local)
    t_rot = base.T @ rot_local @ base
    tq = rig.mat_to_quat(t_rot)
    child = CHILD_OF[j]
    r_world = fk["parts"][child][1]
    entry = {
        "euler_xyz_deg": vec(euler),
        "quat_xyzw": vec([q[1], q[2], q[3], q[0]]),
        "transform_quat_xyzw": vec([tq[1], tq[2], tq[3], tq[0]]),
        "transform_euler_xyz_deg": vec(rig.mat_to_euler_deg(t_rot)),
    }
    if child in LIMB_AXIS:
        entry["limb_dir_world"] = vec(r_world @ np.array(LIMB_AXIS[child], dtype=float))
    if j == "Root":
        entry["transform_pos"] = vec(base.T @ off)
    return entry, euler


def frame_export(x, prev_eulers):
    fk = x["fk"]
    joints, eulers = {}, {}
    for j in rig.JOINTS:
        joints[j], eulers[j] = joint_export(x["rot"][j], prev_eulers.get(j), x["off"], j, fk)
    return dict(
        frame=x["frame"],
        time=r4(x["frame"] / D.FPS),
        torso_offset_hrp=vec(x["off"]),
        code_lunge_forward=r4(-x["world"][2]),
        joints=joints,
        markers={k: vec(v) for k, v in fk["tips"].items()},
    ), eulers


def export_attack(atk, baked, met):
    kf_out, prev = [], {}
    for kf in atk["keyframes"]:
        x = next(b for b in baked if b["frame"] == kf["frame"])
        fr, prev = frame_export(x, prev)
        fr.update(
            name=kf["name"],
            ease_arriving=kf["ease"],
            note=kf["note"],
            cues=kf["cue"],
            planted_feet={k: vec(v) for k, v in kf["sol"]["feet"].items()},
            free_leg=[s for s in ("R", "L") if not (isinstance(kf["legs"][s], dict) and "plant" in kf["legs"][s])],
        )
        kf_out.append(fr)
    prev, frames = {}, []
    for x in baked:
        fr, prev = frame_export(x, prev)
        frames.append(fr)
    return dict(
        id=atk["id"],
        name=atk["name"],
        summary=atk["short"],
        strike_marker=atk["strike_tip"],
        contact_frame=atk["contact_frame"],
        contact_time=r4(atk["contact_frame"] / D.FPS),
        last_frame=atk["keyframes"][-1]["frame"],
        duration_s=r4(atk["keyframes"][-1]["frame"] / D.FPS),
        validation=met,
        keyframes=kf_out,
        baked_frames=frames,
    )


META = {
    "format": "R6 M1 combo, keyframes + every baked 60 fps frame",
    "fps": D.FPS,
    "rig": "R6, default proportions: Torso 2x2x1, Head 2x1x1, arms/legs 1x2x1; HRP centre is 3 studs above the floor",
    "axes_hrp_frame": "+X = character's right, +Y = up, -Z = forward (toward the target). Positions are studs relative to the HumanoidRootPart at frame 0.",
    "joint_rotation_convention": (
        "joints[J].euler_xyz_deg = [x, y, z] degrees applied as Rx(x)*Ry(y)*Rz(z) (Roblox CFrame.Angles order: "
        "Z first, then Y, then X), expressed in TORSO space and applied about the joint pivot by pre-multiplying the "
        "Motor6D's C0 rotation:  C0' = CFrame.new(C0.Position) * CFrame.Angles(x,y,z) * C0.Rotation  "
        "(this is exactly what src/ReplicatedStorage/Combat/Poses.lua does). Zero everywhere = default R6 rest pose."
    ),
    "motor6d_transform": (
        "joints[J].transform_quat_xyzw / transform_euler_xyz_deg / transform_pos is the SAME pose expressed as a "
        "Motor6D.Transform (what an AnimationTrack / KeyframeSequence Pose stores): Part1 = Part0 * C0 * Transform * C1:Inverse(). "
        "transform_quat_xyzw is order-agnostic: CFrame.new(px,py,pz, qx,qy,qz,qw). Only the Root joint has a translation "
        "(transform_pos, in RootJoint space); it is how the torso sits relative to the HumanoidRootPart (torso_offset_hrp, in HRP axes)."
    ),
    "interpolation": "Between keyframes: quaternion slerp of each joint with the easing named on the ARRIVING keyframe (ease_arriving); torso offset is lerped with the same alpha. baked_frames is exactly that, evaluated on every integer frame.",
    "easings": {"Linear": "t", "CubicOut": "1-(1-t)^3", "CubicIn": "t^3", "CubicInOut": "4t^3 (t<0.5) else 1-(-2t+2)^3/2"},
    "code_lunge": "Config.M1.Lunge for Config.M1.LungeTime is applied by the game as physics at swing start. It is NOT animated; baked frames only report it (code_lunge_forward) so reach can be checked. The HumanoidRootPart must not be moved by the animation.",
    "foot_planting": "Planted feet are solved with IK to fixed floor footprints; torso_offset_hrp.y already contains the stance height. Joint values therefore already include the leg IK; just play the joint data.",
    "dummy": f"The storyboard target is a pale R6 dummy whose chest front face is {abs(D.DUMMY_FRONT_Z)} studs in front of the start position (Z = {D.DUMMY_FRONT_Z}); contact_vs_dummy_z in validation is the strike marker's Z minus that face (0 = touching, negative = through it).",
    "timing_source": "contact_frame 7 = Config.M1.Windup (0.11s) at 60 fps; M1_1..M1_3 are 20 frames (Config.M1.SwingCooldown 0.32s); the finisher is 51 frames (Config.M1.EndLag 0.85s).",
    "markers": "RightFist/LeftFist = centre of the arm's free end, RightFoot/LeftFoot = centre of the leg's free end, in world studs relative to the start HRP, including code_lunge_forward.",
}


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def trail_points(baked, tip, upto):
    return [x["fk"]["tips"][tip] for x in baked if x["frame"] <= upto]


def cell_img(b, view, atk, baked, size, trail=True):
    sc, ctr = render.view_geometry(view)
    sc = sc * size / 290.0
    contact = b["frame"] == atk["contact_frame"]
    return render.render_cell(
        b["fk"], view, size, size, sc, ctr, D.DUMMY_FRONT_Z,
        trail=trail_points(baked, atk["strike_tip"], b["frame"]) if trail else None,
        tip_name=atk["strike_tip"], contact=contact,
    )


def keyframe_sheet(atk, baked, cell=290):
    views = ["side", "front", "top"]
    kfs = atk["keyframes"]
    by_frame = {x["frame"]: x for x in baked}
    lm, tm, cap = 96, 64, 46
    W_ = lm + len(kfs) * cell
    H_ = tm + len(views) * (cell + cap)
    sheet = Image.new("RGB", (W_, H_), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((14, 10), f"{atk['id']}  -  {atk['name']}", font=render.font(24, True), fill=(20, 20, 30))
    d.text((14, 40), f"{atk['short']}   |   60 fps   |   contact frame {atk['contact_frame']} ({atk['contact_frame']/D.FPS:.3f}s)   |   red line = path of {atk['strike_tip']}   |   grey ghost = target dummy",
           font=render.font(13), fill=(70, 70, 80))
    for r, view in enumerate(views):
        y0 = tm + r * (cell + cap)
        d.text((8, y0 + cell // 2 - 18), render.VIEWS[view][2].split(" (")[0], font=render.font(14, True), fill=(40, 40, 50))
        for c, kf in enumerate(kfs):
            b = by_frame[kf["frame"]]
            img = cell_img(b, view, atk, baked, cell)
            x0 = lm + c * cell
            sheet.paste(img, (x0, y0))
            d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], outline=(180, 176, 168))
            hot = (200, 40, 30) if kf["frame"] == atk["contact_frame"] else (30, 30, 40)
            d.text((x0 + 6, y0 + cell + 4), f"f{kf['frame']}  {kf['frame']/D.FPS:.3f}s", font=render.font(13, True), fill=hot)
            d.text((x0 + 6, y0 + cell + 22), kf["name"], font=render.font(13), fill=hot)
    return sheet


def allframes_sheet(atk, baked, cell=170, cols=10):
    key_frames = {k["frame"] for k in atk["keyframes"]}
    n = len(baked)
    rows = math.ceil(n / cols)
    views = ["side", "front"]
    tm, cap = 54, 20
    blk = cell + cap
    W_ = cols * cell
    H_ = tm + rows * len(views) * blk
    sheet = Image.new("RGB", (W_, H_), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), f"{atk['id']} {atk['name']} - every frame @60fps (side view above front view). KEY = authored keyframe.", font=render.font(16, True), fill=(20, 20, 30))
    d.text((10, 32), "red = contact frame", font=render.font(12), fill=(160, 40, 30))
    for i, b in enumerate(baked):
        rr, cc = divmod(i, cols)
        for vi, view in enumerate(views):
            img = cell_img(b, view, atk, baked, cell, trail=False)
            x0 = cc * cell
            y0 = tm + (rr * len(views) + vi) * blk
            sheet.paste(img, (x0, y0))
            d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], outline=(200, 196, 188))
            if vi == 0:
                pass
            hot = (200, 40, 30) if b["frame"] == atk["contact_frame"] else (30, 30, 40)
            tag = f"f{b['frame']}" + ("  KEY" if b["frame"] in key_frames else "")
            d.text((x0 + 4, y0 + cell + 2), tag if vi == 0 else f"{b['frame']/D.FPS:.3f}s", font=render.font(11, True), fill=hot)
    return sheet


def overview_sheet(all_baked, cell=250):
    cols = ["Load", "Fire", "CONTACT", "Follow-through"]
    lm, tm = 150, 64
    W_ = lm + len(cols) * cell
    H_ = tm + len(D.ATTACKS) * (cell + 20) + 10
    sheet = Image.new("RGB", (W_, H_), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((14, 10), "M1 combo at a glance (front 3/4 view)  -  4-hit string: Straight > Hook > Overhand > Roundhouse", font=render.font(20, True), fill=(20, 20, 30))
    d.text((14, 38), "Right limbs = orange/red, left limbs = blue. Grey ghost = target. Red line = strike path. Burst = contact frame.", font=render.font(13), fill=(70, 70, 80))
    for r, atk in enumerate(D.ATTACKS):
        baked = all_baked[atk["id"]]
        by_frame = {x["frame"]: x for x in baked}
        y0 = tm + r * (cell + 20)
        d.text((8, y0 + cell // 2 - 22), atk["id"], font=render.font(15, True), fill=(20, 20, 30))
        d.text((8, y0 + cell // 2), atk["name"], font=render.font(12), fill=(60, 60, 70))
        for c, name in enumerate(cols):
            alias = {"Load": ("Load", "Chamber"), "Fire": ("Fire", "Whip")}.get(name, (name,))
            kf = next((k for k in atk["keyframes"] if k["name"] in alias), None)
            if not kf:
                continue
            name = kf["name"] if kf["name"] != "CONTACT" else "CONTACT"
            b = by_frame[kf["frame"]]
            img = cell_img(b, "front", atk, baked, cell)
            x0 = lm + c * cell
            sheet.paste(img, (x0, y0))
            d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], outline=(180, 176, 168))
            hot = (200, 40, 30) if name == "CONTACT" else (30, 30, 40)
            d.text((x0 + 5, y0 + cell + 3), f"f{kf['frame']}  {name}", font=render.font(11, True), fill=hot)
    return sheet


def preview_gif(all_baked, path, cell=270):
    frames = []
    for atk in D.ATTACKS:
        baked = all_baked[atk["id"]]
        for b in baked:
            tiles = [cell_img(b, v, atk, baked, cell, trail=True) for v in ("side", "front", "top")]
            img = Image.new("RGB", (cell * 3, cell + 30), (255, 255, 255))
            for i, t in enumerate(tiles):
                img.paste(t, (i * cell, 30))
            dd = ImageDraw.Draw(img)
            hot = (200, 40, 30) if b["frame"] == atk["contact_frame"] else (30, 30, 40)
            dd.text((8, 6), f"{atk['id']} {atk['name']}   frame {b['frame']:>2}   {b['frame']/D.FPS:.3f}s" + ("   CONTACT" if b["frame"] == atk["contact_frame"] else ""),
                    font=render.font(15, True), fill=hot)
            frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=128))
        # brief neutral hold between attacks so each reads as its own move
        frames.extend([frames[-1]] * 4)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=36, loop=0, optimize=True, disposal=2)


# --------------------------------------------------------------------------
def main(only):
    os.makedirs(OUT, exist_ok=True)
    all_baked, exported, ok = {}, [], True
    for atk in D.ATTACKS:
        solve_attack(atk)
        baked = bake(atk)
        all_baked[atk["id"]] = baked
        met = metrics(atk, baked)
        err = roblox_check(baked)
        met["roblox_transform_roundtrip_max_error"] = float(f"{err:.2e}")
        print(f"[{atk['id']}] {atk['name']}")
        print(f"    contact tip {met['contact_tip_world']}  vs dummy face z={D.DUMMY_FRONT_Z}: {met['contact_vs_dummy_z']:+.2f}")
        print(f"    floor penetration {met['max_floor_penetration']:.2f} | planted-foot slide {met['max_planted_foot_slide']:.2f} | planted-foot float {met['max_planted_foot_float']:.2f} | C0/Transform roundtrip err {err:.1e}")
        ok = ok and err < 1e-6
        exported.append(export_attack(atk, baked, met))
        if only and atk["id"] not in only:
            continue
        keyframe_sheet(atk, baked).save(os.path.join(OUT, f"{atk['id']}_keyframes.png"))
        allframes_sheet(atk, baked).save(os.path.join(OUT, f"{atk['id']}_allframes.png"))
    if not only:
        overview_sheet(all_baked).save(os.path.join(OUT, "combo_overview.png"))
        preview_gif(all_baked, os.path.join(OUT, "combo_preview.gif"))
        with open(os.path.join(HERE, "m1_combo.json"), "w") as f:
            json.dump({"meta": META, "attacks": exported}, f, indent=1)
        print("wrote m1_combo.json, overview, gif")
    if not ok:
        sys.exit("Roblox transform round-trip failed")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
