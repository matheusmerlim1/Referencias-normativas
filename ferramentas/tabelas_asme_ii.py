"""Localiza as tabelas (TABLE N …) das especificações ASME II Partes A/B/C (2007) e recorta cada uma como imagem.

Corpo do texto = 10 pt; tabelas = ≤ 9 pt. A tabela vai do título "TABLE N" até a última linha de fonte pequena
contígua (inclui notas de rodapé da tabela); para em linha de 10 pt, em outro "TABLE" ou num salto vertical grande.

uso: python -P ferramentas/tabelas_asme_ii.py <arquivo.pdf> [pasta_png]   → lista as tabelas (e recorta, se pasta)
"""
import re
import sys

import pymupdf

CORPO = 9.6  # tamanho a partir do qual a linha é texto corrido


def linhas(pg):
    out = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t:
                continue
            tam = max(s["size"] for s in l["spans"])
            out.append({"bb": pymupdf.Rect(l["bbox"]), "tam": tam, "t": t, "vert": abs(l["dir"][0]) < 0.5})
    return sorted(out, key=lambda l: (l["bb"].y0, l["bb"].x0))


def regras(pg):
    rs = []
    for dr in pg.get_drawings():
        for it in dr["items"]:
            if it[0] == "l" and abs(it[1].y - it[2].y) < 0.6 and abs(it[1].x - it[2].x) > 20:
                rs.append(pymupdf.Rect(min(it[1].x, it[2].x), it[1].y - 0.5, max(it[1].x, it[2].x), it[1].y + 0.5))
            elif it[0] == "re" and it[1].height < 1.5 and it[1].width > 20:
                rs.append(pymupdf.Rect(it[1]))
    return rs


def tabelas_da_pagina(pg):
    ls = linhas(pg)
    rs = regras(pg)
    alto = pg.rect.height - 50  # rodapé (nº da página, licença)
    cabs = [i for i, l in enumerate(ls) if re.match(r"^TABLE\s+[A-Z]?\d+(\.\d+)?[A-Z]?\b", l["t"]) and l["tam"] < 10.5]
    res = []
    meio = pg.rect.width / 2
    for k, i in enumerate(cabs):
        h = ls[i]
        num = re.match(r"^TABLE\s+(\S+)", h["t"]).group(1)
        if h["vert"]:  # tabela impressa de lado: a página inteira é a tabela
            tit = " ".join(l["t"] for l in ls if l["vert"] and abs(l["bb"].x0 - h["bb"].x0) < 25 and l["t"].upper() == l["t"])
            caixa = pymupdf.Rect(30, 30, pg.rect.width - 30, alto)
            texto = " ".join(l["t"] for l in ls if l["vert"])
            tit = (h["t"] + " " + tit.replace(h["t"], "")).strip()  # "TABLE N" primeiro
            res.append({"num": num, "titulo": tit, "bbox": caixa, "texto": texto, "girar": True})
            continue
        hc = (h["bb"].x0 + h["bb"].x1) / 2
        # título: linhas logo abaixo do "TABLE N", em maiúsculas, na mesma coluna
        tit = [h["t"]]
        for l in ls[i + 1:i + 6]:
            if abs((l["bb"].x0 + l["bb"].x1) / 2 - hc) > 120:
                continue
            if l["bb"].y0 - h["bb"].y1 < 30 and l["t"].upper() == l["t"] and re.search(r"[A-Z]{3}", l["t"]) and not l["t"].startswith("TABLE"):
                tit.append(l["t"])
            else:
                break
        caixa = pymupdf.Rect(h["bb"])
        # largura: regra horizontal logo abaixo do título que passa pelo centro do título; sem regra, a coluna da página
        rr = [r for r in rs if h["bb"].y0 < r.y0 < h["bb"].y0 + 70 and r.x0 - 5 <= hc <= r.x1 + 5]
        if rr:
            caixa |= pymupdf.Rect(min(r.x0 for r in rr), caixa.y0, max(r.x1 for r in rr), caixa.y1)
        else:
            caixa |= pymupdf.Rect(36 if hc < meio else meio, caixa.y0, meio if hc < meio else pg.rect.width - 36, caixa.y1)
        prox = [ls[j]["bb"].y0 for j in cabs if ls[j]["bb"].y0 > h["bb"].y1 and caixa.x0 - 5 < (ls[j]["bb"].x0 + ls[j]["bb"].x1) / 2 < caixa.x1 + 5]
        y_lim = min(prox) - 2 if prox else alto
        y_fim = h["bb"].y1
        for l in ls[i + 1:]:
            if l["bb"].y0 > y_lim or l["bb"].y0 > alto:
                break
            if l["vert"] or l["bb"].y0 < h["bb"].y0:
                continue
            sobrepoe = l["bb"].x1 > caixa.x0 - 2 and l["bb"].x0 < caixa.x1 + 2
            if not sobrepoe:
                continue
            if l["tam"] >= CORPO:
                break
            if l["bb"].y0 - y_fim > 28:
                break
            caixa |= l["bb"]
            y_fim = max(y_fim, l["bb"].y1)
        for r in rs:
            if caixa.y0 <= r.y0 <= y_fim + 3 and r.x1 > caixa.x0 - 5 and r.x0 < caixa.x1 + 5:
                caixa |= r
        texto = " ".join(l["t"] for l in ls if caixa.contains(l["bb"]) and not l["vert"])
        res.append({"num": num, "titulo": " ".join(tit), "bbox": caixa + (-4, -4, 4, 4), "texto": texto, "girar": False})
    return res


def salvar(d, t, arq, dpi=130):
    """recorta a tabela; tabela de lado é girada para ficar na horizontal. Cinza (8 bits) para arquivo menor."""
    m = pymupdf.Matrix(dpi / 72, dpi / 72)
    if t.get("girar"):
        m = m.prerotate(90)
    pix = d[t["pagina"] - 1].get_pixmap(matrix=m, clip=t["bbox"], colorspace=pymupdf.csGRAY)
    pix.save(arq)


def tabelas(pdf):
    d = pymupdf.open(stream=open(pdf, "rb").read(), filetype="pdf")
    out = []
    for i in range(len(d)):
        for t in tabelas_da_pagina(d[i]):
            t["pagina"] = i + 1
            out.append(t)
    return d, out


if __name__ == "__main__":
    d, ts = tabelas(sys.argv[1])
    for t in ts:
        print(t["pagina"], t["num"], t["titulo"][:70], [round(v) for v in t["bbox"]], len(t["texto"]))
        if len(sys.argv) > 2:
            salvar(d, t, f"{sys.argv[2]}/p{t['pagina']}-t{t['num']}.png")
