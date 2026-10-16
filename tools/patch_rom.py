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
    assert block[0x88:0x8A] == bytes.fromhex("feff")   # audio part's nop 2 from the end
    assert b.put(block) == new
    fields.update({0x24: new + 0x70, 0x28: new + 0x04, 0x2C: new + 0x00})
    if io:
        fields[0x18] = (io[0] << 24) | (io[1] << 16) | (io[2] << 8)   # parameters, inputs, outputs
    b.add_type(new_type, 19, fields)


def mixer_inv(b, new_type=119):
    """The Mixer (3) with input 1 inverted: mpy -x1,x0,a instead of mpy x1,x0,a."""
    mixer3_variant(b, new_type, code_patch={2: (0x44DBA0, 0x44DBA4)})


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


def connection_routine(inputs, outputs, part=1, led=None):
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


def flipflop(b, new_type=120):
    """The G2's FlipFlop: D-type or RS-type, with Rst, Q and NotQ (dsp/flipflop.asm). Built on
    ClkDiv (type 69), a control-rate type with one parameter, whose +$00 hands the parameter's
    value over unchanged; its +$04 is copied to call our own routine, which writes the Type into
    X[1]."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dspasm
    code, marks, _ = dspasm.assemble(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "dsp", "flipflop.asm"))
    x_init = (0x200000, 0, 0, 0, 0)            # high, Type, Clk's last, In's last, Q
    # the parameter: ClkDiv's +$04 ($136E86) calls $10C49E with a routine for the value; ours
    # writes it to X[1] with $10D142(module, value, X word), as ClkDiv's does for its words
    write_type = b.put(m68k("48e7 2030",        # movem.l d2/a2-a3,-(sp)
                            "242f 0014",        # move.l (20,sp),d2     the value
                            "246f 0010",        # movea.l (16,sp),a2    the module
                            "3f3c 0001",        # move.w #1,-(sp)       X[1]
                            "2f02 2f0a",        # move.l d2,-(sp) / move.l a2,-(sp)
                            "4eb9 0010d142",    # jsr $10D142
                            "4fef 000a",        # lea (10,sp),sp
                            "4cdf 0c04",        # movem.l (sp)+,d2/a2-a3
                            "4e75"))            # rts
    param = bytearray(b.rom_bytes(0x136E86, 0x2E))
    at = param.find(bytes.fromhex("487900136eb4"))   # pea $136EB4: ClkDiv's own routine
    assert at > 0 and param[-2:] == bytes.fromhex("4e75")
    param[at + 2:at + 6] = write_type.to_bytes(4, "big")
    param_at = b.put(param)
    led_at = b.put(led_routine(4))                # Q's LED (X[4]); one LED per module on a G1
    conn_at = b.put(connection_routine(
        {0: marks["in0"], 1: marks["in1"], 2: marks["in2"]},
        [(0, marks["out0"][0]), (1, marks["out1"][0])], led=led_at))
    names_at = b.put(param_table([("Type", 1)]))
    x_at = b.put(words(*x_init))
    p_at = b.put(words(*code))
    desc = bytearray(b.rom_bytes(0x14ADBC, 0x30))   # ClkDiv's descriptor: control part only
    assert desc[0x1A:0x1C] == (7).to_bytes(2, "big") and desc[0x22:0x24] == (20).to_bytes(2, "big")
    desc[0x08:0x0A] = (2).to_bytes(2, "big")                 # outputs: the OS gives each its own word
    desc[0x06:0x08] = (len(code) + 16).to_bytes(2, "big")    # control cycles, branches included
    desc[0x1A:0x1C] = len(x_init).to_bytes(2, "big")         # control X words
    desc[0x1E:0x20] = (0).to_bytes(2, "big")                 # control Y words
    desc[0x20:0x24] = len(code).to_bytes(4, "big")           # control P words
    desc_at = b.put(desc)
    data_at = b.put(words(x_at, x_at, p_at, x_at, x_at, p_at) + bytes.fromhex("fffe"))
    b.add_type(new_type, 69, {0x04: param_at, 0x0C: conn_at, 0x18: 0x01030200, 0x1C: names_at,
                              0x24: data_at, 0x28: desc_at})


def noise_sh(b, new_type=122):
    """Noise S&H (dsp/noise_sh.asm): Trig in; Out and Inv out; no parameters. Built on CompareAB
    (type 89), control rate with no parameters."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dspasm
    code, marks, _ = dspasm.assemble(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "dsp", "noise_sh.asm"))
    x_init = (0xE10000, 0x5A3C96, 0, 0)        # taps (x^24+x^23+x^22+x^17+1), seed, Trig's last, held
    conn_at = b.put(connection_routine({0: marks["in0"]},
                                       [(0, marks["out0"][0]), (1, marks["out1"][0])]))
    x_at = b.put(words(*x_init))
    p_at = b.put(words(*code))
    desc = bytearray(b.rom_bytes(0x14A4EE, 0x30))   # CompareAB's descriptor: control part only
    assert desc[0x22:0x24] == (6).to_bytes(2, "big")
    desc[0x06:0x08] = (len(code) + 8).to_bytes(2, "big")     # control cycles, branches included
    desc[0x08:0x0A] = (2).to_bytes(2, "big")                 # two outputs, a word each
    desc[0x1A:0x1C] = len(x_init).to_bytes(2, "big")         # control X words
    desc[0x1E:0x20] = (0).to_bytes(2, "big")                 # control Y words
    desc[0x20:0x24] = len(code).to_bytes(4, "big")           # control P words
    desc_at = b.put(desc)
    data_at = b.put(words(x_at, x_at, p_at, x_at, x_at, p_at) + bytes.fromhex("fffe"))
    b.add_type(new_type, 89, {0x0C: conn_at, 0x18: 0x00010200, 0x24: data_at, 0x28: desc_at})


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
        "every new type: 119 (Mixer Inv), 120 (FlipFlop), 121 (Mix1-1A), 122 (Noise S&H)",
        [mixer_inv, flipflop, mix1_1a, noise_sh], [],
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
