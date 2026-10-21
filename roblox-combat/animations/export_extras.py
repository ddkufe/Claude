"""Generate the human-readable spec (M1_COMBO_SPEC.md) and the Studio builder
(BuildM1Animations.lua) from m1_combo.json, so neither can drift from the data.

    python3 export_extras.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(os.path.join(HERE, "m1_combo.json")))
META = SRC["meta"]

JOINT_ORDER = ["Root", "Neck", "RightShoulder", "LeftShoulder", "RightHip", "LeftHip"]
SHORT = {"Root": "Root (torso)", "Neck": "Neck", "RightShoulder": "R shoulder", "LeftShoulder": "L shoulder", "RightHip": "R hip", "LeftHip": "L hip"}
# JSON joint -> KeyframeSequence pose name (the Motor6D's Part1)
POSE_NAME = {"Root": "Torso", "Neck": "Head", "RightShoulder": "Right Arm", "LeftShoulder": "Left Arm", "RightHip": "Right Leg", "LeftHip": "Left Leg"}
EASE_STYLE = {"Linear": ("Linear", "Out"), "CubicOut": ("Cubic", "Out"), "CubicIn": ("Cubic", "In"), "CubicInOut": ("Cubic", "InOut")}


def f(v):
    return f"{v:g}"


def vec_s(v, nd=1):
    return "[" + ", ".join(f"{x:.{nd}f}" for x in v) + "]"


def dir_word(d):
    x, y, z = d
    parts = []
    if y > 0.5:
        parts.append("up")
    elif y < -0.5:
        parts.append("down")
    elif abs(y) <= 0.25:
        parts.append("level")
    if z < -0.45:
        parts.append("forward")
    elif z > 0.45:
        parts.append("back")
    if x > 0.35:
        parts.append("right")
    elif x < -0.35:
        parts.append("left")
    return " ".join(parts) or "mixed"


def write_spec():
    L = []
    A = L.append
    A("# M1 combo: frame-by-frame animation spec (R6)\n")
    A("A 4-hit string: **Right Straight > Left Hook > Right Overhand > Roundhouse Finisher**. Generated from `m1_combo.json` (the source of truth); the pictures in `storyboards/` are rendered from the same numbers.\n")
    A("## Files\n")
    A("| File | What it is |")
    A("|---|---|")
    A("| `m1_combo.json` | Every keyframe **and every baked 60 fps frame**: joint rotations (Euler + quaternion), Motor6D Transform values, torso offset, strike-marker positions, easing, cues, validation numbers |")
    A("| `storyboards/combo_overview.png` | Whole combo on one page |")
    A("| `storyboards/M1_n_keyframes.png` | Keyframes of one attack in 3 views (side / front 3/4 / top-down), with the strike path in red |")
    A("| `storyboards/M1_n_allframes.png` | **Every frame** of one attack (side above front) |")
    A("| `storyboards/combo_preview.gif` | Slow-motion loop of the whole combo |")
    A("| `BuildM1Animations.lua` | Studio script that builds real `KeyframeSequence` objects from this data |\n")
    A("## How to read the pictures\n")
    A("- The fighter faces **right** in the side view. **Orange/red = right limbs, blue = left limbs.** Two dots = eyes (shows where the head looks).")
    A("- Pale grey ghost = the target, its chest face exactly where the game's hitbox is centred.")
    A("- Red line = path of the striking fist/foot up to that frame. Yellow burst = contact frame (hitbox spawns).")
    A("- The fighter slides toward the target over frames 0-5: that is the game's code-driven lunge (16 studs/s for 0.09s), **not** part of the animation.\n")
    A("## Conventions\n")
    A(f"- **Frame rate:** {META['fps']} fps. Frame 0 = the moment the swing input arrives.")
    A(f"- **Axes (HumanoidRootPart frame):** {META['axes_hrp_frame']}")
    A(f"- **Joint rotation:** {META['joint_rotation_convention']}")
    A(f"- **Same pose as Motor6D.Transform:** {META['motor6d_transform']}")
    A(f"- **Interpolation:** {META['interpolation']}")
    A(f"- **Foot planting:** {META['foot_planting']}")
    A(f"- **Code lunge:** {META['code_lunge']}")
    A(f"- **Timing:** {META['timing_source']}\n")
    A("Rough feel for the angles: shoulder **x = 90** points the arm straight ahead, **x = 180** straight up, **x = -90** straight back; a right-arm **z** > 0 swings it out to the right, a left-arm **z** < 0 out to the left. Root **y** > 0 turns the chest to the left, which brings the **right** shoulder forward; Root **x** < 0 leans forward.\n")

    for atk in SRC["attacks"]:
        v = atk["validation"]
        A(f"---\n\n## {atk['id']}: {atk['name']}\n")
        A(f"*{atk['summary']}*\n")
        A(f"- Plays **frames 0-{atk['last_frame']}** = {atk['last_frame']} frames ({atk['duration_s']:.3f}s). Contact on **frame {atk['contact_frame']}** ({atk['contact_time']:.3f}s) with the **{atk['strike_marker']}**.")
        A(f"- Strike marker at contact: x {v['contact_tip_world'][0]:+.2f}, y {v['contact_tip_world'][1]:+.2f}, z {v['contact_tip_world'][2]:+.2f} (target face z = -4.6, offset {v['contact_vs_dummy_z']:+.2f}).")
        A(f"- Checks: floor penetration {v['max_floor_penetration']:.2f} studs, planted-foot slide {v['max_planted_foot_slide']:.2f}, planted-foot heel-lift {v['max_planted_foot_float']:.2f}.")
        A(f"- Pictures: `storyboards/{atk['id']}_keyframes.png`, `storyboards/{atk['id']}_allframes.png`.\n")
        A("### Keyframes\n")
        A("Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.\n")
        A("| Frame | Time | Phase | ease | " + " | ".join(SHORT[j] for j in JOINT_ORDER) + " | Torso offset (HRP) |")
        A("|---|---|---|---|" + "---|" * (len(JOINT_ORDER) + 1))
        for kf in atk["keyframes"]:
            cells = [vec_s(kf["joints"][j]["euler_xyz_deg"]) for j in JOINT_ORDER]
            A(f"| {kf['frame']} | {kf['time']:.3f}s | **{kf['name']}** | {kf['ease_arriving']} | " + " | ".join(cells) + f" | {vec_s(kf['torso_offset_hrp'], 2)} |")
        A("")
        A("### What the body is doing\n")
        for kf in atk["keyframes"]:
            dirs = ", ".join(
                f"{n} {dir_word(kf['joints'][j]['limb_dir_world'])}"
                for n, j in (("R arm", "RightShoulder"), ("L arm", "LeftShoulder"), ("R leg", "RightHip"), ("L leg", "LeftHip"))
            )
            A(f"- **f{kf['frame']} {kf['name']}**: {kf['note']}  \n  *In world terms:* {dirs}.")
            if kf["cues"]:
                A(f"  *Cues:* " + "; ".join(kf["cues"]) + ".")
        A("")

    A("---\n\n## Recreating it\n")
    A("1. **Easiest:** run `BuildM1Animations.lua` in Studio (instructions in its header). It creates `M1_1` ... `M1_4` KeyframeSequences from the keyframes above, under the selected rig's `AnimSaves` folder so the Animation Editor lists them. Open each, check it, publish, then paste the animation ids into `Config.Animations` (`Jab1`, `Jab2`, `Jab3`, `Finisher`).")
    A("2. **By hand / with another tool:** place poses at each keyframe time with the Euler values above (or the exact `transform_quat_xyzw` in the JSON), honouring `ease`. `baked_frames` in the JSON are what the result should look like on every integer frame; compare against `storyboards/*_allframes.png`.")
    A("3. Do **not** animate the HumanoidRootPart's position; forward travel comes from the game's lunge.")
    A("4. Keep animation priority **Action** so it overrides walk/idle.\n")
    A("## Honest caveats\n")
    A("- Poses were authored and checked in a software model of the R6 rig, not in Roblox Studio. The joint maths is verified against the Roblox Motor6D formula (`Part1 = Part0 * C0 * Transform * C1:Inverse()`, error < 1e-15), but **nothing here has been played in Studio**.")
    A("- The KeyframeSequence's per-pose easing semantics (does it describe the move *into* or *out of* the keyframe) is assumed to be 'into'; if it looks off in the Animation Editor, flip the easing direction.")
    A("- R6 arms and legs are rigid (no elbows/knees), so punches are straight-armed and guards are approximate.")
    A("- During the M1_1 load (frames 2-4) the planted feet shuffle up to ~0.5 studs; a few frames show a small heel-lift on the rear foot. Both are intentional compromises of a deep coil on rigid legs.")
    open(os.path.join(HERE, "M1_COMBO_SPEC.md"), "w").write("\n".join(L) + "\n")


def lua_num(x):
    return f"{x:.5f}".rstrip("0").rstrip(".") if abs(x) > 1e-9 else "0"


def write_lua():
    out = []
    A = out.append
    A("""-- BuildM1Animations.lua  (generated by export_extras.py from m1_combo.json - do not hand-edit)
--
-- Builds the 4 M1 combo animations as KeyframeSequence objects.
--
-- USE IN ROBLOX STUDIO
--   1. Insert an R6 rig (Avatar tab > Rig Builder > R6) and SELECT it in the Explorer.
--   2. View > Command Bar, paste this whole file, press Enter.
--   3. Open the Animation Editor on that rig, click the "..." menu > Load, pick M1_1..M1_4.
--   4. Check, then Publish each one and paste the ids into ReplicatedStorage.Combat.Config.Animations
--      (Jab1 = M1_1, Jab2 = M1_2, Jab3 = M1_3, Finisher = M1_4).
-- If nothing is selected the sequences are put in ServerStorage instead.
--
-- Each pose CFrame is the Motor6D.Transform for that joint (position only on the torso).
-- Easing is applied to the keyframe the motion ARRIVES at; flip it in the editor if it looks off.

local ServerStorage = game:GetService("ServerStorage")
local Selection = game:GetService("Selection")

-- t = seconds, ease = {style, direction}, joints = {px,py,pz, qx,qy,qz,qw}
local DATA = {""")
    for atk in SRC["attacks"]:
        length = atk["keyframes"][-1]["time"]
        A(f'\t{{ name = "{atk["id"]}", label = "{atk["name"]}", length = {lua_num(length)}, keyframes = {{')
        for kf in atk["keyframes"]:
            st, di = EASE_STYLE[kf["ease_arriving"]]
            A(f'\t\t{{ t = {lua_num(kf["time"])}, ease = {{ "{st}", "{di}" }}, poses = {{')
            for j in JOINT_ORDER:
                jd = kf["joints"][j]
                q = jd["transform_quat_xyzw"]
                p = jd.get("transform_pos", [0, 0, 0])
                nums = ", ".join(lua_num(x) for x in (*p, *q))
                A(f'\t\t\t["{POSE_NAME[j]}"] = {{ {nums} }},')
            A("\t\t} },")
        A("\t} },")
    A("}")
    A("""
local function poseCFrame(n)
	return CFrame.new(n[1], n[2], n[3], n[4], n[5], n[6], n[7])
end

local function makePose(name, n, ease, weight)
	local pose = Instance.new("Pose")
	pose.Name = name
	pose.CFrame = poseCFrame(n)
	pose.Weight = weight or 1
	pose.EasingStyle = Enum.PoseEasingStyle[ease[1]]
	pose.EasingDirection = Enum.PoseEasingDirection[ease[2]]
	return pose
end

local function build(anim)
	local sequence = Instance.new("KeyframeSequence")
	sequence.Name = anim.name
	sequence.Loop = false
	sequence.Priority = Enum.AnimationPriority.Action

	for _, kf in ipairs(anim.keyframes) do
		local keyframe = Instance.new("Keyframe")
		keyframe.Time = kf.t
		keyframe.Name = string.format("%s @ %.3f", anim.label, kf.t)

		-- R6 hierarchy: HumanoidRootPart > Torso > {Head, Left Arm, Right Arm, Left Leg, Right Leg}
		local root = Instance.new("Pose")
		root.Name = "HumanoidRootPart"
		root.CFrame = CFrame.new()
		root.Weight = 0
		local torso = makePose("Torso", kf.poses["Torso"], kf.ease)
		torso.Parent = root
		for _, limb in ipairs({ "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }) do
			makePose(limb, kf.poses[limb], kf.ease).Parent = torso
		end
		keyframe:AddPose(root)
		sequence:AddKeyframe(keyframe)
	end
	return sequence
end

local rig = Selection:Get()[1]
local holder
if rig and rig:IsA("Model") then
	holder = rig:FindFirstChild("AnimSaves")
	if not holder then
		holder = Instance.new("Folder")
		holder.Name = "AnimSaves"
		holder.Parent = rig
	end
else
	holder = ServerStorage
	warn("No rig selected: putting the KeyframeSequences in ServerStorage.")
end

for _, anim in ipairs(DATA) do
	local old = holder:FindFirstChild(anim.name)
	if old then
		old:Destroy()
	end
	build(anim).Parent = holder
	print("Built", anim.name, anim.label, "into", holder:GetFullName())
end""")
    open(os.path.join(HERE, "BuildM1Animations.lua"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    write_spec()
    write_lua()
    print("wrote M1_COMBO_SPEC.md and BuildM1Animations.lua")
