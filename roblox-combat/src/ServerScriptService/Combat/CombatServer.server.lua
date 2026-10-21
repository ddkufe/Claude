-- ServerScriptService/Combat/CombatServer (Script)
-- Receives combat requests, validates timing/range/state, and resolves hits.
-- Clients do their own hit detection for responsiveness; the server re-checks
-- every reported victim (range, facing, cooldowns, stun) before applying it.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Combat = ReplicatedStorage:WaitForChild("Combat")
local Config = require(Combat.Config)
local Hitbox = require(Combat.Hitbox)
local State = require(script.Parent.CombatState)
local Resolver = require(script.Parent.HitResolver)

local function getRemote(name)
	local r = Combat:FindFirstChild(name)
	if not r then
		r = Instance.new("RemoteEvent")
		r.Name = name
		r.Parent = Combat
	end
	return r
end

local Request = getRemote("CombatRequest")
local Events = getRemote("CombatEvents")
Resolver.init(Events)

local handlers = {}

function handlers.M1(_player, character, payload)
	local s = State.get(character)
	if not State.canAct(character) or State.isBlocking(character) or State.isDiving(character) then
		return
	end
	local now = State.now()
	if now - s.lastSwing < Config.M1.SwingCooldown * 0.8 then
		return
	end

	local index = (now - s.lastSwing > Config.M1.ComboResetTime) and 1 or (s.combo % Config.M1.ComboLength) + 1
	s.combo = index
	s.lastSwing = now
	s.swingIndex = index
	s.swingHitDone = false

	local kind, pose = "Jab", "Jab" .. ((index - 1) % 3 + 1)
	if index == Config.M1.ComboLength then
		s.combo = 0
		-- The server's copy of the attacker lags a little behind the client, hence the slack.
		local height = Hitbox.groundDistance(character, 80)
		if payload.slam == true and height >= Config.Slam.MinHeight - 4 then
			kind, pose = "Spike", "SlamDive"
			s.slamStart = now
		elseif payload.up == true then
			kind, pose = "Uptilt", "Uptilt"
			s.endLagUntil = now + Config.Uptilt.EndLag
		else
			kind, pose = "Finisher", "Finisher"
			s.endLagUntil = now + Config.M1.EndLag
		end
	end
	s.swingKind = kind

	Resolver.fxAll("Pose", { character = character, name = pose, fromAttacker = true })
	if kind == "Spike" then
		Resolver.fxAll("SlamStart", { character = character })
	end
end

function handlers.M1Hit(player, character, payload)
	local s = State.get(character)
	local now = State.now()
	if s.swingHitDone or not s.swingKind or now - s.lastSwing > 0.6 then
		return
	end
	s.swingHitDone = true
	-- Got hit during your own windup: you lose the trade.
	if State.isStunned(character) or type(payload.hits) ~= "table" then
		return
	end

	local kind = s.swingKind
	local range = kind == "Spike" and Config.Hit.SlamValidationRange or Config.Hit.MaxValidationRange
	local root = character.HumanoidRootPart
	local look = root.CFrame.LookVector
	local results, seen, count = {}, {}, 0

	for _, victim in ipairs(payload.hits) do
		if count >= Config.Hit.MaxTargets then
			break
		end
		if typeof(victim) == "Instance" and victim:IsA("Model") and victim ~= character and not seen[victim] then
			seen[victim] = true
			if State.alive(victim) then
				local offset = victim.HumanoidRootPart.Position - root.Position
				local inFront = offset.Magnitude < 3 or look:Dot(offset.Unit) >= Config.Hit.MinFacingDot
				if offset.Magnitude <= range and (inFront or kind == "Spike") then
					count += 1
					table.insert(results, Resolver.applyHit(character, victim, kind, s.swingIndex))
				end
			end
		end
	end

	if count > 0 then
		Resolver.fxPlayer(player, "HitConfirm", { kind = kind, results = results })
	end
end

function handlers.SlamLand(player, character, payload)
	local s = State.get(character)
	local start = s.slamStart
	s.slamStart = nil
	if not start or State.now() - start > 3 or typeof(payload.position) ~= "Vector3" then
		return
	end
	-- The client lands before the server sees it (ping), so trust its landing
	-- point within a generous radius, then confirm there's real ground there.
	local root = character.HumanoidRootPart
	if (payload.position - root.Position).Magnitude > 45 then
		return
	end
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { character }
	local ground = workspace:Raycast(payload.position + Vector3.new(0, 4, 0), Vector3.new(0, -12, 0), rp)
	if not ground then
		return
	end

	s.endLagUntil = State.now() + Config.Slam.EndLag
	local pos, normal, material, color = Resolver.surfaceInfo(ground)
	Resolver.fxAll("Impact", { position = pos, normal = normal, material = material, color = color, intensity = 1.8 })
	Resolver.fxAll("Pose", { character = character, name = "SlamLand", fromAttacker = true })

	local victims = Hitbox.radius(pos, Config.Slam.AoERadius, { character })
	local results = {}
	for _, victim in ipairs(victims) do
		table.insert(results, Resolver.applyHit(character, victim, "SlamAoE", 0))
	end
	if #victims > 0 then
		Resolver.fxPlayer(player, "HitConfirm", { kind = "SlamAoE", results = results })
	end
end

function handlers.Dodge(_player, character)
	local s = State.get(character)
	local now = State.now()
	if now < s.dodgeReady then
		return
	end
	if State.isStunned(character) then
		if not Config.Dodge.CanEscapeStun then
			return
		end
		character:SetAttribute("StunEnd", now)
	end
	s.dodgeReady = now + Config.Dodge.Cooldown
	State.grantIFrames(character, Config.Dodge.IFrames + 0.05)
	if State.isBlocking(character) then
		State.setBlocking(character, false)
	end
	Resolver.fxAll("Dodge", { character = character })
	Resolver.fxAll("Pose", { character = character, name = "Dodge", fromAttacker = true })
end

-- The stance itself is played by clients; the server only publishes it so other players see it.
function handlers.Stance(_player, character, payload)
	if Config.Stance.Enabled then
		character:SetAttribute("InStance", payload.on == true)
	end
end

function handlers.Block(_player, character, payload)
	local s = State.get(character)
	if payload.on == true then
		if State.isBlocking(character) or not State.canAct(character) or State.isDiving(character) or State.now() < s.blockReady then
			return
		end
		State.setBlocking(character, true)
		Resolver.fxAll("Pose", { character = character, name = "Block", fromAttacker = true })
	elseif State.isBlocking(character) then
		State.setBlocking(character, false)
		Resolver.fxAll("PoseRelease", { character = character, name = "Block" })
	end
end

local rate = {}

Request.OnServerEvent:Connect(function(player, action, payload)
	local handler = type(action) == "string" and handlers[action]
	if not handler then
		return
	end
	local character = player.Character
	if not character or not State.alive(character) then
		return
	end

	local now = os.clock()
	local r = rate[player]
	if not r or now - r.window > 1 then
		r = { window = now, count = 0 }
		rate[player] = r
	end
	r.count += 1
	if r.count > 25 then
		return
	end

	handler(player, character, type(payload) == "table" and payload or {})
end)

Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(character)
		character:SetAttribute("StunEnd", 0)
		character:SetAttribute("IFrameEnd", 0)
		character:SetAttribute("Blocking", false)
		character:SetAttribute("InStance", false)
	end)
end)

Players.PlayerRemoving:Connect(function(player)
	rate[player] = nil
end)
