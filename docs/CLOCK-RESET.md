# Clock & reset

The sequencers and counters all follow the same clock, and **reset** is what keeps them on the
same step. This guide covers the clock signal, how reset works on the G1's own sequencers and on
G1-Mods' **8Steps** and **8Counter**, and the patches that show it.

## The clock

A clock is a regular gate. **ClkGen** makes one (its *4 pulses / beat* and *24 pulses / beat*
outputs); the G1's sequencers, the 8Steps and the 8Counter each move one step on every rising
edge.

## Reset

Reset works the same on the G1's own sequencers and on G1-Mods' modules:

- The **Rst** edge arms the module, and the **next clock** goes to step 1.
- The module **starts on its last step**, so the first clock plays step 1.
- That is what keeps several modules **in step**: give them the same clock and the same reset, and
  they land on step 1 together.

So to start every bar on step 1, send one reset edge to every sequencer and counter, just before
the first clock.

## The patch: 8Steps and a CtrlSeq together

[`modules/step-seq-5/seq5-ctrlseq.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/modules/step-seq-5/seq5-ctrlseq.pch)
shows it: one ClkGen clocks an **8Steps** and a G1 **CtrlSeq**, and one LFOA edge resets both.
They stay on the same step.

[`modules/counter8/counter8.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/modules/counter8/counter8.pch)
does the same with the **8Counter**: its eight outputs are high one at a time, in step with the
clock and reset.

## What to try

- Change the ClkGen's **rate** to speed everything up together.
- Set the 8Steps's knobs (Steps 5) and listen to the pattern.
- Use the 8Counter's eight outputs as the gates of eight events: each fires in turn.
- Clock a long sequencer and a short one from the same source and reset: the short one cycles every
  bar while the long one holds the phrase.
