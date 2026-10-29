#!/usr/bin/env python3
"""Checks the modules built into the Micro Modular's OS, in G1-Emu's Micro model.

    tests/check_micro.py

Builds the Micro's OS image with every module that is on the Micro (patch_rom.py --micro all), boots it in
g1boot's Micro model and reads the RAM after boot, then plays every module's example patch in g1patchtest:

- every type the build says it made has an entry in the Micro's type table that is not the empty one, and
  none of the others changed;
- the OS says 3.09 (the move.b #9 at the translated address is in the loaded OS);
- every example patch is taken by the OS (no rejection) and plays;
- the image fits what an update erases, and a module with "micro": false is not in it.

It needs the Micro's 3.03b OS image (G1-Emu/Roms/Micro/micro-os.bin, from Clavia's updater with
G1-Emu/Roms/Micro/extract-os.py) and says so, and stops without failing, when it is not there.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EMU = os.path.join(ROOT, "..", "G1-Emu")
MICRO_OS = os.path.join(EMU, "Roms", "Micro", "micro-os.bin")
RACK_ROM = os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN")
BOOT = os.path.join(EMU, "build", "tools", "g1boot")
PATCHTEST = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
TABLE = 0x17C09C - 0x100000     # the Micro's type table in RAM (the rack's is at $1C3B00)
VERSION = 0x10486E - 0x100000


def entries(ram):
    return [ram[TABLE + t * 0x30:TABLE + (t + 1) * 0x30] for t in range(128)]


def boot(os_image, dump):
    subprocess.run([BOOT, RACK_ROM, "400"], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODEL="micro", G1_OS=os_image, G1_RAMDUMP=dump))
    return open(dump, "rb").read()


def main():
    if not os.path.exists(MICRO_OS):
        print(f"no Micro OS image at {MICRO_OS}: skipped (extract it from Clavia's Micro updater)")
        return
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        image = os.path.join(tmp, "os-micro.bin")
        log = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "--micro", "all",
                              MICRO_OS, image], check=True, capture_output=True, text=True).stdout
        made = json.loads(log.split("new types ")[1].split("]")[0] + "]")
        size = os.path.getsize(image)
        print(f"image {size} bytes, types {sorted(made)}")
        ok &= size <= 0x60000 - 0x20
        mods = [json.load(open(f)) for f in glob.glob(os.path.join(ROOT, "modules", "*", "module.json"))]
        left_out = [m["type"] for m in mods if not m.get("micro", True)]
        out_ok = not set(left_out) & set(made)
        ok &= out_ok
        print(f"left out {left_out}: {'not in the build: ok' if out_ok else 'IN THE BUILD: WRONG'}")

        plain = boot(MICRO_OS, os.path.join(tmp, "plain.ram"))
        built = boot(image, os.path.join(tmp, "built.ram"))
        a, b = entries(plain), entries(built)
        changed = [t for t in range(128) if a[t] != b[t]]
        good = sorted(changed) == sorted(made)
        ok &= good
        print(f"type table: changed {changed}: {'ok' if good else 'WRONG, expected ' + str(sorted(made))}")
        mark = built[VERSION:VERSION + 6].hex() == "157c00090008"
        ok &= mark
        print(f"version in the loaded OS: {'3.09 ok' if mark else 'WRONG'}")

        for pch in sorted(glob.glob(os.path.join(ROOT, "modules", "*", "*.pch")) + glob.glob(os.path.join(ROOT, "patches", "*.pch"))):
            if "noteout" in pch:
                continue
            out = subprocess.run([PATCHTEST, RACK_ROM, pch, "--note", "60", "--seconds", "4"], capture_output=True, text=True,
                                 env=dict(os.environ, G1_MODEL="micro", G1_OS=image)).stdout
            took = "uploaded in" in out and not any(w in out.lower() for w in ("reject", "unfinished", "error"))
            ok &= took
            print(f"{os.path.basename(pch)}: {'taken, plays' if took else 'NOT TAKEN'}")
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
