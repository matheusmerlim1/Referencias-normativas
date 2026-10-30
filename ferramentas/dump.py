"""Extrai o texto de PDFs, página a página, para arquivos .txt.

Uso:  python -P ferramentas/dump.py <pasta_saida> "<glob do pdf>" ["<outro glob>" ...]
Cada página vira um bloco "=====PAGE N=====" (N = página física do PDF, 1-based).
Abre o PDF como stream: caminhos com acento (ç, Ã...) falham em pymupdf.open(caminho).
"""
import glob
import hashlib
import os
import re
import sys

import pymupdf

saida = sys.argv[1]
os.makedirs(saida, exist_ok=True)
for padrao in sys.argv[2:]:
    for pdf in glob.glob(padrao):
        with open(pdf, "rb") as f:
            doc = pymupdf.open(stream=f.read(), filetype="pdf")
        base = os.path.splitext(os.path.basename(pdf))[0]
        # nome curto (evita MAX_PATH no Windows) + hash para não colidir
        nome = re.sub(r"[^A-Za-z0-9_-]+", "_", base)[:24] + "_" + hashlib.md5(pdf.encode()).hexdigest()[:6]
        with open(os.path.join(saida, nome + ".txt"), "w", encoding="utf-8") as f:
            for i, pagina in enumerate(doc):
                f.write(f"\n=====PAGE {i + 1}=====\n" + pagina.get_text())
        print(f"{nome}.txt  <- {pdf}  ({len(doc)} págs)")
