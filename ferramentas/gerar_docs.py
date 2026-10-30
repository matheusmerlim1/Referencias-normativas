"""Gera fichas de "tabelas e figuras" para normas grandes (ASME BPVC 2007, B16, B18, B31…), usando ferramentas/recortes.py.

Cada tabela/figura achada vira: uma imagem 1 bit em assets/figuras/docs/<ficha>/, uma figura da ficha (com grupo) e um
requisito "Tabela X / Fig. X — título" com item e página (o texto da tabela vai na nota só para a busca).
Grupos: pelo prefixo do item (UG-, UW-, QW-, PG-…; "1-4" → Apêndice 1) nos livros do código, ou pelo documento nas
fichas de família (B16, B18…). Cada documento vira uma norma em conteudo/normas.json.

uso: python -P ferramentas/gerar_docs.py [id_ficha ...] [--gravar]      (sem id: todas; sem --gravar: só conta)
"""
import glob
import json
import os
import re
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(__file__))
import recortes as R

A = "referencias/extraido/ASME"
B7 = f"{A}/ASME BPVC -2007"
OCR = "referencias/ocr"


def doc(id_, arq, titulo, edicao, escopo="", orgao="ASME"):
    return {"id": id_, "arq": arq, "titulo": titulo, "edicao": edicao, "escopo": escopo, "orgao": orgao}


FICHAS = [
    {"id": "asme-viii-1-2007", "titulo": "ASME VIII Div. 1 (2007) — tabelas e figuras", "categoria": "Vasos de pressão e caldeiras", "agrupar": "prefixo",
     "resumo": "Todas as tabelas e figuras do ASME BPVC Seção VIII Divisão 1, edição 2007 (partes UG, UW, UF, UB, UCS, UNF, UHA, UCI, UCL, UCD, UHT, ULW, ULT, UHX, UIG e apêndices), em imagem com item e página.",
     "docs": [doc("ASME-VIII-1-2007", f"{B7}/ASME VIII D1 - 2007/ASME VIII D1.pdf", "BPVC Section VIII, Division 1 — Rules for Construction of Pressure Vessels", "2007")]},
    {"id": "asme-viii-2-2007", "titulo": "ASME VIII Div. 2 (2007) — tabelas e figuras", "categoria": "Vasos de pressão e caldeiras", "agrupar": "prefixo",
     "resumo": "Tabelas e figuras do ASME BPVC Seção VIII Divisão 2 (regras alternativas), edição 2007, em imagem com item e página.",
     "docs": [doc("ASME-VIII-2-2007", f"{B7}/ASME VIII D2  - 2007/ASME VIII D2.pdf", "BPVC Section VIII, Division 2 — Alternative Rules", "2007"),
              doc("ASME-VIII-2-AP4", f"{OCR}/ASME-VIII-2-Ap4.pdf", "Section VIII Division 2 — Appendix 4: Mandatory Design Based on Stress Analysis (cópia OCR)", "s/d")]},
    {"id": "asme-viii-3-2007", "titulo": "ASME VIII Div. 3 (2007) — tabelas e figuras", "categoria": "Vasos de pressão e caldeiras", "agrupar": "prefixo",
     "resumo": "Tabelas e figuras do ASME BPVC Seção VIII Divisão 3 (vasos de alta pressão), edição 2007.",
     "docs": [doc("ASME-VIII-3-2007", f"{B7}/ASME VIII D3 - 2007/ASME VIII D3.pdf", "BPVC Section VIII, Division 3 — Alternative Rules for High Pressure Vessels", "2007")]},
    {"id": "asme-i-2007", "titulo": "ASME I (2007) — caldeiras: tabelas e figuras", "categoria": "Vasos de pressão e caldeiras", "agrupar": "prefixo",
     "resumo": "Tabelas e figuras do ASME BPVC Seção I (caldeiras de potência), edição 2007, em imagem com item e página.",
     "docs": [doc("ASME-I-2007", f"{B7}/ASME I -  2007/ASME SECTION I - 2007.pdf", "BPVC Section I — Rules for Construction of Power Boilers", "2007")]},
    {"id": "asme-ix-2007", "titulo": "ASME IX (2007) — qualificação de soldagem: tabelas e figuras", "categoria": "Soldagem", "agrupar": "prefixo",
     "resumo": "Tabelas (variáveis QW-250…, P-Numbers, F-Numbers, limites de espessura QW-451/452, formulários QW-482…) e figuras do ASME BPVC Seção IX, edição 2007.",
     "docs": [doc("ASME-IX-2007", f"{B7}/ASME IX - 2007/ASME IX.pdf", "BPVC Section IX — Welding and Brazing Qualifications", "2007")]},
    {"id": "asme-x-2007", "titulo": "ASME X (2007) — vasos em PRFV: tabelas e figuras", "categoria": "Vasos de pressão e caldeiras", "agrupar": "prefixo",
     "resumo": "Tabelas e figuras do ASME BPVC Seção X (vasos de pressão em plástico reforçado com fibra), edição 2007.",
     "docs": [doc("ASME-X-2007", f"{B7}/ASME X - 2007/ASME X.pdf", "BPVC Section X — Fiber-Reinforced Plastic Pressure Vessels", "2007")]},
    {"id": "asme-v-2007", "titulo": "ASME V (2007) — ensaios não destrutivos: tabelas e figuras", "categoria": "Ensaios e inspeção", "agrupar": "documento",
     "resumo": "Tabelas e figuras do ASME BPVC Seção V (END: RT, UT, PT, MT, ET, LT, VT…), edição 2007, e das normas de ensaio SE/SD/SA/SB do volume.",
     "docs": "V"},
    {"id": "asme-b16-conexoes-valvulas", "titulo": "ASME B16 — conexões, válvulas, flanges de orifício e figura-8", "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de B16.1 (flanges de ferro fundido), B16.9 (conexões de solda), B16.10 (face a face de válvulas), B16.11 (conexões forjadas SW/rosca), B16.34 (válvulas), B16.36 (flanges de orifício) e B16.48 (raquetes/figura-8).",
     "docs": [doc("ASME-B16.1", f"{A}/ASME B16.1 2020 - Gray Iron Pipe Flanges and Flanged Fittings.pdf", "Gray Iron Pipe Flanges and Flanged Fittings", "2020"),
              doc("ASME-B16.9", f"{A}/ASME B16.9 2001 - Factory-Made Wrought Buttwelding Fittings.pdf", "Factory-Made Wrought Buttwelding Fittings", "2001"),
              doc("ASME-B16.10", f"{A}/ASME B16.10 2000 - FACE-TO-FACE AND END-TO-END DIMEMSIONS OF VALVES.pdf", "Face-to-Face and End-to-End Dimensions of Valves", "2000"),
              doc("ASME-B16.11", f"{OCR}/ASME-B16.11-2001.pdf", "Forged Fittings, Socket-Welding and Threaded (cópia OCR)", "2001"),
              doc("ASME-B16.34", f"{OCR}/ASME-B16.34-2009.pdf", "Valves — Flanged, Threaded, and Welding End (cópia OCR)", "2009"),
              doc("ASME-B16.36", f"{A}/ASME B16.36 2015 - Orifice Flanges.pdf", "Orifice Flanges", "2015"),
              doc("ASME-B16.48", f"{A}/ASME B16.48 2020 - Line Blanks.pdf", "Line Blanks", "2020")]},
    {"id": "asme-b1-b18-roscas-fixadores", "titulo": "ASME B1 e B18 — roscas, parafusos, porcas e arruelas (polegada e métrico)", "categoria": "Parafusos e fixação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de B1.1 (UN/UNR), B1.20.1 (NPT), B1.5/B1.8 (Acme), B18.2.1, B18.2.2, B18.2.3.7M, B18.2.4.1M, B18.3, B18.3.1M, B18.16.6 e B18.21.2M.",
     "docs": [doc("ASME-B1.1", f"{A}/ASME B1.1 - Unified Inch Screw Threads (UN and UNR Thread Form).pdf", "Unified Inch Screw Threads (UN and UNR Thread Form)", "s/d"),
              doc("ASME-B1.20.1", f"{OCR}/ASME-B1.20.1-1983.pdf", "Pipe Threads, General Purpose, Inch — NPT (cópia OCR)", "1983"),
              doc("ASME-B1.5", f"{OCR}/ASME-B1.5-1997.pdf", "Acme Screw Threads (cópia OCR)", "1997"),
              doc("ASME-B1.8", f"{OCR}/ASME-B1.8-1988.pdf", "Stub Acme Screw Threads (cópia OCR)", "1988"),
              doc("ASME-B18.2.1", f"{A}/ASME B18 2 1 2010 Square Hex Heavy Hex and Askew Head Bolts and Hex Heavy Hex Hex Flange Lobed Head and Lag Screws Inch Series.pdf",
                  "Square, Hex, Heavy Hex, and Askew Head Bolts and Hex, Heavy Hex, Hex Flange, Lobed Head, and Lag Screws (Inch Series)", "2010"),
              doc("ASME-B18.2.2", f"{OCR}/ASME-B18.2.2-2015.pdf", "Nuts for General Applications — Inch Series (cópia OCR)", "2015"),
              doc("ASME-B18.2.3.7M", f"{OCR}/ASME-B18.2.3.7M-1979.pdf", "Metric Heavy Hex Structural Bolts (cópia OCR)", "1979"),
              doc("ASME-B18.2.4.1M", f"{OCR}/ASME-B18.2.4.1M-2002.pdf", "Metric Hex Nuts, Style 1 (cópia OCR)", "2002"),
              doc("ASME-B18.3", f"{OCR}/ASME-B18.3-2012.pdf", "Socket Cap, Shoulder, Set Screws, and Hex Keys — Inch Series (cópia OCR)", "2012"),
              doc("ASME-B18.3.1M", f"{OCR}/ASME-B18.3.1M-1986.pdf", "Socket Head Cap Screws — Metric Series (cópia OCR)", "1986"),
              doc("ASME-B18.16.6", f"{A}/ASME B18.16.6 2014 - PREVAILING TORQUE LOCKNUTS INCH SERIES.pdf", "Prevailing-Torque Locknuts — Inch Series", "2014"),
              doc("ASME-B18.21.2M", f"{A}/asme-b18212mpdf.pdf", "Lock Washers (Metric Series)", "s/d")]},
    {"id": "asme-b31-dutos", "titulo": "ASME B31.4 e B31.8 — dutos de líquidos e de gás", "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de B31.4 (transporte de líquidos e lamas por dutos) e B31.8 (transmissão e distribuição de gás).",
     "docs": [doc("ASME-B31.4", f"{OCR}/ASME-B31.4-2019.pdf", "Pipeline Transportation Systems for Liquids and Slurries (cópia OCR — texto do PDF original ilegível)", "2019"),
              doc("ASME-B31.8", f"{A}/ASME B31.8 2003 - Gas Transmission and Distribution Piping Systems.pdf", "Gas Transmission and Distribution Piping Systems", "2003")]},
    {"id": "asme-outros", "titulo": "ASME — reparo (PCC-2), planejamento de içamento (P30.1) e GD&T (Y14.5)", "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ASME PCC-2 (reparo de equipamentos e tubulação), P30.1 (planejamento de movimentação de cargas) e Y14.5 (dimensionamento e tolerâncias geométricas).",
     "docs": [doc("ASME-PCC-2", f"{A}/ASME PCC-2 2022 - Repair of pressure equipment and piping.pdf", "Repair of Pressure Equipment and Piping (só sumário e parte inicial no acervo)", "2022"),
              doc("ASME-P30.1", f"{A}/ASME P30.1 2014 - Planning for Load Handling Activities.pdf", "Planning for Load Handling Activities", "2014"),
              doc("ASME-Y14.5", f"{A}/ASME Y14.5 2018 - Dimensioning and Tolerancing.pdf", "Dimensioning and Tolerancing", "2018")]},
]


# fichas de outros órgãos em arquivos de configuração próprios (ferramentas/docs_*.py, mesmo formato de FICHAS)
import importlib
for _cfg in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "docs_*.py"))):
    FICHAS += importlib.import_module(os.path.splitext(os.path.basename(_cfg))[0]).FICHAS


def docs_secao_v():
    out = [doc("ASME-V-2007", f"{B7}/ASME V - 2007/ASME SECTION V.pdf", "BPVC Section V — Nondestructive Examination", "2007")]
    for f in sorted(glob.glob(f"{B7}/ASME V - 2007/S*.pdf")):
        n = os.path.splitext(os.path.basename(f))[0]
        if n.startswith("SUMMARY"):
            continue
        cod = re.sub(r"^(S[A-Z]) ?(\d+)", r"\1-\2", n.split("-S")[0].strip())
        out.append(doc(f"ASME-V-{cod}", f.replace("\\", "/"), f"{cod} (Seção V, artigo de norma de ensaio)", "2007"))  # glob no Windows usa "\\"
    return out


def grupo_de(item, d, agrupar):
    if agrupar == "documento":
        return f"{d['id'].replace('ASME-', 'ASME ')} — {d['titulo']}"
    m = re.match(r"^([A-Z]{1,5})-", item["num"])
    if m:
        return f"{m.group(1)}-"
    m = re.match(r"^([A-Z]{1,2})?(\d+)-", item["num"])
    if m and not m.group(1):
        return f"Apêndice {m.group(2)}"
    return "Outros itens"


def ordem_grupo(g):
    m = re.match(r"Apêndice (\d+)", g)
    return (1, int(m.group(1)), g) if m else ((2, 0, g) if g == "Outros itens" else (0, 0, g))


def elementos_desenho(pg):
    rs = []
    for img in pg.get_images(full=True):
        for r in pg.get_image_rects(img[0]):
            if r.width > 20 and r.height > 20 and not (r.width >= pg.rect.width * 0.8 and r.height >= pg.rect.height * 0.6):
                rs.append(pymupdf.Rect(r))
    for dr in pg.get_drawings():
        r = pymupdf.Rect(dr["rect"])
        if not (r.width <= 3 or r.height <= 3 or (r.width > pg.rect.width * 0.9 and r.height > pg.rect.height * 0.8)):
            rs.append(r)
    return rs


def repetidos(pdf):
    """elementos IGUAIS (mesma posição) em ≥ 3 páginas = vinheta/logotipo/moldura decorativa."""
    c = {}
    for pg in pdf:
        for k in {tuple(round(v) for v in r) for r in elementos_desenho(pg)}:
            c[k] = c.get(k, 0) + 1
    return {k for k, v in c.items() if v >= 3}


def desenho_pagina(pg, crops=(), ignorar=frozenset()):
    """envoltória dos desenhos/imagens da página que NENHUM recorte cobre (sem traço fino de tabela, sem caixa/faixa em volta
    de texto, sem cabeçalho/rodapé — faixas de 60 pt em cima e embaixo —, sem página escaneada); None se a área descoberta
    for desprezível (< 2 % da página)."""
    t = pg.get_text()
    if re.search(r"(?i)\b(table of contents?|contents|sumário|índice)\b", t[:400]) or re.search(r"(?i)SAMPLE ONLY|NOT TO BE USED", t):
        return None  # sumário (BV "Table of Content": filete sob cada título) / formulário-modelo (ABS)
    ls = R.linhas(pg)
    txt = [l["bb"] for l in ls]
    guia = [l["bb"] for l in ls if re.search(r"e-n-d|G-u-i-d-a-n-c-e|Guidance note", l["t"])]
    y0, y1 = 60, pg.rect.height - 60
    rs = [r for r in elementos_desenho(pg) if not any(r.contains(t) for t in txt)  # caixa/célula/faixa em volta de texto
          and not (r.height < 20 and any(r.intersects(g) for g in guia))  # moldura de "Guidance note" (DNV)
          and tuple(round(v) for v in r) not in ignorar]  # vinheta repetida
    rs = [r for r in rs if r.y1 > y0 and r.y0 < y1]  # logotipo/filete de cabeçalho e rodapé
    crops = [pymupdf.Rect(c) for c in crops]
    rs = [r for r in rs if not any((r & c).get_area() >= 0.6 * max(r.get_area(), 1) for c in crops)]  # já recortado
    if not rs or sum(r.get_area() for r in rs) < 0.02 * pg.rect.get_area():
        return None
    u = pymupdf.Rect(rs[0])
    for r in rs[1:]:
        u |= r
    return u


def processar(f, gravar):
    docs = docs_secao_v() if f["docs"] == "V" else f["docs"]
    pasta = f"assets/figuras/docs/{f['id']}"
    if gravar:
        os.makedirs(pasta, exist_ok=True)
    reqs, figs, normas, usados = [], [], [], set()
    for d in docs:
        if not os.path.exists(d["arq"]):
            print("  FALTA", d["arq"])
            continue
        pdf, its, body = R.itens(d["arq"])
        def tem_desenho(pg):
            t = pg.get_text()
            din = d.get("orgao") == "DIN"  # DIN: a 1ª página já é a norma (sem capa); escaneadas antigas = tabelas de dimensões
            if (pg.number < 2 and not din) or re.search(r"(?i)\b(foreword|contents|bibliography|pdf disclaimer|copyright protected|"
                                          r"british standards institution|national foreword|sumário|prefácio|bibliografia)\b", t[:1500]):
                return False  # capa, aviso, sumário, prefácio, bibliografia
            els = R.elementos(pg, pg.rect.height - 45)
            vetor = [r for r in els if r.width < pg.rect.width * 0.9 and not (r.height < 3 and r.y0 < 90)]  # sem filete de cabeçalho
            if len(vetor) >= 8 or [r for r in vetor if r.width > 40 and r.height > 40]:
                return True  # desenho ou grade de tabela em vetor (traços finos contam pela quantidade)
            escaneada = [r for r in els if r.width >= pg.rect.width * 0.9]
            if escaneada and (len(t.strip()) < 200 or din):
                return True  # página escaneada SEM camada de texto (ex. ISO 7379): não dá para saber — guarda
            dig, let = len(re.findall(r"\d", t)), len(re.findall(r"[A-Za-zÀ-ÿ]", t))
            return bool(escaneada) and dig > 60 and dig > 0.35 * let  # página escaneada com tabela de números (não texto corrido)
        com_item = {it["pagina"] for it in its}
        if d.get("sem_paginas_inteiras"):
            pass  # documento só de texto (caixas/faixas em volta de parágrafos contariam como "desenho")
        elif (not its and len(pdf) <= 40 and (d["arq"].startswith(OCR) or d.get("orgao") == "ABNT")) or (len(pdf) <= 25 and d.get("orgao") not in ("ASME", "ABNT", "DIN", "Petrobras")) or (len(pdf) <= 80 and d.get("orgao") == "DIN"):
            # norma curta: páginas com desenho/grade que não renderam nenhum item viram imagem inteira (ex. tabelas de
            # dimensões de parafusos sem título localizável; escaneadas). Páginas só de texto corrido ficam de fora.
            its += [{"tipo": "pagina", "num": str(i + 1), "titulo": f"Página {i + 1} (página inteira)", "texto": "", "pagina_inteira": True,
                     "pagina": i + 1, "bbox": pdf[i].rect + (20, 30, -20, -40)} for i in range(len(pdf))
                    if i + 1 not in com_item and tem_desenho(pdf[i])]
            its.sort(key=lambda it: it["pagina"])
        # página com DESENHO que nenhum recorte cobriu (desenho padrão sem legenda, figura sem título…): guarda a página inteira —
        # os PDFs de referencias/ vão sair do projeto e o desenho se perderia (o texto vai para dados/textos/)
        if not d.get("sem_paginas_inteiras"):
            ja = {it["pagina"] for it in its if it.get("pagina_inteira")}
            rep = repetidos(pdf)
            for i, pg in enumerate(pdf):
                if i + 1 in ja or (i == 0 and d.get("orgao") != "DIN") or R.escaneada(pg):
                    continue
                u = desenho_pagina(pg, [it["bbox"] for it in its if it["pagina"] == i + 1], rep)
                if u and u.get_area() >= 0.12 * pg.rect.get_area():
                    its.append({"tipo": "pagina", "num": str(i + 1), "titulo": f"Página {i + 1} (desenho sem título localizável)", "texto": "",
                                "pagina_inteira": True, "motivo": "desenho sem título localizável", "pagina": i + 1,
                                "bbox": pg.rect + (20, 30, -20, -40)})
            its.sort(key=lambda it: it["pagina"])
        normas.append({"id": d["id"], "titulo": d["titulo"], "edicao": d["edicao"], "orgao": d.get("orgao", "ASME"), "escopo": d["escopo"] or d["titulo"], "arquivo": d["arq"]})
        if f["agrupar"] == "documento":
            g = grupo_de({"num": ""}, d, "documento")
            reqs.append({"grupo": g, "parametro": "Documento", "valor": f"{d['titulo']} — edição {d['edicao']}; {len(pdf)} págs.; {len(its)} tabelas/figuras localizadas",
                         "norma": d["id"], "item": "—", "pagina": 1})
        for it in its:
            g = grupo_de(it, d, f["agrupar"])
            rot = {"tabela": "Tabela ", "figura": "Fig. ", "pagina": "pág. "}.get(it["tipo"], "") + it["num"]
            slug = re.sub(r"[^a-z0-9]+", "-", f"{d['id']}-p{it['pagina']}-{it['tipo'][0]}-{it['num']}".lower()).strip("-")
            k = 2
            while slug in usados:
                slug = re.sub(r"-\d+$", "", slug) + f"-{k}" if k > 2 else slug + f"-{k}"
                k += 1
            usados.add(slug)
            arq = f"docs/{f['id']}/{slug}.png"
            if gravar:
                R.salvar_1bit(pdf, it, f"assets/figuras/{arq}")
            tit = re.sub(r"\s+", " ", it["titulo"]).strip()
            figs.append({"arquivo": arq, "legenda": tit, "norma": d["id"], "item": rot, "pagina": it["pagina"], "grupo": g})
            nota = (f"Página inteira ({it.get('motivo') or 'texto do PDF ilegível/OCR'}). " if it.get("pagina_inteira") else "")
            if it["texto"]:
                nota += ("Texto (para busca; vale a imagem): " + it["texto"][:350] + ("…" if len(it["texto"]) > 350 else ""))
            r = {"grupo": g, "parametro": tit[:160], "valor": "ver imagem neste grupo", "norma": d["id"], "item": rot, "pagina": it["pagina"]}
            if nota:
                r["nota"] = nota
            reqs.append(r)
        print(f"  {d['id']}: {len(pdf)} págs., corpo {body} pt, {sum(i['tipo'] != 'figura' for i in its)} tabelas, {sum(i['tipo'] == 'figura' for i in its)} figuras")
    ordem = sorted({r["grupo"] for r in reqs}, key=ordem_grupo)
    reqs.sort(key=lambda r: ordem.index(r["grupo"]))
    return reqs, figs, normas


def gravar_ficha(f, reqs, figs, normas):
    arq = f"conteudo/docs/{f['id']}.json"  # fonte; as fichas por norma saem de ferramentas/separar_normas.py
    ant = json.load(open(arq, encoding="utf-8")) if os.path.exists(arq) else {}
    d = {"id": f["id"], "titulo": f["titulo"], "categoria": f["categoria"], "resumo": f["resumo"],
         "palavras_chave": ant.get("palavras_chave") or sorted({n["id"].replace("ASME-", "ASME ") for n in normas}) + ["tabela", "figura", "ASME"],
         "relacionadas": ant.get("relacionadas", []), "figuras": figs, "requisitos": reqs,
         "notas": ant.get("notas") or [{"tipo": "info", "texto": "Tabelas e figuras recortadas da norma em IMAGEM (sem transcrição), com item e página. O texto anexado serve só para a busca."}]}
    open(arq, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    p = "conteudo/normas.json"
    nn = json.load(open(p, encoding="utf-8"))
    ids = {x["id"]: x for x in nn}
    for x in normas:
        if x["id"] in ids:
            ids[x["id"]].update({k: v for k, v in x.items() if k != "id" and not ids[x["id"]].get(k)})
        else:
            nn.append(x)
    json.dump(nn, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("gravado", arq, len(reqs), "req.,", len(figs), "figuras")


if __name__ == "__main__":
    gravar = "--gravar" in sys.argv
    sel = [a for a in sys.argv[1:] if not a.startswith("--")]
    for f in FICHAS:
        if sel and f["id"] not in sel:
            continue
        print(f["id"])
        res = processar(f, gravar)
        if gravar:
            gravar_ficha(f, *res)
