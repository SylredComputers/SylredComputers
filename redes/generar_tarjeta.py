"""Genera tarjetas 1080x1350 de Sylred Computers para Instagram/TikTok.

Uso:
  python3 generar_tarjeta.py "ETIQUETA" "Título" "Tecla o comando" "Paso 1" "Paso 2" "Paso 3" salida.jpg
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG = (15, 20, 32)
PANEL = (26, 33, 50)
RED = (220, 38, 48)
WHITE = (245, 247, 250)
GREY = (160, 170, 190)

F = "/usr/share/fonts/truetype/dejavu/"
bold = lambda s: ImageFont.truetype(F + "DejaVuSans-Bold.ttf", s)
reg = lambda s: ImageFont.truetype(F + "DejaVuSans.ttf", s)
mono = lambda s: ImageFont.truetype(F + "DejaVuSansMono-Bold.ttf", s)


def wrap(draw, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def card(tag, title, key, steps, out):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # barra superior
    d.rectangle([0, 0, W, 14], fill=RED)
    # etiqueta
    f = bold(34)
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle([80, 90, 80 + tw + 56, 150], radius=30, fill=RED)
    d.text((108, 101), tag, font=f, fill=WHITE)
    # título
    y = 210
    ft = bold(78)
    for line in wrap(d, title, ft, W - 160):
        d.text((80, y), line, font=ft, fill=WHITE)
        y += 96
    # tecla / comando destacado
    y += 40
    fk = mono(96)
    kw = d.textlength(key, font=fk)
    d.rounded_rectangle([80, y, 80 + kw + 80, y + 160], radius=24, fill=PANEL, outline=RED, width=5)
    d.text((120, y + 26), key, font=fk, fill=WHITE)
    y += 230
    # pasos
    fs = reg(44)
    for i, s in enumerate(steps, 1):
        d.ellipse([80, y + 2, 136, y + 58], fill=RED)
        n = str(i)
        d.text((108 - d.textlength(n, font=bold(34)) / 2, y + 9), n, font=bold(34), fill=WHITE)
        for j, line in enumerate(wrap(d, s, fs, W - 260)):
            d.text((166, y + j * 56), line, font=fs, fill=WHITE if j == 0 else WHITE)
        y += 56 * len(wrap(d, s, fs, W - 260)) + 36
    # pie de marca
    d.line([80, H - 150, W - 80, H - 150], fill=PANEL, width=3)
    d.text((80, H - 118), "SYLRED COMPUTERS", font=bold(40), fill=WHITE)
    fg = reg(32)
    txt = "Guarda y comparte"
    d.text((W - 80 - d.textlength(txt, font=fg), H - 112), txt, font=fg, fill=GREY)
    im.save(out, quality=95)




if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 5:
        sys.exit(__doc__)
    card(a[0], a[1], a[2], a[3:-1], a[-1])
    print(a[-1])
