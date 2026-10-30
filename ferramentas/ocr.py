"""Gera cópia pesquisável (com camada de texto OCR) de um PDF escaneado, mantendo as mesmas páginas.

Uso: python -P ferramentas/ocr.py "<glob do pdf>" <saida.pdf> [idioma=eng] [dpi=300]
Ex.: python -P ferramentas/ocr.py "referencias/extraido/ISO/ISO 14122-3*" referencias/ocr/ISO-14122-3-2001.pdf eng
Requer Tesseract (winget UB-Mannheim.TesseractOCR) — idiomas eng/por.
"""
import glob
import os
import sys

import pymupdf

TESSDATA = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tessdata")


def main():
    padrao, saida = sys.argv[1], sys.argv[2]
    idioma = sys.argv[3] if len(sys.argv) > 3 else "eng"
    dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    achados = glob.glob(padrao)
    if len(achados) != 1:
        sys.exit(f"glob deve achar 1 arquivo, achou {len(achados)}: {achados}")
    orig = pymupdf.open(stream=open(achados[0], "rb").read(), filetype="pdf")
    novo = pymupdf.open()
    for i, pag in enumerate(orig):
        cinza = pag.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)  # cinza: arquivo ~3× menor que colorido
        # pdfocr_tobytes devolve camada de texto VAZIA para pixmap de 1 canal: o OCR roda em RGB
        # e depois a imagem embutida é trocada pela cinza (texto continua igual)
        bloco = pymupdf.open("pdf", pymupdf.Pixmap(pymupdf.csRGB, cinza).pdfocr_tobytes(language=idioma, tessdata=TESSDATA))
        for img in bloco[0].get_images():
            bloco.update_stream(img[0], cinza.samples, compress=True)
            bloco.xref_set_key(img[0], "ColorSpace", "/DeviceGray")
        novo.insert_pdf(bloco)
        print(f"pág. {i + 1}/{len(orig)}", flush=True)
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    novo.save(saida, garbage=3, deflate=True)
    print("OK ->", saida)


if __name__ == "__main__":
    main()
