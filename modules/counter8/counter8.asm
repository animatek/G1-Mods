; 8Counter (G1-Mods type 126), after the G2's: eight outputs, one high at a time, moving on with
; the clock.
;   inputs 0 Clk, 1 Rst        outputs 0-7 the steps 1-8
; Control rate. Each rising edge of Clk moves to the next step, the eighth back to the first; the
; step's output is high for the whole step. Rst as the 5-Step Seq's and the G1's sequencers': its
; rising edge arms the counter, and the next clock goes to the first step. It starts on the last
; step, so the first clock plays the first: it keeps in step with a CtrlSeq or a 5-Step Seq on the
; same clock and reset. The step is kept as a plain integer (0-7) in X[0], which the OS reads for
; the step LEDs.
; X data (5 words): [0] the step, [1] Clk's last value, [2] Rst's last value, [3] armed (not 0
; after a Rst edge), [4] the logic high.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y1            ; @in1  y1 = Rst
    move x:(r3)+,b          ;       b1 = the step                   r3 -> Clk's last
    move x:(r3)+,x0         ;       x0 = Clk's last value           r3 -> Rst's last
    move x:(r3),a           ;       a = Rst's last value
    move y1,x:(r3)+         ;       remember Rst                    r3 -> armed
    tst a
    bgt norst               ;       Rst was high already: no edge
    tfr y1,a
    tst a
    ble norst               ;       Rst is low: no edge
    move y1,x:(r3)          ;       edge: armed (Rst's value, above 0)
norst:
    move x:$0,y0            ; @in0  y0 = Clk
    move y0,x:(r3-$2)       ;       remember Clk
    tfr x0,a                ;       a = Clk's last value
    tst a
    bgt noclk               ;       Clk was high already: no edge
    tfr y0,a
    tst a
    ble noclk               ;       Clk is low: no edge
    move x:(r3),a           ;       edge: a = armed
    add #<$1,b              ;       the next step
    cmp #<$8,b
    clr b ifge              ;       past the eighth: the first
    tst a
    clr b ifne              ;       armed: the first
    clr a
    move a,x:(r3)           ;       not armed any more
noclk:
    move b,x:(r3-$3)        ;       keep the step
    move x:(r3+$1),x1       ;       x1 = high
    lua (r3+$2),r3          ;       r3 -> past the data
    clr a
    cmp #<$0,b
    tfr x1,a ifeq           ;       high on step 1
    move a,x:$0             ; @out0 Out 1
    clr a
    cmp #<$1,b
    tfr x1,a ifeq           ;       high on step 2
    move a,x:$0             ; @out1 Out 2
    clr a
    cmp #<$2,b
    tfr x1,a ifeq           ;       high on step 3
    move a,x:$0             ; @out2 Out 3
    clr a
    cmp #<$3,b
    tfr x1,a ifeq           ;       high on step 4
    move a,x:$0             ; @out3 Out 4
    clr a
    cmp #<$4,b
    tfr x1,a ifeq           ;       high on step 5
    move a,x:$0             ; @out4 Out 5
    clr a
    cmp #<$5,b
    tfr x1,a ifeq           ;       high on step 6
    move a,x:$0             ; @out5 Out 6
    clr a
    cmp #<$6,b
    tfr x1,a ifeq           ;       high on step 7
    move a,x:$0             ; @out6 Out 7
    clr a
    cmp #<$7,b
    tfr x1,a ifeq           ;       high on step 8
    nop                     ;       the next module's word 0 goes here
    move a,x:$0             ; @out7 Out 8
