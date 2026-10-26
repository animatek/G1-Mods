"""What every module's build uses: the OS's layout (rack OS 3.03), the package the new types go
into (Build), and the routines a type is made of (control_type, audio_type, mixer3_variant...).

A module (modules/<name>/build.py) calls these; tools/patch_rom.py puts the modules together
into the user's ROM. How it all works: NOTES.md.
"""
import os
import re
import sys

import lz

ROM_SHA256 = "d9b199f2"  # start of the rack OS 3.03's sha256 (G1-Emu/NOTES.md, "The ROM")
ROM_SIZE = 512 * 1024

# Where the new types live (NOTES.md, "The first real G1"). An OS update erases only the flash's
# sectors 0-5, so an OS image ends before RAM $15FFE0; Clavia's OS ends at $15DFDF, which leaves
# 8 KB. The package is stored there (STAGE to BOOT), and the bootstrap after it (BOOT, the run's
# last 52 bytes) copies it at boot to RUN, RAM the OS never uses, where it runs. The bootstrap
# runs from the RAM copy of the image (the OS leaves those bytes alone until well after the types
# are registered), but copies the package from the flash's copy, which nothing overwrites.
STAGE = 0x15DFE0          # in the image, right after Clavia's OS: the package
STAGE_END = 0x15FFE0      # where an update stops erasing ($360000 in the flash)
BOOT_LEN = 0x34
BOOT = STAGE_END - BOOT_LEN
ROOM = BOOT - STAGE       # 8,140 bytes for the package
FLASH_OS = 0x300020       # the flash's copy of the image: RAM address X is at FLASH_OS + X - $100000
# A package too big for that goes packed (tools/lz.py), the bootstrap unpacking it with UNLZ.
UNLZ = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "unlz.m68k"), "rb").read()
# A package too big even packed still runs in G1-Emu, which boots the ROM's OS into its flash up to
# $70000: the old layout, in two runs the OS leaves alone until after the registration. Such a
# build cannot go into a real G1 (g1update.py refuses its image).
EMU_STAGES = ((0x166574, 0x16B078), (0x16B07A, 0x16FB7E))   # the OS writes $16B078 and $16FB7E
FREE = RUN = 0x1C6000      # where the package runs: every address in it is a RUN address
FREE_END = 0x1E8000        # (the OS leaves $1C57F0-$1EFECF alone; 32 KB kept below its stacks)
LIST_LAST_JSR = 0x10DF1E  # the registration list's last jsr (type 17's, $143350)
LIST_LAST_TARGET = 0x143350


# The mark an OS with modules carries, for an editor to tell it apart: its IAm says version 3.09
# instead of 3.03. The IAm is built by $10B252 (move.b #$03 for the minor at (8,a2)); a version
# Clavia never released, which Clavia's editor 3.03 still takes (it checks the major and the
# minor's tens only: 3.00 to 3.09). NME reads it as "this synth has G1-Mods" (NOTES.md, "The mark").
MODS_VERSION_LOW = 9
VERSION_MARK = (0x10B288, 0x157C0003, 0x157C0000 | MODS_VERSION_LOW)   # move.b #9,(8,a2)


def ram_to_rom(addr):
    return addr - 0x100000 + 0xC800


# The types the OS leaves free: its table has 128 (0-127, and a patch keeps a type in 7 bits, so
# there can be no more), and these are the ones without a module (unregistered entries in a RAM
# dump after boot, none in NME's modules.xml). 0 is left out, as "no module" may be read into it.
# Which module has which is modules/registry.json; what is left has to be spent with care
# (PORTING.md). 119 (the Mixer Inv, a first test) and 122 (the Noise S&H, easy to patch from G1
# modules) were taken out on 2026-10-17 to free them.
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
        self.calls = {}         # a jsr's address: (the OS's target, ours), see redirect_call

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

    def redirect_call(self, at, old_target, new_target):
        """Points the OS's `jsr old_target.l` at `at` to new_target, a routine in the package that
        calls old_target itself. One module a call: two would need to chain."""
        assert at not in self.calls, f"the call at ${at:06X} is taken already"
        self.calls[at] = (old_target, new_target)

    def patches(self):
        """The redirected calls, as (address, old bytes, new bytes) of each jsr's target."""
        return [(at + 2, old.to_bytes(4, "big"), new.to_bytes(4, "big"))
                for at, (old, new) in sorted(self.calls.items())]

    def finish(self):
        """Returns ([(RAM address in the image, bytes)], hook, installable): the package with its
        registration routine at the end, and a bootstrap that copies it to RUN and calls it. In
        the update's room as it is if it fits; else packed (tools/lz.py), with the bootstrap
        unpacking it (tools/unlz.s); else in the emulator-only layout."""
        reg = self.put(b"".join(self.register) + bytes.fromhex("4e75"))   # ...rts
        package = b"".join(data for _, data in self.blocks)
        assert len(package) == self.at - RUN
        call = m68k("4eb9", f"{LIST_LAST_TARGET:08x}")   # jsr $143350: the call it replaces
        done = m68k("4eb9", f"{reg:08x}",                # jsr registration
                    "4e75")                              # rts
        if len(package) <= ROOM:
            boot = call + copy_routine(FLASH_OS + STAGE - 0x100000, package) + done
            boot += bytes.fromhex("4e71") * ((BOOT_LEN - len(boot)) // 2)   # nop
            return [(STAGE, package), (BOOT, boot)], self._hook(BOOT), True
        packed = lz.pack(package)
        assert lz.unpack(packed, len(package)) == package
        head = call + m68k("2f0a",                                   # move.l a2,-(sp)
                           "41f9", f"{FLASH_OS + STAGE - 0x100000:08x}",   # lea packed (flash),a0
                           "43f9", f"{RUN:08x}",                     # lea RUN,a1
                           "45f9", f"{RUN + len(package):08x}",      # lea RUN+length,a2
                           "6100 000c",                              # bsr.w unlz
                           "245f") + done                            # movea.l (sp)+,a2
        assert len(head) == 40      # the bsr's displacement: unlz right after
        boot = head + UNLZ
        at = (STAGE_END - len(boot)) & ~1
        if STAGE + len(packed) <= at:
            return [(STAGE, packed), (at, boot)], self._hook(at), True
        (s1, e1), (s2, e2) = EMU_STAGES
        first, rest = package[:e1 - s1 - BOOT_LEN], package[e1 - s1 - BOOT_LEN:]
        assert len(rest) <= e2 - s2, f"the package ({len(package)} bytes) does not fit the stages"
        boot = call + copy_routine(s1 + BOOT_LEN, first) + (
            copy_routine(s2, rest, RUN + len(first)) if rest else b"") + done
        assert len(boot) <= BOOT_LEN
        boot += bytes.fromhex("4e71") * ((BOOT_LEN - len(boot)) // 2)   # nop
        blocks = [(s1 + BOOT_LEN, first)] + ([(s2, rest)] if rest else [])
        return blocks + [(s1, boot)], self._hook(s1), False

    @staticmethod
    def _hook(at):
        return LIST_LAST_JSR + 2, LIST_LAST_TARGET.to_bytes(4, "big"), at.to_bytes(4, "big")


def copy_routine(src, data, dst=RUN):
    """68k: copies len(data) bytes from src to dst (a1 runs on when dst is left out)."""
    return m68k("41f9", f"{src:08x}",                              # lea src,a0
                *(("43f9", f"{dst:08x}") if dst == RUN else ()),    # lea RUN,a1
                "303c", f"{len(data) - 1:04x}",                    # move.w #n-1,d0
                "12d8",                                            # move.b (a0)+,(a1)+
                "51c8 fffc")                                       # dbra d0,*-2


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


def write_audio_x_routine(x_word, transform=""):
    """A parameter's value routine for $10C49E, for a type's audio part: as write_x_routine, but
    through the OS's own audio writer: $10C4B0(module, request, word) fills a 12-byte request
    (the DSP, the address: the voice's audio X base at +2 of its entry + the module's at +6 + the
    word, and $B5) and $10C248(request, value) writes it (NOTES.md, "Room for code")."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "242f 0014",          # move.l (20,sp),d2     the value
                "246f 0010",          # movea.l (16,sp),a2    the module
                transform or "2002",  # ... d0 (move.l d2,d0)
                "2400",               # move.l d0,d2          keep it
                "4fef fff4",          # lea (-12,sp),sp       the request
                "264f",               # movea.l sp,a3
                "3f3c", f"{x_word:04x}",  # move.w #x_word,-(sp)
                "2f0b 2f0a",          # move.l a3,-(sp) / move.l a2,-(sp)
                "4eb9 0010c4b0",      # jsr $10C4B0
                "4fef 000a",          # lea (10,sp),sp
                "2f02 2f0b",          # move.l d2,-(sp) / move.l a3,-(sp)
                "4eb9 0010c248",      # jsr $10C248
                "4fef 0014",          # lea (20,sp),sp        its arguments and the request
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
    path = asm if os.path.isabs(asm) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "dsp", asm)   # a module's, or dsp/'s
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


def audio_type(b, new_type, asm, x_init, params=(), x_words=None):
    """An audio-rate type, as control_type is a control-rate one: its DSP code runs every sample
    (the type's audio part; no control part). The descriptor is the Mixer (3)'s (audio only) with
    our counts; the parameters go to the audio X words (write_audio_x_routine). x_words, when
    larger than x_init, reserves more X (a buffer the code clears itself): the loader copies that
    many words from the X data, so past x_init it copies whatever follows, never used."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dspasm
    path = asm if os.path.isabs(asm) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "dsp", asm)   # a module's, or dsp/'s
    code, marks, _ = dspasm.assemble(path)
    inputs = {int(k[2:]): v for k, v in marks.items() if re.fullmatch(r"in\d+", k)}
    outputs = {int(k[3:]): v for k, v in marks.items() if re.fullmatch(r"out\d+", k)}
    assert sorted(inputs) == list(range(len(inputs))) and sorted(outputs) == list(range(len(outputs)))
    assert all(len(v) == 1 for v in outputs.values()), "an output is written at one word"
    x_words = x_words or len(x_init)
    for p in params:
        assert p.x_word < len(x_init) and p.table is None
    fields = {}
    if params:
        fields[0x00], fields[0x04] = param_routines(
            b, [p.custom(b) if p.custom else b.put(write_audio_x_routine(p.x_word, p.transform))
                for p in params])
        fields[0x1C] = b.put(param_table([(p.name, p.maximum) for p in params]))
    fields[0x0C] = b.put(connection_routine(inputs, [(o, w[0]) for o, w in sorted(outputs.items())],
                                            part=0))
    x_at = b.put(words(*x_init))
    p_at = b.put(words(*code))
    desc = bytearray(b.rom_bytes(0x149382, 0x30))         # the Mixer (3)'s: audio only
    known = {0x02, 0x08, 0x0E, 0x12, 0x14, 0x16, 0x24}
    assert all(desc[o:o + 2] == b"\0\0" for o in range(0, 0x30, 2) if o not in known)
    branches = len(BRANCH.findall(open(path).read()))
    desc[0x02:0x04] = (len(code) + 4 * branches).to_bytes(2, "big")   # audio cycles, worst case
    desc[0x08:0x0A] = len(outputs).to_bytes(2, "big")
    desc[0x0E:0x10] = x_words.to_bytes(2, "big")                      # audio X words
    desc[0x12:0x14] = (0).to_bytes(2, "big")                          # audio Y words
    desc[0x14:0x18] = len(code).to_bytes(4, "big")                    # audio P words
    desc[0x24:0x26] = record_words(len(params)).to_bytes(2, "big")
    fields[0x28] = b.put(desc)
    # audio X, Y, P; the control part's (empty) the same; the nop slots: audio 2 words before the
    # end, control none (as the Mixer (3)'s)
    fields[0x24] = b.put(words(x_at, x_at, p_at, x_at, x_at, p_at) + bytes.fromhex("feff"))
    fields[0x08] = 0x136EFE
    fields[0x18] = (len(params) << 24) | (len(inputs) << 16) | (len(outputs) << 8)
    b.specs[new_type] = ([p.maximum for p in params], len(inputs), len(outputs))
    b.add_type(new_type, 19, fields)


def audio_write(x_word):
    """68k that writes d0 to the module's audio X word x_word (a2 the module), through the OS's
    $10C4B0 and $10C248 (write_audio_x_routine); d2 and d0 are lost, d3 and a2 kept."""
    return ("2400 4fef fff4 264f 3f3c" f"{x_word:04x}" " 2f0b 2f0a 4eb9 0010c4b0 4fef 000a"
            " 2f02 2f0b 4eb9 0010c248 4fef 0014")
