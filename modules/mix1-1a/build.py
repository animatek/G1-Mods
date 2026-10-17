"""mix1-1a: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
from g1rom import mixer3_variant


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


def build(b, new_type):
    """Mix1-1A: one input with its level and an on button, plus a chain input added as it comes."""
    mixer3_variant(b, new_type, code=MIX1_1A_CODE, x_words=1, y_words=1, io=(2, 2, 1),
                   params=[("Level", 127), ("Ch 1", 1)])
