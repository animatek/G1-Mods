; Random (G1-Mods type 6): the G2's randoms in one clocked module, with what the G1's lack: a Seed
; that repeats, Poly (every voice its own), Edge (gliding between values) and a chance per clock.
;   inputs 0 Clk, 1 Rst        outputs 0 Out, 1 Trig
;   parameters 0 Seed, 1 Poly, 2 Step, 3 Edge, 4 Prob, 5 Length (0 free, 1-16)
; Control rate. On each rising edge of Clk a new random number is drawn (16 steps of a 24-bit
; Galois shift register). Out moves toward it by Step (127 all the way: a new value each clock;
; low: a wander), gliding there with Edge; it spans -64..+64 units. Trig is high while Clk is,
; on the clocks a second draw falls under Prob. The register is loaded from Seed (and, with Poly
; on, the voice: the Seed routine is called once a voice and writes a value of the voice's) on
; the clock after the Seed is written (when the patch is set up, or the knob turned), on the clock
; after a Rst edge (as the G1's sequencers), and every Length clocks: the same Seed gives the same
; values, Length > 0 loops them.
; X data (18 words): [0] the register's taps, [1] the register, [2] Clk's last value, [3] Rst's
; last value, [4] load (not 0: the next clock loads the seed), [5] clocks since the load,
; [6] Length (an integer, $7FFFFF for 0: never), [7] the seed's value, [8] the voice's value,
; [9] Poly ($FFFFFF or 0), [10] Step (a fraction), [11] the target, [12-13] Out (48 bits, so a
; slow glide still moves), [14] Edge's glide factor, [15] Prob << 16, [16] the gate, [17] high.
; r3 stays put; the words are read at offsets from it.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y1            ; @in1  y1 = Rst
    move x:(r3+$3),a        ;       a = Rst's last value
    move y1,x:(r3+$3)
    tst a
    bgt norst               ;       Rst was high already: no edge
    tfr y1,a
    tst a
    ble norst               ;       Rst is low: no edge
    move y1,x:(r3+$4)       ;       edge: load at the next clock
norst:
    move x:$0,y0            ; @in0  y0 = Clk
    move x:(r3+$2),a        ;       a = Clk's last value
    move y0,x:(r3+$2)
    tst a
    bgt noclk               ;       Clk was high already: no edge
    tfr y0,a
    tst a
    ble noclk               ;       Clk is low: no edge
    move x:(r3+$5),b        ;       a clock: b = clocks since the load + 1
    add #<$1,b
    move x:(r3+$6),x0       ;       x0 = Length
    move x:(r3+$4),a        ;       a = load
    cmp x0,b
    blt noloop
    tfr y0,a                ;       Length reached: load (Clk is above 0)
noloop:
    tst a
    beq draw
    clr b                   ;       load: count from 0
    move x:(r3+$8),a        ;       the voice's value
    move x:(r3+$9),x0
    and x0,a                ;       with Poly on only
    move x:(r3+$7),x0
    eor x0,a                ;       and the seed's
    or #<$1,a               ;       never 0, or the register would stay 0
    move a1,x:(r3+$1)
    clr a
    move a,x:(r3+$4)        ;       loaded
draw:
    move b,x:(r3+$5)        ;       keep the count
    move x:(r3),x0          ;       x0 = taps
    move x:(r3+$1),a        ;       a1 = the register
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    lsr a
    eor x0,a ifcs
    move a1,x:(r3+$1)       ;       keep it
    tfr a,b                 ;       the chance: its low 16 bits (new since the last clock)
    lsl #$8,b
    lsr b                   ;       0..$7FFF80
    move b1,x1
    move x:(r3+$11),y1      ;       y1 = high
    move x:(r3+$f),b        ;       b = Prob << 16
    cmp x1,b
    tfr y1,b ifgt           ;       under it: a gate
    clr b ifle
    move b,x:(r3+$10)
    move x:(r3+$1),a        ;       the register again, as a signed number (the shifts left a2
                            ;       as it was, so a was not)
    asr #$2,a,a             ;       a = the draw, -0.25..0.25 (-64..+64 units)
    move x:(r3+$b),x0       ;       x0 = the target
    sub x0,a
    move a,x1               ;       x1 = draw - target
    move x:(r3+$a),y1       ;       y1 = Step
    mpy y1,x1,a
    add x0,a                ;       the target moves by Step of the way
    move a,x:(r3+$b)
noclk:
    move x:(r3+$c),a        ;       a = Out, 48 bits
    move x:(r3+$d),a0
    move x:(r3+$b),b        ;       b = the target
    sub a,b
    move b,x1               ;       x1 = target - Out
    move x:(r3+$e),y1       ;       y1 = Edge's factor (1: no glide)
    mac y1,x1,a             ;       Out glides toward the target
    move a1,x:(r3+$c)
    move a0,x:(r3+$d)
    move a,x:$0             ; @out0 Out
    move x:(r3+$10),b       ;       b = the gate
    tfr y0,a
    tst a
    clr b ifle              ;       only while Clk is high
    lua (r3+$12),r3         ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out1 Trig
