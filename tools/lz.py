"""The package's packing: LZSS, as tools/unlz.s unpacks it at boot.

    pack(data) -> bytes        unpack(packed, length) -> bytes   (the same as unlz.s, for checks)

A flags byte, then eight items, its bits low first: 1 = a literal byte; 0 = a match of two bytes,
big endian, (distance - 1) << 4 | (length - 3): `length` bytes (3-18) copied from `distance`
(1-4096) back in what is already unpacked. A greedy search; the package is a few KB, so plain.
"""

MIN, MAX, WINDOW = 3, 18, 4096


def _longest(data, i, heads):
    best, at = 0, 0
    for j in reversed(heads.get(data[i:i + MIN], ())):
        if i - j > WINDOW:
            break
        n = 0
        while n < MAX and i + n < len(data) and data[j + n] == data[i + n]:
            n += 1
        if n > best:
            best, at = n, j
            if n == MAX:
                break
    return best, at


def pack(data):
    out, items, flags = bytearray(), bytearray(), 0
    heads = {}
    i = n = 0
    while i < len(data):
        length, at = _longest(data, i, heads) if i + MIN <= len(data) else (0, 0)
        step = length if length >= MIN else 1
        if length >= MIN:
            w = ((i - at - 1) << 4) | (length - MIN)
            items += bytes((w >> 8, w & 0xFF))
        else:
            flags |= 1 << n
            items.append(data[i])
        for k in range(i, i + step):
            heads.setdefault(bytes(data[k:k + MIN]), []).append(k)
        i += step
        n += 1
        if n == 8:
            out.append(flags)
            out += items
            items, flags, n = bytearray(), 0, 0
    if n:
        out.append(flags)
        out += items
    return bytes(out)


def unpack(packed, length):
    out, p = bytearray(), 0
    while len(out) < length:
        flags = packed[p]
        p += 1
        for bit in range(8):
            if len(out) >= length:
                break
            if flags >> bit & 1:
                out.append(packed[p])
                p += 1
            else:
                w = packed[p] << 8 | packed[p + 1]
                p += 2
                src = len(out) - (w >> 4) - 1
                for k in range((w & 15) + MIN):
                    out.append(out[src + k])
    return bytes(out)
