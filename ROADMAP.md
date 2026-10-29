# Roadmap

What is wanted and not done, and what is done but not finished.

## An OS for G1-Emu alone, with more modules

A real G1's flash has room for 393,184 bytes of OS (`NOTES.md`, "The first real G1"), which limits how
many modules go in, and a few modules work only in G1-Emu for now. G1-Emu could run a bigger OS: more
modules than a G1 can hold, and an expanded memory map. That would be a second build, for the emulator
only, with its own file (a whole ROM, which is what G1-Emu boots).

Today the ROM the builder hands out is the same OS as the update image, in a whole ROM for G1-Emu (its
*Settings > ROM > Choose...*). A bigger OS would be a second, different build with its own file.

## The Micro Modular

**Done, in the emulator, from the command line and in the web builder** (2026-10-29): `tools/patch_rom.py all <Micro updater or 3.03b OS image> out.bin`
puts twelve of the thirteen modules into the Micro's OS, and G1-Emu's Micro model boots it and plays their patches
(`tests/check_micro.py`; NOTES.md, "The Micro Modular"). To try it: G1-Emu's *Settings > Micro OS* takes that image.

Still to do, in order of how much it matters:
- **Someone with a real Micro**, and its updater for the way back, to try the update. Until then it is emulator-only.
- **Note Out on the Micro**: its two hooks in the OS main loop are not where the rack's are.
- **NME's side**: check that a Micro that says 3.09 is offered the modules.
