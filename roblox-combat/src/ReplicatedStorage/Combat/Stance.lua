-- ReplicatedStorage/Combat/Stance (ModuleScript, client-side use)
-- The ninja combat stance: draw in -> breathing idle -> relax, with an upper-body
-- guard while moving. Local combat actions enter it; everyone else sees it through
-- the character's "InStance" attribute (set by the server).
--
-- Two ways to play it:
--   * Config.Animations.StanceEnter/Idle/Exit/Move all set -> real AnimationTracks
--     (only the owning client plays them; Roblox replicates them).
--   * otherwise -> procedural: the same keyframes (StanceData) drive Motor6D C0s on
--     every client, through Poses so attacks recover back into the stance.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Combat = script.Parent
local Config = require(Combat.Config)
local Data = require(Combat.StanceData)
local Poses = require(Combat.Poses)

local Stance = {}

local localPlayer = Players.LocalPlayer
local request -- RemoteEvent, set in Stance.init

local MOTOR_KEY = { Root = "Root", Neck = "Neck", RightShoulder = "RS", LeftShoulder = "LS", RightHip = "RH", LeftHip = "LH" }
local UPPER = { "Root", "Neck", "RightShoulder", "LeftShoulder" }
local HIPS = { "RightHip", "LeftHip" }
local IDENTITY = CFrame.new()

-- sampling (pure) -------------------------------------------------------------

local function ease(style, t)
	if style == "CubicOut" then
		return 1 - (1 - t) ^ 3
	elseif style == "CubicIn" then
		return t ^ 3
	elseif style == "CubicInOut" then
		if t < 0.5 then
			return 4 * t ^ 3
		end
		return 1 - ((-2 * t + 2) ^ 3) / 2
	end
	return t -- Linear
end

-- Which two keys time t falls between, and the eased blend between them.
function Stance.locate(anim, t)
	local keys = anim.keys
	if t <= keys[1].t then
		return 1, 1, 0
	end
	for i = 2, #keys do
		if t <= keys[i].t then
			local a, b = keys[i - 1], keys[i]
			return i - 1, i, ease(b.ease, (t - a.t) / (b.t - a.t))
		end
	end
	return #keys, #keys, 0
end

for _, anim in pairs(Data) do
	for _, key in ipairs(anim.keys) do
		key.cf = {}
		for joint, e in pairs(key.pose) do
			key.cf[joint] = CFrame.Angles(math.rad(e[1]), math.rad(e[2]), math.rad(e[3]))
		end
	end
end

local function sample(anim, t)
	local i, j, alpha = Stance.locate(anim, t)
	local from, to = anim.keys[i].cf, anim.keys[j].cf
	local out = {}
	for joint, cf in pairs(from) do
		out[joint] = (i == j) and cf or cf:Lerp(to[joint], alpha)
	end
	return out
end

local function toMotorKeys(rot)
	local out = {}
	for joint, cf in pairs(rot) do
		out[MOTOR_KEY[joint]] = cf
	end
	return out
end

-- state -------------------------------------------------------------------------

-- phase: "off" | "enter" | "hold" | "exit"
local states = setmetatable({}, { __mode = "k" })
local tracks = setmetatable({}, { __mode = "k" })

local function stateOf(character)
	local s = states[character]
	if not s then
		s = { phase = "off", t = 0, mt = 0, blend = 0, locked = false, lastAction = 0, endsAt = 0, trackMoving = false }
		states[character] = s
	end
	return s
end

local function isLocal(character)
	return localPlayer ~= nil and character == localPlayer.Character
end

local function usesTracks()
	local a = Config.Animations
	return (a.StanceEnter or "") ~= "" and (a.StanceIdle or "") ~= "" and (a.StanceExit or "") ~= "" and (a.StanceMove or "") ~= ""
end

local function trackOf(character, key)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local animator = humanoid and humanoid:FindFirstChildOfClass("Animator")
	if not animator then
		return nil
	end
	local cache = tracks[character]
	if not cache then
		cache = {}
		tracks[character] = cache
	end
	local tr = cache[key]
	if not tr then
		local animation = Instance.new("Animation")
		animation.AnimationId = Config.Animations[key]
		tr = animator:LoadAnimation(animation)
		tr.Priority = Enum.AnimationPriority.Movement
		tr.Looped = (key == "StanceIdle" or key == "StanceMove")
		cache[key] = tr
	end
	return tr
end

local function playTrack(character, key, fade)
	local tr = trackOf(character, key)
	if tr then
		tr:Play(fade or 0.1)
	end
end

local function stopTrack(character, key, fade)
	local cache = tracks[character]
	if cache and cache[key] then
		cache[key]:Stop(fade or 0.1)
	end
end

local function horizontalSpeed(character)
	local hrp = character:FindFirstChild("HumanoidRootPart")
	if not hrp then
		return 0
	end
	local v = hrp.AssemblyLinearVelocity
	return Vector3.new(v.X, 0, v.Z).Magnitude
end

-- visual enter / exit (any character) -------------------------------------------------

function Stance.isActive(character)
	local s = states[character]
	return s ~= nil and (s.phase == "enter" or s.phase == "hold")
end

function Stance.enter(character)
	local s = stateOf(character)
	if s.phase == "enter" or s.phase == "hold" then
		return
	end
	if usesTracks() then
		if not isLocal(character) then
			return -- the owner's tracks replicate to us
		end
		stopTrack(character, "StanceExit", 0.05)
		playTrack(character, "StanceEnter", 0.05)
	end
	s.phase, s.t, s.mt, s.blend, s.trackMoving = "enter", 0, 0, 0, false
	s.endsAt = os.clock() + Config.Stance.EnterTime
end

function Stance.exit(character)
	local s = stateOf(character)
	if s.phase == "off" or s.phase == "exit" then
		return
	end
	if usesTracks() then
		if not isLocal(character) then
			s.phase = "off"
			return
		end
		stopTrack(character, "StanceEnter", 0.05)
		stopTrack(character, "StanceIdle", 0.1)
		stopTrack(character, "StanceMove", 0.1)
		playTrack(character, "StanceExit", 0.1)
	end
	s.phase, s.t = "exit", 0
	s.endsAt = os.clock() + Config.Stance.ExitTime
end

-- local player actions ----------------------------------------------------------------

local function tell(on)
	if request then
		request:FireServer("Stance", { on = on })
	end
end

local function setActive(character, on)
	if on then
		Stance.enter(character)
	else
		Stance.exit(character)
	end
	tell(on)
end

-- Call on every local combat action (attack, block, dodge): enters the stance if enabled
-- and restarts the relax timer.
function Stance.engage()
	local character = localPlayer and localPlayer.Character
	if not character or not Config.Stance.Enabled then
		return
	end
	local s = stateOf(character)
	s.lastAction = os.clock()
	if Config.Stance.AutoEnter and (s.phase == "off" or s.phase == "exit") then
		setActive(character, true)
	end
end

-- Call when something happens that should keep the stance alive without entering it (getting hit).
function Stance.bump()
	local character = localPlayer and localPlayer.Character
	if character then
		stateOf(character).lastAction = os.clock()
	end
end

-- Toggle key: hold the stance until toggled off.
function Stance.toggle()
	local character = localPlayer and localPlayer.Character
	if not character or not Config.Stance.Enabled then
		return
	end
	local s = stateOf(character)
	if Stance.isActive(character) then
		s.locked = false
		setActive(character, false)
	else
		s.locked = true
		s.lastAction = os.clock()
		setActive(character, true)
	end
end

-- Sprinting (or anything else that should end the stance outright).
function Stance.dismiss()
	local character = localPlayer and localPlayer.Character
	if not character then
		return
	end
	local s = stateOf(character)
	s.locked = false
	if Stance.isActive(character) then
		setActive(character, false)
	end
end

-- per-frame -------------------------------------------------------------------------------

local function stepProcedural(character, s, dt)
	local rot
	if s.phase == "enter" then
		local anim = Data.STANCE_ENTER
		s.t += dt
		rot = sample(anim, s.t)
		if s.t >= anim.duration then
			s.phase, s.t = "hold", 0
		end
	elseif s.phase == "hold" then
		local idleAnim, moveAnim = Data.STANCE_IDLE, Data.STANCE_MOVE
		s.t = (s.t + dt) % idleAnim.duration
		local target = horizontalSpeed(character) > Config.Stance.MoveSpeedThreshold and 1 or 0
		s.blend += (target - s.blend) * (1 - math.exp(-Config.Stance.BlendSpeed * dt))
		rot = sample(idleAnim, s.t)
		if s.blend > 0.001 then
			s.mt = (s.mt + dt) % moveAnim.duration
			local move = sample(moveAnim, s.mt)
			for _, joint in ipairs(UPPER) do
				rot[joint] = rot[joint]:Lerp(move[joint], s.blend)
			end
			for _, joint in ipairs(HIPS) do
				rot[joint] = rot[joint]:Lerp(IDENTITY, s.blend) -- legs belong to the walk animation
			end
		end
	else -- exit
		local anim = Data.STANCE_EXIT
		s.t += dt
		rot = sample(anim, s.t)
		if s.t >= anim.duration then
			s.phase = "off"
			Poses.setBase(character, nil)
			if not Poses.isBusy(character) then
				Poses.release(character)
			end
			return
		end
	end

	local keyed = toMotorKeys(rot)
	-- Attacks recover toward wherever the stance currently is, so keep the base current.
	Poses.setBase(character, keyed)
	if not Poses.isBusy(character) then
		Poses.applyRotations(character, keyed)
	end
end

local function stepTracks(character, s)
	local now = os.clock()
	if s.phase == "enter" then
		if now >= s.endsAt then
			s.phase = "hold"
			stopTrack(character, "StanceEnter", 0.1)
			playTrack(character, "StanceIdle", 0.1)
		end
	elseif s.phase == "hold" then
		local moving = horizontalSpeed(character) > Config.Stance.MoveSpeedThreshold
		if moving ~= s.trackMoving then
			s.trackMoving = moving
			if moving then
				stopTrack(character, "StanceIdle", 0.15)
				playTrack(character, "StanceMove", 0.15)
			else
				stopTrack(character, "StanceMove", 0.15)
				playTrack(character, "StanceIdle", 0.15)
			end
		end
	elseif s.phase == "exit" then
		if now >= s.endsAt then
			s.phase = "off"
			stopTrack(character, "StanceExit", 0.1)
		end
	end
end

local function stepCharacter(character, s, dt)
	if isLocal(character) and s.phase == "hold" and not s.locked then
		if character:GetAttribute("Blocking") == true then
			s.lastAction = os.clock()
		elseif os.clock() - s.lastAction > Config.Stance.ExitDelay then
			setActive(character, false)
		end
	end
	if usesTracks() then
		if isLocal(character) then
			stepTracks(character, s)
		end
	else
		stepProcedural(character, s, dt)
	end
end

function Stance.step(dt)
	for character, s in pairs(states) do
		if s.phase ~= "off" then
			if character.Parent == nil then
				states[character] = nil
			else
				stepCharacter(character, s, dt)
			end
		end
	end
end

-- other players ---------------------------------------------------------------------------------

local function watchCharacter(character)
	if isLocal(character) then
		return -- the local player drives their own stance directly
	end
	local function sync()
		local want = character:GetAttribute("InStance") == true
		if want and not Stance.isActive(character) then
			Stance.enter(character)
		elseif not want and Stance.isActive(character) then
			Stance.exit(character)
		end
	end
	character:GetAttributeChangedSignal("InStance"):Connect(sync)
	sync()
end

local function watchPlayer(player)
	if player == localPlayer then
		return
	end
	player.CharacterAdded:Connect(watchCharacter)
	if player.Character then
		watchCharacter(player.Character)
	end
end

function Stance.init(remote)
	request = remote
	RunService.RenderStepped:Connect(Stance.step)
	for _, player in ipairs(Players:GetPlayers()) do
		watchPlayer(player)
	end
	Players.PlayerAdded:Connect(watchPlayer)
end

return Stance
