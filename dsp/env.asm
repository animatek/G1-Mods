; Envelope (G1-Mods type 55): the G2's ADDSR, H, D and Mod AHD envelopes from one engine.
;   input 0 Gate        outputs 0 Env, 1 End
;   parameters 0 Mode (0 Gate, 1 Trig), 1 Attack, 2 Decay 1, 3 Level 1, 4 Decay 2, 5 Sustain,
;              6 Release
; Control rate. Stages: attack (to the top), decay 1 (to Level 1), decay 2 (to Sustain), release
; (to 0), each an exponential approach (a factor of the way a control sample, from the time
; knobs, as the Random's Edge: from at once to some 17 s down to -60 dB). Gate's rising edge
; starts the attack from wherever the envelope is. Gate mode: it holds at Sustain while Gate is
; high, and Gate falling releases it from any stage (the ADDSR). Trig mode: Gate's length does
; not matter, decay 2 goes on into release when it reaches Sustain (the D, the H with Decay 1 at
; Level 1 as the hold, the AHD). Env spans 0..+64 units; End is high while it is idle.
; The attack aims above the top (at 0.3) so it gets there, and stops at it; a decay goes on when
; it is within $200 of its level (-60 dB of the top); the release stops at 0 there.
; X data (20 words): [0] Mode, [1] Attack's factor, [2] Decay 1's, [3] Level 1, [4] Decay 2's
; factor, [5] Sustain, [6] Release's factor (all written by their routines), [7] the stage
; (0 idle, 1-4), [8-9] Env (48 bits, so a slow stage still moves), [10] Gate's last value,
; [11] the attack's aim, [12] the top (+64 units), [13] $200, [14] the logic high, [15-19] the
; stage numbers 1, 2, 3, 4 and 0.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y0            ; @in0  y0 = Gate
    move x:(r3+$a),a        ;       a = Gate's last value
    move y0,x:(r3+$a)
    tst a
    bgt washigh
    tfr y0,a
    tst a
    ble stages              ;       low and low
    move x:(r3+$f),x0       ;       rising: the attack
    move x0,x:(r3+$7)
    bra stages
washigh:
    tfr y0,a
    tst a
    bgt stages              ;       high and high
    move x:(r3),a           ;       falling: in Gate mode only,
    tst a
    bne stages
    move x:(r3+$7),a
    tst a
    beq stages              ;       and not when idle,
    move x:(r3+$12),x0      ;       the release
    move x0,x:(r3+$7)
stages:
    move x:(r3+$8),a        ;       a = Env, 48 bits
    move x:(r3+$9),a0
    move x:(r3+$7),b        ;       b = the stage
    cmp #<$1,b
    beq att
    cmp #<$2,b
    beq dec1
    cmp #<$3,b
    beq dec2
    cmp #<$4,b
    beq rel
    clr a                   ;       idle: 0
    bra out
att:
    move x:(r3+$b),b        ;       toward the aim
    sub a,b
    move b,x1
    move x:(r3+$1),y1
    mac y1,x1,a
    move x:(r3+$c),x0       ;       x0 = the top
    cmp x0,a
    blt out
    tfr x0,a                ;       there: stop at the top, decay 1
    move x:(r3+$10),x0
    move x0,x:(r3+$7)
    bra out
dec1:
    move x:(r3+$3),b        ;       toward Level 1
    sub a,b
    move b,x1
    move x:(r3+$2),y1
    mac y1,x1,a
    move x:(r3+$3),b
    sub a,b
    abs b
    move x:(r3+$d),x0
    cmp x0,b
    bge out
    move x:(r3+$11),x0      ;       near enough: decay 2
    move x0,x:(r3+$7)
    bra out
dec2:
    move x:(r3+$5),b        ;       toward Sustain
    sub a,b
    move b,x1
    move x:(r3+$4),y1
    mac y1,x1,a
    move x:(r3),b
    tst b
    beq out                 ;       Gate mode: it holds there
    move x:(r3+$5),b
    sub a,b
    abs b
    move x:(r3+$d),x0
    cmp x0,b
    bge out
    move x:(r3+$12),x0      ;       Trig mode, near enough: the release
    move x0,x:(r3+$7)
    bra out
rel:
    clr b                   ;       toward 0
    sub a,b
    move b,x1
    move x:(r3+$6),y1
    mac y1,x1,a
    move x:(r3+$d),x0
    cmp x0,a
    bge out
    clr a                   ;       near enough: 0, idle
    move x:(r3+$13),x0
    move x0,x:(r3+$7)
out:
    move a1,x:(r3+$8)
    move a0,x:(r3+$9)
    move a,x:$0             ; @out0 Env
    move x:(r3+$7),b        ;       End: high while idle
    tst b
    move x:(r3+$e),x1
    tfr x1,b ifeq
    clr b ifne
    lua (r3+$14),r3         ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out1 End
