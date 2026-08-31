"""Genera el SVG animado del tagline.

GitHub no ejecuta <script> en un README, pero si anima SVG servido por camo,
asi que el efecto se arma con animaciones CSS puras dentro del propio SVG.

El efecto es "constelacion", a proposito distinto del scramble mecanico:
cada letra empieza como un punto tenue, se enciende en orden disperso (no de
izquierda a derecha) y se desvanece suave, como estrellas apareciendo. Va con
la nebula del banner.

    python scripts/build_svg.py

Sin dependencias externas: corre en la Action con python puro.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

# (fondo, tinta, punto tenue)
THEMES = {
    "":       ("#0D1117", "#E6EDF3", "#7D8590"),
    "-light": ("#FFFFFF", "#1F2328", "#9AA1A9"),
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def constellation_svg(phrases: list[str], theme: str, width=620, size=15,
                      seed=29) -> str:
    """Cada letra se enciende y se apaga en su propio momento.

    Todas las animaciones duran el ciclo completo y se ubican con
    animation-delay; los tiempos se agrupan en buckets, asi que decenas de
    reglas alcanzan para cientos de glifos.
    """
    bg, ink, dim = THEMES[theme]
    rng = random.Random(seed)
    adv = size * 0.6                        # avance monoespaciado

    lead = 1.30                             # ventana en la que van naciendo
    hold_end = 3.10                         # cuando empiezan a apagarse
    out_span, fade = 0.70, 0.55
    slot = hold_end + out_span + fade + 0.30
    total = slot * len(phrases)
    height = int(size * 2.6)
    cy = height / 2
    buckets = 12

    css = [
        # opacity:0 de base es imprescindible: un elemento con
        # animation-delay positivo se dibuja con su estilo base mientras
        # espera, y sin esto las frases siguientes se ven encima de la actual
        f".c{{font:{size}px {MONO};fill:{ink};text-anchor:middle;"
        f"dominant-baseline:middle;opacity:0}}",
        f".d{{fill:{dim}}}",
    ]

    def pct(t: float) -> float:
        return t / total * 100

    body = []
    for p, text in enumerate(phrases):
        t0 = p * slot
        chars = list(text)
        x0 = width / 2 - (len(chars) - 1) * adv / 2
        # el orden de encendido se baraja: asi no se lee como una barrida
        order = [i for i, c in enumerate(chars) if c != " "]
        rng.shuffle(order)
        seen = set()

        for rank, i in enumerate(order):
            x = x0 + i * adv
            bi = int(rank / max(1, len(order) - 1) * (buckets - 1))
            bo = rng.randrange(buckets)
            born = lead * (bi + 0.5) / buckets
            gone = hold_end + out_span * (bo + 0.5) / buckets

            key = f"k{p}_{bi}_{bo}"
            if key not in seen:
                seen.add(key)
                a, b = pct(t0 + born), pct(t0 + born + 0.42)
                c, d = pct(t0 + gone), pct(t0 + gone + fade)
                css.append(
                    f"@keyframes {key}{{0%,{a:.3f}%{{opacity:0}}"
                    f"{b:.3f}%,{c:.3f}%{{opacity:1}}"
                    f"{d:.3f}%,100%{{opacity:0}}}}")
                # el punto tenue vive justo antes de que nazca la letra
                dk = f"p{p}_{bi}"
                if dk not in seen:
                    seen.add(dk)
                    e, f = pct(t0 + max(0.0, born - 0.45)), pct(t0 + born)
                    css.append(
                        f"@keyframes {dk}{{0%,{e:.3f}%{{opacity:0}}"
                        f"{e + 0.05:.3f}%{{opacity:.55}}"
                        f"{f:.3f}%,100%{{opacity:0}}}}")

            body.append(
                f'<text class="c d" x="{x:.1f}" y="{cy:.1f}" '
                f'style="animation:p{p}_{bi} {total:.2f}s ease-in-out infinite">'
                f'·</text>')
            body.append(
                f'<text class="c" x="{x:.1f}" y="{cy:.1f}" '
                f'style="animation:{key} {total:.2f}s ease-in-out infinite">'
                f'{esc(chars[i])}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{esc(" · ".join(phrases))}">'
            f'<style>{"".join(dict.fromkeys(css))}</style>'
            f'<rect width="100%" height="100%" fill="{bg}"/>'
            f'{"".join(body)}</svg>')


if __name__ == "__main__":
    profile = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        p = OUT / f"constelacion{theme}.svg"
        p.write_text(constellation_svg(profile["tagline_lines"], theme),
                     encoding="utf-8")
        print(f"  {p.name}  {p.stat().st_size // 1024} KB")
