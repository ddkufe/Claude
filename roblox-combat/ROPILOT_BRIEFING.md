# Project briefing for Ropilot: Naruto-style ninja RPG (Roblox)

Paste this whole file into Ropilot (or one section at a time if it has a message limit).
It sums up everything built for this game so far, outside Studio, so you can pick up from here.

---

## 1. The game

- Anime ninja RPG on Roblox, Naruto-inspired. No title yet.
- Look and feel: classic 2019–2021 Roblox anime-game style.
- **R6 characters only.** Everything below assumes R6 (Torso, Left/Right Arm, Left/Right Leg, Head, HumanoidRootPart).
- World size target: about 15,000 x 15,000 studs.
- Villages named so far: Leaf, Mist, Sand, Stone, Cloud, Sound, plus Rogue (no village).

## 2. World map (design, not built in Studio yet)

One connected continent, ocean only around the outside. Six lands, **divided by stone border walls with watchtowers and gatehouses where roads cross**. There are no rivers, lakes or bridges between the lands.

Each land has a headquarters in its centre, a village ringed around it, and one unique landmark:

| Land | Position | Headquarters | Unique landmark |
|---|---|---|---|
| Grass | Centre | Red-roofed round tower | Cliff with carved stone faces (behind the tower) |
| Snow | North | White castle keep with blue roofs | Giant glowing blue ice crystal |
| Winter | North-west | Dark timber pagoda lodge | Huge ancient white frost tree |
| Desert | East | Domed sandstone fortress | Giant rock arch and red mesas |
| Gloomy | South-west | Black spiked castle with purple windows | Giant coiled serpent skeleton, fog |
| Destroyed | South-east | Half-ruined fortress with scaffolding | Smoking impact crater with lava cracks |

The roads meet at the Grass land, and a main road runs south between Gloomy and Destroyed.
Reference images (the user can attach them):
- `generations/ninjarpg_biome_map_bordered_labeled_1792607580.png`
- `generations/ninjarpg_biome_map_bordered_clean_1792607580.png`

## 3. Combat system (built and ready to install)

A full R6 PvP combat kit, server-validated. Source is in `roblox-combat/src/`; ready-made model files are in `roblox-combat/dist/`.

### Where everything lives in Studio

| Location | Contents |
|---|---|
| `ReplicatedStorage.Combat` (Folder) | ModuleScripts: `Config`, `Poses`, `Stance`, `StanceData`, `VFX`, `Crater`, `Hitbox`, `Knockback`, `ClientEvents` |
| `ServerScriptService.Combat` (Folder) | `CombatServer` (Script), `CombatState`, `HitResolver` (ModuleScripts) |
| `StarterPlayer.StarterPlayerScripts` | `CombatClient` (LocalScript) |

The server creates two RemoteEvents in `ReplicatedStorage.Combat` at runtime:
- `CombatRequest`: client to server. Actions: `M1`, `M1Hit`, `SlamLand`, `Dodge`, `Block`, `Stance`.
- `CombatEvents`: server to clients. Events: `Pose`, `PoseRelease`, `Hit`, `Impact`, `Block`, `Parry`, `GuardBreak`, `Dodge`, `Dodged`, `SlamStart`, `Knockback`, `StopKnockback`, `Hurt`, `HitConfirm`.

The scripts find each other by name and parent, so **don't rename or move them**.

Character attributes the kit uses: `StunEnd`, `IFrameEnd`, `Blocking`, `InStance`, `BaseWalkSpeed`.

### Moves and controls

| Action | PC | Gamepad | Mobile |
|---|---|---|---|
| Attack (hold to chain) | M1 | R2 | "Hit" button |
| Dodge dash (i-frames) | Q | B | "Dash" button |
| Block / parry | F (hold; tap just before a hit to parry) | L2 | "Block" button |
| Sprint | Left Shift | L3 | — |
| Toggle combat stance | C | Y | — |

- **M1 x4:** the 4th hit is a finisher that depends on context:
  - On the ground: a knockback kick. Knocking the target into a wall causes a **wall splat** (crater on the wall, extra damage and stun).
  - Holding Space: an **uptilt** launcher, and the attacker auto-hops up after the target.
  - In the air (at least 7 studs up): a **ground slam**. The attacker dives, spikes the target into the floor (crater and bounce), and the landing hits everyone nearby.
- **Combo route:** M1, M1, M1, Space+M1 (uptilt), then M1 x3 in the air, then M1 (slam).
- **Block:** frontal only. Heavy hits (finisher, uptilt, slam) **guard break**. Blocking within 0.16s of a hit **parries** and stuns the attacker.
- **Trades:** getting hit during your own windup cancels your swing.
- **Dodge:** 0.3s of invulnerability, with a 1.6s cooldown.

### How it works

- Hit detection runs on the attacker's client so hits feel instant. The **server re-validates** every hit (range, facing, cooldown, stun, combo state), and damage only happens on the server, via `Humanoid:TakeDamage`.
- Knockback is applied by whoever owns the physics: the victim's client for players, the server for NPCs.
- Wall and ground impacts are detected on the server by raycasting along the victim's velocity, then broadcast to all clients to draw the crater.
- All VFX are client-side and use built-in `rbxasset://` textures only. Craters copy the material and colour of whatever was hit.
- `CombatClient` sets `Humanoid.WalkSpeed` every frame. **Any other sprint or speed script will fight it**, so merge it into the speed block at the bottom of `CombatClient`.

### Tuning (`ReplicatedStorage.Combat.Config`)

Every number is in `Config`. Key values:

- **M1:**
  - `ComboLength` 4, `ComboResetTime` 1.1, `SwingCooldown` 0.32, `Windup` 0.11, `EndLag` 0.85.
  - `Damage` {3.5, 3.5, 4, 7}, `HitStun` 0.55, `FinisherStun` 0.9, `FinisherKnockback` 70.
  - Lunge: 16 studs/s for 0.09s.
- **Uptilt:** `Damage` 6, `Launch` 70, `Stun` 1.15.
- **Slam:** `MinHeight` 7, `SpikeDamage` 6, `AoEDamage` 6, `AoERadius` 10.
- **Dodge:** `Cooldown` 1.6, `IFrames` 0.3, `Speed` 90.
- **Block:**
  - `DamageMultiplier` 0.15 (blocked hits deal 15% damage).
  - `PerfectWindow` 0.16, `ParryStun` 1.1, `GuardBreakStun` 1.4.
- **Movement:**
  - Walk 16, in stance 14, sprint 28.
  - Attacking 9, blocking 6, stunned 3.
- **Hit:** `FriendlyFire = true`. Set it to false to stop players on the same `Team` (village) from hurting each other.
- **Debug:** `ShowHitboxes = false`. Set it to true while tuning.

### Hooks for game features (not built yet)

- Chakra costs, rank scaling and jutsu: add them in `HitResolver.applyHit` (damage) and the `handlers` table in `CombatServer` (to gate moves).
- Test dummy: any Model with a `Humanoid` and `HumanoidRootPart`. For smooth knockback, run `dummy.HumanoidRootPart:SetNetworkOwner(nil)` on the server.

## 4. Combat stance

- **The stance:** left foot and open left hand lead, torso bladed, right hand drawn back by the hip.
- **Animations:**
  - Draw-in (0.27s).
  - Breathing idle loop.
  - Relax (0.25s).
  - Upper-body guard while moving; the default walk drives the legs.
- **Enters:** on the first attack, block or dodge. C or Y holds it until toggled off.
- **Relaxes:** after 3s with no combat action, or when sprinting.
- **Shared with the combo:** the stance is the M1 combo's start and end pose, so punches flow out of it and back into it.
- **Replication:** other players see it through the `InStance` attribute the server sets.
- **Procedural for now:** it plays procedurally from `StanceData` (Motor6D C0 edits) until real animation ids are set.

## 5. Animations (spec'd frame by frame, not yet published)

There are no uploaded animation ids yet. Every move plays a **procedural pose** until its id is pasted into `Config.Animations`. These are the keys:

- `Jab1`, `Jab2`, `Jab3`, `Finisher`
- `Uptilt`, `SlamDive`, `SlamLand`
- `Hurt`, `Block`, `Dodge`, `GuardBroken`
- `StanceEnter`, `StanceIdle`, `StanceExit`, `StanceMove`

Any key left `""` keeps the procedural pose.

**The M1 combo** is a 4-hit string: Right Straight, Left Hook, Right Overhand, Roundhouse Finisher.
- It runs at 60 fps. Contact is on frame 7, which matches `Windup` 0.11s.
- Hits 1–3 are 20 frames each; the finisher is 51 frames.
- The lunge is code-driven physics; the animation must **not** move the HumanoidRootPart.

**To turn the specs into real animations:**
1. Insert an R6 rig (Avatar > Rig Builder > R6) and select it.
2. Paste `animations/BuildM1Animations.lua` into the Command Bar and press Enter. It builds `KeyframeSequence`s M1_1..M1_4.
3. Do the same with `animations/BuildStanceAnimations.lua` for the four stance animations.
4. Open the Animation Editor, Load each sequence, check it, then Publish.
5. Paste the ids into `Config.Animations`. Map M1_1..M1_4 to Jab1, Jab2, Jab3 and Finisher, and the stance animations to the Stance* keys. **All four Stance* ids must be set** before the stance switches from procedural to real tracks.

Full numbers and pictures:
- `animations/M1_COMBO_SPEC.md` and `animations/STANCE_SPEC.md`
- `animations/m1_combo.json` and `animations/stance.json`
- `animations/storyboards/*.png`

**Joint convention** (for anyone editing poses in code), R6 Motor6D:
- Edit C0: `C0' = CFrame.new(C0.Position) * CFrame.Angles(x, y, z) * C0.Rotation`.
- Same pose as a Transform: `Part1 = Part0 * C0 * Transform * C1:Inverse()`.

## 6. Install status

The kit is built, but the user still needs to put it into the place. Use Insert from File:

| Right-click in Explorer | Insert |
|---|---|
| ReplicatedStorage | `dist/1_ReplicatedStorage.rbxmx` |
| ServerScriptService | `dist/2_ServerScriptService.rbxmx` |
| StarterPlayer > StarterPlayerScripts | `dist/3_StarterPlayerScripts.rbxmx` |

If an older copy is already in the place, delete the old `Combat` folders and `CombatClient` first, or you'll get duplicates.

**Quick test:**
1. Insert an R6 block rig (Avatar > Rig Builder) and punch it.
2. For PvP, use Test > Clients and Servers with 2 players.

## 7. Art made for the game (outside Studio)

- **Discord server:**
  - A stormy purple Rain Village banner with lightning and rain.
  - An icon of three classic-Roblox "god" avatars, each with a different outfit and personality, descending on lightning into the Rain Village.
- **Promo shots:**
  - A green-aura Robloxian descending from heaven.
  - A first-person view of that character in space, looking down at Earth among stars and constellations.
- **World map:** see section 2.

## 8. Suggested next steps (pick with the user)

1. Install the combat kit (section 6) and test it on a dummy.
2. Build the six lands from the map: terrain per biome, border walls, gatehouses, and a headquarters with a village in each.
3. Publish the M1 and stance animations and paste the ids into `Config.Animations`.
4. Add village Teams (Leaf, Mist, Sand, …) and decide on `FriendlyFire`.
5. Add chakra, jutsu and ranks on top of the `HitResolver` / `CombatServer` hooks.

## 9. Gaps in this briefing

- The user's original long game spec (exact palette, lighting and HUD layout) isn't reproduced word for word here, only the parts listed in section 1. Ask the user for anything more specific.
- This briefing was written outside Studio, so it can't tell you what is already in the place. Check the Explorer before inserting anything.
