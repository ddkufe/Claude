-- ReplicatedStorage/Combat/VFX (ModuleScript, client-side use)
-- Hit sparks, flashes, shockwave discs, afterimages, trails, camera shake.
-- Uses only built-in rbxasset:// textures, so nothing needs uploading.

local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local VFX = {}

VFX.Textures = {
	Spark = "rbxasset://textures/particles/sparkles_main.dds",
	Smoke = "rbxasset://textures/particles/smoke_main.dds",
	Fire = "rbxasset://textures/particles/fire_main.dds",
}

VFX.KindColors = {
	Jab = Color3.fromRGB(255, 255, 255),
	Finisher = Color3.fromRGB(255, 190, 90),
	Uptilt = Color3.fromRGB(120, 205, 255),
	Spike = Color3.fromRGB(190, 120, 255),
	SlamAoE = Color3.fromRGB(190, 120, 255),
	WallSplat = Color3.fromRGB(255, 120, 80),
}

local rng = Random.new()
local folder

function VFX.folder()
	if not folder or not folder.Parent then
		folder = Instance.new("Folder")
		folder.Name = "CombatVFX_Local"
		folder.Parent = workspace
	end
	return folder
end

function VFX.part(props)
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.Neon
	for key, value in pairs(props) do
		p[key] = value
	end
	p.Parent = VFX.folder()
	return p
end

function VFX.tween(instance, duration, goal, style, direction)
	local info = TweenInfo.new(duration, style or Enum.EasingStyle.Quad, direction or Enum.EasingDirection.Out)
	local tw = TweenService:Create(instance, info, goal)
	tw:Play()
	return tw
end

function VFX.burst(position, opts)
	local life = opts.life or 0.3
	local speed = opts.speed or 20
	local holder = VFX.part({ Transparency = 1, Size = Vector3.one * 0.2, CFrame = CFrame.new(position) })
	local attachment = Instance.new("Attachment")
	attachment.Parent = holder

	local pe = Instance.new("ParticleEmitter")
	pe.Texture = opts.texture or VFX.Textures.Spark
	pe.Color = ColorSequence.new(opts.color or Color3.new(1, 1, 1))
	pe.LightEmission = opts.light or 1
	pe.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, opts.size or 1),
		NumberSequenceKeypoint.new(1, opts.endSize or 0),
	})
	pe.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, opts.startTransparency or 0),
		NumberSequenceKeypoint.new(1, 1),
	})
	pe.Lifetime = NumberRange.new(life, life * 1.6)
	pe.Speed = NumberRange.new(speed, speed * 1.8)
	pe.SpreadAngle = opts.spread or Vector2.new(180, 180)
	pe.Acceleration = opts.accel or Vector3.zero
	pe.Drag = opts.drag or 4
	pe.Rate = 0
	pe.Rotation = NumberRange.new(0, 360)
	pe.RotSpeed = NumberRange.new(-200, 200)
	if opts.direction then
		holder.CFrame = CFrame.lookAt(position, position + opts.direction) * CFrame.Angles(-math.pi / 2, 0, 0)
		pe.EmissionDirection = Enum.NormalId.Top
	end
	pe.Parent = attachment
	pe:Emit(opts.count or 15)
	Debris:AddItem(holder, life * 2 + 0.3)
end

function VFX.flashSphere(position, color, size, duration)
	local s = VFX.part({
		Shape = Enum.PartType.Ball,
		Color = color,
		Size = Vector3.one * size * 0.3,
		CFrame = CFrame.new(position),
		Transparency = 0.05,
	})
	VFX.tween(s, duration, { Size = Vector3.one * size, Transparency = 1 })
	Debris:AddItem(s, duration + 0.05)
end

-- Flat shockwave disc whose face points along `axis`.
function VFX.ring(position, axis, color, startSize, endSize, duration)
	axis = axis.Magnitude > 0 and axis.Unit or Vector3.yAxis
	local up = math.abs(axis.Y) > 0.99 and Vector3.xAxis or Vector3.yAxis
	local cf = CFrame.lookAt(position, position + axis, up) * CFrame.Angles(0, math.pi / 2, 0)
	local disc = VFX.part({
		Shape = Enum.PartType.Cylinder,
		Color = color,
		Transparency = 0.35,
		Size = Vector3.new(0.2, startSize, startSize),
		CFrame = cf,
	})
	VFX.tween(disc, duration, { Size = Vector3.new(0.05, endSize, endSize), Transparency = 1 })
	Debris:AddItem(disc, duration + 0.05)
end

function VFX.flashCharacter(character, color, duration)
	if not character then
		return
	end
	local hl = Instance.new("Highlight")
	hl.FillColor = color
	hl.OutlineColor = Color3.new(1, 1, 1)
	hl.FillTransparency = 0.2
	hl.OutlineTransparency = 0
	hl.DepthMode = Enum.HighlightDepthMode.Occluded
	hl.Adornee = character
	hl.Parent = VFX.folder()
	VFX.tween(hl, duration, { FillTransparency = 1, OutlineTransparency = 1 })
	Debris:AddItem(hl, duration + 0.05)
end

function VFX.afterimage(character, color)
	if not character then
		return
	end
	for i = 0, 2 do
		task.delay(i * 0.06, function()
			for _, p in ipairs(character:GetChildren()) do
				if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and p.Transparency < 1 then
					local ghost = VFX.part({ Size = p.Size, CFrame = p.CFrame, Color = color, Transparency = 0.45 })
					VFX.tween(ghost, 0.35, { Transparency = 1 })
					Debris:AddItem(ghost, 0.4)
				end
			end
		end)
	end
end

function VFX.trail(character, color, duration)
	local hrp = character and character:FindFirstChild("HumanoidRootPart")
	if not hrp then
		return
	end
	local a0 = Instance.new("Attachment")
	a0.Position = Vector3.new(0, 1.6, 0)
	a0.Parent = hrp
	local a1 = Instance.new("Attachment")
	a1.Position = Vector3.new(0, -1.6, 0)
	a1.Parent = hrp
	local trail = Instance.new("Trail")
	trail.Attachment0 = a0
	trail.Attachment1 = a1
	trail.Color = ColorSequence.new(color)
	trail.LightEmission = 1
	trail.Transparency = NumberSequence.new(0.15, 1)
	trail.Lifetime = 0.25
	trail.FaceCamera = true
	trail.Parent = hrp
	task.delay(duration, function()
		trail.Enabled = false
		Debris:AddItem(trail, 0.3)
		Debris:AddItem(a0, 0.3)
		Debris:AddItem(a1, 0.3)
	end)
end

local shakes = {}
local shakeBound = false

function VFX.shake(intensity, duration)
	table.insert(shakes, { amount = intensity, duration = duration, start = os.clock() })
	if shakeBound then
		return
	end
	shakeBound = true
	RunService:BindToRenderStep("CombatShake", Enum.RenderPriority.Camera.Value + 1, function()
		local now = os.clock()
		local total = 0
		for i = #shakes, 1, -1 do
			local s = shakes[i]
			local alpha = (now - s.start) / s.duration
			if alpha >= 1 then
				table.remove(shakes, i)
			else
				total += s.amount * (1 - alpha)
			end
		end
		if total <= 0 then
			RunService:UnbindFromRenderStep("CombatShake")
			shakeBound = false
			return
		end
		local cam = workspace.CurrentCamera
		cam.CFrame = cam.CFrame
			* CFrame.new(rng:NextNumber(-1, 1) * total * 0.06, rng:NextNumber(-1, 1) * total * 0.06, 0)
			* CFrame.Angles(math.rad(rng:NextNumber(-1, 1) * total), math.rad(rng:NextNumber(-1, 1) * total), 0)
	end)
end

local baseFov
function VFX.fovPunch(amount, duration)
	local cam = workspace.CurrentCamera
	baseFov = baseFov or cam.FieldOfView
	cam.FieldOfView = baseFov + amount
	VFX.tween(cam, duration, { FieldOfView = baseFov })
end

-- Composite effects ---------------------------------------------------------

function VFX.hit(victim, position, kind, direction)
	local color = VFX.KindColors[kind] or Color3.new(1, 1, 1)
	local heavy = kind ~= "Jab"
	VFX.flashSphere(position, color, heavy and 7 or 4, heavy and 0.22 or 0.13)
	VFX.burst(position, {
		color = color,
		count = heavy and 30 or 12,
		speed = heavy and 50 or 28,
		size = heavy and 1.2 or 0.7,
		life = 0.25,
	})
	if heavy then
		VFX.ring(position, direction or Vector3.yAxis, color, 2, 14, 0.25)
	end
	if kind == "Uptilt" then
		VFX.burst(position - Vector3.new(0, 2.5, 0), {
			texture = VFX.Textures.Smoke,
			color = Color3.fromRGB(220, 235, 255),
			count = 10,
			speed = 35,
			size = 2.5,
			endSize = 4,
			life = 0.35,
			light = 0.3,
			direction = Vector3.yAxis,
			spread = Vector2.new(20, 20),
		})
	end
	VFX.flashCharacter(victim, color, heavy and 0.25 or 0.15)
end

function VFX.block(position)
	local c = Color3.fromRGB(150, 210, 255)
	VFX.flashSphere(position, c, 3.5, 0.12)
	VFX.burst(position, { color = c, count = 10, speed = 22, size = 0.6, life = 0.2 })
end

function VFX.parry(position)
	VFX.flashSphere(position, Color3.new(1, 1, 1), 10, 0.2)
	VFX.burst(position, { color = Color3.fromRGB(255, 220, 120), count = 35, speed = 55, size = 1, life = 0.3 })
	VFX.ring(position, Vector3.yAxis, Color3.fromRGB(255, 230, 150), 2, 18, 0.3)
end

function VFX.guardBreak(position)
	VFX.flashSphere(position, Color3.fromRGB(255, 70, 70), 8, 0.2)
	VFX.burst(position, { color = Color3.fromRGB(150, 210, 255), count = 25, speed = 45, size = 0.9, life = 0.4, accel = Vector3.new(0, -60, 0) })
end

function VFX.dodge(character)
	VFX.afterimage(character, Color3.fromRGB(170, 220, 255))
	local hrp = character and character:FindFirstChild("HumanoidRootPart")
	if hrp then
		VFX.burst(hrp.Position - Vector3.new(0, 2.6, 0), {
			texture = VFX.Textures.Smoke,
			color = Color3.fromRGB(200, 195, 185),
			count = 8,
			speed = 10,
			size = 2,
			endSize = 3.5,
			life = 0.45,
			light = 0,
		})
	end
end

return VFX
