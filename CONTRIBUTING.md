# Contributing to G1-Mods

G1-Mods is a passion project and it grows from what people bring to it. Pull requests are welcome and you do
not need to ask first. Take a module from the checklist ([`PORTING.md`](PORTING.md)), write it, test it in
G1-Emu, and your name goes on it: in the module's `author` field, in the changelog line, and in the notes of the
release that includes it.

## Get started

From nothing to your first module playing in the emulator: about an hour, most of it building G1-Emu.

### What you need

- **Python 3** and **git**. The tools (`patch_rom.py`, `dspasm.py`…) need nothing else.
- **Your own 3.03 ROM** (`NORD-MODULAR-RACK-VER-3.03.BIN`). Nothing of Clavia's is ever in the repository or in a
  pull request.
- **G1-Emu**, built from source next to the `G1-Mods` folder (`../G1-Emu`): it is the test bench.
- **Animatek NME 0.25 or later** (the first with G1-Mods support), to see the module's panel and play it.
- A 68k cross toolchain only if your module needs 68k code of its own (as Note Out does). Its assembled bytes
  are kept in the repository, so building and testing never need it.

### How a module is laid out

```
modules/<name>/
  module.json       type, names, author, licence, version
  module.es.json    optional: the same texts (summary, about, usage, notes…) in Spanish, for the web
  build.py          how its type is put into the OS
  <name>.asm        its DSP56300 code, written new
  nme-modules.xml   its entry in NME's module list
  nme-theme.xml     its panel in NME's classic theme
  check_<name>.py   its test in G1-Emu, with the patches it plays (*.pch)
```

A module asks for a type number in `modules/registry.json`, the only place that gives them. A patch keeps the
type for ever, so a number once given is never reused. The builder and NME's data pick the new folder up by
themselves.

### The limits that matter

- The G1 has **128 module types** and that cannot grow. Few are free, so small modules can share one type as
  variants.
- Each DSP has **4K words of program and 2K+2K of data**, all internal, no external RAM. Delays and reverbs of
  the G2's size do not fit a real G1; they could only run in the emulator.
- The OS update has a fixed room (shown by the meter in the [web builder](https://animatek.github.io/G1-Mods/#/builder)):
  every module you add uses some of it.

## Your first pull request

Taking an entry from the checklist to the release notes. A draft that says what it could not finish is a fine
start.

1. **Pick an entry.** Choose a module in `PORTING.md`, or propose your own. Opening an issue to say you are on it
   avoids two people doing the same one, but it is not required.
2. **Fork and branch.** Copy a small module's folder (FlipFlop or Level) as your starting point.
3. **Write it new.** Clavia's code is studied, never copied. Describe how a Clavia module works in words in your
   notes if it helps; the DSP code is yours, under a GPL-compatible licence.
4. **Test it in G1-Emu.** `./run-g1emu.sh` builds a ROM with every module on a flash of its own;
   `python3 tests/run_all.py` runs every module's test. Add a test that plays your module with a patch.
5. **Write the changelog line.** In English, in `CHANGELOG.md`, in the same commit: who, what changes, how it was
   checked.
6. **Open the pull request.** Say which type number you asked for, what works, and what is missing.

## Test before you flash

You can build, run and check nearly all of it without a synth, and a G1 always comes back.

- **In the emulator first.** A real G1 is only flashed when everything works in G1-Emu. Never flash a module that
  has not played there.
- **Every module has a test** that plays it in G1-Emu, and the cross-module checks verify the OS still builds and
  that NME's data matches.
- **The way back always exists.** The update utility is in the G1's ROM chip, which nothing here can write:
  Shift + Store at power-on reaches it whatever the flash holds
  (see [`docs/RECOVERY.md`](docs/RECOVERY.md)).
- **Before touching a real synth**, check which device NME is connected to: the real G1 or G1-Emu.

## House rules

- Nothing of Clavia's in Git: no ROM, no OS image, no DSP code copied from either.
- Everything in English: code, notes, changelog, commits.
- One folder a module, one changelog line a change.
