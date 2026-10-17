"""bits: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bits.asm")


def build(b, new_type):
    """Bits: the G2's BinCounter, ADConv and DAConv in one, by Mode (Count, A>D, D>A): Clk, Rst,
    In and B1-B8 in; Out and Bit 1-8; eight LEDs with the byte."""
    control_type(b, new_type, ASM,
                 # the byte, Clk's last, Rst's last, armed, Mode (Count), high, 255, the counter
                 # (255: the first clock gives 0), unused, 1
                 (0, 0, 0, 0, 0, 0x200000, 255, 255, 0, 1),
                 [Param("Mode", 2, 4)], bits=(0, 0xFF))
