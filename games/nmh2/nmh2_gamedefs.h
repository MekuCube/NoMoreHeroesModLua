// Common types and functions used by NMH2

#pragma once

mHRPc* GetTravis()
{
    float* PosX = (float*)mem::FindDMAAddy(GameModule + 0x8EA1BC, { 0x38 });
    stCharaStatus* TravisStatus = (stCharaStatus*)((char*)PosX - 0x28);
    return (mHRPc*)((char*)TravisStatus - 0x10);
}
mHRChara* GetEnemy()
{
    float* HP = (float*)mem::FindDMAAddy(GameModule + 0x9183A8, { 0x1C8, 0x450, 0x20, 0x1DC, 0x24 });
    if (!HP)
        return nullptr;
    stCharaStatus* EnemyStatus = (stCharaStatus*)((char*)HP - 0x14);
    if (!EnemyStatus)
        return nullptr;
    return (mHRChara*)((char*)EnemyStatus - 0x10);
}

std::vector<mHRChara*> GetAllCharacters()
{
    mHRChara* Travis = GetTravis();
    std::vector<mHRChara*> Result;
    if (Travis == nullptr)
        return Result;

    mHRChara* NextChara = (mHRChara*)Travis->mpNext;
    while (NextChara != nullptr)
    {
        if (NextChara != Travis)
            Result.push_back(NextChara);
        NextChara = (mHRChara*)NextChara->mpNext;
    }
    mHRChara* PrevChara = (mHRChara*)Travis->mpPrev;
    while (PrevChara != nullptr)
    {
        if (PrevChara != Travis)
            Result.push_back(PrevChara);
        PrevChara = (mHRChara*)PrevChara->mpPrev;
    }
    return Result;
}

unsigned int* GetMoneyPtr()
{
    return (unsigned int*)mem::FindDMAAddy(GameModule + 0x9183A8, { 0x190, 0x4, 0x8, 0x8, 0x5B0, 0x624 });
}