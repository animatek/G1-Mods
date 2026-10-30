; Ctrl Send (G1-Mods type 122), after the G2's CtrlSend: control rate.
;   inputs 0 In, 1 Send        output 0 In thru        parameters 0 Ctrl, 1 Value, 2 Chan (68k only
;   for Ctrl and Chan)
; The DSP sends no MIDI: it leaves one word for the 68k, which reads it from the OS's main loop
; and queues a controller change on the MIDI OUT (ctrlsend_poll.s). That word packs Send's rising
; edge count (a step of $100 an edge) and the value (0..127), so a single read tells the 68k
; whether anything happened: the value moved, or Send went high.
; The value: In in control units (one unit is $8000, 0 unplugged) added to the Value knob and
; kept to 0..127, rounded down. A bipolar LFO (-64..+63) into In with Value 64 sweeps the whole
; range.
; X data (9 words): [0] the packed word, [1] Send as last seen (0 or $80), [2] the edge count,
; [3] $100, [4] 127, [5] Value, [6] Ctrl, [7] Chan (written by their routines), [8] $80.
; The words are read at offsets from r3, which is moved past them at the end. Word 0 runs in the
; previous module's nop slot (no a or b); no branch lands on the nop or after it.

    move x:$0,y0            ; @in1  y0 = Send
    move x:$0,y1            ; @in0  y1 = In
    move x:(r3+$1),b        ;       b = Send as last seen
    tfr y0,a
    tst a
    clr a ifle              ;       a = 0 when low
    move x:(r3+$8),x1
    tfr x1,a ifgt           ;       a = $80 when high
    cmp a,b
    beq nosend              ;       no edge
    move a,x:(r3+$1)        ;       remember it
    tst a
    ble nosend              ;       a falling edge: nothing to send
    move x:(r3+$2),b
    move x:(r3+$3),x0
    add x0,b
    move b,x:(r3+$2)        ;       one rising edge more
nosend:
    tfr y1,b
    asr #$f,b,b             ;       b1 = In in units, rounded down
    move x:(r3+$5),x0
    add x0,b                ;       + Value
    tst b
    clr b iflt              ;       below 0: 0
    move x:(r3+$4),x0
    cmp x0,b
    tfr x0,b ifgt           ;       above 127: 127
    move x:(r3+$2),a        ;       the count
    add b,a                 ;       + the value
    move a,x:(r3)           ;       the packed word
    lua (r3+$9),r3          ;       r3 -> past the data
    nop                     ;       the next module's word 0 goes here
    move y1,x:$0            ; @out0 In thru
