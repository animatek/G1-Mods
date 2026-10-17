#!/usr/bin/env python3
"""Checks the Mux8-1 (type 101) in G1-Emu with the G1-Mods ROM.

    modules/mux8/check_mux8.py

mux8.pch: eight Constants into In 1-8 (+4, +8 ... +32 units, so each input is known by its
level), a ninth into Ctrl; Out on output 1, Ctrl on output 2. Each case plays 1 s with another
Sel and Ctrl and Out must be the input Sel + Ctrl / 8 units picks, held to 1..8:
- Ctrl at 0 and Sel 1 to 8: the knob picks (the Sw8-1).
- Sel 1 and Ctrl at -5, 7, 8, 20, 40, 63 units: the level picks, 8 units a step (the Mux8-1).
- Sel 4 with Ctrl 20 (4 + 2 = 6), Sel 8 with Ctrl 20 (held at 8).
- The LEDs: the OS's Meters messages carry the input picked (none for In 1: the OS sends a meter
  when it changes, and it starts at 0).
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
UNIT = 428167 / 64     # one control unit in the recording


def record(rom, xml, patch, tmp):
    pch, wav, pc = (os.path.join(tmp, "m." + e) for e in ("pch", "wav", "pc"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "1", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml, G1_PCPORT_LOG=pc))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return a[0::ch], a[1::ch], open(pc, "rb").read()


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "mux8.pch")).read()
    ok = True
    cases = ([(s, 0) for s in range(8)] + [(0, c) for c in (-5, 7, 8, 20, 40, 63)]
             + [(3, 20), (7, 20)])
    with tempfile.TemporaryDirectory() as tmp:
        for sel, ctrl in cases:
            patch = base.replace("9 101 1 0 ", f"9 101 1 {sel} ").replace("11 43 2 64 0 ", f"11 43 2 {64 + ctrl} 0 ")
            out, c, pc = record(rom, xml, patch, tmp)
            want = min(7, max(0, sel + ctrl // 8))
            got = {round(v / UNIT) for v in out[SETTLE:]}
            leds, at = set(), 0
            while (at := pc.find(bytes.fromhex("f033500601" "3a"), at)) >= 0:
                if pc[at + 18:at + 19] == b"\xf7":
                    leds.add(pc[at + 7])
                at += 1
            # the OS sends a meter only when it changes, from 0: In 1 picked sends nothing (and NME,
            # starting at 0 too, lights the first LED)
            good = got == {4 * (want + 1)} and leds == ({want} if want else set())
            ok &= good
            print(f"Sel {sel + 1} Ctrl {round(c[SETTLE] / UNIT):+3d}: Out {sorted(got)} (In {want + 1} is "
                  f"{4 * (want + 1)}), LEDs {sorted(leds)} -> {'ok' if good else 'WRONG'}")
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
