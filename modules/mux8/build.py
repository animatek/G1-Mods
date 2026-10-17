"""mux8: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mux8.asm")


def build(b, new_type):
    """Mux8-1: In 1-8 and Ctrl in, Out; the G2's Mux8-1 and Sw8-1 in one type: Sel (1-8) plus
    Ctrl (8 units a step) picks the input; eight LEDs show which."""
    control_type(b, new_type, ASM, (7, 0, 0), [Param("Sel", 7, 1)], steps=(2, 7))
