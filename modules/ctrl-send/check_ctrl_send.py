#!/usr/bin/env python3
"""Checks the Ctrl Send (type 122) in G1-Emu with the G1-Mods ROM.

    modules/ctrl-send/check_ctrl_send.py

ctrlsend-lfo.pch: an LFO's square into In, Ctrl 7, Value 32, Chan 1. Each case is that patch with
something changed, played in G1-Emu's g1patchtest, which prints what came out of the G1's MIDI OUT
(G1_PATCHTEST names another build):

- the LFO alone: a ramp into In (the bench prints the first bytes only): control changes on
  channel 1, controller 7, each value one off the last, so every step of the ramp was sent.
- Chan 3, Ctrl 74: the same on channel 3, controller 74.
- live: the Value knob turned from 32 to 100 at 2 s, nothing in In: one CC, the new value.
- Send: the LFO into Send, nothing in In: a CC of the knob's value on every rising edge, all the
  same.
- no Ctrl Send: nothing comes out.
- with a Note Out in the patch too (they share the main loop's call): both send, the notes and
  the CCs. The build lays Note Out out first, so Ctrl Send chains to it.
Exit code 0 when all hold.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.environ.get("G1MODS_BUILD", "all")   # which modules the ROM has (patch_rom.py)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.environ.get("G1_PATCHTEST") or os.path.join(
    EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
LFO_TO_IN = "0 2 0 0 1 1 1 \n"
LFO_TO_SEND = "0 2 1 0 1 1 1 \n"
PARAMS = "2 122 3 7 32 0 \n"


def midi_out(rom, xml, patch, tmp, name, *args):
    pch = os.path.join(tmp, name + ".pch")
    open(pch, "w").write(patch)
    out = subprocess.run([BIN, rom, pch, "--note", "-1", "--seconds", "4", *args], check=True,
                         capture_output=True, text=True, env=dict(os.environ, G1_MODULES_XML=xml)).stdout
    m = re.search(r"^MIDI OUT: \d+ bytes(.*)$", out, re.M)
    if not m:
        sys.exit(f"{BIN} prints no MIDI OUT: a G1-Emu with it is needed (G1_PATCHTEST)")
    b = [int(x, 16) for x in m[1].split() if x != "..."]
    return [tuple(b[i:i + 3]) for i in range(0, len(b) - len(b) % 3, 3)]


def main():
    rom = os.path.join(ROOT, "out", f"rom-{BUILD}.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), BUILD,
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "ctrlsend-lfo.pch")).read()
    assert LFO_TO_IN in base and PARAMS in base
    ok = True

    def report(name, good, msgs):
        nonlocal ok
        ok &= good
        shown = " ".join("".join(f"{b:02x}" for b in m) for m in msgs[:6])
        print(f"{name}: {len(msgs)} messages ({shown}{' ...' if len(msgs) > 6 else ''}) -> {'ok' if good else 'WRONG'}")

    def ccs(msgs, status, ctrl):
        return [m for m in msgs if m[0] == status and m[1] == ctrl]

    with tempfile.TemporaryDirectory() as tmp:
        msgs = midi_out(rom, xml, base, tmp, "lfo")
        def ramp(msgs, status, ctrl):
            vals = [m[2] for m in msgs]
            return (len(msgs) >= 10 and all(m[:2] == (status, ctrl) for m in msgs)
                    and all(abs(a - b) == 1 for a, b in zip(vals, vals[1:])))

        report("the LFO alone (channel 1, controller 7, one step at a time)", ramp(msgs, 0xB0, 7), msgs)

        msgs = midi_out(rom, xml, base.replace(PARAMS, "2 122 3 74 32 2 \n"), tmp, "chan3")
        report("Chan 3, Ctrl 74", ramp(msgs, 0xB2, 74), msgs)

        msgs = midi_out(rom, xml, base.replace(LFO_TO_IN, ""), tmp, "live", "--param-at", "2:1:2:1:100")
        report("live: Value to 100 at 2 s", msgs == [(0xB0, 7, 100)], msgs)

        msgs = midi_out(rom, xml, base.replace(LFO_TO_IN, LFO_TO_SEND), tmp, "send")
        report("Send: the knob's value on each rising edge",
               len(msgs) >= 3 and all(m == (0xB0, 7, 32) for m in msgs), msgs)

        gone = base.replace("2 122 2 8 \n", "").replace(PARAMS, "").replace(LFO_TO_IN, "").replace("2 CCOut\n", "")
        msgs = midi_out(rom, xml, gone, tmp, "none")
        report("no Ctrl Send", msgs == [], msgs)

        both = (base.replace("2 122 2 8 \n", "2 122 2 8 \n3 60 2 14 \n")
                .replace(LFO_TO_IN, LFO_TO_SEND + "0 3 1 0 1 1 1 \n")
                .replace(PARAMS, PARAMS + "3 60 2 0 100 \n")
                .replace("2 CCOut\n", "2 CCOut\n3 NoteOut\n"))
        msgs = midi_out(rom, xml, both, tmp, "both")
        notes = [m for m in msgs if m[0] in (0x90, 0x80)]
        report("with a Note Out too: notes and CCs",
               len(notes) >= 3 and len(ccs(msgs, 0xB0, 7)) >= 3 and len(msgs) == len(notes) + len(ccs(msgs, 0xB0, 7)), msgs)
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
