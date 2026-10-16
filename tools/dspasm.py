#!/usr/bin/env python3
"""A small DSP56300 assembler for one-word instructions, labels and short branches.

    tools/dspasm.py dsp/flipflop.asm          # prints the words and the marks

It knows no syntax of its own: each instruction's encoding is looked up by its text in an index
made by disassembling every one-word opcode with G1-Emu's dspdis (built once into out/, a few
minutes). So an instruction is written exactly as dspdis prints it ("move x:(r3)+,x1",
"clr a ifgt"). Short branches ("bgt LABEL") are looked up by their displacement.

Source format: one instruction per line; "label:" on its own line; ";" starts a comment; a
comment "@name" marks the word for the module's routines (inputs and outputs to patch), e.g.
"move x:$0,y0   ; @in0". A word marked more than once with the same name is listed for each.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DSPDIS = os.path.join(ROOT, "..", "G1-Emu", "build", "tools", "dspdis")
INDEX = os.path.join(ROOT, "out", "dspasm-index.txt")
RANGES = ((0x000000, 0x200000), (0x200000, 0x300000), (0x400000, 0x600000))
BRANCHES = ("bra", "bcc", "bge", "bne", "bpl", "bnn", "bec", "blc", "bgt", "bcs", "blt", "beq",
            "bmi", "bnr", "bes", "bls", "ble", "bhs", "blo")


def norm(text):
    return re.sub(r"\s+", " ", text.strip())


def build_index():
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX + ".tmp", "w") as out:
        for lo, hi in RANGES:
            # each range from address 0, so a word's address is its offset in the range
            words = "".join(f"{v:06x}\n" for v in range(lo, hi))
            text = subprocess.run([DSPDIS], input=words, capture_output=True, text=True, check=True).stdout
            for line in text.splitlines():
                m = re.match(r"([0-9a-f]{6}): (.*);\s*([0-9a-f]{6})$", line)
                if m:
                    out.write(f"{int(m[1], 16) + lo:06x} {norm(m[2])}\n")
    os.replace(INDEX + ".tmp", INDEX)


_plain, _branch = None, None


def load():
    global _plain, _branch
    if _plain is not None:
        return
    if not os.path.exists(INDEX):
        build_index()
    _plain, _branch = {}, {}
    for line in open(INDEX):
        code, text = line.rstrip("\n").split(" ", 1)
        code = int(code, 16)
        m = re.match(r"(\w+) func_([0-9a-f]+)$", text)
        if m and m[1] in BRANCHES:
            # disassembled at address == word value within its range: displacement = target - address
            lo = max(r[0] for r in RANGES if r[0] <= code)
            _branch.setdefault((m[1], int(m[2], 16) - (code - lo)), code)
        else:
            _plain.setdefault(text, code)


def assemble(path):
    """Returns (words, marks {name: [word indexes]}, source lines per word)."""
    load()
    lines = []
    labels = {}
    for raw in open(path):
        text, _, comment = raw.partition(";")
        text = text.strip()
        marks = re.findall(r"@(\w+)", comment)
        if not text:
            continue
        if text.endswith(":"):
            labels[text[:-1]] = len(lines)
            continue
        lines.append((norm(text), marks))
    words, where = [], {}
    for i, (text, marks) in enumerate(lines):
        op, _, arg = text.partition(" ")
        if op in BRANCHES and arg in labels:
            disp = labels[arg] - i
            if (op, disp) not in _branch:
                raise SystemExit(f"{path}: no short {op} of {disp} words (line {i})")
            words.append(_branch[(op, disp)])
        elif text in _plain:
            words.append(_plain[text])
        else:
            raise SystemExit(f"{path}: no one-word encoding for '{text}'")
        for m in marks:
            where.setdefault(m, []).append(i)
    return words, where, [t for t, _ in lines]


if __name__ == "__main__":
    words, marks, src = assemble(sys.argv[1])
    for i, (w, t) in enumerate(zip(words, src)):
        print(f"{i:3}  {w:06x}  {t}")
    print("marks:", marks)
