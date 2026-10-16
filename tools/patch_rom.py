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


FREE = 0x16FB80          # RAM the OS leaves untouched (NOTES.md, "Where new code can live")
TYPE_ENTRY = lambda t: 0x1C3B00 + t * 0x30
LIST_LAST_JSR = 0x10DF1E  # the registration list's last jsr (type 17's, $143350)


def be32(*words):
    return b"".join(w.to_bytes(4, "big") for w in words)


def mixer3_clone(rom, new_type, code_patch):
    """Registers new_type as a copy of the Mixer (3) (type 19) whose DSP code has the words in
    code_patch {index: (expected, new)} changed. Returns the list of (RAM address, bytes) to write."""
    src = 0x14937E              # the Mixer (3)'s data: +$2C, descriptor (+$28), X/Y data, code, +$24
    size = 0x88
    block = bytearray(rom[ram_to_rom(src):ram_to_rom(src) + size])
    new = FREE
    # +$24's first three pointers point inside the block: move them with it
    for i, off in enumerate((0x44, 0x4C, 0x50)):
        at = 0x70 + 4 * i
        assert int.from_bytes(block[at:at + 4], "big") == src + off
        block[at:at + 4] = (new + off).to_bytes(4, "big")
    for index, (old, val) in code_patch.items():
        at = 0x50 + 4 * index
        assert int.from_bytes(block[at:at + 4], "big") == old, f"code word {index}"
        block[at:at + 4] = val.to_bytes(4, "big")
    entry = TYPE_ENTRY(new_type)
    reg = new + size            # the registration routine, hand-assembled
    code = bytes.fromhex(
        "4eb9 00143350"         # jsr $143350          the call it replaces (type 17)
        "3f3c" f"{new_type:04x}"  # move.w #type,-(sp)
        "4eb9 0010dc42"         # jsr $10DC42          mark it registered
        "548f"                  # addq.l #2,sp
        "41f9 001c3e90"         # lea $1C3E90,a0       the Mixer (3)'s entry
        "43f9" f"{entry:08x}"   # lea entry,a1
        "700b"                  # moveq #11,d0
        "22d8"                  # move.l (a0)+,(a1)+   copy the 48 bytes
        "51c8 fffc"             # dbra d0,*-2
        "23fc" f"{new + 0x70:08x}{entry + 0x24:08x}"  # move.l #data,entry+$24
        "23fc" f"{new + 0x04:08x}{entry + 0x28:08x}"  # move.l #descriptor,entry+$28
        "23fc" f"{new + 0x00:08x}{entry + 0x2C:08x}"  # move.l #flags,entry+$2C
        "4e75"                  # rts
        .replace(" ", ""))
    hook = (LIST_LAST_JSR + 2, 0x143350.to_bytes(4, "big"), reg.to_bytes(4, "big"))
    return [(new, bytes(block)), (reg, code)], hook


# name: (what it shows, how)
EXPERIMENTS = {
    "mixer3-silent": (
        "Mixer (3): the rounding multiply-accumulate becomes clr a, so the module is mute",
        lambda rom: ([], None, [(0x1493CE + 5 * 4, 0x2000A3, 0x200013)]),
    ),
    "type119-mixinv": (
        "a new type 119: the Mixer (3) with input 1 inverted (mpy -x1,x0,a)",
        lambda rom: (*mixer3_clone(rom, 119, {2: (0x44DBA0, 0x44DBA4)}), []),
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
    blocks, hook, words = EXPERIMENTS[name][1](bytes(rom))
    for addr, old, new in words:
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old.to_bytes(4, "big"):
            sys.exit(f"unexpected word at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new.to_bytes(4, "big")
    for addr, data in blocks:
        o = ram_to_rom(addr)
        if rom[o:o + len(data)] != b"\xff" * len(data):
            sys.exit(f"${addr:06X} is not free in this ROM")
        rom[o:o + len(data)] = data
    if hook:
        addr, old, new = hook
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old:
            sys.exit(f"unexpected hook at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(rom)
    print(f"{name}: written {dst}")


if __name__ == "__main__":
    main()
