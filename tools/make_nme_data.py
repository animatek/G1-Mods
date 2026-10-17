#!/usr/bin/env python3
"""Adds the modules' types to NME's data: modules.xml and the classic theme.

    tools/make_nme_data.py ../Nomad2026/data out/nme-data      # copies, in out/
    tools/make_nme_data.py ../Nomad2026/data ../Nomad2026/data # in place (NME's g1-mods branch)

Each module's folder has its entries whole (nme-modules.xml and nme-theme.xml); each is placed
right after the type its module.json names (nme_after), in modules/registry.json's nme order, so
the rest of each file stays byte for byte as NME has it. A type already in a file is replaced by
the fresh entry, so running it twice changes nothing and a changed definition reaches the file.
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


def main():
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
