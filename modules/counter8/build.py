"""counter8: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "counter8.asm")


def build(b, new_type):
    """8Counter: Clk and Rst in, eight outputs, one high a step, and a row of eight step LEDs."""
    control_type(b, new_type, ASM,
                 # the step (the last: the first clock plays the first), Clk's last, Rst's last,
                 # armed, high
                 (7, 0, 0, 0, 0x200000),
                 steps=(0, 7))
