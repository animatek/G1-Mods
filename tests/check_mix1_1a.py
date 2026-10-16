#!/usr/bin/env python3
"""Checks the Mix1-1A (type 121) in G1-Emu with the G1-Mods ROM.

    tests/check_mix1_1a.py

tests/mix1-1a-chain.pch: one OscA into a Mixer (3) with only input 1 (output 1, the reference),
into a Mix1-1A A (output 2) and into a Mix1-1A B whose chain input takes A's output (output 3),
all at the same level. Played at levels 100, 64 and 0: output 2 must equal output 1 (same level
curve as the Mixer (3)) and output 3 be 6 dB over it (the chain adds A to B); at 0, silence.
Then the channels' on buttons: B off leaves output 3 with A alone (equal to output 1), and A off
silences output 2 and leaves output 3 with B alone.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
OUT = re.compile(r"output (\d): (silence|peak\s+(-?[\d.]+) dBFS)")


def play(rom, xml, pch):
    r = subprocess.run([BIN, rom, pch, "--seconds", "2"], capture_output=True, text=True,
                       env=dict(os.environ, G1_MODULES_XML=xml))
    return {int(m[1]): (None if m[2] == "silence" else float(m[3])) for m in OUT.finditer(r.stdout)}


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    patch = open(os.path.join(HERE, "mix1-1a-chain.pch")).read()
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        def run(level, a_on, b_on):
            p = os.path.join(tmp, f"{level}-{a_on}{b_on}.pch")
            open(p, "w").write(patch.replace("4 19 3 100 0 0 ", f"4 19 3 {level} 0 0 ")
                               .replace("5 121 2 100 1 ", f"5 121 2 {level} {a_on} ")
                               .replace("6 121 2 100 1 ", f"6 121 2 {level} {b_on} "))
            return play(rom, xml, p)

        def near(a, b, db=0.0, tol=0.3):
            return None not in (a, b) and abs(a - b - db) < tol

        for level in (100, 64, 0):
            o = run(level, 1, 1)
            if level == 0:
                good = o.get(1) is None and o.get(2) is None and o.get(3) is None
            else:
                good = near(o.get(2), o.get(1)) and near(o.get(3), o.get(1), 6.02)
            print(f"level {level}: Mixer (3) {o.get(1)}, Mix1-1A {o.get(2)}, chained {o.get(3)} dBFS"
                  f" -> {'ok' if good else 'WRONG'}")
            ok &= good
        o = run(100, 1, 0)
        good = near(o.get(2), o.get(1)) and near(o.get(3), o.get(1))
        print(f"B off: {o.get(1)}, {o.get(2)}, {o.get(3)} dBFS -> {'ok' if good else 'WRONG'}")
        ok &= good
        o = run(100, 0, 1)
        good = o.get(2) is None and near(o.get(3), o.get(1))
        print(f"A off: {o.get(1)}, {o.get(2)}, {o.get(3)} dBFS -> {'ok' if good else 'WRONG'}")
        ok &= good
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
