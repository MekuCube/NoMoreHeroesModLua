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