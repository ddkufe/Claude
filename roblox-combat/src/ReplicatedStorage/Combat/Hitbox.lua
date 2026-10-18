-- ReplicatedStorage/Combat/Hitbox (ModuleScript)
-- Spatial-query hitboxes that return living characters (players or NPCs).

local Config = require(script.Parent.Config)

local Hitbox = {}

local function characterFromPart(part)
	local parent = part.Parent
	if not parent then
		return nil
	end
	if parent:IsA("Accessory") then
		parent = parent.Parent
	end
	local humanoid = parent and parent:FindFirstChildOfClass("Humanoid")
	if humanoid and humanoid.Health > 0 then
		return parent
	end
	return nil
end

local function collect(parts, origin)
	local seen, list = {}, {}
	for _, part in ipairs(parts) do
		local character = characterFromPart(part)
		if character and not seen[character] and character:FindFirstChild("HumanoidRootPart") then
			seen[character] = true
			table.insert(list, character)
		end
	end
	table.sort(list, function(a, b)
		return (a.HumanoidRootPart.Position - origin).Magnitude < (b.HumanoidRootPart.Position - origin).Magnitude
	end)
	local max = Config.Hit.MaxTargets
	while #list > max do
		table.remove(list)
	end
	return list
end

local function params(ignore)
	local op = OverlapParams.new()
	op.FilterType = Enum.RaycastFilterType.Exclude
	op.FilterDescendantsInstances = ignore
	return op
end

function Hitbox.box(cframe, size, ignore)
	local parts = workspace:GetPartBoundsInBox(cframe, size, params(ignore))
	return collect(parts, cframe.Position)
end

function Hitbox.radius(position, radius, ignore)
	local parts = workspace:GetPartBoundsInRadius(position, radius, params(ignore))
	return collect(parts, position)
end

function Hitbox.debugDraw(cframe, size, color)
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Transparency = 0.7
	p.Color = color or Color3.fromRGB(255, 60, 60)
	p.Material = Enum.Material.ForceField
	p.Size = size
	p.CFrame = cframe
	p.Parent = workspace
	game:GetService("Debris"):AddItem(p, 0.25)
end

function Hitbox.groundDistance(character, maxDistance)
	local hrp = character:FindFirstChild("HumanoidRootPart")
	if not hrp then
		return math.huge
	end
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { character }
	local result = workspace:Raycast(hrp.Position, Vector3.new(0, -(maxDistance or 200), 0), rp)
	if not result then
		return math.huge, nil
	end
	-- HRP center sits 3 studs above the feet on an R6 rig
	return (hrp.Position - result.Position).Magnitude - 3, result
end

return Hitbox
