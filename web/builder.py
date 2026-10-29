"""What the web page calls, inside Pyodide: the same patch_rom.patch() the command line runs, so
a ROM built on the page is byte for byte the one tools/patch_rom.py writes.

    identify(file) -> "rack" or "micro" (what the file is), or raises patch_rom.BuildError saying what is wrong with it
    build(file, ["flipflop", "mux8"]) -> {"target": "rack" or "micro", "rom": bytes or None, "os": bytes or None,
                                          "no_os": why not, "bytes": n, "room": n, "types": [...], "log": str}

The file is the rack's 3.03 ROM, or what the Micro Modular has in place of one: its OS (Clavia's updater, the
.exe or a zip with it, or the extracted image). A Micro has no ROM to give back, so its "rom" is None: the OS
update is the only file. The modules always go in in the registry's build order, whatever order they were
ticked in, so the same list gives the same OS.
"""
import contextlib
import io
import re

import g1rom
import g1update
import patch_rom


def _bytes(x):
    return x.to_bytes() if hasattr(x, "to_bytes") else bytes(x)    # a JS Uint8Array, or bytes


def identify(file):
    return patch_rom.identify(_bytes(file))[0]


def build(file, folders):
    src = _bytes(file)
    target = patch_rom.identify(src)[0]
    g1rom.set_target(target)
    folders = list(folders)
    mods = {m.folder: m for m in patch_rom.modules()}
    if target == "micro":
        left_out = [f for f in folders if f in mods and not mods[f].meta.get("micro", True)]
        if left_out:
            raise patch_rom.BuildError(", ".join(mods[f].meta["name"] for f in left_out)
                                       + " is not on the Micro yet: untick it")
    chosen = [mods[f] for f in patch_rom.registry()["build"] if f in folders]
    if not chosen:
        raise patch_rom.BuildError("tick at least one module")
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            out = patch_rom.patch(src, [m.add for m in chosen])
    except SystemExit as e:              # the tools stop with sys.exit on what they refuse
        raise patch_rom.BuildError(str(e))
    except AssertionError as e:          # Build's own checks: no room left, a type taken...
        raise patch_rom.BuildError(f"the build refused it: {e}")
    image, no_os = None, ""
    try:
        image = g1update.from_rom(out)      # only if it fits what an update erases
    except SystemExit as e:
        no_os = str(e)
    used = re.search(r"packed, (\d+) bytes", log.getvalue()) or re.search(r"(\d+) bytes", log.getvalue())
    return {"target": target, "rom": out if target == "rack" else None, "os": image, "log": log.getvalue().strip(),
            "bytes": int(used[1]) if used else 0, "room": g1rom.ROOM, "no_os": no_os,
            "types": [m.type for m in chosen]}
