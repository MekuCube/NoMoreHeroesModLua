#include "pch.h"
#include <iostream>
#include "framework.h"
#include <vector>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <d3d11.h>
#include "mem.h"
#include "Games/gamedefs.h"

#if WITH_LUA
extern "C"
{
    #include "Lua/lua.h"
    #include "Lua/lauxlib.h"
    #include "Lua/lualib.h"
}
#include "LuaBridge/LuaBridge.h"
#include "LuaBridge/Vector.h"

#ifdef _WIN32
#pragma comment(lib, "lua/lua54.lib")
#endif
#endif

uintptr_t GameModule = NULL;

#ifdef GAME_NMH2
    #include "Games/NMH2/exported_data_types.h"
    #include "Games/NMH2/nmh2_gamedefs.h"
    #include "GameFunctions.h"
#else
    #error "No game specified."
#endif

#if WITH_LUA
bool CheckLua(lua_State* L, int r)
{
    if (r != LUA_OK)
    {
        std::cout << "[Lua] " << lua_tostring(L, -1) << std::endl;
        return false;
    }
    return true;
}
#endif

DWORD WINAPI HackThread(HMODULE hModule)
{
    //Create Console
    AllocConsole();
    FILE* f;
    freopen_s(&f, "CONOUT$", "w", stdout);

#if GAME_NMH2
    GameModule = (uintptr_t)GetModuleHandle(L"nmh2.exe");
#endif

    std::cout << std::setprecision(2) << std::fixed;
    std::cout << "It's kill or be killed.\n";

    bool bIsActive = true;

    lua_State* L = luaL_newstate();
    luaL_openlibs(L);

    luabridge::Namespace GlobalNS = luabridge::getGlobalNamespace(L);
    BindLua_Exported(GlobalNS);

    luabridge::push(L, GetTravis());
    lua_setglobal(L, "Travis");

    while (true)
    {
        if (GetAsyncKeyState(VK_END) & 1)
        {
            bIsActive = !bIsActive;

            if (bIsActive)
                std::cout << "Modding: ON" << std::endl;
            else
                std::cout << "Modding: OFF" << std::endl;
        }

        if (bIsActive)
        {
#if WITH_LUA
            std::ifstream t("E:/Downloads/Script.lua");
            if (t.good())
            {
                std::stringstream buffer;
                buffer << t.rdbuf();

                if (!CheckLua(L, luaL_dostring(L, buffer.str().c_str())))
                {
                    Sleep(500);
                    continue;
                }
            }
#endif
        }
        Sleep(5);
    }

    fclose(f);
    FreeConsole();
    FreeLibraryAndExitThread(hModule, 0);
    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule,
    DWORD  ul_reason_for_call,
    LPVOID lpReserved
)
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        CloseHandle(CreateThread(nullptr, 0, (LPTHREAD_START_ROUTINE)HackThread, hModule, 0, nullptr));
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}