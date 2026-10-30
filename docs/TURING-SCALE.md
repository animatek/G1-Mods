# First patch: Turing Machine → Scale Quantizer

Your first patch with two G1-Mods modules. The **Turing Machine** loops a random pattern, the
**Scale Quantizer** snaps that pattern to a musical scale, and an oscillator plays the result.

You need a build with those two modules ticked (the builder ticks them by default), running in
G1-Emu or a real G1. The finished patch is
[`patches/turing-scale.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/patches/turing-scale.pch):
open it in Animatek NME, or build it by hand below.

## What the patch does

```
ClkGen ─clock─▶ TuringMachine ─cv─▶ ScaleQuant ─pitch─▶ OscA ─▶ 4Output
```

- **ClkGen** clocks the Turing Machine from its *4 pulses / beat* output.
- The Turing Machine's **CV** is its register's low 8 bits as a level: a value that steps on every
  clock, loops, and can be left to drift.
- The **Scale Quantizer** moves that value to the nearest note of a scale (here C, scale 1).
- **OscA**'s pitch follows the note, and the result leaves through the **4Output** (the synth's
  outputs).

## Build it by hand

1. Add a **ClkGen**, a **Turing Machine**, a **Scale Quantizer**, an **OscA** and a **4Output**.
2. Cable ClkGen *4 pulses / beat* → Turing Machine *clock*.
3. Cable Turing Machine *cv* → Scale Quantizer *in*.
4. Cable Scale Quantizer *out* → OscA *pitch 1*.
5. Cable OscA *out* → 4Output input 1.
6. Set OscA **pitch mod 1** to 127 (one control unit is then one semitone) and **freq coarse** to
   the base note you want.

## What to try

- **Prob** on the Turing Machine: to the right (127) the pattern loops; at the centre it drifts; to
  the left it flips almost every bit.
- **Lock** holds the pattern exactly as it is now.
- **Scale** (Turing Machine) tames the CV's range; **Root**, **Scale** and **Octave** (Scale
  Quantizer) pick the key and the octave.
- The Turing Machine's **gate 1–8** are one bit of the pattern each: use them to trigger envelopes
  or drums.

The oscillator drones and steps through scale notes as the pattern shifts. To make it play like an
instrument, add the keyboard's Note to OscA (or gate an AD envelope with a Turing gate). The
**8Counter** and **8Steps** are the next step: see the Clock & reset guide.
