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
    120: (89, None, None, None, None),   # written whole: FULL_ENTRIES below
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


# Types written whole (no donor's entry to adapt): (modules.xml entry, theme entry), each placed
# right after its donor's. The images are the donor's until the module has its own.
FULL_ENTRIES = {
    120: ("""
  <module component-id="m120" index="120" name="FlipFlop" fullname="Flip-Flop D/RS (G1-Mods)" category="Logic (mods)">
    <image type="screenshot" src="img/modules/module-89.png" width="256" height="30" />
    <image type="icon16x16" src="img/icons/16x16/module-id-89.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-89.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="clk" type="input" signal="logic" />
    <connector component-id="c2" index="1" name="in" type="input" signal="logic" />
    <connector component-id="c3" index="2" name="rst" type="input" signal="logic" />
    <connector component-id="c4" index="0" name="Q" type="output" signal="logic" />
    <connector component-id="c5" index="1" name="NotQ" type="output" signal="logic" />
    <light component-id="ledQ" name="LED Q" index="0" type="led" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="type" class="parameter" maxValue="1" extension="m1" />
    <parameter component-id="m1" index="0" name="morph:type" class="morph" role="morph"  minValue="-1" maxValue="1" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.8" />
    <attribute name="x-mem" type="double" value="0.25" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="1.75" />
    <attribute name="dyn-mem" type="double" value="0.25" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="2" />
    <attribute name="background" value="#fc8642" />
  </module>""", """
\t<module component-id="m120" width="255" height="30">
\t\t<name>FlipFlop</name>
\t\t<label x="96" y="17">Rst</label>
\t\t<connector x="114" y="16" size="13" class="cLOGIC">
\t\t\t<connector component-id="c3" alt="rst" />
\t\t</connector>
\t\t<label x="132" y="17">Clk</label>
\t\t<connector x="152" y="16" size="13" class="cLOGIC">
\t\t\t<connector component-id="c1" alt="clk" />
\t\t</connector>
\t\t<label x="164" y="2">In</label>
\t\t<connector x="170" y="1" size="13" class="cLOGIC">
\t\t\t<connector component-id="c2" alt="in" />
\t\t</connector>
\t\t<button x="186" y="7" width="26" height="16" cyclic="true" landscape="false">
\t\t\t<parameter component-id="p1" alt="type" />
\t\t\t<btn index="0">D</btn>
\t\t\t<btn index="1">RS</btn>
\t\t</button>
\t\t<light component-id="ledQ" type="led" x="226" y="4" width="7" height="7" />
\t\t<label x="218" y="2">Q</label>
\t\t<connector x="236" y="1" size="13" class="cLOGIC">
\t\t\t<connector component-id="c4" alt="Q" />
\t\t</connector>
\t\t<label x="216" y="17">nQ</label>
\t\t<connector x="236" y="16" size="13" class="cLOGIC">
\t\t\t<connector component-id="c5" alt="NotQ" />
\t\t</connector>
\t</module>"""),
}


MODULES_ENTRY = r'\n  <module component-id="m{t}" index="{t}" .*?\n  </module>'
THEME_ENTRY = r'\n\t<module component-id="m{t}" .*?\n\t</module>'


def place(text, pattern, donor, new, block):
    """Puts a whole entry right after the donor's, replacing an earlier one of the same type."""
    old = re.search(pattern.format(t=new), text, re.S)
    if old:
        text = text[:old.start()] + text[old.end():]
    m = re.search(pattern.format(t=donor), text, re.S)
    if not m:
        sys.exit(f"type {donor} not found")
    return text[:m.end()] + block + text[m.end():]


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
        if new in FULL_ENTRIES:
            mods = place(mods, MODULES_ENTRY, donor, new, FULL_ENTRIES[new][0])
            theme = place(theme, THEME_ENTRY, donor, new, FULL_ENTRIES[new][1])
            added.append(new)
            continue
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
