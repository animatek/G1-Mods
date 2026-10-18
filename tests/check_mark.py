#!/usr/bin/env python3
"""Checks the mark an OS with modules carries: its IAm says version 3.09, Clavia's 3.03.

    tests/check_mark.py

Boots Clavia's ROM and the `all` build in G1-Emu's g1patchtest (which greets like NME) and reads
the IAm reply off the PC Port log: F0 33 00 06 01 03 <minor> ... Clavia's must say 3, ours
MODS_VERSION_LOW (tools/g1rom.py), and NME must look for that same number
(ConnectionManager::kModsVersionLow, read from ../Nomad2026). Exit code 0 when all hold.
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
CLAVIA = os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from g1rom import MODS_VERSION_LOW  # noqa: E402

IAM = bytes.fromhex("f033000601")


def minor(rom, tmp):
    """The minor version in the IAm the OS in this ROM sends."""
    log = os.path.join(tmp, "pc.log")
    if os.path.exists(log):
        os.remove(log)
    subprocess.run([BIN, rom, os.path.join(ROOT, "modules", "flipflop", "flipflop-lfo.pch"),
                    "--seconds", "1", "--wav", os.path.join(tmp, "w.wav")],
                   check=True, capture_output=True,
                   env=dict(os.environ, G1_PCPORT_LOG=log,
                            G1_MODULES_XML=os.path.join(ROOT, "out", "nme-data", "modules.xml")))
    data = open(log, "rb").read()
    at = data.find(IAM)
    assert at >= 0 and data[at + 5] == 3, "no IAm with version 3 in the PC Port log"
    return data[at + 6]


def main():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        rom = os.path.join(tmp, "rom-all.bin")
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all", CLAVIA, rom],
                       check=True, capture_output=True)
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                        os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.join(ROOT, "out", "nme-data")],
                       check=True, capture_output=True)
        for name, path, want in (("Clavia's", CLAVIA, 3), ("all", rom, MODS_VERSION_LOW)):
            got = minor(path, tmp)
            good = got == want
            print(f"{name}: IAm 3.{got:02d} -> {'ok' if good else f'WRONG (3.{want:02d} expected)'}")
            ok &= good
    header = open(os.path.join(ROOT, "..", "Nomad2026", "source", "midi", "ConnectionManager.h"),
                  encoding="utf-8").read()
    m = re.search(r"kModsVersionLow = (\d+)", header)
    good = m is not None and int(m.group(1)) == MODS_VERSION_LOW
    print(f"NME looks for 3.{int(m.group(1)) if m else -1:02d} -> {'ok' if good else 'WRONG'}")
    ok &= good
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
