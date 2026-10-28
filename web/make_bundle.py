#!/usr/bin/env python3
"""Packs what the web builder runs into web/bundle.json: the builder's Python (tools/), every
module's folder minus its tests, and each module's assembled DSP code (out/dspasm-*.json, made
here first if a source changed), so the browser never needs G1-Emu's disassembler.

    web/make_bundle.py

Nothing of Clavia's goes in: the page builds from the ROM the user picks, in the browser.
"""
import base64
import glob
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET

WEB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(WEB)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import dspasm  # noqa: E402
from g1rom import ROOM  # noqa: E402

TOOLS = ("g1rom.py", "dspasm.py", "patch_rom.py", "g1update.py", "lz.py", "unlz.m68k")
MODULE_FILES = ("module.json", "build.py", "*.asm", "*.m68k")
IMAGES = ("*.png", "*.webp", "*.jpg", "*.jpeg", "*.gif")   # a module's pictures: modules/<name>/images/
OPTIONAL = ("about", "usage", "notes", "credits", "status")   # text for the module's page, in module.json


def sheet(d):
    """What a module's page shows, read from its nme-modules.xml: ports, controls, lights, load."""
    path = os.path.join(d, "nme-modules.xml")
    if not os.path.exists(path):
        return {}
    el = ET.parse(path).getroot()
    ports = {"input": [], "output": []}
    for c in el.findall("connector"):
        ports[c.get("type")].append({"name": c.get("name"), "signal": c.get("signal")})
    controls = []
    for p in el.findall("parameter"):
        if p.get("class") == "parameter":
            controls.append({k: p.get(k) for k in ("name", "minValue", "maxValue", "defaultValue", "formatter")})
    lights = [{"name": l.get("name"), "type": l.get("type")} for l in el.findall("light")]
    load = {a.get("name"): a.get("value") for a in el.findall("attribute")}
    return {"inputs": ports["input"], "outputs": ports["output"], "controls": controls, "lights": lights,
            "load": load, "category": el.get("category")}


def main():
    reg = json.load(open(os.path.join(ROOT, "modules", "registry.json")))
    files = {f"tools/{t}": os.path.join(ROOT, "tools", t) for t in TOOLS}
    files["modules/registry.json"] = os.path.join(ROOT, "modules", "registry.json")
    files["web/builder.py"] = os.path.join(WEB, "builder.py")
    modules = []
    for folder in reg["build"]:
        d = os.path.join(ROOT, "modules", folder)
        for pattern in MODULE_FILES:
            for path in sorted(glob.glob(os.path.join(d, pattern))):
                files[f"modules/{folder}/{os.path.basename(path)}"] = path
                if path.endswith(".asm"):
                    dspasm.assemble(path)       # keeps out/dspasm-<name>.json up to date
                    cache = os.path.join(ROOT, "out", "dspasm-" + os.path.basename(path) + ".json")
                    files[f"out/{os.path.basename(cache)}"] = cache
        meta = json.load(open(os.path.join(d, "module.json")))
        pics = []
        for pattern in IMAGES:
            for path in sorted(glob.glob(os.path.join(d, "images", pattern))):
                dest = os.path.join(WEB, "modules", folder, os.path.basename(path))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(path, dest)
                pics.append(f"modules/{folder}/{os.path.basename(path)}")
        patches = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(d, "*.pch")))]
        modules.append({k: meta.get(k) for k in ("type", "name", "fullname", "summary", "kind",
                                                 "author", "licence", "version", "real_g1") + OPTIONAL}
                       | {"folder": folder, "images": pics, "patches": patches} | sheet(d))
    bundle = {
        "modules": modules,
        "room": ROOM,
        "files": {k: base64.b64encode(open(v, "rb").read()).decode() for k, v in sorted(files.items())},
    }
    out = os.path.join(WEB, "bundle.json")
    json.dump(bundle, open(out + ".tmp", "w"))
    os.replace(out + ".tmp", out)
    print(f"{out}: {len(modules)} modules, {len(files)} files, {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
