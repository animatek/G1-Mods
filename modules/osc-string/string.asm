; Osc String (G1-Mods type 56): a plucked string, Karplus-Strong, after the G2's.
;   inputs 0 Trig, 1 Pitch, 2 Exc        output 0 Out
;   parameters 0 Note, 1 Decay, 2 Damp
; Audio rate. A delay line as long as the note's period feeds back on itself through a one-pole
; lowpass (Damp) and a gain (Decay); a rising edge at Trig plucks it, a period of noise into the
; line; Exc adds any signal into it. Out is the lowpass's output.
; The period: the note n = Note + Pitch (0 units is note 64, as an oscillator's), and the length
; L = L(135) * 2^((135 - n) / 12) samples, L(135) = 96000 / 19912 Hz: the octaves (135 - n) / 12
; split into k (whole) and f; 2^f / 2 by a cubic; then shifted left k + 1 times (rep, so never
; 0 times). L is kept with 12 fraction bits, held to the line's length, and the line is read
; between two samples, linearly.
; The line is cleared one word a sample from the start (it holds whatever the loader copied).
; X data (26 + N words): [0] Note << 15, [1] Decay, [2] Damp (written by their routines),
; [3] the write index, [4] the lowpass, [5] the pluck's samples left, [6] Trig's last value,
; [7] the noise, [8] its taps, [9] L(135) * 4096, [10] 135 << 15, [11] 1/12, [12-15] the
; cubic's coefficients (halved), [16] the longest L * 4096, [17] N, [18] $7FFF, [19] $FFF,
; [20] the pluck's level, [21] the clearing index, [22] 1, [23] the last period (whole), [24]
; the lowpass's delay * 4096 (written by Damp's routine), [25] 26 + N, then the line, N words.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it. r2 is scratch (as Clavia's sequencers use it).

    move x:$0,y1            ; @in0  y1 = Trig
    move x:(r3+$6),a        ;       a = Trig's last value
    move y1,x:(r3+$6)
    tst a
    bgt notrig              ;       Trig was high already
    tfr y1,a
    tst a
    ble notrig              ;       Trig is low
    move x:(r3+$17),x0      ;       a pluck: a period of noise
    move x0,x:(r3+$5)
notrig:
; --- the period
    move x:$0,x1            ; @in1  x1 = Pitch
    move x:(r3),a           ;       a = Note
    add x1,a                ;       n
    move x:(r3+$a),b
    sub a,b                 ;       b = 135 - n
    tst b
    clr b iflt              ;       above 135: 135
    move b,x0
    move x:(r3+$b),y0       ;       y0 = 1/12
    mpy y0,x0,a             ;       a1 = the octaves << 15
    tfr a,b
    asr #$f,b,b             ;       b1 = k
    add #<$1,b
    move b1,y1              ;       y1 = k + 1
    move x:(r3+$12),x0
    and x0,a                ;       the octave's fraction, 15 bits
    asl #$8,a,a             ;       as a fraction f
    move a,x0               ;       x0 = f
    move x:(r3+$c),y0       ;       2^f / 2 = ((c3 f + c2) f + c1) f + c0
    mpy y0,x0,a
    move x:(r3+$d),y0
    add y0,a
    move a,y0
    mpy y0,x0,a
    move x:(r3+$e),y0
    add y0,a
    move a,y0
    mpy y0,x0,a
    move x:(r3+$f),y0
    add y0,a
    move a,x0               ;       x0 = 2^f / 2
    move x:(r3+$9),y0       ;       y0 = L(135) * 4096
    mpy y0,x0,a             ;       a1 = L(135) * 4096 * 2^f / 2
    rep y1
    asl a                   ;       times 2^(k + 1): L * 4096
    move x:(r3+$18),x0      ;       less the lowpass's delay (Damp's routine)
    sub x0,a
    move x:(r3+$10),x0      ;       held to the longest
    cmp x0,a
    tfr x0,a ifgt
    tfr a,b
    asr #$c,b,b             ;       b1 = the whole samples
    move b1,x1
    move x1,x:(r3+$17)      ;       (a pluck's length)
    move x:(r3+$13),x0
    and x0,a                ;       the fraction, 12 bits
    asl #$b,a,a
    move a,y1               ;       y1 = the fraction
; --- read the line: s0 at w - whole, s1 one older, y = s0 + fraction (s1 - s0)
    move x:(r3+$3),a        ;       a = w
    sub x1,a
    move x:(r3+$11),x0      ;       x0 = N
    add x0,a iflt           ;       wrapped
    move a1,x1              ;       x1 = s0's index
    lua (r3+$1a),r2
    move r2,b
    add x1,b
    move b1,r2
    move x:(r2),y0          ;       y0 = s0
    tfr x1,a
    move x:(r3+$16),x0
    sub x0,a                ;       s1's index
    move x:(r3+$11),x0
    add x0,a iflt
    move a1,x1
    lua (r3+$1a),r2
    move r2,b
    add x1,b
    move b1,r2
    move x:(r2),a           ;       a = s1
    sub y0,a
    move a,x0               ;       x0 = s1 - s0
    mpy x0,y1,a
    add y0,a                ;       a = y
; --- the lowpass and the gain
    move x:(r3+$4),b        ;       b = the lowpass
    sub b,a
    move a,x0               ;       x0 = y - lowpass
    move x:(r3+$2),y1       ;       y1 = Damp
    mac x0,y1,b
    move b,x:(r3+$4)        ;       the lowpass
    move b,x0
    move x:(r3+$1),y1       ;       y1 = Decay
    mpy x0,y1,b             ;       b = what goes back in
; --- the pluck
    move x:(r3+$5),a
    tst a
    beq nopluck
    move x:(r3+$16),x0
    sub x0,a
    move a1,x:(r3+$5)       ;       one sample fewer
    move x:(r3+$8),x0       ;       the noise: a Galois step
    move x:(r3+$7),a
    lsr a
    eor x0,a ifcs
    move a1,x:(r3+$7)
    move x:(r3+$7),x0       ;       as a signed number
    move x:(r3+$14),y1      ;       y1 = the pluck's level
    mac x0,y1,b
nopluck:
    move x:$0,x0            ; @in2  x0 = Exc
    add x0,b
; --- write the line, w on
    move x:(r3+$3),x1       ;       x1 = w
    lua (r3+$1a),r2
    move r2,a
    add x1,a
    move a1,r2
    move b,x:(r2)
    tfr x1,a
    move x:(r3+$16),x0
    add x0,a
    move x:(r3+$11),x0
    cmp x0,a
    clr a ifge              ;       past the end: 0
    move a1,x:(r3+$3)
; --- clear the line, a word a sample, from the start
    move x:(r3+$15),a
    move x:(r3+$11),x0
    cmp x0,a
    bge cleared
    move a1,x1
    lua (r3+$1a),r2
    move r2,b
    add x1,b
    move b1,r2
    clr b
    move b,x:(r2)
    move x:(r3+$16),x0
    add x0,a
    move a1,x:(r3+$15)
cleared:
    move x:(r3+$4),b        ;       Out: the lowpass
    move r3,a
    move x:(r3+$19),x0
    add x0,a
    move a1,r3              ;       r3 -> past the data and the line
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0 Out
