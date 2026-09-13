#!/usr/bin/env python3
"""Gera os icones PNG da extensao (quadrado arredondado + seta de download).

Uso: python3 tools/make_icons.py
Sem dependencias externas: rasteriza com supersampling e escreve o PNG na mao.
"""

import struct
import zlib
from pathlib import Path

BG = (232, 84, 47)      # laranja
FG = (255, 255, 255)    # seta
SS = 4                  # fator de supersampling
SIZES = (16, 48, 128)
OUT_DIR = Path(__file__).resolve().parent.parent / "icons"


def inside_rounded_rect(x, y, size, radius):
    if x < 0 or y < 0 or x > size or y > size:
        return False
    cx = min(max(x, radius), size - radius)
    cy = min(max(y, radius), size - radius)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= radius * radius


def inside_rect(x, y, x0, y0, x1, y1):
    return x0 <= x <= x1 and y0 <= y <= y1


def inside_triangle(x, y, apex, half_width, top):
    # Triangulo isosceles apontando para baixo, vertice em `apex` (x_center, y).
    cx, ay = apex
    if y < top or y > ay:
        return False
    t = (y - top) / (ay - top)
    span = half_width * (1 - t)
    return abs(x - cx) <= span


def pixels(size):
    """Devolve linhas RGBA do icone com o tamanho pedido."""
    n = size * SS
    radius = n * 0.22
    cx = n / 2

    stem = (cx - n * 0.075, n * 0.20, cx + n * 0.075, n * 0.52)
    tri_top = n * 0.44
    tri_apex = (cx, n * 0.70)
    tri_half = n * 0.20
    base = (cx - n * 0.24, n * 0.76, cx + n * 0.24, n * 0.845)

    rows = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            bg_hits = 0
            fg_hits = 0
            for sy in range(SS):
                y = py * SS + sy + 0.5
                for sx in range(SS):
                    x = px * SS + sx + 0.5
                    if not inside_rounded_rect(x, y, n, radius):
                        continue
                    bg_hits += 1
                    if (
                        inside_rect(x, y, *stem)
                        or inside_triangle(x, y, tri_apex, tri_half, tri_top)
                        or inside_rect(x, y, *base)
                    ):
                        fg_hits += 1
            total = SS * SS
            if bg_hits == 0:
                row += bytes((0, 0, 0, 0))
                continue
            alpha = round(255 * bg_hits / total)
            mix = fg_hits / bg_hits
            color = tuple(round(BG[i] + (FG[i] - BG[i]) * mix) for i in range(3))
            row += bytes((*color, alpha))
        rows.append(bytes(row))
    return rows


def write_png(path, rows, size):
    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        target = OUT_DIR / f"icon{size}.png"
        write_png(target, pixels(size), size)
        print(f"gerado {target.relative_to(OUT_DIR.parent)} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
