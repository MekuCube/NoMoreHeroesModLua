local Entries = {}
Entries[1] = "Destroy Resort"
Entries[2] = "Destroy University (Charlie)"
Entries[3] = "Destroy University (Kimmy)"
Entries[4] = "Deserted  House"
Entries[5] = "Prison Island"
Entries[6] = "Stadium"
Entries[7] = "Cliff"
Entries[8] = "Supermarket"
Entries[9] = "Highway"
Entries[10] = "Apartment House"
Entries[11] = "Pizza Bat HQ"
Entries[12] = "UAA Chapter 3"
Entries[13] = "UAA Chapter 7"
Entries[14] = "UAA Chapter 12"
Entries[15] = "Pizza Suplex"
Entries[28] = "Revenge Mission 1"
Entries[29] = "Revenge Mission 2"
Entries[30] = "Revenge Mission 3"
Entries[31] = "Revenge Mission 4"
Entries[32] = "Revenge Mission 5"
Entries[33] = "Revenge Mission 6"
Entries[34] = "Revenge Mission 7"
Entries[35] = "Revenge Mission 8"
Entries[36] = "Revenge Mission 9"
Entries[37] = "Revenge Mission 10"

if MapChangesApplied == nil and Gamepad:IsPressingX() then
	MapChangesApplied = 1
	
	local Menu = BackgroundControl:GetSkyMap().mpMenu
	local DefaultParam = Menu:GetListParam(0)
	
	for k, v in pairs(Entries) do
		local ParamIt = DefaultParam
		ParamIt:SetName(v)
		ParamIt.MapID = k
		BackgroundControl:GetSkyMap().mpMenu:SetListParam(Menu.ListItemNum, ParamIt)
		Menu.ListItemNum = Menu.ListItemNum + 1
	end
end