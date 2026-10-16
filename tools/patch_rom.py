#!/usr/bin/env python3
"""Applies an experiment to a copy of the user's G1 ROM (rack OS 3.03).

    tools/patch_rom.py all ../G1-Emu/Roms/NORD-MODULAR-RACK-VER-3.03.BIN out/rom-all.bin
    tools/patch_rom.py --list

Each experiment either changes DSP words in place (with the word expected there checked first)
or adds new module types: their data go into the RAM the OS leaves untouched, one registration
routine registers them all, and the registration list's last call is pointed at it. On any
other ROM it stops instead of writing. The ROM itself never enters the repo, and neither does
the result. How it all works: NOTES.md.
"""
import hashlib
import os
import sys

ROM_SHA256 = "d9b199f2"  # start of the rack OS 3.03's sha256 (G1-Emu/NOTES.md, "The ROM")
ROM_SIZE = 512 * 1024

FREE = 0x16FB80           # RAM the OS leaves untouched (NOTES.md, "Where new code can live")
FREE_END = 0x173800
LIST_LAST_JSR = 0x10DF1E  # the registration list's last jsr (type 17's, $143350)
LIST_LAST_TARGET = 0x143350


def ram_to_rom(addr):
    return addr - 0x100000 + 0xC800


def entry(t):
    return 0x1C3B00 + t * 0x30


def words(*ws):
    return b"".join(w.to_bytes(4, "big") for w in ws)


class Build:
    """The new types' data, laid out from FREE on, and the routine that registers them."""

    def __init__(self, rom):
        self.rom = rom
        self.at = FREE
        self.blocks = []        # (RAM address, bytes)
        self.register = []      # 68k code run at boot, after the list
        self.types = []

    def rom_bytes(self, addr, n):
        return self.rom[ram_to_rom(addr):ram_to_rom(addr) + n]

    def put(self, data):
        data = bytes(data) + b"\0" * (len(data) & 1)
        addr = self.at
        self.blocks.append((addr, data))
        self.at += len(data)
        assert self.at <= FREE_END
        return addr

    def add_type(self, new_type, donor, fields):
        """new_type gets donor's 48-byte entry with some fields replaced {offset: long}."""
        e = entry(new_type)
        code = ("3f3c" f"{new_type:04x}"     # move.w #type,-(sp)
                "4eb9 0010dc42"              # jsr $10DC42          mark it registered
                "548f"                       # addq.l #2,sp
                "41f9" f"{entry(donor):08x}"  # lea donor,a0
                "43f9" f"{e:08x}"            # lea entry,a1
                "700b"                       # moveq #11,d0
                "22d8"                       # move.l (a0)+,(a1)+   copy the 48 bytes
                "51c8 fffc")                 # dbra d0,*-2
        for off, val in sorted(fields.items()):
            code += "23fc" f"{val:08x}{e + off:08x}"   # move.l #val,entry+off
        self.register.append(bytes.fromhex(code.replace(" ", "")))
        self.types.append(new_type)

    def finish(self):
        routine = bytes.fromhex(f"4eb9{LIST_LAST_TARGET:08x}")   # the call it replaces
        routine += b"".join(self.register) + bytes.fromhex("4e75")  # rts
        reg = self.put(routine)
        hook = (LIST_LAST_JSR + 2, LIST_LAST_TARGET.to_bytes(4, "big"), reg.to_bytes(4, "big"))
        return self.blocks, hook


def mixer3_variant(b, new_type, code=None, code_patch=None, x_words=None, y_words=None, io=None):
    """A type built on the Mixer (3) (type 19): its routines (level curve, parameters written to
    X[0], Y[0], X[1], inputs patched at words 1, 3, 4 and the output at word 7) with code of our
    own (8 words) or the Mixer's with some words changed, and maybe other X/Y counts or other
    numbers of parameters, inputs and outputs (io)."""
    src = 0x14937E   # its data: +$2C, descriptor (+$28), X/Y data, code, +$24 and its two offset bytes
    block = bytearray(b.rom_bytes(src, 0x8A))
    new = b.at
    for i, off in enumerate((0x44, 0x4C, 0x50)):       # +$24's pointers into the block
        at = 0x70 + 4 * i
        assert int.from_bytes(block[at:at + 4], "big") == src + off
        block[at:at + 4] = (new + off).to_bytes(4, "big")
    if code:
        assert len(code) == 8
        block[0x50:0x70] = words(*code)
    for index, (old, val) in (code_patch or {}).items():
        at = 0x50 + 4 * index
        assert block[at:at + 4] == words(old), f"code word {index}"
        block[at:at + 4] = words(val)
    desc = 4
    for off, count in ((0x0E, x_words), (0x12, y_words)):   # audio X and Y counts
        if count is not None:
            block[desc + off:desc + off + 2] = count.to_bytes(2, "big")
    assert block[0x88:0x8A] == bytes.fromhex("feff")   # audio part's nop 2 from the end
    assert b.put(block) == new
    fields = {0x24: new + 0x70, 0x28: new + 0x04, 0x2C: new + 0x00}
    if io:
        fields[0x18] = (io[0] << 24) | (io[1] << 16) | (io[2] << 8)   # parameters, inputs, outputs
    b.add_type(new_type, 19, fields)


def mixer_inv(b, new_type=119):
    """The Mixer (3) with input 1 inverted: mpy -x1,x0,a instead of mpy x1,x0,a."""
    mixer3_variant(b, new_type, code_patch={2: (0x44DBA0, 0x44DBA4)})


# Mix1-1A, after the G2's Mixer 1-1 A: out = chain + in × level. Level in X[0] (the Mixer (3)'s
# level 1, with its curve), in at word 1, chain at word 3 (the Mixer's inputs 1 and 2).
MIX1_1A_CODE = (
    0x44DB00,  # move x:(r3)+,x0    level; word 0 lands in the previous module's nop slot
    0x458000,  # move x:$0,x1       in (input 0)
    0x2000A0,  # mpy x1,x0,a
    0x458000,  # move x:$0,x1       chain (input 1)
    0x200060,  # add x1,a
    0x200011,  # rnd a
    0x000000,  # nop                where the next module's word 0 goes
    0x560000,  # move a,x:$0        out
)


def mix1_1a(b, new_type=121):
    """Mix1-1A: one input with its level, plus a chain input added as it comes."""
    mixer3_variant(b, new_type, code=MIX1_1A_CODE, x_words=1, y_words=0, io=(1, 2, 1))


# The D flip-flop's control-rate code (see NOTES.md, "Type 120: a D flip-flop").
# X data: [0] the logic high, [1] the clock's last value, [2] Q.
FLIPFLOP_X = (0x200000, 0, 0)
FLIPFLOP_CODE = (
    0x468000,  # move x:$0,y0       clock (input 0); word 0 lands in the previous module's nop slot
    0x578000,  # move x:$0,b        D (input 1)
    0x45DB00,  # move x:(r3)+,x1    x1 = high
    0x44E300,  # move x:(r3),x0     x0 = last clock
    0x465B00,  # move y0,x:(r3)+    last clock = clock
    0x47E300,  # move x:(r3),y1     y1 = Q
    0x20000B,  # tst b
    0x202F1B,  # clr b ifle         b = D > 0 ? high : 0
    0x202769,  # tfr x1,b ifgt
    0x200051,  # tfr y0,a
    0x200003,  # tst a
    0x202F79,  # tfr y1,b ifle      clock low: keep Q
    0x200041,  # tfr x0,a
    0x200003,  # tst a
    0x202779,  # tfr y1,b ifgt      clock was already high: keep Q
    0x575B00,  # move b,x:(r3)+     Q = b
    0x000000,  # nop                where the next module's word 0 goes
    0x570000,  # move b,x:$0        out (output 0)
)
FLIPFLOP_OUT_WORD = len(FLIPFLOP_CODE) - 1


def flipflop(b, new_type=120):
    """A D flip-flop: Q takes D on the clock's rising edge. CompareAB (type 89) is the donor:
    two inputs, one output, no parameters, control rate."""
    # CompareAB's entry is built in RAM at boot; what it points to (read from a RAM dump) is in ROM
    conn_src, desc_src = 0x134FBA, 0x14A4EE
    # +$0C, the connections: CompareAB's, with the output patched at our last word, not its 5th
    conn = bytearray(b.rom_bytes(conn_src, 0x78))
    at = conn.find(bytes.fromhex("3f3c0005"))
    assert at > 0 and conn[-2:] == bytes.fromhex("4e75")
    conn[at + 2:at + 4] = FLIPFLOP_OUT_WORD.to_bytes(2, "big")
    conn_at = b.put(conn)
    x_at = b.put(words(*FLIPFLOP_X))
    p_at = b.put(words(*FLIPFLOP_CODE))
    # +$28, the descriptor: CompareAB's, with our counts
    desc = bytearray(b.rom_bytes(desc_src, 0x30))
    assert desc[0x1A:0x1C] == b"\0\0" and desc[0x22:0x24] == (6).to_bytes(2, "big")
    desc[0x06:0x08] = (len(FLIPFLOP_CODE) - 1).to_bytes(2, "big")   # control cycles
    desc[0x1A:0x1C] = len(FLIPFLOP_X).to_bytes(2, "big")            # control X words
    desc[0x22:0x24] = len(FLIPFLOP_CODE).to_bytes(2, "big")         # control P words
    desc_at = b.put(desc)
    # +$24: audio X/Y/P (unused: no audio part), control X/Y/P, and the two nop offsets
    data_at = b.put(words(x_at, x_at, p_at, x_at, x_at, p_at) + bytes.fromhex("fffe"))
    b.add_type(new_type, 89, {0x0C: conn_at, 0x24: data_at, 0x28: desc_at})


# name: (what it shows, the new types, or the DSP words to change in place)
EXPERIMENTS = {
    "mixer3-silent": (
        "Mixer (3): the rounding multiply-accumulate becomes clr a, so the module is mute",
        None, [(0x1493CE + 5 * 4, 0x2000A3, 0x200013)],
    ),
    "type119-mixinv": (
        "a new type 119: the Mixer (3) with input 1 inverted",
        [mixer_inv], [],
    ),
    "all": (
        "every new type: 119 (Mixer Inv), 120 (FlipFlop, a D flip-flop), 121 (Mix1-1A)",
        [mixer_inv, flipflop, mix1_1a], [],
    ),
}


def main():
    if sys.argv[1:] == ["--list"]:
        for name, (what, _, _) in EXPERIMENTS.items():
            print(f"{name}: {what}")
        return
    if len(sys.argv) != 4 or sys.argv[1] not in EXPERIMENTS:
        sys.exit(__doc__)
    name, src, dst = sys.argv[1:]
    rom = bytearray(open(src, "rb").read())
    if len(rom) != ROM_SIZE or not hashlib.sha256(rom).hexdigest().startswith(ROM_SHA256):
        sys.exit("not the rack OS 3.03 ROM")
    _, types, in_place = EXPERIMENTS[name]
    for addr, old, new in in_place:
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old.to_bytes(4, "big"):
            sys.exit(f"unexpected word at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new.to_bytes(4, "big")
    if types:
        b = Build(bytes(rom))
        for add in types:
            add(b)
        blocks, (addr, old, new) = b.finish()
        for at, data in blocks:
            o = ram_to_rom(at)
            if rom[o:o + len(data)] != b"\xff" * len(data):
                sys.exit(f"${at:06X} is not free in this ROM")
            rom[o:o + len(data)] = data
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old:
            sys.exit(f"unexpected hook at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new
        print(f"new types {b.types}, {b.at - FREE} bytes at ${FREE:06X}, registered by ${int.from_bytes(new, 'big'):06X}")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(rom)
    print(f"{name}: written {dst}")


if __name__ == "__main__":
    main()
