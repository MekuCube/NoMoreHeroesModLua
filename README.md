# Integrating Lua modding support into No More Heroes 1 + 2.

![nmh](https://user-images.githubusercontent.com/42222519/124152059-78671000-da93-11eb-81ec-78e49c51a886.gif)

A work-in-progress.

## Complete
* Execute Lua in NMH2
* Read/write to NMH2 variables
* Execute functions (static / overloaded / object instance)
* Documentation via json
* Extending classes via json
* Loading multiple Lua scripts

## In progress:
* Common iterators (mHRChara / items / etc)
  * Currently has mHRChara iterator

## Not started:
* Hook on game startup
* Sharing C and Lua namespaces
* Hook game events
* Subclass game classes

# Known issues
* Some function calls are unstable and result in crashing.
  * This is looks to be primarily an issue for functions taking parameters
