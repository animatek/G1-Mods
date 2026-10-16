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
  So the package is **stored** in the 19 KB run at `$166574` and **runs** from `$170000`
  (`$170000`–`$1737FF`, 14 KB, never used by the OS: untouched after a replayed 2 MB NME
  session); a 36-byte bootstrap at `$166574` copies it there at boot, before registering.

## The first new type: 119 (2026-10-16)

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

`tests/check_flipflop.py` plays `tests/flipflop-lfo.pch` (ClkGen 48 Hz into clk, an LFO at
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
- **Checked** (`tests/check_mix1_1a.py`, patch `tests/mix1-1a-chain.pch`): at levels 100, 64
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
- So **a module of ours can light**: its code keeps the value in an X word, its `+$0C` registers
  a value routine with `$1169BA`, and the routine reads that word with `$10C32E`.

## Flashing a real G1 (plan, 2026-10-16)

Feasible, and hard to brick (from `../G1-Emu/NOTES.md`, "Boot and memory map"): the loader, the
MIDI update utility and the factory OS are in the **512 KB ROM, which cannot be written**; the
installed OS and the patch banks are in the 1 MB flash. At power-on the loader copies the flash's
OS to RAM, or enters the MIDI update mode if the flash is empty or a key combination is held, or
boots the ROM's own factory OS with another combination. So an OS of ours that hangs, or a power
cut halfway through, is recovered by sending Clavia's 3.03b update again. Which physical buttons
make those combinations (the loader reads raw panel rows: D1/D2/D3) is still to be checked in
the emulator.

Risks: whether an OS update keeps the patch banks is not known (back them all up first); a
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
(D / RS). Code in `dsp/flipflop.asm` (55 words, with short relative branches), assembled by
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
  Fixed (2); `tests/flipflop-neighbour.pch` keeps watch.
- **The connection routine is generated** (`connection_routine` in `patch_rom.py`) from the
  assembler's marks: an input may be patched into several words (In is read at three places) with
  `$124202(part, connection, record, word)`; the outputs, all in the −1 case, with
  `$1243DA(part, connection, output, word)`.
- **Rules for code with branches**: no branch leaves word 0 (it runs in the previous module's
  nop slot) and none lands on the nop slot or after it (the next module's word 0 goes there).
- **Checked** (`tests/check_flipflop.py`, 4 cases of 6 s): D-type follows In at every clock
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
  `g1patchtest` logs the PC Port with `G1_PCPORT_LOG`; `tests/check_flipflop.py` checks that LED 0
  goes on and off with the FlipFlop toggling.
- NME: `<light ... type="led">` in `modules.xml` and in the theme. The FlipFlop's panel is now
  laid out like the G2's.

## Type 122: Noise S&H (2026-10-16)

Our own module (Javier's idea): on Trig's rising edge it holds a noise value on Out, and the same
negated on Inv. `dsp/noise_sh.asm`, 24 words, control rate: a 24-bit Galois shift register
(taps `$E10000`, x^24+x^23+x^22+x^17+1) steps once per sample (`lsr a` and `eor x0,a ifcs`), and
on the edge its word becomes a signed level scaled to a quarter of full scale (the same peak as
an LFO's). Built on CompareAB, with one input and the descriptor saying two outputs.

- **Checked** (`tests/check_noise_sh.py`): 288 clock edges, 288 changes of Out and none off an
  edge, 285 different values, 138 positive and 150 negative, Inv the negation of Out.
- **Out + Inv is not 0 in a recording**: −63 or −126, one or two LSB after the recording's +36 dB.
  The output chain truncates (the master volume's multiply), so x and −x come out unequal by a
  bit. It is the G1's, not the module's.
- Every voice starts from the same seed, so the voices of a poly patch draw the same sequence;
  a seed per voice is still to do.

## Trying it by hand

`./run-g1emu.sh` starts G1-Emu's window with the ROM of every new type, on its own flash
(`out/flash-all.bin`) and with `G1_OS=` so the settings' `os =` does not replace the modified
OS; close the usual G1-Emu first (same MIDI ports). `./run-nme.sh` starts NME from its `g1-mods`
branch, whose palette has Mixer Inv and FlipFlop. A stock G1 (or G1-Emu with Clavia's OS)
refuses a patch with them. In the maintainer's desktop both have launchers ("G1-Emu (G1-Mods)",
"Animatek NME (G1-Mods)", in `~/.local/share/applications`, outside the repo).

`tests/mixer-demo.pch` is the one to hear: one OscA into inputs 1 and 2 of a Mixer (3) (output 1)
and of a Mixer Inv (output 2), levels 100. **The Mixer (3) doubles it and the Mixer Inv cancels
it**: measured −63.5 dBFS on output 1 and silence on output 2; with the Mixer Inv's input 1
unplugged, output 2 gives −69.5 dBFS, 6 dB under the sum, so the silence is the cancellation.
It also shows **the two mixers working in one patch** despite the RAM variables they share.

## Next

- Modules with parameters: what the routines at `+$00`–`+$10` and `+$20` do with them.
- Q and not-Q (two outputs) and a reset input for the FlipFlop; then an 8Counter.

There is no 68k assembler installed; the routines are short enough to hand-assemble and check
with `g1boot ... dis`, or `vasm` can be built.
