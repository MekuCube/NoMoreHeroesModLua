if Travis ~= nil and  Travis.mStatus ~= nil then
	print("Hello from lua! Travis is at: x=" .. Travis.mStatus.pos.x .. ", z=" .. Travis.mStatus.pos.z)
elseif Travis.mStatus == nil then
	print("Hello from lua! We can find Travis but not Travis.mStatus.")
else
	print("Can't find Travis")
end