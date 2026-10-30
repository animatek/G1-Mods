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
                 # the note (an E), Chan, Vel, Mute's mask ($80: not muted)
                 (0, 0, 0, 0x4000, 64, 0x100, 0x80, 127, 64, 0, 100, 0x80),
                 [Param("Chan", 15, 9), Param("Vel", 127, 10),
                  # Mute: v = 0 or 1, the mask (1 - v) * $80
                  #   move.l d2,d0 / eori.l #1,d0 / lsl.l #7,d0
                  Param("Mute", 1, 11, "2002 0a80 0000 0001 ef88")])
    b.chain_call(MAIN_LOOP_CALL, OS_FIRST, poll)   # other modules (Ctrl Send) chain on the same call
