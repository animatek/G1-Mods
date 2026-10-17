"""flipflop: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flipflop.asm")


def build(b, new_type):
    """The G2's FlipFlop: D-type or RS-type, with Rst, Q and NotQ, and an LED on Q (one LED a
    module on a G1)."""
    control_type(b, new_type, ASM,
                 (0x200000, 0, 0, 0, 0),             # high, Type, Clk's last, In's last, Q
                 [Param("Type", 1, 1)], led=4)
