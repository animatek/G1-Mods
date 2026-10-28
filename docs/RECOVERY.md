# Going back & fixes

The update utility lives in the G1's ROM chip, which nothing here can write. Whatever the flash
holds, **Shift + Store** at power-on reaches it.

## Back to Clavia's OS

1. Delete or overwrite the stored patches that use new modules (see the install guide).
2. Switch the G1 off. **Hold Shift + Store and switch it on.**
3. Run **Clavia's 3.03b updater**, at its safe (slower) speed, through the same MIDI interface.
4. Press **Store** at "Update flash?", wait for *Update completed*, switch it off and on.

**Shift + Patch/Load** at power-on starts the ROM's factory OS, never the one in the flash: a way
to use the synth while you sort it out.

## If something goes wrong

| What you see | What it means | What to do |
| --- | --- | --- |
| *Writing to flash / Write Error* | The flash could not be written. | Switch off and on: it goes back to the update utility by itself. Install Clavia's 3.03b (below). |
| *Update utility / Curr ver 255.255* at a normal power-on | The flash holds no OS (an update that failed halfway). | Install an OS: yours again, or Clavia's 3.03b. |
| It shows its name and version and stays there | The OS installed but does not start. | Shift + Store at power-on and install Clavia's 3.03b. Report it (below). |
| No *Update utility* with Shift + Store | The keys were not held from the start. | Hold both before switching on, until the display changes. |

## Reporting a problem

Open an [issue](https://github.com/animatek/G1-Mods/issues) with: the list of modules in the
build, whether it was G1-Emu or a real G1, what the display showed, and what you did just before.
There is no support for real hardware and no promise of a fix (README, "Who is responsible for
what"), but every report helps.
