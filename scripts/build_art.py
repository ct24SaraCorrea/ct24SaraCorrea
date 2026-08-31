"""Convierte las imagenes de inspiracion a 1 bit para el README.

Todas pasan por el mismo pipeline: se aplanan los tonos casi-negros y
casi-blancos ANTES de ditherear, porque si no el dither lee los artefactos
del JPEG como textura y ensucia lo que deberia ser fondo plano. Se dejan a
resolucion nativa o en multiplos enteros, para no difuminar el grano.

    python scripts/build_art.py --src <carpeta-de-imagenes>

Se corre a mano cuando cambian las fuentes; no va en la Action.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

# (fondo, tinta) — el fondo oscuro es el lienzo de GitHub, para que la
# imagen no se vea como un rectangulo pegado sobre la pagina
THEMES = {"": ((0x0D, 0x11, 0x17), (0xFF, 0xFF, 0xFF)),
          "-light": ((0xFF, 0xFF, 0xFF), (0x0D, 0x11, 0x17))}

PIECES = {
    # la nebula de datos: se recorta la banda central, donde va la onda
    "nebula": dict(file="Gemini_Generated_Image_xy4wsxy4wsxy4wsx.png",
                   box=(0.00, 0.22, 1.00, 0.55), scale=2,
                   floor=26, ceil=232, cutoff=1, blur=0),
    # el templo bajo el planeta, como separador ancho
    "temple": dict(file="WhatsApp Image 2026-08-31 at 3.33.34 PM (2).jpeg",
                   box=(0.02, 0.02, 0.98, 0.98), scale=2,
                   floor=40, ceil=215, cutoff=2, blur=0),
    # el ojo binario: se desenfoca antes para que la forma sobreviva al
    # dither; sin eso los digitos lo convierten en ruido ilegible
    "eye": dict(file="WhatsApp Image 2026-08-31 at 3.33.34 PM (3).jpeg",
                box=(0.02, 0.02, 0.98, 0.98), scale=3,
                floor=40, ceil=215, cutoff=5, blur=2, pre=(240, 240)),
}


def render(path: Path, box, scale, floor, ceil, cutoff, blur, bg, fg,
           pre=None) -> Image.Image:
    im = Image.open(path).convert("L")
    w, h = im.size
    im = im.crop((int(box[0] * w), int(box[1] * h),
                  int(box[2] * w), int(box[3] * h)))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if pre:
        im = im.resize(pre, Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=cutoff)
    im = im.point(lambda v: 0 if v < floor else (255 if v > ceil else v))
    m = im.convert("1")                       # dithering Floyd-Steinberg
    m = m.resize((m.width * scale, m.height * scale), Image.NEAREST)

    out = Image.new("P", m.size)
    out.putpalette(list(bg) + list(fg) + [0] * (256 * 3 - 6))
    src, dst = m.load(), out.load()
    for y in range(m.height):
        for x in range(m.width):
            dst[x, y] = 1 if src[x, y] else 0
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--out", default=Path("assets"), type=Path)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    for suffix, (bg, fg) in THEMES.items():
        for name, cfg in PIECES.items():
            if a.only and name != a.only:
                continue
            cfg = dict(cfg)
            im = render(a.src / cfg.pop("file"), bg=bg, fg=fg, **cfg)
            p = a.out / f"{name}{suffix}.png"
            im.save(p, optimize=True)
            print(f"  {p.name:20} {im.size}  {p.stat().st_size // 1024} KB")
