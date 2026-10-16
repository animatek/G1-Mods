#!/usr/bin/env python3
"""Checks the Noise S&H (type 122) in G1-Emu with the G1-Mods ROM.

    tests/check_noise_sh.py

tests/noise-sh.pch: ClkGen (48 Hz) into Trig; Out on output 1, Inv on output 2, the clock on
output 3. Played for 6 s: Out only changes on a rising clock edge, takes many different values of
both signs (noise, not a constant or a pattern of a few), and Inv is -Out at every sample after the
first 50 ms. Exit code 0 when it holds.
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
SETTLE = 4800


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "n.wav")
        subprocess.run([BIN, rom, os.path.join(HERE, "noise-sh.pch"), "--seconds", "6", "--wav", wav],
                       check=True, capture_output=True, env=dict(os.environ, G1_MODULES_XML=xml))
        w = wave.open(wav)
        n, ch = w.getnframes(), w.getnchannels()
        raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    out, inv, clk = a[0::ch], a[1::ch], a[2::ch]
    high = max(clk) / 2
    edges = {i for i in range(1, n) if clk[i] > high and clk[i - 1] <= high}
    changes = [i for i in range(1, n) if out[i] != out[i - 1]]
    off_edge = [i for i in changes if i not in edges]
    held = [out[i] for i in changes]
    distinct = len(set(held))
    pos, neg = sum(1 for v in held if v > 0), sum(1 for v in held if v < 0)
    # the output chain truncates (the master volume's multiply), so -x and x come out one LSB
    # or two apart (63 per LSB in the recording's +36 dB): Out + Inv is -63 or -126, not 0
    not_inv = sum(1 for i in range(SETTLE, n) if abs(out[i] + inv[i]) > 200)
    print(f"{len(edges)} clock edges, {len(changes)} changes of Out, {len(off_edge)} off an edge, "
          f"{distinct} distinct values ({pos} positive, {neg} negative), Inv != -Out at {not_inv} samples, "
          f"peak {max(abs(v) for v in out)}")
    ok = (len(changes) > 0.9 * len(edges) and not off_edge and distinct > 0.9 * len(changes)
          and pos > len(changes) / 4 and neg > len(changes) / 4 and not_inv == 0)
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
