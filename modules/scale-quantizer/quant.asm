; Scale Quantizer (G1-Mods type 125), after JW-Modules' Quantizer: a pitch to the nearest note of a
; scale, chosen by name, on a root note.
;   input 0 In        output 0 Out        parameters 0 Root (C..B), 1 Scale, 2 Octave (-4..+4)
; Control rate. A semitone is one control unit ($8000), and 0 is note 64, an E (the keyboard's
; Note out). In is rounded to the nearest semitone n; its note in the scale's key,
; (n + 4 - Root) mod 12, with C as 0, picks a correction from a table of 12 (the
; distance to the nearest note of the scale, the lower one on a tie), which the Scale routine
; writes whole. Out = (n + the correction + 12 * Octave) semitones.
; The mod 12 without a divide: m = n + 136 - Root is never negative (n >= -125), and
; q = floor(m / 12) is m times ceil(2^23 / 12) as a fraction, exact for every m it meets.
; X data (18 words): [0] half a semitone ($4000), [1] Root (written by its routine), [2] 12 *
; Octave (written by its routine), [3] 136 (4 for the E, 132 to keep m positive), [4] ceil(2^23 / 12), [5..16] the corrections for the
; notes 0..11 of the key (written by the Scale routine), [17] unused.
; r3 stays put, the words read at offsets from it; r2 is scratch, as in Clavia's sequencers
; (n2 is not: using it stopped the whole DSP).
; Word 0 runs in the previous module's nop slot (no a or b); no branches.

    move x:$0,x1            ; @in0  x1 = In
    tfr x1,a
    move x:(r3),x0          ;       x0 = half a semitone
    add x0,a
    asr #$f,a,a             ;       a1 = n, In in semitones, rounded
    move a1,y1              ;       y1 = n
    move x:(r3+$3),x0
    add x0,a                ;       + 136
    move x:(r3+$1),x0
    sub x0,a                ;       - Root: a1 = m
    move a1,x0              ;       x0 = m
    move x:(r3+$4),y0       ;       y0 = ceil(2^23 / 12)
    mpy y0,x0,b             ;       b1 = q = floor(m / 12)
    move b1,x0
    tfr x0,b                ;       b = q, clean
    asl #$2,b,b             ;       4q
    move b1,y0
    asl b                   ;       8q
    add y0,b                ;       12q
    sub b,a                 ;       a1 = m - 12q, the note in the key, 0..11
    lua (r3+$5),r2          ;       r2 -> the corrections
    move r2,b
    add a,b                 ;       b1 = the address of its correction
    move b1,r2
    tfr y1,a                ;       a = n
    move x:(r2),x0          ;       x0 = its correction
    add x0,a
    move x:(r3+$2),x0       ;       x0 = 12 * Octave
    add x0,a                ;       a1 = Out in semitones
    asl #$f,a,a             ;       as a level
    lua (r3+$12),r3         ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move a,x:$0             ; @out0 Out
