#!/usr/bin/env python3
"""Checks the Envelope (type 55) in G1-Emu with the G1-Mods ROM.

    modules/envelope/check_envelope.py

env.pch: a square LFO into Gate; Env on output 1, End on 2, the gate on 3. Parameters:
Mode, Attack, Decay 1, Level 1, Decay 2, Sustain, Release. Each case plays 4 s, a few notes (the
LFO fast enough for check_insert.py to find notes in its first and last seconds):
- Gate mode, Attack 0, Level 1 20 (10.1 units), Sustain 100 (50.4): at each gate on, Env is at
  the top (64) at once, comes down to Level 1, goes up to Sustain and holds there while the gate
  is high; at gate off it falls to 0 and End goes high; End is low while Env is not 0.
- The release: Env falls by e every 4/k samples (k the time knob's factor, a control sample
  being 4 audio samples), within a tenth.
- Attack 80: Env takes longer to reach the top than with Attack 40.
- Trig mode: the envelope ends (Env 0, End high) while the gate is still high.
Exit code 0 when all hold.
"""
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.environ.get("G1MODS_BUILD", "all")   # which modules the ROM has (patch_rom.py)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
SETTLE = 4800          # 50 ms at 96 kHz: the patch being set up
UNIT = 428167 / 64     # one control unit in the recording
BASE = "3 55 7 0 0 40 20 60 100 60 "


def factor(v):
    """A time knob's factor, as its routine makes it, as a fraction."""
    return ((0x800000 - ((v & 7) << 19)) >> (v >> 3)) - 1


def record(rom, xml, patch, tmp):
    pch, wav = (os.path.join(tmp, "e." + e) for e in ("pch", "wav"))
    open(pch, "w").write(patch)
    subprocess.run([BIN, rom, pch, "--seconds", "4", "--wav", wav], check=True, capture_output=True,
                   env=dict(os.environ, G1_MODULES_XML=xml))
    w = wave.open(wav)
    n, ch = w.getnframes(), w.getnchannels()
    raw = w.readframes(n)
    a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
    return [[v / UNIT for v in a[k::ch]] for k in range(ch)]


def main():
    rom = os.path.join(ROOT, "out", f"rom-{BUILD}.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), BUILD,
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    base = open(os.path.join(HERE, "env.pch")).read()
    ok = True

    def report(what, good, detail):
        nonlocal ok
        print(f"{what}: {detail} -> {'ok' if good else 'WRONG'}")
        ok &= good

    with tempfile.TemporaryDirectory() as tmp:
        def play(mode=0, a=0, d1=40, l1=20, d2=60, s=100, r=60):
            env, end, gate, _ = record(rom, xml, base.replace(BASE, f"3 55 7 {mode} {a} {d1} {l1} {d2} {s} {r} "), tmp)
            ons = [i for i in range(SETTLE, len(gate)) if gate[i] > 0 >= gate[i - 1]]
            offs = [i for i in range(SETTLE, len(gate)) if gate[i] <= 0 < gate[i - 1]]
            return env, end, gate, ons, offs

        env, end, gate, ons, offs = play()
        l1, sus = 20 * 64 / 127, 100 * 64 / 127
        notes = []
        for on in ons:
            off = next((f for f in offs if f > on), None)
            if off is None or off - on < 20000:
                continue
            seg = env[on:off]
            top = max(seg[:100])
            peak = seg.index(top)
            dip = min(seg[peak:])                   # after the attack
            held = seg[-200:]
            notes.append((round(top, 1), round(dip, 1), round(sum(held) / len(held), 1)))
        good = notes and all(t > 63.5 and abs(d - l1) < 0.5 and abs(h - sus) < 0.3 for t, d, h in notes)
        report("Gate mode", good, f"{len(notes)} notes (top, lowest, held): {notes[:3]}, Level 1 {l1:.1f}, "
                                  f"Sustain {sus:.1f}")

        rests = []
        for off in offs:
            on = next((o for o in ons if o > off), len(env))
            seg = env[off:on]
            if len(seg) < 20000:
                continue
            # End rises once, where the module calls Env done (it is then a hair above 0: the
            # output chain leaves a hundredth of a unit or so), and stays high
            j = next((i for i in range(len(seg)) if end[off + i] > 32), None)
            # (the last samples are the next note's: the gate is read a little early)
            ended = j is not None and all(end[off + i] > 32 for i in range(j, len(seg) - 16))
            busy = ended and all(abs(v) < 0.05 for v in seg[j:len(seg) - 16]) and seg[j // 2] > 0.05
            rests.append(bool(ended and busy))
        report("Release and End", rests and all(rests),
               f"{len(rests)} releases to 0 with End high after and low before: {rests}")

        off = offs[0] if offs[0] > ons[0] else offs[1]
        start = env[off + 8]
        when = next(i for i in range(off + 8, len(env)) if env[i] < start / 2.718281828)
        want = 4 / (factor(60) / 2 ** 23)
        report("Release time", abs((when - off - 8) / want - 1) < 0.1,
               f"down by e in {when - off - 8} samples, the model {want:.0f}")

        def rise(attack):
            env, _, _, ons, _ = play(a=attack)
            on = ons[1]
            return next(i for i in range(on, len(env)) if env[i] > 0.9 * 64) - on
        r40, r80 = rise(40), rise(80)
        report("Attack", 0 < r40 < r80, f"to 90 % in {r40} samples (Attack 40), {r80} (Attack 80)")

        env, end, gate, ons, offs = play(mode=1)
        ends = []
        for on in ons:
            off = next((f for f in offs if f > on), None)
            if off is None or off - on < 20000:
                continue
            ends.append(max(env[off - 200:off]) < 0.05 and min(end[off - 200:off]) > 32)
        report("Trig mode", ends and all(ends), f"{len(ends)} notes ended with the gate still high: {ends}")

    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
