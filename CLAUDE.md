# G1-Mods

Modules of our own inside the **Nord Modular G1**: a modified OS that adds module types the G1
never had (a FlipFlop, an 8Counter, switches of 8...), tested on the emulator before anything
touches a real synth. Working name; if it becomes a product it should not carry "Nord" or
"Clavia", which are trademarks.

**Kept apart from `../G1-Emu` on purpose.** G1-Emu emulates the G1 *as it is*, with Clavia's OS
untouched; this repo changes the OS. Mixing them would blur what the emulator is. G1-Emu is used
here as the test bench (`g1boot`, `G1_RAMDUMP`, the module battery, `os =`), never changed from
here: anything the emulator needs goes into G1-Emu itself, as an emulator feature. If this ever
works well, it can be merged.

## Layout

- `modules/<name>/`: one folder a module, everything it needs (`modules/README.md`);
  `modules/registry.json` gives each its type, for ever.
- `tools/`: `patch_rom.py` builds the modules into the user's ROM, `make_nme_data.py` adds them
  to NME's data, `g1rom.py` is what every module's build uses, `dspasm.py` the DSP assembler.
- `tests/`: the tests across modules (`check_insert.py`, `check_nme_data.py`) and `run_all.py`,
  which runs every module's test as well. `dsp/`: only the experiments' code (`vca_test.asm`).

## Rules

- **Nothing of Clavia's goes into Git**: no ROM, no OS image (original or patched), no DSP code
  copied from the ROM or from the G2 demo. Tools take the user's own ROM and write the result
  into `Roms/` (ignored; README, "Where the builds are"), or the scratchpad. `out/` is only
  the tools' working files.
- **Clavia's code is studied, not copied.** The G2 demo (`../G2-Emu`) shows how Clavia wrote a
  module; ours is written new. Notes describe it in words.
- **The emulator first.** A real G1 is only flashed when it all works in G1-Emu, and the ROM's
  MIDI boot mode is known to recover a bad OS. Before touching a real synth, check which device
  NME is connected to.
- NME support for a new module is its folder's `nme-modules.xml` and `nme-theme.xml`;
  `tools/make_nme_data.py --layer ../Nomad2026/data` writes them into NME's layer files
  (`data/mods-modules.xml`, `data/mods-theme.xml`), which NME offers only to a synth whose
  OS says it has them (its IAm says 3.09: `VERSION_MARK` in `tools/g1rom.py`). That lives in NME's `mods-layer` branch, local,
  until Javier decides to publish G1-Mods: NME is public.
- Everything in this repo is in **English** (code, notes, changelog, commits), like G1-Emu, so
  a merge stays easy. On GitHub as `animatek/G1-Mods`, private for now (2026-10-18).

## Changelog

Every change that goes into the repo gets its line in `CHANGELOG.md`, in the same commit:
newest first, under the date, with who did it, what changes and how it was checked.

In the maintainer's workspace, every change also goes into the global changelog
`/mnt/SPEED/CODE/CHANGELOG.md` (rule in `/mnt/SPEED/CODE/AGENTS.md`, section Global Changelog;
that one is written in Spanish). It is a link to an Obsidian note: edit its target, never
replace it.

**Write entries with `cambios apuntar "<project>" "<what changed, verification, commit>" -a <agent>`**, not by editing the file: it files them under the date and project without rewriting anything or breaking the symlink (`cambios proyectos` lists the names; if the link is already broken, `cambios reparar`). Never `sed -i`, `>` or a whole-file write on it: that is how the symlink broke three times.
