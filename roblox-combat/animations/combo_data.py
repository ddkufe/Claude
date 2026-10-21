"""Authoring source for the 4-hit M1 combo (R6, 60 fps).

Conventions (see rig.py): HRP frame, +X right, +Y up, -Z forward (toward target).
Rotations are Rx*Ry*Rz Euler degrees (Roblox CFrame.Angles order).

How to read a pose here:
  Root                  torso rotation relative to the HRP: [pitch, yaw, roll]
                        pitch -  = lean forward   | yaw +  = RIGHT shoulder forward
                        roll  +  = lean left
  W(x, y, z)            "world aim": the limb's orientation measured in the HRP frame, so a
                        punch aimed at the target stays aimed however far the torso twists.
                        (limb hangs along -Y at 0; x raises it forward, z swings a RIGHT limb
                        outward / a LEFT limb inward, y yaws it)
  P(x, z)               planted foot: IK puts that foot flat on the floor at that spot
                        (x = right, z = back; a more negative z = further forward)
"""

FPS = 60
# Target chest face = where the game's hitbox is centred: the root has lunged LUNGE_SPEED*LUNGE_TIME
# (1.44) by the time the hitbox spawns, and Config.M1.HitboxOffset puts its centre 3.2 ahead of that.
DUMMY_FRONT_Z = -4.6  # studs ahead of the start position
LUNGE_SPEED = 16.0  # Config.M1.Lunge  (code-driven: NOT part of the animation)
LUNGE_TIME = 0.09  # Config.M1.LungeTime


def W(x, y, z):
    return {"world": [x, y, z]}


def P(x, z):
    return {"plant": [x, z]}


# stance footprints (guard, left foot leading)
FL = (-0.85, -0.65)
FR = (0.85, 0.45)


def K(frame, name, root, neck, rs, ls, legs, ease="CubicOut", shift=(0.0, 0.0), note="", cue=None):
    return dict(
        frame=frame,
        name=name,
        pose=dict(Root=root, Neck=neck, RightShoulder=rs, LeftShoulder=ls),
        legs=legs,
        ease=ease,
        shift=list(shift),
        note=note,
        cue=cue or [],
    )


def stance(rx=FR[0], rz=FR[1], lx=FL[0], lz=FL[1]):
    return {"L": P(lx, lz), "R": P(rx, rz)}


LOOK = W(-8, 0, 0)  # head stays aimed at the target while the body twists

READY = dict(
    root=[-8, -22, 0],
    neck=LOOK,
    rs=W(72, 0, -26),
    ls=W(66, 0, 16),
)


def ready(frame, ease, note="Guard stance, bladed: left shoulder forward, chin tucked, both hands up."):
    return K(frame, "Ready", READY["root"], READY["neck"], READY["rs"], READY["ls"], stance(), ease, note=note)


ATTACKS = [
    # ------------------------------------------------------------------ 1
    dict(
        id="M1_1",
        name="Right Straight",
        short="Rear-hand cross: hips fire first, shoulder follows, fist last",
        strike_tip="RightFist",
        contact_frame=7,
        loop_frames=20,
        keyframes=[
            ready(0, "Linear"),
            K(3, "Load", [-10, -42, 2], LOOK, W(-42, 0, -12), W(80, 0, 22), stance(rz=0.55), "CubicInOut",
              note="Rear hand drops back to the hip, torso coils right, weight sinks onto the back leg. Lead hand rises to cover the chin.",
              cue=["sfx: cloth rustle"]),
            K(5, "Fire", [-12, -2, 0], LOOK, W(55, 0, -14), W(62, 0, 28), stance(rz=0.35), "Linear",
              note="Hips fire first (torso already unwound), shoulder follows, fist accelerates through the middle of the path.",
              cue=["sfx: whoosh (2 frames before contact)", "vfx: motion trail starts at the fist"]),
            K(7, "CONTACT", [-15, 40, 0], LOOK, W(92, 0, -32), W(48, 0, 36), stance(rx=0.8, rz=0.0), "CubicOut",
              note="Arm fully extended at chest height, slightly crossing the centreline. Chest squared through the target, rear foot pivoted forward, lead hand tight at the chin.",
              cue=["hitbox: spawn now (Config.M1.Windup = 0.11s)", "vfx: hit spark at the fist", "hitstop: hold this pose 3 frames (0.05s) on a confirmed hit"]),
            K(10, "Follow-through", [-17, 46, 0], LOOK, W(98, 0, -26), W(44, 0, 38), stance(rx=0.8, rz=0.0), "CubicOut",
              note="Small overshoot, body commits forward over the lead leg.", cue=["vfx: trail fades"]),
            K(14, "Retract", [-11, -8, 0], LOOK, W(72, 0, -26), W(64, 0, 18), stance(rz=0.35), "CubicInOut",
              note="Fist snaps back to the chin, hips unwind back toward the stance."),
            ready(20, "CubicOut", note="Back in guard. This is where M1_2 can begin (swing cooldown 0.32s = frame 19)."),
        ],
    ),
    # ------------------------------------------------------------------ 2
    dict(
        id="M1_2",
        name="Left Hook",
        short="Lead-hand hook: torso turns the arm like a gate, arc ends across the body",
        strike_tip="LeftFist",
        contact_frame=7,
        loop_frames=20,
        keyframes=[
            ready(0, "Linear"),
            K(3, "Load", [-14, 10, -4], LOOK, W(78, 0, -30), W(0, 20, -95), stance(lz=-0.55), "CubicInOut",
              note="Torso twists left (left shoulder pulled back), left arm cocks out to the side at shoulder height, slightly behind the body. Rear hand guards the chin.",
              cue=["sfx: cloth rustle"]),
            K(5, "Fire", [-14, -20, -2], LOOK, W(80, 0, -32), W(0, -35, -95), stance(lz=-0.65), "Linear",
              note="Torso drives right; the arm is still out wide and just now swinging forward.",
              cue=["sfx: whoosh (2 frames before contact)", "vfx: motion trail starts at the fist"]),
            K(7, "CONTACT", [-14, -52, -4], LOOK, W(84, 0, -34), W(0, -108, -98), stance(rx=0.8, rz=0.25), "CubicOut",
              note="Whole torso has turned right; the straight arm sweeps across the front at head-to-chest height and meets the target on the centreline. Elbow-out hook shape comes from the arm being horizontal.",
              cue=["hitbox: spawn now (Config.M1.Windup = 0.11s)", "vfx: hit spark at the fist", "hitstop: hold this pose 3 frames (0.05s) on a confirmed hit"]),
            K(10, "Follow-through", [-14, -60, -4], LOOK, W(84, 0, -34), W(0, -125, -100), stance(rx=0.8, rz=0.25), "CubicOut",
              note="Arm carries on across the body, shoulders turned away; head still tracks the target.", cue=["vfx: trail fades"]),
            K(14, "Retract", [-10, -28, 0], LOOK, W(76, 0, -28), W(70, 0, 16), stance(rz=0.35), "CubicInOut",
              note="Arm folds back to the guard line, torso unwinding."),
            ready(20, "CubicOut", note="Back in guard. M1_3 can begin here."),
        ],
    ),
    # ------------------------------------------------------------------ 3
    dict(
        id="M1_3",
        name="Right Overhand",
        short="Looping rear-hand chop: arm travels up and over, torso dives with it",
        strike_tip="RightFist",
        contact_frame=7,
        loop_frames=20,
        keyframes=[
            ready(0, "Linear"),
            K(3, "Load", [-6, -46, -8], LOOK, W(-140, 0, -8), W(78, 0, 26), stance(rx=0.9, rz=0.6), "CubicInOut",
              note="Right shoulder dips and tucks back, right arm swings up and behind the head. Weight loads onto the rear leg.",
              cue=["sfx: cloth rustle"]),
            K(5, "Fire", [-14, -4, -4], LOOK, W(-178, 0, -12), W(62, 0, 30), stance(rx=0.85, rz=0.3), "Linear",
              note="Arm is vertical over the shoulder at the top of the loop while the torso rotates through.",
              cue=["sfx: whoosh (2 frames before contact)", "vfx: motion trail starts at the fist"]),
            K(7, "CONTACT", [-19, 36, 0], LOOK, W(92, 0, -28), W(52, 0, 34), stance(rx=0.8, rz=0.1), "CubicOut",
              note="Torso has dived forward and turned; the arm has come down over the top and meets the target ahead of the chest. Heaviest lean of the three punches.",
              cue=["hitbox: spawn now (Config.M1.Windup = 0.11s)", "vfx: hit spark at the fist", "hitstop: hold this pose 3 frames (0.05s) on a confirmed hit"]),
            K(10, "Follow-through", [-26, 50, 4], LOOK, W(52, 0, -42), W(40, 0, 40), stance(rx=0.8, rz=0.1), "CubicOut",
              note="Fist continues down and across toward the left hip, head still up on the target.", cue=["vfx: trail fades"]),
            K(14, "Recover", [-18, 12, 0], LOOK, W(66, 0, -34), W(60, 0, 24), stance(rz=0.35), "CubicInOut",
              note="Torso rises and unwinds, arm returns to guard."),
            ready(20, "CubicOut", note="Back in guard. M1_4 (finisher) can begin here."),
        ],
    ),
    # ------------------------------------------------------------------ 4
    dict(
        id="M1_4",
        name="Roundhouse Finisher",
        short="Grounded finisher: coil, chamber, whip the right leg across the target; long recovery (0.85s)",
        strike_tip="RightFoot",
        contact_frame=7,
        loop_frames=51,
        keyframes=[
            ready(0, "Linear"),
            K(3, "Chamber", [-6, -52, 0], LOOK, W(40, 0, 50), W(75, 0, 20),
              {"L": P(-0.7, -0.3), "R": W(0, -35, 82)}, "CubicInOut",
              note="Torso coils hard right, weight onto the left (planted) leg, right leg lifts out to the side and slightly behind, knee-high.",
              cue=["sfx: deep inhale / cloth snap"]),
            K(5, "Whip", [-4, -2, 6], LOOK, W(25, 0, 62), W(76, 0, 24),
              {"L": P(-0.7, -0.3), "R": W(0, 30, 96)}, "Linear",
              note="Hips and torso unwind explosively; the leg is already sweeping forward at hip height.",
              cue=["sfx: whoosh (2 frames before contact)", "vfx: arc trail starts at the foot"]),
            K(7, "CONTACT", [6, 48, 14], LOOK, W(8, 0, 72), W(80, 0, 30),
              {"L": P(-0.7, -0.3), "R": W(0, 98, 108)}, "CubicOut",
              note="Leg is straight and horizontal, pointing at the target; torso leans back and away to counterbalance, right arm flung wide.",
              cue=["hitbox: spawn now (Config.M1.Windup = 0.11s)", "vfx: hit spark + shockwave ring at the foot", "camera: shake", "hitstop: hold this pose 4 frames (0.07s) on a confirmed hit"]),
            K(10, "Follow-through", [8, 62, 18], LOOK, W(0, 0, 80), W(80, 0, 34),
              {"L": P(-0.7, -0.3), "R": W(0, 128, 100)}, "CubicOut",
              note="Leg keeps travelling across the body, torso fully rotated.", cue=["vfx: trail fades"]),
            K(16, "Hang", [8, 64, 18], LOOK, W(-4, 0, 82), W(80, 0, 34),
              {"L": P(-0.7, -0.3), "R": W(0, 134, 96)}, "Linear",
              note="Brief held overextension (finisher lands heavy, attacker is committed).", cue=["recovery: no cancel into other actions"]),
            K(28, "Retract", [-2, 20, 8], LOOK, W(30, 0, 50), W(76, 0, 24),
              {"L": P(-0.75, -0.4), "R": W(0, 62, 70)}, "CubicInOut",
              note="Leg pulls back, torso starts to square up."),
            K(40, "Set down", [-8, -8, 0], LOOK, W(60, 0, -10), W(70, 0, 20),
              {"L": P(-0.85, -0.6), "R": W(0, 14, 34)}, "CubicInOut",
              note="Right foot is coming back toward the floor."),
            ready(51, "CubicOut", note="Planted again in guard. End lag over (Config.M1.EndLag = 0.85s)."),
        ],
    ),
]
