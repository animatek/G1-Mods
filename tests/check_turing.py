#!/usr/bin/env python3
"""Checks the Turing Machine (type 124) in G1-Emu with the G1-Mods ROM.

    tests/check_turing.py

tests/turing.pch: ClkGen (48 Hz) into Clk; CV on output 1, Gate on 2, the clock on 3. Each case
plays 6 s with other parameters (Prob, Length, Lock), and reads the register's low byte from CV
at the end of each clock period:
- Prob 0, Length 8: CV only changes on a rising clock edge, and the bytes repeat every 8 clocks.
- Prob 0, Length 16: every 16 clocks, and not every 8.
- Prob 127, Length 8: nearly every bit flips, so a byte comes back inverted 8 clocks later
  (255 - it) and repeats every 16.
- Prob 127 with Lock on: every 8 again, as Prob 0.
- Prob 64: no repeat, and many different bytes.
- Gate: high only while the clock is, and then just when the byte's bit 0 is 1.
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
LSB = HIGH / 256       # CV is the byte << 13: 256 of them make the high


def record(rom, xml, patch, tmp):
    pch, wav = (os.path.join(tmp, "t." + e) for e in ("pch", "wav"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "6", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)]


def edges(c):
    high = max(c) / 2
    return [i for i in range(1, len(c)) if c[i] > high and c[i - 1] <= high]


def bytes_per_clock(cv, e):
    """The byte CV holds just before each clock edge (after the first few)."""
    return [round(cv[i - 2] / LSB) for i in e if i > SETTLE]


def repeats(b, n):
    return all(b[i] == b[i + n] for i in range(len(b) - n))


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "turing.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    with tempfile.TemporaryDirectory() as tmp:
        def play(prob, length, lock):
            cv, gate, clk, _ = record(rom, xml, base.replace("3 124 3 0 7 0 ", f"3 124 3 {prob} {length} {lock} "), tmp)
            e = edges(clk)
            return cv, gate, clk, e, bytes_per_clock(cv, e)

        cv, gate, clk, e, b = play(0, 7, 0)
        es = set(e)
        off = [i for i in range(SETTLE, len(cv)) if cv[i] != cv[i - 1] and not any(j in es for j in range(i - 8, i + 1))]
        report("Prob 0, Length 8", repeats(b, 8) and len(set(b)) > 1 and not off,
               f"{len(b)} clocks, bytes {b[:9]}..., {len(off)} changes off a clock edge")
        top = max(clk) / 2
        bad = [i for i in range(SETTLE, len(gate) - 8)
               if (gate[i] > HIGH / 2) != (clk[i] > top and round(cv[i] / LSB) % 2 == 1)
               and not any(abs(j - i) <= 8 for j in e)]
        gates = sum(1 for i in range(SETTLE, len(gate)) if gate[i] > HIGH / 2 >= gate[i - 1])
        report("Gate", not bad and gates > 0, f"{gates} gates, {len(bad)} samples where Gate is not bit 0 and Clk")

        *_, b = play(0, 15, 0)
        report("Prob 0, Length 16", repeats(b, 16) and not repeats(b, 8), f"bytes {b[:17]}...")

        *_, b = play(127, 7, 0)
        inv = sum(1 for i in range(len(b) - 8) if b[i + 8] == 255 - b[i])
        report("Prob 127, Length 8", inv > 0.8 * (len(b) - 8),
               f"{inv} of {len(b) - 8} bytes inverted 8 clocks later")

        *_, b = play(127, 7, 1)
        report("Lock", repeats(b, 8), f"bytes {b[:9]}...")

        *_, b = play(64, 7, 0)
        report("Prob 64", not repeats(b, 8) and not repeats(b, 16) and len(set(b)) > 50,
               f"{len(set(b))} different bytes in {len(b)} clocks")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
