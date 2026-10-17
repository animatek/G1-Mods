"""random: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type, m68k

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "random.asm")


def seed_routine(x_seed, x_voice, x_load):
    """The Random's Seed routine, for $10C49E: writes the seed's value, (v + 1) * $9E37, to X word
    x_seed, the voice's, voice * $B5A3, to x_voice, and 1 to x_load, so the next clock loads the
    seed (a clock can come before the seed is written while a patch is set up; and a Seed turned
    live starts its values at the next clock). The OS calls it once a voice, with the voice in
    the byte at 2 of the module's structure (as $10D142 reads it)."""
    return m68k("48e7 2030",          # movem.l d2/a2-a3,-(sp)
                "242f 0014",          # move.l (20,sp),d2     the value
                "246f 0010",          # movea.l (16,sp),a2    the module
                "2002 5280",          # move.l d2,d0 / addq.l #1,d0
                "c0fc 9e37",          # mulu.w #$9E37,d0
                "3f3c", f"{x_seed:04x}",  # move.w #x_seed,-(sp)
                "2f00 2f0a",          # move.l d0,-(sp) / move.l a2,-(sp)
                "4eb9 0010d142",      # jsr $10D142
                "4fef 000a",          # lea (10,sp),sp
                "7000 102a 0002",     # moveq #0,d0 / move.b (2,a2),d0   the voice
                "c0fc b5a3",          # mulu.w #$B5A3,d0
                "3f3c", f"{x_voice:04x}",  # move.w #x_voice,-(sp)
                "2f00 2f0a",
                "4eb9 0010d142",
                "4fef 000a",
                "7001",               # moveq #1,d0
                "3f3c", f"{x_load:04x}",   # move.w #x_load,-(sp)
                "2f00 2f0a",
                "4eb9 0010d142",
                "4fef 000a",
                "4cdf 0c04",          # movem.l (sp)+,d2/a2-a3
                "4e75")               # rts


def build(b, new_type):
    """Random: Clk and Rst in; Out and Trig; Seed, Poly, Step, Edge, Prob, Length and Uni."""
    control_type(b, new_type, ASM,
                 # taps, the register, Clk's last, Rst's last, load (yes), count, Length (free),
                 # seed, voice, Poly, Step, target, Out (2), Edge's factor, Prob, gate, high
                 (0xE10000, 0x5A3C96, 0, 0, 1, 0, 0x7FFFFF, 0x9E37, 0, 0, 0x7FFE00, 0, 0, 0,
                  0x7FFFFF, 0x400000, 0, 0x200000, 0, 0x100000),   # ..., Uni, 32 units
                 [Param("Seed", 127, 7, routine=lambda b: b.put(seed_routine(7, 8, 4))),
                  # value 1: $FFFFFF, else 0
                  #   moveq #0,d0 / tst.l d2 / beq.s +6 / move.l #$FFFFFF,d0
                  Param("Poly", 1, 9, "7000 4a82 6706 203c 00ffffff"),
                  # Step: the fraction (v << 16) + (v << 9), 127 nearly 1
                  Param("Step", 127, 10, "2002 4840 4240 2202 e181 d281 d081"),
                  # Edge: the glide factor ($800000 - (v & 7) << 19) >> (v >> 3), less 1: 1 for
                  # 0 (no glide), halving every 8, about 2^-16 for 127
                  #   move.l d2,d1 / andi.l #7,d1 / moveq #19,d0 / lsl.l d0,d1 /
                  #   move.l #$800000,d0 / sub.l d1,d0 / move.l d2,d1 / lsr.l #3,d1 /
                  #   lsr.l d1,d0 / subq.l #1,d0
                  Param("Edge", 127, 14, "2202 0281 00000007 7013 e1a9 203c 00800000 9081 "
                                         "2202 e689 e2a8 5380"),
                  # Prob: (v << 16) + (v << 9) + (v << 2), 127 above every draw: always
                  #   ... / move.l d2,d1 / asl.l #2,d1 / add.l d1,d0
                  Param("Prob", 127, 15, "2002 4840 4240 2202 e181 d281 d081 2202 e581 d081"),
                  # Length: v, or $7FFFFF (never) for 0
                  #   move.l d2,d0 / bne.s +6 / move.l #$7FFFFF,d0
                  Param("Length", 16, 6, "2002 6606 203c 007fffff"),
                  Param("Uni", 1, 18)])
