local Entries = {}
Entries[1] = "Destroy Resort"
Entries[2] = "Destroy Uni (Charlie)"
Entries[3] = "Destroy Uni (Kimmy)"
Entries[4] = "Deserted  House"
Entries[5] = "Prison Island"
Entries[6] = "Destroy Stadium"
Entries[7] = "Cliff"
Entries[8] = "Supermarket Guan's"
Entries[9] = "Highway"
Entries[10] = "Apartment House"
Entries[11] = "Pizza Batt Tower"
Entries[12] = "UAA Chapter 3"
Entries[13] = "UAA Chapter 7"
Entries[14] = "UAA Chapter 12"
Entries[15] = "Burger Suplex"
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

if BackgroundControl:GetSkyMap() ~= nil then
	local Menu = BackgroundControl:GetSkyMap().mpMenu
	if Menu ~= nil and (MapChangesApplied == nil or MapChangesApplied ~= Menu.ListItemNum) and Gamepad:IsPressingX() then
		local DefaultParam = Menu:GetListParam(0)
		
		for k, v in pairs(Entries) do
			local ParamIt = DefaultParam
			ParamIt:SetName(v .. "  ")
			ParamIt.MapID = k
			BackgroundControl:GetSkyMap().mpMenu:SetListParam(Menu.ListItemNum, ParamIt)
			Menu.ListItemNum = Menu.ListItemNum + 1
		end
		MapChangesApplied = Menu.ListItemNum
	end
end