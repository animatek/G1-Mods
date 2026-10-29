#!/usr/bin/env python3
"""Builds the new module types into a copy of the user's G1 ROM (rack OS 3.03).

    tools/patch_rom.py all ../G1-Emu/Roms/NORD-MODULAR-RACK-VER-3.03.BIN Roms/rom-all.bin
    tools/patch_rom.py flipflop,mux8 <rom> Roms/rom-mine.bin     # just these modules
    tools/patch_rom.py all <Micro updater .exe, or its extracted image> Roms/os-micro.bin   # the Micro Modular's OS
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
import g1rom as G  # noqa: E402  (the target, the package's place and its room change with what is brought)
import g1update  # noqa: E402
from g1rom import Build, Param, audio_type, ram_to_rom  # noqa: E402,F401

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
    """Every module, or on the Micro the ones that are on it (a module's "micro": false in its module.json)."""
    mods = [m for m in modules() if G.TARGET == "rack" or m.meta.get("micro", True)]
    EXPERIMENTS["all"] = ("every module in modules/" + (" that is on the Micro" if G.TARGET == "micro" else "") + ": " +
                          ", ".join(f"{m.type} ({m.meta['name']})" for m in mods), [m.add for m in mods], [])


_all()


class BuildError(Exception):
    """A ROM the build cannot go into: not the 3.03, or not as expected where it writes."""


def identify(src):
    """What was brought: ("rack", the 512 KB ROM) or ("micro", the Micro's 3.03b OS image). The Micro has
    no ROM to bring: its OS is Clavia's update image, which can come as it is, extracted from the updater
    (`Nord Micro Modular OS v3.03b Update.exe`), or in a .zip that holds the updater."""
    data = bytes(src)
    if data[:2] == b"PK":                                  # a zip: the updater inside it
        import io
        import zipfile
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
            names = [n for n in z.namelist() if n.lower().endswith(".exe")]
            data = z.read(names[0]) if names else b""
        except zipfile.BadZipFile:
            data = b""
        if not data:
            raise BuildError("that zip has no Clavia updater (.exe) in it")
    if data[:2] == b"MZ":                                  # an updater: its payload is the OS
        try:
            model, major, minor, image = g1update.extract_updater(data)
        except ValueError as e:
            raise BuildError(f"that program has no Clavia OS update in it ({e})")
        if "micro" not in model.lower():
            raise BuildError(f"that is the updater of the {model}'s OS: for a rack the builder takes the 3.03 ROM, "
                             "for a Micro Modular its updater")
        data = image
    if len(data) == G.ROM_SIZE and hashlib.sha256(data).hexdigest().startswith(G.ROM_SHA256):
        return "rack", data
    if len(data) == G.MICRO_OS_SIZE and hashlib.sha256(data).hexdigest().startswith(G.MICRO_OS_SHA256):
        return "micro", data
    raise BuildError("not the rack OS 3.03 ROM, nor the Micro Modular's 3.03b OS (its updater, or the image)")


def patch(src, types, in_place=()):
    """What was brought (identify) with these types (callables given the Build) and in-place words; the new
    ROM as bytes (for the Micro, a ROM-shaped buffer holding its OS: g1update.from_rom turns it into the image).
    What the command line and the web builder (web/) both call."""
    target, data = identify(src)
    G.set_target(target)
    if target == "micro":
        # Put where the rack ROM keeps its OS, so every address below works as it does for the rack.
        rom = bytearray(b"\xff" * G.ROM_SIZE)
        rom[ram_to_rom(0x100000):ram_to_rom(0x100000) + len(data)] = data
    else:
        rom = bytearray(data)
    if types:
        in_place = list(in_place) + [G.VERSION_MARK]   # an OS with modules says so (3.09)
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
        packed = installable and blocks[0][0] == G.STAGE and len(blocks[0][1]) < b.at - G.RUN
        where = (f"stored at ${G.STAGE:06X}{' packed, ' + str(len(blocks[0][1])) + ' bytes' if packed else ''}"
                 ": fits an OS update" if installable else
                 f"too big for an OS update ({G.ROOM} bytes): G1-Emu only")
        print(f"new types {b.types}, {b.at - G.RUN} bytes, {where}, run at ${G.RUN:06X}")
    return bytes(rom)


def main():
    if sys.argv[1:] == ["--list"]:
        for name, (what, _, _) in EXPERIMENTS.items():
            print(f"{name}: {what}")
        return
    micro = "--micro" in sys.argv         # optional: says that what is brought must be the Micro's
    if micro:
        sys.argv.remove("--micro")
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    name, src, dst = sys.argv[1:]
    brought = open(src, "rb").read()
    try:
        target = identify(brought)[0]
    except BuildError as e:
        sys.exit(str(e))
    if micro and target != "micro":
        sys.exit("--micro, but what was brought is the rack's ROM")
    G.set_target(target)                  # "all" is every module that is on this target
    _all()
    if name not in EXPERIMENTS:
        mods = {m.folder: m for m in modules()}
        if any(n not in mods for n in name.split(",")):
            sys.exit(f"no experiment or module '{name}' (--list)")
        EXPERIMENTS[name] = (name, [mods[n].add for n in name.split(",")], [])
    try:
        rom = patch(brought, *EXPERIMENTS[name][1:])
    except BuildError as e:
        sys.exit(str(e))
    if target == "micro":
        try:
            rom = g1update.from_rom(rom)     # the OS image, the Micro's modules in it
        except SystemExit as e:
            sys.exit(str(e))
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst + ".tmp", "wb").write(rom)
    os.replace(dst + ".tmp", dst)   # never a half-written ROM for an emulator starting meanwhile
    print(f"{name}: written {dst}")


if __name__ == "__main__":
    main()
