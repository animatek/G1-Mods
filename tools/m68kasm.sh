#!/usr/bin/env bash
# Assembles a module's 68k source for the G1's CPU32 (the 68331) into raw bytes, with GNU as in
# Digitakt-Mods' Docker image (digitakt-cross: there is no m68k toolchain packaged for Arch).
#
#   tools/m68kasm.sh source.s output.bin [--defsym NAME=VALUE ...]
#
# The output is what the build puts into the package, so the code must be position independent
# (its own data pc-relative, the OS's by absolute address). Only needed when the source changes:
# the module keeps the assembled bytes next to it, and its check says when they are stale.
set -euo pipefail
src=$(realpath "$1"); out=$(realpath -m "$2"); shift 2
dir=$(dirname "$src")
[[ $(dirname "$out") == "$dir" ]] || { echo "the output goes next to the source" >&2; exit 1; }
docker run --rm -u "$(id -u):$(id -g)" -v "$dir":/w -w /w digitakt-cross sh -c \
  "m68k-linux-gnu-as -mcpu=cpu32 $* -o /tmp/m.o $(basename "$src") &&
   m68k-linux-gnu-objcopy -O binary -j .text /tmp/m.o $(basename "$out")"
