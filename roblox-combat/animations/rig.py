"""R6 forward kinematics, pose interpolation, ground solving and a tiny
software renderer for animation storyboards.

Conventions (identical to src/ReplicatedStorage/Combat/Poses.lua):
  * Everything is in the HumanoidRootPart frame: +X = character's right,
    +Y = up, -Z = forward (toward the target).
  * A joint rotation is Rx(x) * Ry(y) * Rz(z) (Roblox CFrame.Angles order:
    Z is applied first, then Y, then X), expressed in TORSO space and applied
    about the joint's pivot. Angles are degrees in the data files.
  * Zero = default R6 rest pose (arms and legs hanging straight down).
"""

import math

import numpy as np

DEG = math.pi / 180.0
JOINTS = ["Root", "Neck", "RightShoulder", "LeftShoulder", "RightHip", "LeftHip"]
GROUND_Y = -3.0  # HRP center is 3 studs above the floor on an R6 rig


# --------------------------------------------------------------------------
# rotations
# --------------------------------------------------------------------------
def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def euler_deg(v):
    x, y, z = (a * DEG for a in v)
    return rx(x) @ ry(y) @ rz(z)


def mat_to_quat(m):
    """Rotation matrix -> unit quaternion (w, x, y, z)."""
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    q = np.array(q, dtype=float)
    return q / np.linalg.norm(q)


def quat_to_mat(q):
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def slerp(q0, q1, t):
    d = float(np.dot(q0, q1))
    if d < 0:
        q1, d = -q1, -d
    if d > 0.9995:
        q = q0 + t * (q1 - q0)
        return q / np.linalg.norm(q)
    th = math.acos(d)
    return (math.sin((1 - t) * th) * q0 + math.sin(t * th) * q1) / math.sin(th)


def ease(name, t):
    t = min(1.0, max(0.0, t))
    if name == "Linear":
        return t
    if name == "CubicOut":
        return 1 - (1 - t) ** 3
    if name == "CubicIn":
        return t**3
    if name == "CubicInOut":
        return 4 * t**3 if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2
    if name == "Constant":
        return 0.0 if t < 1 else 1.0
    raise ValueError(name)


# --------------------------------------------------------------------------
# R6 geometry (torso-local; torso center is the origin; torso faces -Z)
# --------------------------------------------------------------------------
# pivot: where the Motor6D sits.  offset: pivot -> part center at rest.
PARTS = {
    "Torso": dict(size=(2, 2, 1), pivot=None, offset=None),
    "Head": dict(size=(2, 1, 1), pivot=(0, 1, 0), offset=(0, 0.5, 0), joint="Neck"),
    "RightArm": dict(size=(1, 2, 1), pivot=(1, 0.5, 0), offset=(0.5, -0.5, 0), joint="RightShoulder"),
    "LeftArm": dict(size=(1, 2, 1), pivot=(-1, 0.5, 0), offset=(-0.5, -0.5, 0), joint="LeftShoulder"),
    "RightLeg": dict(size=(1, 2, 1), pivot=(1, -1, 0), offset=(-0.5, -1, 0), joint="RightHip"),
    "LeftLeg": dict(size=(1, 2, 1), pivot=(-1, -1, 0), offset=(0.5, -1, 0), joint="LeftHip"),
}
TIPS = {  # tip = center of the limb's free end, as a pivot-relative rest vector
    "RightFist": ("RightArm", (0.5, -1.5, 0)),
    "LeftFist": ("LeftArm", (-0.5, -1.5, 0)),
    "RightFoot": ("RightLeg", (-0.5, -2.0, 0)),
    "LeftFoot": ("LeftLeg", (0.5, -2.0, 0)),
}


def forward_kinematics(pose, torso_offset=(0, 0, 0), world_offset=(0, 0, 0)):
    """Return {'parts': {name: (center, R, size)}, 'tips': {name: xyz}}."""
    t0 = np.array(torso_offset, dtype=float) + np.array(world_offset, dtype=float)
    r_root = euler_deg(pose.get("Root", (0, 0, 0)))
    parts, tips = {}, {}
    parts["Torso"] = (t0.copy(), r_root, np.array(PARTS["Torso"]["size"], dtype=float))
    jr = {}
    for name, spec in PARTS.items():
        if spec["pivot"] is None:
            continue
        r_j = euler_deg(pose.get(spec["joint"], (0, 0, 0)))
        jr[name] = r_j
        pivot = np.array(spec["pivot"], dtype=float)
        center_local = pivot + r_j @ np.array(spec["offset"], dtype=float)
        parts[name] = (t0 + r_root @ center_local, r_root @ r_j, np.array(spec["size"], dtype=float))
    for tip, (part, vec) in TIPS.items():
        pivot = np.array(PARTS[part]["pivot"], dtype=float)
        tips[tip] = t0 + r_root @ (pivot + jr[part] @ np.array(vec, dtype=float))
    return {"parts": parts, "tips": tips}


def box_corners(center, r, size):
    sx, sy, sz = size / 2
    pts = []
    for dx in (-sx, sx):
        for dy in (-sy, sy):
            for dz in (-sz, sz):
                pts.append(center + r @ np.array([dx, dy, dz]))
    return np.array(pts)


def foot_low(fk, side):
    c, r, s = fk["parts"][side + "Leg"]
    return box_corners(c, r, s)[:, 1].min()


def shortest_arc(a, b):
    """Rotation matrix taking unit direction a onto unit direction b."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    c = float(np.dot(a, b))
    if c < -0.999999:
        axis = np.cross(a, [1.0, 0.0, 0.0])
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(a, [0.0, 0.0, 1.0])
        axis /= np.linalg.norm(axis)
        k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + 2 * (k @ k)
    v = np.cross(a, b)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + (k @ k) / (1 + c)


LEG_LEN = math.hypot(0.5, 2.0)  # pivot -> bottom-centre of a leg


def _joint_matrix(spec, r_root):
    """A joint spec is [x,y,z] (torso space) or {'world': [x,y,z]} (HRP space)."""
    if isinstance(spec, dict):
        return r_root.T @ euler_deg(spec["world"])
    return euler_deg(spec)


def solve_pose(kf):
    """Turn an authored keyframe into joint rotations + torso translation.

    kf['pose']  : Root, Neck, RightShoulder, LeftShoulder (torso-space list or {'world': list})
    kf['legs']  : {'R': leg, 'L': leg}; leg = {'plant': [x, z]} -> IK onto that floor
                  footprint, or {'world': [x,y,z]} / [x,y,z] for a free (kicking) leg
    kf['shift'] : [x, z] preferred torso position relative to the HRP. With both feet
                  planted only the component along the line that keeps both feet exactly
                  on their footprints is used.
    Returns dict(rot={joint: 3x3 local rotation}, off=[x, y, z], feet={side: (x, y, z)}).
    """
    pose = kf["pose"]
    r_root = euler_deg(pose.get("Root", (0, 0, 0)))
    rot = {"Root": r_root}
    for j in ("Neck", "RightShoulder", "LeftShoulder"):
        rot[j] = _joint_matrix(pose.get(j, (0, 0, 0)), r_root)

    legs = kf["legs"]
    side_name = {"R": "RightLeg", "L": "LeftLeg"}
    joint_name = {"R": "RightHip", "L": "LeftHip"}
    pivot0 = {k: r_root @ np.array(PARTS[side_name[k]]["pivot"], dtype=float) for k in "RL"}
    q_xz = {k: pivot0[k][[0, 2]] for k in "RL"}
    v0 = {k: np.array(TIPS["RightFoot" if k == "R" else "LeftFoot"][1], dtype=float) for k in "RL"}
    planted = {k: np.array(legs[k]["plant"], dtype=float) for k in "RL" if isinstance(legs[k], dict) and "plant" in legs[k]}

    want = np.array(kf.get("shift", (0.0, 0.0)), dtype=float)

    def need_y(k, txz_):
        d = min(float(np.linalg.norm(planted[k] - (txz_ + q_xz[k]))), LEG_LEN - 1e-3)
        return GROUND_Y + math.sqrt(LEG_LEN**2 - d**2) - pivot0[k][1]

    txz = want.copy()
    if len(planted) == 2:
        # Both feet must reach their footprints at ONE torso height. The torso position
        # that does that lies on a curve; start on the equal-distance line and Newton-step
        # the height mismatch to zero, staying as close to the authored shift as possible.
        a = planted["L"] - q_xz["L"]
        b = planted["R"] - q_xz["R"]
        diff = b - a
        if np.linalg.norm(diff) > 1e-6:
            d_hat = np.array([-diff[1], diff[0]]) / np.linalg.norm(diff)
            mid = (a + b) / 2
            txz = mid + d_hat * float(np.dot(want - mid, d_hat))
        start_txz = txz.copy()
        converged = False
        for _ in range(40):
            g = need_y("L", txz) - need_y("R", txz)
            if abs(g) < 1e-9:
                converged = True
                break
            grad = np.zeros(2)
            for i in range(2):
                e = np.zeros(2)
                e[i] = 1e-5
                grad[i] = ((need_y("L", txz + e) - need_y("R", txz + e)) - g) / 1e-5
            nn = float(np.dot(grad, grad))
            if nn < 1e-12:
                break
            step = g * grad / nn
            norm = float(np.linalg.norm(step))
            if norm > 0.15:
                step *= 0.15 / norm
            txz = txz - step
        if not converged or float(np.linalg.norm(txz - want)) > 1.5:
            txz = start_txz  # no exact two-foot solution nearby: keep the equal-distance point
    ys = [need_y(k, txz) for k in planted]
    ty = float(np.mean(ys)) if ys else 0.0
    t0 = np.array([txz[0], ty, txz[1]])

    world_leg, feet = {}, {}
    for k in "RL":
        if k in planted:
            piv = t0 + pivot0[k]
            drop = piv[1] - GROUND_Y
            reach = math.sqrt(max(LEG_LEN**2 - drop**2, 0.0))
            to = planted[k] - piv[[0, 2]]
            n = float(np.linalg.norm(to))
            u = to / n if n > 1e-6 else np.array([0.0, -1.0])
            foot = np.array([piv[0] + u[0] * reach, GROUND_Y, piv[2] + u[1] * reach])
            world_leg[k] = shortest_arc(v0[k], foot - piv)
            feet[k] = foot
        else:
            world_leg[k] = _free_leg_world(legs[k], r_root)

    if planted:  # the tilted box's lowest corner, not its bottom-centre, must touch the floor
        lows = []
        for k in planted:
            piv = t0 + pivot0[k]
            c = piv + world_leg[k] @ np.array(PARTS[side_name[k]]["offset"], dtype=float)
            lows.append(box_corners(c, world_leg[k], np.array(PARTS[side_name[k]]["size"], dtype=float))[:, 1].min())
        dy = GROUND_Y - min(lows)
        ty += dy
        for k in feet:
            feet[k] = feet[k] + np.array([0.0, dy, 0.0])

    for k in "RL":
        rot[joint_name[k]] = r_root.T @ world_leg[k]
    return dict(rot=rot, off=[float(txz[0]), float(ty), float(txz[1])], feet={k: [float(x) for x in v] for k, v in feet.items()})


def _free_leg_world(spec, r_root):
    if isinstance(spec, dict):
        return euler_deg(spec["world"])
    return r_root @ euler_deg(spec)


def interpolate(kf_a, kf_b, f):
    """Joint rotation matrices + torso offset at integer frame f."""
    span = kf_b["frame"] - kf_a["frame"]
    a = ease(kf_b.get("ease", "Linear"), (f - kf_a["frame"]) / span)
    rot = {}
    for j in JOINTS:
        qa = mat_to_quat(kf_a["sol"]["rot"][j])
        qb = mat_to_quat(kf_b["sol"]["rot"][j])
        rot[j] = quat_to_mat(slerp(qa, qb, a))
    off = (1 - a) * np.array(kf_a["sol"]["off"]) + a * np.array(kf_b["sol"]["off"])
    return rot, off


def forward_kinematics_mats(rot, torso_offset, world_offset=(0, 0, 0)):
    """Like forward_kinematics but joints are already rotation matrices."""
    t0 = np.array(torso_offset, dtype=float) + np.array(world_offset, dtype=float)
    r_root = rot["Root"]
    parts, tips = {}, {}
    parts["Torso"] = (t0.copy(), r_root, np.array(PARTS["Torso"]["size"], dtype=float))
    jr = {}
    for name, spec in PARTS.items():
        if spec["pivot"] is None:
            continue
        r_j = rot[spec["joint"]]
        jr[name] = r_j
        pivot = np.array(spec["pivot"], dtype=float)
        center_local = pivot + r_j @ np.array(spec["offset"], dtype=float)
        parts[name] = (t0 + r_root @ center_local, r_root @ r_j, np.array(spec["size"], dtype=float))
    for tip, (part, vec) in TIPS.items():
        pivot = np.array(PARTS[part]["pivot"], dtype=float)
        tips[tip] = t0 + r_root @ (pivot + jr[part] @ np.array(vec, dtype=float))
    return {"parts": parts, "tips": tips}


def mat_to_euler_deg(m, near=None):
    """Rx*Ry*Rz decomposition (degrees). `near` picks the branch closest to it."""
    sy = float(np.clip(m[0, 2], -1.0, 1.0))
    y = math.asin(sy)
    if abs(sy) < 0.99999:
        x = math.atan2(-m[1, 2], m[2, 2])
        z = math.atan2(-m[0, 1], m[0, 0])
    else:
        x = math.atan2(m[2, 1], m[1, 1])
        z = 0.0
    cand = [(x, y, z), (x + math.pi, math.pi - y, z + math.pi)]
    cand = [tuple(((a / DEG + 180) % 360) - 180 for a in c) for c in cand]
    if near is None:
        return list(cand[0])
    return list(min(cand, key=lambda c: sum(min(abs(c[i] - near[i]), 360 - abs(c[i] - near[i])) for i in range(3))))
