-- ReplicatedStorage/Combat/ClientEvents (ModuleScript, client-side use)
-- Turns server broadcasts into poses, VFX, camera shake and local knockback.

local Players = game:GetService("Players")

local Combat = script.Parent
local Crater = require(Combat.Crater)
local Knockback = require(Combat.Knockback)
local Poses = require(Combat.Poses)
local VFX = require(Combat.VFX)

local ClientEvents = {}

local player = Players.LocalPlayer

local function myRoot()
	local character = player.Character
	return character and character:FindFirstChild("HumanoidRootPart")
end

local function shakeNear(position, radius, strength, duration)
	local root = myRoot()
	if not root then
		return
	end
	local distance = (root.Position - position).Magnitude
	if distance < radius then
		VFX.shake(strength * (1 - distance / radius), duration)
	end
end

function ClientEvents.connect(callbacks)
	local events = Combat:WaitForChild("CombatEvents")

	events.OnClientEvent:Connect(function(name, payload)
		payload = payload or {}
		local mine = payload.character ~= nil and payload.character == player.Character

		if name == "Pose" then
			-- Our own attacks/dodges/blocks were already played locally.
			if not (mine and payload.fromAttacker) then
				Poses.play(payload.character, payload.name)
			end
		elseif name == "PoseRelease" then
			if not mine then
				Poses.release(payload.character, payload.name)
			end
		elseif name == "Hit" then
			VFX.hit(payload.victim, payload.position, payload.kind, payload.direction)
		elseif name == "Impact" then
			Crater.spawn(payload.position, payload.normal, payload.material, payload.color, payload.intensity)
			shakeNear(payload.position, 70, 3.5 * (payload.intensity or 1), 0.4)
		elseif name == "Block" then
			VFX.block(payload.position)
		elseif name == "Parry" then
			VFX.parry(payload.position)
			shakeNear(payload.position, 30, 2, 0.2)
		elseif name == "GuardBreak" then
			VFX.guardBreak(payload.position)
			shakeNear(payload.position, 30, 2, 0.25)
		elseif name == "Dodge" then
			if not mine then
				VFX.dodge(payload.character)
			end
		elseif name == "Dodged" then
			VFX.afterimage(payload.victim, Color3.fromRGB(170, 220, 255))
		elseif name == "SlamStart" then
			if not mine then
				VFX.trail(payload.character, VFX.KindColors.Spike, 1.5)
			end
		elseif name == "Knockback" then
			if player.Character then
				Knockback.apply(player.Character, payload.velocity, payload.duration)
			end
		elseif name == "StopKnockback" then
			Knockback.stop(player.Character)
		elseif name == "Hurt" then
			VFX.shake(payload.kind == "Jab" and 1 or 2.5, 0.25)
			if callbacks.onHurt then
				callbacks.onHurt(payload)
			end
		elseif name == "HitConfirm" then
			if callbacks.onHitConfirm then
				callbacks.onHitConfirm(payload)
			end
		end
	end)
end

return ClientEvents
