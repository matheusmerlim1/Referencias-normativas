"""Índice de títulos por página dos PDFs de referencias/ → dados/indice.js (busca do site, sem valores).

De cada PDF com texto extrai: sumário embutido (bookmarks) e, página a página, títulos de seção numerados,
tabelas, figuras e anexos. A busca do site encontra o assunto e abre o PDF na página (arquivo.pdf#page=N).
Uso:  python -P ferramentas/indexar_referencias.py            (gera dados/indice.js)
      python -P ferramentas/indexar_referencias.py --teste "<glob>"   (mostra as entradas de um PDF)
"""
import glob
import json
import re
import sys
import time
from pathlib import Path

import pymupdf

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "dados" / "indice.js"
MAX_POR_DOC = 1500
MAX_LEN = 110

R_ROTULO = re.compile(r"^(Table|TABLE|Tabela|TABELA|Figure|FIGURE|Figura|FIGURA|Fig\.|Quadro|QUADRO|Chart|Exhibit)\s*"
                      r"([A-Z]?[\d]+[\d.\-A-Za-z]*|[A-Z](?:[.\-]\d+)+)\b(.*)$")
R_ANEXO = re.compile(r"^(Annex|ANNEX|Anexo|ANEXO|Appendix|APPENDIX|Apêndice|APÊNDICE|Mandatory Appendix|Nonmandatory Appendix)\s+"
                     r"([A-Z]{1,3}|\d+)\b(.*)$")
R_SECAO = re.compile(r"^((?:[A-Z]\.|[A-Z]{2,3}-)?\d{1,3}(?:\.\d{1,3}){0,4})\.?\s+(\S.*)$")
R_SO_NUM = re.compile(r"^((?:[A-Z]\.|[A-Z]{2,3}-)?\d{1,3}(?:\.\d{1,3}){0,4})\.?$")
LIXO = re.compile(r"copyright|licensed|provided by ihs|no reproduction|all rights reserved|todos os direitos|"
                  r"impresso por|exemplar para uso|not for resale|downloaded|^page \d+|^p[aá]gina \d+", re.I)


def limpo(s):
    s = re.sub(r"(\s*\.){3,}\s*\d*\s*$|…+\s*\d*\s*$", "", s)  # pontilhado + nº de página do sumário
    return re.sub(r"\s+", " ", s).strip(" .:–—-—–")[:MAX_LEN]


def bom_titulo(t):
    if len(t) < 3 or LIXO.search(t):
        return False
    letras = sum(c.isalpha() for c in t)
    return letras >= 3 and letras / max(len(t), 1) >= 0.55 and not re.search(r"\.{4,}|…{2,}", t)


FRASE = re.compile(r"\b(shall|should|must|may be|is the|are the|is informative|is normative|deve|devem|pode ser|são|é o|é a)\b", re.I)
FIM_CORTADO = re.compile(r"\b(the|of|and|or|to|is|a|an|be|will|in|for|with|by|e|ou|de|do|da|dos|das|que|em|para|com)$", re.I)


def titulo_ok(t):
    return bom_titulo(t) and not FRASE.search(t) and not FIM_CORTADO.search(t) and not t.endswith(",")


def rotulo(m, prox):
    resto = m.group(3).strip()
    if resto and (resto[0] in ",);]" or resto[0].islower() or re.match(r"^(and|or|e|ou|para|of|in|shows|mostra)\b", resto, re.I)):
        return None  # referência no meio do texto, não legenda
    tit = limpo(resto) if resto else (limpo(prox) if titulo_ok(limpo(prox)) else "")
    if tit and FRASE.search(tit):
        return None
    return limpo(f"{m.group(1)} {m.group(2)} {tit}")


def entradas_pagina(texto):
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    out = []
    for i, l in enumerate(linhas):
        prox = linhas[i + 1] if i + 1 < len(linhas) else ""
        m = R_ROTULO.match(l) or R_ANEXO.match(l)
        if m:
            t = rotulo(m, prox)
            if t:
                out.append(t)
            continue
        m = R_SECAO.match(l)
        if m and len(l) <= 100:
            tit = limpo(m.group(2))
            topo = "." not in m.group(1)  # "8 WARNING: ..." / "5 Allowable ..." costumam ser notas de rodapé
            if titulo_ok(tit) and not tit[0].islower() and not (topo and (len(tit.split()) > 8 or ":" in tit)):
                out.append(limpo(f"{m.group(1)} {tit}"))
            continue
        m = R_SO_NUM.match(l)
        if m and "." in m.group(1) and bom_titulo(limpo(prox)) and len(prox) <= 90:
            out.append(limpo(f"{m.group(1)} {prox}"))
    return out


def indexar(caminho):
    doc = pymupdf.open(stream=open(caminho, "rb").read(), filetype="pdf")
    vistos, ent = set(), []

    def add(p, t):
        k = (p, t.lower())
        if t and k not in vistos and len(ent) < MAX_POR_DOC:
            vistos.add(k)
            ent.append([p, t])

    for nivel, tit, pag in doc.get_toc(simple=True):
        if nivel <= 4 and pag >= 1 and bom_titulo(limpo(tit)):
            add(pag, limpo(tit))
    for i, pg in enumerate(doc):
        for t in entradas_pagina(pg.get_text()):
            add(i + 1, t)
    ent.sort(key=lambda x: x[0])
    return ent, len(doc)


def main():
    if "--teste" in sys.argv:
        for c in glob.glob(sys.argv[sys.argv.index("--teste") + 1]):
            ent, n = indexar(c)
            print(f"# {c} — {n} págs, {len(ent)} entradas")
            for p, t in ent:
                print(f"  p{p}: {t}")
        return
    refs = json.loads((RAIZ / "conteudo" / "referencias.json").read_text(encoding="utf-8"))
    normas = json.loads((RAIZ / "conteudo" / "normas.json").read_text(encoding="utf-8"))
    alvos = [(d["arquivo"], d["codigo"], d["titulo"], d.get("edicao") or "") for d in refs
             if d.get("texto_extraivel") and str(d["arquivo"]).lower().endswith(".pdf")]
    # cópias OCR (referencias/ocr/) usadas nas fichas
    alvos += [(n["arquivo"], n["id"], n["titulo"], n.get("edicao") or "") for n in normas if n["arquivo"].startswith("referencias/ocr/")]
    docs, entradas, erros, t0 = [], [], [], time.time()
    for k, (arq, cod, tit, ed) in enumerate(alvos):
        try:
            ent, _ = indexar(RAIZ / arq)
        except Exception as e:  # PDF corrompido etc.
            erros.append(f"{arq}: {e}")
            continue
        if not ent:
            continue
        di = len(docs)
        docs.append([arq, cod, tit, str(ed)[:30]])
        entradas += [[di, p, t] for p, t in ent]
        if k % 50 == 0:
            print(f"{k}/{len(alvos)} docs, {len(entradas)} entradas, {time.time() - t0:.0f}s", flush=True)
    SAIDA.write_text("window.UVA_INDICE = " + json.dumps({"docs": docs, "e": entradas}, ensure_ascii=False, separators=(",", ":")) + ";\n",
                     encoding="utf-8")
    print(f"OK: {len(docs)} documentos, {len(entradas)} entradas, {SAIDA.stat().st_size / 1e6:.1f} MB -> {SAIDA.relative_to(RAIZ)}")
    for e in erros:
        print("ERRO", e)


if __name__ == "__main__":
    main()
