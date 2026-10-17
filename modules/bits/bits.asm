; Bits (G1-Mods type 41): the G2's BinCounter, ADConv and DAConv in one module, by a Mode button.
;   inputs 0 Clk, 1 Rst, 2 In, 3-10 B1-B8        outputs 0 Out, 1-8 Bit 1-8
;   parameter 0 Mode (0 Count, 1 A>D, 2 D>A)
; Control rate. Each mode makes a byte (0-255); Out is it as a level, 0 to +64 units (the byte
; << 13, as the Turing Machine's CV), and Bit 1-8 its bits as logic levels (Bit 1 the lowest). The
; byte is X[0], which the OS reads for the eight LEDs.
; - Count (the BinCounter): each rising edge of Clk adds one, 255 back to 0. Rst as the
;   sequencers': its edge arms the counter and the next clock goes to 0; it starts on 255, so the
;   first clock gives 0. It counts in every mode, so switching back finds it where it went.
; - A>D (the ADConv): In, 0..+64 units, in 256 steps (a step a quarter of a unit); below 0 is 0.
; - D>A (the DAConv): B1-B8 as bits, each one set when its input is above 0.
; X data (10 words): [0] the byte, [1] Clk's last value, [2] Rst's last value, [3] armed,
; [4] Mode (written by its routine), [5] the logic high, [6] 255, [7] the counter, [8] unused,
; [9] 1.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y1            ; @in1  y1 = Rst
    move x:(r3+$2),a        ;       a = Rst's last value
    move y1,x:(r3+$2)
    tst a
    bgt norst               ;       Rst was high already: no edge
    tfr y1,a
    tst a
    ble norst               ;       Rst is low: no edge
    move y1,x:(r3+$3)       ;       edge: armed
norst:
    move x:$0,y0            ; @in0  y0 = Clk
    move x:(r3+$1),a        ;       a = Clk's last value
    move y0,x:(r3+$1)
    tst a
    bgt noclk               ;       Clk was high already: no edge
    tfr y0,a
    tst a
    ble noclk               ;       Clk is low: no edge
    move x:(r3+$7),b        ;       a clock: the counter + 1
    add #<$1,b
    move x:(r3+$6),x0
    and x0,b                ;       255 back to 0
    move x:(r3+$3),a
    tst a
    clr b ifne              ;       armed: 0
    clr a
    move a,x:(r3+$3)        ;       not armed any more
    move b1,x:(r3+$7)
noclk:
    move x:(r3+$4),a        ;       a = Mode
    tst a
    bne notcount
    move x:(r3+$7),b        ;       Count: the counter
    bra bits
notcount:
    cmp #<$1,a
    bne da
    move x:$0,a             ; @in2  A>D: a = In
    asr #$d,a,a             ;       in steps of 2^13 ($200000 is 256 of them)
    move a1,y1
    tfr y1,b                ;       b = the step, with nothing below b1
    tst b
    clr b iflt              ;       below 0: 0
    move x:(r3+$6),x0
    cmp x0,b
    tfr x0,b ifgt           ;       above 255: 255
    bra bits
da:
    clr b                   ;       D>A: B8 first, each a bit lower
    move x:(r3+$9),y1       ;       y1 = 1
    asl b
    move x:$0,a             ; @in10  a = B8
    tst a
    add y1,b ifgt           ;       high: bit 7 set
    asl b
    move x:$0,a             ; @in9  a = B7
    tst a
    add y1,b ifgt           ;       high: bit 6 set
    asl b
    move x:$0,a             ; @in8  a = B6
    tst a
    add y1,b ifgt           ;       high: bit 5 set
    asl b
    move x:$0,a             ; @in7  a = B5
    tst a
    add y1,b ifgt           ;       high: bit 4 set
    asl b
    move x:$0,a             ; @in6  a = B4
    tst a
    add y1,b ifgt           ;       high: bit 3 set
    asl b
    move x:$0,a             ; @in5  a = B3
    tst a
    add y1,b ifgt           ;       high: bit 2 set
    asl b
    move x:$0,a             ; @in4  a = B2
    tst a
    add y1,b ifgt           ;       high: bit 1 set
    asl b
    move x:$0,a             ; @in3  a = B1
    tst a
    add y1,b ifgt           ;       high: bit 0 set
bits:
    move b1,x:(r3)          ;       keep the byte, for the LEDs
    tfr b,a                 ;       a = the byte, for the bits
    asl #$d,b,b             ;       as a level, 0..$1FE000
    move b,x:$0             ; @out0 Out
    move x:(r3+$5),x1       ;       x1 = high
    clr b
    lsr a                   ;       bit 0 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out1 Bit 1
    clr b
    lsr a                   ;       bit 1 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out2 Bit 2
    clr b
    lsr a                   ;       bit 2 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out3 Bit 3
    clr b
    lsr a                   ;       bit 3 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out4 Bit 4
    clr b
    lsr a                   ;       bit 4 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out5 Bit 5
    clr b
    lsr a                   ;       bit 5 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out6 Bit 6
    clr b
    lsr a                   ;       bit 6 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out7 Bit 7
    clr b
    lsr a                   ;       bit 7 to the carry
    tfr x1,b ifcs
    lua (r3+$a),r3          ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out8 Bit 8
