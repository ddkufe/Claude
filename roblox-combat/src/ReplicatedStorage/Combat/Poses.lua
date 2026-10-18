-- ReplicatedStorage/Combat/Poses (ModuleScript)
-- Procedural R6 attack/hurt poses, layered on top of the default Animate
-- script by tweening Motor6D.C0. If Config.Animations has a real id for a
-- move, that AnimationTrack is played instead.
-- Rotations are {x, y, z} radians in Torso space at the joint pivot:
--   +x swings a limb forward, +z swings a right limb outward (left limbs: -z),
--   Root +x leans the torso back, Root +y twists the torso left.

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.Config)

local Poses = {}

local MOTORS = {
	RS = { "Torso", "Right Shoulder" },
	LS = { "Torso", "Left Shoulder" },
	RH = { "Torso", "Right Hip" },
	LH = { "Torso", "Left Hip" },
	Neck = { "Torso", "Neck" },
	Root = { "HumanoidRootPart", "RootJoint" },
}

local H = math.pi / 2

Poses.Library = {
	Jab1 = { hold = 0.12, pose = { RS = { H, 0, 0 }, LS = { 0.8, 0, 0.3 }, Root = { -0.1, 0.45, 0 } } },
	Jab2 = { hold = 0.12, pose = { LS = { H, 0, 0 }, RS = { 0.8, 0, -0.3 }, Root = { -0.1, -0.45, 0 } } },
	Jab3 = { hold = 0.14, pose = { RS = { 1.3, 0, 0.9 }, LS = { 0.6, 0, 0.3 }, Root = { -0.15, 0.75, 0 } } },
	Finisher = {
		hold = 0.24,
		pose = { RH = { 1.75, 0, 0 }, LH = { -0.25, 0, 0 }, RS = { 0.4, 0, 0.8 }, LS = { 0.4, 0, -0.8 }, Root = { 0.3, 0.25, 0 } },
	},
	Uptilt = {
		hold = 0.28,
		pose = {
			RS = { 3.0, 0, 0.15 },
			LS = { 0.5, 0, -0.5 },
			RH = { -0.3, 0, 0 },
			LH = { 0.55, 0, 0 },
			Root = { 0.35, 0.3, 0 },
			Neck = { 0.35, 0, 0 },
		},
	},
	SlamDive = {
		hold = 1.6,
		pose = { RS = { 3.0, 0, 0 }, LS = { 3.0, 0, 0 }, RH = { 0.9, 0, 0 }, LH = { 0.9, 0, 0 }, Root = { -0.7, 0, 0 } },
	},
	SlamLand = {
		hold = 0.3,
		pose = { RS = { 1.0, 0, 0.3 }, LS = { 1.0, 0, -0.3 }, RH = { 0.9, 0, 0 }, LH = { -0.6, 0, 0 }, Root = { -0.5, 0, 0 } },
	},
	Hurt = {
		hold = 0.25,
		pose = { RS = { 0.4, 0, 0.6 }, LS = { 0.4, 0, -0.6 }, Root = { 0.35, 0, 0.1 }, Neck = { 0.4, 0, 0 } },
	},
	GuardBroken = {
		hold = 0.8,
		pose = { RS = { 0.6, 0, 1.4 }, LS = { 0.6, 0, -1.4 }, Root = { 0.45, 0, 0 }, Neck = { 0.5, 0, 0 } },
	},
	Block = {
		hold = math.huge,
		pose = { RS = { 1.6, 0, -0.7 }, LS = { 1.6, 0, 0.7 }, Root = { -0.12, 0, 0 }, Neck = { -0.1, 0, 0 } },
	},
	Dodge = {
		hold = 0.18,
		pose = { RS = { -0.5, 0, 0.3 }, LS = { -0.5, 0, -0.3 }, RH = { 0.6, 0, 0 }, LH = { -0.4, 0, 0 }, Root = { -0.45, 0, 0 } },
	},
}

local defaults = setmetatable({}, { __mode = "k" })
local tokens = setmetatable({}, { __mode = "k" })
local tracks = setmetatable({}, { __mode = "k" })

local function getMotor(character, key)
	local spec = MOTORS[key]
	local part = character:FindFirstChild(spec[1])
	return part and part:FindFirstChild(spec[2])
end

local function baseC0(motor)
	local base = defaults[motor]
	if not base then
		base = motor.C0
		defaults[motor] = base
	end
	return base
end

local function rotated(base, r)
	return CFrame.new(base.Position) * CFrame.Angles(r[1], r[2], r[3]) * base.Rotation
end

local function tweenC0(motor, goal, duration)
	TweenService:Create(motor, TweenInfo.new(duration, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { C0 = goal })
		:Play()
end

function Poses.usesTrack(name)
	local id = Config.Animations[name]
	return id ~= nil and id ~= ""
end

local function playTrack(character, name)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local animator = humanoid and humanoid:FindFirstChildOfClass("Animator")
	if not animator then
		return
	end
	local cache = tracks[character]
	if not cache then
		cache = {}
		tracks[character] = cache
	end
	local track = cache[name]
	if not track then
		local animation = Instance.new("Animation")
		animation.AnimationId = Config.Animations[name]
		track = animator:LoadAnimation(animation)
		track.Priority = Enum.AnimationPriority.Action
		cache[name] = track
	end
	track:Play(0.05)
end

function Poses.release(character, name)
	if not character then
		return
	end
	if name and Poses.usesTrack(name) then
		local cache = tracks[character]
		if cache and cache[name] then
			cache[name]:Stop(0.1)
		end
		return
	end
	tokens[character] = nil
	for key in pairs(MOTORS) do
		local motor = getMotor(character, key)
		if motor and defaults[motor] then
			tweenC0(motor, defaults[motor], 0.18)
		end
	end
end

function Poses.play(character, name, hold)
	local entry = Poses.Library[name]
	if not entry or not character then
		return
	end
	hold = hold or entry.hold

	if Poses.usesTrack(name) then
		-- A player's own client plays (and replicates) their tracks.
		local owner = Players:GetPlayerFromCharacter(character)
		if owner and owner ~= Players.LocalPlayer then
			return
		end
		playTrack(character, name)
		return
	end

	local token = {}
	tokens[character] = token
	for key in pairs(MOTORS) do
		local motor = getMotor(character, key)
		if motor then
			local base = baseC0(motor)
			local r = entry.pose[key]
			tweenC0(motor, r and rotated(base, r) or base, 0.07)
		end
	end

	if hold ~= math.huge then
		task.delay(0.07 + hold, function()
			if tokens[character] == token then
				Poses.release(character)
			end
		end)
	end
end

return Poses
