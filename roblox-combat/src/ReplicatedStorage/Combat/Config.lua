-- ReplicatedStorage/Combat/Config (ModuleScript)
-- Every tunable number for the combat system lives here.

local Config = {}

Config.Debug = {
	ShowHitboxes = false,
}

Config.M1 = {
	ComboLength = 4,
	ComboResetTime = 1.1,
	SwingCooldown = 0.32,
	EndLag = 0.85,
	Windup = 0.11,
	Damage = { 3.5, 3.5, 4, 7 },
	HitboxSize = Vector3.new(5.5, 6, 5.5),
	HitboxOffset = 3.2,
	Lunge = 16,
	LungeTime = 0.09,
	HitStun = 0.55,
	FinisherStun = 0.9,
	FinisherKnockback = 70,
	FinisherLift = 14,
	JabPush = 7,
	AutoFaceRange = 11,
	AutoFaceAngle = 75,
}

Config.Air = {
	JuggleLift = 20,
	AttackerHang = 9,
}

Config.Uptilt = {
	Damage = 6,
	Launch = 70,
	LaunchTime = 0.16,
	Stun = 1.15,
	AttackerHop = 72,
	EndLag = 0.2,
}

Config.Slam = {
	MinHeight = 7,
	DiveVelocity = 140,
	SpikeDamage = 6,
	SpikeVelocity = 120,
	SpikeStun = 1.2,
	AoEDamage = 6,
	AoERadius = 10,
	AoEStun = 0.9,
	AoEKnockback = 45,
	AoELift = 32,
	EndLag = 0.6,
	HitboxSize = Vector3.new(7, 9, 7),
}

Config.Dodge = {
	Cooldown = 1.6,
	IFrames = 0.3,
	Speed = 90,
	Duration = 0.2,
	CanEscapeStun = false,
	DefaultDirection = "Forward",
}

Config.Block = {
	DamageMultiplier = 0.15,
	PerfectWindow = 0.16,
	ParryStun = 1.1,
	GuardBreakStun = 1.4,
	GuardBreakDamage = 4,
	MaxAngle = 75,
	Pushback = 10,
	ReleaseCooldown = 0.25,
}

Config.Impact = {
	MinSpeed = 35,
	WallSplatDamage = 3,
	WallSplatStun = 0.7,
	GroundBounce = 24,
	WatchTime = 0.7,
}

Config.Movement = {
	WalkSpeed = 16,
	SprintSpeed = 28,
	AttackingSpeed = 9,
	BlockingSpeed = 6,
	StunnedSpeed = 3,
	JumpPower = 50,
}

Config.Hit = {
	MaxTargets = 4,
	MaxValidationRange = 14,
	SlamValidationRange = 18,
	MinFacingDot = -0.35,
	-- false = players on the same Team (village) can't damage each other
	FriendlyFire = true,
}

-- Optional: paste real uploaded R6 animation ids here (e.g. "rbxassetid://123").
-- Any move left as "" falls back to the built-in procedural pose.
Config.Animations = {
	Jab1 = "",
	Jab2 = "",
	Jab3 = "",
	Finisher = "",
	Uptilt = "",
	SlamDive = "",
	SlamLand = "",
	Hurt = "",
	Block = "",
	Dodge = "",
	GuardBroken = "",
}

return Config
