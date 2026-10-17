"""turing-machine: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "turing.asm")


def build(b, new_type):
    """Turing Machine: Clk in; CV and eight gates (bits 0-7) out; Prob, Length (1-16), Lock and
    Scale; eight LEDs, the register's low byte."""
    control_type(b, new_type, ASM,
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
