#!/usr/bin/env python3
"""Checks the 8Counter (type 126) in G1-Emu with the G1-Mods ROM.

    modules/counter8/check_counter8.py

counter8.pch: ClkGen (48 Hz) into Clk and an LFO (about 2 Hz) into Rst, so its edges fall
between clocks; on the outputs, Out 1, Out 2, the clock and the LFO. A model of the counter runs
on the recorded clock and reset (starts on step 8; a Rst edge arms it; the next clock, or one in
the same sample, goes to step 1; any other clock to the next step, the eighth back to the
first), and every sample of the outputs from the first Rst on (the first clocks may come while
the patch is being set up) must be the model's, a control period or two late.
Played again with Out 8 in place of Out 2. The step LEDs: the OS's Meters messages carry the
step, each of 0 to 7.
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
LATE = 12              # the outputs may follow the model by this many samples


def record(rom, xml, patch, tmp):
    pch, wav, pc = (os.path.join(tmp, "c." + e) for e in ("pch", "wav", "pc"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "6", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml, G1_PCPORT_LOG=pc))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)], open(pc, "rb").read()


def rising(c):
    """Where c goes above 0, as the module sees an edge (the LFO is bipolar)."""
    return {i for i in range(1, len(c)) if c[i] > 0 >= c[i - 1]}


def model(clk, rst):
    """The step (0-7) at each sample."""
    ce, re_ = rising(clk), rising(rst)
    step, armed, steps = 7, False, []
    for i in range(len(clk)):
        if i in re_:
            armed = True
        if i in ce:
            step = 0 if armed else (step + 1) % 8
            armed = False
        steps.append(step)
    return steps


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "counter8.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    with tempfile.TemporaryDirectory() as tmp:
        for second in (1, 7):
            patch = base.replace("0 2 1 0 3 1 1 ", f"0 2 1 0 3 {second} 1 ")
            (o1, o2, clk, rst), pc = record(rom, xml, patch, tmp)
            steps = model(clk, rst)
            high = max(max(o1), max(o2)) / 2
            # from the first Rst on: the first clocks may come while the patch is still being set
            # up, so the counter can start a step behind the model
            start = min(rising(rst)) + LATE
            for out, k in ((o1, 0), (o2, second)):
                wrong = sum(1 for i in range(start, len(out))
                            if all((out[i] > high) != (steps[i - d] == k) for d in range(LATE)))
                gates = sum(1 for i in range(SETTLE, len(out)) if out[i] > high >= out[i - 1])
                report(f"Out {k + 1}", wrong == 0 and gates > 3,
                       f"{gates} steps on it, {wrong} samples off the model")
            both = sum(1 for i in range(SETTLE, len(o1)) if o1[i] > high and o2[i] > high)
            resets = len([i for i in rising(rst) if i > SETTLE])
            report("one at a time", both == 0, f"{both} samples with two outputs high, {resets} Rst edges")

            meters, at = set(), 0
            while (at := pc.find(bytes.fromhex("f033500601" "3a"), at)) >= 0:
                if pc[at + 18:at + 19] == b"\xf7":      # a whole message (19 bytes)
                    meters.add(pc[at + 7])              # B: the step
                at += 1
        report("step LEDs", meters == set(range(8)), f"the module's meter seen as {sorted(meters)}")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
