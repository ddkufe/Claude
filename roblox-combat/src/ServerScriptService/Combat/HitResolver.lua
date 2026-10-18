-- ServerScriptService/Combat/HitResolver (ModuleScript)
-- Server-authoritative outcome of a hit: i-frames, block / parry / guard break,
-- damage, hitstun, knockback, and wall/ground impact detection.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Combat = ReplicatedStorage.Combat
local Config = require(Combat.Config)
local Hitbox = require(Combat.Hitbox)
local Knockback = require(Combat.Knockback)
local State = require(script.Parent.CombatState)

local Resolver = {}

local events
local HEAVY = { Finisher = true, Uptilt = true, Spike = true, SlamAoE = true }

function Resolver.init(remote)
	events = remote
end

function Resolver.fxAll(name, payload)
	events:FireAllClients(name, payload)
end

function Resolver.fxPlayer(player, name, payload)
	events:FireClient(player, name, payload)
end

function Resolver.knockback(character, velocity, duration)
	local player = Players:GetPlayerFromCharacter(character)
	if player then
		events:FireClient(player, "Knockback", { velocity = velocity, duration = duration })
	else
		Knockback.apply(character, velocity, duration)
	end
end

function Resolver.stopKnockback(character)
	local player = Players:GetPlayerFromCharacter(character)
	if player then
		events:FireClient(player, "StopKnockback")
	else
		Knockback.stop(character)
	end
end

function Resolver.surfaceInfo(result)
	local color = Color3.fromRGB(110, 105, 100)
	local inst = result.Instance
	if inst:IsA("Terrain") then
		pcall(function()
			color = workspace.Terrain:GetMaterialColor(result.Material)
		end)
	elseif inst:IsA("BasePart") then
		color = inst.Color
	end
	return result.Position, result.Normal, result.Material, color
end

local function isCharacterPart(inst)
	local model = inst:FindFirstAncestorOfClass("Model")
	return model ~= nil and model:FindFirstChildOfClass("Humanoid") ~= nil
end

function Resolver.canDamage(attacker, victim)
	if Config.Hit.FriendlyFire ~= false then
		return true
	end
	local a = Players:GetPlayerFromCharacter(attacker)
	local v = Players:GetPlayerFromCharacter(victim)
	return not (a and v and a.Team ~= nil and a.Team == v.Team)
end

-- mode "Wall": horizontal launches splat into walls.
-- mode "Ground": spikes crater into the floor and bounce.
function Resolver.watchImpact(victim, attacker, mode)
	local hrp = victim:FindFirstChild("HumanoidRootPart")
	if not hrp then
		return
	end
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { victim, attacker }

	local started = State.now()
	local conn
	conn = RunService.Heartbeat:Connect(function(dt)
		if not hrp.Parent or State.now() - started > Config.Impact.WatchTime then
			conn:Disconnect()
			return
		end
		local velocity = hrp.AssemblyLinearVelocity
		local speed = velocity.Magnitude
		if speed < Config.Impact.MinSpeed then
			return
		end
		local result = workspace:Raycast(hrp.Position, velocity.Unit * (speed * dt * 1.5 + 2.6), rp)
		if not result or isCharacterPart(result.Instance) then
			return
		end
		if result.Instance:IsA("BasePart") and not result.Instance.CanCollide then
			return
		end
		local isGround = result.Normal.Y > 0.6
		if mode == "Wall" and isGround then
			return
		end

		conn:Disconnect()
		local pos, normal, material, color = Resolver.surfaceInfo(result)
		Resolver.fxAll("Impact", {
			position = pos,
			normal = normal,
			material = material,
			color = color,
			intensity = math.clamp(speed / 60, 0.6, 2),
		})

		if isGround then
			Resolver.knockback(victim, Vector3.new(0, Config.Impact.GroundBounce, 0), 0.08)
		else
			Resolver.stopKnockback(victim)
			local humanoid = victim:FindFirstChildOfClass("Humanoid")
			if humanoid then
				humanoid:TakeDamage(Config.Impact.WallSplatDamage)
			end
			State.stun(victim, Config.Impact.WallSplatStun)
			Resolver.fxAll("Hit", { victim = victim, position = pos, kind = "WallSplat", direction = normal })
		end
	end)
end

local function damageFor(kind, index)
	if kind == "Jab" then
		return Config.M1.Damage[index] or Config.M1.Damage[1]
	elseif kind == "Finisher" then
		return Config.M1.Damage[Config.M1.ComboLength]
	elseif kind == "Uptilt" then
		return Config.Uptilt.Damage
	elseif kind == "Spike" then
		return Config.Slam.SpikeDamage
	elseif kind == "SlamAoE" then
		return Config.Slam.AoEDamage
	end
	return 0
end

local function flatLook(root)
	local look = root.CFrame.LookVector * Vector3.new(1, 0, 1)
	return look.Magnitude > 0.01 and look.Unit or Vector3.zAxis
end

local function tryBlock(attacker, victim, kind, index, hitPos, humanoid)
	local aRoot, vRoot = attacker.HumanoidRootPart, victim.HumanoidRootPart
	local toAttacker = (aRoot.Position - vRoot.Position) * Vector3.new(1, 0, 1)
	local frontal = toAttacker.Magnitude < 0.1
		or flatLook(vRoot):Dot(toAttacker.Unit) >= math.cos(math.rad(Config.Block.MaxAngle))
	if not frontal or kind == "SlamAoE" then
		return nil
	end

	if State.now() - State.get(victim).blockStart <= Config.Block.PerfectWindow then
		State.stun(attacker, Config.Block.ParryStun)
		Resolver.fxAll("Parry", { position = hitPos })
		Resolver.fxAll("Pose", { character = attacker, name = "GuardBroken" })
		return "parried"
	end

	if HEAVY[kind] then
		State.setBlocking(victim, false)
		humanoid:TakeDamage(Config.Block.GuardBreakDamage)
		State.stun(victim, Config.Block.GuardBreakStun)
		Resolver.fxAll("GuardBreak", { position = hitPos })
		Resolver.fxAll("Pose", { character = victim, name = "GuardBroken" })
		return "guardbreak"
	end

	humanoid:TakeDamage(damageFor(kind, index) * Config.Block.DamageMultiplier)
	Resolver.knockback(victim, flatLook(aRoot) * Config.Block.Pushback, 0.1)
	Resolver.fxAll("Block", { position = hitPos })
	return "blocked"
end

function Resolver.applyHit(attacker, victim, kind, index)
	if not State.alive(victim) or not State.alive(attacker) or not Resolver.canDamage(attacker, victim) then
		return "none"
	end
	local humanoid = victim:FindFirstChildOfClass("Humanoid")
	local aRoot, vRoot = attacker.HumanoidRootPart, victim.HumanoidRootPart
	local flat = flatLook(aRoot)
	local offset = aRoot.Position - vRoot.Position
	local hitPos = vRoot.Position + (offset.Magnitude > 0.1 and offset.Unit or flat) * 1.1

	if State.hasIFrames(victim) then
		Resolver.fxAll("Dodged", { victim = victim })
		return "dodged"
	end

	if State.isBlocking(victim) then
		local blocked = tryBlock(attacker, victim, kind, index, hitPos, humanoid)
		if blocked then
			return blocked
		end
	end

	humanoid:TakeDamage(damageFor(kind, index))

	local stun, velocity, duration, watch
	if kind == "Jab" then
		stun = Config.M1.HitStun
		if Hitbox.groundDistance(attacker, 30) > 3 then
			velocity = flat * 4 + Vector3.new(0, Config.Air.JuggleLift, 0)
			duration = 0.12
		else
			velocity = flat * Config.M1.JabPush
			duration = 0.1
		end
	elseif kind == "Finisher" then
		stun = Config.M1.FinisherStun
		velocity = flat * Config.M1.FinisherKnockback + Vector3.new(0, Config.M1.FinisherLift, 0)
		duration = 0.22
		watch = "Wall"
	elseif kind == "Uptilt" then
		stun = Config.Uptilt.Stun
		velocity = flat * 4 + Vector3.new(0, Config.Uptilt.Launch, 0)
		duration = Config.Uptilt.LaunchTime
	elseif kind == "Spike" then
		stun = Config.Slam.SpikeStun
		velocity = flat * 8 + Vector3.new(0, -Config.Slam.SpikeVelocity, 0)
		duration = 0.5
		watch = "Ground"
	else -- SlamAoE
		local out = (vRoot.Position - aRoot.Position) * Vector3.new(1, 0, 1)
		out = out.Magnitude > 0.1 and out.Unit or flat
		stun = Config.Slam.AoEStun
		velocity = out * Config.Slam.AoEKnockback + Vector3.new(0, Config.Slam.AoELift, 0)
		duration = 0.18
		watch = "Wall"
	end

	State.stun(victim, stun)
	Resolver.knockback(victim, velocity, duration)
	if watch then
		Resolver.watchImpact(victim, attacker, watch)
	end

	Resolver.fxAll("Hit", { victim = victim, position = hitPos, kind = kind, direction = velocity.Unit })
	Resolver.fxAll("Pose", { character = victim, name = "Hurt" })
	local victimPlayer = Players:GetPlayerFromCharacter(victim)
	if victimPlayer then
		Resolver.fxPlayer(victimPlayer, "Hurt", { kind = kind })
	end
	return "hit"
end

return Resolver
