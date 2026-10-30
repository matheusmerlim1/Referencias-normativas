"""Recorta uma região de uma página de PDF como PNG (para figuras com cotas).

Uso:  python -P ferramentas/crop.py "<glob do pdf>" <pagina> "x0,y0,x1,y1" <dpi> <saida.png>
Coordenadas em pontos PDF (A4 = 595 x 842). Dica: renderize a página inteira primeiro
com o retângulo "0,0,595,842" a 70 dpi para localizar a figura (1 px ≈ 1,03 pt).
"""
import glob
import sys

import pymupdf

pdf = glob.glob(sys.argv[1])[0]
with open(pdf, "rb") as f:
    doc = pymupdf.open(stream=f.read(), filetype="pdf")
ret = pymupdf.Rect(*map(float, sys.argv[3].split(",")))
doc[int(sys.argv[2]) - 1].get_pixmap(dpi=int(sys.argv[4]), clip=ret).save(sys.argv[5])
print("ok", sys.argv[5])
