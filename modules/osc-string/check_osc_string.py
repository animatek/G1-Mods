#!/usr/bin/env python3
"""Checks the Osc String (type 56) in G1-Emu with the G1-Mods ROM.

    modules/osc-string/check_osc_string.py

string.pch: a square LFO (about 1 Hz) into Trig, plucking the string; Out on output 1, the
LFO on 2. Each case plays 3 s and measures the note's period after the first pluck
(autocorrelation over 0.2 s, refined between samples):
- Note at A1..A5 (45, 57, 69, 81): 110, 220, 440, 880 Hz within 2 cents.
- Damp 30 and 10 at A4: still 440 Hz within 2 cents (Damp's routine takes the lowpass's delay
  from the period).
- The keyboard into Pitch, Note at 64 (E4, as an oscillator's 0): A3, A4 and E5 played.
- Decay 60 dies away faster than Decay 110.
Exit code 0 when all hold.
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
BASE = "3 56 3 69 110 127 "


def record(rom, xml, patch, tmp, *extra):
    pch, wav = (os.path.join(tmp, "s." + e) for e in ("pch", "wav"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "3", "--wav", wav, *extra], check=True,
                   capture_output=True, env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return a[0::ch], a[1::ch]


def pitch(out, trig):
    """The frequency after the first pluck, and the level 0.1 s and 0.6 s after it."""
    e = [i for i in range(1, len(trig)) if trig[i] > 0 >= trig[i - 1]]
    seg = out[e[0] + 2000:e[0] + 2000 + 19200]
    m = sum(seg) / len(seg)
    seg = [v - m for v in seg]

    def cc(lag):
        return sum(seg[i] * seg[i + lag] for i in range(0, 8000, 2))
    lag = max(range(20, 2000), key=cc)
    y0, y1, y2 = cc(lag - 1), cc(lag), cc(lag + 1)
    period = lag + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    level = [max(abs(v) for v in out[e[0] + d:e[0] + d + 960]) for d in (9600, 57600)]
    return 96000 / period, level


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "string.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    def cents(f, note):
        return 1200 * math.log2(f / (440 * 2 ** ((note - 69) / 12)))

    with tempfile.TemporaryDirectory() as tmp:
        def play(note=69, decay=110, damp=127, patch=None, *extra):
            p = (patch or base).replace(BASE, f"3 56 3 {note} {decay} {damp} ")
            return pitch(*record(rom, xml, p, tmp, *extra))

        for note in (45, 57, 69, 81):
            f, _ = play(note)
            report(f"Note {note}", abs(cents(f, note)) < 2, f"{f:.2f} Hz, {cents(f, note):+.1f} cents")
        for damp in (30, 10):
            f, _ = play(damp=damp)
            report(f"Damp {damp}", abs(cents(f, 69)) < 2, f"{f:.2f} Hz, {cents(f, 69):+.1f} cents")

        kb = base.replace("3 56 4 0 \n", "3 56 4 0 \n4 1 8 0 \n")
        kb = kb.replace("0 2 1 0 1 1 1 \n", "0 2 1 0 1 1 1 \n0 3 1 0 4 0 1 \n")
        kb = kb.replace(BASE + "\n", BASE + "\n4 1 0  \n").replace("3 OscString\n", "3 OscString\n4 Keyboard\n")
        for note in (57, 69, 76):
            f, _ = play(64, 110, 127, kb, "--note", str(note))
            report(f"Keyboard {note}", abs(cents(f, note)) < 2, f"{f:.2f} Hz, {cents(f, note):+.1f} cents")

        _, (a60, b60) = play(decay=60)
        _, (a110, b110) = play(decay=110)
        report("Decay", b60 / a60 < b110 / a110 < 1,
               f"after 0.5 s: {b60 / a60:.2f} of the level (Decay 60), {b110 / a110:.2f} (Decay 110)")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
