#!/usr/bin/env python3
"""Checks that every new type survives a module added live, in G1-Emu with the G1-Mods ROM.

    tests/check_insert.py

Each test patch plays for 3 s and a FilterE (type 51) is added to it at 1 s, the message NME sends
when a module is dropped on the canvas (G1-Emu's --add-module-at). The output must go on as it
was: its peak in the last second within a fifth of the first second's. It broke when a type's
descriptor gave its record (in the OS's RAM) too few words for its parameters: the new module's
record was written over them (NOTES.md, "A module's record in the OS's RAM").
"""
import os
import subprocess
import sys
import tempfile
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.environ.get("G1MODS_BUILD", "all")   # which modules the ROM has (patch_rom.py)
EMU = os.path.join(ROOT, "..", "G1-Emu")
BIN = os.path.join(EMU, "build", "tools", "patchtest", "g1patchtest_artefacts", "Release", "g1patchtest")
PATCHES = ("mix1-1a/mix1-1a-chain.pch",
           "flipflop/flipflop-lfo.pch",
           "step-seq-5/seq5.pch",
           "turing-machine/turing.pch",
           "scale-quantizer/quant.pch",
           "counter8/counter8.pch",
           "mux8/mux8.pch",
           "random/random.pch",
           "bits/bits.pch",
           "level/level.pch",
           "envelope/env.pch",
           "osc-string/string.pch")   # in modules/
RATE = 96000


def main():
    rom = os.path.join(ROOT, "out", f"rom-{BUILD}.bin")
    xml = os.path.join(ROOT, "out", "nme-data", "modules.xml")
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "patch_rom.py"), BUILD,
                    os.path.join(EMU, "Roms", "NORD-MODULAR-RACK-VER-3.03.BIN"), rom], check=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_nme_data.py"),
                    os.path.join(ROOT, "..", "Nomad2026", "data"), os.path.dirname(xml)], check=True)
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for name in PATCHES:
            wav = os.path.join(tmp, "w.wav")
            subprocess.run([BIN, rom, os.path.join(ROOT, "modules", name), "--seconds", "3",
                            "--add-module-at", "1:51:20:5:0", "--wav", wav],
                           check=True, capture_output=True, env=dict(os.environ, G1_MODULES_XML=xml))
            w = wave.open(wav)
            n, ch = w.getnframes(), w.getnchannels()
            raw = w.readframes(n)
            a = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)]
            good = True
            peaks = []
            for c in range(ch):
                x = a[c::ch]
                before = max(abs(v) for v in x[RATE // 20:RATE])
                after = max(abs(v) for v in x[2 * RATE:])
                if before:
                    peaks.append(f"{before}->{after}")
                    good &= abs(after - before) <= before / 5
            print(f"{name}: output peaks before and after the insertion {', '.join(peaks)} -> {'ok' if good else 'WRONG'}")
            ok &= good
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
