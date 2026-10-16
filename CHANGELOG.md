# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-16

- Claude: **type 122, Noise S&H** (our own: a sample and hold with its own noise, Out and Inv),
  `dsp/noise_sh.asm` on CompareAB. `tests/check_noise_sh.py` passes (Out changes on every edge and
  only there, 285 values of both signs in 288 edges, Inv its negation); the FlipFlop's and the
  Mix1-1A's tests still pass. NME's `g1-mods` branch has it, and now the Patch Mutator too
  (`mutator-g2` merged in, NME `b24fe26`).
- Claude: **the FlipFlop lights Q's LED**: a value routine reading Q through the DSP's host port,
  registered with `$116832` (the OS keeps one LED per module). `tests/check_flipflop.py` gains a
  sixth case (LED 0 on and off in the Lights messages, logged with G1-Emu's new
  `G1_PCPORT_LOG`); all pass. `make_nme_data.py`: the FlipFlop's panel laid out like the G2's, with
  the LED. `NOTES.md`: plain LEDs.
- Claude: **fixed the FlipFlop's NotQ sharing a word with the next module's output** (Javier: on
  the G2 demo the two outputs alternate; here one gave fast triggers unrelated to the clock). The
  descriptor's output count (`+$08`) was ClkDiv's 1; now 2. `tests/check_flipflop.py` has a fifth
  case, a Constant right after the FlipFlop, which stays constant now and changed with NotQ before.
  All cases pass, and the Mix1-1A's test too.
- Claude: **fixed the modified OS hanging on its second boot.** The package crossed `$70000` in
  the flash, where the patch banks start and which the OS formats on its first boot, erasing the
  registration routine. Now it is stored at `$166574`, inside the OS's sectors, and a bootstrap
  copies it to `$170000` at boot. Checked: three boots on the same flash, the old hanging flash,
  both module tests, and a replayed 2 MB NME session (package intact). `NOTES.md` corrected.
- Claude: with a fresh flash the G1-Emu window boots the G1-Mods ROM (checked by Javier), so the
  blank display came from the old `out/flash-all.bin` (kept aside). Noted in `NOTES.md` as an open
  problem to solve before a real G1.
- Claude: `patch_rom.py` writes the ROM under a temporary name and renames it, so an emulator
  starting while a test rebuilds it never reads half a ROM; `dspasm.py` keeps each source's
  assembled words in `out/` (keyed by its text), so a build without code changes does not load
  the index. Checked: the same ROM with and without the cache. Done while chasing a G1-Emu window
  that showed a blank display with the G1-Mods ROM (that ROM boots in `g1boot` and `g1patchtest`;
  the window's flash, `out/flash-all.bin`, was set aside to try a fresh one).
- Claude: **the FlipFlop is complete** (the G2's: D/RS Type, Clk, In, Rst, Q, NotQ), with DSP code
  written in assembly (`dsp/flipflop.asm`) and a small assembler (`tools/dspasm.py`) that finds
  encodings in an index of G1-Emu's disassembler. ClkDiv is the donor; the Type is written to X by
  a routine of ours; the connection routine is generated from the code's marks.
  `tests/check_flipflop.py` checks four cases (D, toggle, reset, set) and passes; so does
  `check_mix1_1a.py`. `make_nme_data.py` takes whole entries (the FlipFlop's). Also in `NOTES.md`:
  how a module's lights reach the editor (from the CtrlSeq), and the plan to flash a real G1;
  in `PORTING.md`: G1 and G2 sequencers compared, and new modules of our own (Noise S&H, 5-step
  sequencer, small reverb, Turing Machine). `tools/__pycache__` out of Git.
- Claude: `PORTING.md`, the porting checklist: every G2-only module and the G2 versions that do
  more than the G1's, with their DSP size in the demo, whether a real G1 can run them (the limit:
  each DSP has 4K program and 2K+2K data words, no external RAM, so long delays and the reverb
  are emulator-only) and their status; and the order proposed.
- Claude: `make_nme_data.py` puts each new type in "<donor's family> (mods)" ("Mixer (mods)",
  "Logic (mods)"), which NME's `g1-mods` branch lists right after the family in the module bar,
  the browser and the right-click Add Module menu (NME `8d72735`).
- Claude: **Mix1-1A gets its Ch 1 button** (mutes the channel, not the chain): parameter 1 to Y[0],
  9-word code with its own connection routine, and a parameter table of its own (`Level` 127,
  `Ch 1` 1). Found why a first try hung the OS: a parameter's width comes from its maximum (NME's
  `modules.xml`, the OS's `+$1C` table) and the two disagreed. `tests/check_mix1_1a.py` now checks
  both buttons too; all pass, and so does the FlipFlop's. `make_nme_data.py` replaces a type it
  made before instead of skipping it. `NOTES.md`: the button, the widths, and what the Lin/dB/Exp
  curves need.
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
