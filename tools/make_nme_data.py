#!/usr/bin/env python3
"""Adds the modules' types to NME's data: modules.xml and the classic theme.

    tools/make_nme_data.py ../Nomad2026/data out/nme-data      # copies, in out/
    tools/make_nme_data.py --layer ../Nomad2026/data           # NME's layer files, see below

Each module's folder has its entries whole (nme-modules.xml and nme-theme.xml); each is placed
right after the type its module.json names (nme_after), in modules/registry.json's nme order, so
the rest of each file stays byte for byte as NME has it. A type already in a file is replaced by
the fresh entry, so running it twice changes nothing and a changed definition reaches the file.
That merged copy is what G1-Emu's g1patchtest reads in the tests (G1_MODULES_XML).

--layer writes NME's own files instead, mods-modules.xml and mods-theme.xml: the modules alone,
which NME loads on top of Clavia's and offers only to a synth whose OS has them (its IAm says
3.09). Clavia's files are left untouched.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_rom  # noqa: E402

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


LAYER_HEAD = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
              "<!-- The G1-Mods layer: the module types a modified OS adds, loaded on top of\n"
              "     {file}. Written by G1-Mods' tools/make_nme_data.py (its layer mode), from its\n"
              "     modules/ folders: change them there, not here. GPL-3.0-only. -->\n")


def layer(dst):
    """NME's layer files: each module's entries, in the registry's nme order."""
    mods = [patch_rom.Module(f) for f in patch_rom.registry()["nme"]]
    entry = lambda m, f: open(os.path.join(m.dir, f), encoding="utf-8").read().rstrip("\n") + "\n"
    with open(os.path.join(dst, "mods-modules.xml"), "w", encoding="utf-8") as out:
        out.write(LAYER_HEAD.format(file="modules.xml") + "<ModuleDescriptions>\n<body>\n"
                  + "".join(entry(m, "nme-modules.xml") for m in mods) + "</body>\n</ModuleDescriptions>\n")
    with open(os.path.join(dst, "mods-theme.xml"), "w", encoding="utf-8") as out:
        out.write(LAYER_HEAD.format(file="classic-theme.xml") + "<modules>\n"
                  + "".join(entry(m, "nme-theme.xml") for m in mods) + "</modules>\n")
    print(f"written {dst}: mods-modules.xml, mods-theme.xml, types {[m.type for m in mods]}")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--layer":
        return layer(sys.argv[2])
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    os.makedirs(dst, exist_ok=True)
    mods = open(os.path.join(src, "modules.xml"), encoding="utf-8").read()
    theme = open(os.path.join(src, "classic-theme.xml"), encoding="utf-8").read()
    added = []
    for m in patch_rom.modules("nme"):
        entry = lambda f: "\n" + open(os.path.join(m.dir, f), encoding="utf-8").read().rstrip("\n")
        mods = place(mods, MODULES_ENTRY, m.meta["nme_after"], m.type, entry("nme-modules.xml"))
        theme = place(theme, THEME_ENTRY, m.meta["nme_after"], m.type, entry("nme-theme.xml"))
        added.append(m.type)
    open(os.path.join(dst, "modules.xml"), "w", encoding="utf-8").write(mods)
    open(os.path.join(dst, "classic-theme.xml"), "w", encoding="utf-8").write(theme)
    print(f"written {dst}: types {added}")


if __name__ == "__main__":
    main()
