#!/usr/bin/env python3
"""Applies an experiment to a copy of the user's G1 ROM (rack OS 3.03).

    tools/patch_rom.py mixer3-silent ../G1-Emu/Roms/NORD-MODULAR-RACK-VER-3.03.BIN out/rom.bin
    tools/patch_rom.py --list

Each experiment is a list of DSP words to change, by RAM address, with the word expected there
first: on any other ROM it stops instead of writing. The ROM itself never enters the repo, and
neither does the result.
"""
import hashlib
import os
import sys

ROM_SHA256 = "d9b199f2"  # start of the rack OS 3.03's sha256 (G1-Emu/NOTES.md, "The ROM")
ROM_SIZE = 512 * 1024


def ram_to_rom(addr):
    return addr - 0x100000 + 0xC800


# name: (what it shows, [(RAM address, expected word, new word)])
EXPERIMENTS = {
    "mixer3-silent": (
        "Mixer (3): the rounding multiply-accumulate becomes clr a, so the module is mute",
        [(0x1493CE + 5 * 4, 0x2000A3, 0x200013)],
    ),
}


def main():
    if sys.argv[1:] == ["--list"]:
        for name, (what, _) in EXPERIMENTS.items():
            print(f"{name}: {what}")
        return
    if len(sys.argv) != 4 or sys.argv[1] not in EXPERIMENTS:
        sys.exit(__doc__)
    name, src, dst = sys.argv[1:]
    rom = bytearray(open(src, "rb").read())
    if len(rom) != ROM_SIZE or not hashlib.sha256(rom).hexdigest().startswith(ROM_SHA256):
        sys.exit("not the rack OS 3.03 ROM")
    for addr, old, new in EXPERIMENTS[name][1]:
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old.to_bytes(4, "big"):
            sys.exit(f"unexpected word at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new.to_bytes(4, "big")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(rom)
    print(f"{name}: written {dst}")


if __name__ == "__main__":
    main()
