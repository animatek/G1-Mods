#!/usr/bin/env python3
"""Checks that NME's data and the OS agree on every new type.

    tests/check_nme_data.py

For each new type the ROM is built with, modules.xml (as tools/make_nme_data.py writes it) must
have the same parameters, each with the same maximum (NME packs a patch's parameters by it, the
OS unpacks them by the ROM's: a mismatch shifts every parameter after it), and the same number of
inputs and outputs. And NME's ParameterEncoder (in its g1-mods branch, read with git show, so
whatever branch is checked out) must give each parameter the width of its maximum. No emulator
is needed.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import patch_rom  # noqa: E402


def encoder_widths():
    """{type: [bits]} from the ParameterEncoder's switch: each run of case labels and its return."""
    src = subprocess.run(["git", "-C", os.path.join(ROOT, "..", "Nomad2026"), "show",
                          "g1-mods:source/protocol/ParameterEncoder.cpp"],
                         check=True, capture_output=True, text=True).stdout
    widths = {}
    for cases, ret in re.findall(r"((?:\s*case \d+:)+)(?:\s*//[^\n]*)*\s*return \{([\d, ]*)\};", src):
        for t in re.findall(r"\d+", cases):
            widths[int(t)] = [int(w) for w in ret.split(",") if w.strip()]
    return widths


def main():
    rom = open(os.path.join(ROOT, "..", "G1-Emu", "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), "rb").read()
    xml_dir = os.path.join(ROOT, "out", "nme-data")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), xml_dir], check=True)
    xml = open(os.path.join(xml_dir, "modules.xml"), encoding="utf-8").read()
    b = patch_rom.Build(rom)
    for add in patch_rom.EXPERIMENTS["all"][1]:
        add(b)
    widths = encoder_widths()
    ok = True
    for t, (maxima, inputs, outputs) in sorted(b.specs.items()):
        m = re.search(r'\n  <module component-id="m%d" .*?\n  </module>' % t, xml, re.S)
        if not m:
            print(f"type {t}: not in modules.xml -> WRONG")
            ok = False
            continue
        entry = m.group(0)
        nme_max = [int(re.search(r'maxValue="(\d+)"', p).group(1)) if "maxValue" in p else 127
                   for p in re.findall(r'<parameter [^>]*class="parameter"[^>]*/>', entry)]
        nme_in = len(re.findall(r'type="input"', entry))
        nme_out = len(re.findall(r'type="output"', entry))
        bits = [m.bit_length() for m in maxima]
        good = (nme_max, nme_in, nme_out) == (maxima, inputs, outputs) and widths.get(t) == bits
        print(f"type {t}: OS {maxima} {inputs} in {outputs} out, NME {nme_max} {nme_in} in {nme_out} out,"
              f" encoder {widths.get(t)} bits for {bits}"
              f" -> {'ok' if good else 'WRONG'}")
        ok &= good
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
