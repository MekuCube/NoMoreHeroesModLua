#include "pch.h"
#include <iostream>
#include "framework.h"
#include <vector>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <filesystem>
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
    std::cout << "Init...\n";

    bool bIsActive = true;

#if WITH_LUA
    lua_State* L = luaL_newstate();
    luaL_openlibs(L);

    luabridge::Namespace GlobalNS = luabridge::getGlobalNamespace(L);
    BindLua_Exported(GlobalNS);

    luabridge::push(L, GetTravis());
    lua_setglobal(L, "Travis");
#endif
    std::cout << "It's kill or be killed.\n";

    while (true)
    {
        double DeltaTime = 1.0 / 1000.0;
        luabridge::push(L, DeltaTime);
        lua_setglobal(L, "DeltaTime");

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
            for (const std::filesystem::directory_entry &el : std::filesystem::recursive_directory_iterator("D:/Steam/steamapps/common/No More Heroes 2 Desperate Struggle/Mods/", std::filesystem::directory_options::skip_permission_denied))
            {
                if (el.is_directory()) continue;
                if (!el.path().has_extension()) continue;
                if (el.path().extension() != ".lua") continue;
                std::string FilePath = el.path().string();
                char const* FilePathC = FilePath.c_str();
                if (!CheckLua(L, luaL_dofile(L, FilePathC)))
                {
                    Sleep(5000);
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