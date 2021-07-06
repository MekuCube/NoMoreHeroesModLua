// Common types and functions used by NMH2

#pragma once

mHRPad* GetGamepad()
{
    return (mHRPad*)(GameModule + 0x9183a4);
}

mHRBattle* GetBattle()
{
    return (mHRBattle*)(GameModule + 0x9183A8);
}

CBgCtrl* GetBackgroundControl()
{
    return (CBgCtrl*)(GameModule + 0x915420);
}

HrMessage* GetHrMessage()
{
    return (HrMessage*)mem::FindDMAAddy(GameModule + 0x90f1b4, { 0x8, 0x0 });
}

mHRPc* GetTravis()
{
    return GetBattle()->mGetPcPtr();
}

HrScreenStatus* GetScreenStatus()
{
    return GetBattle()->mGetBtEffect() ? GetBattle()->mGetBtEffect()->pScreenStatus : nullptr;
}

mHRChara* GetEnemy()
{
    float* HP = (float*)mem::FindDMAAddy((uintptr_t)GetBattle(), { 0x1C8, 0x450, 0x20, 0x1DC, 0x24 });
    if (!HP)
        return nullptr;
    stCharaStatus* EnemyStatus = (stCharaStatus*)((char*)HP - 0x14);
    if (!EnemyStatus)
        return nullptr;
    return (mHRChara*)((char*)EnemyStatus - 0x10);
}

HrSysMessage* GetSysMessage()
{
    return (HrSysMessage*)(GameModule + 0x918d34);
}

HrTalk* GetHrTalk()
{
    return (HrTalk*)(GameModule + 0x918d2c);
}

HrBattleIcon* GetHrBattleIcon()
{
    return (HrBattleIcon*)(GameModule + 0x918d80);
}

std::vector<mHRChara*> GetAllCharacters()
{
    mHRPc* Travis = GetTravis();
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
    return (unsigned int*)mem::FindDMAAddy((uintptr_t)GetBattle(), { 0x190, 0x4, 0x8, 0x8, 0x5B0, 0x624 });
}