"""osc-string: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, audio_type, audio_write, m68k, words

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "string.asm")


def damp_routine(x_k, x_comp):
    """The Osc String's Damp routine: the lowpass's factor k = $100000 + v * $E000 to x_k, and
    the delay the lowpass adds at low notes, (1 - k) / k samples, times 4096, to x_comp, which the
    code takes from the period so Damp does not detune the string."""
    return m68k("48e7 3030",          # movem.l d2-d3/a2-a3,-(sp)
                "242f 0018",          # move.l (24,sp),d2     the value
                "246f 0014",          # movea.l (20,sp),a2    the module
                "2002 c0fc e000 0680 00100000",   # d0 = $100000 + v * $E000
                "2600",               # move.l d0,d3          k
                audio_write(x_k),
                "203c 00800000 9083", # move.l #$800000,d0 / sub.l d3,d0     1 - k
                "e188",               # lsl.l #8,d0
                "2203 e889",          # move.l d3,d1 / lsr.l #4,d1
                "4c41 0000",          # divu.l d1,d0          (1 - k) / k * 4096
                audio_write(x_comp),
                "4cdf 0c0c",          # movem.l (sp)+,d2-d3/a2-a3
                "4e75")


STRING_N = 1024          # the Osc String's line: 96000 / 1024 = 94 Hz its lowest note


def build(b, new_type):
    """Osc String: a plucked string (Karplus-Strong). Trig, Pitch and Exc in, Out; Note, Decay,
    Damp. Its line is STRING_N words of X, which its code clears."""
    n = STRING_N
    fr = lambda v: round(v * 2 ** 23)
    l135 = 96000 / (440 * 2 ** ((135 - 69) / 12))
    # 2^f ~ 1 + 0.6951786 f + 0.2261745 f^2 + 0.0786469 f^3 on 0..1, halved
    c0, c1, c2, c3 = 0.5, 0.6951786 / 2, 0.2261745 / 2, 0.0786469 / 2
    # Decay: the loss is a time knob's factor (the Random's Edge) / 8, the gain 1 less it:
    # 0.875 for 0, 1 - 2^-19 for 127
    decay = ("2202 0281 00000007 7013 e1a9 203c 00800000 9081 2202 e689 e2a8 5380"
             " e688 223c 007fffff 9280 2001")    # lsr.l #3,d0 / move.l #$7FFFFF,d1 / sub.l d0,d1 / move.l d1,d0
    audio_type(b, new_type, ASM,
               (64 << 15, 0x7FF000, 0x600000, 0, 0, 0, 0, 0x5A3C96, 0xE10000, round(l135 * 4096),
                135 << 15, 0x0AAAAB, fr(c3), fr(c2), fr(c1), fr(c0), (n - 2) * 4096, n, 0x7FFF,
                0xFFF, 0x200000, 0, 1, 100, 0, 26 + n),
               [Param("Note", 127, 0, "2002 720f e3a0"),   # v << 15
                Param("Decay", 127, 1, decay),
                # Damp: $100000 + v * $E000: dark at 0, all through at 127
                #   move.l d2,d0 / mulu.w #$E000,d0 / addi.l #$100000,d0
                Param("Damp", 127, 2, routine=lambda b: b.put(damp_routine(2, 24)))],
               x_words=26 + n)
