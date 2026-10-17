"""level: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "level.asm")


def build(b, new_type):
    """Level: the G2's ModAmt, MinMax, T&H and WindSw in one, by Mode: A and B in, Out 1 and 2;
    Amount, Lo and Hi."""
    # Lo, Hi: value v = 0..127, (v - 64) control units, a unit being $8000
    bipolar = "2002 0480 00000040 720f e3a0"
    control_type(b, new_type, ASM,
                 # Mode, Amount, Lo (-64), Hi (+63), held 1, high, 1, unused, held 2
                 (0, 0, 0xE00000, 0x1F8000, 0, 0x200000, 0x7FFFFF, 0, 0),
                 [Param("Mode", 3, 0),
                  # Amount: the fraction (v << 16) + (v << 9), 127 nearly 1
                  Param("Amount", 127, 1, "2002 4840 4240 2202 e181 d281 d081"),
                  Param("Lo", 127, 2, bipolar),
                  Param("Hi", 127, 3, bipolar)])
