"""step-seq-5: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seq5.asm")


def build(b, new_type):
    """5-Step Seq: Clk and Rst in, Out, five bipolar knobs (-64..+63 units), the step's LEDs."""
    # value v = 0..127: (v - 64) control units, a unit being $8000
    #   move.l d2,d0 / subi.l #64,d0 / moveq #15,d1 / asl.l d1,d0
    bipolar = "2002 0480 00000040 720f e3a0"
    control_type(b, new_type, ASM,
                 # the step (the last: the first clock plays the first), Clk's last, Rst's last,
                 # armed, the values
                 (4, 0, 0, 0, 0, 0, 0, 0, 0),
                 [Param(f"Step {i + 1}", 127, 4 + i, bipolar) for i in range(5)],
                 steps=(0, 4))
