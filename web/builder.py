"""What the web page calls, inside Pyodide: the same patch_rom.patch() the command line runs, so
a ROM built on the page is byte for byte the one tools/patch_rom.py writes.

    build(rom, ["flipflop", "mux8"]) -> {"rom": bytes, "os": bytes or None, "no_os": why not, "bytes": n, "types": [...], "log": str}

The modules always go in in the registry's build order, whatever order they were ticked in, so
the same list gives the same ROM.
"""
import contextlib
import io
import re

import g1update
import patch_rom


def build(rom, folders):
    rom = rom.to_bytes() if hasattr(rom, "to_bytes") else bytes(rom)   # a JS Uint8Array, or bytes
    folders = list(folders)
    mods = {m.folder: m for m in patch_rom.modules()}
    chosen = [mods[f] for f in patch_rom.registry()["build"] if f in folders]
    if not chosen:
        raise patch_rom.BuildError("tick at least one module")
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            out = patch_rom.patch(rom, [m.add for m in chosen])
    except SystemExit as e:              # the tools stop with sys.exit on what they refuse
        raise patch_rom.BuildError(str(e))
    except AssertionError as e:          # Build's own checks: no room left, a type taken...
        raise patch_rom.BuildError(f"the build refused it: {e}")
    image, no_os = None, ""
    try:
        image = g1update.from_rom(out)      # only if it fits what an update erases
    except SystemExit as e:
        no_os = str(e)
    used = re.search(r"(\d+) bytes", log.getvalue())
    return {"rom": out, "os": image, "log": log.getvalue().strip(),
            "bytes": int(used[1]) if used else 0, "types": [m.type for m in chosen], "no_os": no_os}
