#!/usr/bin/env python3
"""Checks the 5-Step Seq (type 123) in G1-Emu with the G1-Mods ROM.

    tests/check_seq5.py

tests/seq5.pch: ClkGen (48 Hz) into Clk; Out on output 1, the clock on output 2. The knobs at 0,
32, 64, 96 and 127, so the steps give -64, -32, 0, +32 and +63 control units. Played for 6 s:
- Out only changes on a rising clock edge, takes the five values and goes through them in order,
  the fifth back to the first.
- with the clock divided by 8 (a ClkDivFix) into Rst, and on output 3: after each Rst edge Out is
  the first step's until the next clock, and the second's after it.
- live: the third knob turned to 127 at 3 s, as NME does (G1-Emu's --param-at): the third step
  gives +63 after it.
- the step's LEDs: the OS's Meters messages (NMInfo $3A) on the PC Port carry the module's step,
  each of 0 to 4.
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
SETTLE = 4800       # 50 ms at 96 kHz: the patch being set up
UNIT = 428167 / 64  # one control unit in the recording (the logic high, 64 units, is 428167)
STEPS = [-64, -32, 0, 32, 63]
RST = "0 4 0 0 1 0 1 \n0 3 1 0 4 2 1 \n0 2 2 0 4 2 1 \n"   # clock into the ClkDivFix, its /8 into Rst and output 3


def record(rom, xml, patch, tmp, *extra):
    pch, wav, pc = (os.path.join(tmp, "s." + e) for e in ("pch", "wav", "pc"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "6", "--wav", wav, *extra], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml, G1_PCPORT_LOG=pc))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)], open(pc, "rb").read()


def edges(c):
    high = max(c) / 2
    return [i for i in range(1, len(c)) if c[i] > high and c[i - 1] <= high]


def step_of(v):
    """The step whose value v is (within half a unit), or None."""
    for k, s in enumerate(STEPS):
        if abs(v / UNIT - s) < 0.5:
            return k
    return None


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "seq5.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    with tempfile.TemporaryDirectory() as tmp:
        (out, clk, *_), pc = record(rom, xml, base, tmp)
        e = set(edges(clk))
        ch = [i for i in range(SETTLE, len(out)) if out[i] != out[i - 1]]
        steps = [step_of(out[i]) for i in ch]
        order = sum(1 for a, b in zip(steps, steps[1:]) if a is None or b != (a + 1) % 5)
        report("in order", len(ch) > 0.9 * len(e) and not [i for i in ch if i not in e]
               and set(steps) == set(range(5)) and order == 0,
               f"{len(ch)} changes for {len(e)} clock edges, {len([i for i in ch if i not in e])} off an edge, "
               f"steps seen {sorted(set(s for s in steps if s is not None))}, {order} out of order")

        meters, at = set(), 0
        while (at := pc.find(bytes.fromhex("f033500601" "3a"), at)) >= 0:
            meters.add(pc[at + 7])           # startIndex at +6, then the pairs, B first
            at += 1
        report("step LEDs", meters == set(range(5)), f"the module's meter seen as {sorted(meters)}")

        patch = base.replace("[/CableDump]", RST + "[/CableDump]", 1)
        (out, clk, rst, *_), _ = record(rom, xml, patch, tmp)
        ce = sorted(edges(clk))
        re_ = [r for r in edges(rst) if r > SETTLE]
        bad = 0
        for r in re_:
            nxt = [c for c in ce if c > r + 1]
            if len(nxt) < 2:
                continue
            first, second = step_of(out[nxt[0] - 1]), step_of(out[nxt[0] + 1])
            bad += (first, second) != (0, 1)
        report("Rst", len(re_) > 20 and bad == 0,
               f"{len(re_)} Rst edges, {bad} not followed by the first step and then the second")

        (out, clk, *_), _ = record(rom, xml, base, tmp, "--param-at", "3:1:3:2:127")
        half = len(out) // 2
        before = {round(v / UNIT) for v in out[SETTLE:half - 4800]}
        after = {round(v / UNIT) for v in out[half + 4800:]}
        report("live knob", before == set(STEPS) and after == {-64, -32, 63, 32},
               f"values {sorted(before)} before, {sorted(after)} after the third knob to 127")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
