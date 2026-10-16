# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-16

- Claude: **the first new module type works.** `tools/patch_rom.py type119-mixinv` registers a
  type 119 (the Mixer (3) with input 1 inverted) with a hand-assembled routine hooked to the end of
  the registration list; `tools/make_modules_xml.py` writes a `modules.xml` with it for NME and the
  test bench. Checked in G1-Emu: the OS registers it (RAM dump), the battery measures it at
  −61.8 dBFS against −52.3 for the Mixer (3) (−9.54 dB predicted), and the original ROM refuses
  the same patch. `NOTES.md`, "The first new type: 119".
- Claude: `NOTES.md`, "The registration list": the boot routine that empties the 128 entries,
  the list of 110 `jsr` at `$10DC90` (ROM `$1A490`) with the type each one registers, what
  `$10DC42` does, and the ~15 KB the OS leaves untouched at the end of its RAM image
  (`$16FB7F`–`$1737FF`) for code of ours. Types 63, 65 and 77 are registered after all (the
  earlier note was wrong). Plan for the first new type. Checked by walking the list in the ROM and
  comparing a RAM dump after boot with the ROM.
- Claude: repo created, apart from G1-Emu so the emulator stays Clavia's OS untouched
  (`CLAUDE.md`: the rules). `NOTES.md`, "Module types in the OS", moved here from G1-Emu before
  it was pushed: one 48-byte entry per type at `$1C3B00`, filled by a registration routine per
  type; the counts of parameters, inputs and outputs; the DSP descriptor with the module's code;
  18 free type numbers. `tools/patch_rom.py` applies an experiment to a copy of the user's ROM;
  the first, `mixer3-silent`, gives the same ROM as the hand-made one the battery found silent
  (checked with `cmp`). `git status` shows no ROM.
