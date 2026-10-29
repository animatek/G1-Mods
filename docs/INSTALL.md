# Installing G1-Mods

How to get the new modules into **G1-Emu** and into a **real Nord Modular G1 rack**, step by
step. Read it all once before you start, and see the way back (`docs/RECOVERY.md`) before you
touch a real synth.

> **Experimental.** On one real G1 (2026-10-26) all 13 modules have played in one build, and
> going back to Clavia's OS worked every time. That is one synth. A modified OS may still lose
> your patches or leave your G1 unusable, and recovery is not guaranteed. You do it at your own
> risk; you are responsible for your instrument. Try everything in G1-Emu first.

## Two files, two ways in

The builder gives two files. They are **not interchangeable**; this is the whole difference:

| File | For | How it loads |
| --- | --- | --- |
| **OS update** (`g1mods-...-os.bin`) | **G1-Emu and a real G1** | **Only through update mode**, the same on both: put the synth in update mode, then NME's *Device > Update Synth OS*. In G1-Emu: *Settings > OS... > Update mode*. On a real G1: Shift + Store held at power-on. |
| **ROM** (`g1mods-...-rom.bin`) | **G1-Emu only** | In G1-Emu's *Settings > ROM > Choose...*; it offers to restart with it. A real G1 cannot take it, and NME's Update Synth OS refuses it (it is 512 KB, an update has room for 393,184 bytes). |

If you are unsure, use the OS update: it works on both. The ROM is only a shortcut for the emulator.

## What you need

- **The rack's 3.03 ROM**, the file G1-Emu boots (`NORD-MODULAR-RACK-VER-3.03.BIN`, 512 KB). We
  do not give it: it is Clavia's. The modules are built into your own copy.
- **Animatek NME 0.25 or later**: the first version with G1-Mods support. It shows the new modules
  when a synth has them, and has *Device > Update Synth OS* to install an OS over MIDI. Older
  versions do not know the new modules: with one, a G1-Mods OS connects but the modules are not offered.
- **G1-Emu**, to try a build before a real synth.
- **A rack or keyboard G1.** The **Micro Modular** runs another OS. Twelve of the modules can be built into it
  from the command line (`tools/patch_rom.py --micro`) and run in G1-Emu's Micro model; the web builder takes the
  rack's ROM only, and nobody has tried it on a real Micro (see the [roadmap](../ROADMAP.md) and `NOTES.md`).
- For a real G1: a MIDI interface connected to the G1's **PC port** (both ways), as for editing.
- For the way back on a real G1, either of these:
    - **NME's *Device > Update Synth OS*** with **Clavia's own 3.03b OS image** (a `.bin`): the same
      way you installed yours, with the G1 in update mode. Keep that image before you start (see *Going back & fixes*);
    - or **Clavia's OS 3.03b updater** (Windows `.exe`, or the Mac version; on Linux it runs in Wine).

## 1. Build your OS

On the builder page (on the live site, or `web/serve.sh` from a clone):

1. Drop your 3.03 ROM on it. It checks it is the right one. Nothing is uploaded.
2. Tick the modules you want.
3. Tick that you have read the risks, and press **Build my OS**.
4. You get **one file, the OS update** (`g1mods-...-os.bin`), and it serves for both: install
   it into G1-Emu (put in update mode) or into a real G1's flash, the same way, with NME's
   *Device > Update Synth OS*. The page also gives the whole ROM (`g1mods-...-rom.bin`), for G1-Emu
   only: NME refuses it as too big for an update. If there is no OS update (too many modules, or a
   module that works only in G1-Emu for now; a build for G1-Emu alone is on the [roadmap](../ROADMAP.md)),
   the page says why and the ROM is the only file.

From a clone of this repo the same is `tools/patch_rom.py` and `tools/g1update.py fromrom`
(README, "Where the builds are").

Keep your list of modules, not the files: the files contain Clavia's firmware and must not be
shared. Anyone with their own ROM builds the same OS from the same list.

## 2. Try it in G1-Emu

**With the OS update (the usual way, the same as a real G1):** put G1-Emu in update mode
(*Settings > OS... > Update mode*), then in NME *Device > Update Synth OS*, pick the `…-os.bin`
and start. When it ends, G1-Emu keeps that OS. Then go on with "Either way" below.

**Or with the ROM** (`g1mods-...-rom.bin`): in G1-Emu, *Settings > ROM > Choose...*; it offers to
restart with it (a G1-Emu older than 2026-10-29 only writes it down: close and open it again). Your
usual flash is then the one it uses, so patches that name a new module are best kept for a flash of
its own. From a clone, `./run-g1emu.sh` builds the ROM and starts G1-Emu with it and **a flash of its own**.

If G1-Emu's settings name an OS file (`os =`, left by an earlier update), that OS boots instead of the
one in the ROM and the modules are not there: *Settings > OS... > The ROM's own OS* clears it
(`./run-g1emu.sh` starts with `G1_OS=` empty for the same reason).

Either way:

1. Connect NME. It says **MODDED OS** in its status bar, the synth reports version **3.09**, and
   the new modules are in the module palette.
2. Load a patch that uses them (each module's folder has one, `modules/<name>/*.pch`).

## 3. Install it on a real G1

Do these in order. The whole update takes about **12 minutes** at the safe speed.

1. **Back up your patches.** In NME, save every bank you care about to your computer.
2. **Check which synth NME is talking to**: the real G1, not G1-Emu.
3. **Switch the G1 off. Hold Shift + Store and switch it on.** It shows *Update utility* and
   waits.
4. In NME: **Device > Update Synth OS**. Pick the **OS update** file (`g1mods-...-os.bin`), speed
   **Safe**, and start.
5. Leave it alone until it ends: do not touch the cable, the synth or the computer.
6. The G1 asks **"Update flash?"**: press **Store**. Any other key keeps your old OS.
   It shows *Erasing flash*, *Writing to flash*, *Verifying flash*, then *Update completed*.
7. **Switch it off and on.** It starts as usual.
8. Connect NME: **MODDED OS** in the status bar, and the new modules in the palette.

### Using the modules

- Play patches with new modules **in a slot**. Storing one in a bank works with the modified OS,
  but under Clavia's OS that patch names a module the OS does not have, and loading it may hang
  the synth. **Before going back to Clavia's OS, delete or overwrite every stored patch that uses
  a new module.**
- A patch with a new module can be sent only to a synth whose OS has that module: NME checks.
