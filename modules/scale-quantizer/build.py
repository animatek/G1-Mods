"""scale-quantizer: how the module is built into the OS. tools/patch_rom.py calls build(b, type)
with the type module.json gives it."""
import os

from g1rom import Param, control_type

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quant.asm")


# The Scale Quantizer's scales: (name, the notes in it, as semitones from the root)
SCALES = [
    ("Chromatic", range(12)),
    ("Major", (0, 2, 4, 5, 7, 9, 11)),
    ("Minor", (0, 2, 3, 5, 7, 8, 10)),
    ("Dorian", (0, 2, 3, 5, 7, 9, 10)),
    ("Phrygian", (0, 1, 3, 5, 7, 8, 10)),
    ("Lydian", (0, 2, 4, 6, 7, 9, 11)),
    ("Mixolydian", (0, 2, 4, 5, 7, 9, 10)),
    ("Locrian", (0, 1, 3, 5, 6, 8, 10)),
    ("Harmonic minor", (0, 2, 3, 5, 7, 8, 11)),
    ("Melodic minor", (0, 2, 3, 5, 7, 9, 11)),
    ("Major pentatonic", (0, 2, 4, 7, 9)),
    ("Minor pentatonic", (0, 3, 5, 7, 10)),
    ("Blues", (0, 3, 5, 6, 7, 10)),
    ("Whole tone", (0, 2, 4, 6, 8, 10)),
    ("Hirajoshi", (0, 2, 3, 7, 8)),
    ("Double harmonic", (0, 1, 4, 5, 7, 8, 11)),
]


def corrections(notes):
    """For each note 0..11 of the key, the distance to the nearest note of the scale (an octave
    up or down counts), the lower one on a tie."""
    row = []
    for k in range(12):
        best = min((abs(d), d) for n in notes for o in (-12, 0, 12) for d in [n + o - k])
        row.append(best[1])
    return row


def build(b, new_type):
    """Scale Quantizer: In and Out; Root, Scale (by name) and Octave."""
    control_type(b, new_type, ASM,
                 # half a semitone, Root (C), 12 * Octave (0), 136 (0 is an E, and m kept
                 # positive), ceil(2^23 / 12), the corrections (Chromatic: none), unused
                 (0x4000, 0, 0, 136, (2 ** 23 + 11) // 12) + (0,) * 12 + (0,),
                 [Param("Root", 11, 1),
                  Param("Scale", len(SCALES) - 1, 5, table=[corrections(n) for _, n in SCALES]),
                  # Octave: value v = 0..8 for -4..+4, 12 * (v - 4) semitones
                  #   move.l d2,d0 / subq.l #4,d0 / muls.w #12,d0
                  Param("Octave", 8, 2, "2002 5980 c1fc 000c")])
