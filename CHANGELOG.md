# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-19

- Claude: NOTES, flashing a real G1: **Shift + Store at power-on enters the MIDI update mode**,
  confirmed by Javier on his G1, so a bad OS of ours has a way back; and Shift + Patch/Load
  boots the ROM's factory OS (tried too): two ways back from a bad OS.
- Claude: NOTES, **an OS update keeps the patch banks** in G1-Emu: Clavia's 3.03b updater over a
  flash with the factory OS, then a plain restart; the banks' bytes compared with a copy taken
  before, unchanged.
- Claude: NOTES, **Clavia's 3.03b flashed over itself on Javier's real G1**: the whole procedure
  (Shift + Store, Safe (Slower), the G1's own Store to confirm), as the rehearsal before an OS of
  ours.
- Claude: NOTES, **a MIDI Out module as the G2's** (idea): how the G2's NoteSend works (a DSP
  mailbox the CPU polls). Then read in the G1's OS: the MIDI-out sender and its queues, the
  keyboard model's unused note senders, and why the lights' poll does not do for notes (active
  slot only, with an editor); the plan, a poll of our own from the main loop. Testing is ready:
  G1-Emu's plugin now has the MIDI OUT as its MIDI output (G1-Emu PR #79).

## 2026-10-18

- Claude: **a README**: what G1-Mods is and how it works, the twelve modules, the layout, how to
  try it, who is responsible for what, firmware and rights, licence (GPLv3, the `LICENSE` file
  added, as G1-Emu's) and credits (Gearmulator), from PORTING's notices agreed with Javier on
  2026-10-17. On GitHub as `animatek/G1-Mods`, private for now.

- Claude: **the mark**: every build with modules says version 3.09 in its IAm instead of 3.03
  (`VERSION_MARK`, one `move.b` at `$10B288`), so NME tells it apart synth by synth on
  connecting (after Javier: with several synths, a Clavia OS sits next to a modified one).
  Clavia's editor 3.03 still connects to it (it takes 3.00-3.09). NOTES.md, "The mark". Checked:
  `tests/check_mark.py` boots both in G1-Emu (3.03 and 3.09, NME looking for 9); the `all` ROM
  differs from before in that byte only.

- Claude: **NME's layer**: `tools/make_nme_data.py --layer <NME's data>` writes
  `mods-modules.xml` and `mods-theme.xml`, the modules alone, which NME's `mods-layer` branch
  loads on top of Clavia's files and offers only to a synth ticked "OS with G1-Mods modules" in
  MIDI Setup (per synth, after Javier: with several synths, a Clavia OS sits next to a modified one).
  `tests/check_nme_data.py` now checks that layer as it is on disk (and that it is not stale),
  and that NME's ParameterEncoder has no case of its own for the types (their widths come from
  data). `run-nme.sh` builds from `mods-layer`. Checked: `check_nme_data.py` passes, 12 types.

- Claude: **one folder per module** (`modules/<name>/`: `module.json`, `build.py`, its DSP code,
  NME's entries whole, its test and patches) and **a registry of types**
  (`modules/registry.json`), steps 1 and 2 of PORTING's "Next: opening it up". What every build
  uses moved to `tools/g1rom.py`; `patch_rom.py` reads the folders, and takes a list of them
  (`flipflop,mux8`) as well as an experiment; `make_nme_data.py` places each folder's entries
  (928 lines to 53; Mix1-1A's entry, cloned from the Mixer (3)'s, now written whole). Checked:
  the four ROMs (`all`, `stringtest`, `audiotest`, `mixer3-silent`) and NME's two files come out
  byte for byte as before, and `tests/run_all.py` passes in G1-Emu.

## 2026-10-17

- Claude: `PORTING.md`, open and free for good: nothing of the mods exclusive to Patreon or paid,
  Gearmulator credited everywhere (Javier).

- Claude: `PORTING.md`, "The builder and the catalogue": a Modwerk-like site building in the
  browser from the user's own OS, one C++ core (WebAssembly and NME), NME showing the mods only
  with a modified OS, and who is responsible for what: tested only on the emulator, each owner
  responsible for their G1, no hardware support, community modules in their authors' repos and
  linked after a review, with draft notices (agreed with Javier).

- Claude: `PORTING.md`, "Next: opening it up": a folder per module, a type registry, GitHub, the
  builder in NME (agreed with Javier).

- Claude: `PORTING.md`, the modules asked for after the first post, in one entry.

- Javier (Claude wrote it down): **the ROM with the package at `$1C6000` works**, played in
  G1-Emu.

- Claude: **more room for the package**: it runs from `$1C6000` (136 KB the OS never touches,
  found by replaying NME's 2.1 MB session with the RAM filled with a pattern) and is stored in
  both 19 KB runs of the OS image, copied by a 52-byte bootstrap: 38 KB in all, 24 KB left (was
  under 900 bytes). The 97 KB after the old room are OS buffers, not free. Checked: all tests
  pass; a ROM split over both runs by force plays bit for bit as the normal one. `NOTES.md`,
  "More room".

- Claude: `PORTING.md`, the Osc String next to the G2's (no pluck of its own, Cent and KBT): add
  Cent and KBT to ours, keeping Trig and Exc (Javier likes ours).

- Javier (Claude wrote it down): **the Osc String works**, played in G1-Emu.

- Claude: **type 56, Osc String** (`dsp/string.asm`), a plucked string (Karplus-Strong), the
  first audio-rate type: `audio_type` and `write_audio_x_routine` (checked first on a VCA, the
  `audiotest` experiment), a 1,024-word line the code clears itself, the period from Note and
  Pitch by a cubic and shifts, Damp's delay taken from it (`damp_routine`). NME `g1-mods`
  `93d31ca`. New `tests/check_string.py`: in tune within a cent from A1 to A5, from the keyboard,
  at any Damp; all tests pass. Under 900 bytes of room left; six free types.

- Claude: `PORTING.md`, the builder picks among the new modules only (Javier); swapping all the
  G1's modules for the G2's noted as not recommended, and why.

- Claude: `PORTING.md`, Javier's idea of an OS builder (pick the modules, a bar for the room
  left, build from the user's own OS), with the rules it needs.

- Claude: `NOTES.md`, starting the String: **only 2.3 KB of room for code are left** (the package
  runs from 14 KB the OS never touches; the eleven types take 12 KB), how the OS writes a
  parameter to a module's audio X (`$10C4B0` and `$10C248`), and the G1 Delay's memory as the
  measure of a string's buffer. `PORTING.md`: room for code as the second limit.

- Claude: **type 55, Envelope** (`dsp/env.asm`): the G2's ADDSR, H, D and AHD from one engine,
  Gate/Trig, Attack, Decay 1, Level 1, Decay 2, Sustain, Release, Env and End. NME `g1-mods`
  `8bee1f9`. New `tests/check_env.py` (levels, release time to a sample of the model, End, Trig)
  passes; all tests pass. Seven free types left.

- Claude: **type 42, Level** (`dsp/level.asm`): the G2's ModAmt, MinMax, T&H and WindSw in one
  module with a Mode selector, A, B, Out 1, Out 2, Amount, Lo and Hi. **The Random gets a Bi/Uni
  button** (Javier), its seventh parameter. NME `g1-mods` `fba49d5`. New `tests/check_level.py`
  (every sample of each mode) and a Uni case in `check_random.py` pass; all tests pass. Eight
  free types left.

- Claude: **type 41, Bits** (`dsp/bits.asm`): the G2's BinCounter, ADConv and DAConv in one module
  with a Mode selector (Count, A>D, D>A) and all their connectors, Out, eight bits and eight LEDs.
  NME data in "Logic (mods)" (NME `g1-mods` `3a23de3`). New `tests/check_bits.py` passes;
  `bits.pch` starts in D>A for `check_insert.py`. All tests pass. Nine free types left.

- Claude: `PORTING.md`, ideas from Javier's first tries: the Random's range and a Uni/Bi button
  to check, one NME and one G1-Emu that tell the modified OS by themselves, and the mods tabs
  under their family's.

- Javier (Claude wrote it down): **the Random's Poly works**, checked by ear in G1-Emu: each voice
  plays its own sequence.

- Claude: **type 6, Random** (`dsp/random.asm`): the G2's randoms in one clocked module, Clk, Rst,
  Out, Trig, with Seed, Poly (a seed per voice: the Seed routine gets the voice), Step, Edge,
  Prob and Length. NME data in "LFO (mods)" (NME `g1-mods` `5847ad1`). New
  `tests/check_random.py`: the values match a Python model of the module one by one; Length, Rst,
  Prob, Step and Edge checked; Poly by ear only. All tests pass. Ten free types left.

- Claude: `PORTING.md`: the plan for the free types, revised with Javier: the switches go into
  the Mux8-1's type and the G2 mixers into the Mix1-1A's, so four new types cover the small
  families and seven are left for big modules (oscillators, effects), one a type.

- Claude: **the Mixer Inv (119) and the Noise S&H (122) are out**, to free their types (Javier:
  the first was a test, the second is easy to patch with G1 modules). Their code, notes and tests
  stay in git history; `tests/mixer-demo.pch`, `noise-sh.pch` and `check_noise_sh.py` go.
  Eleven free types now. `PORTING.md` has the plan agreed with Javier: a type per family (Random,
  Switches, Conversion, Level, Envelopes, G2 mixers, one big oscillator and one effect, three kept
  back) and virtual modules in NME (one type, several panels), to do.

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
