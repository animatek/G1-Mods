#!/usr/bin/env python3
"""Builds the MIDI stream that installs an OS into a G1's flash, as Clavia's updater does.

    tools/g1update.py build OS.bin out.syx [--version 3.03]
    tools/g1update.py unpack capture.syx OS.bin       (a recorded update back into its OS image)
    tools/g1update.py fromrom Roms/rom-all.bin OS.bin  (the OS inside a ROM patch_rom.py built)

OS.bin is the image that runs from RAM at $100000 (385,024 bytes for the rack's 3.03b), as G1-Emu
keeps it (`os/received-...bin`) and as tools/patch_rom.py works on. Nothing of Clavia's is in this
file: the user brings the image. The format was read from the boot ROM's update utility and checked
against a capture of Clavia's updater (NOTES.md, "The update protocol"):

- Every message is F0 33 7F 06 <cmd> ... F7.
- 00 00 00: greeting. A G1 in its update utility answers F0 33 00 06 01 03 03 7F 01 08 01 F7 (the
  ROM's version, then 7F: update mode).
- 70: header. Address and length (5 bytes each, packed below) and the OS version (two bytes), then
  the sum of those 12 bytes & 7F.
- 71: data, 112 bytes a message. The last is sent full; the G1 takes only what the length still
  asks for, so its padding does not matter (Clavia's updater pads with leftovers of its buffer,
  this one with zeros: apart from that, the stream is byte for byte the updater's).
  No answer per message: the G1 takes them as they come, so they must be paced.
- 73: the sum of every data byte as sent (32 bits, packed). The G1 answers F0 33 00 06 7F F7 and
  asks "Update flash?": Store writes it, any other key keeps the old OS.

Packing: groups of 8 bytes, the first carrying the low bit of each of the next 7 (LSB first); each
data byte is (b << 1) | bit. The data are scrambled before packing: each byte goes through an XOR
with a key that starts at 17 and grows by 17, and its odd and even bits are swapped.
"""

import argparse
import sys

HEADER = bytes([0xF0, 0x33, 0x7F, 0x06])
FLASH_OS = 0x300020     # where the OS goes in the flash, after its 32-byte header
BLOCK = 112
ROM_OS = 0xC800             # the factory OS in the boot ROM, run from RAM at $100000
MAX_IMAGE = 0x70000 - 0x20 - 4  # the flash keeps the OS only up to $70000; the loader copies a long more


def pack(data):
    out = bytearray()
    for g in range(0, len(data), 7):
        chunk = data[g:g + 7]
        lo = 0
        for k, b in enumerate(chunk):
            lo |= (b & 1) << k
        out.append(lo)
        out += bytes(b >> 1 for b in chunk)
    return bytes(out)


def unpack(packed, count):
    out = bytearray()
    j = 0
    while len(out) < count:
        lo = packed[j]
        j += 1
        for _ in range(7):
            if len(out) >= count:
                break
            out.append(((packed[j] << 1) | (lo & 1)) & 0xFF)
            lo >>= 1
            j += 1
    return bytes(out)


def swap_bits(x):
    return ((x & 0x55) << 1) | ((x & 0xAA) >> 1)


def scramble(image):
    out = bytearray(len(image))
    key = 17
    for i, x in enumerate(image):
        out[i] = swap_bits(x) ^ key
        key = (key + 17) & 0xFF
    return bytes(out)


def unscramble(data):
    out = bytearray(len(data))
    key = 17
    for i, x in enumerate(data):
        out[i] = swap_bits(x ^ key)
        key = (key + 17) & 0xFF
    return bytes(out)


def message(cmd, body=b""):
    return HEADER + bytes([cmd]) + body + b"\xF7"


def build(image, version=(3, 3)):
    """The whole update as a list of messages, greeting first."""
    data = scramble(image)
    head = pack(FLASH_OS.to_bytes(4, "big")) + pack(len(data).to_bytes(4, "big")) + bytes(version)
    msgs = [message(0x00, b"\x00\x00"), message(0x70, head + bytes([sum(head) & 0x7F]))]
    for i in range(0, len(data), BLOCK):
        block = data[i:i + BLOCK]
        msgs.append(message(0x71, pack(block.ljust(BLOCK, b"\x00"))))
    msgs.append(message(0x73, pack((sum(data) & 0xFFFFFFFF).to_bytes(4, "big"))))
    return msgs


def split(stream):
    msgs, i = [], 0
    while (s := stream.find(0xF0, i)) >= 0:
        e = stream.find(0xF7, s)
        msgs.append(stream[s:e + 1])
        i = e + 1
    return msgs


def from_capture(stream):
    msgs = split(stream)
    head = next(m for m in msgs if m[4] == 0x70)
    length = int.from_bytes(unpack(head[10:15], 4), "big")
    data, left = bytearray(), length
    for m in msgs:
        if m[4] == 0x71:
            n = min(BLOCK, left)
            data += unpack(m[5:-1], n)
            left -= n
    tail = next(m for m in msgs if m[4] == 0x73)
    if int.from_bytes(unpack(tail[5:10], 4), "big") != sum(data) & 0xFFFFFFFF:
        sys.exit("the capture's checksum does not match its data")
    return unscramble(bytes(data))


def from_rom(rom):
    """The factory OS a ROM carries, as an update image: patch_rom.py's modules included.

    G1-Emu boots the ROM's OS as the whole rest of the ROM (0x73800 bytes), more than a flash
    holds; past MAX_IMAGE it is all $FF in the rack's 3.03 ROM and in every build of ours, so it
    is cut there and the loader sees the same $FF it would in a flash."""
    if len(rom) != 0x80000:
        sys.exit("not a 512 KB G1 ROM")
    image = rom[ROM_OS:ROM_OS + MAX_IMAGE]
    if any(b != 0xFF for b in rom[ROM_OS + MAX_IMAGE:]):
        sys.exit("this ROM's OS goes past what a flash holds ($16FFE0): it cannot be installed")
    if image[:4] != bytes([0x46, 0xFC, 0x27, 0x00]):
        sys.exit("no G1 OS at $C800")
    return image


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("os")
    b.add_argument("out")
    b.add_argument("--version", default="3.03", help="major.minor the G1 shows (default 3.03)")
    u = sub.add_parser("unpack")
    u.add_argument("capture")
    u.add_argument("os")
    r = sub.add_parser("fromrom")
    r.add_argument("rom")
    r.add_argument("os")
    a = ap.parse_args()
    if a.cmd == "build":
        major, minor = a.version.split(".")
        msgs = build(open(a.os, "rb").read(), (int(major), int(minor)))
        open(a.out, "wb").write(b"".join(msgs))
        print(f"{a.out}: {len(msgs)} messages")
    elif a.cmd == "fromrom":
        image = from_rom(open(a.rom, "rb").read())
        open(a.os, "wb").write(image)
        print(f"{a.os}: {len(image)} bytes")
    else:
        image = from_capture(open(a.capture, "rb").read())
        open(a.os, "wb").write(image)
        print(f"{a.os}: {len(image)} bytes")


if __name__ == "__main__":
    main()
