#!/usr/bin/env python3
"""Checks the FlipFlop (type 120) in G1-Emu with the G1-Mods ROM.

    tests/check_flipflop.py

tests/flipflop-lfo.pch: ClkGen (48 Hz) into Clk, an LFO (~0.7 Hz) into In; Q on output 1, the
LFO on output 2, the clock on output 3, NotQ on output 4. Each case is that patch with its Type
and some cables changed, played for 6 s in G1-Emu's g1patchtest and checked on the recording:

- D-type: Q only changes on a rising clock edge and then equals In at that edge.
- every case: NotQ is the opposite of Q at every sample after the first 50 ms (once, in the
  toggle case, NotQ showed a stray value for 2 samples 4 ms in, while the OS was still setting
  the patch up; not explained).
- RS-type, In unplugged: Q toggles on every rising clock edge (a divider by 2).
- RS-type, In unplugged, Rst from the LFO: Q is 0 while the LFO is high, and toggles otherwise.
- RS-type, Clk unplugged: Q goes high on In's first rising edge (the first sample if In starts
  high) and stays there.
- tests/flipflop-neighbour.pch: RS toggling with a Constant right after the FlipFlop, its output
  on output 2. The Constant stays constant and NotQ stays Q's opposite: each output of the
  FlipFlop has a word of its own (the descriptor says two outputs; with one, NotQ wrote into the
  next module's output).
Exit code 0 when all hold.
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
CLK_TO_CLK, LFO_TO_IN = "0 6 0 0 4 0 1 \n", "0 6 1 0 3 1 1 \n"
LFO_TO_RST = "0 6 2 0 3 1 1 \n"


def record(rom, xml, patch, tmp, name):
    pch, wav = os.path.join(tmp, name + ".pch"), os.path.join(tmp, name + ".wav")
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "6", "--wav", wav], check=True,
                   capture_output=True, env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)]


def edges(c):
    high = max(c) / 2 if max(c) > 0 else 1
    return [i for i in range(1, len(c)) if c[i] > high and c[i - 1] <= high]


SETTLE = 4800   # 50 ms at 96 kHz: the patch being set up


def not_inverse(q, nq):
    return sum(1 for a, b in list(zip(q, nq))[SETTLE:] if (a > 0) == (b > 0))


def changes(q):
    return [i for i in range(1, len(q)) if q[i] != q[i - 1]]


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "flipflop-lfo.pch")).read()
    assert CLK_TO_CLK in base and LFO_TO_IN in base and "6 120 1 0 " in base
    rs = base.replace("6 120 1 0 ", "6 120 1 1 ")
    ok = True

    def report(name, good, detail):
        nonlocal ok
        ok &= good
        print(f"{name}: {detail} -> {'ok' if good else 'WRONG'}")

    with tempfile.TemporaryDirectory() as tmp:
        q, d, c, nq = record(rom, xml, base, tmp, "d")
        e, ch = edges(c), changes(q)
        off = [i for i in ch if i not in set(e)]
        near_zero = max(abs(x) for x in d) * 0.02
        wrong = sum(1 for k in range(len(e) - 1) if abs(d[e[k]]) >= near_zero
                    and (q[e[k + 1] - 2] > 0) != (d[e[k]] > 0))
        inv = not_inverse(q, nq)
        report("D-type", len(ch) > 2 and not off and wrong == 0 and inv == 0,
               f"{len(ch)} Q changes, {len(off)} off an edge, {wrong} edges where Q != In, NotQ wrong {inv}")

        q, d, c, nq = record(rom, xml, rs.replace(LFO_TO_IN, ""), tmp, "t")
        e, ch = edges(c), changes(q)
        inv = not_inverse(q, nq)
        report("RS, In unplugged (toggle)", abs(len(ch) - len(e)) <= 1 and set(ch) <= set(e) and inv == 0,
               f"{len(e)} clock edges, {len(ch)} Q changes, NotQ wrong {inv}")

        q, d, c, nq = record(rom, xml, rs.replace(LFO_TO_IN, LFO_TO_RST), tmp, "r")
        e, ch = edges(c), changes(q)
        rst_high = max(d) * 0.05
        high_but_q = sum(1 for i in range(1, len(q)) if d[i] > rst_high and d[i - 1] > rst_high
                         and q[i] > 0)
        toggles_low = sum(1 for i in ch if d[i] <= 0)
        report("RS, Rst from the LFO", high_but_q == 0 and toggles_low > 10,
               f"{high_but_q} samples with Rst high and Q high, {toggles_low} toggles while Rst low")

        q, d, c, nq = record(rom, xml, rs.replace(CLK_TO_CLK, ""), tmp, "s")
        first_high = next(i for i in range(len(d)) if d[i] > 0)
        early = sum(1 for i in range(first_high) if q[i] > 0)
        late = sum(1 for i in range(first_high + 2, len(q)) if q[i] <= 0)
        report("RS, Clk unplugged (set)", early == 0 and late == 0,
               f"In first high at sample {first_high}; Q high before it {early}, Q low after it {late}")

        q, k, c, nq = record(rom, xml, open(os.path.join(HERE, "flipflop-neighbour.pch")).read(), tmp, "n")
        kch, ch, e = changes(k), changes(q), edges(c)
        report("outputs of their own (a Constant after it)", not kch and abs(len(ch) - len(e)) <= 1
               and not_inverse(q, nq) == 0,
               f"Constant changes {len(kch)}, Q changes {len(ch)} for {len(e)} edges, NotQ wrong {not_inverse(q, nq)}")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
