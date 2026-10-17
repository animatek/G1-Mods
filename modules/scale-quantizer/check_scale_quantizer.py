#!/usr/bin/env python3
"""Checks the Scale Quantizer (type 125) in G1-Emu with the G1-Mods ROM.

    modules/scale-quantizer/check_scale_quantizer.py

quant.pch: an LFO (sine, about 2 Hz, the full -64..+64 units) into In; Out on output 1, the
LFO on output 2. Each case plays 3 s with another Root, Scale and Octave, and every sample of Out
must be the note the scale table gives for In a few samples before (In rounded to a semitone,
corrected to the scale's nearest note, plus the octaves; 0 is note 64, an E), and every note out
must be in the scale. The cases: every one of the 16 scales on C, and D minor pentatonic, A minor
an octave up, F# major two octaves down.
Exit code 0 when all hold.
"""
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
SETTLE = 4800          # 50 ms at 96 kHz: the patch being set up
UNIT = 428167 / 64     # one control unit, a semitone at a pitch input, in the recording
LATE = 12              # Out may follow In by this many samples

sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(ROOT, "tools"))
from build import SCALES, corrections  # noqa: E402


def record(rom, xml, patch, tmp):
    pch, wav = (os.path.join(tmp, "q." + e) for e in ("pch", "wav"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "3", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return a[0::ch], a[1::ch]


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "quant.pch")).read()
    ok = True

    cases = [(0, s, 4) for s in range(len(SCALES))] + [(2, 11, 4), (9, 2, 5), (6, 1, 2)]
    with tempfile.TemporaryDirectory() as tmp:
        for root, scale, octave in cases:
            out, inp = record(rom, xml, base.replace("3 125 3 0 1 4 ", f"3 125 3 {root} {scale} {octave} "), tmp)
            name, notes = SCALES[scale]
            corr = corrections(notes)

            def expected(v):
                n = round(v / UNIT)
                return n + corr[(n + 4 - root) % 12] + 12 * (octave - 4)

            wrong, checked = 0, 0
            for i in range(SETTLE + LATE, len(out)):
                if abs(inp[i] / UNIT - round(inp[i] / UNIT)) > 0.4:
                    continue                      # In near a half semitone: either side is right
                checked += 1
                if all(round(out[i] / UNIT) != expected(inp[i - k]) for k in range(LATE)):
                    wrong += 1
            got = {round(v / UNIT) for v in out[SETTLE:]}
            outside = sorted({(g + 4 - root) % 12 for g in got} - set(notes))
            good = wrong == 0 and not outside and checked > 1000 and len(got) > 20
            ok &= good
            print(f"root {root:2} {name:16} octave {octave - 4:+d}: {len(got)} notes out, {wrong} of "
                  f"{checked} samples wrong, outside the scale {outside} -> {'ok' if good else 'WRONG'}")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
