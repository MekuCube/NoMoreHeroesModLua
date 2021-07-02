// Common types and functions used by NMH2

#pragma once

mHRPc* GetTravis()
{
    float* PosX = (float*)mem::FindDMAAddy(GameModule + 0x8EA1BC, { 0x38 });
    stCharaStatus* TravisStatus = (stCharaStatus*)((char*)PosX - 0x28);
    return (mHRPc*)((char*)TravisStatus - 0x10);
}
unsigned int* GetMoneyPtr()
{
    return (unsigned int*)mem::FindDMAAddy(GameModule + 0x9183A8, { 0x190, 0x4, 0x8, 0x8, 0x5B0, 0x624 });
}