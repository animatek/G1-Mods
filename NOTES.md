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
- **Where new code can live:** the ROM's empty end (`$6A7E0`–`$7FFFF`, 88 KB of `$FF`) is copied
  to RAM `$15DFE0`–`$1737FF` with the rest of the OS, but the OS uses its lower part for
  variables: after boot it has written up to `$16FB7E`. **`$16FB7F`–`$1737FF` (~15 KB) stays
  untouched**; still to check after patch loads and editing. The `$FF` runs in between (8 KB,
  19 KB) look like buffers.

## The first new type: 119 (2026-10-16)

**It works.** `tools/patch_rom.py type119-mixinv` makes a ROM where type 119 is the Mixer (3)
with input 1 inverted (`mpy -x1,x0,a` instead of `mpy x1,x0,a`), and
`tools/make_modules_xml.py` a `modules.xml` with a "Mixer Inv" of type 119 for NME and the test
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

Next: a module that is not a copy (own I/O and parameters: a FlipFlop), which means writing its
own `+$24`/`+$28` data and checking what the five routines and `+$20` need; a patch with the
Mixer (3) and the new type together; and the real editor's view (NME in a branch).

There is no 68k assembler installed; the routines are short enough to hand-assemble and check
with `g1boot ... dis`, or `vasm` can be built.
