; Noise S&H (G1-Mods type 122), an idea of Javier's: a sample and hold with its own noise.
;   input 0 Trig        outputs 0 Out, 1 Inv        parameters 0 Range (1-5 octaves), 1 Uni/Bi
; Control rate. The noise is a 24-bit Galois shift register that steps once per sample; on Trig's
; rising edge its value is held. Every sample the held value is scaled to the range: Bi spans
; -6n..+6n semitones, Uni 0..12n (n octaves; 12 control units are an octave at a pitch input with
; its amount at 127). Inv is the mirror within the range: Out negated in Bi, reflected about the
; middle in Uni.
; X data (6 words): [0] the register's taps, [1] the register, [2] Trig's last value, [3] the held
; noise, [4] the scale A (6n semitones as a fraction, written by the Range routine), [5] 1.0 for
; Uni or 0 for Bi (written by the Uni/Bi routine). Out = noise * A + U * A, Inv = U * A - noise * A.
; Word 0 runs in the previous module's nop slot (no a or b); no branch lands on the nop slot or
; after it.

    move x:$0,y0            ; @in0  y0 = Trig
    move x:(r3)+,x0         ;       x0 = taps
    move x:(r3),a           ;       a1 = the register
    lsr a                   ;       shift it right; the bit out goes to the carry
    eor x0,a ifcs           ;       and feeds back through the taps
    move a1,x:(r3)+         ;       keep it                         r3 -> Trig's last
    move x:(r3),b           ;       b = Trig's last value
    move y0,x:(r3)+         ;       remember Trig                   r3 -> the held noise
    tst b
    bgt hold                ;       Trig was high already: no edge
    tfr y0,b
    tst b
    ble hold                ;       Trig is low: no edge
    move a1,x:(r3)          ;       edge: hold the register
hold:
    move x:(r3)+,x0         ;       x0 = held noise                 r3 -> A
    move x:(r3)+,x1         ;       x1 = A                          r3 -> U
    mpy x1,x0,a             ;       a = noise * A
    move x:(r3)+,y0         ;       y0 = U                          r3 -> past the data
    mpy x1,y0,b             ;       b = U * A, the offset
    move b,y1
    add a,b                 ;       b = Out
    neg a
    add y1,a                ;       a = Inv
    move a,x:$0             ; @out1 Inv
    nop                     ;       the next module's word 0 goes here
    move b,x:$0             ; @out0 Out
