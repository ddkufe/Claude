# Ninja RPG Combat Kit (R6)

Server-validated PvP combat: M1 strings, uptilt launcher, air combos, ground
slam with craters, wall splats, hitstun, block / parry / guard break, dodge
dash with i-frames, sprint, and hit/impact VFX. R6 only. Works out of the box
with procedural poses; swap in real animations whenever you have them.

## Install (Roblox Studio, no plugins)

Create these exactly (names matter), and paste each file's contents in:

| In Studio | Type | File |
|---|---|---|
| ReplicatedStorage > **Combat** | Folder | |
| ReplicatedStorage > Combat > **Config** | ModuleScript | `src/ReplicatedStorage/Combat/Config.lua` |
| ReplicatedStorage > Combat > **Knockback** | ModuleScript | `.../Combat/Knockback.lua` |
| ReplicatedStorage > Combat > **Hitbox** | ModuleScript | `.../Combat/Hitbox.lua` |
| ReplicatedStorage > Combat > **Poses** | ModuleScript | `.../Combat/Poses.lua` |
| ReplicatedStorage > Combat > **VFX** | ModuleScript | `.../Combat/VFX.lua` |
| ReplicatedStorage > Combat > **Crater** | ModuleScript | `.../Combat/Crater.lua` |
| ReplicatedStorage > Combat > **ClientEvents** | ModuleScript | `.../Combat/ClientEvents.lua` |
| ServerScriptService > **Combat** | Folder | |
| ServerScriptService > Combat > **CombatState** | ModuleScript | `src/ServerScriptService/Combat/CombatState.lua` |
| ServerScriptService > Combat > **HitResolver** | ModuleScript | `src/ServerScriptService/Combat/HitResolver.lua` |
| ServerScriptService > **CombatServer** | Script | `src/ServerScriptService/CombatServer.server.lua` |
| StarterPlayer > StarterPlayerScripts > **CombatClient** | LocalScript | `src/StarterPlayerScripts/CombatClient.client.lua` |

The two RemoteEvents (`CombatRequest`, `CombatEvents`) are created by the
server script automatically.

Using Rojo instead? `rojo serve` from this folder; `default.project.json`
maps everything.

## Controls

| Action | PC | Gamepad | Mobile |
|---|---|---|---|
| Attack (hold to chain) | M1 | R2 | "Hit" button |
| Dodge dash (i-frames) | Q | B | "Dash" button |
| Block / parry | F (hold; tap right before a hit to parry) | L2 | "Block" button |
| Sprint | Left Shift (hold) | L3 | — |

## How the moves chain

- **M1 x4**: the 4th hit is the finisher, and changes with context:
  - grounded → **knockback kick**; slamming the target into a wall = **wall splat** (crater on the wall, extra damage + stun).
  - holding **Space** → **uptilt** launcher; on hit you auto-hop up after them.
  - airborne (at least `Slam.MinHeight` studs up) → **ground slam**: you dive, spike anyone below you into the floor (crater + bounce), and the landing does an AoE shockwave.
- **Combo route**: M1, M1, M1, **Space+M1** (uptilt) → M1, M1, M1 in the air (each air hit keeps you both floating) → M1 (**slam**).
- **Block**: frontal only. Heavy hits (finisher, uptilt, slam) **guard break**. Blocking within `Block.PerfectWindow` of the hit **parries** and stuns the attacker.
- **Trades**: getting hit during your own windup cancels your swing.
- **Dodge**: `Dodge.IFrames` seconds of invulnerability; attacks that pass through you show an afterimage.

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
