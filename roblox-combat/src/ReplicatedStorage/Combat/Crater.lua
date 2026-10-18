-- ReplicatedStorage/Combat/Crater (ModuleScript, client-side use)
-- Ground/wall impact: a ring of rubble that matches the surface's material and
-- color, flying debris chunks, a dust cloud and a shockwave disc. Works on any
-- surface orientation, so the same call makes floor craters and wall splats.

local Debris = game:GetService("Debris")

local VFX = require(script.Parent.VFX)

local Crater = {}

local rng = Random.new()

local function applyLook(p, material, color)
	pcall(function()
		p.Material = material
	end)
	p.Color = color
end

local function surfaceBasis(position, normal)
	local up = normal.Unit
	local ref = math.abs(up.Y) > 0.95 and Vector3.zAxis or Vector3.yAxis
	local right = ref:Cross(up).Unit
	return CFrame.fromMatrix(position, right, up)
end

local function rubbleRing(base, material, color, intensity)
	local count = math.floor(8 + 6 * intensity)
	local radius = 2.5 + 2.5 * intensity
	for i = 1, count do
		local angle = (i / count) * math.pi * 2 + rng:NextNumber(-0.15, 0.15)
		local scale = 0.8 + 0.35 * intensity
		local size = Vector3.new(rng:NextNumber(1.2, 2.3), rng:NextNumber(0.8, 1.7), rng:NextNumber(1.2, 2.3)) * scale
		local offset = Vector3.new(math.cos(angle) * radius, size.Y * 0.15, math.sin(angle) * radius)
		local final = base
			* CFrame.new(offset)
			* CFrame.Angles(rng:NextNumber(-0.6, 0.6), rng:NextNumber(0, math.pi * 2), rng:NextNumber(-0.6, 0.6))
		local rock = Instance.new("Part")
		rock.Anchored = true
		rock.CanCollide = false
		rock.CanQuery = false
		rock.CanTouch = false
		rock.Size = size
		rock.CFrame = final * CFrame.new(0, -size.Y * 1.5, 0)
		applyLook(rock, material, color)
		rock.Parent = VFX.folder()

		VFX.tween(rock, 0.14, { CFrame = final }, Enum.EasingStyle.Back)
		local linger = 2.5 + rng:NextNumber(0, 1)
		task.delay(linger, function()
			VFX.tween(rock, 0.6, { CFrame = final * CFrame.new(0, -size.Y * 1.5, 0), Transparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		end)
		Debris:AddItem(rock, linger + 0.7)
	end
end

local function flyingDebris(position, base, material, color, intensity)
	local up = base.UpVector
	for _ = 1, math.floor(5 + 5 * intensity) do
		local chunk = Instance.new("Part")
		chunk.Size = Vector3.one * rng:NextNumber(0.5, 1.1)
		chunk.CFrame = CFrame.new(position + up * 1.2) * CFrame.Angles(rng:NextNumber(0, 6), rng:NextNumber(0, 6), 0)
		chunk.CanQuery = false
		chunk.CanTouch = false
		applyLook(chunk, material, color)
		chunk.Parent = VFX.folder()

		local tangent = (base.RightVector * rng:NextNumber(-1, 1) + base.LookVector * rng:NextNumber(-1, 1))
		tangent = tangent.Magnitude > 0 and tangent.Unit or base.RightVector
		chunk.AssemblyLinearVelocity = up * rng:NextNumber(30, 55) * intensity + tangent * rng:NextNumber(12, 30)
		chunk.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-15, 15), rng:NextNumber(-15, 15), rng:NextNumber(-15, 15))

		task.delay(1.6, function()
			VFX.tween(chunk, 0.5, { Transparency = 1 })
		end)
		Debris:AddItem(chunk, 2.2)
	end
end

function Crater.spawn(position, normal, material, color, intensity)
	intensity = math.clamp(intensity or 1, 0.4, 2.5)
	normal = (normal and normal.Magnitude > 0) and normal or Vector3.yAxis
	if material == nil or material == Enum.Material.Air then
		material = Enum.Material.Slate
	end
	color = color or Color3.fromRGB(110, 105, 100)

	local base = surfaceBasis(position, normal)
	rubbleRing(base, material, color, intensity)
	flyingDebris(position, base, material, color, intensity)

	VFX.burst(position + normal * 1, {
		texture = VFX.Textures.Smoke,
		color = Color3.fromRGB(175, 165, 150),
		count = math.floor(12 + 8 * intensity),
		speed = 16 * intensity,
		size = 3 * intensity,
		endSize = 6 * intensity,
		life = 0.9,
		light = 0,
		drag = 5,
		startTransparency = 0.3,
	})
	VFX.ring(position + normal * 0.2, normal, Color3.fromRGB(255, 245, 230), 2, 16 * intensity, 0.35)
	VFX.flashSphere(position, Color3.fromRGB(255, 240, 220), 6 * intensity, 0.18)
end

return Crater
