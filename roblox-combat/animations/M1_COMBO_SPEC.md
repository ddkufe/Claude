# M1 combo: frame-by-frame animation spec (R6)

A 4-hit string: **Right Straight > Left Hook > Right Overhand > Roundhouse Finisher**. Generated from `m1_combo.json` (the source of truth); the pictures in `storyboards/` are rendered from the same numbers.

## Files

| File | What it is |
|---|---|
| `m1_combo.json` | Every keyframe **and every baked 60 fps frame**: joint rotations (Euler + quaternion), Motor6D Transform values, torso offset, strike-marker positions, easing, cues, validation numbers |
| `storyboards/combo_overview.png` | Whole combo on one page |
| `storyboards/M1_n_keyframes.png` | Keyframes of one attack in 3 views (side / front 3/4 / top-down), with the strike path in red |
| `storyboards/M1_n_allframes.png` | **Every frame** of one attack (side above front) |
| `storyboards/combo_preview.gif` | Slow-motion loop of the whole combo |
| `BuildM1Animations.lua` | Studio script that builds real `KeyframeSequence` objects from this data |

## How to read the pictures

- The fighter faces **right** in the side view. **Orange/red = right limbs, blue = left limbs.** Two dots = eyes (shows where the head looks).
- Pale grey ghost = the target, its chest face exactly where the game's hitbox is centred.
- Red line = path of the striking fist/foot up to that frame. Yellow burst = contact frame (hitbox spawns).
- The fighter slides toward the target over frames 0-5: that is the game's code-driven lunge (16 studs/s for 0.09s), **not** part of the animation.

## Conventions

- **Frame rate:** 60 fps. Frame 0 = the moment the swing input arrives.
- **Axes (HumanoidRootPart frame):** +X = character's right, +Y = up, -Z = forward (toward the target). Positions are studs relative to the HumanoidRootPart at frame 0.
- **Joint rotation:** joints[J].euler_xyz_deg = [x, y, z] degrees applied as Rx(x)*Ry(y)*Rz(z) (Roblox CFrame.Angles order: Z first, then Y, then X), expressed in TORSO space and applied about the joint pivot by pre-multiplying the Motor6D's C0 rotation:  C0' = CFrame.new(C0.Position) * CFrame.Angles(x,y,z) * C0.Rotation  (this is exactly what src/ReplicatedStorage/Combat/Poses.lua does). Zero everywhere = default R6 rest pose.
- **Same pose as Motor6D.Transform:** joints[J].transform_quat_xyzw / transform_euler_xyz_deg / transform_pos is the SAME pose expressed as a Motor6D.Transform (what an AnimationTrack / KeyframeSequence Pose stores): Part1 = Part0 * C0 * Transform * C1:Inverse(). transform_quat_xyzw is order-agnostic: CFrame.new(px,py,pz, qx,qy,qz,qw). Only the Root joint has a translation (transform_pos, in RootJoint space); it is how the torso sits relative to the HumanoidRootPart (torso_offset_hrp, in HRP axes).
- **Interpolation:** Between keyframes: quaternion slerp of each joint with the easing named on the ARRIVING keyframe (ease_arriving); torso offset is lerped with the same alpha. baked_frames is exactly that, evaluated on every integer frame.
- **Foot planting:** Planted feet are solved with IK to fixed floor footprints; torso_offset_hrp.y already contains the stance height. Joint values therefore already include the leg IK; just play the joint data.
- **Code lunge:** Config.M1.Lunge for Config.M1.LungeTime is applied by the game as physics at swing start. It is NOT animated; baked frames only report it (code_lunge_forward) so reach can be checked. The HumanoidRootPart must not be moved by the animation.
- **Timing:** contact_frame 7 = Config.M1.Windup (0.11s) at 60 fps; M1_1..M1_3 are 20 frames (Config.M1.SwingCooldown 0.32s); the finisher is 51 frames (Config.M1.EndLag 0.85s).

Rough feel for the angles: shoulder **x = 90** points the arm straight ahead, **x = 180** straight up, **x = -90** straight back; a right-arm **z** > 0 swings it out to the right, a left-arm **z** < 0 out to the left. Root **y** > 0 turns the chest to the left, which brings the **right** shoulder forward; Root **x** < 0 leans forward.

---

## M1_1: Right Straight

*Rear-hand cross: hips fire first, shoulder follows, fist last*

- Plays **frames 0-20** = 20 frames (0.333s). Contact on **frame 7** (0.117s) with the **RightFist**.
- Strike marker at contact: x +0.34, y +0.53, z -4.62 (target face z = -4.6, offset -0.02).
- Checks: floor penetration 0.04 studs, planted-foot slide 0.55, planted-foot heel-lift 0.40.
- Pictures: `storyboards/M1_1_keyframes.png`, `storyboards/M1_1_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Ready** | Linear | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |
| 3 | 0.050s | **Load** | CubicInOut | [-10.0, -42.0, 2.0] | [4.5, 41.8, -4.5] | [-39.0, 35.8, 11.6] | [90.0, -2.0, -20.0] | [15.0, 40.7, 2.6] | [32.2, 36.0, -54.7] | [0.08, 0.41, -0.04] |
| 5 | 0.083s | **Fire** | Linear | [-12.0, -2.0, 0.0] | [4.0, 2.0, -0.1] | [67.0, 0.8, -15.8] | [74.0, 0.6, 26.1] | [0.9, 4.1, 7.2] | [26.8, 3.8, -13.4] | [0.10, 0.21, -0.30] |
| 7 | 0.117s | **CONTACT** | CubicOut | [-15.0, 40.0, 0.0] | [9.1, -39.6, 5.8] | [103.2, 10.8, 6.7] | [68.7, -17.0, 72.8] | [-27.4, -32.5, -0.7] | [39.2, -30.8, 9.1] | [-0.06, 0.16, -0.90] |
| 10 | 0.167s | **Follow-through** | CubicOut | [-17.0, 46.0, 0.0] | [12.8, -45.3, 9.2] | [107.9, 17.7, 17.2] | [68.9, -20.4, 80.2] | [-32.4, -38.0, -2.2] | [44.7, -33.8, 15.6] | [-0.12, 0.15, -0.97] |
| 14 | 0.233s | **Retract** | CubicInOut | [-11.0, -8.0, 0.0] | [3.0, 8.0, -0.4] | [83.1, 1.0, -33.9] | [75.1, 2.1, 10.3] | [5.8, 8.9, 7.5] | [26.4, 9.3, -15.5] | [0.07, 0.22, -0.17] |
| 20 | 0.333s | **Ready** | CubicOut | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |

### What the body is doing

- **f0 Ready**: Guard stance, bladed: left shoulder forward, chin tucked, both hands up.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.
- **f3 Load**: Rear hand drops back to the hip, torso coils right, weight sinks onto the back leg. Lead hand rises to cover the chin.  
  *In world terms:* R arm down back, L arm level forward right, R leg down, L leg down left.
  *Cues:* sfx: cloth rustle.
- **f5 Fire**: Hips fire first (torso already unwound), shoulder follows, fist accelerates through the middle of the path.  
  *In world terms:* R arm down forward, L arm forward right, R leg down, L leg down.
  *Cues:* sfx: whoosh (2 frames before contact); vfx: motion trail starts at the fist.
- **f7 CONTACT**: Arm fully extended at chest height, slightly crossing the centreline. Chest squared through the target, rear foot pivoted forward, lead hand tight at the chin.  
  *In world terms:* R arm level forward left, L arm down forward right, R leg down back, L leg down.
  *Cues:* hitbox: spawn now (Config.M1.Windup = 0.11s); vfx: hit spark at the fist; hitstop: hold this pose 3 frames (0.05s) on a confirmed hit.
- **f10 Follow-through**: Small overshoot, body commits forward over the lead leg.  
  *In world terms:* R arm level forward left, L arm down forward right, R leg down back, L leg down.
  *Cues:* vfx: trail fades.
- **f14 Retract**: Fist snaps back to the chin, hips unwind back toward the stance.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.
- **f20 Ready**: Back in guard. This is where M1_2 can begin (swing cooldown 0.32s = frame 19).  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.

---

## M1_2: Left Hook

*Lead-hand hook: torso turns the arm like a gate, arc ends across the body*

- Plays **frames 0-20** = 20 frames (0.333s). Contact on **frame 7** (0.117s) with the **LeftFist**.
- Strike marker at contact: x +0.36, y +1.42, z -4.45 (target face z = -4.6, offset +0.15).
- Checks: floor penetration 0.20 studs, planted-foot slide 0.27, planted-foot heel-lift 0.38.
- Pictures: `storyboards/M1_2_keyframes.png`, `storyboards/M1_2_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Ready** | Linear | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |
| 3 | 0.050s | **Load** | CubicInOut | [-14.0, 10.0, -4.0] | [6.8, -9.5, 5.1] | [92.0, 4.3, -20.1] | [12.6, 11.2, -88.6] | [-13.2, -5.9, 10.3] | [24.1, -6.2, -4.2] | [0.12, 0.17, -0.62] |
| 5 | 0.083s | **Fire** | Linear | [-14.0, -20.0, -2.0] | [5.7, 20.1, -0.1] | [93.8, 0.6, -52.1] | [12.4, -15.1, -97.9] | [20.7, 18.7, 8.5] | [33.6, 20.9, -18.8] | [-0.04, 0.20, 0.10] |
| 7 | 0.117s | **CONTACT** | CubicOut | [-14.0, -52.0, -4.0] | [4.6, 52.1, -1.2] | [94.9, -2.3, -86.1] | [-1.7, -55.6, -110.5] | [14.6, 51.9, -2.9] | [-17.5, 51.4, -17.8] | [0.51, 0.35, -0.79] |
| 10 | 0.167s | **Follow-through** | CubicOut | [-14.0, -60.0, -4.0] | [5.1, 60.1, -2.4] | [94.0, -2.9, -94.0] | [-10.0, -64.0, -118.8] | [27.6, 56.8, -12.8] | [-18.8, 60.1, -19.8] | [0.52, 0.35, -0.64] |
| 14 | 0.233s | **Retract** | CubicInOut | [-10.0, -28.0, 0.0] | [2.3, 28.0, -1.1] | [86.5, 1.9, -55.9] | [81.2, 4.7, -11.6] | [64.7, 18.7, 14.5] | [69.2, 32.6, -12.3] | [-0.92, -0.34, 1.18] |
| 20 | 0.333s | **Ready** | CubicOut | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |

### What the body is doing

- **f0 Ready**: Guard stance, bladed: left shoulder forward, chin tucked, both hands up.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.
- **f3 Load**: Torso twists left (left shoulder pulled back), left arm cocks out to the side at shoulder height, slightly behind the body. Rear hand guards the chin.  
  *In world terms:* R arm level forward left, L arm level left, R leg down, L leg down.
  *Cues:* sfx: cloth rustle.
- **f5 Fire**: Torso drives right; the arm is still out wide and just now swinging forward.  
  *In world terms:* R arm level forward left, L arm level forward left, R leg down, L leg down.
  *Cues:* sfx: whoosh (2 frames before contact); vfx: motion trail starts at the fist.
- **f7 CONTACT**: Whole torso has turned right; the straight arm sweeps across the front at head-to-chest height and meets the target on the centreline. Elbow-out hook shape comes from the arm being horizontal.  
  *In world terms:* R arm level forward left, L arm level forward, R leg down, L leg down left.
  *Cues:* hitbox: spawn now (Config.M1.Windup = 0.11s); vfx: hit spark at the fist; hitstop: hold this pose 3 frames (0.05s) on a confirmed hit.
- **f10 Follow-through**: Arm carries on across the body, shoulders turned away; head still tracks the target.  
  *In world terms:* R arm level forward left, L arm level forward right, R leg down, L leg down left.
  *Cues:* vfx: trail fades.
- **f14 Retract**: Arm folds back to the guard line, torso unwinding.  
  *In world terms:* R arm level forward left, L arm forward, R leg forward right, L leg down forward.
- **f20 Ready**: Back in guard. M1_3 can begin here.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.

---

## M1_3: Right Overhand

*Looping rear-hand chop: arm travels up and over, torso dives with it*

- Plays **frames 0-20** = 20 frames (0.333s). Contact on **frame 7** (0.117s) with the **RightFist**.
- Strike marker at contact: x +0.53, y +0.46, z -4.69 (target face z = -4.6, offset -0.09).
- Checks: floor penetration 0.02 studs, planted-foot slide 0.10, planted-foot heel-lift 0.30.
- Pictures: `storyboards/M1_3_keyframes.png`, `storyboards/M1_3_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Ready** | Linear | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |
| 3 | 0.050s | **Load** | CubicInOut | [-6.0, -46.0, -8.0] | [-11.0, 45.0, 13.4] | [-126.9, -36.5, 23.1] | [85.7, 12.3, -19.2] | [15.0, 46.9, 29.4] | [6.2, 47.4, -3.1] | [-0.42, 0.33, 0.22] |
| 5 | 0.083s | **Fire** | Linear | [-14.0, -4.0, -4.0] | [5.7, 4.4, 3.6] | [-164.3, -4.9, -14.8] | [76.0, 4.8, 27.1] | [-2.9, 7.1, 9.7] | [19.0, 5.7, -11.9] | [0.23, 0.15, -0.61] |
| 7 | 0.117s | **CONTACT** | CubicOut | [-19.0, 36.0, 0.0] | [13.5, -35.2, 7.9] | [107.3, 12.2, 6.1] | [74.4, -11.0, 68.5] | [-23.0, -28.7, 0.9] | [39.9, -27.1, 7.5] | [-0.02, 0.12, -0.97] |
| 10 | 0.167s | **Follow-through** | CubicOut | [-26.0, 50.0, 4.0] | [22.8, -48.4, 14.8] | [82.1, -13.1, 6.8] | [73.6, -22.0, 86.2] | [-32.9, -41.1, -4.8] | [55.0, -34.0, 20.9] | [-0.18, 0.07, -1.06] |
| 14 | 0.233s | **Recover** | CubicInOut | [-18.0, 12.0, 0.0] | [10.2, -11.8, 2.1] | [84.1, -1.2, -22.1] | [78.3, -2.5, 35.7] | [-6.2, -7.4, 6.0] | [33.6, -8.1, -7.0] | [0.11, 0.12, -0.62] |
| 20 | 0.333s | **Ready** | CubicOut | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |

### What the body is doing

- **f0 Ready**: Guard stance, bladed: left shoulder forward, chin tucked, both hands up.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.
- **f3 Load**: Right shoulder dips and tucks back, right arm swings up and behind the head. Weight loads onto the rear leg.  
  *In world terms:* R arm up back, L arm level forward right, R leg down right, L leg down.
  *Cues:* sfx: cloth rustle.
- **f5 Fire**: Arm is vertical over the shoulder at the top of the loop while the torso rotates through.  
  *In world terms:* R arm up, L arm forward right, R leg down, L leg down.
  *Cues:* sfx: whoosh (2 frames before contact); vfx: motion trail starts at the fist.
- **f7 CONTACT**: Torso has dived forward and turned; the arm has come down over the top and meets the target ahead of the chest. Heaviest lean of the three punches.  
  *In world terms:* R arm level forward left, L arm down forward right, R leg down back, L leg down.
  *Cues:* hitbox: spawn now (Config.M1.Windup = 0.11s); vfx: hit spark at the fist; hitstop: hold this pose 3 frames (0.05s) on a confirmed hit.
- **f10 Follow-through**: Fist continues down and across toward the left hip, head still up on the target.  
  *In world terms:* R arm forward left, L arm down forward right, R leg down back right, L leg down.
  *Cues:* vfx: trail fades.
- **f14 Recover**: Torso rises and unwinds, arm returns to guard.  
  *In world terms:* R arm forward left, L arm forward right, R leg down, L leg down.
- **f20 Ready**: Back in guard. M1_4 (finisher) can begin here.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.

---

## M1_4: Roundhouse Finisher

*Grounded finisher: coil, chamber, whip the right leg across the target; long recovery (0.85s)*

- Plays **frames 0-51** = 51 frames (0.850s). Contact on **frame 7** (0.117s) with the **RightFoot**.
- Strike marker at contact: x +0.52, y +0.03, z -4.45 (target face z = -4.6, offset +0.15).
- Checks: floor penetration 0.02 studs, planted-foot slide 0.09, planted-foot heel-lift 0.06.
- Pictures: `storyboards/M1_4_keyframes.png`, `storyboards/M1_4_allframes.png`.

### Keyframes

Joint values are `[x, y, z]` degrees (torso-space Euler, convention above). `ease` = how the motion arrives at that frame.

| Frame | Time | Phase | ease | Root (torso) | Neck | R shoulder | L shoulder | R hip | L hip | Torso offset (HRP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.000s | **Ready** | Linear | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |
| 3 | 0.050s | **Chamber** | CubicInOut | [-6.0, -52.0, 0.0] | [-3.2, 52.0, 2.6] | [59.3, 33.2, 7.4] | [84.4, 7.1, -31.7] | [5.1, 16.8, 77.1] | [-7.4, 50.7, -10.6] | [0.00, 0.33, 0.00] |
| 5 | 0.083s | **Whip** | Linear | [-4.0, -2.0, 6.0] | [-3.8, 2.4, -5.9] | [29.0, -1.2, 55.8] | [80.0, -5.6, 21.0] | [7.8, 31.4, 88.8] | [13.9, 2.1, -15.1] | [0.00, 0.28, 0.00] |
| 7 | 0.117s | **CONTACT** | CubicOut | [6.0, 48.0, 14.0] | [-32.2, -39.9, -32.2] | [-12.3, -46.8, 53.5] | [78.2, -25.6, 74.0] | [17.2, 47.7, 80.0] | [6.2, -47.9, -24.6] | [0.00, 0.52, 0.00] |
| 10 | 0.167s | **Follow-through** | CubicOut | [8.0, 62.0, 18.0] | [-49.3, -46.2, -49.8] | [-40.9, -52.1, 36.6] | [80.0, -33.6, 91.6] | [41.5, 56.9, 49.3] | [-8.4, -61.8, -41.0] | [0.00, 0.60, 0.00] |
| 16 | 0.267s | **Hang** | Linear | [8.0, 64.0, 18.0] | [-51.5, -47.4, -51.9] | [-47.6, -50.5, 33.0] | [80.6, -33.9, 93.8] | [47.8, 59.1, 40.2] | [-9.0, -63.9, -41.6] | [0.00, 0.60, 0.00] |
| 28 | 0.467s | **Retract** | CubicInOut | [-2.0, 20.0, 8.0] | [-9.2, -18.8, -10.6] | [31.3, -21.2, 53.8] | [78.5, -11.9, 42.0] | [8.4, 41.3, 60.2] | [21.3, -18.6, -12.5] | [0.00, 0.32, 0.00] |
| 40 | 0.667s | **Set down** | CubicInOut | [-8.0, -8.0, 0.0] | [0.0, 8.0, 0.0] | [68.2, 3.0, -17.4] | [78.1, 1.7, 12.2] | [8.4, 21.9, 32.8] | [25.2, 9.9, -13.5] | [0.00, 0.20, 0.00] |
| 51 | 0.850s | **Ready** | CubicOut | [-8.0, -22.0, 0.0] | [0.0, 22.0, 0.0] | [80.7, 3.7, -47.7] | [75.1, 5.9, -5.2] | [18.8, 19.8, 8.3] | [30.2, 22.7, -19.4] | [-0.12, 0.20, 0.29] |

### What the body is doing

- **f0 Ready**: Guard stance, bladed: left shoulder forward, chin tucked, both hands up.  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.
- **f3 Chamber**: Torso coils hard right, weight onto the left (planted) leg, right leg lifts out to the side and slightly behind, knee-high.  
  *In world terms:* R arm right, L arm level forward, R leg level back right, L leg down.
  *Cues:* sfx: deep inhale / cloth snap.
- **f5 Whip**: Hips and torso unwind explosively; the leg is already sweeping forward at hip height.  
  *In world terms:* R arm right, L arm level forward right, R leg level forward right, L leg down.
  *Cues:* sfx: whoosh (2 frames before contact); vfx: arc trail starts at the foot.
- **f7 CONTACT**: Leg is straight and horizontal, pointing at the target; torso leans back and away to counterbalance, right arm flung wide.  
  *In world terms:* R arm right, L arm level forward right, R leg forward, L leg down.
  *Cues:* hitbox: spawn now (Config.M1.Windup = 0.11s); vfx: hit spark + shockwave ring at the foot; camera: shake; hitstop: hold this pose 4 frames (0.07s) on a confirmed hit.
- **f10 Follow-through**: Leg keeps travelling across the body, torso fully rotated.  
  *In world terms:* R arm level right, L arm level forward right, R leg level forward left, L leg down left.
  *Cues:* vfx: trail fades.
- **f16 Hang**: Brief held overextension (finisher lands heavy, attacker is committed).  
  *In world terms:* R arm level right, L arm level forward right, R leg level forward left, L leg down left.
  *Cues:* recovery: no cancel into other actions.
- **f28 Retract**: Leg pulls back, torso starts to square up.  
  *In world terms:* R arm down right, L arm level forward right, R leg forward right, L leg down.
- **f40 Set down**: Right foot is coming back toward the floor.  
  *In world terms:* R arm forward, L arm forward, R leg down right, L leg down.
- **f51 Ready**: Planted again in guard. End lag over (Config.M1.EndLag = 0.85s).  
  *In world terms:* R arm forward left, L arm forward, R leg down, L leg down.

---

## Recreating it

1. **Easiest:** run `BuildM1Animations.lua` in Studio (instructions in its header). It creates `M1_1` ... `M1_4` KeyframeSequences from the keyframes above, under the selected rig's `AnimSaves` folder so the Animation Editor lists them. Open each, check it, publish, then paste the animation ids into `Config.Animations` (`Jab1`, `Jab2`, `Jab3`, `Finisher`).
2. **By hand / with another tool:** place poses at each keyframe time with the Euler values above (or the exact `transform_quat_xyzw` in the JSON), honouring `ease`. `baked_frames` in the JSON are what the result should look like on every integer frame; compare against `storyboards/*_allframes.png`.
3. Do **not** animate the HumanoidRootPart's position; forward travel comes from the game's lunge.
4. Keep animation priority **Action** so it overrides walk/idle.

## Honest caveats

- Poses were authored and checked in a software model of the R6 rig, not in Roblox Studio. The joint maths is verified against the Roblox Motor6D formula (`Part1 = Part0 * C0 * Transform * C1:Inverse()`, error < 1e-15), but **nothing here has been played in Studio**.
- The KeyframeSequence's per-pose easing semantics (does it describe the move *into* or *out of* the keyframe) is assumed to be 'into'; if it looks off in the Animation Editor, flip the easing direction.
- R6 arms and legs are rigid (no elbows/knees), so punches are straight-armed and guards are approximate.
- During the M1_1 load (frames 2-4) the planted feet shuffle up to ~0.5 studs; a few frames show a small heel-lift on the rear foot. Both are intentional compromises of a deep coil on rigid legs.
