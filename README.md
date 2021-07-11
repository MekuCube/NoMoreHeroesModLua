# Integrating Lua modding support into No More Heroes 1 + 2.

![nmh](https://user-images.githubusercontent.com/42222519/124508418-2ba37200-ddd0-11eb-9fb5-204542c6d18c.gif)
![nmh](https://user-images.githubusercontent.com/42222519/124152059-78671000-da93-11eb-81ec-78e49c51a886.gif)

A work-in-progress.

## How to use
* Build as .DLL then inject into NMH.exe / NMH2.exe
* Currently injection has to be done manually, I use Cheat Engine
* Afterwards, the game will load all .lua files in the /Mods/ folder of the game's install folder (so SteamApps/Common/No More Heroes/Mods/)

## Included mods
I've included some sample mods by default in the /Mods/ folder.
**VisitAnyMap.lua**: Press X on the map screen in No More Heroes 2 to expand the menu to include every map in the game.
**SprintOutOfCombat.lua**: Hold RB while moving to sprint (when not in combat).

## Complete
* Execute Lua in NMH2
* Read/write to NMH2 variables
* Execute functions (static / overloaded / object instance)
* Documentation via json
* Extending classes via json
* Loading multiple Lua scripts
* Common iterators
  * AllCharacters / AllZako / AllCommonObj global lists
* Function hooks (pre-call hooks only)

## In progress:
* Function hooks (post-call hooks)

## Not started:
* Hook on game startup
* Sharing C and Lua namespaces
* Subclass game classes

# Known issues
* Some function calls / hooks are unstable and result in crashing.
