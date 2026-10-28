# Connect Animatek NME to G1-Emu

The safe way in: try every build and patch in **G1-Emu** before anything touches a real G1. This
walks through starting G1-Emu with a G1-Mods OS and connecting **Animatek NME** to it.

## What you need

- A build: the web builder's ROM, or `tools/patch_rom.py` (see the install guide).
- **G1-Emu**, built (this repo's test bench).
- **Animatek NME** with the G1-Mods layer: it offers the new modules to a synth whose OS reports
  3.09 on connecting.

## 1. Start G1-Emu with the build

Close any G1-Emu that is already running: both would take the same MIDI ports. From this repo:

```
./run-g1emu.sh
```

It builds the ROM into `Roms/rom-all.bin`, makes its own flash (your usual flash is never touched)
and opens G1-Emu's window with that ROM. By hand it is the same: start G1-Emu with your built ROM
and a scratch flash.

## 2. Connect NME

In NME, choose G1-Emu's **PC Port** as the MIDI input and output — the editor port, the same one
you would use for a real G1.

## 3. What you should see

- NME's status bar says **MODDED OS**, and the synth reports version **3.09**.
- The new modules are in the palette — TuringMachine, ScaleQuant, 5-StepSeq, 8Counter and the rest
  — under their own category.

## 4. Open a patch

Open
[`patches/turing-scale.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/patches/turing-scale.pch)
and you hear the oscillator stepping through scale notes. Every module folder also has a patch of
its own (`modules/<name>/*.pch`).

The same steps on a real G1 — plus installing the OS with *Device > Update Synth OS* — are in the
install guide.
