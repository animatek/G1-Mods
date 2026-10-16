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
- **Free type numbers**, empty in the OS and unused in NME's `modules.xml`: 6, 41, 42, 55, 56,
  60, 93, 101, 109, 116, 119–126. Types 63, 65 and 77 are in NME but have the OS's empty entry:
  not checked why.
- The same conventions as the G2 (input pointers in `r3`/`r4`, addresses filled by the linker,
  the `nop` chaining slot): its 8Counter has the same shape. Clavia's code is studied, not
  copied: a module of ours is written new.

Next: who calls the registration routines (the list to add one to), what the five routines and
`+$20` do for the Mixer (3), and then a new type cloned from it with code of our own.
