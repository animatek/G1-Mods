# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-16

- Claude: **type 121, Mix1-1A** (the G2's Mixer 1-1 A: one input with its level plus a chain
  input), on the Mixer (3)'s routines with code of our own and 1 parameter, 2 inputs, 1 output.
  `tests/check_mix1_1a.py`: same level as the Mixer (3) at 100, 64 and 0, +6.0 dB chained.
  `NOTES.md`: how a parameter reaches the DSP. `patch_rom.py` builds Mixer (3) variants with
  one function (`mixer3_variant`); `make_nme_data.py` can drop connectors and knobs.
- Claude: `tests/mixer-demo.pch`, the Mixer (3) and the Mixer Inv side by side on one oscillator:
  output 1 at −63.5 dBFS, output 2 silent (cancelled); with one input on the Mixer Inv it gives
  −69.5 dBFS, 6 dB under the sum. The two mixers work in one patch. Launchers for both apps in
  the maintainer's desktop (outside the repo), noted in `NOTES.md`.
- Claude: **type 120, a D flip-flop, works** (`NOTES.md`, "Type 120"): own DSP code and X data,
  CompareAB's entry with our descriptor and its connection routine patching the output at word
  17. `tests/check_flipflop.py` checks it in G1-Emu: Q changes 8 times for 8 crossings of D, each
  on a clock edge, and equals D at all 283 edges checked. `tools/patch_rom.py` rewritten: types
  are laid out from `$16FB80` and registered by one routine; experiment `all` (119 and 120).
  **Fixed** in type 119: the two nop-offset bytes after `+$24` were not copied (the next module
  of audio would have been placed 78 words away). `tools/make_nme_data.py` (replaces
  `make_modules_xml.py`) adds the types to NME's `modules.xml` and classic theme. `run-g1emu.sh`
  and `run-nme.sh` to try them by hand. `NOTES.md`, "How a module's data is loaded", from the
  loader.
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
