; Level (G1-Mods type 42): the G2's ModAmt, MinMax, T&H and WindSw in one module, by a Mode selector.
;   inputs 0 A, 1 B        outputs 0 Out 1, 1 Out 2
;   parameters 0 Mode (0 ModAmt, 1 MinMax, 2 T&H, 3 Window), 1 Amount, 2 Lo, 3 Hi
; Control rate (for levels and gates).
; - ModAmt: B sets how much of A goes through, by Amount: Out 1 = A * (1 - Amount + Amount * B),
;   B read as 0..1 over 0..+64 units (below 0 as 0): Amount 0 passes A whole, 127 makes B a VCA
;   on it. Out 2 = A - Out 1, the rest.
; - MinMax: Out 1 the lower of A and B, Out 2 the higher.
; - T&H: Out 1 tracks A while B is high and holds it while low; Out 2 the other way round.
; - Window: Out 1 is A while B is within Lo..Hi, else 0; Out 2 high while it is, else 0.
; X data (9 words): [0] Mode, [1] Amount (a fraction), [2] Lo, [3] Hi (as levels, written by their
; routines), [4] Out 1's held value, [5] the logic high, [6] 1 ($7FFFFF), [7] unused, [8] Out 2's
; held value.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,x1            ; @in1  x1 = B
    move x:$0,y0            ; @in0  y0 = A
    move x:(r3),a           ;       a = Mode
    tst a
    bne notamt
    tfr x1,a                ;       ModAmt
    asl #$2,a,a             ;       B over 0..64 units as 0..1
    move a,x0               ;       (at most 1)
    tfr x0,a
    move x:(r3+$6),x0       ;       x0 = 1
    sub x0,a                ;       a = B - 1
    move a,x0               ;       (at least -1: B below 0 counts as 0)
    move x:(r3+$1),y1       ;       y1 = Amount
    mpy x0,y1,b             ;       b = Amount * (B - 1)
    move x:(r3+$6),x0
    add x0,b                ;       b = 1 - Amount + Amount * B
    move b,x0
    mpy y0,x0,a             ;       Out 1 = A times that
    tfr y0,b
    sub a,b                 ;       Out 2 = A - Out 1
    bra done
notamt:
    cmp #<$1,a
    bne notminmax
    tfr y0,a                ;       MinMax: a = A, b = B
    tfr x1,b
    cmp x1,a
    tfr x1,a ifgt           ;       A above B: Out 1 = B
    tfr y0,b ifgt           ;       and Out 2 = A
    bra done
notminmax:
    cmp #<$2,a
    bne window
    tfr x1,b                ;       T&H
    tst b
    ble low
    move y0,x:(r3+$4)       ;       B high: Out 1 tracks
    bra held
low:
    move y0,x:(r3+$8)       ;       B low: Out 2 tracks
held:
    move x:(r3+$4),a
    move x:(r3+$8),b
    bra done
window:
    tfr x1,a                ;       Window: a = B
    move x:(r3+$2),x0
    cmp x0,a
    blt outside             ;       below Lo
    move x:(r3+$3),x0
    cmp x0,a
    bgt outside             ;       above Hi
    tfr y0,a                ;       within: Out 1 = A
    move x:(r3+$5),b        ;       Out 2 = high
    bra done
outside:
    clr a
    clr b
done:
    move a,x:$0             ; @out0 Out 1
    lua (r3+$9),r3          ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out1 Out 2
