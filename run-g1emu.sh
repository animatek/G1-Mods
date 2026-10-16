#!/bin/sh
# G1-Emu with the G1-Mods test OS, in a window. Close your usual G1-Emu first: both take the
# same MIDI ports.
#   ./run-g1emu.sh [experiment]     (default: all, every new type; tools/patch_rom.py --list)
#
# - The ROM is built from G1-Emu's own (Roms/ there) into out/, never into Git.
# - Its own flash, out/flash-<experiment>.bin: your usual flash.bin is not touched.
# - G1_OS= (empty) overrides the settings' "os =": with an OS image there, the emulator would
#   boot Clavia's update instead of the modified OS in the ROM, and the new types would not exist.
cd "$(dirname "$0")"
exp=${1:-all}
emu=../G1-Emu
rom=out/rom-$exp.bin
python3 -I tools/patch_rom.py "$exp" "$emu/Roms/NORD-MODULAR-RACK-VER-3.03.BIN" "$rom" || exit 1
bin=$emu/build/app/gui/g1gui_artefacts/Release/G1-Emu
[ -x "$bin" ] || { echo "build G1-Emu first ($bin)"; exit 1; }
G1_OS= exec "$bin" "$rom" "$PWD/out/flash-$exp.bin" 2>/dev/null
