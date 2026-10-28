# The Nord Modular G1

A virtual-analogue modular synthesizer by Clavia, released in 1998: a rack of DSP chips you patch
from a computer, with real knobs for the parameters you assign.

## What it is

- You build the sound on screen from **modules** (oscillators, filters, envelopes, sequencers…)
  joined by cables, in an editor.
- The patch runs **inside the synth**, on its DSPs, so it keeps sounding without the computer.
- Knobs, **morphs** and MIDI controllers can be assigned to any parameter, which makes it playable.

## A short history

Clavia made the Nord Modular as a modular that runs on DSPs instead of racks of analogue boards:
you design the sound in software and the hardware plays it. Clavia stopped at 128 module types and
moved on to the Nord Modular **G2**; the G1's OS still runs today, which is what G1-Mods builds on.

## The models

- **Keyboard**: the keys plus the panel, in one instrument.
- **Rack** — the one G1-Mods targets. Four DSPs, no keyboard, patched from the editor.
- **Micro Modular**: the small one, a single DSP and a smaller panel.

## How a patch runs

The patch runs **inside the synth**, not on the computer.

- The rack has **four DSPs** (the Micro, one). A patch is spread across them as one chain, joined
  by high-speed links that carry nine words every sample.
- Modules are **control rate** (sequencers, envelopes, slow LFOs: updated less often, cheap) or
  **audio rate** (oscillators, filters: every sample). G1-Mods' first modules are control rate;
  Osc String is the first audio-rate one.
- What an editor (Animatek NME, or Clavia's) uploads is a list of modules, their parameters and
  their cables. The OS lays that out on the DSPs and runs it.

## Why add modules now

Clavia stopped at 128 module types and moved on to the G2. The G1's OS is a program like any
other: if you know where a module is registered, what its parameters are and how its DSP code is
laid out, you can add one. That is what this project does, with code written new.

## From a type number to a module

1. The OS knows each module by a **type number**. G1-Mods takes the free ones.
2. It registers the module: name, parameters, lights, inputs and outputs.
3. It adds the module's **DSP56300** code, assembled by our own tool.
4. The OS says **3.09** when an editor asks. Animatek NME then offers the new panels.

## Tools around it

- [Animatek NME](https://github.com/animatek/Animatek-NME) — the modern editor for the G1, with
  support for modified OSes.
- [G1-Emu](https://github.com/animatek/G1-Emu) — the G1 running its own OS, as a plugin or
  standalone. The test bench here.
