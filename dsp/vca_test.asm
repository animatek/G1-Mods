; VCA test (G1-Mods, an experiment only, type 56): the first audio-rate type of ours, to check
; audio_type and its parameter routine: Out = In * Level.
;   input 0 In        output 0 Out        parameter 0 Level
; X data (1 word): [0] Level (a fraction, written by its routine).

    move x:$0,x1            ; @in0  x1 = In
    move x:(r3)+,x0         ;       x0 = Level                      r3 -> past the data
    mpy x1,x0,a
    nop                     ;       the next module's word 0 goes here
    move a,x:$0             ; @out0 Out
