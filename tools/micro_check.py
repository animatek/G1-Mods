#!/usr/bin/env python3
"""Checks, on the images you bring, the table that turns the rack ROM's OS addresses into the Micro's.

    tools/micro_check.py <rack ROM> <Micro 3.03b OS image>

g1rom.py names OS routines and data in the rack ROM's coordinates and, for the Micro, looks them up in
MICRO_ADDR. This lines the two OSes up (every 24-byte run that is in both exactly once, kept in order),
reads each address of the table off the nearest run, and says whether it is the one in MICRO_ADDR and
whether the code there starts the same. It also prints where the Micro's type table and the end of its OS
are. Nothing of Clavia's is written anywhere. NOTES.md, "The Micro Modular".
"""
import bisect
import collections
import os
import sys

os.environ["G1MODS_TARGET"] = "micro"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g1rom  # noqa: E402

W = 24


def landmarks(a, b):
    def unique(img):
        d = collections.defaultdict(list)
        for i in range(len(img) - W):
            d[img[i:i + W]].append(i)
        return {k: v[0] for k, v in d.items() if len(v) == 1}
    ua, ub = unique(a), unique(b)
    pairs = sorted((ua[k], ub[k]) for k in ua if k in ub)
    tails, idx, prev = [], [], [-1] * len(pairs)
    for n, (_, y) in enumerate(pairs):          # the longest run of them that keeps the order
        p = bisect.bisect_left(tails, y)
        if p == len(tails):
            tails.append(y)
            idx.append(n)
        else:
            tails[p] = y
            idx[p] = n
        prev[n] = idx[p - 1] if p else -1
    chain, n = [], idx[-1]
    while n != -1:
        chain.append(pairs[n])
        n = prev[n]
    return chain[::-1]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    rom = open(sys.argv[1], "rb").read()
    micro = open(sys.argv[2], "rb").read()
    rack = rom[g1rom.ram_to_rom(0x100000):g1rom.ram_to_rom(0x100000) + 0x5E000]
    chain = landmarks(rack, micro)
    keys = [a for a, _ in chain]
    print(f"{len(chain)} landmarks, the Micro's OS {len(micro):#x} bytes, ending at ${0x100000 + len(micro):06X}")
    bad = 0
    for addr, want in sorted(g1rom.MICRO_ADDR.items()):
        i = addr - 0x100000
        k = bisect.bisect_right(keys, i) - 1
        a, b = chain[k]
        got = 0x100000 + b + (i - a)
        same = sum(1 for x, y in zip(rack[i:i + 12], micro[got - 0x100000:got - 0x100000 + 12]) if x == y)
        ok = got == want and same >= 8
        bad += not ok
        print(f"${addr:06X} -> ${got:06X} {'==' if got == want else '!='} ${want:06X}, first bytes equal {same}/12  {'ok' if ok else 'WRONG'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
