# Installing G1-Mods

How to get the new modules into **G1-Emu** and into a **real Nord Modular G1 rack**, step by
step, and how to go back to Clavia's OS. Read it all once before you start.

> **Experimental.** On one real G1 (2026-10-26) all 13 modules have played in one build, and
> going back to Clavia's OS worked every time. That is one synth. A modified OS may still lose
> your patches or leave your G1 unusable, and recovery is not guaranteed. You do it at your own
> risk; you are responsible for your instrument. Try everything in G1-Emu first.

## What you need

- **The rack's 3.03 ROM**, the file G1-Emu boots (`NORD-MODULAR-RACK-VER-3.03.BIN`, 512 KB). We
  do not give it: it is Clavia's. The modules are built into your own copy.
- **Animatek NME** with G1-Mods support: it shows the new modules when a synth has them, and has
  *Device > Update Synth OS* to install an OS over MIDI.
- **G1-Emu**, to try a build before a real synth.
- For a real G1: a MIDI interface connected to the G1's **PC port** (both ways), as for editing.
- For the way back on a real G1: **Clavia's OS 3.03b updater** (Windows `.exe`, or the Mac
  version; on Linux it runs in Wine).

## 1. Build your OS

On the builder page (`web/`, `web/serve.sh` on your computer for now):

1. Drop your 3.03 ROM on it. It checks it is the right one. Nothing is uploaded.
2. Tick the modules you want.
3. Tick that you have read the risks, and press **Build my OS**.
4. You get two files:
   - **the ROM** (`g1mods-...-rom.bin`): for G1-Emu;
   - **the OS update** (`g1mods-...-os.bin`): for a real G1's flash. If the page does not offer
     it, say why it gives (too many modules, or a module not ready for a real G1).

From a clone of this repo the same is `tools/patch_rom.py` and `tools/g1update.py fromrom`
(README, "Where the builds are").

Keep your list of modules, not the files: the files contain Clavia's firmware and must not be
shared. Anyone with their own ROM builds the same OS from the same list.

## 2. Try it in G1-Emu

1. Close G1-Emu if it is running.
2. Start it with the ROM you built and **a flash of its own**, so your usual patches are not
   touched: `G1-Emu g1mods-rom.bin g1mods-flash.bin`.
3. If G1-Emu's settings name an OS file (`os =`), start it with that empty (`G1_OS=`): that OS
   would boot instead of the one in your ROM, and the modules would not be there.
4. Connect NME. It says **MODDED OS** in its status bar, the synth reports version **3.09**, and
   the new modules are in the module palette.
5. Load a patch that uses them (each module's folder has one, `modules/<name>/*.pch`).

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

## 4. Going back to Clavia's OS

1. Delete or overwrite the stored patches that use new modules (above).
2. Switch the G1 off. **Hold Shift + Store and switch it on.**
3. Run **Clavia's 3.03b updater**, at its safe (slower) speed, through the same MIDI interface.
4. Press **Store** at "Update flash?", wait for *Update completed*, switch it off and on.

## If something goes wrong

| What you see | What it means | What to do |
| --- | --- | --- |
| *Writing to flash / Write Error* | The flash could not be written. | Switch off and on: it goes back to the update utility by itself. Install Clavia's 3.03b (section 4). |
| *Update utility / Curr ver 255.255* at a normal power-on | The flash holds no OS (an update that failed halfway). | Install an OS: yours again, or Clavia's 3.03b. |
| It shows its name and version and stays there | The OS installed but does not start. | Shift + Store at power-on and install Clavia's 3.03b. Report it (below). |
| No *Update utility* with Shift + Store | The keys were not held from the start. | Hold both before switching on, until the display changes. |

The update utility lives in the G1's ROM chip, which nothing here can write. Whatever the flash
holds, Shift + Store at power-on reaches it. **Shift + Patch/Load** at power-on starts the ROM's
factory OS, never the one in the flash: a way to use the synth while you sort it out.

## Reporting a problem

Open an issue with: the list of modules in the build, whether it was G1-Emu or a real G1, what
the display showed, and what you did just before. There is no support for real hardware and no
promise of a fix (README, "Who is responsible for what"), but every report helps.
