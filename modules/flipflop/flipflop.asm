; FlipFlop (G1-Mods type 120), after the G2's: control rate.
;   inputs  0 Clk, 1 In (D or S), 2 Rst        outputs 0 Q, 1 NotQ        parameter 0 Type
;   D-type:  on Clk's rising edge Q takes In.
;   RS-type: In's rising edge sets Q; with In low, each rising edge of Clk toggles Q.
;   Rst high clears Q, in both types, over everything else.
; X data (r3 walks through it, 5 words): [0] the logic high, [1] Type (0 D, 1 RS, written by
; the parameter routine), [2] Clk's last value, [3] In's last value, [4] Q.
; Word 0 runs in the previous module's nop slot: it must not touch a or b, and no branch may
; leave from it. No branch may land on the nop or after it: the next module's word 0 goes there.
; "@inN"/"@outN" mark the words the connection routine patches with that input's or output's
; address (an input may be read in several words).

    move x:$0,y0            ; @in0  y0 = Clk
    move x:(r3)+,x1         ;       x1 = high
    move x:(r3)+,a          ;       a = Type
    move x:(r3),b           ;       b = Clk's last value
    move y0,x:(r3)+         ;       remember Clk                   r3 -> In's last value
    tst a
    bne rs

; --- D-type: b = Clk's last value, y0 = Clk
    move x:$0,a             ; @in1  a = In
    move a,x:(r3)+          ;       remember In                    r3 -> Q
    tst b
    bgt reset               ;       Clk was high already: no edge
    tfr y0,b
    tst b
    ble reset               ;       Clk is low: no edge
    tst a                   ;       edge: Q = In > 0 ? high : 0
    clr a ifle
    tfr x1,a ifgt
    move a,x:(r3)
    bra reset

; --- RS-type: b = Clk's last value, y0 = Clk
rs:
    tfr y0,a
    tst b
    clr a ifgt              ;       a > 0 only on Clk's rising edge
    move a,y0               ;       y0 = that
    move x:(r3),b           ;       b = In's last value
    move x:$0,a             ; @in1  a = In
    move a,x:(r3)+          ;       remember In                    r3 -> Q
    tst b
    clr a ifgt              ;       a > 0 only on In's rising edge
    tst a
    bgt set
    move x:$0,a             ; @in1  In high (and no edge): no toggle
    tst a
    bgt reset
    tfr y0,a
    tst a
    ble reset               ;       no Clk edge: no toggle
    move x:(r3),a           ;       toggle: Q = Q > 0 ? 0 : high
    tst a
    clr a ifgt
    tfr x1,a ifle
    move a,x:(r3)
    bra reset
set:
    move x1,x:(r3)          ;       Q = high

; --- both: Rst clears Q, then the outputs
reset:
    move x:$0,a             ; @in2  a = Rst
    tst a
    ble out
    clr a
    move a,x:(r3)
out:
    move x:(r3)+,b          ;       b = Q                          r3 -> past the data
    tst b
    clr a ifgt
    tfr x1,a ifle           ;       a = NotQ
    move a,x:$0             ; @out1
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0
