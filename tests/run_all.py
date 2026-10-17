#!/usr/bin/env python3
"""Runs every test of the new types, one after another, and says which failed.

    tests/run_all.py

Each module's check_*.py (in modules/<name>/), then this folder's, builds the ROM and NME's
data itself and plays its patches in G1-Emu's g1patchtest (built in ../G1-Emu/build). Exit code 0 when all of them pass.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    failed = []
    for test in (sorted(glob.glob(os.path.join(HERE, "..", "modules", "*", "check_*.py")))
                 + sorted(glob.glob(os.path.join(HERE, "check_*.py")))):
        name = os.path.basename(test)
        print(f"== {name}", flush=True)
        if subprocess.run([sys.executable, "-I", test]).returncode:
            failed.append(name)
    print("ALL OK" if not failed else "FAILED: " + ", ".join(failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
