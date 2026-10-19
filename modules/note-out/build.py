"""note-out: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

HERE = os.path.dirname(os.path.abspath(__file__))
ASM = os.path.join(HERE, "noteout.asm")
POLL = os.path.join(HERE, "noteout_poll.m68k")   # noteout_poll.s, by tools/m68kasm.sh
MAIN_LOOP_CALL = 0x100E6E                         # the main loop's first call: jsr $1156BE
OS_FIRST = 0x1156BE


def build(b, new_type):
    """The G2's NoteSend: Note and Gate in; a note on at Gate's rising edge, with the note Note
    had then, and its note off at the falling edge, on the channel Chan and with the velocity
    Vel. The DSP only packs the gate's edges and the note into a word (noteout.asm); the 68k
    reads it from the OS's main loop and queues the MIDI (noteout_poll.s), so the main loop's
    first call is pointed at that routine."""
    poll = open(POLL, "rb").read()
    # the routine was assembled for this type (cmpi.b #TYPE,($0E,a0), twice)
    assert poll.count(bytes.fromhex("0c28 00") + bytes([new_type]) + bytes.fromhex("000e")) == 2, \
        "noteout_poll.m68k is not for this type: tools/m68kasm.sh it with --defsym TYPE=" + str(new_type)
    control_type(b, new_type, ASM,
                 # the packed word, the gate, the edge count, half a semitone, 64, $100, $80, 127,
                 # the note (an E), Chan, Vel
                 (0, 0, 0, 0x4000, 64, 0x100, 0x80, 127, 64, 0, 100),
                 [Param("Chan", 15, 9), Param("Vel", 127, 10)])
    b.redirect_call(MAIN_LOOP_CALL, OS_FIRST, b.put(poll))
