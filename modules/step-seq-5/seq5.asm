; 8Steps (G1-Mods type 123), after Bogaudio's ADDR-SEQ: eight knobs, a length, a
; first step and a direction. It was the 5-Step Seq; the type is the same.
;   inputs 0 Clk, 1 Rst        output 0 Out
;   parameters 0-7 the steps' values (-64..+63), 8 Steps (the last step, 0-7), 9 Start, 10 Reverse
; Control rate. Each rising edge of Clk moves one step on, forwards or (Reverse) backwards, and
; the last step goes back to the first (the first, to the last, in reverse). Rst works as the G1's
; own sequencers' (measured on the CtrlSeq): its rising edge changes nothing at once, it arms the
; sequencer, and the next clock goes to Start, not to the next step. It starts armed, so the
; first clock plays Start. Out is the current step's value. The step is kept as a plain integer
; (0-7) in X[0], which the OS reads for the step LEDs.
; X data (15 words): [0] the step, [1] Clk's last value, [2] Rst's last value, [3] armed (not 0
; after a Rst edge), [4] the last step (Steps - 1), [5] Start, [6] Reverse, [7..14] the eight
; values (written by the parameter routines). The value's address is r3 + the step, through r2 (a
; scratch register Clavia's sequencers use the same way).
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
    move x:(r3+$1),x1       ;       edge: x1 = the last step
    move x:(r3+$3),a        ;       a = Reverse
    tst a
    bne back
    add #<$1,b              ;       forwards: the next step
    cmp x1,b
    clr b ifgt              ;       past the last: the first
    bra moved
back:
    sub #<$1,b              ;       backwards: the one before
    tst b
    tfr x1,b iflt           ;       before the first: the last
moved:
    move x:(r3+$2),y1       ;       y1 = Start
    move x:(r3),a           ;       a = armed
    tst a
    tfr y1,b ifne           ;       armed: Start
    clr a
    move a,x:(r3)           ;       not armed any more
noclk:
    lua (r3+$4),r3          ;       r3 -> the first value
    move b,x:(r3-$7)        ;       keep the step
    move r3,a
    add b,a                 ;       a1 = the address of the step's value
    move a1,r2
    lua (r3+$8),r3          ;       r3 -> past the data
    move x:(r2),b           ;       b = the step's value
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0 Out
