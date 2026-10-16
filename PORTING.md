# Porting the G2's modules to the G1

The checklist: every module the G2 has and the G1 does not, plus the G2 versions of modules the
G1 already has when they do more. Updated as modules get ported. How a module is built:
`NOTES.md`; the G1↔G2 equivalences: `../G2-Emu/MODULOS.md`.

**Status:** ✅ done and checked in G1-Emu · 🟡 partly done · ⬜ to do · ✖ not doing.

**Feasible?** What a real G1 allows, which is the limit that matters:

- **Easy**: small code, control rate or a few audio words, no memory beyond a few X words.
- **Medium**: more code (50–150 DSP words), several parameters or lights, or a short buffer.
- **Hard**: needs 68k work beyond a registration (MIDI in or out, voice handling), or no
  reference to study (the demo leaves it out).
- **Emulator only**: needs memory a real G1 does not have. Each G1 DSP is a 56303 with
  **4K words of program and 2K+2K of data, all internal, no external RAM**: at 96 kHz 2K words
  are about 21 ms of audio, shared by every module of the voice. The G2's delays (up to 2.7 s)
  and its reverb do not fit; in G1-Emu the DSPs could be given more memory, but a patch with
  them would never run on hardware.
- **No**: the G1 lacks the hardware (four audio inputs) or it is not a module.

**DSP words** is the size of the module's code in the G2 demo (its parts added, approximate):
a guide to the effort, not code to copy. Our code is written new.

## Already on the G1-Mods OS

| Module | G1-Mods type | Status | What is missing |
| --- | --- | --- | --- |
| Mixer 1-1 A (Mix1-1A) | 121 | 🟡 | Level, Ch 1 button and chain work (checked). Missing: the Lin / dB / Exp curves (needs a 68k routine of our own; see `NOTES.md`). |
| FlipFlop | 120 | ✅ | D-type and RS-type, Clk, In, Rst, Q and NotQ (`dsp/flipflop.asm`; `tests/check_flipflop.py`). |
| Noise S&H (our own) | 122 | ✅ | `dsp/noise_sh.asm`, `tests/check_noise_sh.py`. Every voice starts from the same seed, so in a poly patch they draw the same sequence. |
| Mixer Inv (test only) | 119 | ✅ | Not a G2 module: the first test, the Mixer (3) with input 1 inverted. |

## Modules only the G2 has

### Logic

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| FlipFlop | 9 + latch 17–18 | Easy | ✅ | See above. |
| 8Counter | 34 | Easy | ⬜ | Eight outputs, one high per clock; reset. The one most asked for. |
| BinCounter | 36 | Easy | ⬜ | Binary counter, several outputs. |
| ADConv | 31 | Easy | ⬜ | Level to 8 logic bits. |
| DAConv | 29 | Easy | ⬜ | 8 logic bits to a level. |

### Switches and selectors

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Sw1-2, Sw2-1 | 6–7 | Easy | ⬜ | |
| Sw1-2M, Sw2-1M | 6–7 | Easy | ⬜ | Momentary versions. |
| Sw1-8, Sw8-1 | 15–16 | Easy | ⬜ | The G1 has 1-4 and 4-1 only. |
| SwOnOffM | 5 | Easy | ⬜ | Momentary on/off. |
| ValSw1-2, ValSw2-1 | 9–12 | Easy | ⬜ | Switched by a control value. |
| Mux1-8, Mux8-1, Mux8-1X | 14–57 | Easy | ⬜ | Selected by a control input; the X one crossfades. |
| WindSw | 11 | Easy | ⬜ | Window switch. |
| T&H | 7 | Easy | ⬜ | Track and hold. |

### Level

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| MinMax | 7 | Easy | ⬜ | |
| ModAmt | 9 | Easy | ⬜ | The G2's most used modulation helper. |
| ConstSwT, ConstSwM | ~5 | Easy | ⬜ | Constant with a toggle / momentary switch. |
| Red2Blue, Blue2Red | 2–9 | Easy | ⬜ | Audio-rate ↔ control-rate converters. |

### Mixers

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Mixer 1-1 A | 5–8 | Easy | 🟡 | Type 121, see above. |
| Mixer 1-1 S | ~8 | Easy | ⬜ | Stereo chain mixer: the Mix1-1A in stereo. |
| Mixer 2-1 B, 4-1 C, 4-1 S | 5–11 | Easy | ⬜ | With Lin/dB/Exp and channel buttons; same work as the curves of Mix1-1A. |
| MixStereo | 43 | Easy | ⬜ | Six inputs with pan. |
| MixFader | ~15 | Easy | ⬜ | Eight inputs, fader style. |

### Envelopes

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Envelope H | 14 | Medium | ⬜ | Hold only. |
| Envelope D | 15 | Medium | ⬜ | Decay only. |
| Envelope ADDSR | ~86 | Medium | ⬜ | |
| Envelope Mod AHD | 61 | Medium | ⬜ | AHD with modulation inputs. |

### Oscillators

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Osc Shape A, Osc Shape B | 60–150 | Medium | ⬜ | Waveshaped oscillators. |
| Osc D | ~60 | Medium | ⬜ | |
| Osc Dual | ~120 | Medium | ⬜ | Two oscillators in one. |
| Osc Phase Mod | ~60 | Medium | ⬜ | |
| Noise Osc | ~60 | Medium | ⬜ | Tuned noise. |
| Metallic Noise | 60 | Medium | ⬜ | |
| Driver, Resonator | ~60 | Medium | ⬜ | Physical-model parts. |
| Osc String | 221 + delay | Hard | ⬜ | Karplus-Strong: the string is a delay line; 2K words reach down to ~47 Hz, so it fits, but it is the biggest code here. |
| FM Operator, DX Router | 50–130 | Hard | ⬜ | The demo blocks and leaves them out: no reference until the G2 firmware is read. |

### Filters and EQ

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Eq 3-band | ~50 | Medium | ⬜ | |
| WahWah | 34 | Medium | ⬜ | |
| Phase Filter | ~135 | Medium | ⬜ | |
| Comb Filter | 121 + buffer | Medium | ⬜ | Needs a short delay: fits down to ~47 Hz. |

### Effects

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Flanger | ~57 | Medium | ⬜ | A few ms of delay: fits. |
| FreqShift | ~126 | Medium | ⬜ | Bode shifter, no long memory. |
| PShift | ~150 + buffer | Hard | ⬜ | Needs tens of ms; at the limit of 2K words. |
| Scratch | ~80 + buffer | Hard | ⬜ | |
| Reverb | 387 + long buffers | Emulator only | ⬜ | The G2's long reverb needs far more memory than a G1 DSP has. A small one of our own does fit: see "New modules of our own". |

### Delays

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| DlyShiftReg | 40 | Easy | ⬜ | Eight clocked steps: memory of 8 words. |
| Delay Clock | 47 | Medium | ⬜ | Clocked delay. |
| Delay Single A/B, Dual, Quad, Eight, Stereo, Delay A/B | 25–82 | Emulator only (long) · Medium (short) | ⬜ | On a G1, up to ~20 ms shared by the voice: chorus/comb lengths, not echoes. Full length only in G1-Emu with more memory. |

### Sequencers, notes, random, LFO

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Sequencer Values | ~72 | Medium | ⬜ | Many parameters; the step LED is now understood (see the comparison below). |
| Sequencer Controlled | ~72 | Medium | ⬜ | |
| Zero Crossing Counter | ~23 | Medium | ⬜ | |
| Pitch Tracker | ~25 | Medium | ⬜ | |
| Rnd Clock B | ~100 | Medium | ⬜ | Random clock with "character". |
| LFO Shp A | 200 | Medium | ⬜ | LFO with shape modulation. |
| Saturate | 43 | Easy | ⬜ | |

### Sequencers: G1 and G2 compared

| | G1 (NoteSeqA/B, EventSeq, CtrlSeq) | G2 (Sequencer Note, Event, Values, Level, Controlled) |
| --- | --- | --- |
| Steps | 16 | 16 |
| A gate row per step | EventSeq only (two gate rows) | every one: a value and a gate per step |
| Chaining | a `link` output | Chain inputs and outputs: modules in series make 32, 48… steps |
| Play mode | loop | loop or Cycle (one pass) |
| Step chosen by a voltage | no | Sequencer Controlled: a control input picks the step |
| Buttons | Record/Pause (NoteSeqA) | Clr and Rnd (clear, randomise), Polarity |

All of it is feasible with what is known (parameters written to X per index, the step LED as a
`led-array`: see `NOTES.md`, "How a module's lights reach the editor"). Medium, because of the
number of parameters (16 values + 16 gates + the rest) and the panels. Clr and Rnd can be done in
the editor (NME writes the parameters), with nothing in the OS.

### MIDI

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| CtrlSend, PCSend, NoteSend | 20–26 | Hard | ⬜ | The DSP part is small; the 68k must read it and send MIDI. Also needs the MIDI OUT path that G1-Emu does not have yet. |
| CtrlRcv, NoteRcv | 4–5 | Hard | ⬜ | The 68k must route incoming MIDI into the module. |
| Automate | 1 | Hard | ⬜ | |

### Not doing

| Module | Why |
| --- | --- |
| 4 Inputs | The G1 has two audio inputs (its AudioIn is the G2's 2 Inputs). |
| Sampler | Not Clavia's: G2-Edit's own module. |
| Device, Name Bar, Status | Not sound modules. |

## New modules of our own (neither the G1 nor the G2 has them)

Ideas built from what is known now. Same scale of feasibility.

| Module | What it does | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Noise S&H | Sample and hold with its own noise: on Trig's rising edge it holds a random value; outputs **Out** and **Inv** (the same value negated, for mirrored melodies). | Easy | ✅ (type 122) | A shift-register noise in a few DSP words, its state per voice in X, so each voice of a poly patch draws its own. One logic input, two outputs. |
| 5-step sequencer | Clk, Rst, one control output and **five bipolar knobs** (−64…+63), after Buchla's 5-stage sequencers (with knobs instead of sliders). | Easy–Medium | ⬜ | Five parameters written to X by the type's own `+$04` (the same routine as the FlipFlop's Type, per parameter). Step LEDs: understood now, from the CtrlSeq (`NOTES.md`, "How a module's lights reach the editor"): a value routine registered with `$1169BA` that reads the step from X. Worth checking which extras Buchla's had (a pulse out per step, an input that picks the step), cheap to add. |
| Turing Machine | After Music Thing Modular's: a looping shift register whose bits may flip at random. Clk (and Rst); outputs **CV** (the low 8 bits as a level) and **Gate** (bit 0); a **probability** knob (locked at one end, random in the middle, locked and inverted, twice as long, at the other), a **Lock** button as a shortcut, and a **length** (2–16 steps); **8 LEDs**, one per bit. | Easy–Medium | ⬜ | Cheap for the DSP: the register fits in one word (24 bits) and a clock costs ~20 instructions; the coin toss reuses the Noise S&H's noise. Its 8 LEDs are the hard part: the G1's OS keeps **one plain LED per module** (`NOTES.md`, "Plain LEDs"). Options: the meter list (a `led-array` 0–255 showing the register, drawn by NME as 8 LEDs), which also gives the FlipFlop a NotQ LED. Idea from Javier, 2026-10-16. |
| Small reverb | A short room or plate: a few combs and allpasses, run at a lower rate (24 kHz) to stretch the memory. | Hard | ⬜ | At 24 kHz the 4K data words of one DSP make ~170 ms of delay line, enough for a small Schroeder-type reverb, but it takes nearly all of that DSP's memory, so a patch with it gets fewer voices. Not the G2's long hall. The G1 patches that already make a reverb from many short Delays prove short networks work. |

## G2 versions of modules the G1 has, that do more

| G2 module | G1 module | What the G2's adds | Feasible | Status |
| --- | --- | --- | --- | --- |
| Random A | RndStepGen | Mono/Poly, rate range, Step and Edge amounts | Medium | ⬜ |
| Random B | RandomGen | Poly, rate range, KBT, Step, Edge | Medium | ⬜ |
| Rnd Clock A | ClkRndGen | Seed (repeatable sequences), Poly, Step, reset | Medium | ⬜ |
| Rnd Trig | RndPulsGen | Clocked, Seed, probability | Medium | ⬜ |
| Rnd Pattern | PatternGen | Pattern A/B, Step/Prob, loop length | Medium | ⬜ |
| Mixers (all) | Mixer (3), Mixer (8) | Lin / dB / Exp curves, channel buttons, chain | Easy once the curves are done | 🟡 (Mix1-1A) |
| FlipFlop | — | (see above) | Easy | ✅ |
| Envelopes | ADSR, AHD… | Shapes per segment, more modulation | Medium | ⬜ |

## Order proposed

1. **Finish what is half done:** the Lin/dB/Exp curves
   (with a 68k assembler, `vasm`): that unlocks every G2 mixer.
2. **The easy batch:** 8Counter, switches and muxes, MinMax, ModAmt, T&H, Saturate,
   DlyShiftReg. Mostly logic and control rate.
3. **The randoms**, G2 versions (Seed, Poly, Edge): new modules beside the G1's.
4. **Medium audio:** Flanger, Comb Filter, WahWah, Eq 3-band, the new oscillators.
5. Later, if ever: MIDI modules (68k work), PShift and Scratch, and the long delays and the
   reverb as G1-Emu-only.
