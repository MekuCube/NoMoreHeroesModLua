if TimeWithoutAttacking == nil then
	TimeWithoutAttacking = 0
end
if Travis:mCheckAttack() > 0 then
	TimeWithoutAttacking = 0
else
	TimeWithoutAttacking = TimeWithoutAttacking + DeltaTime
end

local TimeToSprint = 0.2
WasSprinting = IsSprinting
IsSprinting = TimeWithoutAttacking >= TimeToSprint and (Gamepad:GetLStick():SizeSquared() > 0 or Gamepad:GetRStick():SizeSquared() > 0) and Gamepad:IsPressingRB()

if IsSprinting == true and WasSprinting == false then
	print("Sprint start")
	ShowMessage("Sprinting!", true)
	Travis:CreateGuardBreakEffect()
	Travis.mStatus.motSpd = 2
end

if IsSprinting == false and WasSprinting == true then
	print("Sprint stop")
	Travis:CreateGuardBreakEffect()
	Travis.mStatus.motSpd = 1
end

if IsSprinting then
	if SweatEffect == nil then
		SweatEffect = 0
	else
		SweatEffect = SweatEffect + DeltaTime
		if SweatEffect > 0.5 then
			SweatEffect = 0
			Travis:CreateGuardBreakEffect()
		end
	end
	Travis:CreateFootSmokeEffect()
	Travis.mStatus.motSpd = 2
end