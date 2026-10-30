"""step-seq-5 (the 8Steps, once the 5-Step Seq): how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seq5.asm")


def build(b, new_type):
    """8Steps: Clk and Rst in, Out, eight bipolar knobs (-64..+63 units), Steps (the
    last step, 0-7), Start (the step an armed clock goes to) and Reverse, the step's LEDs."""
    # value v = 0..127: (v - 64) control units, a unit being $8000
    #   move.l d2,d0 / subi.l #64,d0 / moveq #15,d1 / asl.l d1,d0
    bipolar = "2002 0480 00000040 720f e3a0"
    control_type(b, new_type, ASM,
                 # the step, Clk's last, Rst's last, armed (the first clock plays Start), the last
                 # step (7), Start, Reverse, the values
                 (0, 0, 0, 1, 7, 0, 0) + (0,) * 8,
                 [Param(f"Step {i + 1}", 127, 7 + i, bipolar) for i in range(8)] +
                 [Param("Steps", 7, 4), Param("Start", 7, 5), Param("Reverse", 1, 6)],
                 steps=(0, 7))
