# Ninja combat stance: frame-by-frame animation spec (R6)

The stance the character drops into when a fight starts, holds with a breathing loop, drops back out of, and keeps (upper body only) while moving. **Its idle pose is exactly the 'Ready' pose the M1 combo starts and ends in**, so every punch flows out of it and back into it. Generated from `stance.json` (the source of truth); the pictures in `storyboards/` are rendered from the same numbers.

## The stance in words

Left foot and open left hand lead; the torso is bladed a little (left shoulder forward) and leans in; the right hand is drawn back by the hip, ready to fire; weight is slightly back; head level, eyes on the target. Two slow breaths and a gentle sway keep it alive.

## Animations

| ID | Plays | Loops | Priority | Purpose |
|---|---|---|---|---|
| `STANCE_ENTER` | frames 0-16 (0.27s) | no | Movement | Relaxed > coil down (anticipation) > snap the lead hand up > settle into the stance |
| `STANCE_IDLE` | frames 0-192 (3.20s) | yes | Movement | Held stance with two breaths and a slow weight sway; loops every 3.2s |
| `STANCE_EXIT` | frames 0-15 (0.25s) | no | Movement | Stance > rise and loosen > relaxed standing pose |
| `STANCE_MOVE` | frames 0-36 (0.60s) | yes | Movement | Upper-body guard layered over the default walk/run legs; torso only turns slightly so legs don't skate |

## Files

| File | What it is |
|---|---|
| `stance.json` | Every keyframe and every baked 60 fps frame for all four animations (Euler + quaternion + Motor6D Transform) |
| `storyboards/stance_overview.png` | The stance and its transitions in 3 views, on one page |
| `storyboards/STANCE_*_keyframes.png` | Keyframe sheets (side / front 3/4 / top-down) |
| `storyboards/STANCE_*_allframes.png` | Frame strips (every frame; every 8th for the 192-frame idle, every 2nd for the move loop) |
| `storyboards/stance_preview.gif` | Slow-motion loop: draw in > idle > relax > moving |
| `BuildStanceAnimations.lua` | Studio script that builds the four `KeyframeSequence` objects |

## Conventions

- **Frame rate:** 60 fps.
- **Axes (HumanoidRootPart frame):** +X = character's right, +Y = up, -Z = forward (toward the target). Positions are studs relative to the HumanoidRootPart at frame 0.
- **Joint rotation:** joints[J].euler_xyz_deg = [x, y, z] degrees applied as Rx(x)*Ry(y)*Rz(z) (Roblox CFrame.Angles order: Z first, then Y, then X), expressed in TORSO space and applied about the joint pivot by pre-multiplying the Motor6D's C0 rotation:  C0' = CFrame.new(C0.Position) * CFrame.Angles(x,y,z) * C0.Rotation  (this is exactly what src/ReplicatedStorage/Combat/Poses.lua does). Zero everywhere = default R6 rest pose.
- **Same pose as Motor6D.Transform:** joints[J].transform_quat_xyzw / transform_euler_xyz_deg / transform_pos is the SAME pose expressed as a Motor6D.Transform (what an AnimationTrack / KeyframeSequence Pose stores): Part1 = Part0 * C0 * Transform * C1:Inverse(). transform_quat_xyzw is order-agnostic: CFrame.new(px,py,pz, qx,qy,qz,qw). Only the Root joint has a translation (transform_pos, in RootJoint space); it is how the torso sits relative to the HumanoidRootPart (torso_offset_hrp, in HRP axes).
- **Interpolation:** Between keyframes: quaternion slerp of each joint with the easing named on the ARRIVING keyframe (ease_arriving); torso offset is lerped with the same alpha. baked_frames is exactly that, evaluated on every integer frame.
- **Loops:** STANCE_IDLE and STANCE_MOVE loop: their last keyframe equals their first (validation.loop_seam_error ~ 0). Set KeyframeSequence.Loop = true for them.
- **Upper-body-only track:** STANCE_MOVE only contains Torso(rotation only)/Head/Arm poses and NO leg poses and NO torso translation: play it at Movement priority (above the default walk, below Action-priority attacks) while the walk animation keeps driving the legs. Legs in its pictures are shown at rest purely for context.
- **Foot planting:** Planted feet are solved with IK to fixed floor footprints; torso_offset_hrp.y already contains the stance height. Joint values therefore already include the leg IK; just play the joint data. For STANCE_ENTER / IDLE / EXIT the feet are IK-planted (see foot_planting); the torso sinks to the stance height (torso_offset_hrp.y) as the legs spread.

Rough feel for the angles: shoulder **x = 90** points the arm straight ahead, **x = 180** straight up, **x = -90** straight back; a right-arm **z** > 0 swings it out to the right, a left-arm **z** < 0 out to the left. Root **y** > 0 turns the chest to the left, which brings the **right** shoulder forward (so the stance's negative y brings the **left** shoulder forward); Root **x** < 0 leans forward.

---

## STANCE_ENTER: Stance: draw in

*Relaxed > coil down (anticipation) > snap the lead hand up > settle into the stance*

- Plays **frames 0-16** (0.267s); priority **Movement**.
- Checks: floor penetration 0.17 studs; planted-foot slide 0.47 (for the one-shots this is the feet legitimately travelling between footprints).
- Pictures: `storyboards/STANCE_ENTER_keyframes.png`, `storyboards/STANCE_ENTER_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Relaxed** | Linear | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.00, 0.00, 0.00] |
| 5 | 0.083s | **Dip** | CubicOut | [-20.0, -32.0, 0.0] | [11.7, 31.5, -6.2] | [-16.4, 30.9, -1.4] | [62.1, 16.3, -17.9] | [35.5, 25.4, -4.3] | [60.3, 18.5, -51.7] | [0.17, 0.23, 0.38] |
| 10 | 0.167s | **Snap** | CubicOut | [-10.0, -22.0, 0.0] | [5.4, 21.9, -2.0] | [-19.3, 20.9, -2.9] | [104.9, -5.9, -11.2] | [20.2, 19.7, 6.7] | [34.9, 21.5, -24.8] | [-0.03, 0.23, 0.28] |
| 16 | 0.267s | **Ready** | CubicInOut | [-10.0, -20.0, 0.0] | [4.3, 19.9, -1.5] | [-8.5, 19.8, -5.1] | [90.0, 0.0, -8.0] | [19.3, 17.9, 7.8] | [32.6, 20.6, -19.5] | [-0.10, 0.20, 0.24] |

### What the body is doing

- **f0 Relaxed**: Default relaxed standing pose (arms hanging, feet together).  
  *In world terms:* R arm down, L arm down, R leg down, L leg down.
- **f5 Dip**: Anticipation: feet spread wide, body drops and coils, both hands pulled in toward the body.  
  *In world terms:* R arm down back, L arm down forward, R leg down, L leg down forward left.
  *Cues:* sfx: cloth snap / sharp inhale.
- **f10 Snap**: Overshoot: the lead hand snaps up past its final height, torso rises and twists into the blade.  
  *In world terms:* R arm down back, L arm level forward, R leg down, L leg down.
  *Cues:* vfx: small dust puff at the feet (optional).
- **f16 Ready**: Settles into the stance (identical to STANCE_IDLE frame 0).  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.

---

## STANCE_IDLE: Stance: idle loop (breathing)

*Held stance with two breaths and a slow weight sway; loops every 3.2s*

- Plays **frames 0-192** (3.200s); priority **Movement**; **loops** (seam error 5.6e-16).
- Checks: floor penetration 0.00 studs; planted-foot slide 0.00 (for the one-shots this is the feet legitimately travelling between footprints).
- Pictures: `storyboards/STANCE_IDLE_keyframes.png`, `storyboards/STANCE_IDLE_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Exhale** | CubicInOut | [-10.0, -20.0, 0.0] | [4.3, 19.9, -1.5] | [-8.5, 19.8, -5.1] | [90.0, 0.0, -8.0] | [19.3, 17.9, 7.8] | [32.6, 20.6, -19.5] | [-0.10, 0.20, 0.24] |
| 48 | 0.800s | **Inhale** | CubicInOut | [-8.6, -20.4, 0.8] | [4.5, 19.1, -2.3] | [-3.3, 20.4, -8.6] | [94.3, -2.4, -9.3] | [20.1, 17.8, 7.3] | [33.3, 20.8, -20.0] | [-0.13, 0.19, 0.32] |
| 96 | 1.600s | **Exhale (sway)** | CubicInOut | [-10.8, -23.2, -0.8] | [4.5, 24.8, -1.0] | [-10.3, 22.7, -4.2] | [88.4, 1.5, -10.2] | [26.1, 20.0, 7.5] | [36.8, 23.7, -20.5] | [-0.16, 0.18, 0.37] |
| 144 | 2.400s | **Inhale (sway)** | CubicInOut | [-8.8, -17.5, 1.2] | [4.5, 15.8, -2.5] | [-4.0, 17.5, -6.9] | [93.6, -2.3, -6.4] | [16.2, 15.7, 7.2] | [31.8, 18.0, -19.3] | [-0.09, 0.21, 0.23] |
| 192 | 3.200s | **Exhale** | CubicInOut | [-10.0, -20.0, 0.0] | [4.3, 19.9, -1.5] | [-8.5, 19.8, -5.1] | [90.0, 0.0, -8.0] | [19.3, 17.9, 7.8] | [32.6, 20.6, -19.5] | [-0.10, 0.20, 0.24] |

### What the body is doing

- **f0 Exhale**: The stance pose itself, chest lowered. First and last keyframe are identical so the loop is seamless.  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.
- **f48 Inhale**: Chest rises, shoulders lift ~6 degrees, head lifts and drifts a touch to the right.  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.
- **f96 Exhale (sway)**: Chest lowers; torso sways a little further into the blade, head drifts back left.  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.
- **f144 Inhale (sway)**: Second breath; torso sways back the other way.  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.
- **f192 Exhale**: Back to the exact first pose: loop point.  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.

---

## STANCE_EXIT: Stance: relax

*Stance > rise and loosen > relaxed standing pose*

- Plays **frames 0-15** (0.250s); priority **Movement**.
- Checks: floor penetration 0.02 studs; planted-foot slide 0.14 (for the one-shots this is the feet legitimately travelling between footprints).
- Pictures: `storyboards/STANCE_EXIT_keyframes.png`, `storyboards/STANCE_EXIT_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Ready** | Linear | [-10.0, -20.0, 0.0] | [4.3, 19.9, -1.5] | [-8.5, 19.8, -5.1] | [90.0, 0.0, -8.0] | [19.3, 17.9, 7.8] | [32.6, 20.6, -19.5] | [-0.10, 0.20, 0.24] |
| 7 | 0.117s | **Release** | CubicInOut | [-4.0, -10.0, 0.0] | [2.0, 10.0, -0.4] | [-4.1, 10.0, -5.3] | [54.4, 5.9, -0.1] | [5.6, 9.7, 6.5] | [9.9, 11.0, -6.4] | [-0.05, 0.12, 0.01] |
| 15 | 0.250s | **Relaxed** | CubicOut | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] | [0.00, 0.00, 0.00] |

### What the body is doing

- **f0 Ready**: Starts from the stance.  
  *In world terms:* R arm down, L arm level forward, R leg down, L leg down.
- **f7 Release**: Body rises, hands loosen and drop, feet draw back together.  
  *In world terms:* R arm down, L arm down forward, R leg down, L leg down.
- **f15 Relaxed**: Default relaxed standing pose.  
  *In world terms:* R arm down, L arm down, R leg down, L leg down.

---

## STANCE_MOVE: Stance: moving (upper body only)

*Upper-body guard layered over the default walk/run legs; torso only turns slightly so legs don't skate*

- Plays **frames 0-36** (0.600s); priority **Movement**; **loops** (seam error 2.2e-16); **upper body only: no leg poses, no torso translation**.
- Pictures: `storyboards/STANCE_MOVE_keyframes.png`, `storyboards/STANCE_MOVE_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Guard A** | Linear | [-8.0, -14.0, 0.0] | [4.1, 14.0, -1.0] | [-4.1, 14.0, -7.0] | [78.3, 2.9, -3.7] | [0.00, 0.00, 0.00] |
| 18 | 0.300s | **Guard B** | CubicInOut | [-9.0, -15.0, 0.0] | [5.2, 14.9, -1.3] | [-1.0, 15.0, -7.7] | [82.3, 2.1, -4.9] | [0.00, 0.00, 0.00] |
| 36 | 0.600s | **Guard A** | CubicInOut | [-8.0, -14.0, 0.0] | [4.1, 14.0, -1.0] | [-4.1, 14.0, -7.0] | [78.3, 2.9, -3.7] | [0.00, 0.00, 0.00] |

### What the body is doing

- **f0 Guard A**: Torso leans in and turns slightly (less than the idle stance), lead hand forward, rear hand back. No leg or torso-translation data: the walk animation keeps driving those.  
  *In world terms:* R arm down, L arm forward.
  *Cues:* play at Movement priority while the character is moving.
- **f18 Guard B**: Tiny bob so the upper body never freezes.  
  *In world terms:* R arm down, L arm forward.
- **f36 Guard A**: Loop point: identical to the first keyframe.  
  *In world terms:* R arm down, L arm forward.

---

## How the game uses it

- **Enter** on the first attack, block or dodge (`Config.Stance.AutoEnter`) or when toggled with **C**. **Exit** after `Config.Stance.ExitDelay` seconds with no combat action, when sprinting, or when toggled off. While toggled on it stays until you toggle it off.
- Standing still plays `STANCE_IDLE`; moving swaps to the upper-body `STANCE_MOVE` while the default walk animation drives the legs. Movement speed is `Config.Movement.StanceWalkSpeed` while in the stance.
- Attacks (Action priority) play over the stance and return into it. Other players see your stance too (it replicates through a character attribute).
- Until you publish the animations and paste their ids into `Config.Animations`, the kit plays the **same data procedurally** (rotations only: no torso translation / leg IK), so it works out of the box.

## Recreating it

1. Run `BuildStanceAnimations.lua` in Studio (instructions in its header), open each sequence in the Animation Editor, publish, and paste the ids into `Config.Animations` (`StanceEnter`, `StanceIdle`, `StanceExit`, `StanceMove`).
2. Or place poses by hand at each keyframe time using the Euler values or the exact `transform_quat_xyzw` in the JSON; `baked_frames` is the expected result on every frame.
3. Set `Loop` on `STANCE_IDLE` and `STANCE_MOVE`. Priority **Movement** for all four (above the default idle/walk, below the Action-priority attacks).

## Honest caveats

- Authored and checked in a software model of the R6 rig, not Roblox Studio. The Transform maths is verified against Roblox's Motor6D formula (error < 1e-15) and both loops close exactly, but **nothing here has been played in Studio**.
- The procedural fallback skips the torso translation and leg IK, so feet may sit a few hundredths of a stud off the floor until the published animations are used.
- Pose easing direction in KeyframeSequences is assumed to describe the move *into* each keyframe; flip it in the editor if it looks off.
- R6 limbs are rigid, so the 'guard' is an arm angle, not a bent elbow.
