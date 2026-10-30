# Roadmap

What is wanted and not done, and what is done but not finished.

## An OS for G1-Emu alone, with more modules

A real G1's flash has room for 393,184 bytes of OS (`NOTES.md`, "The first real G1"), which limits how
many modules go in, and a few modules work only in G1-Emu for now. G1-Emu could run a bigger OS: more
modules than a G1 can hold, and an expanded memory map. That would be a second build, for the emulator
only, with its own file (a whole ROM, which is what G1-Emu boots).

Today the ROM the builder hands out is the same OS as the update image, in a whole ROM for G1-Emu (its
*Settings > ROM > Choose...*). A bigger OS would be a second, different build with its own file.

## Panel designer (idea, 2026-10-30)

A web tool (`tools/panel-designer/`, one HTML file) to lay a module's panel out by dragging: 255 px wide, rows of 15 px, a palette (knob, button, connector, label, number display, LED array, slider, Rnd/Clr), a properties panel, any existing module (ours or Clavia's) as a template, saved as the `nme-theme.xml` NME reads. Phase 1: open, move, resize, add, delete, save. Phase 2: a module from scratch (its connectors and parameters in `nme-modules.xml`; the DSP stays by hand). Phase 3, maybe: lines and decoration, which the theme format does not have (a change in NME's theme reader). The preview is an approximation of NME's drawing, not the same.

## CCOut (done 2026-10-30)

Type 122, CCOut (the G2's CtrlSend): a CC out of the MIDI OUT, with In, Send, Ctrl, Value and Chan. It shares the main loop's first call with Note Out: `Build.chain_call` chains any number of modules on one call. Tried in G1-Emu (`modules/ctrl-send/check_ctrl_send.py`); **not yet on a real G1**. PCSend (a program change) may follow as a mode of it.

## The Micro Modular

**Not offered publicly** (decided 2026-10-29): the web builder refuses a Micro OS (`MICRO_ENABLED = false` in `web/app.js`) and the README and guides do not mention it, because what a real Micro does with an OS update is unknown. The work below stays, for the emulator and the command line.

**Done, in the emulator, from the command line and in the web builder** (2026-10-29): `tools/patch_rom.py all <Micro updater or 3.03b OS image> out.bin`
puts twelve of the thirteen modules into the Micro's OS, and G1-Emu's Micro model boots it and plays their patches
(`tests/check_micro.py`; NOTES.md, "The Micro Modular"). To try it: G1-Emu's *Settings > Micro OS* takes that image.

Still to do, in order of how much it matters:
- **Someone with a real Micro**, and its updater for the way back, to try the update. Until then it is emulator-only.
- **Note Out on the Micro**: its two hooks in the OS main loop are not where the rack's are.
- **NME's side**: check that a Micro that says 3.09 is offered the modules.
