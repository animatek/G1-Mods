"""ctrl-send: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

HERE = os.path.dirname(os.path.abspath(__file__))
ASM = os.path.join(HERE, "ctrlsend.asm")
POLL = os.path.join(HERE, "ctrlsend_poll.m68k")   # ctrlsend_poll.s, by tools/m68kasm.sh
MAIN_LOOP_CALL = 0x100E6E                          # the main loop's first call: jsr $1156BE
OS_FIRST = 0x1156BE


def build(b, new_type):
    """The G2's CtrlSend: In and Send in; a control change on the MIDI OUT whenever the value
    (In plus the Value knob) changes or Send goes high, with the controller Ctrl on the channel
    Chan. The DSP only packs the value and Send's edges into a word (ctrlsend.asm); the 68k
    reads it from the OS's main loop and queues the MIDI (ctrlsend_poll.s). The main loop's first
    call is shared with Note Out: the two chain, whichever the build lays out first."""
    poll = open(POLL, "rb").read()
    # the routine was assembled for this type (cmpi.b #TYPE,($0E,a0), twice)
    assert poll.count(bytes.fromhex("0c28 00") + bytes([new_type]) + bytes.fromhex("000e")) == 2, \
        "ctrlsend_poll.m68k is not for this type: tools/m68kasm.sh it with --defsym TYPE=" + str(new_type)
    control_type(b, new_type, ASM,
                 # the packed word, Send's last, the edge count, $100, 127, Value, Ctrl, Chan, $80
                 (0, 0, 0, 0x100, 127, 0, 1, 0, 0x80),
                 [Param("Ctrl", 127, 6), Param("Value", 127, 5), Param("Chan", 15, 7)])
    b.chain_call(MAIN_LOOP_CALL, OS_FIRST, poll)
