#!/usr/bin/env python3
"""Adds the module types of the test OS to NME's data: modules.xml and the classic theme.

    tools/make_nme_data.py ../Nomad2026/data out/nme-data      # copies, in out/
    tools/make_nme_data.py ../Nomad2026/data ../Nomad2026/data # in place (NME's g1-mods branch)

Each new type is a text copy of an existing module's entry in both files, with its index,
component id, names and connectors changed, so the rest of each file stays byte for byte as NME
has it. A type already in a file is replaced by a fresh copy, so running it twice changes
nothing and a changed definition reaches the file.
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
    121: (19, "Mix1-1A", "1 Input Chain Mixer (G1-Mods)",
          [('name="in1"', 'name="in"'), ('name="in2"', 'name="chain"'),
           ('\n    <connector component-id="c3" index="2" name="in3" type="input" signal="audio" />', ''),
           ('<parameter component-id="p2" index="1" name="in level 2" class="parameter" defaultValue="127" extension="m2" role="audio,in,level" />',
            '<parameter component-id="p2" index="1" name="on" class="parameter" maxValue="1" defaultValue="1" formatter="fmtOffOn" extension="m2" />'),
           ('\n    <parameter component-id="p3" index="2" name="in level 3" class="parameter" defaultValue="127" extension="m3" role="audio,in,level" />', ''),
           ('<parameter component-id="m2" index="1" name="morph:in level 2" class="morph" role="morph"  minValue="-127" maxValue="127" />',
            '<parameter component-id="m2" index="1" name="morph:on" class="morph" role="morph"  minValue="-1" maxValue="1" />'),
           ('\n    <parameter component-id="m3" index="2" name="morph:in level 3" class="morph" role="morph"  minValue="-127" maxValue="127" />', ''),
           ('name="in level 1"', 'name="level"'), ('name="morph:in level 1"', 'name="morph:level"')],
          [("<name>Mixer</name>", "<name>Mix1-1A</name>"),
           ('alt="in1"', 'alt="in"'),
           ('<connector x="103" y="8" size="13" class="cAUDIO">\n\t\t\t<connector component-id="c2" alt="in2" />',
            '<connector x="190" y="8" size="13" class="cAUDIO">\n\t\t\t<connector component-id="c2" alt="chain" />'),
           ('\n\t\t<connector x="154" y="8" size="13" class="cAUDIO">\n\t\t\t<connector component-id="c3" alt="in3" />\n\t\t</connector>', ''),
           ('alt="in level 1"', 'alt="level"'),
           ('<knob x="120" y="4" size="21">\n\t\t\t<parameter component-id="p2" alt="in level 2" />\n\t\t</knob>',
            '<button x="100" y="7" width="30" height="16" cyclic="true" landscape="false">\n\t\t\t<parameter component-id="p2" alt="on" />\n\t\t\t<btn index="0">Ch 1</btn>\n\t\t\t<btn index="1">Ch 1</btn>\n\t\t</button>'),
           ('\n\t\t<knob x="171" y="4" size="21">\n\t\t\t<parameter component-id="p3" alt="in level 3" />\n\t\t</knob>', ''),
           ('\n\t</module>', '\n\t\t<label x="158" y="9">Chain</label>\n\t</module>')]),
}


MODULES_ENTRY = r'\n  <module component-id="m{t}" index="{t}" .*?\n  </module>'
THEME_ENTRY = r'\n\t<module component-id="m{t}" .*?\n\t</module>'


def clone(text, pattern, donor, new, header, subs):
    old = re.search(pattern.format(t=new), text, re.S)
    if old:                      # made by an earlier run: made again from the donor
        text = text[:old.start()] + text[old.end():]
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
    return text[:m.end()] + block + text[m.end():], not old


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    os.makedirs(dst, exist_ok=True)
    mods = open(os.path.join(src, "modules.xml"), encoding="utf-8").read()
    theme = open(os.path.join(src, "classic-theme.xml"), encoding="utf-8").read()
    added = []
    for new, (donor, name, fullname, mod_subs, theme_subs) in NEW_TYPES.items():
        # in NME the new types sit in "<donor's family> (mods)", listed right after the family
        header = (r'index="%d" name="[^"]*" fullname="[^"]*" category="([^"]*)"' % donor,
                  f'index="{new}" name="{name}" fullname="{fullname}" category="\\1 (mods)"')
        mods, a = clone(mods, MODULES_ENTRY, donor, new, header, mod_subs)
        theme, b = clone(theme, THEME_ENTRY, donor, new, None, theme_subs)
        added.append(new)
    open(os.path.join(dst, "modules.xml"), "w", encoding="utf-8").write(mods)
    open(os.path.join(dst, "classic-theme.xml"), "w", encoding="utf-8").write(theme)
    print(f"written {dst}: types {added}")


if __name__ == "__main__":
    main()
