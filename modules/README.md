# Modules

One folder a module. `tools/patch_rom.py` builds them into the user's own ROM, and
`tools/make_nme_data.py` adds them to NME's data; neither needs changing to add one.

```
modules/<name>/
  module.json       its type, names, author, licence, version, and where NME lists it
  build.py          build(b, type): how its type is put into the OS (tools/g1rom.py has the parts)
  *.asm             its DSP56300 code, ours (tools/dspasm.py assembles it)
  *.s, *.m68k       68k code of its own, when it needs some (note-out): the source, and the bytes
                    tools/m68kasm.sh assembles from it, kept so a build needs no toolchain
  nme-modules.xml   its entry in NME's modules.xml, whole
  nme-theme.xml     its panel in NME's classic theme, whole
  check_*.py        its test in G1-Emu, with the patches it plays (*.pch)
```

`module.json`:

| Field | What |
| --- | --- |
| `type` | its type number, from `registry.json`. Given for ever: a patch keeps it. |
| `name`, `fullname` | as NME shows them. |
| `kind` | `control` or `audio`: which DSP rate its code runs at. |
| `author`, `licence`, `version` | who wrote it, under what (GPL-compatible), and which release. |
| `nme_after` | the type its entries follow in NME's files, so the rest stays byte for byte. |
| `tests` | its tests, run by `tests/run_all.py`. |

`registry.json` says which type each module has (`given`), which are still free (`free`), and the
order the builder lays the modules out in (`build`) and writes NME's data in (`nme`). A new
module asks for a type there; nowhere else gives one.

Nothing of Clavia's goes into a module folder: no ROM bytes, no DSP code copied from the ROM or
from the G2 demo. `build.py` may read the user's ROM through `g1rom` (a donor type's routines),
never carry it.

Building only some modules: `tools/patch_rom.py flipflop,mux8 <your 3.03 ROM> Roms/rom-mine.bin`.
