# Roadmap

What is wanted and not done. Nothing here works yet.

## An OS for G1-Emu alone, with more modules

A real G1's flash has room for 393,184 bytes of OS (`NOTES.md`, "The first real G1"), which limits how
many modules go in, and a few modules work only in G1-Emu for now. G1-Emu could run a bigger OS: more
modules than a G1 can hold, and an expanded memory map. That would be a second build, for the emulator
only, with its own file (a whole ROM, which is what G1-Emu boots).

Today the ROM the builder hands out is the same OS as the update image, in a whole ROM for G1-Emu (its
*Settings > ROM > Choose...*). A bigger OS would be a second, different build with its own file.

## The Micro Modular

G1-Mods builds on the **rack's 3.03 ROM**, and that is the only thing the builder takes. A Micro Modular
runs **its own OS**, a different binary on one DSP with other addresses, and there is no Micro ROM image to
rebuild: its OS comes out of Clavia's updater as an update image. So a G1-Mods OS does not exist for the
Micro: in G1-Emu's Micro model, or in the plugin's, the Micro's own OS runs and the modules are not there
(NME offers them only to a synth that says 3.09, which a Micro never does).

What it would take: a patcher that works on the Micro's OS image instead of a ROM (the hooks, the free
module types, the DSP room are all found again for that OS), and its own test in G1-Emu's Micro model before
anything goes near a real Micro. Not started.
