#!/usr/bin/env python3
"""Builds the new module types into a copy of the user's G1 ROM (rack OS 3.03).

    tools/patch_rom.py all ../G1-Emu/Roms/NORD-MODULAR-RACK-VER-3.03.BIN Roms/rom-all.bin
    tools/patch_rom.py flipflop,mux8 <rom> Roms/rom-mine.bin     # just these modules
    tools/patch_rom.py --list

Each module is a folder in modules/ (its module.json, its build.py, its DSP code and its tests);
modules/registry.json gives each its type, for ever, and the order they are laid out in. An
experiment either changes DSP words in place (with the word expected there checked first) or
adds new module types: their data go into the RAM the OS leaves untouched, one registration
routine registers them all, and the registration list's last call is pointed at it. On any
other ROM it stops instead of writing. The ROM itself never enters the repo, and neither does
the result. The parts every module uses are in g1rom.py; how it all works: NOTES.md.
"""
import hashlib
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g1rom import (ROM_SHA256, ROM_SIZE, ROOM, RUN, STAGE, VERSION_MARK, Build, Param,  # noqa: E402,F401
                   audio_type, ram_to_rom)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MODULES = os.path.join(ROOT, "modules")


class Module:
    """A module's folder: its module.json (meta) and its build.py's build(b, type)."""

    def __init__(self, folder):
        self.folder = folder
        self.dir = os.path.join(MODULES, folder)
        self.meta = json.load(open(os.path.join(self.dir, "module.json")))
        self.type = self.meta["type"]
        spec = importlib.util.spec_from_file_location(f"g1mod_{folder.replace('-', '_')}",
                                                      os.path.join(self.dir, "build.py"))
        self.code = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.code)

    def add(self, b):
        self.code.build(b, self.type)


def registry():
    return json.load(open(os.path.join(MODULES, "registry.json")))


def modules(order="build"):
    """Every module, in the registry's build (or nme) order; each one's type checked against it."""
    reg = registry()
    out = [Module(f) for f in reg[order]]
    for m in out:
        assert reg["given"].get(str(m.type)) == m.folder, f"{m.folder}: type {m.type} not given to it"
    assert sorted(m.folder for m in out) == sorted(reg["given"].values())
    return out


def vca_test(b, new_type=56):
    """An audio-rate test type: Out = In * Level (the fraction (v << 16) + (v << 9))."""
    audio_type(b, new_type, "vca_test.asm", (0x7FFE00,),
               [Param("Level", 127, 0, "2002 4840 4240 2202 e181 d281 d081")])


# name: (what it shows, the new types (a callable each, given the Build), or the DSP words to
# change in place). Any comma-separated list of modules' folders is an experiment too.
EXPERIMENTS = {
    "mixer3-silent": (
        "Mixer (3): the rounding multiply-accumulate becomes clr a, so the module is mute",
        None, [(0x1493CE + 5 * 4, 0x2000A3, 0x200013)],
    ),
    "stringtest": (
        "type 56 alone, the Osc String (as it was made, before it was known to fit with the rest)",
        [lambda b: Module("osc-string").add(b)], [],
    ),
    "audiotest": (
        "an audio-rate test type 56, a VCA: Out = In * Level",
        [vca_test], [],
    ),
}


def _all():
    mods = modules()
    EXPERIMENTS["all"] = ("every module in modules/: " + ", ".join(
        f"{m.type} ({m.meta['name']})" for m in mods), [m.add for m in mods], [])


_all()


class BuildError(Exception):
    """A ROM the build cannot go into: not the 3.03, or not as expected where it writes."""


def patch(src, types, in_place=()):
    """The user's ROM (bytes) with these types (callables given the Build) and in-place words;
    the new ROM, as bytes. What the command line and the web builder (web/) both call."""
    rom = bytearray(src)
    if len(rom) != ROM_SIZE or not hashlib.sha256(rom).hexdigest().startswith(ROM_SHA256):
        raise BuildError("not the rack OS 3.03 ROM")
    if types:
        in_place = list(in_place) + [VERSION_MARK]   # an OS with modules says so (3.09)
    for addr, old, new in in_place:
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old.to_bytes(4, "big"):
            raise BuildError(f"unexpected word at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new.to_bytes(4, "big")
    if types:
        b = Build(bytes(rom))
        for add in types:
            add(b)
        blocks, (addr, old, new), installable = b.finish()
        for at, data in blocks:
            o = ram_to_rom(at)
            if rom[o:o + len(data)] != b"\xff" * len(data):
                raise BuildError(f"${at:06X} is not free in this ROM")
            rom[o:o + len(data)] = data
        o = ram_to_rom(addr)
        if rom[o:o + 4] != old:
            raise BuildError(f"unexpected hook at ${addr:06X}: {rom[o:o + 4].hex()}")
        rom[o:o + 4] = new
        for addr, old, new in b.patches():      # the OS's calls a module takes over
            o = ram_to_rom(addr)
            if rom[o - 2:o] != b"\x4e\xb9" or rom[o:o + 4] != old:
                raise BuildError(f"unexpected call at ${addr - 2:06X}: {rom[o - 2:o + 4].hex()}")
            rom[o:o + 4] = new
        packed = installable and blocks[0][0] == STAGE and len(blocks[0][1]) < b.at - RUN
        where = (f"stored at ${STAGE:06X}{' packed, ' + str(len(blocks[0][1])) + ' bytes' if packed else ''}"
                 ": fits an OS update" if installable else
                 f"too big for an OS update ({ROOM} bytes): G1-Emu only")
        print(f"new types {b.types}, {b.at - RUN} bytes, {where}, run at ${RUN:06X}")
    return bytes(rom)


def main():
    if sys.argv[1:] == ["--list"]:
        for name, (what, _, _) in EXPERIMENTS.items():
            print(f"{name}: {what}")
        return
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    name, src, dst = sys.argv[1:]
    if name not in EXPERIMENTS:
        mods = {m.folder: m for m in modules()}
        if any(n not in mods for n in name.split(",")):
            sys.exit(f"no experiment or module '{name}' (--list)")
        EXPERIMENTS[name] = (name, [mods[n].add for n in name.split(",")], [])
    try:
        rom = patch(open(src, "rb").read(), *EXPERIMENTS[name][1:])
    except BuildError as e:
        sys.exit(str(e))
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst + ".tmp", "wb").write(rom)
    os.replace(dst + ".tmp", dst)   # never a half-written ROM for an emulator starting meanwhile
    print(f"{name}: written {dst}")


if __name__ == "__main__":
    main()
