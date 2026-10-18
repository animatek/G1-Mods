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

## Only eleven types left

**The G1 has room for 128 module types (0–127), and that cannot grow**: the OS's table has 128
entries and a patch keeps a module's type in 7 bits. Clavia's take 110 of them; G1-Mods uses 6, 41, 42, 55, 56, 101,
120, 121 and 123–126. **Free now: 60, 93, 109, 116, 119, 122** (0 is left out:
it may read as "no module"). Found 2026-10-17, when 127 and 128 were about to be used (127 is the
PolyAreaIn); the same day the Mixer Inv (119, a first test) and the Noise S&H (122, easy to patch
from G1 modules) were taken out to free theirs (in git history). So far fewer G2 modules can come
than this list has, and they have to be chosen:

- **Variants share a type**: a mode button or a knob instead of a module each (the Mux8-1 is the
  G2's Mux8-1 and Sw8-1 at once). Small modules only: every instance loads the DSP code of all
  its modes.
- **Virtual modules in NME** (to do): NME shows each variant as a module of its own, with its
  panel and name, and writes them all as one type with a hidden parameter that fixes the mode.
  One type then gives a family of 4–6 small modules.
- **What a G1 module already does well is not ported again.**
- `patch_rom.py` refuses a type not in `FREE_TYPES`.
- **Room for code is the other limit (2026-10-17)**: the package runs from 14 KB of RAM the OS
  never touches; with the Osc String the twelve types take 13,460 bytes, under 900 left. The
  next big module needs more room found first (`NOTES.md`, "Room for code"), or the builder.
- Not doing: widening the type to more bits (the OS's loader, connections, patch and SysEx, and
  NME): a great deal of reverse engineering and patches nothing else could read. At most, a day
  to see whether the OS keeps the type in a whole byte inside.

**The plan agreed with Javier (2026-10-17): a type per family, not per module**, with the virtual
modules of NME. Two families go into types G1-Mods already uses: a type can have the inputs and
outputs of all its variants and each panel shows its own.

| Type | Family |
| --- | --- |
| 101 (Mux8-1) | Switches: Sw1-2, Sw2-1, Sw1-8, Mux1-8, the momentary ones |
| 121 (Mix1-1A) | The G2's mixers with Lin/dB/Exp |
| 6 (Random) | Random: one clocked module does Random A/B (Out, Step, Edge), Rnd Trig (Prob) and Rnd Pattern (Seed, Length); done 2026-10-17 |
| 41 (Bits) | Conversion and logic: BinCounter, ADConv, DAConv in one module with a Mode selector and every connector (no virtual modules needed); done 2026-10-17 |
| 42 (Level) | Level: ModAmt, MinMax, T&H and WindSw in one module with a Mode selector; done 2026-10-17 |
| 55 (Envelope) | Envelopes: one engine, ADDSR in Gate mode, one shot (D, H, AHD) in Trig mode; done 2026-10-17 |
| the other 7 | Big modules, one a type (oscillators, effects): Javier's list of 5–6 by preference, and one or two kept back. Two big ones share a type only if they share most of their code (a Flanger and a Phaser): every instance loads the code of all its modes. The DSP's memory per voice limits a patch more than the types do. |

## Already on the G1-Mods OS

| Module | G1-Mods type | Status | What is missing |
| --- | --- | --- | --- |
| Mixer 1-1 A (Mix1-1A) | 121 | 🟡 | Level, Ch 1 button and chain work (checked). Missing: the Lin / dB / Exp curves (needs a 68k routine of our own; see `NOTES.md`). |
| FlipFlop | 120 | ✅ | D-type and RS-type, Clk, In, Rst, Q and NotQ (`modules/flipflop/flipflop.asm`; `modules/flipflop/check_flipflop.py`). |
| 5-Step Seq (our own) | 123 | ✅ | Clk, Rst, Out, five bipolar knobs and a row of five step LEDs (`modules/step-seq-5/seq5.asm`, `modules/step-seq-5/check_step_seq_5.py`). |
| Turing Machine (our own) | 124 | ✅ | Clk, CV, 8 gates (bits 0–7), Prob (bipolar, as the original's big knob), Length 1–16, Lock, Scale and 8 LEDs (`modules/turing-machine/turing.asm`, `modules/turing-machine/check_turing_machine.py`). Missing: a Rst, and the expander's mixes (1+2, 2+4, 4+7, 1+2+4+7). |
| Scale Quantizer (our own) | 125 | ✅ | In, Out, Root, Scale (16 by name) and Octave, after JW-Modules' Quantizer (`modules/scale-quantizer/quant.asm`, `modules/scale-quantizer/check_scale_quantizer.py`). Missing: CV inputs for Root and Scale. |
| 8Counter | 126 | ✅ | Clk, Rst (as the G1's sequencers'), eight outputs, one high a step, and eight step LEDs (`modules/counter8/counter8.asm`, `modules/counter8/check_counter8.py`). |
| Mux8-1 (with the Sw8-1) | 101 | ✅ | In 1–8, Ctrl, Out, a Sel knob that Ctrl adds to (8 units a step), eight LEDs (`modules/mux8/mux8.asm`, `modules/mux8/check_mux8.py`). Control rate. |
| Random (the G2's randoms in one) | 6 | ✅ | Clk, Rst, Out, Trig; Seed, Poly, Step, Edge, Prob, Length, Uni/Bi (`modules/random/random.asm`, `modules/random/check_random.py`). Poly checked by Javier by ear (2026-10-17: the voices play different sequences). |
| Bits (BinCounter, ADConv, DAConv) | 41 | ✅ | Clk, Rst, In, B1–B8; Out, Bit 1–8; Mode (Count, A>D, D>A); eight LEDs (`modules/bits/bits.asm`, `modules/bits/check_bits.py`). |
| Level (ModAmt, MinMax, T&H, WindSw) | 42 | ✅ | A, B; Out 1, Out 2; Mode, Amount, Lo, Hi (`modules/level/level.asm`, `modules/level/check_level.py`). Control rate. |
| Envelope (ADDSR, H, D, AHD) | 55 | ✅ | Gate; Env, End; Gate/Trig, Attack, Decay 1, Level 1, Decay 2, Sustain, Release (`modules/envelope/env.asm`, `modules/envelope/check_envelope.py`). Control rate; no time modulation inputs (the Mod AHD's) yet. |
| Osc String | 56 | ✅ | Trig, Pitch, Exc; Out; Note, Decay, Damp (`modules/osc-string/string.asm`, `modules/osc-string/check_osc_string.py`). Audio rate. Lowest note about 94 Hz (a 1,024-word line); lower would need the line run at half or a quarter of the rate. Javier played it (2026-10-17): it works. |

## Modules only the G2 has

### Logic

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| FlipFlop | 9 + latch 17–18 | Easy | ✅ | See above. |
| 8Counter | 34 | Easy | ✅ | Type 126, see above. |
| BinCounter | 36 | Easy | ✅ | Binary counter, several outputs. |
| ADConv | 31 | Easy | ✅ | Level to 8 logic bits. |
| DAConv | 29 | Easy | ✅ | 8 logic bits to a level. |

### Switches and selectors

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| Sw1-2, Sw2-1 | 6–7 | Easy | ⬜ | |
| Sw1-2M, Sw2-1M | 6–7 | Easy | ⬜ | Momentary versions. |
| Sw1-8, Sw8-1 | 15–16 | Easy | 🟡 | Sw8-1: in the Mux8-1 (type 101), its Sel knob. Sw1-8 to do. |
| SwOnOffM | 5 | Easy | ⬜ | Momentary on/off. |
| ValSw1-2, ValSw2-1 | 9–12 | Easy | ⬜ | Switched by a control value. |
| Mux1-8, Mux8-1, Mux8-1X | 14–57 | Easy | 🟡 | Mux8-1: type 101. Mux1-8 and the crossfading X to do. |
| WindSw | 11 | Easy | ✅ | Window switch. |
| T&H | 7 | Easy | ✅ | Track and hold. |

### Level

| Module | DSP words | Feasible | Status | Notes |
| --- | --- | --- | --- | --- |
| MinMax | 7 | Easy | ✅ | |
| ModAmt | 9 | Easy | ✅ | The G2's most used modulation helper. |
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
| Envelope H | 14 | Medium | ✅ | Hold only. |
| Envelope D | 15 | Medium | ✅ | Decay only. |
| Envelope ADDSR | ~86 | Medium | ✅ | |
| Envelope Mod AHD | 61 | Medium | 🟡 | AHD with modulation inputs. |

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
| Osc String | 221 + delay | Hard | ✅ | Karplus-Strong: the string is a delay line; 2K words reach down to ~47 Hz, so it fits, but it is the biggest code here. |
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
| Noise S&H | Sample and hold with its own noise: on Trig's rising edge it holds a random value; outputs **Out** and **Inv** (the same value negated, for mirrored melodies). | Easy | ✖ (was type 122, taken out 2026-10-17: easy to patch from G1 modules) | A shift-register noise in a few DSP words, its state per voice in X, so each voice of a poly patch draws its own. One logic input, two outputs. |
| 5-step sequencer | Clk, Rst, one control output and **five bipolar knobs** (−64…+63), after Buchla's 5-stage sequencers (with knobs instead of sliders). | Easy–Medium | ✅ (type 123) | Five parameters written to X by the type's own `+$04` (the same routine as the FlipFlop's Type, per parameter). Step LEDs: understood now, from the CtrlSeq (`NOTES.md`, "How a module's lights reach the editor"): a value routine registered with `$1169BA` that reads the step from X. Worth checking which extras Buchla's had (a pulse out per step, an input that picks the step), cheap to add. |
| Turing Machine | After Music Thing Modular's: a looping shift register whose bits may flip at random. Clk (and Rst); outputs **CV** (the low 8 bits as a level) and **Gate** (bit 0); a **probability** knob (locked at one end, random in the middle, locked and inverted, twice as long, at the other), a **Lock** button as a shortcut, and a **length** (2–16 steps); **8 LEDs**, one per bit. | Easy–Medium | 🟡 (type 124) | Cheap for the DSP: the register fits in one word (24 bits) and a clock costs ~20 instructions; the coin toss reuses the Noise S&H's noise. Its 8 LEDs are the hard part: the G1's OS keeps **one plain LED per module** (`NOTES.md`, "Plain LEDs"). Options: the meter list (a `led-array` 0–255 showing the register, drawn by NME as 8 LEDs), which also gives the FlipFlop a NotQ LED. Idea from Javier, 2026-10-16. |
| Scale Quantizer | After JW-Modules' Quantizer (Javier, 2026-10-17): a pitch to the nearest note of a scale picked by name on a root, easier than the G1's KeyQuant and its twelve buttons. | Easy | ✅ (type 125) | A 12-word table per scale, written by the Scale routine; the mod 12 by a multiply. |
| Scope | Shows a signal's waveform in the editor. | Hard (real G1) · Medium (G1-Emu) | ⬜ | The DSP can capture a block of samples into X; getting it to the editor is the hard part: the OS sends module values a few times a second and 7 bits at a time (`Meters`), far too little for a waveform, so a real G1 would need a new SysEx message from the 68k. In G1-Emu the emulator can read the DSP's memory itself and send it to NME over the direct link. Javier's idea, 2026-10-16. |
| Small reverb | A short room or plate: a few combs and allpasses, run at a lower rate (24 kHz) to stretch the memory. | Hard | ⬜ | At 24 kHz the 4K data words of one DSP make ~170 ms of delay line, enough for a small Schroeder-type reverb, but it takes nearly all of that DSP's memory, so a patch with it gets fewer voices. Not the G2's long hall. The G1 patches that already make a reverb from many short Delays prove short networks work. |

## G2 versions of modules the G1 has, that do more

| G2 module | G1 module | What the G2's adds | Feasible | Status |
| --- | --- | --- | --- | --- |
| Random A | RndStepGen | Mono/Poly, rate range, Step and Edge amounts | Medium | ✅ in the Random (type 6) |
| Random B | RandomGen | Poly, rate range, KBT, Step, Edge | Medium | ✅ in the Random (type 6) |
| Rnd Clock A | ClkRndGen | Seed (repeatable sequences), Poly, Step, reset | Medium | ⬜ (the Random, clocked by a ClkRndGen, covers most of it) |
| Rnd Trig | RndPulsGen | Clocked, Seed, probability | Medium | ✅ in the Random (type 6) |
| Rnd Pattern | PatternGen | Pattern A/B, Step/Prob, loop length | Medium | ✅ in the Random (type 6) |
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

## Next: opening it up (agreed with Javier, 2026-10-17)

After the first post, people want to use it and add modules (Cristiano Silva works on Micro Modular
mods in an emulator of his own). Before it grows, in this order:

1. ✅ **One folder per module** (2026-10-18; `modules/README.md`): `modules/<name>/` holds its
   `module.json`, its `build.py`, its DSP code, NME's entries and its test with its patches;
   `tools/g1rom.py` is what every build uses and `patch_rom.py` the builder that reads the
   folders. Adding a module = adding a folder. The ROMs and NME's data came out byte for byte
   the same.
2. ✅ **A registry of type numbers** (`modules/registry.json`): each accepted module keeps its
   type for ever, so a patch opens on any build that has that module. Only six are left (60, 93,
   109, 116, 119, 122): the registry is where it is decided which modules get one.
3. **Publish G1-Mods on GitHub**, public, GPLv3 like G1-Emu: README (no ROM or OS given, it builds
   from yours, the notices below), CONTRIBUTING (the module folder in your own repo, the tests,
   nothing of Clavia's). Before: check the whole history for anything of Clavia's. Ask Javier
   before publishing.
4. **The builder** (see "The builder and the catalogue" below): pick your OS, tick modules, get
   the ROM; with it NME telling the modified OS apart. NME's side is ready (2026-10-18, branch
   `mods-layer`, local): the modules in a layer of their own (`data/mods-modules.xml`), offered
   only to a synth ticked "OS with G1-Mods modules" in MIDI Setup (per synth: a Clavia OS can
   sit next to a modified one), their widths from data. It replaces the old `g1-mods` branch
   and goes into `main` when G1-Mods is published (NME is public). The box is set by hand
   until the builder marks the OS in a way NME can read when it connects.

Real hardware only after this, once the ROM's MIDI boot mode is known to recover a bad OS.

## The builder and the catalogue (agreed with Javier, 2026-10-17)

The model is Modwerk (modwerk.app, see `../Digitakt-Mods/NOTES.md`): a web catalogue of modules
and a builder that runs **in the user's browser, from the user's own OS file**. The site never
holds anything of Clavia's, and a built OS never leaves the user's computer.

**Optional, but in the main programs:**

- **G1-Emu does not change**: a modified OS is just another OS file (`os =`). At most a picker in
  Settings ("Clavia's OS / an OS with mods..."). Who never touches it has the G1 as it is.
- **NME, one program**: the mods modules' data in `main`, shown only when the connected OS says it
  has them. The builder writes a signature and the list of its modules (with their types) into
  the OS; NME reads it when it connects. With Clavia's OS, NME is exactly today's. A patch that
  uses a module the OS lacks is not sent: NME says which one is missing.

**One builder, written once:**

- Modules are **data packages**: a folder with a `module.json` (fixed type number, size,
  parameters, author, licence, repo, version), its assembled DSP and 68k code, NME's data, and a
  test. Nothing of Clavia's in it.
- **A small C++ core** does what `patch_rom.py` does: checks the user's OS is a supported version
  (by hash), places the packages, fixes the checksums, refuses a build over the room for code or
  the free types. Compiled to WebAssembly for the site, linked into NME for an offline "Mods"
  window. `patch_rom.py` stays as the reference: both must give the same image, byte for byte.
- **The site is static** (Vercel or GitHub Pages): a page per module (what it does, an audio
  example, a capture of its NME panel), ticks with a bar filling as room is spent, and a build
  button. No server: nothing is uploaded.

**What makes the G1 different from Modwerk's machines:** the limit is the types, not the code
(about 14 types in all against the Digitakt's 128 KB of room), so the catalogue grows by
families (one type, several virtual panels in NME), and the type registry (step 2 above) is the
heart of it: a number given is given for ever. CI cannot hold the OS, so on GitHub only the
packages' format and their build are checked; booting in G1-Emu and the module battery are run
locally by a maintainer.

### Who is responsible for what

We make the tool. We are not responsible for anyone's G1, nor for the modules others write.

- **Tested only on the emulator.** Until it says otherwise, every page, the README and the build
  button say so: nothing has been tried on a real G1, a build may not work on one, and it may
  leave it unusable (bricked). Recovery is not guaranteed.
- **Each owner is responsible for their own G1.** The build button stays disabled until the user
  ticks that they have read the risks. No support for real hardware: issues are for bugs in the
  tool and the modules, with no promise of an answer or a fix.
- **Community modules live in their authors' own repos, not in ours.** Each author owns their
  module, its licence and its support. We link to a module only after trying it in G1-Emu and
  finding it right (or asking for fixes); a linked module is pinned to a reviewed version (a tag
  or a commit), so a later change in the author's repo does not reach users until it is reviewed
  again. Linking it is not a guarantee: the module page names its author and says it is a
  community module. Our own modules stay in this repo, as the reference.
- **Type numbers stay ours**: an author asks for one when the module is linked; the registry here
  is the only place they are given.
- **Per module, "Works for me" and "Report an issue"** (as Modwerk's page), each report saying the
  build, the OS version and whether it was G1-Emu or a real G1, so a hardware report is never
  mistaken for an emulator one.
- **Licences**: the tool GPLv3, as G1-Emu. A linked module must have an open licence that allows
  it to be built into a user's OS (GPL-compatible), with its file in its repo; a licences page
  lists each one, as Modwerk's `THIRD_PARTY_NOTICES`. No rights to Clavia's firmware or
  trademarks are given.
- **Open and free, for good** (Javier, 2026-10-17): everything about the mods is open source and
  as collaborative as possible. No module, build or early access is ever exclusive to Patreon or
  paid: Patreon only supports Javier's work, for whoever wants to. It stands on Gearmulator (G1-Emu
  and its DSP56300 core come from it), so Gearmulator is credited on the site, the README and the
  licences page.

**The notices** (drafts, for the site, the README and the builder; in English like the rest):

- *Independence:* "An independent, unofficial project. Not affiliated with, endorsed by or
  supported by Clavia."
- *Hardware:* "Tested only in the G1-Emu emulator. It has never been tried on a real Nord Modular
  G1. A modified OS may not work on real hardware, may lose your patches and may leave your synth
  unusable. Recovery is not guaranteed. You use it entirely at your own risk; you are solely
  responsible for your instrument."
- *No support:* "Provided as is, without warranty of any kind (GPLv3, sections 15 and 16). We do
  not offer support for real hardware."
- *Community modules:* "Community modules are written and maintained by their authors, in their
  own repositories. We link to them after a review in the emulator, which is not a guarantee.
  Report problems to the module's author."
- *Firmware:* "Do not upload, share or redistribute OS images, original or built: they contain
  Clavia's copyrighted firmware. Share your list of modules instead."

## Ideas, not started

- **Asked for after the first post (2026-10-17, Facebook and Patreon)**, to weigh, not promised:
  a sequential switch matrix (WMD SSM), a VCA or matrix mixer, an LFO synced to the DAW (MIDI
  clock), a control sequencer, 8-1/1-8 switches (planned: type 101 and NME panels), the Event
  Seq sending to MIDI out and its Random button triggerable from a patch. An oscilloscope in NME
  (Cristiano Silva, who works on mods for the Micro Modular in an emulator of his own).

- **The Osc String, as the G2's** (Javier, 2026-10-17, from a picture of it): the G2's has no
  pluck of its own (it sounds only from what its audio input brings), a Pitch knob in semitones and
  cents and a KBT button. Ours was written from the textbook Karplus-Strong, not from the G2's
  code, and Javier likes it as it is: add a Cent knob and KBT on/off to it, keeping Trig and Exc.

- **An OS builder: pick your modules** (Javier, 2026-10-17, as Eurorack firmwares that let you
  choose which apps fit): a library of every G1-Mods module, a window where the user ticks the
  ones they want with a bar filling as the room for code (and the types) is spent, and a button
  that builds their OS from their own OS file. Rules so patches stay portable: each module keeps
  its type number for ever (the library no larger than the free types), and the build tells NME
  which modules it has. The patcher already builds from a list (`EXPERIMENTS`), and while a module
  is being made it is built alone, so the room limit does not stop development. Home: NME (it
  knows the modules and has a window), or a small tool of its own. Removing Clavia modules to free
  their code's RAM is possible but breaks old patches: not first.
- **All the G1's modules swapped for the G2's** (Javier, 2026-10-17, as a thought): not
  recommended. Every G1 patch (his and the community's 34,000) would stop loading, each G2 module
  is written new here, and most of the G2's are the G1's own (`../G2-Emu/MODULOS.md`). At most,
  later, the builder could let a user leave out a few heavy Clavia modules for room, warned.

- **From Javier's first tries (2026-10-17), to check**: the Random into a filter's modulation
  seemed to move it little (its Out is ±64 units, bipolar, as a G1 LFO's; check Step and Edge
  there), and the notes through a Scale Quantizer and a S&H sounded odd at times. A **Uni/Bi
  button** on the Random (done 2026-10-17). Uni↔Bi conversion itself is the G1's InvLevShift, no new type.
- **One NME, one G1-Emu** (Javier, 2026-10-17): NME asks the synth which OS it runs and shows the
  mods modules only with the modified one (the `g1-mods` branch merged into `main`); G1-Emu is
  already the same emulator, the modified OS is only another ROM, so no fork of it. The patcher
  stays here (it needs the user's own OS and never ships Clavia's).
- **The mods categories in NME's module bar** (Javier): not a tab beside each family but under
  it (a second row), or the same tab in another colour.

- **G2 patches on a G1** (Javier, 2026-10-16): not loaded as they are (another file format and
  171 module types), but converted, in NME, for a patch whose every module has a counterpart on
  the G1 or in G1-Mods; one with a module never ported, or too big for the G1's DSPs, would not
  convert. Possible only once most of the G2's modules are here, so after the batches above.
- **A Mutator inside the synth** (Javier, 2026-10-17): interpolating between patch variations on
  the G1 itself. Most of it needs no OS change: the G1's morph already interpolates in the synth,
  so NME's Mutator could write a child as morph ranges and a knob or CC sweeps parent to child.
  Generating variations on the synth (68k code of our own, the front panel's menus) is far more
  work and risk.
