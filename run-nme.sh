#!/bin/sh
# NME with the G1-Mods layer (Nomad2026's local branch mods-layer-2): it offers the new types to a
# synth whose OS says 3.09 on connecting, and has Device > Update Synth OS to install an OS.
# The binary lives outside both repos, in ~/.local/share/Animatek/G1-Mods/, until the layer goes
# into NME's main. To rebuild it:
#   cd ../Nomad2026 && git worktree add ../nme-mods mods-layer-2 && cd ../nme-mods \
#     && cmake -B build-release -DCMAKE_BUILD_TYPE=Release && cmake --build build-release -j$(nproc) \
#     && cp build-release/AnimatekNME_artefacts/Release/AnimatekNME ~/.local/share/Animatek/G1-Mods/
cd "$(dirname "$0")"
bin=$HOME/.local/share/Animatek/G1-Mods/AnimatekNME
[ -x "$bin" ] || { echo "no NME with the G1-Mods layer at $bin (see this script)"; exit 1; }
exec "$bin" "$@"
