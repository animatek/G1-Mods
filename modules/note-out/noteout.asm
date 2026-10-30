; Note Out (G1-Mods type 60), after the G2's NoteSend: control rate.
;   inputs  0 Note, 1 Gate        output 0 Gate thru        parameters 0 Chan, 1 Vel (68k only), 2 Mute
; The DSP sends no MIDI: it leaves one word for the 68k, which reads it from the OS's main loop
; and queues the note on the MIDI OUT (noteout_poll.s). That word packs the gate's edge count
; (a step of $100 an edge), the gate (bit 7) and the note latched on the last rising edge
; (0..127), so a single read tells the 68k whether anything happened and what.
; The note: a semitone is one control unit ($8000), and 0 is note 64, an E (the keyboard's Note
; out); rounded to the nearest semitone and kept to 0..127. Gate is high above 0.
; Mute: the gate counts as low while it is on, so a note held is turned off (the falling edge)
; and no note goes out; Gate thru is left as it comes.
; X data (12 words): [0] the packed word, [1] the gate as last seen (0 or $80), [2] the edge
; count, [3] half a semitone ($4000), [4] 64, [5] $100, [6] $80, [7] 127, [8] the note latched,
; [9] Chan and [10] Vel (written by their routines, read by the 68k), [11] Mute's mask: $80 off,
; 0 on.
; The words are read at offsets from r3, which is moved past them at the end. Word 0 runs in the
; previous module's nop slot (no a or b); no branch lands on the nop or after it.

    move x:$0,y0            ; @in1  y0 = Gate
    move x:(r3+$1),b        ;       b = the gate as last seen
    tfr y0,a
    tst a
    clr a ifle              ;       a = 0 when low
    move x:(r3+$6),x1
    tfr x1,a ifgt           ;       a = $80 when high
    move x:(r3+$b),x0
    and x0,a                ;       muted: a = 0
    cmp a,b
    beq pack                ;       no edge
    move a,x:(r3+$1)        ;       remember it
    move x:(r3+$2),b
    move x:(r3+$5),x0
    add x0,b
    move b,x:(r3+$2)        ;       one edge more
    tst a
    ble pack                ;       a falling edge: the note stays
    move x:$0,b             ; @in0  b = Note
    move x:(r3+$3),x0
    add x0,b                ;       + half a semitone
    asr #$f,b,b             ;       b1 = semitones from the E, rounded down
    move x:(r3+$4),x0
    add x0,b                ;       + 64
    tst b
    clr b iflt              ;       below 0: 0
    move x:(r3+$7),x0
    cmp x0,b
    tfr x0,b ifgt           ;       above 127: 127
    move b,x:(r3+$8)        ;       the note, latched
pack:
    move x:(r3+$2),b        ;       the count
    move x:(r3+$8),x0
    add x0,b                ;       + the note
    move x:(r3+$1),x0
    add x0,b                ;       + the gate
    move b,x:(r3)           ;       the packed word
    lua (r3+$c),r3          ;       r3 -> past the data: r3 walks through every module's X
                            ;       data, and the next one reads its own from here (left at
                            ;       our start, the module after this one ran on our words)
    nop                     ;       the next module's word 0 goes here
    move y0,x:$0            ; @out0 Gate thru (y0 = Gate since word 0)
