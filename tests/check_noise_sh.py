#!/usr/bin/env python3
"""Checks the Noise S&H (type 122) in G1-Emu with the G1-Mods ROM.

    tests/check_noise_sh.py

tests/noise-sh.pch: ClkGen (48 Hz) into Trig; Out on output 1, Inv on output 2, the clock on
output 3. Played for 6 s at 1 octave Bi, 5 octaves Bi and 3 octaves Uni: Out only changes on a
rising clock edge and takes many different values; Bi spans about ±6 semitones an octave of range
and Inv is -Out; Uni spans 0..12 semitones an octave and Out + Inv is the whole range (the mirror).
Exit code 0 when it holds.
"""
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
SETTLE = 4800       # 50 ms at 96 kHz: the patch being set up
UNIT = 428167 / 64  # one control unit (a semitone at a pitch input at 127) in the recording: the
                    # logic high, 64 units, records as 428167


def record(rom, xml, rng, uni, tmp):
    patch = open(os.path.join(HERE, "noise-sh.pch")).read().replace("6 122 2 0 0 ", f"6 122 2 {rng} {uni} ")
    pch, wav = os.path.join(tmp, "n.pch"), os.path.join(tmp, "n.wav")
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "6", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return a[0::ch], a[1::ch], a[2::ch]


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for rng, uni in ((0, 0), (4, 0), (2, 1)):
            out, inv, clk = record(rom, xml, rng, uni, tmp)
            n = len(out)
            octaves = rng + 1
            high = max(clk) / 2
            edges = {i for i in range(1, n) if clk[i] > high and clk[i - 1] <= high}
            changes = [i for i in range(1, n) if out[i] != out[i - 1]]
            off_edge = [i for i in changes if i not in edges]
            held = [out[i] for i in changes]
            lo, hi = min(held) / UNIT, max(held) / UNIT
            # the output chain truncates (the master volume's multiply), so a sum of two outputs is
            # one or two LSB off, a hundredth of a semitone: the tolerance is far above it
            sums = [(out[i] + inv[i]) / UNIT for i in range(SETTLE, n)]
            if uni:
                span_ok = lo > -0.5 and abs(hi - 12 * octaves) < 0.15 * 12 * octaves
                mirror = max(abs(x - 12 * octaves) for x in sums) < 0.3       # Out + Inv = the range
            else:
                span_ok = abs(max(-lo, hi) - 6 * octaves) < 0.15 * 6 * octaves and lo < 0 < hi
                mirror = max(abs(x) for x in sums) < 0.3                       # Inv = -Out
            # distinct values: with a small range the recording has fewer levels in it, so some
            # draws repeat by chance (259 of 288 at 1 octave)
            good = (len(changes) > 0.9 * len(edges) and not off_edge
                    and len(set(held)) > 0.8 * len(changes) and span_ok and mirror)
            print(f"{octaves} oct {'Uni' if uni else 'Bi '}: {len(changes)} changes for {len(edges)} edges, "
                  f"{len(off_edge)} off an edge, {len(set(held))} distinct, Out from {lo:+.1f} to {hi:+.1f} semitones, "
                  f"Out + Inv within {min(sums):+.2f}..{max(sums):+.2f} -> {'ok' if good else 'WRONG'}")
            ok &= good
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
