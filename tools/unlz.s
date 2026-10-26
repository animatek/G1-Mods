| unlz: unpacks the package at boot (tools/lz.py packs it). Called by the bootstrap with
|   a0 = the packed bytes (in the flash), a1 = where they go (RUN), a2 = a1 + unpacked length.
| Format: a flags byte, then eight items, its bits low first: 1 = a literal byte; 0 = a match of
| two bytes, big endian, (distance - 1) << 4 | (length - 3): copy `length` bytes from `distance`
| bytes back in what is already unpacked (3-18 bytes, 1-4096 back; they may overlap).
| Position independent; d0-d1/a0-a1 are the caller's to lose, the rest is kept.
| Assembled with tools/m68kasm.sh into tools/unlz.m68k, which g1rom.py puts into the bootstrap.

unlz:
        movem.l %d2-%d3/%a3,-(%sp)
flags:
        cmpa.l  %a2,%a1
        bcc.s   done
        move.b  (%a0)+,%d1
        moveq   #7,%d2
item:
        cmpa.l  %a2,%a1
        bcc.s   done
        lsr.b   #1,%d1
        bcc.s   match
        move.b  (%a0)+,(%a1)+
        dbra    %d2,item
        bra.s   flags
match:
        move.b  (%a0)+,%d0
        lsl.w   #8,%d0
        move.b  (%a0)+,%d0
        moveq   #15,%d3
        and.w   %d0,%d3
        lsr.w   #4,%d0
        movea.l %a1,%a3
        suba.w  %d0,%a3
        subq.l  #1,%a3
        addq.w  #2,%d3
copy:
        move.b  (%a3)+,(%a1)+
        dbra    %d3,copy
        dbra    %d2,item
        bra.s   flags
done:
        movem.l (%sp)+,%d2-%d3/%a3
        rts
