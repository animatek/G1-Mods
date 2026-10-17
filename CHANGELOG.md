# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-17

- Claude: **type 101, Mux8-1** (`dsp/mux8.asm`): the G2's Mux8-1 and Sw8-1 in one type, In 1–8,
  Ctrl, Out, a Sel knob that Ctrl adds to (8 units a step) and eight LEDs. **Found: the G1 has
  128 types and only nine are left free** (6, 41, 42, 55, 56, 60, 93, 109, 116); 127 is Clavia's
  PolyAreaIn and 128 does not exist. `FREE_TYPES` in `patch_rom.py`, which refuses any other;
  `PORTING.md` says how to spend them. NME `g1-mods` `c7980d6`, `60c29ca` (its mods test knew only
  119 and above). New `tests/check_mux8.py` passes; all tests pass.

- Claude: **type 126, 8Counter** (`dsp/counter8.asm`), the G2's: Clk, Rst (as the 5-Step Seq's,
  so it keeps in step with the G1's sequencers), eight outputs, one high a step, and eight step
  LEDs. NME data in "Logic (mods)" (NME `g1-mods` `0fdcd0c`). New `tests/check_counter8.py` (every
  sample against a model of the counter, Rst included, and the step LEDs) passes; all tests pass.

- Claude: **type 125, Scale Quantizer** (`dsp/quant.asm`, Javier's idea, after JW-Modules'
  Quantizer): In, Out, Root (C..B), Scale (16 by name) and Octave (−4..+4). A table per scale
  written by the Scale routine (`write_table_routine`, `Param(table=)`). Found on the way: 0 at a
  pitch input is an E, and n2 is not free between modules. NME data in "Control (mods)" (NME
  `g1-mods` `3f849f8`). New `tests/check_quant.py` (every scale, sample by sample) passes;
  `check_nme_data.py` checks the scale names; `check_turing.py` reads only whole Meters messages
  (the PC Port log cut one once). All tests pass.

- Claude: **the Turing Machine grows** (Javier): eight gate outputs, bits 0–7 while Clk is high
  (the Gate output goes: it was gate 1), a Scale knob for CV, and eight LEDs with the register's
  low byte, through the meter (`bits_routine`, `control_type`'s `bits`; NME `g1-mods` `led-array`
  with `bits="true"`). Height 5. `tests/check_turing.py` now also checks gates 1, 4 and 8, Scale
  64 and the byte in the Meters messages; all tests pass.

- Claude: **a meter carries 14 bits**, read in the OS's meter poll and sender (`NOTES.md`): the
  value routine's word goes out as two 7-bit values, so the Turing Machine's 8 LEDs fit in one
  module's meter. `PORTING.md`: a Mutator inside the synth, as an idea (the G1's morph already
  interpolates).

- Claude: **the Turing Machine's Prob is bipolar**, as the original's big knob (Javier: a 0..127
  knob locked at both ends confused): centre random, right locked, left the pattern inverted each
  pass; NME draws it from the centre (`value-64`, default 64). `tests/check_turing.py` updated
  and passing. `PORTING.md`: a bigger Turing Machine with the expander's outputs, as an idea.

## 2026-10-16

- Claude: **type 124, Turing Machine** (`dsp/turing.asm`), after Music Thing Modular's: Clk in,
  CV (the register's low byte as a level) and Gate (bit 0 while Clk is high) out, Prob, Length
  1–16 and Lock. Built with `control_type`; NME data in "Sequencer (mods)" (NME `g1-mods`
  `7f91264`). New `tests/check_turing.py` (repeats every Length with Prob 0 or Lock, inverted at
  the top, drifting at 64, the Gate) passes, and every other test; `check_insert.py` plays it
  too. Without its 8 LEDs yet.

- Claude: **the 5-Step Seq's Rst works as the G1's sequencers'** (Javier: the sequencers would
  not sync). Measured against a CtrlSeq on the same clock and reset: Clavia's Rst arms the
  sequencer and the next clock goes to the first step, and it starts on the last step; ours
  jumped to the first at the Rst edge, a step ahead. Now the same. `tests/check_seq5.py` plays
  both (`tests/seq5-ctrlseq.pch`, Rst between clocks) and they stay on the same step; all tests
  pass. `PORTING.md`: G2 patches on a G1, as an idea.

- Claude: **type 123, 5-Step Seq** (`dsp/seq5.asm`): Clk, Rst, Out and five bipolar knobs
  (−64…+63), after Buchla's five-stage sequencers, with a row of five step LEDs (a led-array on
  the OS's meter list, `$1169BA`, as the CtrlSeq's; `value_routine` and `connection_routine`'s
  `meter`). Built with `control_type`. NME data in "Sequencer (mods)". New `tests/check_seq5.py`
  (order, Rst, a knob live, the step LEDs) passes, and every other test with it;
  `check_insert.py` plays it too.

- Claude: **a control type is described once** (`control_type` and `Param` in `patch_rom.py`):
  DSP file, X words, parameters and LED, and the counts, parameter table and routines, `+$08`,
  connection routine and descriptor derived from them, instead of fields copied from a donor and
  fixed by hand (where the day's three bugs came from). The FlipFlop and the Noise S&H use it.
  New `tests/check_nme_data.py` (the OS and NME agree on each type's parameters, widths, inputs
  and outputs; it catches a changed maximum) and `tests/run_all.py`. All tests pass.

- Claude: **fixed patches breaking when a module was added live** next to a Noise S&H (Javier: the
  oscillators stopped, only clicks). The descriptor's word at `+$24` is the size of the module's
  record in the OS's RAM; the Noise S&H had CompareAB's (no parameters) with two, so the next
  record was written over its parameters. Now every type's is computed from its parameters.
  `tests/check_insert.py` (a FilterE added live to each test patch) passes, and so do the others.
  Found with G1-Emu's new `--add-module-at`, `G1_WATCH_PC` and `G1_RAMDUMP`. `NOTES.md`: a module's
  record.
- Claude: **fixed the Noise S&H's knobs doing nothing when turned** (Javier): before a live change
  the OS asks the type's `+$08`, and CompareAB's left `d0` as it was; now ClkDiv's (`clr.b d0`).
  Both tests gain a live case with G1-Emu's new `--param-at` (Range 1 → 5 octaves, Bi → Uni;
  FlipFlop D → RS) and pass. `NOTES.md`: how a parameter reaches the DSP live. `PORTING.md`: a
  Scope, as an idea.
- Claude: the Noise S&H's panel in NME gets a knob for Range next to its display (Javier: the
  display alone could not be changed). NME `g1-mods`.
- Claude: **Noise S&H gets Range (1–5 octaves) and Uni/Bi**, with parameter routines of our own
  (`param_routines`, `write_x_routine`); a semitone measured as one control unit at a pitch input.
  `tests/check_noise_sh.py` checks 1 and 5 octaves Bi and 3 Uni (spans, mirror, edges) and passes;
  so do the FlipFlop's and the Mix1-1A's. NME `g1-mods`: a display for Range and a button for
  Bi/Uni.
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
