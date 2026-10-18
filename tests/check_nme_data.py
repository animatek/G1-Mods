#!/usr/bin/env python3
"""Checks that NME's data and the OS agree on every new type.

    tests/check_nme_data.py

For each new type the ROM is built with, NME's layer (../Nomad2026/data/mods-modules.xml, as
it is on disk) must have the same parameters, each with the same maximum (NME packs a patch's
parameters by it, the OS unpacks them by the ROM's: a mismatch shifts every parameter after it),
and the same number of inputs and outputs. The layer must be what tools/make_nme_data.py --layer
writes now (not stale); NME's ParameterEncoder must have no case of its own for the type, so the
width comes from that maximum (setWidthsFromData); and its fmtScaleName as many names as the
Scale Quantizer has scales (it shows them by their order). No emulator is needed.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import patch_rom  # noqa: E402


NME = os.path.join(ROOT, "..", "Nomad2026")


def encoder_cases():
    """The types NME's ParameterEncoder switch has a case for."""
    src = open(os.path.join(NME, "source", "protocol", "ParameterEncoder.cpp"), encoding="utf-8").read()
    return {int(t) for t in re.findall(r"\bcase (\d+):", src)}


def main():
    rom = open(os.path.join(ROOT, "..", "G1-Emu", "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), "rb").read()
    layer = os.path.join(NME, "data", "mods-modules.xml")
    xml = open(layer, encoding="utf-8").read()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                        "--layer", tmp], check=True, capture_output=True)
        fresh = open(os.path.join(tmp, "mods-modules.xml"), encoding="utf-8").read()
    ok = xml == fresh
    print(f"NME's layer as make_nme_data.py --layer writes it now -> {'ok' if ok else 'STALE'}")
    b = patch_rom.Build(rom)
    for add in patch_rom.EXPERIMENTS["all"][1]:
        add(b)
    cases = encoder_cases()
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
        good = (nme_max, nme_in, nme_out) == (maxima, inputs, outputs) and t not in cases
        print(f"type {t}: OS {maxima} {inputs} in {outputs} out, NME {nme_max} {nme_in} in {nme_out} out,"
              f" encoder {'its own case' if t in cases else 'from data'}"
              f" -> {'ok' if good else 'WRONG'}")
        ok &= good
    fmt = open(os.path.join(NME, "source", "format", "ValueFormatters.cpp"), encoding="utf-8").read()
    m = re.search(r"fmtScaleName \(int value\)\s*\{\s*static const char\* names\[\] = \{([^}]*)\}", fmt)
    names = re.findall(r'"([^"]*)"', m.group(1)) if m else []
    scales = patch_rom.Module("scale-quantizer").code.SCALES
    good = len(names) == len(scales)
    print(f"scale names: NME {len(names)}, OS {len(scales)} -> {'ok' if good else 'WRONG'}")
    ok &= good
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
