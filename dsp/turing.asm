; Turing Machine (G1-Mods type 124), after Music Thing Modular's: a looping shift register that
; random chance rewrites.
;   input 0 Clk        outputs 0 CV, 1 Gate        parameters 0 Prob, 1 Length (1-16), 2 Lock
; Control rate. The register has 16 bits. On each rising edge of Clk it moves one bit up; the bit
; that leaves the loop (bit Length-1) comes back in as bit 0, flipped at random unless Lock is on.
; Prob is bipolar, as the original's big knob: right (127) or Lock repeats the pattern every
; Length clocks, the centre (64) flips half the bits, left (0) nearly every bit, which repeats the
; pattern inverted, every 2*Length clocks. The chance is (127 - Prob)/128.
; CV is the register's low 8 bits as a level, 0 to +64 units (0..255 << 13). Gate is bit 0 while
; Clk is high, so two ones in a row give two gates.
; The chance comes from a 24-bit Galois shift register (as the Noise S&H's) stepped every sample.
; X data (10 words): [0] the noise's taps, [1] the noise, [2] Clk's last value, [3] the register,
; [4] the leaving bit's mask, 1 << (Length-1) (written by the Length routine), [5] the threshold,
; (127 - Prob) << 16 (written by the Prob routine), [6] Lock, [7] $FFFF, [8] $FF, [9] the logic high.
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
    asl #$d,a,a             ;       as a level, 0..$1FE000
    move a,x:$0             ; @out0 CV
    move x:(r3+$6),x1       ;       x1 = high
    move x:(r3),b
    and #<$1,b              ;       b = bit 0
    tst b
    tfr x1,b ifne           ;       1: high
    tfr y0,a
    tst a
    clr b ifle              ;       only while Clk is high
    lua (r3+$7),r3          ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out1 Gate
