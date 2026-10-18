-- ReplicatedStorage/Combat/Knockback (ModuleScript)
-- Shared by server (for NPCs it owns) and client (for its own character),
-- because a player's character physics are owned by that player's client.

local Knockback = {}

local NAME = "CombatKnockback"

local function rootOf(character)
	return character and character:FindFirstChild("HumanoidRootPart")
end

function Knockback.stop(character)
	local hrp = rootOf(character)
	if not hrp then
		return
	end
	local existing = hrp:FindFirstChild(NAME)
	if existing then
		existing:Destroy()
	end
end

function Knockback.apply(character, velocity, duration)
	local hrp = rootOf(character)
	if not hrp then
		return
	end
	Knockback.stop(character)

	local attachment = hrp:FindFirstChild("RootAttachment") or hrp:FindFirstChildWhichIsA("Attachment")
	if not attachment then
		attachment = Instance.new("Attachment")
		attachment.Name = "RootAttachment"
		attachment.Parent = hrp
	end

	local lv = Instance.new("LinearVelocity")
	lv.Name = NAME
	lv.Attachment0 = attachment
	lv.RelativeTo = Enum.ActuatorRelativeTo.World
	lv.MaxForce = math.huge
	lv.VectorVelocity = velocity
	lv.Parent = hrp

	hrp.AssemblyLinearVelocity = velocity

	task.delay(duration, function()
		if lv.Parent then
			lv:Destroy()
		end
	end)
	return lv
end

return Knockback
