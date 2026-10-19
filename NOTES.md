# Notes

What is known about how the G1 OS defines its modules. Addresses are hexadecimal (`$`); RAM
address X is at ROM offset `X − $100000 + $C800` (see `../G1-Emu/NOTES.md`, "The ROM").

## Module types in the OS (2026-10-16)

Read from a RAM dump after boot (`G1_RAMDUMP=file g1boot ROM 60`, in `../G1-Emu`).

- **One entry of 48 bytes per type at `$1C3B00 + type × $30`**, types 0–127, filled at boot by
  one registration routine per type. Type 25's, at `$131C3A` (RAM): `jsr $10DC42` with the type,
  then `+$00`–`+$10` five routines, `+$18`/`+$19`/`+$1A` the number of parameters, inputs and
  outputs (Mixer (3): 3/3/1, OscA: 10/5/2), `+$1C` the parameter names (what `g1knobs.h` reads),
  `+$20` a routine, and `+$24`, `+$28`, `+$2C` data. The loader's "per-type resource tables"
  (`$1C3B24`, `$1C3B28`) are `+$24` and `+$28` of type 0.
- **`+$28` is the DSP descriptor**: resource counts (the Mixer (3) has 8 P words, at `+$14`) and,
  `$4C` bytes in, **the DSP code itself**, one 24-bit word per long. `+$24` points to three
  pointers (X data, Y data, code) and three RAM variables. The code lives in the ROM's DSP area:
  RAM address X is at ROM `X − $100000 + $C800`.
- **The Mixer (3) is 8 instructions**: it reads its inputs through `r3`/`r4`, multiplies each by
  its level and accumulates, rounds and stores the result. Its `x:$0` operands are addresses
  the loader fills in, and the `nop` before the last instruction is where the next module is
  chained (the "NOP before the previous module's epilogue" of the loader).
- **Changing the code in the ROM changes the sound**: with the `macr` replaced by `clr a` (`tools/patch_rom.py mixer3-silent`) the battery finds the Mixer (3) silent; with the original
  ROM it sounds at −52 dBFS. The OS does not check a checksum that would stop it. An `asl a` in
  place of the `nop` gave +2.5 dB instead of +6: that slot is overwritten when modules are
  chained, so it is not ours to use.
- **Free type numbers**, never registered by the OS and unused in NME's `modules.xml`: 6, 41,
  42, 55, 56, 60, 93, 101, 109, 116, 119–126.
- The same conventions as the G2 (input pointers in `r3`/`r4`, addresses filled by the linker,
  the `nop` chaining slot): its 8Counter has the same shape. Clavia's code is studied, not
  copied: a module of ours is written new.

## The registration list (2026-10-16)

- **At boot `$10DBAE`** fills all 128 entries with the empty one (routines `$1198FE`…, names
  `$145DAA`, descriptors `$145D90`/`$145D50`/`$145DB6`), clears the "registered" byte of each
  type (`$1A7BC0 + type`), sets `$162CDA = $FFFF` and `$162CDC = 0`, and calls the list.
- **The list is `$10DC90`** (ROM `$1A490`): **110 `jsr` in a row and an `rts`** (ROM `$1A724`).
  The first, `$11988E`, registers type 0 (the empty module); each of the other 109 registers one
  type, and every type NME knows is among them (63, 65 and 77 too: their first routine is just
  the empty one's). They are not in type order (OscA's is third, type 17's last).
- **Each registration routine** starts with `move.w #type,-(sp)` / `jsr $10DC42`, then writes the
  entry. **`$10DC42(type)`** sets `$1A7BC0[type] = 1` and counts it in `$162CDC`; if the type was
  already registered it stores it in `$162CDA` (a duplicate). `$10DC70(type)` answers whether a
  type is registered (type 0 always is); no direct `jsr`/`bsr` to it was found, so who asks
  (probably the patch loader, through a pointer) is still open.
- **Where new code can live (corrected 2026-10-16).** The ROM's empty end (`$6A7E0`–`$7FFFF`)
  is copied to RAM `$15DFE0`–`$1737FF` with the rest of the OS, but two limits apply:
  - **the flash keeps the OS only up to `$70000`** (RAM `$16FFE0`); past that are the patch
    banks, formatted on the first boot, so nothing stored past `$16FFDF` survives a real G1's
    second boot;
  - the OS uses most of `$15DFE0`–`$16FB7E` as variables, except some runs (two of 19 KB at
    `$166573` and `$16B079`, two of 8 KB) that are still untouched when the types are registered.
  So the package was first **stored** in the 19 KB run at `$166574` and **ran** from `$170000`
  (`$170000`-`$1737FF`, 14 KB); since 2026-10-17 it is stored in both 19 KB runs and runs from
  `$1C6000` (see "More room: the RAM the OS never touches").

## The first new type: 119 (2026-10-16)

*Taken out on 2026-10-17 to free type 119 (only 128 types: see "Only 128 types"); its code is
in git history.*

**It works.** `tools/patch_rom.py type119-mixinv` makes a ROM where type 119 is the Mixer (3)
with input 1 inverted (`mpy -x1,x0,a` instead of `mpy x1,x0,a`), and
`tools/make_nme_data.py` (then `make_modules_xml.py`) a `modules.xml` with a "Mixer Inv" of type 119 for NME and the test
bench (`G1_MODULES_XML`, in G1-Emu's `g1patchtest` and battery).

- **How:** the Mixer (3)'s data block (`$14937E`, `$88` bytes: `+$2C`, descriptor, X/Y data,
  code, `+$24` table) is copied to `$16FB80`, with the three pointers of `+$24` that point inside
  it moved along. A hand-assembled routine right after it (`$16FC08`, 70 bytes) makes the list's
  last call (type 17), registers 119 with `$10DC42`, copies the Mixer (3)'s entry and points
  `+$24`, `+$28` and `+$2C` to the copy. The list's last `jsr` (`$10DF1E`) now calls it.
- **Checked:** after boot `$1A7BC0[119] = 1`, 111 types registered, no duplicate, the entry is
  the Mixer (3)'s with the three new pointers, and the code in RAM has the inverted multiply.
  In the battery (one oscillator into all three inputs, levels at 127) the Mixer (3) gives
  −52.3 dBFS and the new type **−61.8 dBFS**: one third, −9.54 dB, exactly what the inverted
  input predicts.
- **The OS refuses an unregistered type:** the same patch on the original ROM fails to upload
  ("the OS did not take the patch"). So registering is what makes a type valid.
- **Shared with the Mixer (3)** for now: its five routines, parameter names and the three RAM
  variables in `+$24` (`$1A5B68`…). A patch with both may clash through those variables; not
  tried.

**A bug in the first version, fixed:** the copy stopped at `$88` and left out the two bytes after
`+$24`'s pointers, which are the nop offsets (see below); the next byte, from the registration
routine, said +78. A second audio module after a Mixer Inv would have had its first word written
78 words away. The battery did not show it because the module under test goes last.

## How a module's data is loaded (2026-10-16)

From the module loader (`$122F72`):

- **`+$24` is two sets of X data, Y data and code**: `[0..2]` the audio part, `[3..5]` the
  control part, then two bytes: the offset of the nop slot of each part (`$FE` = 2 words before
  the end). **`+$28`, the descriptor**, gives the counts (in words, at byte offsets): audio
  cycles `+$02`, X `+$0E`, Y `+$12`, code `+$14` (long, 0 = no audio part) and `+$16` (count);
  control cycles `+$06`, X `+$1A`, Y `+$1E`, code `+$20`/`+$22`. The Mixer (3) has only an audio
  part; the logic modules only a control part.
- **A module's first code word goes into the previous module's nop slot**, the rest from the
  base on. So the first word runs before the previous module's last instruction (its output
  store): it must not touch `a` or `b`. Clavia's first words only load `x0`/`y0`/`x1`.
- **`r3` and `r4` walk through all the modules' X and Y data**: each module must advance them
  by exactly its own X and Y counts.
- **Inputs and outputs are code words the type's routines patch** (`x:$0` operands). For
  CompareAB the routine at `+$0C` (`$134FBA`) patches input 0 into word 0, input 1 into word 1
  and the output into word 5, by calling `$124202` and `$1243DA` with the part (1 = control) and
  the word index. Most of its other routines are the generic ones.

## Type 120: a D flip-flop (2026-10-16)

**It works.** Q takes D on the clock's rising edge. Donor: CompareAB (type 89: two inputs, one
output, no parameters, control rate). Its entry is copied with three fields replaced:

- `+$0C`: a copy of CompareAB's connection routine with the output word changed from 5 to 17.
- `+$28`: CompareAB's descriptor with our counts (control: 17 cycles, 3 X words, 18 code words).
- `+$24`: our X data `[high = $200000, last clock, Q]` and our code, written new (18 words, in
  `tools/patch_rom.py`): word 0 loads the clock into `y0` (safe in the nop slot), word 1 loads D,
  then `b = D > 0 ? high : 0`, kept as the old Q unless the clock is high now and was not before;
  Q is stored, then the nop slot and the output store.

`modules/flipflop/check_flipflop.py` plays `modules/flipflop/flipflop-lfo.pch` (ClkGen 48 Hz into clk, an LFO at
~0.7 Hz into D; Q, D and the clock on outputs 1–3) for 6 s in `g1patchtest` and checks the
recording: **D crosses zero 8 times, Q changes 8 times, every change on a clock edge, and Q
equals D at all 283 edges checked.** Q's levels are 0 and the same high as the clock's.

## Type 121: Mix1-1A, a chain mixer (2026-10-16)

After the G2's Mixer 1-1 A: `out = chain + in × level`, so one-channel mixers chain into a mixer
of any size. Built on the Mixer (3) with code of our own (8 words, in `tools/patch_rom.py`) and
the entry's counts set to 1 parameter, 2 inputs, 1 output:

- **How a parameter reaches the DSP** (the Mixer (3)'s routines): `+$00` turns the 0–127 value
  into the DSP value through a table at `$156A3C` (the level curve); `+$04` writes parameter 0 to
  X[0], 1 to Y[0], 2 to X[1] (through `$10C4B0`); `+$10` formats it for the display. The new
  type keeps them all, so its level is the Mixer (3)'s level 1, curve included.
- The connection routine puts input 0 at word 1, input 1 at word 3, input 2 at word 4 and the
  output at word 7: our code reads in at word 1 and chain at word 3 and never has a third input.
  X has 1 word (the level), Y none.
- **The Ch 1 button** (the G2's channel on/off): parameter 1, written by the Mixer (3)'s
  routine to Y[0] through the same level table, where 0 gives 0 and 1 gives `$4C5`. The code (9
  words now, so its own copy of the connection routine with the output at word 8) clears the
  channel when Y[0] is 0, before adding the chain.
- **A parameter's width in a patch comes from its maximum, on both sides.** NME takes it from
  `maxValue` in `modules.xml` (`PatchSerializer`, `pdlBitWidth`) and the OS from the type's
  parameter table (`+$1C`: 12 bytes per parameter, 11 of name and the maximum). With the
  Mixer (3)'s table the OS read the button as a 7-bit "Level 2" while NME sent 1 bit: the patch
  went out of step and the OS stopped answering (no reply to the first packet). 1 and 3
  parameters worked, 2 did not; a table of its own (`Level` 127, `Ch 1` 1) fixed it, and the
  G1's display now has the right names. NME's `ParameterEncoder` (used when a module is added
  live) has to say the same: `{7, 1}`.
- **Checked** (`modules/mix1-1a/check_mix1_1a.py`, patch `modules/mix1-1a/mix1-1a-chain.pch`): at levels 100, 64
  and 0 it gives exactly the Mixer (3)'s level (−69.5, −85.1 dBFS, silence), a Mix1-1A chained
  into another gives +6.0 dB, B's button off leaves A alone on B's output, and A's off silences A
  and leaves B alone. Not checked yet: turning the knob or the button live from the editor.
- **Not done: the G2's Lin / dB / Exp curves.** The level reaches the DSP already through the
  G1's table (a dB-like curve: 100 → −69.5, 64 → −85.1 dBFS here), so the DSP cannot rebuild
  another curve from it. It needs a `+$00` routine of our own that hands the DSP the raw value
  (or picks one of three tables) and a third parameter, the mode, whose change rewrites the
  level. That is 68k code of some size: time for an assembler (`vasm`) instead of hand
  assembly.

## How a module's lights reach the editor (2026-10-16)

Read from the CtrlSeq (type 91), whose step LED is a `led-array` 0–16 in NME:

- **The editor gets them in two messages**: plain LEDs in `Lights` (NMInfo `$39`: a start index and
  2 bits per LED) and meters and sequencers' step arrays in `Meters` (`$3A`, 7-bit values in
  pairs). Each module with lights takes the next slots in the patch's order (NME's
  `LightMeterLayout`).
- **The OS registers a module's light when its outputs are connected**: in the `+$0C` routine's
  output case (−1), after `$1243DA`, the CtrlSeq calls **`$1169BA(slot, section, module, value
  routine, 0)`** with the bytes at 0, 1 and 3 of the connection record. That adds the module to
  the slot's meter list (`$110666(slot) + $5252`). `$1169FC`, next to it, does the same on the
  list at `+$5636`, most likely the plain LEDs.
- **The value routine** (CtrlSeq's: `$13A618`) is called with the module's two records (A2, A3)
  and reads one of its X words through the DSP's host port: **`$10C32E(dsp, address)`**, address
  = the two records' X bases (word at +8 of each) + the word index (2 for the CtrlSeq). It
  returns the value to send; the CtrlSeq keeps a pointer there and turns it into the step 0–15,
  or 16 for none.
- **A meter carries 14 bits** (read 2026-10-17 in the poll and the sender, `$10AF2E`): the value
  routine's word is kept per entry and sent as two 7-bit values, the low 7 bits first (NME's
  slot B) and the next 7 (slot A); the meter list sends 5 entries a message, the list holds 40.
  So one module can show a byte (8 LEDs) with no second entry.
- So **a module of ours can light**: its code keeps the value in an X word, its `+$0C` registers
  a value routine with `$1169BA`, and the routine reads that word with `$10C32E`.

## Flashing a real G1 (plan, 2026-10-16)

Feasible, and hard to brick (from `../G1-Emu/NOTES.md`, "Boot and memory map"): the loader, the
MIDI update utility and the factory OS are in the **512 KB ROM, which cannot be written**; the
installed OS and the patch banks are in the 1 MB flash. At power-on the loader copies the flash's
OS to RAM, or enters the MIDI update mode if the flash is empty or a key combination is held, or
boots the ROM's own factory OS with another combination. So an OS of ours that hangs, or a power
cut halfway through, is recovered by sending Clavia's 3.03b update again. **Holding Shift + Store
at power-on enters the MIDI update mode** (Javier, on his real G1, 2026-10-19); and **Shift +
Patch/Load boots the ROM's factory OS**, which does not use the flash's OS at all (tried by Javier
too: slots "Empty patch", and the next plain power-on is back to normal). So even an OS of ours
that hangs leaves two ways back (`../G1-Emu/NOTES.md`, "Boot and memory map").

Risks: an OS update keeps the patch banks, at least in G1-Emu (2026-10-19: Clavia's updater in Wine over a flash with the factory OS, then a plain restart: every byte from `$70000` on unchanged, patches there; still back them all up before a real G1); and **on Javier's real G1** (2026-10-19) Clavia's 3.03b went over its 3.03b the same way: Shift + Store at power-on, the updater with Safe (Slower) through the UM-ONE, the G1 asks "Update flash? Store = yes" (any other key keeps the old OS), Store, `Update completed`, restart; a
patch with new types stored in a bank may trip Clavia's OS later (while testing, upload such
patches to a slot, never store them); and the real hardware against the emulator.

**Solved (2026-10-16): an OS of ours that hung on its second boot.** G1-Emu's window showed a
blank display with a flash the OS had already formatted. The flash keeps the OS only up to
`$70000` (RAM `$16FFE0`): from there on are the patch banks, which the OS formats ("INIT FLASH")
on its first boot, and G1-Emu, like the loader, restores the OS only up to there
(`Engine::OsBytes`). The package then ran from `$16FB80` to past `$170000`, so its registration
routine was in the banks' sector: erased by the formatting, and on the next boot the list jumped
into `$FF`. `g1boot` with `G1_FLASH` did not see it because that option first restored the whole
image. Now the package is stored at `$166574` (inside the OS's sectors) and copied at boot to
`$170000` (see "Where new code can live"). Checked: three boots in a row on the same flash with
`g1run`, the old hanging flash, both module tests, and a 2 MB recorded NME session replayed with
the package still intact at the end.

Before a real G1:
1. **Port the experiments to the 3.03b update's OS**, which is what a real G1 runs: the same
   code linked with other addresses (G1-Emu's notes: mostly `$20` higher), so every address in
   `tools/patch_rom.py` needs its update counterpart, and the untouched RAM must be checked again.
2. **An updater of our own**, sending the modified OS the way Clavia's updater does. G1-Emu
   already takes the official updater's MIDI (in Wine): capture it, learn the format, reproduce it.
3. **Rehearse in G1-Emu**: flash ours, boot, play, flash Clavia's back, try the key combinations.
4. **On the G1**: back up the banks, flash Clavia's once (the procedure works), then ours, test,
   and back to Clavia's.

## Type 120, complete: D-type and RS-type (2026-10-16)

The FlipFlop is now the G2's: inputs Clk, In and Rst, outputs Q and NotQ, a Type parameter
(D / RS). Code in `modules/flipflop/flipflop.asm` (55 words, with short relative branches), assembled by
`tools/dspasm.py`, which looks every instruction up by its text in an index of all one-word
opcodes disassembled by G1-Emu's `dspdis` (built once into `out/`).

- **Built on ClkDiv (type 69)**, a control-rate type with one parameter: its `+$00` hands the
  value over unchanged, and a copy of its `+$04` calls a routine of ours that writes the Type to
  X[1] with **`$10D142(module, value, X word)`** (what ClkDiv uses for its own words). LogicProc's
  shows the other way: **`$10D046(module, instruction, code word)`** rewrites an instruction.
- **The descriptor says how many outputs the module has** (word at `+$08`: 1, 2, 4… across
  Clavia's types), and the OS gives each output a word of its own from it. Copied from ClkDiv it
  said 1, so NotQ wrote into the next module's output: with Javier's patch (Q and NotQ into two
  envelopes' triggers, like on the G2 demo) one output alternated and the other gave fast triggers
  unrelated to the clock, and in a test a Constant placed after the FlipFlop changed with NotQ.
  Fixed (2); `modules/flipflop/flipflop-neighbour.pch` keeps watch.
- **The connection routine is generated** (`connection_routine` in `patch_rom.py`) from the
  assembler's marks: an input may be patched into several words (In is read at three places) with
  `$124202(part, connection, record, word)`; the outputs, all in the −1 case, with
  `$1243DA(part, connection, output, word)`.
- **Rules for code with branches**: no branch leaves word 0 (it runs in the previous module's
  nop slot) and none lands on the nop slot or after it (the next module's word 0 goes there).
- **Checked** (`modules/flipflop/check_flipflop.py`, 4 cases of 6 s): D-type follows In at every clock
  edge; RS with In unplugged toggles on all 288 edges (a divider by 2); RS with Rst from an LFO
  holds Q at 0 while Rst is high and toggles 152 times while it is low; RS with Clk unplugged sets
  Q on In and keeps it. NotQ is Q's opposite everywhere after the first 50 ms. Weak spots: in the
  set case In is already high at the first sample, so the edge is the start; and once, in the
  toggle case, NotQ had a stray value for 2 samples 4 ms in, while the patch was being set up,
  not explained.

## Plain LEDs, and the FlipFlop's (2026-10-16)

- **A plain LED is registered with `$116832(slot, section, module, value routine)`** (the
  RndPulsGen's), on the slot's LED list (`+$5636`), in the outputs case of `+$0C`. The value
  routine returns 1 (lit) or 0; it reads the module's data through the host port, X with
  `$10C32E` (host command `$BB`) or Y with `$10C2F6` (`$BC`), at the record's base (word at +8 for
  X, +10 for Y, of both records) plus the word.
- **One LED per module**: the list's add routine (`$1168FC`) returns at once when the module is
  already in it, so a second call for the same module adds nothing. The FlipFlop lights Q (the
  G2's NotQ LED is its opposite anyway).
- The editor gets them in `Lights` (NMInfo `$39`): a start index, then 2 bits per LED. G1-Emu's
  `g1patchtest` logs the PC Port with `G1_PCPORT_LOG`; `modules/flipflop/check_flipflop.py` checks that LED 0
  goes on and off with the FlipFlop toggling.
- NME: `<light ... type="led">` in `modules.xml` and in the theme. The FlipFlop's panel is now
  laid out like the G2's.

## Type 122: Noise S&H (2026-10-16)

*Taken out on 2026-10-17 to free type 122: a G1 Noise into a Sample&Hold does it. Its code and
test are in git history; its noise lives on in the Turing Machine.*

Our own module (Javier's idea): on Trig's rising edge it holds a noise value; Out gives it and
Inv its mirror. Parameters: **Range** (1–5 octaves) and **Uni/Bi**. `dsp/noise_sh.asm`, 26 words,
control rate: a 24-bit Galois shift register (taps `$E10000`, x^24+x^23+x^22+x^17+1) steps once a
sample (`lsr a` and `eor x0,a ifcs`); the edge holds its word; every sample the held noise is
scaled: Out = N·A + U·A, Inv = U·A − N·A, with A = 6 semitones per octave of range and U = 1.0 (Uni)
or 0 (Bi). Built on CompareAB with one input, two outputs (in the descriptor) and two parameters.

- **A semitone is 1 control unit** at a pitch input with its amount at 127: measured with a
  Constant into an OscA (+12 units: 262 → 524 Hz, +24: 1047 Hz). The logic high, `$200000`, is 64
  units, so a unit is `$8000` in the DSP.
- **Parameters of our own** (`param_routines`, `write_x_routine` in `patch_rom.py`, reusable): a
  `+$00` that hands every value over unchanged, a `+$04` that sends each parameter to its routine
  through `$10C49E`, and per parameter a routine that writes an X word with `$10D142`: Range
  writes A = (v+1)·3 << 16, Uni/Bi writes 1.0 or 0. Their own table (`Range` max 4, `Uni` max 1),
  so NME's widths (3 and 1 bits) match.
- **How a parameter reaches the DSP, live** (found because Range did nothing when turned):
  `+$04` does not write anything itself. With `$10C49E` it copies the parameter's record and
  **returns the routine** that will write the value, which the OS calls later, at patch load and
  on every change. Before a live change the OS asks **`+$08`**: 0 means "this routine", while the
  Mixer's answers 1 after `$113834` (the morph and smoothing path, it seems). CompareAB's `+$08`
  is a bare `rts` that leaves `d0` as it was, so the Noise S&H's changes never reached its
  routine; it uses ClkDiv's now (`clr.b d0`). **Every type with parameters of ours needs a `+$08`
  that answers 0.**
- **Checked** (`tests/check_noise_sh.py`, three cases): every Trig edge changes Out and nothing
  else does; 1 octave Bi spans −6.0..+6.0 semitones, 5 octaves Bi −29.9..+29.9, 3 octaves Uni
  0..35.9; Out + Inv is 0 (Bi) or 36.00 (Uni) within a hundredth of a semitone (the output chain
  truncates by a bit: x and −x come out one or two LSB apart).
- Every voice starts from the same seed, so the voices of a poly patch draw the same sequence;
  a seed per voice is still to do.
- NME shows Range in a display ("1 Oct"… "5 Oct", formatter `fmtOctaves1to5` in the `g1-mods`
  branch) and Uni/Bi as a button.

## A module's record in the OS's RAM (2026-10-16)

Found because adding any module live to a patch with a Noise S&H stopped the oscillators and left
clicks (Javier). In G1-Emu, with `g1patchtest --add-module-at`, `G1_WATCH_PC` and `G1_RAMDUMP`:

- **Every module has a record in the slot's RAM**: `$24` bytes of header (the type at `+$0E`, the
  position at `+$0F`/`+$10`, the name at `+$13`) and 8 bytes a parameter from `+$24` (the value in
  the fifth). They are laid out one after another by a bump allocator (`$1197BA`): the next one
  goes at `$18C1CA` + what the slot has used, and the size it adds is **the descriptor's word at
  `+$24`, in words**: `$12` for CompareAB (no parameter), `$16` for ClkDiv (one), `$1E` for the
  Mixer (3) (three), `$32` for type 25 (eight).
- The Noise S&H had CompareAB's `$12` with two parameters: a module added after it got its record
  written over the Noise S&H's parameters, and the OS, re-sending them to the DSP for every voice
  (`$10DA00`, with each value through `+$00`), sent 5 and `$8A` instead of the patch's values: a
  scale five times too big, the oscillators driven off the scale, clicks. A full upload hid it
  (records laid out fresh, the next one after the last). Now every type's descriptor says
  `($24 + 8 × parameters) / 2` (`record_words` in `patch_rom.py`).
- `tests/check_insert.py` adds a FilterE live to each test patch and checks the outputs go on as
  before; it passes, and the other tests too.

## A control type, described once (2026-10-16)

The three bugs of the day (NotQ sharing a word, the knobs dead live, the record overwritten) all
came from fields copied from a donor and fixed by hand. `control_type` in `patch_rom.py` now
builds a control-rate type from its DSP file, its X words' initial values, its parameters
(`Param`: name, maximum, the X word it goes to, a 68k transform) and maybe one LED, and derives
the rest: the counts at `+$18` (inputs and outputs from the `@inN`/`@outN` marks), the parameter
table and routines, ClkDiv's `+$08`, the connection routine, and the descriptor (outputs,
cycles, X and P words, the record's size). The descriptor starts from ClkDiv's, whose other
fields are checked to be zero. The cycles are the code's words plus 4 a branch (worst case;
the FlipFlop said 16 more, now 36). The FlipFlop and the Noise S&H are built with it; every test
passes as before.

`tests/check_nme_data.py` compares, for every new type, what the OS was built with against NME's
data: each parameter's maximum and the inputs and outputs in `modules.xml`, and the bit widths
in `ParameterEncoder.cpp` (its `g1-mods` branch, read with `git show`). `tests/run_all.py`
runs every test.

## Type 123: 5-Step Seq, and a row of step LEDs (2026-10-16)

- **The step's value is read at r3 + the step**: the step is a plain integer in X[0] (`add #<$1`,
  `cmp #<$5` work on b1), `move r3,a / add b,a / move a1,r2` and `x:(r2)`. r2 is a scratch
  register between modules: Clavia's CtrlSeq uses it (and r5) the same way, though it keeps the
  step as an absolute address its 68k routines relocate; a step relative to r3 needs none.
  `lua (r3+$5),r3` skips the five values.
- **The step LEDs are a led-array on the meter list**: the outputs case of `+$0C` calls
  `$1169BA(slot, section, module, value routine, 0)`, the last argument a word (the CtrlSeq
  clears the word left on the stack), and the value routine returns the step, or 16 for none, as
  the CtrlSeq's does. NME draws it from the Meters message (`$3A`, the module's B value); its
  theme's `led-array` takes `steps="5"` now (branch `g1-mods`).
- The knobs: (v − 64) control units, `(v − 64) << 15` in the parameter's 68k transform.
- **Rst as the G1's sequencers have it** (measured on the CtrlSeq, same clock and reset): a Rst
  edge changes nothing at once and arms the sequencer; the next clock, or one in the same sample,
  goes to the first step. It starts on the last step, so the first clock plays the first. The
  first version jumped to the first step at the Rst edge, so it ran a step ahead of a CtrlSeq
  reset with it (Javier: the sequencers would not sync). The CtrlSeq's output changes one control
  period (4 samples at 96 kHz) after ours at each clock: a fixed latency, not a step.
- `modules/step-seq-5/check_step_seq_5.py`: the steps in order with the clock, a knob turned live, the step in the
  Meters messages, and **in step with a CtrlSeq** (`modules/step-seq-5/seq5-ctrlseq.pch`, Rst from an LFO, its
  edges between clocks); `check_insert.py` plays it too.

## Type 124: Turing Machine (2026-10-16)

- **A 16-bit register in one X word**, an integer in a1/b1: on a Clk edge `asl b` moves it up,
  the leaving bit (the register `and` a mask, `1 << (Length-1)`, which the Length routine writes)
  comes back with `or #<$1,b`, and `eor #<$1,b` flips it; `and` with $FFFF keeps 16 bits. The
  logic immediates (`or`, `eor`, `and #<$1`) work on b1, as `add #<$1` did in the 5-Step Seq.
- **The coin toss**: the Noise S&H's Galois register, stepped every sample, shifted once more so
  the draw is 0..$7FFFFF, against (127 - Prob) << 16: Prob is bipolar, as the original's big
  knob (Javier found a one-way 0..127 knob with both ends locked confusing): 127 (right) never
  flips, 64 (centre) flips half, 0 (left) 127 times in 128, the pattern inverted each pass.
  NME draws it from the centre (`value-64`, default 64).
  Lock is its own X word, tested on the edge (a second parameter on the same word is not
  possible: each routine writes a whole word).
- **CV** is the low byte `asl #$d,a,a`: 0..$1FE000, 0 to +64 units, as a G1 logic high. **Gate**
  is bit 0 while Clk is high, so ones in a row give separate gates.
- r3 stays on the register after the Clk test and the rest is read at offsets
  (`x:(r3+$n)`, one word each), `lua (r3+$7),r3` at the end: no pointer walking to keep equal
  on both paths.
- Length is 1–16 (`value+1`, a formatter NME has) rather than the 2–16 planned: no NME change.
- `modules/turing-machine/check_turing_machine.py`: Prob 127 repeats every Length clocks (8 and 16), Prob 0 comes back
  inverted after Length, gates 1, 4 and 8 are their bits, Scale 64 halves CV, the Meters
  messages carry the byte, Lock holds it, 64 drifts, CV changes only on clock edges, Gate is bit 0
  and Clk. `check_insert.py` plays it too.
- **Eight gates, Scale and the 8 LEDs** (2026-10-17, Javier's bigger module): outputs 1-8 are
  bits 0-7 while Clk is high, each `clr b / lsr a / tfr x1,b ifcs / move b,x:$0` (the bits
  shifted out through the carry; a is cleared first when Clk is low). The Gate output went: it
  was gate 1. Scale multiplies CV (`mpy`, the fraction (v << 16) + (v << 9)). The LEDs are the
  meter list with `bits_routine` (the register's X word `and` $FF): the OS sends bits 0-6 on B
  and bit 7 on A, and NME's `led-array` with `bits="true"` lights one LED a bit. Height 5.
- **Not yet**: a Rst, and the expander's mixes (1+2, 2+4, 4+7, 1+2+4+7).

## Type 125: Scale Quantizer (2026-10-17)

- **The pitch scale**: a semitone is one control unit ($8000) and **0 is note 64, an E** (the
  Keyboard's Note out): the first version took 0 as a C, so "C major" was E major. The key's note
  is (n + 4 - Root) mod 12.
- **In to semitones**: `+ $4000`, `asr #$f,a,a`: a1 is In rounded to the nearest semitone,
  negative ones too (an arithmetic shift floors).
- **mod 12 without a divide**: m = n + 136 - Root (never negative for the inputs a G1 has), times
  ceil(2^23 / 12) with `mpy`: b1 = floor(m / 12), exact for every m up to a few thousand; 12q by
  shifts (`asl #$2`, `asl`, `add`).
- **A table of 12 corrections per scale**, the distance to the scale's nearest note (the lower
  one on a tie), computed in `patch_rom.py` (`SCALES`, `corrections`) and written whole by the
  Scale routine: `write_table_routine` writes a value's row of signed bytes to 12 X words, one
  `$10D142` each, and `Param(..., table=)` builds it. The DSP looks it up at r3 + 5 + the note,
  through r2.
- **n2 is not scratch**: reading the table with `move a1,n2` / `x:(r2+n2)` stopped the whole DSP
  (the LFO next to it froze); the address made in b and `move b1,r2` works.
- NME shows the root, the scale's name and the octave with formatters of its own; their names
  are in NME, so `check_nme_data.py` checks it has as many scale names as `SCALES`.
- `modules/scale-quantizer/check_scale_quantizer.py`: an LFO over the whole range into In, and every sample of Out the note
  the table gives, for the 16 scales on C and three other roots and octaves; `check_insert.py`
  plays it too.

## Type 126: 8Counter (2026-10-17)

- The 5-Step Seq's clock and Rst code (Rst arms, the next clock goes to the first step, it
  starts on the last), the step 0-7 in X[0] for a row of eight step LEDs (`steps=(0, 7)`), and
  eight outputs, each `clr a / cmp #<$k,b / tfr x1,a ifeq / move a,x:$0`: high for the whole
  step. No parameters (NME's encoder has an empty case for it, which `check_nme_data.py` wants).
- `modules/counter8/check_counter8.py`: a model of the counter on the recorded clock and an LFO's Rst, and
  every sample of Out 1, 2 and 8 the model's, from the first Rst on. Before it, the counter may
  be a step behind the model: the first clock can come while the patch is still being set up
  (the 5-Step Seq too; nothing to fix). `check_insert.py` plays it too.

## Only 128 types (2026-10-17)

- The type table at `$1C3B00` has 128 entries, and a patch keeps a type in 7 bits: there can be
  no type 128. 127 is Clavia's PolyAreaIn. In a RAM dump after boot, the unregistered entries (the
  default routines `$1198FE`...) are 0, 6, 41, 42, 55, 56, 60, 93, 101, 109, 116 and 119-126, the
  same ones modules.xml has no module for. `FREE_TYPES` in `patch_rom.py` lists them (without 0)
  and `add_type` refuses any other: types 127 and 128 were nearly used.
- The same day, the Mixer Inv (119) and the Noise S&H (122) were taken out to free their types:
  eleven free now (`PORTING.md` has the plan to spend them, a type per family).
- NME's `test_mods_categories` took every mods type as 119 or above; it knows the free types now.

## Type 101: Mux8-1, with the Sw8-1 (2026-10-17)

- The G2's Mux8-1 and Sw8-1 in one type, to spare types: the input picked is Sel (a knob, 0-7)
  plus Ctrl in steps of 8 units (`asr #$12`: Ctrl / 2^18), held to 0..7. Unplugged, Ctrl is 0
  and the knob picks.
- Picking without an index: each input is read and `tfr x0,b ifeq` after `cmp #<$k,a`, eight
  times (an input's address is patched into its own word, so they cannot be indexed).
- The LEDs: the input picked in X[2], a led-array of 8 (`steps=(2, 7)`). The OS sends a meter only
  when it changes, starting from 0: with In 1 picked nothing is sent, and NME lights the first.
- Control rate: for levels and gates. Audio through it is sampled at the control rate.
- `modules/mux8/check_mux8.py`: eight Constants of known levels, and every Sel and Ctrl tried picks its
  input; `check_insert.py` plays it too.

## Type 6: Random (2026-10-17)

- **The G2's randoms in one clocked module**, since the G1 already has free-running ones: Seed,
  Poly, Step, Edge, Prob and Length. One engine does Random A/B (Out), Rnd Trig (Trig and Prob)
  and Rnd Pattern (Seed and Length).
- **A seed per voice is possible**: a parameter's routine is called once a voice (`$10DA00`),
  and the structure it gets has the voice in its byte 2 (what `$10D142` reads to find the voice's
  X base). The Seed routine (`seed_routine`) writes the seed's value, the voice's, and a "load"
  flag, three `$10D142` calls; the DSP loads seed ^ (voice & Poly).
- **The draw**: 16 steps of the 24-bit Galois register a clock (unrolled, 32 words), so the top 16
  bits are new each clock; Out from all of it (a quarter, ±64 units), the chance from the low 16.
  After the shifts a2 is still the old sign (`lsr` moves a1 only): the register is read again
  before it is used as a number (the first version spanned ±128 units).
- **Out** moves toward the draw by Step (`T + S (draw - T)`), and glides with Edge, a factor of
  1 down to about 2^-16 (`($800000 - (v & 7) << 19) >> (v >> 3)`), on a 48-bit Out (two X words)
  so a slow glide still moves.
- **Load**: the first clock after the Seed is written, after a Rst edge (armed, as the
  sequencers), and every Length clocks. A patch takes about 15 clocks (at 48 Hz) to set up before
  a recording starts; the Seed routine sets the load flag, so the values start from the seed.
- `modules/random/check_random.py` checks the values against a model in Python, one by one, for two seeds,
  and Length, Rst, Prob, Step and Edge. Poly the bench cannot check (it plays one voice): Javier
  checked it by ear, chords on a Random in Poly give a sequence a voice.

## Type 41: Bits (2026-10-17)

- The G2's BinCounter, ADConv and DAConv in one module, with a Mode selector and the connectors
  of all three (Clk, Rst, In, B1-B8 in; Out, Bit 1-8 out), as the DrumSynth has many: no virtual
  modules needed. Each mode makes a byte; Out is it as a level (<< 13, 0..+64 units), Bit 1-8 its
  bits, the eight LEDs (the meter, `bits=(0, $FF)`) show it.
- Count: the 5-Step Seq's clock and Rst, the counter in its own X word, so it keeps counting in the
  other modes. A>D: In `asr #$d`, held to 0..255. D>A: B8 down to B1, `asl b` and `add y1,b ifgt`
  (y1 = 1): a conditional add, one word.
- NME's three-way selector is a `button` with `cyclic="false" landscape="true"`: three segments
  in a row.
- `modules/bits/check_bits.py`: Count a step a clock with its bits and LEDs, A>D against an LFO in
  every sample, D>A from eight Constants. `modules/bits/bits.pch` starts in D>A: `check_insert.py`
  compares the peak of the first and last seconds, which a counter's ramp would not keep.

## Type 42: Level (2026-10-17)

- The G2's ModAmt, MinMax, T&H and WindSw in one module with a four-way Mode selector, inputs A
  and B, Out 1 and Out 2, and Amount, Lo and Hi. ModAmt: Out 1 = A (1 - Amount + Amount B), B
  as 0..1 over 0..+64 units, Out 2 the rest of A. MinMax: the lower and the higher. T&H: Out 1
  tracks A while B is high, Out 2 while low. Window: Out 1 is A and Out 2 high while Lo <= B <= Hi.
- MinMax without branches: `cmp x1,a` then `tfr x1,a ifgt` and `tfr y0,b ifgt`.
- `modules/level/check_level.py` checks every sample of each mode against its formula (two LFOs, a
  clock, a Constant); `level.pch` starts on ModAmt with the Constant, steady for
  `check_insert.py`.

## The Random's Bi/Uni (2026-10-17)

- A seventh parameter, Uni (Javier: a filter or a resonance wants a positive signal): Out becomes
  (Out + 64 units) / 2, 0..+64, with an `asr` and an add at the output. A patch saved with the
  six-parameter Random loads its Out as Bi.

## Type 55: Envelope (2026-10-17)

- The G2's ADDSR, H, D and AHD from one engine: attack, decay 1 to Level 1, decay 2 to Sustain,
  release, each an exponential approach by a factor a control sample (the Random's Edge formula:
  from at once to about 2.4 s a time constant, some 17 s down to -60 dB). Gate mode holds at
  Sustain and releases when Gate falls (ADDSR); Trig mode goes on into release at Sustain, whatever
  the gate (D, H with Decay 1 at Level 1 as the hold, AHD).
- The attack aims at 0.3 to reach the top (0.25, +64 units) and stops there; a decay moves on
  within $200 of its level; the release stops at 0 there and End goes high. Env is kept in 48 bits.
- Stage numbers are kept in X words (an 8-bit immediate move to a data register would land in its
  top byte, not as an integer).
- The recording of a level at 0 reads about 0.009 units: the output chain leaves a hair of offset.
- `modules/envelope/check_envelope.py`: the levels (top, Level 1, Sustain), the release's time constant (684
  samples against 683 from the factor), Attack 40 against 80, End, Trig mode. `env.pch` has a
  fast enough gate for `check_insert.py`.
- Not yet: the Mod AHD's inputs that modulate the times.

## More room: the RAM the OS never touches (2026-10-17)

- **Found** as the first 14 KB were: NME's recorded session (2.1 MB, every byte read by the OS)
  replayed in `g1boot` and the RAM dumped at the end, then the same replay with the candidate runs
  filled with `$A5` just before it (a local, uncommitted fill option in `g1boot`), to tell a run
  the OS never touches from one it uses and leaves at zero.
- **`$1C57F0`-`$1EFECF` (170 KB) is free**: the pattern came out whole, and no code in the OS
  holds an address in it (the 198 longwords that fall in it are jump tables and data). Above it,
  up to `$1FFF00` (the reset SP), are the OS's stacks and variables; just below, a tick counter at
  `$1C57E0`. **The package runs from `$1C6000`-`$1E7FFF`** (136 KB), 32 KB kept below the stacks.
- **The 97 KB right after the old room (`$173810`-`$18BDA2`) is not free**: five OS buffers of
  exactly `$4B06` bytes from `$174684`, zero in that session, but the OS wrote their headers
  (`00 00 16 45 AA`...) as soon as they held anything else. The three 13.8 KB runs at `$1B16F0`,
  `$1B76F0` and `$1BD6F0` are used too (some 300 bytes written in each).
- **Storing it is now the limit**: the package lives in the ROM, inside the OS image the flash
  keeps (up to RAM `$16FFDF`). The bootstrap (52 bytes at `$166574`) copies the first 19 KB run
  (`$1665A8`-`$16B077`) and then the second (`$16B07A`-`$16FB7D`; the OS writes the bytes at
  `$16B078` and `$16FB7E`) to `$1C6000`. 38,352 bytes in all: with 13,460 used, **24 KB left**.
  Checked: all tests pass, and a ROM split by force (the first run cut to 4,000 bytes, the String
  in the second) plays the String, Turing and Envelope patches bit for bit as the normal one.
  The two 8 KB runs of "Where new code can live" could be a third and fourth stage if needed.

## Room for code: 2.3 KB left (2026-10-17, before the move)

- **The package (every new type's code, data and routines) runs from the 14 KB at `$170000`**
  ("Where new code can live"), and with the eleven types it takes 11,992 bytes: some 2.3 KB are
  left. A type takes 340 (Mix1-1A) to 1,480 bytes (Random); repeated blocks would save only 228.
  What it is made of: the DSP code at 4 bytes a word, the X data's initial values, a 68k routine
  per parameter (~40 bytes), the parameter table, the connection routine, the descriptor.
- **The big modules need more**: more DSP code, and a delay line's initial X data (zeros) would
  be 4 bytes a word (a 1,024-word string, 4 KB) unless the loader is pointed at zeros already in
  RAM. So before the String: find more room that the OS never touches while it runs (as the 14 KB
  were found: a long recorded NME session replayed and the RAM dumped), and point big buffers at
  zeros.
- **Audio parameters** (found for the String): the OS writes a parameter to a module's audio X
  through `$10C4B0(module, request, word)`, which fills a 12-byte request (the DSP's host port, the
  address = the voice's audio X base at +2 of its entry, + the module's at +6, + the word, and
  `$B5`), and `$10C248(request, value)`, which writes it. The control part's `$10D142` is the same
  with +8 and +8. The voice and module tables are the same for both parts.
- **The G1's Delay** (type 78, 2.65 ms at 96 kHz) takes 133 X and 131 Y words, its buffer split
  across both; NME rates that at 9.25 % of each: about 1,440 words of X and as many of Y a voice.
  A string's buffer at the full rate reaches down to 96000 / words Hz: 512 words 187 Hz, 1,024
  (about 70 % of X or of Y) 94 Hz; at half or a quarter rate it reaches 47 or 23 Hz.

## Type 56: Osc String, the first audio-rate type (2026-10-17)

- **`audio_type`** (as `control_type`, for a type's audio part): the Mixer (3)'s descriptor with
  our counts (audio cycles `+$02`, X `+$0E`, Y `+$12`, code `+$14`), the connection routine with
  part 0, `+$24` with the nop slots `$FE`/`$FF`, and the parameters written to the audio X with
  `write_audio_x_routine` (`$10C4B0` then `$10C248`). Checked first with a VCA (`vca_test`, the
  `audiotest` experiment): Level 127, 64, 0 gave 1.000, 0.504, 0.
- **X memory**: a module with 1,400 X words still loads in a patch with an oscillator; 2,048 does
  not (the patch is refused). The string takes 26 + 1,024.
- **The line is never initialised by the loader**: it copies the descriptor's X count from the X
  data, so past our 26 words it copies whatever follows; the code clears one word a sample from
  the start. No 4 KB of zeros in the package.
- **The period**: n = Note + Pitch (as an oscillator's: 0 units is note 64), L = L(135) *
  2^((135 - n) / 12). The octaves split into k and f; 2^f by a cubic (1 + 0.6951786 f +
  0.2261745 f^2 + 0.0786469 f^3, halved); then `rep y1` / `asl a` k + 1 times (rep never gets 0).
  L is kept * 4096 and read between two samples linearly. A first version was an octave high:
  the constant and the cubic were both halved.
- **The lowpass detunes**: y += k (x - y) delays the loop by about (1 - k) / k samples (measured
  1.89 against 2.03 at Damp 30, 15 cents flat). Damp's routine (`damp_routine`, with a `divu.l`
  of our own) writes that * 4096 too, and the code takes it from L: now within a cent at any Damp.
- **Decay** is the loop's gain once a round trip: 1 - a time factor / 8.
- `modules/osc-string/check_osc_string.py`: A1 to A5 from the knob, A3, A4, E5 from the keyboard, Damp 30 and 10,
  all within 2 cents (they are within 1); Decay 60 against 110.
- Lowest note 94 Hz (96000 / 1024). Lower: run the line at half or a quarter of the rate.

## The mark: an OS with modules says 3.09 (2026-10-18)

An editor has to tell an OS with modules from Clavia's, synth by synth: with several synths, a
Clavia OS can sit next to a modified one, and a module of ours sent to Clavia's would land on a
type it does not have. The IAm reply is where the synth says what it is, so the mark goes there.

- **The IAm is built by `$10B252`**, not kept as bytes: it waits for the send buffer
  (`$1A5BBC`), writes `F0 33 00 06`, sender 1 (`(6,a2)`), version 3 (`(7,a2)`) and 3
  (`(8,a2)`, a `move.b #$03` at `$10B288`), then the serial number from `$1258D2` in three
  7-bit bytes (bits 14-19, 7-13, 0-6) and the model from `$1C3AAC`, and sends 12 bytes. The
  byte NME's PDL calls "reserved" is the serial's top: G1-Emu's flash has no serial, so it
  reads `3F 7F 7F`; a real G1 sends its own. Not free, then.
- **The version's minor is**: Clavia's editor 3.03 sets what it expects at startup from its own
  version (`0x004273e0`: major 3, the minor's tens 0) and takes a synth whose major is 3 and
  whose minor / 10 is 0 (`0x00426890`, `../G1originaleditor`), so 3.00 to 3.09; a `7F` there
  is the update mode. NME takes any. Clavia never released a 3.09.
- So the builder changes that one `move.b` to `#$09` (`VERSION_MARK`, `tools/g1rom.py`) in
  every build with modules, and NME takes a synth that says 3.09 as one with them
  (`ConnectionManager::isModsVersion`), until it disconnects. `tests/check_mark.py` boots both
  ROMs in G1-Emu: Clavia's says 3.03, ours 3.09, and NME looks for the same number.

## Trying it by hand

`./run-g1emu.sh` starts G1-Emu's window with the ROM of every new type, on its own flash
(`out/flash-all.bin`) and with `G1_OS=` so the settings' `os =` does not replace the modified
OS; close the usual G1-Emu first (same MIDI ports). `./run-nme.sh` starts NME from its `g1-mods`
branch, whose palette has the new types. A stock G1 (or G1-Emu with Clavia's OS)
refuses a patch with them. In the maintainer's desktop both have launchers ("G1-Emu (G1-Mods)",
"Animatek NME (G1-Mods)", in `~/.local/share/applications`, outside the repo).

## Next

- More room for code (or the builder), then the next big modules (`PORTING.md`); NME's virtual
  modules for the switches and the G2 mixers.

There is no 68k assembler installed; the routines are short enough to hand-assemble and check
with `g1boot ... dis`, or `vasm` can be built.

## A MIDI Out module, as the G2's (2026-10-19)

Asked for by users: the G1's sequencers playing notes out of its MIDI Out. The G1 already sends
CC there (knob moves), so the port is wired and the OS can write to it: the 68331's SCI
(`../G1-Emu/NOTES.md`, "two independent serial ports").

**How the G2 does it** (`../G2-Emu`, Ghidra on the demo's Mac binary, read only, 2026-10-19):
the DSP part of NoteSend only watches the gate and leaves a "pending" word in its Y memory with
the note and velocity next to it; the CPU polls every MIDI module's memory over the host port
(`CPatchMIDIOut::PollQue`), builds the note on or off from those words, sends it, and clears the
pending word with a host command. The DSP never touches MIDI: it is a mailbox the CPU reads.

**The G1's MIDI out, read 2026-10-19 (factory OS, linear disassembly of ROM `$C800`):**

- **The sender** is `$103556`, called from the timer interrupt (`$1009BC`), one byte per call
  when the SCI can take it (`SCSR $FFFC0C` bit 8, data to `SCDR $FFFC0E`). In order of priority:
  a MIDI clock `$F8` when `$1C5354` is set; the **byte queue at `$15E2D2`**; the 3-byte queue at
  `$15E5E0` (sent as whole messages); the 2-byte queue at `$15E8EE`; the SysEx buffer at
  `$1A5724` (length word, data from +2).
- **Each queue** is a ring of `$300` bytes: data from its base, read pointer at `+$300`, write
  pointer at `+$304`, last address at `+$308`, count (word) at `+$30C`. Writing: store, bump `+$304`,
  wrap to the base past `+$308`, then `addq` the count (one instruction, so safe against the
  interrupt that drains it).
- **The OS already has note senders**: `$103790(note, velocity)` queues `$9n note vel` and
  `$1037FC(note, velocity)` `$8n note vel` into the byte queue, once for each channel in the list
  at `$15EBFD` (count at `$15EBFC`, built at `$103A54` from the slots' channels). Their only
  callers are the keyboard scan (`$117A6E`, `$117AF8`, `$11795C`, `$117B2C`): it is the keyboard
  model's key-to-MIDI path, alive but unused in the rack. The CC sender is `$1038D2(channel,
  controller, value)` (3-byte queue, a pending message for the same controller is updated in
  place); `$103868` sends CC 64, `$10395A` bank (CC 32) and program change.
- So a module of ours **sends a note by writing three bytes into the byte queue** with its own
  channel (the senders above use the keyboard's channel list, not ours), the same way they do.

**The lights' path does not do for notes.** The value routines (`$1169BA`) are polled from
`$116A3E` only for the active slot (`$1C3ABE`), 5 entries at a time, and only while the PC port
is free (`$1177A2`, `$1A5BBC`): they exist to feed the editor. A MIDI Out module needs its own
poll: a list of our own (slot, DSP, X address, channel), filled by the module's `+$0C` like the
light registration, and walked from the OS's main loop, reading each mailbox with `$10C32E` and
writing the note into the byte queue. Not from the timer interrupt: the host port reads would
race the main loop's. (The dial's decoder, `$104DAA`, is not the main loop: the timer interrupt
calls it, at `$1009B0`.)

**The main loop** is the end of `$100ACA`, the last call of the OS's start (`$109754` →
`$1097FC`): from `$100E6E` it calls `$1156BE` and `$1133EC`, takes the next event with
`$100208` (a word: `$04xx` a panel button, `$01xx`...), handles it, and branches back to
`$100E6E` (`$101122`); with no event it goes to `$101126` (the editor's lights among other
things). So the hook is the `jsr $1156BE` at `$100E6E`: pointed at a routine of ours that calls
`$1156BE` and then polls, it runs once a turn of the loop, events or not.

Still open: the hook into the main loop, what the DSP side keeps (gate, note, velocity, a
pending flag cleared by the 68k, as the G2), notes left hanging when a patch changes (send note
offs), and the same addresses in the 3.03b update. **Testing is ready (2026-10-19):** G1-Emu's
standalone already sent the MIDI OUT to its `MIDI` port, and its plugin now has it as its MIDI
output (G1-Emu branch `midi-out-plugin`; Javier saw a knob's CC reach another track in Bitwig).
`g1patchtest --knob-at S:knob` prints what came out of the MIDI OUT.

## Type 60: Note Out (2026-10-19)

The plan above, made: `modules/note-out/`. Note and Gate in, Chan and Vel, and Gate again out
(Thru); a note on at Gate's rising edge with the note Note had then, its note off at the falling
edge.

- **The DSP side** (`noteout.asm`, 35 words) sends no MIDI. It counts Gate's edges and latches
  the note on each rising one, and keeps one X word: the count (a step of `$100`), the gate (bit
  7) and the note (0-127: 64 + Note in semitones, rounded). One host-port read tells the 68k
  whether anything happened and what. Chan and Vel go to X words of their own, for the 68k.
- **The 68k side** (`noteout_poll.s`) is the first of ours written in assembly, not hand-made
  hex: GNU as for the CPU32 in Digitakt-Mods' Docker image (`tools/m68kasm.sh`), position
  independent, the bytes kept next to it (`noteout_poll.m68k`; `build.py` checks they are for its
  type). The build points the main loop's first call (`jsr $1156BE` at `$100E6E`) at it
  (`Build.redirect_call`, applied by `patch_rom.py`). Each turn it calls `$1156BE`, then:
  - **finds the modules without a list**: 8 module pointers a turn, a cursor over the four slots'
    common and poly pointers (1024 in all), the type at `+$0E`. Up to 16 followed at once, each
    checked again every turn (its pointer still there, still our type) before it is read, so a
    patch changed or a module deleted drops it, with a note off for a note it left on.
  - reads each one's word with `$10C32E`, at the voice record's X base (`+$228` of the section's
    pointers, voice 0) plus the module's: on a change, the note left on goes off and, with the
    gate high, the new one goes on, the channel and velocity read then. A velocity of 0 is sent
    as 1.
  - queues the three bytes into the byte queue at `$15E2D2` as the OS's own note senders do; the
    timer interrupt sends them.
- **Found on the way:** the whole scan at once (some 1 000 pointers every 256 turns) held the main
  loop up long enough for the OS to miss a patch upload (no ACK; G1-Emu's boot display showed
  dropped characters too). The OS does timed things in its main loop: the poll must stay short.
- **Found later the same day (Javier): the module after it stopped.** A second NoteSeq in the
  patch stood still, and a ClkDivFix added live silenced the MIDI. The DSP code read its words
  at offsets from r3 and left r3 there, but **r3 walks through every module's X data**: each
  module must leave it past its own (`lua (r3+$n),r3` before the nop, as the others do), or the
  next module runs on its words, and writes over them. With nothing after it (the first tests)
  it did not show. Now it moves r3 on, and `check_note_out.py` has an LFO after it in the
  patch's order. It also got its output then (Gate thru): first suspected, not the cause.
- **What is not there yet:** only voice 0 of a poly section is read (a Note Out is one voice's
  anyway: in the common section, or a mono patch); edges closer together than one turn of the
  loop are merged (a note shorter than that is lost, a retrigger is an off and an on); a patch
  uploaded with another Note Out at the very same record keeps the entry, and its note goes off
  only at the next change of its word; no SysEx, no CC.
- **Checked:** `check_note_out.py` in G1-Emu (its g1patchtest prints the MIDI OUT since PR #79,
  in main since 2026-10-19): an LFO into Gate gives `90 40 64` /
  `80 40 40` in turn; a Constant of +12 into Note with Chan 3 and Vel 90, `92 4C 5A` / `82 4C 40`;
  Chan changed live to 5, the note on goes off on channel 1 and the next ones are on 5; a patch
  without it sends nothing.
- **Played by Javier (2026-10-19):** a G1 sequencer into Note and Gate in G1-Emu's window, the
  notes on another track in Bitwig. Bitwig on Linux reads raw MIDI cards only: it hears G1-Emu
  through the `G1` gadget card (`G1 MIDI 1`), which the emulator links by itself only when its
  `rawMidiCard` setting names that card (it said `G1Emu` here, and nothing arrived until
  `aconnect` linked the ports by hand).
