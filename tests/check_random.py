#!/usr/bin/env python3
"""Checks the Random (type 6) in G1-Emu with the G1-Mods ROM.

    tests/check_random.py

tests/random.pch: ClkGen (48 Hz) into Clk; Out on output 1, Trig on 2, the clock on 3, an LFO on
4 (into Rst too in one case). Parameters: Seed, Poly, Step, Edge, Prob, Length. Out is read just
before each clock edge (the value of the clock before). Each case plays 3 s:
- Seed: the values are a model's of the register (in Python here), for Seed 0 and Seed 5, from
  wherever the recording starts (the patch takes some clocks to set up); they span most of
  -64..+64 units and no more.
- Length 4: the values repeat every 4 clocks, the model's first four; Length 0: they do not repeat within 16.
- Rst: with the LFO into Rst, the clock after each Rst edge gives the model's first value.
- Prob 0: no Trig; 127: a Trig every clock; 64: between a third and two thirds of them. Trig is
  high only while the clock is.
- Step 20: Out wanders (its steps are a fraction of Step 127's).
- Edge 0: Out holds between clocks; Edge 60: it glides (many values between two clocks, each a
  bit nearer the next).
Poly needs two voices playing, which the bench cannot do: checked by ear.
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
UNIT = 428167 / 64     # one control unit in the recording
BASE = "3 6 6 0 0 127 0 64 0 "


def record(rom, xml, patch, tmp):
    pch, wav = (os.path.join(tmp, "r." + e) for e in ("pch", "wav"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "3", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)]


def model(seed, n):
    """The values a Seed gives from its load (one voice, Poly off), in units: 16 steps of the
    24-bit Galois register (taps $E10000) from (seed + 1) * $9E37 | 1, a quarter of its value."""
    state, out = ((seed + 1) * 0x9E37) | 1, []
    for _ in range(n):
        for _ in range(16):
            carry, state = state & 1, state >> 1
            if carry:
                state ^= 0xE10000
        v = state - (1 << 24) if state & 0x800000 else state
        out.append(round(v / 2 ** 23 * 64, 1))
    return out


def within(seq, ref):
    """Whether seq is a run of ref (the clocks while the patch is set up are not recorded), each
    within 0.15 units (Step 127 is a hair under 1, so a value keeps a trace of the one before)."""
    return any(all(abs(x - y) <= 0.15 for x, y in zip(seq, ref[k:k + len(seq)]))
               for k in range(len(ref) - len(seq) + 1))


def rising(c):
    return [i for i in range(1, len(c)) if c[i] > 0 >= c[i - 1]]


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "random.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    with tempfile.TemporaryDirectory() as tmp:
        def play(seed=0, poly=0, step=127, edge=0, prob=64, length=0, rst=False):
            patch = base.replace(BASE, f"3 6 6 {seed} {poly} {step} {edge} {prob} {length} ")
            if rst:
                patch = patch.replace("0 2 3 0 4 1 1 \n", "0 2 3 0 4 1 1 \n0 3 1 0 4 1 1 \n")
            out, trig, clk, lfo = record(rom, xml, patch, tmp)
            e = rising(clk)
            vals = [round(out[i - 2] / UNIT, 1) for i in e[1:]]
            return out, trig, clk, lfo, e, vals

        out, trig, clk, _, e, a = play()
        _, _, _, _, _, b = play(seed=5)
        m0, m5 = model(0, 400), model(5, 400)
        report("Seed", within(a[2:60], m0) and within(b[2:60], m5) and min(a) >= -64.1
               and max(a) <= 64.1 and min(a) < -40 and max(a) > 40,
               f"seed 0 {a[2:6]}... and seed 5 {b[2:6]}... in their model's values: "
               f"{within(a[2:60], m0)}, {within(b[2:60], m5)}; from {min(a)} to {max(a)}")

        trigs = sum(1 for i in e if trig[i + 40] > 0)
        report("Prob 64", len(e) / 3 < trigs < 2 * len(e) / 3, f"{trigs} Trigs in {len(e)} clocks")
        high = max(clk) / 2
        bad = sum(1 for i in range(SETTLE, len(trig)) if trig[i] > 0 and clk[i] <= 0
                  and not any(abs(i - j) <= 8 for j in e))
        report("Trig only with Clk", bad == 0 and high > 0, f"{bad} samples of Trig with Clk low")
        held = all(len({out[i] for i in range(e[k] + 8, e[k + 1] - 2)}) == 1 for k in range(2, 20))
        report("Edge 0", held, "Out holds between clocks" if held else "Out moves between clocks")

        _, _, _, _, _, v = play(length=4)
        _, _, _, _, _, f = play(length=0)
        report("Length", all(v[i] == v[i + 4] for i in range(len(v) - 4)) and set(v[:4]) == set(m0[:4])
               and not any(all(f[i] == f[i + n] for i in range(40)) for n in range(1, 17)),
               f"Length 4 {v[:9]}... (the model's first four {m0[:4]}), Length 0 repeats within 16: no")

        # the value of the clock after each Rst edge (read just before the clock after that)
        firsts = []
        out, _, clk, lfo, e, v = play(rst=True)
        for r in rising(lfo):
            nxt = [j for j in e if j > r]
            if len(nxt) >= 2 and r > SETTLE:
                firsts.append(round(out[nxt[1] - 2] / UNIT, 1))
        report("Rst", len(firsts) > 3 and set(firsts) == {m0[0]},
               f"{len(firsts)} Rst edges, the clock after each gives {sorted(set(firsts))}, the model's first {m0[0]}")

        _, _, _, _, _, s = play(step=20)
        d20 = sum(abs(s[i + 1] - s[i]) for i in range(len(s) - 1)) / (len(s) - 1)
        d127 = sum(abs(a[i + 1] - a[i]) for i in range(len(a) - 1)) / (len(a) - 1)
        report("Step 20", d20 < d127 / 3, f"mean step {d20:.1f} units, {d127:.1f} at Step 127")

        out, _, _, _, e, _ = play(edge=60)
        k = 10
        seg = out[e[k] + 8:e[k + 1] - 2]
        toward = (seg[-1] - seg[0]) * (out[e[k + 1] + 200] - seg[0]) >= 0
        report("Edge 60", len(set(seg)) > 100 and toward,
               f"{len(set(seg))} values between two clocks, toward the next: {toward}")

        _, t0, _, _, _, _ = play(prob=0)
        _, t1, clk, _, e, _ = play(prob=127)
        n1 = sum(1 for i in e if t1[i + 40] > 0)
        report("Prob 0 and 127", max(t0[SETTLE:]) <= 0 and n1 == len(e),
               f"Prob 0: {'no Trig' if max(t0[SETTLE:]) <= 0 else 'Trigs'}; Prob 127: {n1} of {len(e)} clocks")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
