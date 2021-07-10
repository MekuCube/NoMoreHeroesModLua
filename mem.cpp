#include "pch.h"
#include "mem.h"

void mem::Patch(BYTE* dst, BYTE* src, unsigned int size)
{
	DWORD oldprotect;
	VirtualProtect(dst, size, PAGE_EXECUTE_READWRITE, &oldprotect);

	memcpy(dst, src, size);
	VirtualProtect(dst, size, oldprotect, &oldprotect);
}

DWORD mem::HookFunc(BYTE* targetFunc, BYTE* OurFunc, unsigned int size)
{
	if (size < 5)
		return NULL;

	DWORD oldprotect;
	VirtualProtect(targetFunc, size, PAGE_EXECUTE_READWRITE, &oldprotect);

	memset(targetFunc, 0x90, size); // Nop
	
	DWORD relativeAddress = ((DWORD)OurFunc - (DWORD)targetFunc) - 5;

	*targetFunc = 0xE9;
	*(DWORD*)((DWORD)targetFunc + 1) = relativeAddress;

	VirtualProtect(targetFunc, size, oldprotect, &oldprotect);

	return (DWORD)((BYTE*)targetFunc + size);
}

BYTE* mem::TrampHook(BYTE* targetFunc, BYTE* OurFunc, unsigned int size)
{
	if (size < 5)
		return nullptr;

	// Create Gateway
	unsigned int GatewaySize = size + 5;
	BYTE* gateway = (BYTE*)VirtualAlloc(0, GatewaySize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
	if (gateway == nullptr)
		return nullptr;

	// Debug: NOP
	memset(gateway, 0x90, GatewaySize);

	// Write the stolen bytes to the gateway
	memcpy_s(gateway, size, targetFunc, size);

	// Get the gateway to destination address
	uintptr_t gatewayRelativeAddr = targetFunc - gateway - 5;

	// add the jmp opcode to the end of the gateway
	*(gateway + size) = 0xE9;

	// Write the address of the gateway to the jmp
	*(uintptr_t*)((uintptr_t)gateway + size + 1) = gatewayRelativeAddr;

	// Perform the detour
	mem::HookFunc(targetFunc, OurFunc, size);

	return gateway;
}

void mem::Nop(BYTE* dst, unsigned int size)
{
	DWORD oldprotect;
	VirtualProtect(dst, size, PAGE_EXECUTE_READWRITE, &oldprotect);
	memset(dst, 0x90, size);
	VirtualProtect(dst, size, oldprotect, &oldprotect);
}

uintptr_t mem::FindDMAAddy(uintptr_t ptr, std::vector<unsigned int> offsets)
{
	uintptr_t addr = ptr;
	for (unsigned int i = 0; i < offsets.size(); ++i)
	{
		addr = *(uintptr_t*)addr;
		addr += offsets[i];
	}
	return addr;
}