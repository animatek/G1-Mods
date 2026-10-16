; 5-Step Seq (G1-Mods type 123), after Buchla's five-stage sequencers, with knobs.
;   inputs 0 Clk, 1 Rst        output 0 Out        parameters 0-4 the steps' values (-64..+63)
; Control rate. Each rising edge of Clk moves to the next step, the fifth back to the first; a
; rising edge of Rst goes to the first, and wins over a clock in the same sample. Out is the
; current step's value. The step is kept as a plain integer (0-4) in X[0], which the OS reads
; for the step LEDs.
; X data (8 words): [0] the step, [1] Clk's last value, [2] Rst's last value, [3..7] the five
; values (written by the parameter routines). The value's address is r3 + the step, through r2
; (a scratch register Clavia's sequencers use the same way).
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y0            ; @in0  y0 = Clk
    move x:(r3)+,b          ;       b1 = the step                   r3 -> Clk's last
    move x:(r3),a           ;       a = Clk's last value
    move y0,x:(r3)+         ;       remember Clk                    r3 -> Rst's last
    tst a
    bgt noclk               ;       Clk was high already: no edge
    tfr y0,a
    tst a
    ble noclk               ;       Clk is low: no edge
    add #<$1,b              ;       edge: the next step
    cmp #<$5,b
    clr b ifge              ;       past the fifth: the first
noclk:
    move x:$0,y1            ; @in1  y1 = Rst
    move x:(r3),a           ;       a = Rst's last value
    move y1,x:(r3)+         ;       remember Rst                    r3 -> the first value
    tst a
    bgt norst               ;       Rst was high already: no edge
    tfr y1,a
    tst a
    ble norst               ;       Rst is low: no edge
    clr b                   ;       edge: the first step
norst:
    move b,x:(r3-$3)        ;       keep the step
    move r3,a
    add b,a                 ;       a1 = the address of the step's value
    move a1,r2
    lua (r3+$5),r3          ;       r3 -> past the data
    move x:(r2),b           ;       b = the step's value
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0 Out
