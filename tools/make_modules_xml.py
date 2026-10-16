#!/usr/bin/env python3
"""Writes a copy of NME's modules.xml with the module types the experimental OS adds.

    tools/make_modules_xml.py ../Nomad2026/data/modules.xml out/modules.xml

Each new type is a text copy of an existing module's entry with its index, component id and
names changed, so the rest of the file stays byte for byte as NME has it.
"""
import re
import sys

# new type: (the type it is copied from, name, full name)
NEW_TYPES = {
    119: (19, "Mixer Inv", "3 Inputs Mixer, input 1 inverted (G1-Mods test)"),
}


def module_text(xml, index):
    m = re.search(r'\n  <module component-id="m%d" index="%d" .*?\n  </module>' % (index, index), xml, re.S)
    if not m:
        sys.exit(f"type {index} not found")
    return m


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    xml = open(sys.argv[1], encoding="utf-8").read()
    for new, (src, name, fullname) in NEW_TYPES.items():
        if f'index="{new}" name=' in xml:
            sys.exit(f"type {new} already exists")
        m = module_text(xml, src)
        text = re.sub(r'<module component-id="m%d" index="%d" name="[^"]*" fullname="[^"]*"' % (src, src),
                      f'<module component-id="m{new}" index="{new}" name="{name}" fullname="{fullname}"',
                      m.group(0), count=1)
        xml = xml[:m.end()] + text + xml[m.end():]
    open(sys.argv[2], "w", encoding="utf-8").write(xml)
    print(f"written {sys.argv[2]}: {len(NEW_TYPES)} new type(s)")


if __name__ == "__main__":
    main()
