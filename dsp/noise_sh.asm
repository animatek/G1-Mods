; Noise S&H (G1-Mods type 122), an idea of Javier's: a sample and hold with its own noise.
;   input 0 Trig        outputs 0 Out, 1 Inv (Out negated, for mirrored melodies)
; Control rate. The noise is a 24-bit Galois shift register that steps once per sample; on Trig's
; rising edge its value, scaled to the G1's control range (a quarter of full scale, like an LFO's
; peak), is held on Out, and negated on Inv.
; X data (4 words): [0] the register's taps, [1] the register, [2] Trig's last value, [3] the held
; value. Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop
; slot or after it.

    move x:$0,y0            ; @in0  y0 = Trig
    move x:(r3)+,x0         ;       x0 = taps
    move x:(r3),a           ;       a1 = the register
    lsr a                   ;       shift it right; the bit out goes to the carry
    eor x0,a ifcs           ;       and feeds back through the taps
    move a1,x:(r3)+         ;       keep it                         r3 -> Trig's last
    move x:(r3),b           ;       b = Trig's last value
    move y0,x:(r3)+         ;       remember Trig                   r3 -> the held value
    tst b
    bgt hold                ;       Trig was high already: no edge
    tfr y0,b
    tst b
    ble hold                ;       Trig is low: no edge
    move a1,x1              ;       edge: hold the register as a signed level
    tfr x1,a
    asr a
    asr a                   ;       a quarter of full scale
    move a,x:(r3)
hold:
    move x:(r3)+,b          ;       b = the held value              r3 -> past the data
    tfr b,a
    neg a
    move a,x:$0             ; @out1 Inv
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0 Out
