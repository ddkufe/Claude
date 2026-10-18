-- ServerScriptService/Combat/CombatState (ModuleScript)
-- Per-character combat state. Timers that clients need to read are mirrored
-- as attributes on the character, in workspace:GetServerTimeNow() units.

local Players = game:GetService("Players")

local Config = require(game:GetService("ReplicatedStorage").Combat.Config)

local CombatState = {}

local data = setmetatable({}, { __mode = "k" })

function CombatState.now()
	return workspace:GetServerTimeNow()
end

function CombatState.get(character)
	local s = data[character]
	if not s then
		s = {
			combo = 0,
			lastSwing = -math.huge,
			swingKind = nil,
			swingHitDone = true,
			endLagUntil = 0,
			dodgeReady = 0,
			blockStart = 0,
			blockReady = 0,
			slamStart = nil,
		}
		data[character] = s
	end
	return s
end

local function humanoidOf(character)
	return character and character:FindFirstChildOfClass("Humanoid")
end

function CombatState.alive(character)
	local h = humanoidOf(character)
	return h ~= nil and h.Health > 0 and character:FindFirstChild("HumanoidRootPart") ~= nil
end

function CombatState.isStunned(character)
	return (character:GetAttribute("StunEnd") or 0) > CombatState.now()
end

function CombatState.hasIFrames(character)
	return (character:GetAttribute("IFrameEnd") or 0) > CombatState.now()
end

function CombatState.isBlocking(character)
	return character:GetAttribute("Blocking") == true
end

-- Times out so a client that never reports landing can't lock itself up.
function CombatState.isDiving(character)
	local start = CombatState.get(character).slamStart
	return start ~= nil and CombatState.now() - start < 3
end

function CombatState.canAct(character)
	if not CombatState.alive(character) or CombatState.isStunned(character) then
		return false
	end
	return CombatState.now() >= CombatState.get(character).endLagUntil
end

function CombatState.stun(character, duration)
	local now = CombatState.now()
	local finish = math.max(character:GetAttribute("StunEnd") or 0, now + duration)
	character:SetAttribute("StunEnd", finish)
	character:SetAttribute("Blocking", false)

	local s = CombatState.get(character)
	s.combo = 0
	s.slamStart = nil

	-- Players' speed is driven by their own client from the StunEnd attribute.
	-- NPCs are server-owned, so slow them here.
	if not Players:GetPlayerFromCharacter(character) then
		local humanoid = humanoidOf(character)
		if humanoid then
			if humanoid:GetAttribute("BaseWalkSpeed") == nil then
				humanoid:SetAttribute("BaseWalkSpeed", humanoid.WalkSpeed)
			end
			humanoid.WalkSpeed = Config.Movement.StunnedSpeed
			task.delay(finish - now + 0.02, function()
				if humanoid.Parent and not CombatState.isStunned(character) then
					humanoid.WalkSpeed = humanoid:GetAttribute("BaseWalkSpeed")
				end
			end)
		end
	end
end

function CombatState.grantIFrames(character, duration)
	character:SetAttribute("IFrameEnd", CombatState.now() + duration)
end

function CombatState.setBlocking(character, on)
	character:SetAttribute("Blocking", on)
	local s = CombatState.get(character)
	if on then
		s.blockStart = CombatState.now()
	else
		s.blockReady = CombatState.now() + Config.Block.ReleaseCooldown
	end
end

return CombatState
