"""Genera tarjetas 1080x1350 de Sylred Computers para Instagram/TikTok.

Uso:
  python3 generar_tarjeta.py "ETIQUETA" "Título" "Tecla o comando" "Paso 1" "Paso 2" "Paso 3" salida.jpg

La ETIQUETA decide el color y el estilo del elemento destacado:
  CIBERSEGURIDAD  -> rojo/violeta, insignia con candado
  TRUCO WINDOWS   -> azul, teclas 3D (separa las teclas con "+")
  TRUCO LINUX     -> verde, ventana de terminal
  NUEVO EN EL BLOG (o cualquier etiqueta con "BLOG") -> morado/rosa, botón a la web
Variable de entorno TEMA=claro para el estilo claro (por defecto: degradado).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
M = 80  # margen lateral
DIR = os.path.dirname(os.path.abspath(__file__))


def _font(name, size, fallbacks):
    for p in [os.path.join(DIR, "fuentes", name)] + fallbacks:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


GF = "/usr/share/fonts/truetype/google-fonts/"
DJ = "/usr/share/fonts/truetype/dejavu/"
bold = lambda s: _font("Poppins-Bold.ttf", s, [GF + "Poppins-Bold.ttf", DJ + "DejaVuSans-Bold.ttf"])
medium = lambda s: _font("Poppins-Medium.ttf", s, [GF + "Poppins-Medium.ttf", DJ + "DejaVuSans.ttf"])
mono = lambda s: _font("DejaVuSansMono-Bold.ttf", s, [DJ + "DejaVuSansMono-Bold.ttf"])
sym_b = lambda s: _font("DejaVuSans-Bold.ttf", s, [DJ + "DejaVuSans-Bold.ttf"])
sym_r = lambda s: _font("DejaVuSans.ttf", s, [DJ + "DejaVuSans.ttf"])

# Colores por categoría: (degradado inicio, degradado fin, acento)
TEMAS = {
    "seguridad": ((255, 61, 87), (124, 58, 237), (225, 29, 72)),
    "windows": ((0, 99, 255), (0, 200, 255), (0, 110, 240)),
    "linux": ((0, 168, 120), (132, 204, 22), (5, 150, 105)),
    "blog": ((124, 58, 237), (236, 72, 153), (168, 50, 200)),
}
DARK = (17, 24, 39)
GREY = (100, 110, 125)
WHITE = (255, 255, 255)


def categoria(tag):
    t = tag.upper()
    if "BLOG" in t:
        return "blog"
    if "WINDOWS" in t:
        return "windows"
    if "LINUX" in t:
        return "linux"
    return "seguridad"


# ---------- texto con respaldo para flechas y símbolos ----------
def _needs_sym(ch):
    return ord(ch) > 0x24F and not ch.isspace()


def runs(text, font, symfont):
    out, cur, cur_f = [], "", None
    for ch in text:
        f = symfont if _needs_sym(ch) else font
        if f is not cur_f and cur:
            out.append((cur, cur_f))
            cur = ""
        cur_f = f
        cur += ch
    if cur:
        out.append((cur, cur_f))
    return out


def tlen(d, text, font, symfont):
    return sum(d.textlength(t, font=f) for t, f in runs(text, font, symfont))


def text(d, xy, s, font, symfont, fill):
    x, y = xy
    asc = font.getmetrics()[0]
    for t, f in runs(s, font, symfont):
        dy = asc - f.getmetrics()[0] if f is not font else 0
        d.text((x, y + dy), t, font=f, fill=fill)
        x += d.textlength(t, font=f)


def wrap(d, s, font, symfont, maxw):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if tlen(d, t, font, symfont) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------- utilidades gráficas ----------
def gradient(c1, c2):
    x = np.linspace(0, 1, W)[None, :]
    y = np.linspace(0, 1, H)[:, None]
    t = np.clip(x * 0.45 + y * 0.55, 0, 1)[..., None]
    arr = np.array(c1) * (1 - t) + np.array(c2) * t
    return Image.fromarray(arr.astype("uint8"), "RGB")


def shadow(im, box, radius, offset=(0, 14), blur=22, alpha=90):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(
        [box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1]],
        radius=radius, fill=(0, 0, 0, alpha))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))


def deco_circles(im, color, alpha):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = color + (alpha,)
    d.ellipse([W - 330, -170, W + 170, 330], fill=c)
    d.ellipse([-220, H - 470, 200, H - 50], fill=c)
    d.ellipse([W - 170, 560, W + 50, 780], outline=color + (alpha + 30,), width=10)
    for i in range(5):
        for j in range(3):
            d.ellipse([W - 250 + i * 26, 92 + j * 26, W - 242 + i * 26, 100 + j * 26],
                      fill=color + (alpha + 40,))
    im.alpha_composite(lay)


# ---------- iconos sencillos (dibujados, genéricos) ----------
def icon(d, cat, x, y, s, col, inner=WHITE):
    if cat == "seguridad":  # escudo con candado
        d.polygon([(x + s * .5, y), (x + s, y + s * .18), (x + s * .92, y + s * .62),
                   (x + s * .5, y + s), (x + s * .08, y + s * .62), (x, y + s * .18)], fill=col)
        d.rounded_rectangle([x + s * .33, y + s * .45, x + s * .67, y + s * .72], radius=3, fill=inner)
        d.arc([x + s * .38, y + s * .28, x + s * .62, y + s * .56], 180, 360, fill=inner, width=max(2, int(s * .07)))
    elif cat == "windows":  # ventana genérica
        d.rounded_rectangle([x, y + s * .1, x + s, y + s * .9], radius=s * .12, fill=col)
        d.rectangle([x + s * .1, y + s * .34, x + s * .9, y + s * .8], fill=inner)
        for k in range(3):
            d.ellipse([x + s * (.12 + k * .13), y + s * .17, x + s * (.2 + k * .13), y + s * .25], fill=inner)
    elif cat == "linux":  # terminal >_
        d.rounded_rectangle([x, y + s * .1, x + s, y + s * .9], radius=s * .12, fill=col)
        w = max(3, int(s * .09))
        d.line([(x + s * .2, y + s * .32), (x + s * .4, y + s * .5), (x + s * .2, y + s * .68)], fill=inner, width=w)
        d.line([(x + s * .5, y + s * .68), (x + s * .8, y + s * .68)], fill=inner, width=w)
    else:  # blog: hoja con líneas
        d.rounded_rectangle([x + s * .1, y, x + s * .9, y + s], radius=s * .12, fill=col)
        for k in range(4):
            ww = .62 if k < 3 else .4
            d.rounded_rectangle([x + s * .24, y + s * (.2 + k * .17), x + s * (.24 + ww * .85), y + s * (.28 + k * .17)],
                                radius=3, fill=inner)


# ---------- elementos destacados ----------
def keycaps(im, d, key, y, light, acc):
    keys = [k.strip() for k in key.split("+") if k.strip()] or [key]
    f, sf = bold(66), sym_b(66)
    plus = bold(60)
    h, pad, gap = 150, 44, 22
    widths = [max(h, tlen(d, k, f, sf) + pad * 2) for k in keys]
    pw = d.textlength("+", font=plus)
    total = sum(widths) + (len(keys) - 1) * (pw + gap * 2)
    scale = min(1, (W - 2 * M) / total)
    if scale < 1:  # demasiado ancho: reduce
        f, sf, plus = bold(int(66 * scale)), sym_b(int(66 * scale)), bold(int(60 * scale))
        widths = [max(h * scale, tlen(d, k, f, sf) + pad * 2 * scale) for k in keys]
        pw = d.textlength("+", font=plus)
    x = M
    for i, (k, w) in enumerate(zip(keys, widths)):
        box = [x, y, x + w, y + h]
        shadow(im, box, 28, offset=(0, 16), blur=18, alpha=70)
        d.rounded_rectangle([x, y + 14, x + w, y + h], radius=28, fill=(205, 212, 225) if not light else acc)
        d.rounded_rectangle([x, y, x + w, y + h - 14], radius=28, fill=WHITE if not light else DARK)
        tw = tlen(d, k, f, sf)
        text(d, (x + (w - tw) / 2, y + (h - 14) / 2 - f.getmetrics()[0] * .62), k, f, sf,
             DARK if not light else WHITE)
        x += w
        if i < len(keys) - 1:
            text(d, (x + gap, y + 26), "+", plus, plus, WHITE if not light else DARK)
            x += pw + gap * 2
    return y + h + 20


def terminal(im, d, key, y, light, acc):
    f = mono(70)
    w = min(W - 2 * M, max(560, d.textlength("$ " + key, font=f) + 120))
    box = [M, y, M + w, y + 190]
    shadow(im, box, 26, alpha=110)
    d.rounded_rectangle(box, radius=26, fill=(15, 23, 42))
    d.rounded_rectangle([M, y, M + w, y + 46], radius=26, fill=(30, 41, 59))
    d.rectangle([M, y + 26, M + w, y + 46], fill=(30, 41, 59))
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        d.ellipse([M + 24 + i * 34, y + 14, M + 44 + i * 34, y + 34], fill=c)
    d.text((M + 40, y + 78), "$", font=f, fill=(74, 222, 128))
    d.text((M + 40 + d.textlength("$ ", font=f), y + 78), key, font=f, fill=WHITE)
    cx = M + 40 + d.textlength("$ " + key, font=f) + 10
    d.rectangle([cx, y + 88, cx + 34, y + 156], fill=(74, 222, 128))
    return y + 190 + 20


def badge(im, d, key, y, light, acc, cat):
    f, sf = bold(72), sym_b(72)
    if cat == "blog":
        label = key if key.lower() != "blog" else "Léelo en el blog"
        f, sf = bold(54), sym_b(54)
    else:
        label = key
    tw = tlen(d, label, f, sf)
    ic = 96
    w = min(W - 2 * M, tw + ic + 130)
    box = [M, y, M + w, y + 170]
    shadow(im, box, 85, alpha=80)
    d.rounded_rectangle(box, radius=85, fill=WHITE if not light else DARK)
    icon(d, cat, M + 40, y + 37, ic, acc)
    text(d, (M + 40 + ic + 34, y + 85 - f.getmetrics()[0] * .62), label, f, sf, DARK if not light else WHITE)
    yy = y + 170 + 20
    if cat == "blog":
        fu = medium(36)
        text(d, (M + 8, yy + 6), "sylredcomputers.com  →", fu, sym_r(36), WHITE if not light else acc)
        yy += 60
    return yy


# ---------- tarjeta ----------
def card(tag, title, key, steps, out):
    cat = categoria(tag)
    c1, c2, acc = TEMAS[cat]
    light = os.environ.get("TEMA", "").lower() == "claro"

    if light:
        im = Image.new("RGB", (W, H), (255, 248, 238)).convert("RGBA")
        deco_circles(im, c1, 40)
        fg = DARK
    else:
        im = gradient(c1, c2).convert("RGBA")
        deco_circles(im, (255, 255, 255), 28)
        fg = WHITE
    d = ImageDraw.Draw(im)

    # etiqueta
    ft = bold(34)
    tw = d.textlength(tag, font=ft)
    pill = [M, 80, M + tw + 130, 150]
    d.rounded_rectangle(pill, radius=35, fill=WHITE if not light else acc)
    icon(d, cat, M + 22, 93, 44, acc if not light else WHITE, WHITE if not light else acc)
    d.text((M + 84, 92), tag, font=ft, fill=acc if not light else WHITE)

    # contenido central (título + destacado + pasos) en una capa aparte
    # para poder centrarlo verticalmente entre la etiqueta y el pie
    def build(tmax, fsz):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)

        # título (se reduce si ocupa más de 3 líneas)
        size = tmax
        while True:
            fti, sti = bold(size), sym_b(size)
            lines = wrap(d, title, fti, sti, W - 2 * M)
            if len(lines) <= 3 or size <= 60:
                break
            size -= 6
        y = 0
        lh = int(size * 1.18)
        for line in lines:
            text(d, (M, y), line, fti, sti, fg)
            y += lh
        if light:  # subrayado de acento
            d.rounded_rectangle([M, y + 6, M + 180, y + 22], radius=8, fill=acc)
        y += 50

        # elemento destacado
        if cat == "windows":
            y = keycaps(lay, d, key, y, light, acc)
        elif cat == "linux":
            y = terminal(lay, d, key, y, light, acc)
        else:
            y = badge(lay, d, key, y, light, acc, cat)
        d = ImageDraw.Draw(lay)

        # pasos en tarjeta blanca
        fs, ss = medium(fsz), sym_r(fsz)
        LH = int(fsz * 1.38)
        inner = W - 2 * M - 150
        blocks = [wrap(d, s, fs, ss, inner) for s in steps]
        ch = 52 + sum(len(b) * LH + 38 for b in blocks) + 14
        y += 24
        box = [M - 10, y, W - M + 10, y + ch]
        shadow(lay, box, 36, alpha=70)
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle(box, radius=36, fill=WHITE)
        yy = y + 52
        for i, b in enumerate(blocks, 1):
            d.ellipse([M + 30, yy - 2, M + 96, yy + 64], fill=acc)
            n = str(i)
            fn = bold(38)
            d.text((M + 63 - d.textlength(n, font=fn) / 2, yy + 6), n, font=fn, fill=WHITE)
            for j, line in enumerate(b):
                text(d, (M + 126, yy + j * LH), line, fs, ss, DARK)
            yy += len(b) * LH + 38
        content_h = y + ch + 30  # margen para la sombra
        return lay, content_h

    top, bottom = 195, H - 150
    tmax, fsz = 92, 42
    while True:
        lay, content_h = build(tmax, fsz)
        if content_h <= bottom - top or tmax <= 64:
            break
        tmax, fsz = tmax - 6, max(34, fsz - 2)

    off = top + max(0, (bottom - top - content_h) // 2)
    im.alpha_composite(lay, (0, int(off)))
    d = ImageDraw.Draw(im)

    # pie
    fb = bold(40)
    d.text((M, H - 105), "SYLRED", font=fb, fill=fg)
    d.text((M + d.textlength("SYLRED ", font=fb), H - 105), "COMPUTERS", font=fb,
           fill=fg if not light else acc)
    fg2 = medium(32)
    txt = "Guarda y comparte"
    tx = W - M - d.textlength(txt, font=fg2)
    # icono marcador
    bx = tx - 46
    d.polygon([(bx, H - 104), (bx + 28, H - 104), (bx + 28, H - 62), (bx + 14, H - 74), (bx, H - 62)],
              fill=fg if not light else acc)
    d.text((tx, H - 102), txt, font=fg2, fill=fg)

    im.convert("RGB").save(out, quality=93)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 5:
        sys.exit(__doc__)
    card(a[0], a[1], a[2], a[3:-1], a[-1])
    print(a[-1])
