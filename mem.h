#pragma once
#include "pch.h"
#include <windows.h>
#include <vector>

// https://guidedhacking.com/threads/how-to-hack-any-game-tutorial-c-trainer-3-first-internal.12142/

namespace mem
{
	void Patch(BYTE* dst, BYTE* src, unsigned int size);
	void Nop(BYTE* dst, unsigned int size);
	DWORD HookFunc(BYTE* targetFunc, BYTE* OurFunc, unsigned int size);
	uintptr_t FindDMAAddy(uintptr_t ptr, std::vector<unsigned int> offsets);
	// Trampoline hook
	BYTE* TrampHook(BYTE* targetFunc, BYTE* OurFunc, unsigned int size);
}