import struct, zlib

def render(N):
    S = N * 2
    px = [[(0, 0, 0)] * S for _ in range(S)]
    cell = max(2, S // 170)
    for y in range(S):
        t = y / S
        base = (30 - 20 * t, 30 - 20 * t, 42 - 28 * t)
        for x in range(S):
            d = 3 if ((x // cell + y // cell) % 2) else -2
            px[y][x] = (base[0] + d, base[1] + d, base[2] + d)

    def inside(poly, x, y):
        c = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]; xj, yj = poly[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c

    def fill(poly, colfn, alpha=1.0, dx=0.0, dy=0.0):
        pts = [((x + dx) * S, (y + dy) * S) for x, y in poly]
        x0 = max(0, int(min(p[0] for p in pts))); x1 = min(S - 1, int(max(p[0] for p in pts)) + 1)
        y0 = max(0, int(min(p[1] for p in pts))); y1 = min(S - 1, int(max(p[1] for p in pts)) + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if inside(pts, x + .5, y + .5):
                    c = colfn(x / S, y / S)
                    o = px[y][x]
                    px[y][x] = tuple(o[k] * (1 - alpha) + c[k] * alpha for k in range(3))

    red = lambda x, y: (235 - 70 * x, 8 + 4 * x, 0)
    fill([(0, .84), (1, .64), (1, .72), (0, .92)], red)
    fill([(0, .78), (1, .58), (1, .60), (0, .80)], lambda x, y: (255, 90, 70), .55)
    fill([(0, .96), (1, .76), (1, .78), (0, .98)], lambda x, y: (255, 90, 70), .30)

    k = .20
    sk = lambda x, y: (x + (.5 - y) * k, y)
    R = lambda x0, y0, x1, y1: [sk(x0, y0), sk(x1, y0), sk(x1, y1), sk(x0, y1)]
    letras = [
        R(.20, .22, .29, .62), R(.20, .22, .52, .31), R(.20, .38, .46, .46),
        [sk(.62, .22), sk(.74, .22), sk(.74, .62), sk(.65, .62), sk(.65, .32), sk(.55, .32), sk(.55, .27)],
    ]
    branco = lambda x, y: (255 - 60 * max(0, min(1, (y - .22) / .4)),) * 3
    for dx, dy, col, a in ((.020, .026, (0, 0, 0), .55), (.012, .015, (0, 0, 0), .45), (.007, .009, (120, 122, 135), 1.0)):
        for p in letras:
            fill(p, lambda x, y, col=col: col, a, dx, dy)
    for p in letras:
        fill(p, branco)

    out = bytearray()
    for y in range(N):
        out.append(0)
        for x in range(N):
            for k2 in range(3):
                v = (px[2*y][2*x][k2] + px[2*y][2*x+1][k2] + px[2*y+1][2*x][k2] + px[2*y+1][2*x+1][k2]) / 4
                out.append(max(0, min(255, int(v))))
    return bytes(out)

def salvar(N, nome):
    raw = render(N)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", N, N, 8, 2, 0, 0, 0)
    open(nome, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    print("ok:", nome)

for n in (180, 192, 512):
    salvar(n, "icone-%d.png" % n)
