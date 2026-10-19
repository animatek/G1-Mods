#!/usr/bin/env python3
"""Checks the Note Out (type 60) in G1-Emu with the G1-Mods ROM.

    modules/note-out/check_note_out.py

noteout-lfo.pch: an LFO's square into Gate, Note unplugged, Chan 1 and Vel 100. Each case is
that patch with something changed, played in G1-Emu's g1patchtest, which prints what came out
of the G1's MIDI OUT (G1-Emu 2026-10-19, PR #79; G1_PATCHTEST names another build):

- the LFO alone: notes on and off in turn, all E4 (64) on channel 1 with velocity 100, each off
  for the note just turned on.
- a Constant (+12) into Note, Chan 3, Vel 90: E5 (76) on channel 3 with velocity 90.
- live: Chan changed to 5 at 2 s as NME does (--param-at): the notes move to channel 5, and the
  one left on is turned off on its own channel.
- a patch with no Note Out: nothing comes out.
- an LFO after it (in the patch's order) into Note: the notes follow it, so the module after
  the Note Out runs on its own data (the Note Out once left r3 at its own words, and the module
  after it ran on them: a second NoteSeq stood still, and a module added live silenced the MIDI).
Exit code 0 when all hold.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.environ.get("G1_PATCHTEST") or os.path.join(
    EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
LFO_TO_GATE = "0 2 1 0 1 1 1 \n"


def midi_out(rom, xml, patch, tmp, name, *args):
    pch = os.path.join(tmp, name + ".pch")
    open(pch, "w").write(patch)
    out = subprocess.run([BIN, rom, pch, "--note", "-1", "--seconds", "4", *args], check=True,
                         capture_output=True, text=True, env=dict(os.environ, G1_MODULES_XML=xml)).stdout
    m = re.search(r"^MIDI OUT: \d+ bytes(.*)$", out, re.M)
    if not m:
        sys.exit(f"{BIN} prints no MIDI OUT: a G1-Emu with it is needed (G1_PATCHTEST)")
    assert "..." not in m[1], "more MIDI OUT than the bench prints"
    b = [int(x, 16) for x in m[1].split()]
    return [tuple(b[i:i + 3]) for i in range(0, len(b) - len(b) % 3, 3)]


def pairs_ok(msgs, channel, note, vel, least=4):
    """Ons and offs in turn on the channel, the note and velocity given, each off for the last on."""
    want = [(0x90 | channel, note, vel), (0x80 | channel, note, 64)]
    return len(msgs) >= least and all(m == want[i % 2] for i, m in enumerate(msgs))


def main():
    rom = os.path.join(ROOT, "out", "rom-all.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), "all",
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "noteout-lfo.pch")).read()
    assert LFO_TO_GATE in base and "2 60 2 0 100 \n" in base
    ok = True

    def report(name, good, msgs):
        nonlocal ok
        ok &= good
        shown = " ".join("".join(f"{b:02x}" for b in m) for m in msgs[:6])
        print(f"{name}: {len(msgs)} messages ({shown}{' ...' if len(msgs) > 6 else ''}) -> {'ok' if good else 'WRONG'}")

    with tempfile.TemporaryDirectory() as tmp:
        msgs = midi_out(rom, xml, base, tmp, "lfo")
        report("the LFO alone (E4, channel 1, velocity 100)", pairs_ok(msgs, 0, 64, 100), msgs)

        const = (base.replace("2 60 2 8 \n", "2 60 2 8 \n3 43 2 12 \n")
                 .replace(LFO_TO_GATE, LFO_TO_GATE + "0 2 0 0 3 0 1 \n")
                 .replace("2 60 2 0 100 \n", "2 60 2 2 90 \n3 43 2 76 0 \n")
                 .replace("2 NoteOut\n", "2 NoteOut\n3 Constant\n"))
        msgs = midi_out(rom, xml, const, tmp, "const")
        report("a Constant (+12) into Note, Chan 3, Vel 90", pairs_ok(msgs, 2, 76, 90), msgs)

        msgs = midi_out(rom, xml, base, tmp, "live", "--param-at", "2:1:2:0:4")
        chans = [m[0] & 0x0F for m in msgs]
        on1, on5 = [m for m in msgs if m[0] & 0x0F == 0], [m for m in msgs if m[0] & 0x0F == 4]
        # a note on when Chan changes still goes off on channel 1: each channel's own pairs
        good = (chans == sorted(chans) and set(chans) == {0, 4}
                and all(m == ((0x90, 64, 100), (0x80, 64, 64))[i % 2] for i, m in enumerate(on1))
                and len(on1) % 2 == 0 and pairs_ok(on5, 4, 64, 100, least=2))
        report("live: Chan to 5 at 2 s", good, msgs)

        after = (base.replace("2 60 2 8 \n", "2 60 2 8 \n3 24 2 12 \n")
                 .replace(LFO_TO_GATE, LFO_TO_GATE + "1 2 0 0 3 1 1 \n")
                 .replace("2 60 2 0 100 \n", "2 60 2 0 100 \n3 24 8 40 1 0 0 0 0 64 0 \n")
                 .replace("2 NoteOut\n", "2 NoteOut\n3 LFOB\n"))
        msgs = midi_out(rom, xml, after, tmp, "after")
        notes = {m[1] for m in msgs if m[0] == 0x90}
        report("an LFO after it into Note", len(notes) > 1 and all(m[0] in (0x90, 0x80) for m in msgs), msgs)

        msgs = midi_out(rom, xml, base.replace("2 60 2 8 \n", "").replace("2 60 2 0 100 \n", "")
                        .replace(LFO_TO_GATE, "").replace("2 NoteOut\n", ""), tmp, "none")
        report("no Note Out", msgs == [], msgs)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
