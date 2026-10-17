; Turing Machine (G1-Mods type 124), after Music Thing Modular's: a looping shift register that
; random chance rewrites, with its pulse expander's eight gates.
;   input 0 Clk        outputs 0 CV, 1-8 the gates of bits 0-7
;   parameters 0 Prob, 1 Length (1-16), 2 Lock, 3 Scale
; Control rate. The register has 16 bits. On each rising edge of Clk it moves one bit up; the bit
; that leaves the loop (bit Length-1) comes back in as bit 0, flipped at random unless Lock is on.
; Prob is bipolar, as the original's big knob: right (127) or Lock repeats the pattern every
; Length clocks, the centre (64) flips half the bits, left (0) nearly every bit, which repeats the
; pattern inverted, every 2*Length clocks. The chance is (127 - Prob)/128.
; CV is the register's low 8 bits as a level, 0 to +64 units (0..255 << 13), times Scale (0..1).
; Gate n (1-8) is bit n-1 while Clk is high, so ones in a row give separate gates.
; The chance comes from a 24-bit Galois shift register (as the Noise S&H's) stepped every sample.
; X data (11 words): [0] the noise's taps, [1] the noise, [2] Clk's last value, [3] the register
; (its low byte is what the OS reads for the 8 LEDs), [4] the leaving bit's mask, 1 << (Length-1)
; (written by the Length routine), [5] the threshold, (127 - Prob) << 16 (written by the Prob
; routine), [6] Lock, [7] $FFFF, [8] $FF, [9] the logic high, [10] Scale as a fraction.
; r3 stays on the register from the Clk test to the end; the rest is read at offsets from it.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y0            ; @in0  y0 = Clk
    move x:(r3)+,x0         ;       x0 = taps                       r3 -> the noise
    move x:(r3),a           ;       a1 = the noise
    lsr a                   ;       shift it right; the bit out goes to the carry
    eor x0,a ifcs           ;       and feeds back through the taps
    move a1,x:(r3)+         ;       keep it                         r3 -> Clk's last
    lsr a                   ;       a1 = the noise >> 1, 0..$7FFFFF
    move a1,x1              ;       x1 = the draw
    move x:(r3),b           ;       b = Clk's last value
    move y0,x:(r3)+         ;       remember Clk                    r3 -> the register
    tst b
    bgt noclk               ;       Clk was high already: no edge
    tfr y0,b
    tst b
    ble noclk               ;       Clk is low: no edge
    move x:(r3),b           ;       edge: b = the register
    move x:(r3+$1),x0       ;       x0 = the leaving bit's mask
    tfr b,a
    and x0,a                ;       a1 = the leaving bit
    asl b                   ;       b = the register moved up
    tst a
    beq zero
    or #<$1,b               ;       it comes back in as bit 0
zero:
    move x:(r3+$2),a        ;       a = the threshold
    cmp x1,a
    ble keep                ;       the draw is not below it: no flip
    move x:(r3+$3),a        ;       a = Lock
    tst a
    bne keep                ;       locked: no flip
    eor #<$1,b              ;       flip it
keep:
    move x:(r3+$4),x0       ;       x0 = $FFFF
    and x0,b                ;       16 bits
    move b1,x:(r3)          ;       keep the register
noclk:
    move x:(r3),a           ;       a = the register
    move x:(r3+$5),x0       ;       x0 = $FF
    and x0,a                ;       its low 8 bits
    tfr a,b                 ;       b = them, for the gates
    asl #$d,a,a             ;       as a level, 0..$1FE000
    move a,x0
    move x:(r3+$7),y1       ;       y1 = Scale
    mpy x0,y1,a
    move a,x:$0             ; @out0 CV
    tfr y0,a                ;       a = Clk
    tst a
    clr b ifle              ;       Clk low: no gates
    tfr b,a                 ;       a = the bits to send
    move x:(r3+$6),x1       ;       x1 = high
    clr b
    lsr a                   ;       bit 0 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out1 Gate 1
    clr b
    lsr a                   ;       bit 1 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out2 Gate 2
    clr b
    lsr a                   ;       bit 2 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out3 Gate 3
    clr b
    lsr a                   ;       bit 3 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out4 Gate 4
    clr b
    lsr a                   ;       bit 4 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out5 Gate 5
    clr b
    lsr a                   ;       bit 5 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out6 Gate 6
    clr b
    lsr a                   ;       bit 6 to the carry
    tfr x1,b ifcs
    move b,x:$0             ; @out7 Gate 7
    clr b
    lsr a                   ;       bit 7 to the carry
    tfr x1,b ifcs
    lua (r3+$8),r3          ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out8 Gate 8
