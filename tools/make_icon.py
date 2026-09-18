"""Generate the wifiscan app icon (PNG, pure stdlib) – Hackerman synthwave: chrome "H" on purple, laser grid, sunset.
Usage: python3 tools/make_icon.py assets/icon_1024.png [size]"""
import math, struct, sys, zlib

BG = (11, 4, 24); PINK = (255, 43, 214); CYAN = (25, 240, 255); SUN1 = (255, 209, 102); SUN2 = (255, 122, 89)
CHROME1 = (246, 249, 255); CHROME2 = (143, 180, 217); CHROME3 = (44, 74, 120)

FONT_H = ["10001", "10001", "10001", "11111", "10001", "10001", "10001"]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make(size=1024):
    px = bytearray(size * size * 4)

    def put(x, y, c, a=255):
        if 0 <= x < size and 0 <= y < size:
            i = (y * size + x) * 4
            px[i:i + 4] = bytes((c[0], c[1], c[2], a))

    m = int(size * 0.10); r = int(size * 0.185)
    x0, y0, x1, y1 = m, m, size - m, size - m

    def inside(x, y):
        if x < x0 or x >= x1 or y < y0 or y >= y1:
            return False
        cx = x0 + r if x < x0 + r else (x1 - 1 - r if x >= x1 - r else x)
        cy = y0 + r if y < y0 + r else (y1 - 1 - r if y >= y1 - r else y)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r

    horizon = int(size * 0.62); sun_cx, sun_cy, sun_r = size // 2, int(size * 0.58), int(size * 0.24)
    for y in range(size):
        for x in range(size):
            if not inside(x, y):
                continue
            t = (y - y0) / (y1 - y0)
            c = lerp((58, 26, 110), BG, min(1, t * 1.4))
            # sunset (striped)
            d = math.hypot(x - sun_cx, y - sun_cy)
            if d < sun_r and y < horizon:
                stripe = ((y - sun_cy + sun_r) // (size // 40)) % 3
                if stripe != 2 or y < sun_cy - sun_r * 0.2:
                    c = lerp(SUN1, PINK, (y - (sun_cy - sun_r)) / (2 * sun_r))
            # laser grid below horizon
            if y >= horizon:
                depth = (y - horizon) / (y1 - horizon)
                gap = 1 + depth * 6
                gx = (x - size / 2) / gap
                if int(abs(gx)) % (size // 14) < 3 or (y - horizon) % max(3, int(size / 40 * (0.3 + depth * 1.5))) < 3:
                    c = lerp(PINK, c, 0.25 + depth * 0.2)
            # scanlines
            if y % 4 == 0:
                c = lerp(c, (0, 0, 0), 0.22)
            put(x, y, c)
    # chrome "H" with pink glow
    cell = int(size * 0.075); gw, gh = 5 * cell, 7 * cell
    ox, oy = (size - gw) // 2, int(size * 0.20)
    for gy, row in enumerate(FONT_H):
        for gx, bit in enumerate(row):
            if bit != "1":
                continue
            for dy in range(cell):
                for dx in range(cell):
                    x, y = ox + gx * cell + dx, oy + gy * cell + dy
                    # glow border
                    for g in range(1, int(size * 0.012)):
                        for (ex, ey) in ((x + g, y), (x - g, y), (x, y + g), (x, y - g)):
                            if inside(ex, ey) and (ex, ey) not in ():
                                i = (ey * size + ex) * 4
                                if px[i:i + 3] != bytes(CHROME1) and px[i:i + 3] != bytes(CHROME3):
                                    put(ex, ey, lerp(PINK, tuple(px[i:i + 3]), 0.55))
            for dy in range(cell):
                for dx in range(cell):
                    x, y = ox + gx * cell + dx, oy + gy * cell + dy
                    t = (y - oy) / gh
                    c = lerp(CHROME1, CHROME1, 0) if t < 0.38 else (lerp(CHROME3, CHROME2, (t - 0.5) / 0.12) if 0.5 <= t < 0.62 else (CHROME3 if t < 0.5 else lerp(CHROME2, CHROME1, (t - 0.62) / 0.38)))
                    put(x, y, c)
    # thin cyan frame
    for y in range(size):
        for x in range(size):
            if inside(x, y) and not (inside(x - 6, y) and inside(x + 6, y) and inside(x, y - 6) and inside(x, y + 6)):
                put(x, y, CYAN)
    return png(size, size, px)


def png(w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/icon_1024.png"
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    open(out, "wb").write(make(size)); print("wrote", out)
