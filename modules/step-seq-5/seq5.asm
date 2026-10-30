; 8Steps (G1-Mods type 123), after Bogaudio's ADDR-SEQ: eight knobs, a length, a
; first step and a direction. It was the 5-Step Seq; the type is the same.
;   inputs 0 Clk, 1 Rst        output 0 Out
;   parameters 0-7 the steps' values (-64..+63), 8 Steps (the last step, 0-7), 9 Start, 10 Reverse,
;   11 Level (the output's share of the step value, 0-100 %)
; Control rate. The loop runs from Start to the last step (Steps). Each rising edge of Clk moves
; one step on, forwards or (Reverse) backwards, and the last step goes back to Start (Start, to
; the last, in reverse): with Start 2 and 8 Steps it plays 2 to 8 and starts over at 2. A Start
; past the last step counts as the last; a step outside the loop (Start or Steps turned while it
; plays) is brought into it at the next clock. Rst works as the G1's own sequencers' (measured on
; the CtrlSeq): its rising edge changes nothing at once, it arms the sequencer, and the next
; clock goes to Start, not to the next step. It starts armed, so the first clock plays Start. Out is the current step's value times Level. The step is kept as a plain integer
; (0-7) in X[0], which the OS reads for the step LEDs.
; X data (16 words): [0] the step, [1] Clk's last value, [2] Rst's last value, [3] armed (not 0
; after a Rst edge), [4] the last step (Steps - 1), [5] Start, [6] Reverse, [7..14] the eight
; values and [15] Level, a fraction (all written by the parameter routines). The value's address is r3 + the step, through r2 (a
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
    move x:(r3+$2),a        ;       a = Start
    cmp x1,a
    tfr x1,a ifgt           ;       Start past the last step: the last
    move a1,y1              ;       y1 = the loop's first step
    move x:(r3+$3),a        ;       a = Reverse
    tst a
    bne back
    add #<$1,b              ;       forwards: the next step
    cmp x1,b
    tfr y1,b ifgt           ;       past the last: the first
    cmp y1,b
    tfr y1,b iflt           ;       before the first (Start turned up): the first
    bra moved
back:
    sub #<$1,b              ;       backwards: the one before
    cmp y1,b
    tfr x1,b iflt           ;       before the first: the last
    cmp x1,b
    tfr x1,b ifgt           ;       past the last (Steps turned down): the last
moved:
    move x:(r3),a           ;       a = armed
    tst a
    tfr y1,b ifne           ;       armed: the first step
    clr a
    move a,x:(r3)           ;       not armed any more
noclk:
    lua (r3+$4),r3          ;       r3 -> the first value
    move b,x:(r3-$7)        ;       keep the step
    move r3,a
    add b,a                 ;       a1 = the address of the step's value
    move a1,r2
    move x:(r3+$8),x0       ;       x0 = Level
    lua (r3+$9),r3          ;       r3 -> past the data
    move x:(r2),x1          ;       x1 = the step's value
    mpy x1,x0,b             ;       b1 = the value times Level
    nop                     ;       the next module's word 0 goes here
    move b1,x:$0            ; @out0 Out
