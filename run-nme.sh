#!/bin/sh
# NME from its g1-mods branch (built in ../Nomad2026/build-g1mods), which knows the new types.
# Build it with:
#   cd ../Nomad2026 && git switch g1-mods && cmake -B build-g1mods -DCMAKE_BUILD_TYPE=Release \
#     && cmake --build build-g1mods -j$(nproc) && git switch -
cd "$(dirname "$0")"
bin=../Nomad2026/build-g1mods/AnimatekNME_artefacts/Release/AnimatekNME
[ -x "$bin" ] || { echo "build NME's g1-mods branch first (see this script)"; exit 1; }
exec "$bin" "$@"
