"""OCR célula a célula de tabela com grade (linhas pretas). uso:
python -P celocr.py "<glob pdf>" <pág> <saida.json> [x0,y0,x1,y1 em pt]
Detecta linhas horizontais (soma) e verticais (traço contínuo), recorta cada célula e roda tesseract
--psm 7 só com dígitos; células vazias têm nova tentativa com psm 8/13/6. Env: LIM (limiar de cinza), VFRAC."""
import glob
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pymupdf
from PIL import Image

TESS = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
WL = "tessedit_char_whitelist=" + os.environ.get("WL", "0123456789./")
FF = chr(12)  # separador de página da saída do tesseract
p = glob.glob(sys.argv[1])[0]
d = pymupdf.open(stream=open(p, "rb").read(), filetype="pdf")
pg = d[int(sys.argv[2]) - 1]
clip = pymupdf.Rect(*map(float, sys.argv[4].split(","))) if len(sys.argv) > 4 else pg.rect
pix = pg.get_pixmap(dpi=int(os.environ.get("DPI", "400")), clip=clip, colorspace=pymupdf.csGRAY)
im = Image.frombytes("L", (pix.width, pix.height), pix.samples)
if os.environ.get("ROT"):  # tabela girada na página: ROT=90 gira o recorte no sentido anti-horário
    im = im.rotate(int(os.environ["ROT"]), expand=True, fillcolor=255)
a = np.array(im) < int(os.environ.get("LIM", "200"))


def linhas(proj, minfrac):
    idx = np.where(proj > minfrac * proj.max())[0]
    grupos = []
    for i in idx:
        if grupos and i - grupos[-1][-1] <= 3:
            grupos[-1].append(i)
        else:
            grupos.append([i])
    return [(g[0], g[-1]) for g in grupos]


def corrida(m):
    """maior sequência contínua de pixels escuros em cada coluna"""
    best = np.zeros(m.shape[1], int)
    cur = np.zeros(m.shape[1], int)
    for row in m:
        cur = np.where(row, cur + 1, 0)
        best = np.maximum(best, cur)
    return best


def ocr(arquivos, psm):
    lista = os.path.join(tmp, "l.txt")
    open(lista, "w").write(chr(10).join(arquivos))
    o = subprocess.run([TESS, lista, "stdout", "--psm", psm, "-c", WL], capture_output=True, text=True).stdout
    return [t.strip() for t in o.split(FF)]


hs = linhas(a.sum(1), 0.5)
vs = linhas(corrida(a), float(os.environ.get("VFRAC", "0.45")))
if vs[0][0] > 60:  # tabela sem borda externa: bordas virtuais nas pontas do recorte
    vs = [(0, 0)] + vs
if vs[-1][1] < a.shape[1] - 60:
    vs = vs + [(a.shape[1] - 1, a.shape[1] - 1)]
tmp = tempfile.mkdtemp()
cel = []
for r in range(len(hs) - 1):
    y0, y1 = hs[r][1] + 4, hs[r + 1][0] - 4
    if y1 - y0 < 25:
        continue
    for c in range(len(vs) - 1):
        x0, x1 = vs[c][1] + 4, vs[c + 1][0] - 4
        if x1 - x0 < 20:
            continue
        sub = im.crop((x0, y0, x1, y1))
        f = os.path.join(tmp, f"c{r:02d}_{c:02d}.png")
        bg = Image.new("L", (sub.width + 40, sub.height + 40), 255)
        bg.paste(sub, (20, 20))
        bg.save(f)
        cel.append((r, c, f))
res = {}
vazias = []
for (r, c, f), t in zip(cel, ocr([f for _, _, f in cel], os.environ.get("PSM1", "7"))):
    res.setdefault(r, {})[c] = t
    if not t:
        vazias.append((r, c, f))
for psm in ("8", "13", "6"):
    if not vazias:
        break
    resto = []
    for (r, c, f), t in zip(vazias, ocr([f for _, _, f in vazias], psm)):
        if t:
            res[r][c] = t
        else:
            resto.append((r, c, f))
    vazias = resto
rows = [[res[r].get(c, "") for c in sorted(res[r])] for r in sorted(res)]
json.dump(rows, open(sys.argv[3], "w"))
print(len(hs), "h", len(vs), "v", len(rows), "linhas")
for row in rows:
    print(" | ".join(row))
