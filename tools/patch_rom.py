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
import re
import sys

ROM_SHA256 = "d9b199f2"  # start of the rack OS 3.03's sha256 (G1-Emu/NOTES.md, "The ROM")
ROM_SIZE = 512 * 1024

# Where the new types live (NOTES.md, "Where new code can live"). The flash keeps the OS only up
# to $70000 (RAM $16FFE0): past that are the patch banks, which the OS formats. So the package is
# stored at STAGE, in a run of the OS image the OS leaves alone until well after the types are
# registered, and a bootstrap there copies it at boot to RUN, RAM the OS never uses, where it runs.
STAGE = 0x166574          # in the image, inside the flash's OS area
STAGE_END = 0x16B078
FREE = RUN = 0x170000      # where the package runs: every address in it is a RUN address
FREE_END = 0x173800
LIST_LAST_JSR = 0x10DF1E  # the registration list's last jsr (type 17's, $143350)
LIST_LAST_TARGET = 0x143350


def ram_to_rom(addr):
    return addr - 0x100000 + 0xC800


# The types the OS leaves free: its table has 128 (0-127, and a patch keeps a type in 7 bits, so
# there can be no more), and these are the ones without a module (unregistered entries in a RAM
# dump after boot, none in NME's modules.xml). 0 is left out, as "no module" may be read into it.
# G1-Mods uses 101, 120, 121 and 123-126; what is left has to be spent with care (PORTING.md).
# 119 (the Mixer Inv, a first test) and 122 (the Noise S&H, easy to patch from G1 modules) were
# taken out on 2026-10-17 to free them.
FREE_TYPES = (6, 41, 42, 55, 56, 60, 93, 101, 109, 116, 119, 120, 121, 122, 123, 124, 125, 126)


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
        self.specs = {}         # type: (parameter maximums, inputs, outputs), what NME must say

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
        assert new_type in FREE_TYPES and new_type not in self.types, f"type {new_type} is not free"
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
        """Returns ([(RAM address in the image, bytes)], hook): the package with its registration
        routine at the end, behind a bootstrap at STAGE that copies it to RUN and calls it."""
        reg = self.put(b"".join(self.register) + bytes.fromhex("4e75"))   # ...rts
        package = b"".join(data for _, data in self.blocks)
        assert len(package) == self.at - RUN
        boot_len = 0x24
        src = STAGE + boot_len
        boot = m68k("4eb9", f"{LIST_LAST_TARGET:08x}",       # jsr $143350: the call it replaces
                    "41f9", f"{src:08x}",                    # lea package,a0
                    "43f9", f"{RUN:08x}",                    # lea RUN,a1
                    "303c", f"{len(package) - 1:04x}",       # move.w #n-1,d0
                    "12d8",                                  # move.b (a0)+,(a1)+
                    "51c8 fffc",                             # dbra d0,*-2
                    "4eb9", f"{reg:08x}",                    # jsr registration
                    "4e75")                                  # rts
        assert len(boot) <= boot_len and src + len(package) <= STAGE_END
        boot += bytes.fromhex("4e71") * ((boot_len - len(boot)) // 2)   # nop
        hook = (LIST_LAST_JSR + 2, LIST_LAST_TARGET.to_bytes(4, "big"), STAGE.to_bytes(4, "big"))
        return [(STAGE, boot + package)], hook


def param_table(params):
    """The OS's parameter table of a type (+$1C): 12 bytes per parameter, 11 of name and the
    maximum value. The OS reads the maximum to know each parameter's width in a patch, so it must
    match the editor's (NME takes the width from modules.xml's maxValue)."""
    out = b""
    for name, maximum in params:
        assert len(name) <= 11
        out += name.encode("ascii").ljust(11, b"\0") + bytes([maximum])
    return out


def mixer3_variant(b, new_type, code=None, code_patch=None, x_words=None, y_words=None, io=None,
                   params=None):
    """A type built on the Mixer (3) (type 19): its routines (level curve, parameters written to
    X[0], Y[0], X[1], inputs patched at words 1, 3, 4 and the output at word 7) with code of our
    own or the Mixer's with some words changed, and maybe other X/Y counts, other numbers of
    parameters, inputs and outputs (io) and a parameter table of its own. Code longer than 8 words goes on its own, with a copy of
    the connection routine that patches the output at its last word."""
    src = 0x14937E   # its data: +$2C, descriptor (+$28), X/Y data, code, +$24 and its two offset bytes
    fields = {}
    code_at = None
    if params:
        fields[0x1C] = b.put(param_table(params))
    if code and len(code) != 8:
        conn = bytearray(b.rom_bytes(0x131B94, 0x8E))   # the Mixer (3)'s +$0C
        at = conn.find(bytes.fromhex("3f3c0007"))      # move.w #7,-(sp): the output's word
        assert at > 0 and conn[-2:] == bytes.fromhex("4e75")
        conn[at + 2:at + 4] = (len(code) - 1).to_bytes(2, "big")
        fields[0x0C] = b.put(conn)
        code_at = b.put(words(*code))
    block = bytearray(b.rom_bytes(src, 0x8A))
    new = b.at
    for i, off in enumerate((0x44, 0x4C, 0x50)):       # +$24's pointers into the block
        at = 0x70 + 4 * i
        assert int.from_bytes(block[at:at + 4], "big") == src + off
        block[at:at + 4] = (new + off).to_bytes(4, "big")
    desc = 4
    if code_at:
        block[0x78:0x7C] = code_at.to_bytes(4, "big")                      # audio code pointer
        block[desc + 0x02:desc + 0x04] = (len(code) - 1).to_bytes(2, "big")  # audio cycles
        block[desc + 0x16:desc + 0x18] = len(code).to_bytes(2, "big")        # audio P words
    elif code:
        block[0x50:0x70] = words(*code)
    for index, (old, val) in (code_patch or {}).items():
        at = 0x50 + 4 * index
        assert block[at:at + 4] == words(old), f"code word {index}"
        block[at:at + 4] = words(val)
    for off, count in ((0x0E, x_words), (0x12, y_words)):   # audio X and Y counts
        if count is not None:
            block[desc + off:desc + off + 2] = count.to_bytes(2, "big")
    if io:                                                   # its record, by its parameters
        block[desc + 0x24:desc + 0x26] = record_words(io[0]).to_bytes(2, "big")
    assert block[0x88:0x8A] == bytes.fromhex("feff")   # audio part's nop 2 from the end
    assert b.put(block) == new
    fields.update({0x24: new + 0x70, 0x28: new + 0x04, 0x2C: new + 0x00})
    if io:
        fields[0x18] = (io[0] << 24) | (io[1] << 16) | (io[2] << 8)   # parameters, inputs, outputs
    io = io or (3, 3, 1)
    b.specs[new_type] = ([m for _, m in params] if params else [127] * io[0], io[1], io[2])
    b.add_type(new_type, 19, fields)


# Mix1-1A, after the G2's Mixer 1-1 A: out = chain + (on ? in × level : 0). Parameter 0, the
# level, goes to X[0] through the Mixer (3)'s level curve; parameter 1, the channel's on button,
# to Y[0] through the same table (0 -> 0, 1 -> not 0). In at word 1, chain at word 3 (the Mixer's
# inputs 1 and 2), the output at word 8.
MIX1_1A_CODE = (
    0xF09B00,  # move x:(r3)+,x0 y:(r4)+,y0   level, on; word 0 lands in the previous module's nop slot
    0x458000,  # move x:$0,x1       in (input 0)
    0x2000A0,  # mpy x1,x0,a
    0x458059,  # tfr y0,b x:$0,x1   chain (input 1)
    0x20000B,  # tst b
    0x202A13,  # clr a ifeq         channel off: drop in
    0x200060,  # add x1,a
    0x000000,  # nop                where the next module's word 0 goes
    0x560000,  # move a,x:$0        out
)


def mix1_1a(b, new_type=121):
    """Mix1-1A: one input with its level and an on button, plus a chain input added as it comes."""
    mixer3_variant(b, new_type, code=MIX1_1A_CODE, x_words=1, y_words=1, io=(2, 2, 1),
                   params=[("Level", 127), ("Ch 1", 1)])


def m68k(*parts):
    """Concatenates hex strings of hand-assembled 68k code."""
    return bytes.fromhex("".join(parts).replace(" ", ""))


def led_routine(x_word, on_when_set=True):
    """A plain LED's value routine, for $116832: reads the module's X word through the DSP's host
    port ($10C32E, address = the X bases of its two records, word at +8 of each, + x_word) and
    returns 1 when it is not 0 (or when it is 0). Its frame is the CtrlSeq's step routine's."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "246f 0010",          # movea.l (16,sp),a2
                "266f 0014",          # movea.l (20,sp),a3
                "7000 302a 0008",     # moveq #0,d0 / move.w (8,a2),d0
                "7200 322b 0008",     # moveq #0,d1 / move.w (8,a3),d1
                "d081",               # add.l d1,d0
                "0680", f"{x_word:08x}",  # addi.l #x_word,d0
                "2f00",               # move.l d0,-(sp)       the address
                "1012 3f00",          # move.b (a2),d0 / move.w d0,-(sp)   the DSP
                "4eb9 0010c32e",      # jsr $10C32E           read X
                "5c8f",               # addq.l #6,sp
                "4a80",               # tst.l d0
                "56c0" if on_when_set else "57c0",   # sne d0 / seq d0
                "0280 00000001",      # andi.l #1,d0
                "4cdf 0c04",          # movem.l (sp)+,d2/a2-a3
                "4e75")               # rts


def value_routine(x_word, maximum):
    """A led-array's value routine, for $1169BA: reads the module's X word as led_routine does and
    returns it as it is (a step, 0..maximum), or 16 (no LED lit) when it is out of range, as
    the CtrlSeq's does."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "246f 0010",          # movea.l (16,sp),a2
                "266f 0014",          # movea.l (20,sp),a3
                "7000 302a 0008",     # moveq #0,d0 / move.w (8,a2),d0
                "7200 322b 0008",     # moveq #0,d1 / move.w (8,a3),d1
                "d081",               # add.l d1,d0
                "0680", f"{x_word:08x}",  # addi.l #x_word,d0
                "2f00",               # move.l d0,-(sp)       the address
                "1012 3f00",          # move.b (a2),d0 / move.w d0,-(sp)   the DSP
                "4eb9 0010c32e",      # jsr $10C32E           read X
                "5c8f",               # addq.l #6,sp
                "0c80", f"{maximum:08x}",  # cmpi.l #maximum,d0
                "6302",               # bls.s +2              in range: as it is
                "7010",               # moveq #16,d0          out of range: none
                "4cdf 0c04",          # movem.l (sp)+,d2/a2-a3
                "4e75")               # rts


def bits_routine(x_word, mask):
    """A meter's value routine, for $1169BA, that sends bits: reads the module's X word as
    led_routine does and returns it masked. The OS sends the word's low 7 bits and the next 7 as
    the meter's two values (NOTES.md), so up to 14 bits; NME's led-array with `bits` lights one
    LED a bit."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "246f 0010",          # movea.l (16,sp),a2
                "266f 0014",          # movea.l (20,sp),a3
                "7000 302a 0008",     # moveq #0,d0 / move.w (8,a2),d0
                "7200 322b 0008",     # moveq #0,d1 / move.w (8,a3),d1
                "d081",               # add.l d1,d0
                "0680", f"{x_word:08x}",  # addi.l #x_word,d0
                "2f00",               # move.l d0,-(sp)       the address
                "1012 3f00",          # move.b (a2),d0 / move.w d0,-(sp)   the DSP
                "4eb9 0010c32e",      # jsr $10C32E           read X
                "5c8f",               # addq.l #6,sp
                "0280", f"{mask:08x}",  # andi.l #mask,d0
                "4cdf 0c04",          # movem.l (sp)+,d2/a2-a3
                "4e75")               # rts


def connection_routine(inputs, outputs, part=1, led=None, meter=None):
    """A type's +$0C: patches each input's address into its code words ({input: [words]}) with
    $124202, and every output's ([(output, word)]) with $1243DA, like Clavia's (CompareAB's,
    ClkDivFix's). part: 0 audio, 1 control. Branches are word-sized, resolved here."""
    head = m68k("48e7 0030",      # movem.l a2-a3,-(sp)
                "246f 000c",      # movea.l (12,sp),a2   the connection
                "266f 0010",      # movea.l (16,sp),a3
                "7000",           # moveq #0,d0
                "102a 0005")      # move.b (5,a2),d0     which input, or -1: the outputs
    end = m68k("4cdf 0c00", "4e75")  # movem.l (sp)+,a2-a3 / rts
    cases = [(i, b"".join(m68k("3f3c", f"{w:04x}",       # move.w #word,-(sp)
                               "2f0b 2f0a",              # move.l a3,-(sp) / move.l a2,-(sp)
                               "3f3c", f"{part:04x}",    # move.w #part,-(sp)
                               "4eb9 00124202",          # jsr $124202
                               "4fef 000c") for w in ws))  # lea (12,sp),sp
             for i, ws in sorted(inputs.items())]
    outs = b"".join(m68k("3f3c", f"{w:04x}", "3f3c", f"{o:04x}",  # word, output
                         "2f0a", "3f3c", f"{part:04x}",           # a2, part
                         "4eb9 001243da", "4fef 000a") for o, w in outputs)
    if meter:
        # a led-array (a sequencer's step), on the slot's meter list, as the CtrlSeq does:
        # $1169BA(slot, section, module, value routine, 0)
        outs += m68k("4267",                         # clr.w -(sp)
                     "4879", f"{meter:08x}",         # pea value routine
                     "102a 0003 3f00",               # move.b (3,a2),d0 / move.w d0,-(sp)   module
                     "102a 0001 3f00",               # move.b (1,a2),d0 / move.w d0,-(sp)   section
                     "1012 3f00",                    # move.b (a2),d0 / move.w d0,-(sp)     slot
                     "4eb9 001169ba",                # jsr $1169BA
                     "4fef 000c")                    # lea (12,sp),sp
    if led:
        # the module's LED, on the slot's LED list, as the RndPulsGen does: the OS keeps one
        # entry per module (a second call for the same module adds nothing)
        outs += m68k("4879", f"{led:08x}",          # pea value routine
                     "102a 0003 3f00",              # move.b (3,a2),d0 / move.w d0,-(sp)   module
                     "102a 0001 3f00",              # move.b (1,a2),d0 / move.w d0,-(sp)   section
                     "1012 3f00",                   # move.b (a2),d0 / move.w d0,-(sp)     slot
                     "4eb9 00116832",               # jsr $116832
                     "4fef 000a")                   # lea (10,sp),sp
    cases.append((0xFF, outs))
    tests_len = 8 * len(cases)                      # cmpi.b #n,d0 (4) + beq.w (4) each
    body_at = len(head) + tests_len + len(end)
    tests, bodies, at = b"", b"", body_at
    for n, (key, body) in enumerate(cases):
        here = len(head) + 8 * n + 4                # the beq.w's address
        tests += m68k("0c00", f"{key:04x}", "6700", f"{(at - (here + 2)) & 0xFFFF:04x}")
        jump_from = at + len(body)                  # bra.w back to end
        bodies += body + m68k("6000", f"{(len(head) + tests_len - (jump_from + 2)) & 0xFFFF:04x}")
        at += len(body) + 4
    return head + tests + end + bodies


def record_words(params):
    """The descriptor's word at +$24: the size, in words, of the module's record in the OS's RAM
    ($24 bytes and 8 a parameter). The OS places the next module's record after it: a size too
    small and a module added later is written over this one's parameters."""
    return (0x24 + 8 * params) // 2


def write_x_routine(x_word, transform=""):
    """A parameter's value routine for $10C49E: d2 = the value (as +$00 handed it over), the
    68k in `transform` turns it into d0, written to the module's X word with $10D142(module,
    value, X word), as ClkDiv's own routines do. Without a transform, d0 = the value."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "242f 0014",          # move.l (20,sp),d2     the value
                "246f 0010",          # movea.l (16,sp),a2    the module
                transform or "2002",  # ... d0 (move.l d2,d0)
                "3f3c", f"{x_word:04x}",  # move.w #x_word,-(sp)
                "2f00 2f0a",          # move.l d0,-(sp) / move.l a2,-(sp)
                "4eb9 0010d142",      # jsr $10D142
                "4fef 000a",          # lea (10,sp),sp
                "4cdf 0c04",          # movem.l (sp)+,d2/a2-a3
                "4e75")               # rts


def param_routines(b, callbacks):
    """A type's +$00 and +$04 for parameters handled by routines of ours: +$00 hands every
    parameter's value over unchanged; +$04 calls $10C49E with the routine of that parameter
    (callbacks[i], placed with b.put) and, for any other, answers $10C49C as ClkDiv's does."""
    p00 = b.put(m68k("7000 102f 0009 4e75"))   # moveq #0,d0 / move.b (9,sp),d0 / rts
    head = m68k("226f 0004 206f 0008",          # movea.l (4,sp),a1 / movea.l (8,sp),a0
                "7000 1029 0004")               # moveq #0,d0 / move.b (4,a1),d0: which parameter
    default = m68k("203c 0010c49c 4e75")         # move.l #$10C49C,d0 / rts
    tests_len = 8 * len(callbacks)
    body_at = len(head) + tests_len + len(default)
    tests, bodies = b"", b""
    for i, cb in enumerate(callbacks):
        here = len(head) + 8 * i + 4
        tests += m68k("0c00", f"{i:04x}", "6700", f"{(body_at + len(bodies) - (here + 2)) & 0xFFFF:04x}")
        bodies += m68k("4879", f"{cb:08x}",      # pea routine
                       "2f08 2f09",              # move.l a0,-(sp) / move.l a1,-(sp)
                       "4eb9 0010c49e",          # jsr $10C49E
                       "4fef 000c 4e75")         # lea (12,sp),sp / rts
    return p00, b.put(head + tests + default + bodies)


def write_table_routine(x_word, table_at, width):
    """A parameter's value routine for $10C49E that writes a row of a table: for the value v it
    writes the `width` signed bytes at table_at + v * width to the module's X words x_word,
    x_word + 1..., each with $10D142 as write_x_routine does."""
    return m68k("48e7 3030",          # movem.l d2-d3/a2-a3,-(sp)
                "242f 0018",          # move.l (24,sp),d2     the value
                "246f 0014",          # movea.l (20,sp),a2    the module
                "47f9", f"{table_at:08x}",  # lea table,a3
                "c4fc", f"{width:04x}",     # mulu.w #width,d2
                "d7c2",               # adda.l d2,a3          the row
                "7600",               # moveq #0,d3
                # loop:
                "101b 4880 48c0",     # move.b (a3)+,d0 / ext.w d0 / ext.l d0
                "3203",               # move.w d3,d1
                "0641", f"{x_word:04x}",    # addi.w #x_word,d1
                "3f01 2f00 2f0a",     # move.w d1,-(sp) / move.l d0,-(sp) / move.l a2,-(sp)
                "4eb9 0010d142",      # jsr $10D142
                "4fef 000a",          # lea (10,sp),sp
                "5243",               # addq.w #1,d3
                "0c43", f"{width:04x}",     # cmpi.w #width,d3
                "66dc",               # bne.s loop
                "4cdf 0c0c",          # movem.l (sp)+,d2-d3/a2-a3
                "4e75")               # rts


class Param:
    """A parameter of a control type: its name and maximum (param_table), and the X word its
    value is written to, through a 68k transform (write_x_routine; none: the value as it is),
    or, with a table (a row of signed bytes for each value), the X words from x_word on that
    take the value's row (write_table_routine), or a routine of its own (routine: a callable that
    places it with b.put and returns its address)."""

    def __init__(self, name, maximum, x_word, transform="", table=None, routine=None):
        self.name, self.maximum, self.x_word, self.transform = name, maximum, x_word, transform
        self.table, self.custom = table, routine
        if table is not None:
            assert len(table) == maximum + 1 and len({len(r) for r in table}) == 1

    def routine(self, b):
        if self.custom is not None:          # a routine of its own, placed by the callable
            return self.custom(b)
        if self.table is None:
            return b.put(write_x_routine(self.x_word, self.transform))
        width = len(self.table[0])
        at = b.put(bytes(v & 0xFF for row in self.table for v in row))
        return b.put(write_table_routine(self.x_word, at, width))


BRANCH = re.compile(r"^\s+(b|j)(cc|cs|ec|eq|es|ge|gt|lc|le|ls|lt|mi|ne|nn|nr|pl|ra|sr)\b", re.M)


def control_type(b, new_type, asm, x_init, params=(), led=None, steps=None, bits=None):
    """A control-rate type, described once: its DSP code (dsp/<asm>, its inputs and outputs from
    the @inN/@outN marks), the initial values of its X words, its parameters and maybe one LED
    (the X word it shows) or a row of step LEDs (steps: the X word with the step, the last step)
    or of bit LEDs (bits: the X word, the mask of the bits shown, up to 14).
    Everything the OS reads about the type is derived from that: the counts
    at +$18, the parameter table, the parameter routines (+$00, +$04, and ClkDiv's +$08, which
    answers 0: the value goes through our routine), the connection routine, and the descriptor
    (outputs, cycles, X and P words, the record's size). Each of those, copied by hand from a
    donor, has broken once (NOTES.md)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dspasm
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dsp", asm)
    code, marks, _ = dspasm.assemble(path)
    inputs = {int(k[2:]): v for k, v in marks.items() if re.fullmatch(r"in\d+", k)}
    outputs = {int(k[3:]): v for k, v in marks.items() if re.fullmatch(r"out\d+", k)}
    assert sorted(inputs) == list(range(len(inputs))) and sorted(outputs) == list(range(len(outputs)))
    assert all(len(v) == 1 for v in outputs.values()), "an output is written at one word"
    for p in params:
        assert p.x_word + (len(p.table[0]) if p.table else 1) <= len(x_init)
    fields = {}
    if params:
        fields[0x00], fields[0x04] = param_routines(
            b, [p.routine(b) for p in params])
        fields[0x1C] = b.put(param_table([(p.name, p.maximum) for p in params]))
    led_at = b.put(led_routine(led)) if led is not None else None
    meter_at = (b.put(value_routine(*steps)) if steps is not None
                else b.put(bits_routine(*bits)) if bits is not None else None)
    fields[0x0C] = b.put(connection_routine(inputs, [(o, w[0]) for o, w in sorted(outputs.items())],
                                            led=led_at, meter=meter_at))
    x_at = b.put(words(*x_init))
    p_at = b.put(words(*code))
    # the descriptor: ClkDiv's (control part only), with every field we know of set here, and
    # the ones we do not know zero in it, as checked
    desc = bytearray(b.rom_bytes(0x14ADBC, 0x30))
    known = {0x06, 0x08, 0x1A, 0x1E, 0x20, 0x22, 0x24}
    assert all(desc[o:o + 2] == b"\0\0" for o in range(0, 0x30, 2) if o not in known)
    branches = len(BRANCH.findall(open(path).read()))
    desc[0x06:0x08] = (len(code) + 4 * branches).to_bytes(2, "big")  # control cycles, worst case
    desc[0x08:0x0A] = len(outputs).to_bytes(2, "big")        # outputs: the OS gives each its own word
    desc[0x1A:0x1C] = len(x_init).to_bytes(2, "big")         # control X words
    desc[0x1E:0x20] = (0).to_bytes(2, "big")                 # control Y words
    desc[0x20:0x24] = len(code).to_bytes(4, "big")           # control P words
    desc[0x24:0x26] = record_words(len(params)).to_bytes(2, "big")   # its record
    fields[0x28] = b.put(desc)
    fields[0x24] = b.put(words(x_at, x_at, p_at, x_at, x_at, p_at) + bytes.fromhex("fffe"))
    fields[0x08] = 0x136EFE
    fields[0x18] = (len(params) << 24) | (len(inputs) << 16) | (len(outputs) << 8)
    b.specs[new_type] = ([p.maximum for p in params], len(inputs), len(outputs))
    b.add_type(new_type, 69, fields)


def flipflop(b, new_type=120):
    """The G2's FlipFlop: D-type or RS-type, with Rst, Q and NotQ, and an LED on Q (one LED a
    module on a G1)."""
    control_type(b, new_type, "flipflop.asm",
                 (0x200000, 0, 0, 0, 0),             # high, Type, Clk's last, In's last, Q
                 [Param("Type", 1, 1)], led=4)


def seq5(b, new_type=123):
    """5-Step Seq: Clk and Rst in, Out, five bipolar knobs (-64..+63 units), the step's LEDs."""
    # value v = 0..127: (v - 64) control units, a unit being $8000
    #   move.l d2,d0 / subi.l #64,d0 / moveq #15,d1 / asl.l d1,d0
    bipolar = "2002 0480 00000040 720f e3a0"
    control_type(b, new_type, "seq5.asm",
                 # the step (the last: the first clock plays the first), Clk's last, Rst's last,
                 # armed, the values
                 (4, 0, 0, 0, 0, 0, 0, 0, 0),
                 [Param(f"Step {i + 1}", 127, 4 + i, bipolar) for i in range(5)],
                 steps=(0, 4))


def turing(b, new_type=124):
    """Turing Machine: Clk in; CV and eight gates (bits 0-7) out; Prob, Length (1-16), Lock and
    Scale; eight LEDs, the register's low byte."""
    control_type(b, new_type, "turing.asm",
                 # the noise's taps and seed (as the Noise S&H's), Clk's last, the register, the
                 # mask (Length 16), the threshold, Lock, $FFFF, $FF, high, Scale (1)
                 (0xE10000, 0x5A3C96, 0, 0x9D2B, 0x8000, 0, 0, 0xFFFF, 0xFF, 0x200000, 0x7FFE00),
                 # Prob, bipolar as the original's big knob: value v = 0..127, the threshold
                 # (127 - v) << 16, a chance of (127 - v)/128: 127 (right) locked, 64 (centre)
                 # random, 0 (left) nearly every bit flipped, the pattern inverted each pass
                 #   moveq #127,d0 / sub.l d2,d0 / swap d0 / clr.w d0
                 [Param("Prob", 127, 5, "707f 9082 4840 4240"),
                  # Length: value v = 0..15 for 1..16, the mask 1 << v
                  #   moveq #1,d0 / move.l d2,d1 / asl.l d1,d0
                  Param("Length", 15, 4, "7001 2202 e3a0"),
                  Param("Lock", 1, 6),
                  # Scale: value v = 0..127, the fraction (v << 16) + (v << 9), 127 nearly 1
                  #   move.l d2,d0 / swap d0 / clr.w d0 / move.l d2,d1 / asl.l #8,d1 /
                  #   add.l d1,d1 / add.l d1,d0
                  Param("Scale", 127, 10, "2002 4840 4240 2202 e181 d281 d081")],
                 bits=(3, 0xFF))


def counter8(b, new_type=126):
    """8Counter: Clk and Rst in, eight outputs, one high a step, and a row of eight step LEDs."""
    control_type(b, new_type, "counter8.asm",
                 # the step (the last: the first clock plays the first), Clk's last, Rst's last,
                 # armed, high
                 (7, 0, 0, 0, 0x200000),
                 steps=(0, 7))


def mux8(b, new_type=101):
    """Mux8-1: In 1-8 and Ctrl in, Out; the G2's Mux8-1 and Sw8-1 in one type: Sel (1-8) plus
    Ctrl (8 units a step) picks the input; eight LEDs show which."""
    control_type(b, new_type, "mux8.asm", (7, 0, 0), [Param("Sel", 7, 1)], steps=(2, 7))


def seed_routine(x_seed, x_voice, x_load):
    """The Random's Seed routine, for $10C49E: writes the seed's value, (v + 1) * $9E37, to X word
    x_seed, the voice's, voice * $B5A3, to x_voice, and 1 to x_load, so the next clock loads the
    seed (a clock can come before the seed is written while a patch is set up; and a Seed turned
    live starts its values at the next clock). The OS calls it once a voice, with the voice in
    the byte at 2 of the module's structure (as $10D142 reads it)."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "242f 0014",          # move.l (20,sp),d2     the value
                "246f 0010",          # movea.l (16,sp),a2    the module
                "2002 5280",          # move.l d2,d0 / addq.l #1,d0
                "c0fc 9e37",          # mulu.w #$9E37,d0
                "3f3c", f"{x_seed:04x}",  # move.w #x_seed,-(sp)
                "2f00 2f0a",          # move.l d0,-(sp) / move.l a2,-(sp)
                "4eb9 0010d142",      # jsr $10D142
                "4fef 000a",          # lea (10,sp),sp
                "7000 102a 0002",     # moveq #0,d0 / move.b (2,a2),d0   the voice
                "c0fc b5a3",          # mulu.w #$B5A3,d0
                "3f3c", f"{x_voice:04x}",  # move.w #x_voice,-(sp)
                "2f00 2f0a",
                "4eb9 0010d142",
                "4fef 000a",
                "7001",               # moveq #1,d0
                "3f3c", f"{x_load:04x}",   # move.w #x_load,-(sp)
                "2f00 2f0a",
                "4eb9 0010d142",
                "4fef 000a",
                "4cdf 0c04",          # movem.l (sp)+,d2/a2-a3
                "4e75")               # rts


def random(b, new_type=6):
    """Random: Clk and Rst in; Out and Trig; Seed, Poly, Step, Edge, Prob and Length."""
    control_type(b, new_type, "random.asm",
                 # taps, the register, Clk's last, Rst's last, load (yes), count, Length (free),
                 # seed, voice, Poly, Step, target, Out (2), Edge's factor, Prob, gate, high
                 (0xE10000, 0x5A3C96, 0, 0, 1, 0, 0x7FFFFF, 0x9E37, 0, 0, 0x7FFE00, 0, 0, 0,
                  0x7FFFFF, 0x400000, 0, 0x200000),
                 [Param("Seed", 127, 7, routine=lambda b: b.put(seed_routine(7, 8, 4))),
                  # value 1: $FFFFFF, else 0
                  #   moveq #0,d0 / tst.l d2 / beq.s +6 / move.l #$FFFFFF,d0
                  Param("Poly", 1, 9, "7000 4a82 6706 203c 00ffffff"),
                  # Step: the fraction (v << 16) + (v << 9), 127 nearly 1
                  Param("Step", 127, 10, "2002 4840 4240 2202 e181 d281 d081"),
                  # Edge: the glide factor ($800000 - (v & 7) << 19) >> (v >> 3), less 1: 1 for
                  # 0 (no glide), halving every 8, about 2^-16 for 127
                  #   move.l d2,d1 / andi.l #7,d1 / moveq #19,d0 / lsl.l d0,d1 /
                  #   move.l #$800000,d0 / sub.l d1,d0 / move.l d2,d1 / lsr.l #3,d1 /
                  #   lsr.l d1,d0 / subq.l #1,d0
                  Param("Edge", 127, 14, "2202 0281 00000007 7013 e1a9 203c 00800000 9081 "
                                         "2202 e689 e2a8 5380"),
                  # Prob: (v << 16) + (v << 9) + (v << 2), 127 above every draw: always
                  #   ... / move.l d2,d1 / asl.l #2,d1 / add.l d1,d0
                  Param("Prob", 127, 15, "2002 4840 4240 2202 e181 d281 d081 2202 e581 d081"),
                  # Length: v, or $7FFFFF (never) for 0
                  #   move.l d2,d0 / bne.s +6 / move.l #$7FFFFF,d0
                  Param("Length", 16, 6, "2002 6606 203c 007fffff")])


def bits(b, new_type=41):
    """Bits: the G2's BinCounter, ADConv and DAConv in one, by Mode (Count, A>D, D>A): Clk, Rst,
    In and B1-B8 in; Out and Bit 1-8; eight LEDs with the byte."""
    control_type(b, new_type, "bits.asm",
                 # the byte, Clk's last, Rst's last, armed, Mode (Count), high, 255, the counter
                 # (255: the first clock gives 0), unused, 1
                 (0, 0, 0, 0, 0, 0x200000, 255, 255, 0, 1),
                 [Param("Mode", 2, 4)], bits=(0, 0xFF))


# The Scale Quantizer's scales: (name, the notes in it, as semitones from the root)
SCALES = [
    ("Chromatic", range(12)),
    ("Major", (0, 2, 4, 5, 7, 9, 11)),
    ("Minor", (0, 2, 3, 5, 7, 8, 10)),
    ("Dorian", (0, 2, 3, 5, 7, 9, 10)),
    ("Phrygian", (0, 1, 3, 5, 7, 8, 10)),
    ("Lydian", (0, 2, 4, 6, 7, 9, 11)),
    ("Mixolydian", (0, 2, 4, 5, 7, 9, 10)),
    ("Locrian", (0, 1, 3, 5, 6, 8, 10)),
    ("Harmonic minor", (0, 2, 3, 5, 7, 8, 11)),
    ("Melodic minor", (0, 2, 3, 5, 7, 9, 11)),
    ("Major pentatonic", (0, 2, 4, 7, 9)),
    ("Minor pentatonic", (0, 3, 5, 7, 10)),
    ("Blues", (0, 3, 5, 6, 7, 10)),
    ("Whole tone", (0, 2, 4, 6, 8, 10)),
    ("Hirajoshi", (0, 2, 3, 7, 8)),
    ("Double harmonic", (0, 1, 4, 5, 7, 8, 11)),
]


def corrections(notes):
    """For each note 0..11 of the key, the distance to the nearest note of the scale (an octave
    up or down counts), the lower one on a tie."""
    row = []
    for k in range(12):
        best = min((abs(d), d) for n in notes for o in (-12, 0, 12) for d in [n + o - k])
        row.append(best[1])
    return row


def quant(b, new_type=125):
    """Scale Quantizer: In and Out; Root, Scale (by name) and Octave."""
    control_type(b, new_type, "quant.asm",
                 # half a semitone, Root (C), 12 * Octave (0), 136 (0 is an E, and m kept
                 # positive), ceil(2^23 / 12), the corrections (Chromatic: none), unused
                 (0x4000, 0, 0, 136, (2 ** 23 + 11) // 12) + (0,) * 12 + (0,),
                 [Param("Root", 11, 1),
                  Param("Scale", len(SCALES) - 1, 5, table=[corrections(n) for _, n in SCALES]),
                  # Octave: value v = 0..8 for -4..+4, 12 * (v - 4) semitones
                  #   move.l d2,d0 / subq.l #4,d0 / muls.w #12,d0
                  Param("Octave", 8, 2, "2002 5980 c1fc 000c")])


# name: (what it shows, the new types, or the DSP words to change in place)
EXPERIMENTS = {
    "mixer3-silent": (
        "Mixer (3): the rounding multiply-accumulate becomes clr a, so the module is mute",
        None, [(0x1493CE + 5 * 4, 0x2000A3, 0x200013)],
    ),
    "all": (
        "every new type: 120 (FlipFlop), 121 (Mix1-1A), 123 (5-Step Seq), 124 (Turing Machine), "
        "125 (Scale Quantizer), 126 (8Counter), 101 (Mux8-1), 6 (Random), 41 (Bits)",
        [flipflop, mix1_1a, seq5, turing, quant, counter8, mux8, random, bits], [],
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
        print(f"new types {b.types}, {b.at - RUN} bytes, stored at ${STAGE:06X}, run at ${RUN:06X}")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst + ".tmp", "wb").write(rom)
    os.replace(dst + ".tmp", dst)   # never a half-written ROM for an emulator starting meanwhile
    print(f"{name}: written {dst}")


if __name__ == "__main__":
    main()
