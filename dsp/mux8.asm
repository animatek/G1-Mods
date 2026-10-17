; Mux8-1 (G1-Mods type 101), after the G2's Mux8-1 and Sw8-1 in one (a G1 has few free types):
; one of eight inputs to the output, picked by a Sel knob plus a level at Ctrl.
;   inputs 0-7 In 1-8, 8 Ctrl        output 0 Out        parameter 0 Sel (1-8)
; Control rate (for levels and gates; audio through it would be at the control rate). The input
; picked is Sel plus Ctrl in eighths of 0..+64 units (8 units a step), held to 1..8: with Ctrl
; unplugged the knob picks (the Sw8-1), with Sel on 1 a level does (the Mux8-1). It is kept in
; X[2] for a row of eight LEDs.
; X data (3 words): [0] 7, [1] Sel (0-7, written by its routine), [2] the input picked (0-7).
; Word 0 runs in the previous module's nop slot (no a or b); no branches.

    move x:$0,x1            ; @in8  x1 = Ctrl
    tfr x1,a
    asr #$12,a,a            ;       a1 = floor(Ctrl / 8 units)
    move a1,y1
    tfr y1,a                ;       the same, with nothing below a1
    move x:(r3)+,y0         ;       y0 = 7                          r3 -> Sel
    move x:(r3)+,x0         ;       x0 = Sel                        r3 -> the input picked
    add x0,a
    tst a
    clr a iflt              ;       below: In 1
    cmp #<$7,a
    tfr y0,a ifgt           ;       above: In 8
    move a1,x:(r3)+         ;       keep it, for the LEDs           r3 -> past the data
    clr b
    move x:$0,x0            ; @in0  x0 = In 1
    cmp #<$0,a
    tfr x0,b ifeq           ;       picked: Out = In 1
    move x:$0,x0            ; @in1  x0 = In 2
    cmp #<$1,a
    tfr x0,b ifeq           ;       picked: Out = In 2
    move x:$0,x0            ; @in2  x0 = In 3
    cmp #<$2,a
    tfr x0,b ifeq           ;       picked: Out = In 3
    move x:$0,x0            ; @in3  x0 = In 4
    cmp #<$3,a
    tfr x0,b ifeq           ;       picked: Out = In 4
    move x:$0,x0            ; @in4  x0 = In 5
    cmp #<$4,a
    tfr x0,b ifeq           ;       picked: Out = In 5
    move x:$0,x0            ; @in5  x0 = In 6
    cmp #<$5,a
    tfr x0,b ifeq           ;       picked: Out = In 6
    move x:$0,x0            ; @in6  x0 = In 7
    cmp #<$6,a
    tfr x0,b ifeq           ;       picked: Out = In 7
    move x:$0,x0            ; @in7  x0 = In 8
    cmp #<$7,a
    tfr x0,b ifeq           ;       picked: Out = In 8
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0 Out
