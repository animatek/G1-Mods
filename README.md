# G1-Mods

New module types for the **Nord Modular G1**, inside the synth itself: a modified OS that adds
modules the G1 never had (a FlipFlop, a Turing Machine, a plucked string...), with their panels
in [Animatek NME](https://github.com/animatek/Animatek-NME), the editor. Each is written new,
tested in [G1-Emu](https://github.com/animatek/G1-Emu), the G1 emulator, and kept here in a
folder of its own.

> **An independent, unofficial project.** Not affiliated with, endorsed by or supported by
> Clavia. "Nord" and "Nord Modular" are Clavia's trademarks, named here only to say which
> instrument this is for.

> **Experimental on a real G1.** On one real Nord Modular G1 (2026-10-26), all 13 modules have played
> in one build. An earlier build hung at power-on and Clavia's OS had to be sent again (that
> worked). An OS update has room for every module so far (packed); every module is tested in the G1-Emu emulator. A modified OS may lose your patches and may leave your synth
> unusable. Recovery is not guaranteed. You use it entirely at your own risk; you are solely
> responsible for your instrument.

**Status: a work in progress.** Fourteen module types play in G1-Emu. On a real
G1, all 13 in one build have played (2026-10-26)
(`NOTES.md`, "The first real G1"). NME (0.25 or later) installs an OS into a G1 (its
*Device > Update Synth OS*), and the web builder is live at
<https://animatek.github.io/G1-Mods/> (`web/`).

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
| 123 | AddrSeq | Address sequencer, after Bogaudio's ADDR-SEQ: eight bipolar knobs, Steps, Start, Reverse, step LEDs. It was the 5-Step Seq. |
| 124 | Turing Machine | A looping random shift register: CV, eight gates, Prob, Length 1–16, Lock, Scale, LEDs. |
| 125 | Scale Quantizer | A pitch to the nearest note of one of 16 scales, with Root and Octave. |
| 126 | 8Counter | Eight outputs, one high a step, with Rst and LEDs. |
| 101 | Mux8-1 | Eight to one selector, by a knob and a level (the G2's Sw8-1 inside). |
| 6 | Random | The G2's randoms in one: Seed, Poly, Step, Edge, Prob, Length, Uni/Bi. |
| 41 | Bits | Binary counter, analogue to digital and digital to analogue. |
| 42 | Level | ModAmt, MinMax, Track and Hold, Window. |
| 55 | Envelope | ADDSR, or one shot (D, H, AHD). |
| 56 | Osc String | A plucked string (Karplus-Strong), the first audio-rate module. |
| 60 | Note Out | A gate and a note out of the G1's MIDI OUT, as the G2's NoteSend: Chan, Vel, Gate thru. |
| 122 | CtrlSend | A control change out of the G1's MIDI OUT, as the G2's CtrlSend: Ctrl, Value, Chan, In and Send. |

Each has a test that plays it in G1-Emu. What is left of each, and the G2's modules still to port,
are in [`PORTING.md`](PORTING.md). Four types are still free (93, 109, 116, 119), so the
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
  [`CONTRIBUTING.md`](CONTRIBUTING.md): how to take part. [`PORTING.md`](PORTING.md): the plan. [`CHANGELOG.md`](CHANGELOG.md): what changed.

## Trying it

You need a G1-Emu built from source next to this folder (`../G1-Emu`), with your own 3.03 ROM in
its `Roms/`, and **Animatek NME 0.25 or later** (the G1-Mods layer is in its `main`).

```sh
./run-g1emu.sh             # G1-Emu with every new module, on a flash of its own
python3 tests/run_all.py   # every module's test in G1-Emu
tools/patch_rom.py flipflop,mux8 <your 3.03 ROM> Roms/rom-mine.bin   # only some modules
```

Close your usual G1-Emu first: both take the same MIDI ports. Your usual flash is not touched.

## The web builder

`web/` is the builder as a web page: you pick your ROM, tick the modules, and it gives you the
OS update, which both G1-Emu and a real G1 take through update mode, and a ROM, for G1-Emu alone. It runs **in your browser** (the same Python
as `tools/patch_rom.py`, through Pyodide), so nothing is uploaded and the result is byte for byte
the command line's.

- **On the web: <https://animatek.github.io/G1-Mods/>** (GitHub Pages; built from `main` by
  `.github/workflows/deploy-pages.yml`).
- **On your own computer:**

```sh
web/serve.sh               # then open http://localhost:8090
```

It needs the internet once, to load Pyodide. `web/make_bundle.py` packs the modules into
`web/bundle.json` (ignored; `serve.sh` and the Pages workflow each make it). The workflow packs
it from the committed DSP caches (`out/dspasm-*.json`), so it needs no G1-Emu; edit an `.asm`
and run `web/serve.sh` locally first to refresh its cache.

## Installing

[`docs/INSTALL.md`](docs/INSTALL.md): building your OS, trying it in G1-Emu and installing it on a
real G1 with NME, step by step. [`docs/RECOVERY.md`](docs/RECOVERY.md): going back to Clavia's OS
and what to do when something goes wrong.

## Where the builds are

Everything built goes into **`Roms/`**, next to this README. Git ignores the whole folder (it
holds Clavia's code), so it is never uploaded: it lives only on your computer.

| File | What it is | What it is for |
| --- | --- | --- |
| `Roms/rom-all.bin` | The G1's whole ROM (512 KB) with **every** new module (all the types in the table above). | Booting G1-Emu with the modules: `./run-g1emu.sh` does it. |
| `Roms/os-all.bin` | The same OS alone, as an update image (393,184 bytes, what an update has room for; the modules go packed). Made only when it fits (`NOTES.md`, "The first real G1"). | Putting it into a G1's flash like an OS update: NME's *Device > Update Synth OS*. |
| `Roms/flash-all.bin` | The flash G1-Emu uses with that ROM: the patches you save there. | Kept apart from your usual G1-Emu flash, which is never touched. |
| `Roms/clavia-original/` | Clavia's 3.03b OS: `clavia-3.03b-os.bin`, the image (`g1update.py unpack` of the `.syx` beside it, recorded from G1-Emu on 2026-10-25). | The way back: Shift + Store at power-on, then NME's *Update Synth OS* with `clavia-3.03b-os.bin`, Safe. It brought a real G1 back on 2026-10-26. |
| `Roms/works-on-real-g1/` | Only the OS images that have booted on a real G1, with a `README.txt` saying which is which. | What to install on a real G1, and the way back to Clavia's OS. |
| `Roms/tests/` | Images built to try one thing on a real G1 (a module alone, a set without one). | Each says in `NOTES.md` what it tries. |
| `Roms/old/` | Earlier experiments (Note Out's tries, the first FlipFlop, audio tests...) and flashes kept aside. | Nothing; kept only to look back. It can be deleted. |

`./run-g1emu.sh` **rebuilds `rom-all.bin` and `os-all.bin` every time it starts**, from G1-Emu's
own ROM and the modules as they are now, so the two are always the current ones and always in
step. Another selection gets its own names: `./run-g1emu.sh flipflop` writes `rom-flipflop.bin`,
`os-flipflop.bin` and `flash-flipflop.bin`. By hand:

```sh
tools/patch_rom.py all ../G1-Emu/Roms/NORD-MODULAR-RACK-VER-3.03.BIN Roms/rom-all.bin
tools/g1update.py fromrom Roms/rom-all.bin Roms/os-all.bin
```

**The Micro Modular is not offered.** Its OS builds and runs in G1-Emu's Micro model (`NOTES.md`, "The
Micro Modular"), but nobody knows what a real Micro does with an OS update, so the web builder and these
guides leave it out until someone with a Micro can try one.

`out/` is something else: the tools' working files (the DSP assembler's index, NME data copies).
No ROM goes there.

## Who is responsible for what

We make the tool. We are not responsible for anyone's G1, nor for the modules others write.

- **Works in the emulator only.** Tried once on a real G1, it did not boot (2026-10-26). Until this
  says otherwise, a build may not work on a real G1 and may leave it unusable. Recovery is not
  guaranteed.
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
