"""Genera vídeos verticales (1080x1920, 30 fps) con locución para Instagram Reels y TikTok.

Uso:
  python3 redes/video/generar_video.py guion.json salida.mp4

guion.json:
{
  "etiqueta": "TRUCO WINDOWS",          # CIBERSEGURIDAD / TRUCO WINDOWS / TRUCO LINUX / NUEVO EN EL BLOG (decide colores y estilo)
  "gancho": "¿Sigues recortando capturas en Paint?",
  "titulo": "Captura solo lo que quieras",
  "tecla": "Win + Shift + S",           # Windows: teclas separadas por "+"; Linux: comando; seguridad: idea clave
  "titulo_pasos": "Así de fácil",       # opcional
  "pasos": ["Paso 1", "Paso 2", "Paso 3"],   # 2 o 3 pasos, máx. ~45 caracteres cada uno
  "cierre": "Guárdalo para cuando lo necesites",
  "subcierre": "Más trucos cada semana",  # opcional; en el blog, por defecto lleva al artículo
  "voz": {                              # lo que dice la locución en cada escena
    "gancho": "...", "tecla": "...",
    "pasos": ["...", "...", "..."],     # una frase por paso
    "cierre": "..."
  }
}

Requisitos: playwright (Chromium), ffmpeg y edge-tts (pip install edge-tts).
La voz usa el servicio de lectura en voz alta de Microsoft Edge: el dominio
speech.platform.bing.com debe estar permitido. Variables opcionales:
  VOZ (por defecto es-ES-AlvaroNeural), VELOCIDAD (por defecto +8%).
Sale con código distinto de 0 si algo falla (no deja vídeos a medias).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright

DIR = os.path.dirname(os.path.abspath(__file__))
FPS = 30
TEMAS = {  # mismos colores que generar_tarjeta.py: (inicio, fin, acento)
    "seguridad": ("#FF3D57", "#7C3AED", "#E11D48"),
    "windows": ("#0063FF", "#00C8FF", "#006EF0"),
    "linux": ("#00A878", "#84CC16", "#059669"),
    "blog": ("#7C3AED", "#EC4899", "#A832C8"),
}


def categoria(tag):
    t = tag.upper()
    if "BLOG" in t:
        return "blog"
    if "WINDOWS" in t:
        return "windows"
    if "LINUX" in t:
        return "linux"
    return "seguridad"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"Error en {cmd[0]}: {r.stderr.strip()[-600:]}")
    return r.stdout


def duracion(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def tts(texto, salida):
    env = dict(os.environ)
    if os.path.exists("/root/.ccr/ca-bundle.crt"):
        env.setdefault("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
    cmd = ["edge-tts", "--voice", os.environ.get("VOZ", "es-ES-AlvaroNeural"),
           "--rate=" + os.environ.get("VELOCIDAD", "+8%"), "--text", texto, "--write-media", salida]
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        cmd[1:1] = ["--proxy", proxy]
    run(cmd, env=env)
    if not os.path.exists(salida) or os.path.getsize(salida) < 2000:
        sys.exit("La locución ha salido vacía: revisa el acceso a speech.platform.bing.com")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    salida = os.path.abspath(sys.argv[2])
    cat = categoria(spec["etiqueta"])
    spec["cat"], spec["colores"] = cat, TEMAS[cat]
    spec.setdefault("subcierre", "Artículo completo en sylredcomputers.com" if cat == "blog" else "Más trucos cada semana")
    voz = spec["voz"]
    if len(spec["pasos"]) != len(voz["pasos"]):
        sys.exit("'pasos' y 'voz.pasos' deben tener el mismo número de elementos")

    tmp = tempfile.mkdtemp(prefix="video-sylred-")
    try:
        # 1) Locución: un audio por frase
        frases = {"gancho": [voz["gancho"]], "tecla": [voz["tecla"]], "pasos": voz["pasos"], "cierre": [voz["cierre"]]}
        escenas = []  # (id, duración, [inicio de cada frase], [archivos])
        for sid, textos in frases.items():
            archivos, marcas, t = [], [], 0.2
            for i, tx in enumerate(textos):
                f = os.path.join(tmp, f"{sid}_{i}.mp3")
                tts(tx, f)
                archivos.append(f)
                marcas.append(t)
                t += duracion(f) + 0.15
            escenas.append((sid, round(max(t + 0.45, 2.5), 2), marcas, archivos))

        # 2) Imagen: una escena por archivo, mismos ajustes, luego concat sin recodificar
        partes = []
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto("file://" + os.path.join(DIR, "plantilla.html"))
            pg.evaluate("s => setup(s)", spec)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            for sid, dur, marcas, _ in escenas:
                tmpf = os.path.join(tmp, f"{sid}.tmp.mp4")
                ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                                       "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                                       "-pix_fmt", "yuv420p", "-r", str(FPS), tmpf], stdin=subprocess.PIPE)
                for i in range(round(dur * FPS)):
                    pg.evaluate("a => render(a[0], a[1], a[2], a[3])", [sid, i / FPS, dur, marcas])
                    ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
                ff.stdin.close()
                if ff.wait() != 0:
                    sys.exit(f"ffmpeg falló en la escena {sid}")
                dst = os.path.join(tmp, f"{sid}.mp4")
                os.replace(tmpf, dst)
                partes.append(dst)
            b.close()
        lista = os.path.join(tmp, "lista.txt")
        with open(lista, "w") as f:
            f.writelines(f"file '{x}'\n" for x in partes)
        mudo = os.path.join(tmp, "mudo.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", mudo])

        # 3) Audio: cada frase en su momento, normalizado
        entradas, filtros, etiquetas, offset = [], [], [], 0.0
        n = 0
        for sid, dur, marcas, archivos in escenas:
            for m, a in zip(marcas, archivos):
                ms = int((offset + m) * 1000)
                entradas += ["-i", a]
                filtros.append(f"[{n}:a]aresample=48000,adelay={ms}|{ms}[a{n}]")
                etiquetas.append(f"[a{n}]")
                n += 1
            offset += dur
        filtros.append("".join(etiquetas) + f"amix=inputs={n}:normalize=0,atrim=0:{offset:.2f},"
                       "loudnorm=I=-14:TP=-1.5:LRA=11[out]")
        audio = os.path.join(tmp, "voz.m4a")
        run(["ffmpeg", "-y", "-loglevel", "error", *entradas, "-filter_complex", ";".join(filtros),
             "-map", "[out]", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", audio])

        final_tmp = salida + ".tmp.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", mudo, "-i", audio, "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", final_tmp])
        os.replace(final_tmp, salida)
        print(f"OK {salida} ({offset:.1f} s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
