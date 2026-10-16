#!/usr/bin/env python3
"""Checks the FlipFlop (type 120) in G1-Emu with the G1-Mods ROM.

    tests/check_flipflop.py

tests/flipflop-lfo.pch: ClkGen (48 Hz) into clk, an LFO (~0.7 Hz) into D; Q on output 1, D on
output 2 and the clock on output 3. It is played for 6 s in G1-Emu's g1patchtest and the
recording is checked: Q only changes on a rising clock edge, and after each edge it equals D at
that edge (edges where D is near zero are skipped). Exit code 0 when it holds.
"""
import bisect
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "ff.wav")
        subprocess.run([BIN, rom, os.path.join(HERE, "flipflop-lfo.pch"), "--seconds", "6", "--wav", wav],
                       check=True, capture_output=True, env=dict(os.environ, G1_MODULES_XML=xml))
        w = wave.open(wav)
        n, ch = w.getnframes(), w.getnchannels()
        raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    q, d, c = a[0::ch], a[1::ch], a[2::ch]
    high = max(c) / 2
    edges = [i for i in range(1, n) if c[i] > high and c[i - 1] <= high]
    changes = [i for i in range(1, n) if q[i] != q[i - 1]]
    crossings = sum(1 for i in range(1, n) if (d[i] > 0) != (d[i - 1] > 0))
    off_edge = [i for i in changes if bisect.bisect_right(edges, i) == 0
                or i != edges[bisect.bisect_right(edges, i) - 1]]
    near_zero = max(abs(x) for x in d) * 0.02
    checked = wrong = 0
    for k in range(len(edges) - 1):
        if abs(d[edges[k]]) < near_zero:
            continue
        checked += 1
        wrong += (q[edges[k + 1] - 2] > 0) != (d[edges[k]] > 0)
    print(f"clock edges {len(edges)}, D crossings {crossings}, Q changes {len(changes)}, "
          f"changes off an edge {len(off_edge)}, edges checked {checked}, Q != D {wrong}")
    ok = len(changes) > 2 and not off_edge and wrong == 0
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
