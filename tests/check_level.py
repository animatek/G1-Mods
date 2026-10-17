#!/usr/bin/env python3
"""Checks the Level module (type 42) in G1-Emu with the G1-Mods ROM.

    tests/check_level.py

tests/level.pch (ModAmt with the Constant, a steady output for check_insert.py): an LFO (about
2 Hz) into A; into B a slower LFO, or a ClkGen (T&H), or a
Constant at +32 units (ModAmt); Out 1 on output 1, Out 2 on 2, A on 3, B on 4. Each case plays
3 s, and every sample of the outputs must be the mode's result for A and B a few samples before,
within a hundredth of the range:
- ModAmt, Amount 127, B +32 units (a half): Out 1 = A / 2, Out 2 = A - Out 1; Amount 0: Out 1 = A.
- MinMax with the two LFOs: Out 1 the lower, Out 2 the higher.
- T&H with the clock: Out 1 follows A while the clock is high and holds while low, Out 2 the
  other way round.
- Window with the slow LFO, Lo 0 and Hi +32 units: Out 1 = A and Out 2 high while B is within.
Exit code 0 when all hold.
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
SETTLE = 4800          # 50 ms at 96 kHz: the patch being set up
HIGH = 428167          # the logic high, 64 units, in the recording
TOL = HIGH * 2 / 100   # a hundredth of the -64..+64 range
LATE = 12              # the outputs may follow the inputs by this many samples
BASE = "3 42 4 0 127 64 96 "


def record(rom, xml, patch, tmp):
    pch, wav = (os.path.join(tmp, "l." + e) for e in ("pch", "wav"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "3", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)]


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "level.pch")).read()
    ok = True

    def play(mode, amount=127, lo=64, hi=96, b="lfo"):
        patch = base.replace(BASE, f"3 42 4 {mode} {amount} {lo} {hi} ")
        src = {"lfo": "4 1", "clk": "5 0", "const": "6 0"}[b]
        patch = patch.replace("0 3 1 0 6 0 1 ", f"0 3 1 0 {src} 1 ").replace("0 2 3 0 6 0 1 ", f"0 2 3 0 {src} 1 ")
        return record(rom, xml, patch, tmp)

    def check(what, outs, want):
        """want(A, B, i) -> (out 1, out 2) or None (no check there); outs = (o1, o2, a, b)."""
        nonlocal ok
        o1, o2, a, b = outs
        wrong = checked = 0
        for i in range(SETTLE + LATE, len(o1)):
            got = False
            for d in range(LATE):
                w = want(a[i - d], b[i - d], i - d)
                if w is None:
                    got = None
                    break
                if abs(o1[i] - w[0]) <= TOL and abs(o2[i] - w[1]) <= TOL:
                    got = True
                    break
            if got is None:
                continue
            checked += 1
            wrong += not got
        good = wrong == 0 and checked > 100000
        ok &= good
        print(f"{what}: {wrong} of {checked} samples off -> {'ok' if good else 'WRONG'}")

    with tempfile.TemporaryDirectory() as tmp:
        check("ModAmt, Amount 127, B a half", play(0, b="const"), lambda a, b, i: (a / 2, a - a / 2))
        check("ModAmt, Amount 0", play(0, amount=0, b="const"), lambda a, b, i: (a, 0))
        check("MinMax", play(1), lambda a, b, i: (min(a, b), max(a, b)))

        o1, o2, a, b = play(2, b="clk")
        held1 = held2 = 0
        trace = []
        for i in range(len(a)):
            if b[i] > 0:
                held1 = a[i]
            else:
                held2 = a[i]
            trace.append((held1, held2))
        edges = [i for i in range(1, len(b)) if (b[i] > 0) != (b[i - 1] > 0)]
        near = set(j for e in edges for j in range(e - LATE, e + LATE))
        check("T&H", (o1, o2, a, b), lambda x, y, i: None if i in near else trace[i])

        o1, o2, a, b = play(3, lo=64, hi=96)
        unit = HIGH / 64

        def win(x, y, i):
            if abs(y) < unit or abs(y - 32 * unit) < unit:
                return None                         # at an edge of the window
            inside = 0 <= y <= 32 * unit
            return (x, HIGH) if inside else (0, 0)
        check("Window", (o1, o2, a, b), win)

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
