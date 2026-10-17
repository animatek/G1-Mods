"""envelope: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "env.asm")


def build(b, new_type):
    """Envelope: the G2's ADDSR, H, D and Mod AHD from one engine: Gate in; Env and End; Mode
    (Gate, Trig), Attack, Decay 1, Level 1, Decay 2, Sustain and Release."""
    # a time: the factor ($800000 - (v & 7) << 19) >> (v >> 3), less 1 (the Random's Edge)
    time = "2202 0281 00000007 7013 e1a9 203c 00800000 9081 2202 e689 e2a8 5380"
    # a level: (v << 14) + (v << 7), 127 nearly the top ($200000, +64 units)
    #   move.l d2,d0 / moveq #14,d1 / asl.l d1,d0 / move.l d2,d1 / asl.l #7,d1 / add.l d1,d0
    lvl = "2002 720e e3a0 2202 ef81 d081"
    control_type(b, new_type, ASM,
                 # Mode, Attack, Decay 1, Level 1, Decay 2, Sustain, Release, stage, Env (2), Gate's
                 # last, the aim, the top, $200, high, 1, 2, 3, 4, 0
                 (0, 0x7FFFFF, 0x1000, 0x100000, 0x1000, 0x100000, 0x1000, 0, 0, 0, 0,
                  0x266666, 0x200000, 0x200, 0x200000, 1, 2, 3, 4, 0),
                 [Param("Mode", 1, 0), Param("Attack", 127, 1, time), Param("Decay 1", 127, 2, time),
                  Param("Level 1", 127, 3, lvl), Param("Decay 2", 127, 4, time),
                  Param("Sustain", 127, 5, lvl), Param("Release", 127, 6, time)])
