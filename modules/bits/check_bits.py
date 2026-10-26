#!/usr/bin/env python3
"""Checks the Bits module (type 41) in G1-Emu with the G1-Mods ROM.

    modules/bits/check_bits.py

bits.pch (in D>A, whose steady Out check_insert.py can compare): ClkGen (48 Hz) into Clk, an LFO into In, eight Constants into B1-B8 (1 0 1 1 0 0
1 0, Bit 1 first: 77); Out on output 1, Bit 1 on 2, Bit 8 on 3, the clock on 4 (the LFO in A>D).
Each mode plays 3 s:
- Count: the byte goes up one a clock, 255 back to 0; Bit 1 and Bit 8 are its bits; the OS's
  Meters messages (the LEDs) carry it, its low 7 bits and bit 7 (bytes of 128 and above seen).
- A>D: the byte is In in quarter units, 0..255, held at both ends.
- D>A: the byte is 77 from the Constants, and 255 with all eight high.
Exit code 0 when all hold.
"""
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.environ.get("G1MODS_BUILD", "all")   # which modules the ROM has (patch_rom.py)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
SETTLE = 4800          # 50 ms at 96 kHz: the patch being set up
HIGH = 428167          # the logic high, 64 units, in the recording
LSB = HIGH / 256       # a step of the byte
LATE = 12              # a sample may follow In by this many


def record(rom, xml, patch, tmp):
    pch, wav, pc = (os.path.join(tmp, "b." + e) for e in ("pch", "wav", "pc"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "3", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml, G1_PCPORT_LOG=pc))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [a[k::ch] for k in range(ch)], open(pc, "rb").read()


def main():
    rom = os.path.join(ROOT, "out", f"rom-{BUILD}.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), BUILD,
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "bits.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    def mode(m, patch=base):
        return patch.replace("3 41 1 2 ", f"3 41 1 {m} ")

    with tempfile.TemporaryDirectory() as tmp:
        (out, b1, b8, clk), pc = record(rom, xml, mode(0), tmp)
        e = [i for i in range(1, len(clk)) if clk[i] > 0 >= clk[i - 1] and i > SETTLE]
        seq = [round(out[i - 2] / LSB) for i in e]
        steps = {(seq[k + 1] - seq[k]) % 256 for k in range(len(seq) - 1)}
        bits_ok = all((b1[i - 2] > HIGH / 2) == (seq[k] & 1 == 1) and (b8[i - 2] > HIGH / 2) == (seq[k] >= 128)
                      for k, i in enumerate(e))
        report("Count", steps == {1} and bits_ok, f"bytes {seq[:6]}..., steps {sorted(steps)}, Bit 1 and 8 its bits: {bits_ok}")
        meters, at = set(), 0
        while (at := pc.find(bytes.fromhex("f033500601" "3a"), at)) >= 0:
            if pc[at + 18:at + 19] == b"\xf7":
                meters.add(pc[at + 7] | pc[at + 8] << 7)
            at += 1
        # the OS sends meters some 30 times a second, the clock is 48 Hz: not every byte is sent
        report("LEDs", len(meters) > 40 and max(meters) >= 128 and meters <= set(range(256)),
               f"{len(meters)} bytes in the Meters messages, from {min(meters)} to {max(meters)}")

        (out, _, _, lfo), _ = record(rom, xml, mode(1, base.replace("0 2 3 0 1 0 1 ", "0 2 3 0 4 1 1 ")), tmp)

        def ad(v):
            return min(255, max(0, int(v // LSB)))

        wrong = sum(1 for i in range(SETTLE + LATE, len(out))
                    if all(abs(round(out[i] / LSB) - ad(lfo[i - d])) > 1 for d in range(LATE)))
        got = {round(v / LSB) for v in out[SETTLE:]}
        report("A>D", wrong == 0 and 0 in got and 255 in got and len(got) > 200,
               f"{len(got)} bytes from {min(got)} to {max(got)}, {wrong} samples off In")

        (out, b1, b8, _), _ = record(rom, xml, mode(2), tmp)
        got = {round(v / LSB) for v in out[SETTLE:]}
        allhigh = base
        for k in range(8):
            allhigh = allhigh.replace(f"{5 + k} 43 2 64 0 ", f"{5 + k} 43 2 127 0 ")
        (out2, _, _, _), _ = record(rom, xml, mode(2, allhigh), tmp)
        got2 = {round(v / LSB) for v in out2[SETTLE:]}
        report("D>A", got == {77} and got2 == {255} and min(b1[SETTLE:]) > HIGH / 2 and max(b8[SETTLE:]) <= 0,
               f"1 0 1 1 0 0 1 0 gives {sorted(got)}, all high {sorted(got2)}")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
