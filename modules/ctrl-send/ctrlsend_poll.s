| Ctrl Send's 68k side: the OS's main loop calls this once a turn, in place of its own first call
| ($1156BE, at $100E6E) or of the call another module put there (the build chains them: this
| routine's first call is patched to the previous one). It finds the Ctrl Send modules of the four
| slots, reads each one's packed word from its DSP and queues a controller change (CC) on the
| MIDI OUT when the word has moved: its value changed, or a rising edge on Send (ctrlsend.asm
| says what the word holds). A turn with the queue more than half full leaves the change for
| the next turn, so a sweep never floods the MIDI OUT or loses its last value.
|
| On a real G1 the first build with this hung at power-on (2026-10-26, NOTES.md): the scan now
| follows a pointer only into RAM, even, and with a DSP number that exists, as unused pointers hold
| power-on garbage there.
|
| No list is registered by the module: a scan of every slot's module pointers (common and poly,
| indexes 1..127) finds them, a few pointers a turn (SCAN_STEP), and each turn a module already
| found is checked again (its pointer and its type) before it is read, so a patch changed or a
| module deleted drops it (with a note off for a note it left on). The whole scan in one turn
| held the main loop up long enough for the OS to miss a patch upload: it does things on time
| there.
|
| Assembled with GNU as for the CPU32 (tools/m68kasm.sh); position independent, so the build
| places it anywhere in the package. TYPE comes from the build (--defsym).
|
| The OS, rack 3.03 (G1-Emu/NOTES.md, G1-Mods/NOTES.md):
|   slot block       $1AB988 + slot * $6000; module pointers, a long an index: +$467A common,
|                    +$4C66 poly; voice records from +$228 of the same (14 bytes each)
|   module record    the type at +$0E, its X base (word) at +8; the voice record's X base at +8
|                    and its DSP at +0: a module's X word n is at both bases + n
|   $10C32E(dsp.w, address.l)   reads an X word through the DSP's host port
|   $15E2D2          the MIDI OUT's byte queue: data, read +$300, write +$304, last +$308,
|                    count (word) +$30C; drained by the timer interrupt

        .equ SLOTS,      0x1AB988
        .equ SLOT_SIZE,  0x6000
        .equ COMMON,     0x467A
        .equ POLY,       0x4C66
        .equ VOICES,     0x228
        .equ READ_X,     0x10C32E
        .equ OS_FIRST,   0x1156BE
        .equ QUEUE,      0x15E2D2
        .equ X_PACKED,   0
        .equ X_CTRL,     6
        .equ X_CHAN,     7
        .equ BUSY,       0x180           | queue count above which a change waits
        .equ MAX,        16              | modules followed at once
        .equ RAM_LO,     0x100000        | the RAM a module record can be in
        .equ RAM_HI,     0x1FFF00
        .equ DSPS,       4
        .equ SCAN_STEP,  8               | module pointers looked at a turn (1024 in all)

| an entry, 20 bytes
        .equ E_MOD,      0               | module record (0: free)
        .equ E_VOICE,    4               | voice record
        .equ E_LAST,     8               | the packed word last read
        .equ E_SLOT,     12              | the module pointer's address
        .equ E_SIZE,     20

| the state, at the end, through a5 (pc-relative is read-only)
        .equ S_CURSOR,   0               | the next pointer to look at: slot, section, index
        .equ S_ENTRIES,  2

        .text
        .globl poll
poll:
        jsr     OS_FIRST                 | the call this one replaces
        movem.l %d2-%d7/%a2-%a5,-(%sp)
        lea     (state,%pc),%a5          | the state, written through a5 (not pc-relative)
        bsr     scan

        lea     S_ENTRIES(%a5),%a4
        moveq   #MAX-1,%d7
next:   tst.l   E_MOD(%a4)
        beq.s   skip
        movea.l E_SLOT(%a4),%a0          | still this module, of our type?
        move.l  (%a0),%d0
        cmp.l   E_MOD(%a4),%d0
        bne.s   gone
        movea.l %d0,%a0
        cmpi.b  #TYPE,0x0E(%a0)
        bne.s   gone
        moveq   #X_PACKED,%d0
        bsr     readx
        cmp.l   E_LAST(%a4),%d0
        beq.s   skip                     | nothing happened
        move.l  %d0,%d6
        lea     QUEUE,%a1
        cmpi.w  #BUSY,0x30C(%a1)
        bcc.s   skip                     | the MIDI OUT is busy: the change waits
        moveq   #X_CTRL,%d0
        bsr     readx
        andi.b  #0x7F,%d0
        move.b  %d0,%d4                  | the controller
        moveq   #X_CHAN,%d0
        bsr     readx
        andi.b  #0x0F,%d0
        ori.b   #0xB0,%d0
        move.b  %d0,%d3                  | control change, on the channel
        move.b  %d6,%d5
        andi.b  #0x7F,%d5                | the value
        bsr     queue
        move.l  %d6,E_LAST(%a4)
        bra.s   skip
gone:   clr.l   E_MOD(%a4)
skip:   lea     E_SIZE(%a4),%a4
        dbra    %d7,next
        movem.l (%sp)+,%d2-%d7/%a2-%a5
        rts

| X word d0 of entry a4's module, through the host port, into d0
readx:  movea.l E_VOICE(%a4),%a0
        movea.l E_MOD(%a4),%a1
        moveq   #0,%d1
        move.w  8(%a0),%d1
        add.l   %d1,%d0
        move.w  8(%a1),%d1
        add.l   %d1,%d0
        move.l  %d0,-(%sp)               | the address
        moveq   #0,%d0
        move.b  (%a0),%d0
        move.w  %d0,-(%sp)               | the DSP
        jsr     READ_X
        addq.l  #6,%sp
        rts

| d3 d4 d5 into the MIDI OUT's byte queue, as the OS's own note senders do ($103790): dropped
| when it is full. The count goes up last, in one instruction, for the interrupt that drains it.
queue:  lea     QUEUE,%a1
        cmpi.w  #0x2FD,0x30C(%a1)
        bcc.s   1f
        movea.l 0x304(%a1),%a0
        move.b  %d3,(%a0)+
        move.b  %d4,(%a0)+
        move.b  %d5,(%a0)+
        cmpa.l  0x308(%a1),%a0
        bls.s   2f
        movea.l %a1,%a0
2:      move.l  %a0,0x304(%a1)
        addq.w  #3,0x30C(%a1)
1:      rts

| SCAN_STEP more module pointers, from the cursor (bits 9-8 the slot, 7 the section, poly when
| set, 6-0 the index): a Ctrl Send there not followed yet gets a free entry. Its word as it is
| now is taken as already seen, so finding a module sends nothing.
scan:   movem.l %d7/%a4,-(%sp)
        moveq   #SCAN_STEP-1,%d4
s_next: move.w  S_CURSOR(%a5),%d2
        move.w  %d2,%d0
        addq.w  #1,%d0
        andi.w  #0x3FF,%d0
        move.w  %d0,S_CURSOR(%a5)
        move.w  %d2,%d3
        andi.w  #0x7F,%d3                | the index
        beq.w   s_done                   | 0 is no module
        move.w  %d2,%d0
        lsr.w   #8,%d0                   | the slot
        mulu.w  #SLOT_SIZE,%d0
        addi.l  #SLOTS+COMMON,%d0
        btst    #7,%d2
        beq.s   1f
        addi.l  #POLY-COMMON,%d0
1:      movea.l %d0,%a3                  | the section's module pointers
        moveq   #0,%d0
        move.w  %d3,%d0
        lsl.w   #2,%d0
        lea     (%a3,%d0.l),%a1          | the pointer's address
        move.l  (%a1),%d0
        beq.w   s_done
        cmpi.l  #RAM_LO,%d0              | a pointer into RAM, even: a slot never used holds
        bcs.w   s_done                   | whatever the RAM had at power-on (zeros only in
        cmpi.l  #RAM_HI,%d0              | G1-Emu), and following it may stop the CPU
        bcc.w   s_done
        btst    #0,%d0
        bne.w   s_done
        movea.l %d0,%a0
        cmpi.b  #TYPE,0x0E(%a0)
        bne.w   s_done
        cmpi.b  #DSPS-1,VOICES(%a3)      | and the section's DSP one of the four
        bhi.w   s_done
        lea     S_ENTRIES(%a5),%a4       | followed already?
        moveq   #MAX-1,%d7
2:      cmp.l   E_MOD(%a4),%d0
        beq.w   s_done
        lea     E_SIZE(%a4),%a4
        dbra    %d7,2b
        lea     S_ENTRIES(%a5),%a4       | a free entry
        moveq   #MAX-1,%d7
3:      tst.l   E_MOD(%a4)
        beq.s   4f
        lea     E_SIZE(%a4),%a4
        dbra    %d7,3b
        bra.w   s_done                   | none: not followed
4:      move.l  %d0,E_MOD(%a4)
        move.l  %a1,E_SLOT(%a4)
        lea     VOICES(%a3),%a0
        move.l  %a0,E_VOICE(%a4)
        moveq   #X_PACKED,%d0
        bsr     readx
        move.l  %d0,E_LAST(%a4)
s_done: dbra    %d4,s_next
        movem.l (%sp)+,%d7/%a4
        rts

        .even
state:
        .fill   S_ENTRIES+MAX*E_SIZE,1,0
