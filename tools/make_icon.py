"""Generate the sadrobot wifiscan app icon (PNG, pure stdlib): pale-blue rounded tile, steel-blue "sr" mark, soft signal rings.
Usage: python3 tools/make_icon.py assets/icon_1024.png [size]"""
import math, struct, sys, zlib

BG1 = (245, 249, 253); BG2 = (215, 232, 247); BRAND = (47, 100, 151); RING = (191, 220, 245); INK = (27, 39, 51)
FONT = {  # 5x7
    "s": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
}


def lerp(a, b, t):
    t = max(0, min(1, t)); return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make(size=1024):
    px = bytearray(size * size * 4)
    def put(x, y, c, a=255):
        if 0 <= x < size and 0 <= y < size:
            i = (y * size + x) * 4; px[i:i + 4] = bytes((c[0], c[1], c[2], a))
    m = int(size * 0.10); r = int(size * 0.22); x0, y0, x1, y1 = m, m, size - m, size - m
    def inside(x, y):
        if x < x0 or x >= x1 or y < y0 or y >= y1: return False
        cx = x0 + r if x < x0 + r else (x1 - 1 - r if x >= x1 - r else x)
        cy = y0 + r if y < y0 + r else (y1 - 1 - r if y >= y1 - r else y)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    ccx, ccy = int(size * 0.72), int(size * 0.30)          # signal rings origin (top-right)
    for y in range(size):
        for x in range(size):
            if not inside(x, y): continue
            c = lerp(BG1, BG2, (x + y) / (2 * size))
            d = math.hypot(x - ccx, y - ccy) / size
            for k in (0.16, 0.26, 0.36):
                if abs(d - k) < 0.018:
                    c = lerp(c, RING, 0.9)
            put(x, y, c)
    # "sr" mark
    cell = int(size * 0.062); gap = cell
    total_w = 2 * 5 * cell + gap; ox = (size - total_w) // 2; oy = int(size * 0.40)
    for gi, ch in enumerate("sr"):
        for gy, row in enumerate(FONT[ch]):
            for gx, bit in enumerate(row):
                if bit != "1": continue
                bx = ox + gi * (5 * cell + gap) + gx * cell; by = oy + gy * cell
                for dy in range(cell):
                    for dx in range(cell):
                        put(bx + dx, by + dy, BRAND)
    # soften mark corners slightly: no-op for pixel art look
    return png(size, size, px)


def png(w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/icon_1024.png"
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    open(out, "wb").write(make(size)); print("wrote", out)
