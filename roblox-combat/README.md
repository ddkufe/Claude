# Ninja RPG Combat Kit (R6)

Server-validated PvP combat: M1 strings, uptilt launcher, air combos, ground
slam with craters, wall splats, hitstun, block / parry / guard break, dodge
dash with i-frames, sprint, a ninja combat stance, and hit/impact VFX. R6 only.
Works out of the box with procedural poses; swap in real animations whenever
you have them.

## Install (Roblox Studio, about 1 minute)

The `dist/` folder has three ready-made model files. In Studio's Explorer,
right-click each target below, choose **Insert from File...**, and pick the
matching file:

| Right-click this in Explorer | Insert this file | You get |
|---|---|---|
| **ReplicatedStorage** | `dist/1_ReplicatedStorage.rbxmx` | `Combat` folder with 9 ModuleScripts |
| **ServerScriptService** | `dist/2_ServerScriptService.rbxmx` | `Combat` folder with the `CombatServer` Script + 2 ModuleScripts |
| **StarterPlayer > StarterPlayerScripts** | `dist/3_StarterPlayerScripts.rbxmx` | `CombatClient` LocalScript |

If something lands in the wrong place, drag it to the right parent in
Explorer: names and parents matter, the scripts find each other by them.
The two RemoteEvents (`CombatRequest`, `CombatEvents`) are created by the
server script automatically. Press Play to test.

**Updating an earlier install?** Delete the old `Combat` folder in
ReplicatedStorage, the old `Combat` folder in ServerScriptService and the old
`CombatClient` first, otherwise Insert from File leaves you with duplicates.

Quick test target: Avatar tab > **Rig Builder** > R6 > Block Rig, then
punch it. For PvP, use Test > Clients and Servers with 2 players.

After editing anything in `src/`, rebuild the model files with
`python3 build_rbxmx.py`. Using Rojo instead? `rojo serve` from this folder;
`default.project.json` maps everything.

## Controls

| Action | PC | Gamepad | Mobile |
|---|---|---|---|
| Attack (hold to chain) | M1 | R2 | "Hit" button |
| Dodge dash (i-frames) | Q | B | "Dash" button |
| Block / parry | F (hold; tap right before a hit to parry) | L2 | "Block" button |
| Sprint (also relaxes the stance) | Left Shift (hold) | L3 | — |
| Toggle combat stance | C | Y | — |

## How the moves chain

- **M1 x4**: the 4th hit is the finisher, and changes with context:
  - grounded → **knockback kick**; slamming the target into a wall = **wall splat** (crater on the wall, extra damage + stun).
  - holding **Space** → **uptilt** launcher; on hit you auto-hop up after them.
  - airborne (at least `Slam.MinHeight` studs up) → **ground slam**: you dive, spike anyone below you into the floor (crater + bounce), and the landing does an AoE shockwave.
- **Combo route**: M1, M1, M1, **Space+M1** (uptilt) → M1, M1, M1 in the air (each air hit keeps you both floating) → M1 (**slam**).
- **Block**: frontal only. Heavy hits (finisher, uptilt, slam) **guard break**. Blocking within `Block.PerfectWindow` of the hit **parries** and stuns the attacker.
- **Trades**: getting hit during your own windup cancels your swing.
- **Dodge**: `Dodge.IFrames` seconds of invulnerability; attacks that pass through you show an afterimage.

## Combat stance

A ninja stance (left foot and open left hand lead, torso bladed, right hand
drawn back by the hip) with a breathing idle, a draw-in, a relax, and an
upper-body guard while moving. It is also the pose the M1 combo starts and ends
in, so punches flow out of it and back into it.

- **Enters** on your first attack, block or dodge (`Config.Stance.AutoEnter`),
  or hold it with **C** / **Y** until you toggle it off.
- **Relaxes** after `Config.Stance.ExitDelay` (3s) with no combat action, or
  when you sprint. Standing plays the idle loop; moving swaps to the upper-body
  guard while the default walk drives the legs. You walk at
  `Config.Movement.StanceWalkSpeed` while in it.
- **Other players see it** (the server publishes it as an `InStance`
  attribute). Turn the whole thing off with `Config.Stance.Enabled = false`.
- It plays **procedurally** from `Combat/StanceData` (generated from the same
  keyframes as the animations) until you publish the real animations and fill
  in all four of `Config.Animations.StanceEnter / StanceIdle / StanceExit /
  StanceMove`; then it uses real tracks.

Spec, pictures and data: `animations/STANCE_SPEC.md`,
`animations/storyboards/stance_overview.png`, `animations/stance.json`; build
the KeyframeSequences with `animations/BuildStanceAnimations.lua`.

## Animation spec (frame-by-frame M1 combo)

`animations/` holds a 4-hit M1 string (Right Straight > Left Hook > Right
Overhand > Roundhouse Finisher) as pictures plus exact numbers, so the real
animations can be recreated frame by frame. Start with
`animations/M1_COMBO_SPEC.md`; the pictures are in `animations/storyboards/`
(`combo_overview.png`, per-attack keyframe and every-frame sheets, a GIF) and
the machine-readable data is `animations/m1_combo.json`.

To get actual KeyframeSequences in Studio, run
`animations/BuildM1Animations.lua` (instructions in its header), then publish
and paste the ids into `Config.Animations`. Rebuild everything (both the combo
and the stance) from `animations/combo_data.py` with
`pip install pillow numpy; python3 build_storyboards.py; python3 export_extras.py`
(this also regenerates `Combat/StanceData.lua`; rebuild the model files after).

The kit still plays its simple procedural poses until those ids are set.

## Tuning

Everything (damage, stun, cooldowns, knockback, hitbox sizes, speeds) is in
`ReplicatedStorage.Combat.Config`. Turn on `Config.Debug.ShowHitboxes` to
see hitboxes while tuning.

## Real animations

Upload R6 animations, then paste the ids into `Config.Animations`
(`"rbxassetid://..."`). Any move with an id uses the AnimationTrack; anything
left blank keeps the procedural pose.

## How it's built (and why)

- **Hit detection runs on the attacker's client** (feels instant, no ping
  whiffs), then the **server re-validates** every reported victim: range,
  facing, cooldown, stun, combo state. It is the only place damage happens.
- **Knockback is applied by whoever owns the physics**: the victim's own
  client for players, the server for NPCs (`Knockback` module is shared).
- **Wall/ground impacts are detected on the server** by raycasting along each
  launched victim's velocity, then broadcast so every client draws the crater.
- **All VFX are client-side** and only use built-in `rbxasset://` textures.
  Craters copy the material and color of whatever was hit.

## Integrating with your game

- `CombatClient` sets `Humanoid.WalkSpeed` every frame (walk / sprint /
  attacking / blocking / stunned). Remove or merge any existing sprint script,
  or move its logic into the speed block at the bottom of `CombatClient`.
- Damage uses `Humanoid:TakeDamage`, so your existing health bar keeps working.
- Chakra costs, rank scaling, or jutsu hooks: `HitResolver.applyHit` (damage)
  and the `handlers` in `CombatServer` (gate moves) are the places to add them.
- Same-village protection: set `Config.Hit.FriendlyFire = false` (uses
  `Player.Team`).
- Test dummies: any `Model` with a `Humanoid` and `HumanoidRootPart` is a
  valid target. For the smoothest knockback on dummies, run
  `dummy.HumanoidRootPart:SetNetworkOwner(nil)` from a server script.
