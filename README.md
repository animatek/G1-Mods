# G1-Mods

New module types for the **Nord Modular G1**, inside the synth itself: a modified OS that adds
modules the G1 never had (a FlipFlop, a Turing Machine, a plucked string...), with their panels
in [Animatek NME](https://github.com/animatek/Animatek-NME), the editor. Each is written new,
tested in [G1-Emu](https://github.com/animatek/G1-Emu), the G1 emulator, and kept here in a
folder of its own.

> **An independent, unofficial project.** Not affiliated with, endorsed by or supported by
> Clavia. "Nord" and "Nord Modular" are Clavia's trademarks, named here only to say which
> instrument this is for.

> **Tested only in the G1-Emu emulator.** It has never been tried on a real Nord Modular G1. A
> modified OS may not work on real hardware, may lose your patches and may leave your synth
> unusable. Recovery is not guaranteed. You use it entirely at your own risk; you are solely
> responsible for your instrument.

**Status: a work in progress, private for now.** Twelve module types play in G1-Emu. There is no
builder for users yet, nor a way to send the OS to a real G1.

## How it works

The G1's OS knows each module by a **type number**, and there are only 128 of them: Clavia used
almost all. G1-Mods takes the free numbers (and a few Clavia never finished), and for each one
adds to the OS what a module needs: its registration, its parameters and lights, and its
DSP56300 code, ours. The OS then runs our modules as it runs Clavia's.

Nothing here contains Clavia's firmware. The tools take **your own OS file**, add the modules to
it on your computer, and write the result outside the repo. A built OS says **version 3.09** when
an editor asks (instead of Clavia's 3.03), so NME knows that synth has the new modules and offers
them only to it; next to it, a G1 with Clavia's OS works as always. Clavia's own editor still
connects to a 3.09.

## The modules

| Type | Module | What it does |
| --- | --- | --- |
| 120 | FlipFlop | D-type and RS-type flip-flop: Clk, In, Rst, Q and NotQ. |
| 121 | Mix1-1A | One-input chain mixer, as the G2's (its Lin/dB/Exp curves still missing). |
| 123 | 5-Step Seq | Five bipolar knobs, one a step, with step LEDs. |
| 124 | Turing Machine | A looping random shift register: CV, eight gates, Prob, Length 1–16, Lock, Scale, LEDs. |
| 125 | Scale Quantizer | A pitch to the nearest note of one of 16 scales, with Root and Octave. |
| 126 | 8Counter | Eight outputs, one high a step, with Rst and LEDs. |
| 101 | Mux8-1 | Eight to one selector, by a knob and a level (the G2's Sw8-1 inside). |
| 6 | Random | The G2's randoms in one: Seed, Poly, Step, Edge, Prob, Length, Uni/Bi. |
| 41 | Bits | Binary counter, analogue to digital and digital to analogue. |
| 42 | Level | ModAmt, MinMax, Track and Hold, Window. |
| 55 | Envelope | ADDSR, or one shot (D, H, AHD). |
| 56 | Osc String | A plucked string (Karplus-Strong), the first audio-rate module. |

Each has a test that plays it in G1-Emu. What is left of each, and the G2's modules still to port,
are in [`PORTING.md`](PORTING.md). Six types are still free (60, 93, 109, 116, 119, 122), so the
catalogue grows by families: one type, several panels in NME.

## Layout

- `modules/<name>/`: one folder a module, with everything it needs: its type and names
  (`module.json`), how it goes into the OS (`build.py`), its DSP code (`*.asm`), its entries for
  NME, and its test with the patches it plays. See [`modules/README.md`](modules/README.md).
- `modules/registry.json`: the type each module has, **for ever**. A patch stores a module's type,
  so a number once given is never given to another module. This file is the only place they are
  given.
- `tools/`: `patch_rom.py` builds the modules into your OS, `make_nme_data.py` writes NME's data,
  `g1rom.py` is what every module's build uses, `dspasm.py` the DSP assembler.
- `tests/`: the tests across modules, and `run_all.py`, which runs them all.
- [`NOTES.md`](NOTES.md): how it was worked out, the OS's insides, step by step.
  [`PORTING.md`](PORTING.md): the plan. [`CHANGELOG.md`](CHANGELOG.md): what changed.

## Trying it

You need a G1-Emu built from source next to this folder (`../G1-Emu`), with your own 3.03 ROM in
its `Roms/`, and NME built from its `mods-layer` branch (`run-nme.sh` says how).

```sh
./run-g1emu.sh             # G1-Emu with every new module, on a flash of its own
./run-nme.sh               # NME, which offers them to that synth
python3 tests/run_all.py   # every module's test in G1-Emu
tools/patch_rom.py flipflop,mux8 <your 3.03 ROM> out/rom-mine.bin   # only some modules
```

Close your usual G1-Emu first: both take the same MIDI ports. Your usual flash is not touched.

## Who is responsible for what

We make the tool. We are not responsible for anyone's G1, nor for the modules others write.

- **Tested only in the emulator.** Until this says otherwise, nothing has been tried on a real G1:
  a build may not work on one, and it may leave it unusable. Recovery is not guaranteed.
- **Each owner is responsible for their own G1.** When there is a builder, its button stays off
  until you tick that you have read the risks.
- **No support for real hardware.** Provided as is, without warranty of any kind (GPLv3, sections
  15 and 16). Issues are for bugs in the tool and the modules, with no promise of an answer or a
  fix. Say in each report which build, which OS version, and whether it was G1-Emu or a real G1.
- **Community modules live in their authors' repos**, not in this one. Each author owns their
  module, its licence and its support. A module is linked only after we try it in G1-Emu, pinned
  to the version we tried, so later changes do not reach anyone until they are reviewed again.
  Being linked is not a guarantee: report its problems to its author.
- **Type numbers are given only here**, in `modules/registry.json`: an author asks for one when
  their module is linked.

## Firmware and rights

- **Nothing of Clavia's is in this repo, and nothing of Clavia's may come into it**: no ROM, no
  OS image, original or built, and no code copied from the G1's OS or from the G2's. Clavia's code
  is studied, not copied; our modules are written new, and the notes describe the OS in words.
- **Do not upload, share or redistribute OS images, original or built**: they contain Clavia's
  copyrighted firmware. Share your list of modules instead; anyone with their own OS can build
  the same one.
- **No rights to Clavia's firmware or trademarks are given** by anything here.

## Licence

GPLv3, as G1-Emu (see [`LICENSE`](LICENSE)). Every module carries its licence in its
`module.json` (ours: `GPL-3.0-only`); a community module must have an open licence that allows it
to be built into a user's OS (GPL-compatible), with its file in its repo.

**Open and free, for good.** Everything here is open source and meant to be as collaborative as
possible. No module, build or early access is ever exclusive to Patreon or paid: Patreon only
supports the work, for whoever wants to.

## Credits

G1-Mods stands on [Gearmulator](https://github.com/dsp56300/gearmulator): G1-Emu, its test
bench, is built on Gearmulator's emulation core and its DSP56300. Thanks to its authors, and to
joelanders for the fork that started G1-Emu.

Made by Animatek (Javier), with Claude.
