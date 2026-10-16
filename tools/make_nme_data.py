#!/usr/bin/env python3
"""Adds the module types of the test OS to NME's data: modules.xml and the classic theme.

    tools/make_nme_data.py ../Nomad2026/data out/nme-data      # copies, in out/
    tools/make_nme_data.py ../Nomad2026/data ../Nomad2026/data # in place (NME's g1-mods branch)

Each new type is a text copy of an existing module's entry in both files, with its index,
component id, names and connectors changed, so the rest of each file stays byte for byte as NME
has it. A type already in a file is left alone, so running it twice changes nothing.
"""
import os
import re
import sys

# new type: (donor type, name, full name, [(old, new) in modules.xml], [(old, new) in the theme])
NEW_TYPES = {
    119: (19, "Mixer Inv", "3 Inputs Mixer, input 1 inverted (G1-Mods test)", [], []),
    120: (89, "FlipFlop", "D Flip-Flop (G1-Mods)",
          [('name="A" type="input" signal="control"', 'name="clk" type="input" signal="logic"'),
           ('name="B" type="input" signal="control"', 'name="D" type="input" signal="logic"'),
           ('name="A>=B"', 'name="Q"')],
          [("<name>CompareAB</name>", "<name>FlipFlop</name>"),
           ('class="cCONTROL"', 'class="cLOGIC"'),
           ('alt="A"', 'alt="clk"'), ('alt="B"', 'alt="D"'), ('alt="A&gt;=B"', 'alt="Q"'),
           (">A</label>", ">Clk</label>"), (">B</label>", ">D</label>"),
           (">A&gt;=B</label>", ">Q</label>")]),
}


MODULES_ENTRY = r'\n  <module component-id="m{t}" index="{t}" .*?\n  </module>'
THEME_ENTRY = r'\n\t<module component-id="m{t}" .*?\n\t</module>'


def clone(text, pattern, donor, new, header, subs):
    if re.search(pattern.format(t=new), text, re.S):
        return text, False
    m = re.search(pattern.format(t=donor), text, re.S)
    if not m:
        sys.exit(f"type {donor} not found")
    block = m.group(0).replace(f'component-id="m{donor}"', f'component-id="m{new}"', 1)
    if header:
        block = re.sub(header[0], header[1], block, count=1)
    for old, rep in subs:
        if old not in block:
            sys.exit(f"type {new}: '{old}' not in type {donor}'s entry")
        block = block.replace(old, rep)
    return text[:m.end()] + block + text[m.end():], True


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    os.makedirs(dst, exist_ok=True)
    mods = open(os.path.join(src, "modules.xml"), encoding="utf-8").read()
    theme = open(os.path.join(src, "classic-theme.xml"), encoding="utf-8").read()
    added = []
    for new, (donor, name, fullname, mod_subs, theme_subs) in NEW_TYPES.items():
        header = (r'index="%d" name="[^"]*" fullname="[^"]*"' % donor,
                  f'index="{new}" name="{name}" fullname="{fullname}"')
        mods, a = clone(mods, MODULES_ENTRY, donor, new, header, mod_subs)
        theme, b = clone(theme, THEME_ENTRY, donor, new, None, theme_subs)
        if a or b:
            added.append(new)
    open(os.path.join(dst, "modules.xml"), "w", encoding="utf-8").write(mods)
    open(os.path.join(dst, "classic-theme.xml"), "w", encoding="utf-8").write(theme)
    print(f"written {dst}: added {added or 'nothing (already there)'}")


if __name__ == "__main__":
    main()
