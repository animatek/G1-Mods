#!/usr/bin/env python3
"""Checks the Turing Machine (type 124) in G1-Emu with the G1-Mods ROM.

    tests/check_turing.py

tests/turing.pch: ClkGen (48 Hz) into Clk; CV on output 1, Gate 1 on 2, the clock on 3. Each case
plays 6 s with other parameters (Prob, Length, Lock, Scale), and reads the register's low byte from
CV at the end of each clock period:
- Prob 127 (right, locked), Length 8: CV only changes on a rising clock edge, and the bytes repeat
  every 8 clocks.
- Prob 127, Length 16: every 16 clocks, and not every 8.
- Prob 0 (left), Length 8: nearly every bit flips, so a byte comes back inverted 8 clocks later
  (255 - it) and repeats every 16.
- Prob 0 with Lock on: every 8 again, as Prob 127.
- Prob 64 (centre): no repeat, and many different bytes.
- Gates 1, 4 and 8 (output 2 moved to each): high only while the clock is, and then just when
  the byte's bit 0, 3 or 7 is 1.
- Scale 64: CV is the same bytes at about half the level.
- The 8 LEDs: the OS's Meters messages (NMInfo $3A) carry the byte, its low 7 bits and bit 7 as
  the meter's two values, and every byte sent is one CV played.
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
    pch, wav, pc = (os.path.join(tmp, "t." + e) for e in ("pch", "wav", "pc"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "6", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml, G1_PCPORT_LOG=pc))
    record.pc = open(pc, "rb").read()
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
        def play(prob, length, lock, scale=127, gate=1):
            patch = base.replace("3 124 4 127 7 0 127 ", f"3 124 4 {prob} {length} {lock} {scale} ")
            patch = patch.replace("0 2 1 0 3 1 1 ", f"0 2 1 0 3 {gate} 1 ")
            cv, g, clk, _ = record(rom, xml, patch, tmp)
            e = edges(clk)
            return cv, g, clk, e, bytes_per_clock(cv, e)

        cv, gate, clk, e, b = play(127, 7, 0)
        es = set(e)
        off = [i for i in range(SETTLE, len(cv)) if cv[i] != cv[i - 1] and not any(j in es for j in range(i - 8, i + 1))]
        report("Prob 127, Length 8", repeats(b, 8) and len(set(b)) > 1 and not off,
               f"{len(b)} clocks, bytes {b[:9]}..., {len(off)} changes off a clock edge")

        meters, at = set(), 0
        while (at := record.pc.find(bytes.fromhex("f033500601" "3a"), at)) >= 0:
            if record.pc[at + 18:at + 19] == b"\xf7":     # a whole message (19 bytes): the log
                meters.add(record.pc[at + 7] | record.pc[at + 8] << 7)   # can cut one; B, then A
            at += 1
        report("8 LEDs", len(meters) > 4 and meters <= set(b) | {round(cv[SETTLE] / LSB)},
               f"the meter carried {sorted(meters)}, the bytes played {sorted(set(b))}")

        for gate in (1, 4, 8):
            cv, g, clk, e, _ = play(127, 7, 0, gate=gate)
            top = max(clk) / 2
            bad = [i for i in range(SETTLE, len(g) - 8)
                   if (g[i] > HIGH / 2) != (clk[i] > top and round(cv[i] / LSB) >> (gate - 1) & 1 == 1)
                   and not any(abs(j - i) <= 8 for j in e)]
            gates = sum(1 for i in range(SETTLE, len(g)) if g[i] > HIGH / 2 >= g[i - 1])
            report(f"Gate {gate}", not bad and gates > 0,
                   f"{gates} gates, {len(bad)} samples where it is not bit {gate - 1} and Clk")

        *_, b = play(127, 15, 0)
        report("Prob 127, Length 16", repeats(b, 16) and not repeats(b, 8), f"bytes {b[:17]}...")

        *_, b = play(0, 7, 0)
        inv = sum(1 for i in range(len(b) - 8) if b[i + 8] == 255 - b[i])
        report("Prob 0, Length 8", inv > 0.8 * (len(b) - 8),
               f"{inv} of {len(b) - 8} bytes inverted 8 clocks later")

        *_, b = play(0, 7, 1)
        report("Lock", repeats(b, 8), f"bytes {b[:9]}...")

        *_, b = play(64, 7, 0)
        report("Prob 64", not repeats(b, 8) and not repeats(b, 16) and len(set(b)) > 50,
               f"{len(set(b))} different bytes in {len(b)} clocks")

        _, _, _, _, full = play(127, 7, 0)
        cv, _, _, e, _ = play(127, 7, 0, scale=64)
        half = [cv[i - 2] / LSB for i in e if i > SETTLE]
        ratio = [h / f for h, f in zip(half, full) if f > 16]
        report("Scale 64", ratio and all(abs(r - 64.5 / 128) < 0.02 for r in ratio),
               f"CV at {min(ratio):.3f}..{max(ratio):.3f} of Scale 127's")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
