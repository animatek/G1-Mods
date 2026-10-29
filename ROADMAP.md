# Roadmap

What is wanted and not done. Nothing here works yet.

## An OS for G1-Emu alone, with more modules

A real G1's flash has room for 393,184 bytes of OS (`NOTES.md`, "The first real G1"), which limits how
many modules go in, and a few modules work only in G1-Emu for now. G1-Emu could run a bigger OS: more
modules than a G1 can hold, and an expanded memory map. That would be a second build, for the emulator
only, with its own file (a whole ROM, which is what G1-Emu boots).

Today it does not work in the emulator, so the web builder offers only the OS update, the one file that
G1-Emu (in update mode) and a real G1 both take through NME's *Device > Update Synth OS*. When this is
built, the ROM comes back to the builder as its own download, labelled for G1-Emu.
