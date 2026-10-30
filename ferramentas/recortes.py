"""Localiza TABELAS e FIGURAS em normas com texto (ASME BPVC, B16, B18, B31…) e recorta cada uma como imagem 1 bit.

- Tamanho do corpo do texto = tamanho de fonte mais usado no documento (por nº de caracteres).
- Tabela: título "TABLE X" / "Table X" e as linhas de fonte MENOR que o corpo logo abaixo (mesma coluna; notas incluídas).
- Figura: legenda "FIG. X" / "Fig. X" / "Figure X"; a figura é a faixa de desenhos, imagens e rótulos entre a legenda e
  a próxima linha de corpo de texto (na coluna da legenda, ou largura toda se a legenda é centrada). Se não houver nada
  abaixo, procura acima da legenda (estilo com legenda embaixo).
Itens citados no meio do texto ("see Fig. UG-34") são ignorados: a legenda tem de começar a linha e não ser texto corrido.

uso: python -P ferramentas/recortes.py <arquivo.pdf> [pasta_png] [pág_ini-pág_fim]
"""
import collections
import io
import re
import sys

import pymupdf
from PIL import Image

RX_TAB = re.compile(r"^(TABLE|Table|TABELA|Tabela|QUADRO|Quadro)\s+([A-Z]\.\d+[\w.\-‐–]*|[A-Z]{0,5}[-‐–]?\d[\w.\-‐–()]*|[A-Z]{1,3}-?\d*)")
RX_COD = re.compile(r"[A-Z]{1,4}-\d+(\.\d+)*(\([a-z]\))?[A-Z]?")
RX_FIG = re.compile(r"^(FIG\.|Fig\.|FIGURE|Figure|FIGURA|Figura)\s+([A-Z]\.\d+[\w.\-‐–]*|[A-Z]{0,5}[-‐–]?\d[\w.\-‐–()]*|[A-Z]{1,3}-?\d*)")


def corpo(d, amostra=40):
    """tamanho do texto corrido: moda (por caracteres) das linhas de PROSA — longas e com várias palavras minúsculas.
    Linhas de tabela têm poucas palavras; o rodapé de licença (5 pt, em toda página) fica fora."""
    c, todos = collections.Counter(), collections.Counter()
    n = len(d)
    paginas = range(n) if n <= 3 * amostra else range(0, n, max(1, n // amostra))
    for i in paginas:
        alto = d[i].rect.height - 60
        for b in d[i].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                if not l["spans"] or l["bbox"][1] > alto:
                    continue
                t = "".join(s["text"] for s in l["spans"]).strip()
                tam = round(max(s["size"] for s in l["spans"]), 1)
                todos[tam] += len(t)
                if len(t) > 50 and len(re.findall(r"\b[a-z]{3,}\b", t)) >= 6:
                    c[tam] += len(t)
    m = c or todos
    return m.most_common(1)[0][0] if m else 10.0


def linhas(pg):
    out = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if t:
                out.append({"bb": pymupdf.Rect(l["bbox"]), "tam": max(s["size"] for s in l["spans"]), "t": t,
                            "vert": abs(l["dir"][0]) < 0.5, "bold": any(s["flags"] & 16 or re.search(r"Bold|Black|Heavy", s["font"]) for s in l["spans"])})
    return sorted(out, key=lambda l: (l["bb"].y0, l["bb"].x0))


def elementos(pg, alto):
    """retângulos de desenhos (sem fundos de página inteira) e imagens."""
    rs = []
    for dr in pg.get_drawings():
        r = dr["rect"]
        if r.y0 > alto or (r.width > pg.rect.width * 0.95 and r.height > pg.rect.height * 0.9):
            continue
        r = pymupdf.Rect(r)  # traço de espessura 0: Rect | Rect vazio IGNORA o vazio → engrossa 0,25 pt de cada lado
        if r.width < 0.5:
            r.x0, r.x1 = r.x0 - 0.25, r.x1 + 0.25
        if r.height < 0.5:
            r.y0, r.y1 = r.y0 - 0.25, r.y1 + 0.25
        rs.append(r)
    tiras = []
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.y0 < alto and r.width > 20 and r.height > 20:
                rs.append(pymupdf.Rect(r))
            elif r.width > pg.rect.width * 0.5:
                tiras.append(pymupdf.Rect(r))
    if len(tiras) >= 10:  # página escaneada guardada em tiras de poucos pt de altura (ex. ISO 7379)
        u = pymupdf.Rect(tiras[0])
        for r in tiras[1:]:
            u |= r
        rs.append(u)
    return rs


def escaneada(pg):
    """página coberta por uma imagem (ou tiras) do tamanho da página."""
    return any(r.width >= pg.rect.width * 0.8 and r.height >= pg.rect.height * 0.6 for r in elementos(pg, pg.rect.height))


def coluna(pg, h):
    """coluna do item a partir do título JÁ completo (legenda + título): largura toda só se ele cruza o meio da página."""
    meio = pg.rect.width / 2
    if (h.x0 < meio - 50 and h.x1 > meio + 50) or h.width > meio * 0.9 or abs((h.x0 + h.x1) / 2 - meio) < 30:  # cruza o meio com folga (tabela larga ao lado de outra)
        return 36, pg.rect.width - 36
    return (36, meio) if h.x0 < meio - 20 else (meio, pg.rect.width - 36)


def sobre(bb, x0, x1, folga=10):
    """sobreposição horizontal de mais de `folga` pt (linha justificada da coluna esquerda termina em x≈306)."""
    return min(bb.x1, x1) - max(bb.x0, x0) > folga


def prosa(l):
    return len(l["t"]) > 35 and len(re.findall(r"(?<![\w])[a-zà-ÿ]{3,}(?![\w])", l["t"])) >= 5


def secao_l(l, body, so_numero=True):
    """título de seção: "3.4.4" em negrito sozinho na linha (BV), "6.4.8 Buckling" em negrito ou em fonte maior (DNV).
    so_numero=False: ignora o nº sozinho (cota "0.5" em negrito dentro de desenho)."""
    if RX_TAB.match(l["t"]) or RX_FIG.match(l["t"]):
        return False
    return bool((so_numero and l["bold"] and l["tam"] >= body - 0.25 and re.match(r"^\d+(\.\d+)+\s*$", l["t"]))
                or ((l["bold"] or l["tam"] >= body + 2) and re.match(r"^[A-Z]?\.?\d+(\.\d+)*\s+[A-Z]", l["t"])))


RX_PARAG = re.compile(r"^[A-Z]{1,4}-\d+(\.\d+)*[a-z]?(\([a-z0-9]+\))?\s+[A-Z]")


def titulo(ls, i, h, body=None):
    h0 = pymupdf.Rect(h)  # legenda original: o título continua SOBRE ela (não na coluna vizinha)
    tit = [ls[i]["t"]]
    mesma = [l for l in ls if l is not ls[i] and abs(l["bb"].y0 - h.y0) < 3 and h.x1 - 2 <= l["bb"].x0 < h.x1 + 40
             and not (RX_TAB.match(l["t"]) or RX_FIG.match(l["t"]))]
    for l in sorted(mesma, key=lambda l: l["bb"].x0):  # título na mesma linha da legenda ("FIG. UG-28   DIAGRAMMATIC …")
        tit.append(l["t"])
        h = h | l["bb"]
    for l in [l for l in ls[i + 1:i + 8] if l not in mesma][:6]:
        if l["bb"].y0 - h.y1 > 25:
            break
        if abs((l["bb"].x0 + l["bb"].x1) / 2 - (h.x0 + h.x1) / 2) > 150 or not sobre(l["bb"], h0.x0 - 60, h0.x1 + 60, 1):
            continue  # linha de outra coluna na mesma altura (título da tabela vizinha)
        if RX_TAB.match(l["t"]) or RX_FIG.match(l["t"]):
            break
        if (body and secao_l(l, body)) or RX_PARAG.match(l["t"]):
            break  # título de seção logo abaixo não é título do item
        if any(x is not l and x not in mesma and x is not ls[i] and abs(x["bb"].y0 - l["bb"].y0) < 2 for x in ls):
            break  # linha com várias células = cabeçalho da tabela
        so_cod = len(tit) == 1 and (RX_TAB.fullmatch(tit[0].strip()) or RX_FIG.fullmatch(tit[0].strip())) \
            and not tit[0].lower().startswith("figura")
        if (l["t"].upper() == l["t"] and re.search(r"[A-Z]{3}", l["t"])) or (l["bold"] and len(tit) < 3) or (so_cod and l["t"][:1].isupper()):
            tit.append(l["t"])
            h = h | l["bb"]
        else:
            break
    return " ".join(tit), h


def itens_de_lado(pg, todas):
    """tabela/figura impressa de lado (texto vertical): a página inteira, girada ao salvar."""
    res = []
    for l in todas:
        m = RX_TAB.match(l["t"]) or RX_FIG.match(l["t"])
        if l["vert"] and m and not l["t"][m.end():].strip()[:1].islower():
            perto = sorted([x for x in todas if x["vert"] and x is not l and 0 < x["bb"].x0 - l["bb"].x0 < 30 and x["bold"]
                            and x["bb"].y0 < l["bb"].y1 + 200 and x["bb"].y1 > l["bb"].y0 - 200], key=lambda x: x["bb"].x0)
            tit = " ".join([l["t"]] + [x["t"] for x in perto[:2] if not (RX_TAB.match(x["t"]) or RX_FIG.match(x["t"]))])
            res.append({"tipo": "tabela" if RX_TAB.match(l["t"]) else "figura", "num": m.group(2), "titulo": tit,
                        "bbox": pymupdf.Rect(20, 30, pg.rect.width - 20, pg.rect.height - 40), "texto": " ".join(x["t"] for x in todas)[:2000],
                        "girar": True})
    return res


def itens_pagina(pg, body, ocr=False, leg_doc=None):
    todas = linhas(pg)
    de_lado = itens_de_lado(pg, todas)
    if de_lado:
        return de_lado
    ls = [l for l in todas if not l["vert"]]
    alto = pg.rect.height - 45
    els = elementos(pg, alto)
    cabs = []
    txt_pag = " ".join(l["t"] for l in ls)
    def linha_sumario(l):  # "Figura 3 — Título ..... 12" ou "Tabela 2 Título 15": título E nº de página depois do nº do item
        m = RX_TAB.match(l["t"]) or RX_FIG.match(l["t"])
        resto = l["t"][m.end():] if m else ""
        return bool(m) and (bool(re.search(r"\.{3,}|…{2,}", resto)) or bool(re.search(r"[A-Za-zÀ-ÿ]{3,}.*\s\d{1,3}\s*$", resto)))
    for k, l in enumerate(ls[:-1]):
        if not (RX_TAB.match(l["t"]) or RX_FIG.match(l["t"])):
            continue
        y = l["bb"].y1
        for nx in ls[k + 1:k + 4]:  # título em até 3 linhas; pontilhado (com ou sem nº de página) = sumário
            if RX_TAB.match(nx["t"]) or RX_FIG.match(nx["t"]) or nx["bb"].y0 - y > 6:
                break
            if re.search(r"\.{5,}\s*\d*\s*$", nx["t"]):
                l["sumario"] = True  # "TABLE 1  Título" / "continuação ........ 159"
                break
            y = nx["bb"].y1
    n_sum = sum(1 for l in ls if linha_sumario(l) or l.get("sumario"))
    n_leg = sum(1 for l in ls if RX_TAB.match(l["t"]) or RX_FIG.match(l["t"]))
    sem_desenho = len([r for r in els if r.height < pg.rect.height * 0.7]) < 3  # sumário quase não tem traço
    if re.search(r"\b(Sumário|SUMÁRIO|Índice|ÍNDICE|CONTENTS|Contents)\b", txt_pag) or n_sum >= 3 or (n_leg >= 5 and sem_desenho):
        return []  # sumário/lista de tabelas e figuras (continuação do sumário não tem o título "Sumário")
    for i, l in enumerate(ls):
        m = RX_TAB.match(l["t"]) or RX_FIG.match(l["t"])
        if not m and l["bold"] and l["tam"] < body - 0.4 and RX_COD.fullmatch(l["t"]) and i + 1 < len(ls) \
                and ls[i + 1]["t"].upper() == ls[i + 1]["t"] and re.search(r"[A-Z]{4}", ls[i + 1]["t"]):
            cabs.append((i, "item", l["t"]))  # Seção IX: tabela titulada só pelo código ("QW-451.1" + título em maiúsculas)
            continue
        if not m or l["bb"].y0 > alto:
            continue
        resto = l["t"][m.end():].strip()
        if l.get("sumario"):
            continue  # entrada de sumário (ABS)
        if re.fullmatch(r"\S+\s+\S+\.", l["t"].strip()):  # "TABLE 2." sozinho: título só se a linha de baixo é título
            nx = ls[i + 1] if i + 1 < len(ls) else None
            if not (nx and nx["bb"].y0 - l["bb"].y1 < 15 and len(nx["t"]) < 120 and not RX_TAB.match(nx["t"])
                    and (nx["bold"] or (nx["t"].upper() == nx["t"] and re.search(r"[A-Z]{3}", nx["t"]))
                         or (ocr and nx["t"][:1].isupper()))):  # cópia OCR: título em caixa mista, sem negrito
                continue  # citação "… see TABLE 2." no fim de frase (ABS)
        if resto[:1] in (";", ","):
            continue  # entrada de índice ("Figura 2; 5.4;")
        if resto[:1].islower() or len(l["t"]) > 140 or (")" in m.group(2) and "(" not in m.group(2) and not re.match(r"^\s*[—–-]", resto)):  # citação
            continue
        if not re.search(r"\d", m.group(2)):
            continue  # "Table T" (letra solta) — referência, não título
        prox_tit = i + 1 < len(ls) and ls[i + 1]["t"][:1].isupper() and len(ls[i + 1]["t"]) < 120 and ls[i + 1]["bb"].y0 - l["bb"].y1 < 15
        if re.search(r"\.{5,}|…{2,}", l["t"]):
            continue  # linha de sumário ("Figura 1 – Dimensões ........ 4")
        abnt = bool(re.match(r"^[—–-]\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", resto)) or (resto in ("-", "—", "–") and prox_tit)  # "Tabela 1 — …" / "Table 1 -" + título abaixo
        if not (l["bold"] or m.group(1).isupper() or abnt or (ocr and len(l["t"]) < 110 and (resto[:1].isupper() or (not resto and prox_tit)))):
            continue  # título é negrito ou "TABLE"/"FIG." em maiúsculas; "Fig. UW-16.1" no texto corrido é citação
            # (cópia OCR não tem negrito: aceita "Table 403.2.1-1 Título" em linha curta)
        num = re.sub(r"(\d)[-‐–][A-Z][a-z]{2,}.*$", r"\1", m.group(2))  # "4.4-Bevel" (AWS OCR) → "4.4"
        cabs.append((i, "tabela" if RX_TAB.match(l["t"]) else "figura", num))
    # legenda no cabeçalho da página ("Fig. UG-28.1" no topo, VIII-1 2001) repetida mais abaixo: fica a de baixo
    cabs = [c for c in cabs if not (ls[c[0]]["bb"].y0 < 75 and any(o[2] == c[2] and ls[o[0]]["bb"].y0 > ls[c[0]]["bb"].y0 + 20 for o in cabs)
                                    and any(x is not ls[c[0]] and abs(x["bb"].y0 - ls[c[0]]["bb"].y0) < 3 for x in ls))]  # cabeçalho = linha com outro texto ao lado
    res = []
    esc = max(1.0, pg.rect.width / 612)  # distâncias em pt valem para página A4/carta
    for k, (i, tipo, num) in enumerate(cabs):
        h = pymupdf.Rect(ls[i]["bb"])
        tit, hh = titulo(ls, i, h, body)
        x0, x1 = coluna(pg, hh)
        # 4) próxima legenda abaixo que sobrepõe a coluna encerra o item
        prox = [ls[j]["bb"].y0 for j, _, _ in cabs if ls[j]["bb"].y0 > hh.y1 + 2 and sobre(ls[j]["bb"], x0, x1)]
        y_lim = min(prox) - 2 if prox else alto
        caixa = pymupdf.Rect(hh)
        y_fim = hh.y1
        if tipo in ("tabela", "item"):
            for l in ls:
                if l["bb"].y0 <= hh.y1 - 1 or l["bb"].y0 > y_lim:
                    continue
                if not sobre(l["bb"], x0, x1):
                    continue
                dentro_grade = any(r.y0 >= hh.y0 - 2 and r.y0 < l["bb"].y0 and r.y1 > l["bb"].y1 and r.height < pg.rect.height * 0.7
                                   and ((r.width < 3 and r.height > 8 and x0 - 5 < r.x0 < x1 + 5) or (r.width >= 3 and sobre(r, x0, x1, 5)))
                                   for r in els)  # traço vertical da grade ou célula/moldura que contém a linha
                secao = secao_l(l, body) \
                    or re.match(r"^([A-Z] \d{3}\s+[A-Z]|Guidance note|-+e-+n-+d)", l["t"])  # DNV
                if (l["tam"] >= body - 0.25 and (prosa(l) or (l["bold"] and RX_PARAG.match(l["t"])) or secao) and not dentro_grade) \
                        or re.match(r"^(Guidance note|-+e-+n-+d)", l["t"]):
                    break  # texto corrido ou título de parágrafo: fim da tabela (VIII-2 usa 10 pt também nas tabelas)
                if l["bb"].y0 - y_fim > 28 * esc * (2 if ocr and y_fim <= hh.y1 + 2 else 1):  # OCR: vão maior até a 1ª linha
                    desenho = [r for r in els if r.y0 >= y_fim - 2 and r.y1 <= l["bb"].y0 + 2 and r.x1 > x0 and r.x0 < x1
                               and (r.height > 4 or r.width > 4)
                               and (y_fim <= hh.y1 + 2 or r.height < 3 or r.width < 3)]  # croqui só antes da 1ª linha de dados
                    if not desenho:  # vão sem desenho = fim da tabela
                        break
                    for r in desenho:  # tabela com croqui entre o título e os dados (ex. B16.48)
                        caixa |= r
                caixa |= l["bb"]
                y_fim = max(y_fim, l["bb"].y1)
            for r in els:
                if hh.y0 - 2 <= r.y0 <= y_fim + 3 and r.x1 > x0 - 5 and r.x0 < x1 + 5 and r.height < 3:
                    caixa |= r
            # tabela com GRADE/MOLDURA (ABNT): cresce por traços e caixas da coluna da tabela, encostados no fundo atual
            # (texto descritivo dentro da grade não encerra a tabela). Ignora a moldura da página inteira.
            lim = (min(prox) - 2 if prox else pg.rect.height - 15) + 2  # sem legenda abaixo: até a margem real da página
            cand = [r for r in els if r.y0 >= hh.y0 - 2 and r.y1 <= lim and r.height < pg.rect.height * 0.7
                    and r.x0 >= x0 - 15 and r.x1 <= x1 + 15 and sobre(r, x0, x1, 5)]
            cresceu = True
            while cresceu:
                cresceu = False
                for r in cand:
                    fino = r.height < 3 or r.width < 3
                    if r.y0 <= caixa.y1 + (3 if fino else 30) * esc and r.y1 > caixa.y1 + 0.5 and sobre(r, caixa.x0, caixa.x1, 20) \
                            and not any(RX_FIG.match(l["t"]) and caixa.y1 < l["bb"].y0 < r.y1 for l in ls):
                        caixa.y1 = r.y1
                        if not fino:
                            caixa.x0, caixa.x1 = min(caixa.x0, r.x0), max(caixa.x1, r.x1)
                        cresceu = True
            for r in els:  # traços/moldura da tabela que passam da coluna do título (última coluna cortada)
                if r.y0 >= caixa.y0 - 2 and r.y1 <= caixa.y1 + 2 and r.height < pg.rect.height * 0.7 and sobre(r, caixa.x0, caixa.x1, 5):
                    caixa.x0, caixa.x1 = min(caixa.x0, r.x0), max(caixa.x1, r.x1)
            for l in ls:  # notas logo abaixo da grade, em fonte menor que o corpo
                if re.match(r"^(Guidance note|-+e-+n-+d)", l["t"]) or secao_l(l, body):
                    if caixa.y1 < l["bb"].y0 < caixa.y1 + 14:
                        break
                    continue
                if caixa.y1 < l["bb"].y0 < caixa.y1 + 14 and l["tam"] < body - 0.4 and sobre(l["bb"], x0, x1) and l["bb"].y0 < y_lim:
                    caixa |= l["bb"]
        else:
            def faixa_abaixo():
                corpo_abaixo = [l["bb"].y0 for l in ls if l["bb"].y0 > hh.y1 + 2 and l["tam"] >= body - 0.25 and not l["bold"]
                                and sobre(l["bb"], x0, x1) and prosa(l) and not RX_FIG.match(l["t"])] \
                    + [l["bb"].y0 for l in ls if l["bb"].y0 > hh.y1 + 2 and sobre(l["bb"], x0, x1)
                       and (secao_l(l, body) or re.match(r"^(Guidance note|-+e-+n-+d)", l["t"]))]
                yl = min([y_lim] + corpo_abaixo)
                f = [r for r in els if r.y0 >= hh.y0 - 2 and r.y0 < yl - 2 and r.y1 <= max(yl + 2, min(y_lim, yl + 30 * esc))
                     and r.x1 > x0 - 5 and r.x0 < x1 + 5]  # bbox da linha de prosa às vezes invade o desenho
                return f + [l["bb"] for l in ls if l["bb"].y0 > hh.y1 and l["bb"].y1 <= yl + 1 and sobre(l["bb"], x0, x1)]

            def faixa_acima():
                # até a linha de prosa anterior ou a legenda/título anterior na coluna (figuras empilhadas)
                corpo_acima = [l["bb"].y1 for l in ls if l["bb"].y1 < h.y0 - 2 and l["tam"] >= body - 0.25 and not l["bold"]
                               and sobre(l["bb"], x0, x1) and prosa(l)]
                leg_acima = [ls[j]["bb"].y1 for j, _, _ in cabs if ls[j]["bb"].y1 < h.y0 - 2 and sobre(ls[j]["bb"], x0, x1)]
                ja = [r["bbox"].y1 for r in res if not r.get("pagina_inteira") and r["bbox"].y1 < h.y0 and sobre(r["bbox"], x0, x1, 40)]
                sec = [l["bb"].y1 for l in ls if l["bb"].y1 < h.y0 - 2 and sobre(l["bb"], x0, x1) and secao_l(l, body, False)]
                y_ini = max(corpo_acima + leg_acima + ja + sec + [62])  # abaixo do cabeçalho da página
                f = [r for r in els if r.y0 >= y_ini - 2 and r.y1 <= h.y0 + 2 and r.x1 > x0 - 5 and r.x0 < x1 + 5]
                return f + [l["bb"] for l in ls if l["bb"].y0 >= y_ini and l["bb"].y1 <= h.y0 and sobre(l["bb"], x0, x1)]

            bbs_txt = [l["bb"] for l in ls]

            def tem_desenho(f):  # só desenhos/imagens (linhas de texto e filetes não contam)
                d = [r for r in f if r not in bbs_txt]
                if not d:
                    return False
                e = pymupdf.Rect(d[0])
                for r in d[1:]:
                    e |= r
                return e.width >= 15 and e.height >= 15

            # ABNT ("Figura N — …"): legenda EMBAIXO da figura → procura acima primeiro; ASME ("FIG. UG-28"): acima da figura
            legenda_embaixo = ls[i]["t"].lower().startswith("figura") or bool(re.match(r"^\S+\s+\S+?\s*[—–]", ls[i]["t"]))  # ABNT / ISO "Figure 1 — …"
            if leg_doc is not None:
                legenda_embaixo = leg_doc  # votação no documento (ASTM "FIG. 86 Título", AWS OCR "Figure 4.4-…" ficam embaixo)
            ordem = (faixa_acima, faixa_abaixo) if legenda_embaixo else (faixa_abaixo, faixa_acima)
            faixa = ordem[0]()
            if not tem_desenho(faixa):
                f2 = ordem[1]()
                d2 = [r for r in f2 if r not in bbs_txt]
                if d2:  # desenho do outro lado encostado em OUTRA legenda = é dela
                    lo, hi = min(r.y0 for r in d2), max(r.y1 for r in d2)
                    if any(j != i and sobre(ls[j]["bb"], x0, x1) and (abs(ls[j]["bb"].y0 - hi) < 30 * esc or abs(lo - ls[j]["bb"].y1) < 30 * esc)
                           for j, _, _ in cabs):
                        f2 = []
                faixa = f2
            for r in faixa:
                caixa |= r
            des = [r for r in faixa if r not in [l["bb"] for l in ls]]
            env = pymupdf.Rect(des[0]) if des else None
            for r in des[1:]:
                env |= r
            if not env or env.height < 15 or env.width < 15:
                # figura RASTER (ex. ASTM F1166): a imagem encosta na legenda, mas rótulos de texto sobre ela parecem prosa
                # e cortam a faixa — pega a imagem inteira mais próxima, acima ou abaixo, na coluna (não a página escaneada)
                perto = []
                for img in pg.get_images(full=True):
                    for r in pg.get_image_rects(img[0]):
                        if r.width < 40 or r.height < 40 or (r.width >= pg.rect.width * 0.8 and r.height >= pg.rect.height * 0.6) \
                                or not sobre(r, x0, x1, 20):
                            continue
                        d = h.y0 - r.y1 if r.y1 <= h.y0 + 4 else (r.y0 - hh.y1 if r.y0 >= hh.y1 - 4 else None)
                        if d is not None and d < 30 * esc:
                            perto.append((d, pymupdf.Rect(r)))
                if perto:
                    r = min(perto, key=lambda x: x[0])[1]
                    caixa = pymupdf.Rect(hh) | r
                    for l in ls:  # rótulos e notas sobre/junto da imagem
                        if r.y0 - 2 <= l["bb"].y0 and l["bb"].y1 <= r.y1 + 2 and sobre(l["bb"], r.x0, r.x1):
                            caixa |= l["bb"]
                    txt = " ".join(l["t"] for l in ls if caixa.contains(l["bb"]))
                    res.append({"tipo": tipo, "num": num, "titulo": re.sub(r"\s+", " ", tit), "bbox": (caixa + (-4, -4, 4, 4)) & pg.rect, "texto": txt})
                    continue
                # sem desenho/imagem junto da legenda (figura de lado, foto…): guarda a página inteira
                res.append({"tipo": "figura", "num": num, "titulo": re.sub(r"\s+", " ", tit),
                            "bbox": pymupdf.Rect(20, 30, pg.rect.width - 20, pg.rect.height - 40), "texto": "", "pagina_inteira": True,
                            "motivo": "figura sem desenho localizável junto da legenda"})
                continue
        if caixa.height < hh.height + 12:
            continue  # só o título (sumário, lista de tabelas)
        txt = " ".join(l["t"] for l in ls if caixa.contains(l["bb"]))
        res.append({"tipo": tipo, "num": num, "titulo": re.sub(r"\s+", " ", tit), "bbox": (caixa + (-4, -4, 4, 4)) & pg.rect, "texto": txt})
    inteiras = [r for r in res if r.get("pagina_inteira")]
    base = lambda n: re.match(r"[^\-‐–(]*", n).group(0).strip(" .")  # "26-a)" → "26"
    recortados = {base(r["num"]) for r in res if not r.get("pagina_inteira")}
    coberto = sum(r["bbox"].height for r in res if not r.get("pagina_inteira"))
    if inteiras and coberto > pg.rect.height * 0.45:  # página já recortada: some só a página inteira de figura que já tem recorte
        res = [r for r in res if not (r.get("pagina_inteira") and base(r["num"]) in recortados)]
        inteiras = [r for r in res if r.get("pagina_inteira")]
    if len(inteiras) > 1:
        inteiras[0]["titulo"] = " / ".join(r["titulo"][:60] for r in inteiras)
        res = [r for r in res if not r.get("pagina_inteira")] + [inteiras[0]]
    vistos, unicos = set(), []
    for r in res:  # mesma tabela/figura 2× na página (título em 2 linhas, página inteira repetida)
        k = (r["tipo"], r["num"], tuple(round(v) for v in r["bbox"]))
        if k not in vistos:
            vistos.add(k)
            unicos.append(r)
    return unicos


RX_PAG = re.compile(r"(?:^|\s)(TABLE|Table|FIG\.|Fig\.|FIGURE|Figure)\s*([A-Z]{0,5}-?\d[\d.\-]*[A-Z]?)\s*([A-Z][A-Za-z ,()/-]{3,80})")


def itens_pagina_inteira(pg, i):
    """texto quebrado (1 letra por linha, fonte 0,1 pt): página inteira como imagem, pelos títulos achados no texto."""
    t = re.sub(r"\s+", " ", pg.get_text().replace("\n", ""))
    achados = []
    for m in RX_PAG.finditer(t):
        tipo = "tabela" if m.group(1).lower().startswith("tab") else "figura"
        if (tipo, m.group(2)) not in [(a["tipo"], a["num"]) for a in achados]:
            achados.append({"tipo": tipo, "num": m.group(2), "titulo": f"{m.group(1)} {m.group(2)} {m.group(3).strip()}",
                            "bbox": pymupdf.Rect(20, 20, pg.rect.width - 20, pg.rect.height - 40), "texto": "", "pagina_inteira": True})
    return achados


def voto_legenda(d, paginas=None):
    """legenda de figura EMBAIXO (True) ou EM CIMA (False) do desenho no documento todo: o desenho mais perto de cada
    legenda "FIG./Figure N" decide; só vale com ≥ 5 votos e ≥ 75 % de acordo (senão None = regra pela pontuação)."""
    v = [0, 0]
    for i in paginas or range(len(d)):
        pg = d[i]
        ls = [l for l in linhas(pg) if not l["vert"]]
        figs = [l for l in ls if RX_FIG.match(l["t"]) and len(l["t"]) < 140]
        if not figs:
            continue
        txt = [l["bb"] for l in ls]
        els = [r for r in elementos(pg, pg.rect.height - 45) if r.height < pg.rect.height * 0.6 and r not in txt and (r.width > 8 or r.height > 8)]
        for l in figs:
            b = l["bb"]
            ac = [b.y0 - r.y1 for r in els if r.y1 <= b.y0 + 2 and sobre(r, b.x0 - 100, b.x1 + 100)]
            ab = [r.y0 - b.y1 for r in els if r.y0 >= b.y1 - 2 and sobre(r, b.x0 - 100, b.x1 + 100)]
            a, c = (min(ac) if ac else 999), (min(ab) if ab else 999)
            if min(a, c) < 40:
                v[0 if a < c else 1] += 1
    n = sum(v)
    if n >= 5 and max(v) >= 0.75 * n:
        return v[0] > v[1]
    return None


def itens(pdf, paginas=None):
    d = pymupdf.open(stream=open(pdf, "rb").read(), filetype="pdf")
    body = corpo(d)
    ocr = "GlyphLessFont" in str(d[min(2, len(d) - 1)].get_fonts())  # camada de texto do Tesseract
    out = []
    leg_doc = voto_legenda(d, paginas) if body >= 3 else None
    for i in paginas or range(len(d)):
        its = itens_pagina_inteira(d[i], i) if body < 3 else itens_pagina(d[i], body, ocr or escaneada(d[i]), leg_doc)
        for t in its:
            t["pagina"] = i + 1
            out.append(t)
    return d, out, body


def salvar_1bit(d, t, arq, dpi=150):
    m = pymupdf.Matrix(dpi / 72, dpi / 72)
    if t.get("girar") and d[t["pagina"] - 1].rotation % 180 != 90:  # página com /Rotate 90 já sai deitada certa
        m = m.prerotate(90)
    pix = d[t["pagina"] - 1].get_pixmap(matrix=m, clip=t["bbox"], colorspace=pymupdf.csGRAY)
    im = Image.open(io.BytesIO(pix.tobytes("png")))
    h = im.histogram()
    if sum(h[90:225]) > 0.15 * sum(h):  # muito cinza médio (desenho sombreado, tabela colorida): 1 bit apagaria
        im.point(lambda v: v // 16 * 17).save(arq, "PNG", optimize=True)
    else:
        im.point(lambda v: 255 if v > 150 else 0).convert("1").save(arq, "PNG", optimize=True)


if __name__ == "__main__":
    pags = None
    if len(sys.argv) > 3:
        a, b = map(int, sys.argv[3].split("-"))
        pags = range(a - 1, b)
    d, its, body = itens(sys.argv[1], pags)
    print("corpo", body, "pt;", len(its), "itens")
    for t in its:
        print(t["pagina"], t["tipo"], t["num"], t["titulo"][:60], [round(v) for v in t["bbox"]])
        if len(sys.argv) > 2 and sys.argv[2] != "-":
            salvar_1bit(d, t, f"{sys.argv[2]}/p{t['pagina']}-{t['tipo'][0]}{re.sub(r'[^A-Za-z0-9.]+', '_', t['num'])}.png")
