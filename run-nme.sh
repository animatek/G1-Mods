#!/bin/sh
# NME from its mods-layer branch (built in ../Nomad2026/build-g1mods). In MIDI Setup, tick
# "OS with G1-Mods modules" on G1-Emu's port, so its slots take the new types.
# Build it with:
#   cd ../Nomad2026 && git switch mods-layer && cmake -B build-g1mods -DCMAKE_BUILD_TYPE=Release \
#     && cmake --build build-g1mods -j$(nproc) && git switch -
cd "$(dirname "$0")"
bin=../Nomad2026/build-g1mods/AnimatekNME_artefacts/Release/AnimatekNME
[ -x "$bin" ] || { echo "build NME's mods-layer branch first (see this script)"; exit 1; }
exec "$bin" "$@"
