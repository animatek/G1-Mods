# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-16

- Claude: repo created, apart from G1-Emu so the emulator stays Clavia's OS untouched
  (`CLAUDE.md`: the rules). `NOTES.md`, "Module types in the OS", moved here from G1-Emu before
  it was pushed: one 48-byte entry per type at `$1C3B00`, filled by a registration routine per
  type; the counts of parameters, inputs and outputs; the DSP descriptor with the module's code;
  18 free type numbers. `tools/patch_rom.py` applies an experiment to a copy of the user's ROM;
  the first, `mixer3-silent`, gives the same ROM as the hand-made one the battery found silent
  (checked with `cmp`). `git status` shows no ROM.
