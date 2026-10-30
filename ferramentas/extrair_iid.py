"""Extrai as tabelas de tensão admissível do ASME II-D 2019 (métrico) — Tabela 1A (ferrosos), 1B (não ferrosos), 3 (parafusos).

Cada grupo de páginas da tabela traz: identificação (composição, forma, spec, grau, UNS, classe, espessura, P-No., grupo),
propriedades (Su, Sy, limites de temperatura por seção, carta de pressão externa, notas) e as tensões S por temperatura
(1 ou 2 páginas). O nº da linha recomeça a cada grupo; as páginas do grupo são juntadas pelo nº da linha.

Palavras → linha pela proximidade vertical ao nº da linha. Identificação: colunas pelo menor x0 das palavras do cabeçalho.
Propriedades: regex sobre o texto da linha. Tensões: tokens em ordem = temperaturas do cabeçalho (confere a contagem).

uso: python -P ferramentas/extrair_iid.py <saida.json> [1A|1B|3 ...] [--gravar]
     --gravar reescreve o campo "tabelas" de conteudo/fichas/materiais-asme-ii-d.json (a ficha precisa existir)
"""
import glob
import json
import re
import sys

import pymupdf

PDF = glob.glob("referencias/extraido/ASME/ASME SECTION II PART D 2019*.pdf")[0]
FAIXAS = {"1A": (74, 217), "1B": (222, 345), "3": (464, 487), "U": (618, 717), "Y-1": (720, 923)}
COMUM = [("comp", ["Nominal", "Composition"]), ("forma", ["Product", "Form"]), ("spec", ["Spec."])]
LIM = r"(NP|…|\d+(?: \([^)]*\))?)"
CFG = {
    "1A": {"ident": COMUM + [("grau", ["Type/Grade"]), ("uns", ["Alloy", "Desig./", "UNS"]), ("classe", ["Class/", "Condition/", "Temper"]),
                             ("esp", ["Size/", "Thickness,", "mm"]), ("pno", ["P-No."]), ("grupo", ["Group"])],
           "pre": [], "props": ["su", "sy", "I", "III", "VIII-1", "XII", "carta", "notas"]},
    "1B": {"ident": COMUM + [("grau", ["Type/Grade"]), ("uns", ["Alloy", "Desig./UNS"]), ("classe", ["Class/Condition/", "Temper"])],
           "pre": [("esp", ["Size/Thickness,", "mm"]), ("pno", ["P-No."])], "props": ["su", "sy", "I", "III", "VIII-1", "XII", "carta", "notas"]},
    # Tabela 3 (2019): os cabeçalhos estão deslocados — sob "Size" vem o UNS, sob "Alloy" a classe, sob "Class" a espessura
    "3": {"ident": COMUM + [("grau", ["Type/", "Grade"]), ("uns", ["Size/", "Thickness,", "mm"]), ("classe", ["Alloy", "Desig./UNS"]),
                            ("esp", ["Class/", "Condition/", "Temper"], 14)],
          "pre": [], "props": ["su", "sy", "III", "VIII-1", "VIII-2", "XII", "notas"]},
    # Tabela U: Su mín. na própria página de identificação; depois Su × temperatura
    # mesmo deslocamento da Tabela 3: sob "Size" vem o UNS, sob "Alloy" a classe, sob "Class" a espessura
    "U": {"ident": COMUM + [("grau", ["Type/Grade"]), ("uns", ["Size/", "Thickness,", "mm"]), ("classe", ["Alloy", "Desig./UNS"]),
                            ("esp", ["Class/", "Condition/", "Temper"], 14), ("su", ["Min.", "MPa"])],
          "pre": [], "props": []},
    # Y-1: dados ~12 pt à esquerda dos cabeçalhos de spec/grau/classe
    "Y-1": {"ident": COMUM[:1] + [("forma", ["Product", "Form"], 18), ("spec", ["Spec."], 16), ("grau", ["Type/Grade"], 16), ("uns", ["Alloy", "Desig./UNS"], 8),
                                  ("classe", ["Class/Condition/", "Temper"], 12)],
            "pre": [("esp", ["Size/Thickness,", "mm"])], "props": ["su", "sy", "notas"]},
}


def rx_props(nomes):
    """Su, Sy, limites (NP | nº | nº (obs.)), [carta], notas."""
    lims = [n for n in nomes if n not in ("su", "sy", "carta", "notas")]
    r = r"^(\S+) (\S+)" + "".join(" " + LIM for _ in lims) + (r" (\S+)" if "carta" in nomes else "") + r" (.+)$"
    return re.compile(r)


FRAC = {"1/2": "½", "1/4": "¼", "3/4": "¾"}
LIXO = re.compile(r"^[-`,]+$|^#$|^ð19Þ$|^(Ferrous|Nonferrous|Materials|\(Cont'd\))$")


def palavras(pg):
    return [w for w in pg.get_text("words") if not LIXO.match(w[4]) and "``" not in w[4] and "ð19Þ" not in w[4]]


def linhas(ws, xs_linha, y_dados):
    """{nº: [palavras]} — cada palavra vai para o nº de linha mais próximo na vertical."""
    nums = sorted([w for w in ws if re.fullmatch(r"\d+", w[4]) and abs(w[0] - xs_linha) < 10 and w[1] > y_dados], key=lambda w: w[1])
    out = {int(n[4]): [] for n in nums}
    for w in ws:
        if w[1] <= y_dados or w[0] < xs_linha + 12 or w in nums:
            continue
        yc = (w[1] + w[3]) / 2
        n = min(nums, key=lambda n: abs((n[1] + n[3]) / 2 - yc))
        if abs((n[1] + n[3]) / 2 - yc) < 12:
            out[int(n[4])].append(w)
    return out


def colunas(banda, cab):
    """[(nome, x da fronteira esquerda)]; folga padrão 6 pt (3º elemento opcional para dados centralizados e largos)."""
    return [(c[0], min(w[0] for w in banda if w[4] in c[1]) - (c[2] if len(c) > 2 else 6)) for c in cab]


def por_coluna(ww, cols):
    reg = {}
    for w in sorted(ww, key=lambda w: (round(w[1] / 4), w[0])):  # "≤" fica ~0,3 pt acima da linha
        j = max(i for i, (_, f) in enumerate(cols) if w[0] >= f or i == 0)
        reg.setdefault(cols[j][0], []).append(w[4])
    return {k: " ".join(v) for k, v in reg.items()}


def ler_pagina(pg, cfg):
    ws = palavras(pg)
    txt = pg.get_text()
    line = min((w for w in ws if w[4] == "Line"), key=lambda w: w[1])
    no = min((w for w in ws if w[4] == "No." and w[1] > line[1] and abs(w[0] - line[0]) < 8), key=lambda w: w[1])
    y_dados = no[3]
    xs = line[0]
    rows = linhas(ws, xs, y_dados)
    banda = [w for w in ws if line[1] - 30 < w[1] < y_dados]
    res = {}
    if "Nominal" in txt and "Composition" in txt:
        cols = colunas(banda, cfg["ident"])
        for ln, ww in rows.items():
            res[ln] = por_coluna(ww, cols)
            u = res[ln].get("uns", "").split()
            if len(u) > 1 and not re.fullmatch(r"[A-Z]\d{5}|…", u[-1]):  # "Solution ann." centralizado invade a coluna UNS
                k = max(i for i, x in enumerate(u) if re.fullmatch(r"[A-Z]\d{5}|…", x)) + 1 if any(re.fullmatch(r"[A-Z]\d{5}|…", x) for x in u) else 0
                res[ln]["uns"] = " ".join(u[:k]) or "…"
                res[ln]["classe"] = " ".join(u[k:] + [c for c in [res[ln].get("classe")] if c and c != "…"])
            m = re.match(r"^(\S+) (SA/\S+)$", res[ln].get("spec", ""))  # "SA/EN 10028–3" quebra em 2 linhas
            if m:
                res[ln]["spec"] = m.group(2) + " " + m.group(1)
            for k in ("comp", "grau"):  # frações em sobrescrito/subscrito: "13/4Cr–1/2Mo" = 1¾Cr–½Mo
                if k in res[ln]:
                    res[ln][k] = re.sub(r"([13])/([24])", lambda m: FRAC[m.group(0)], res[ln][k])
            m = re.match(r"^(.*?) ?(Smls\.|Wld\.|Cond\.)$", res[ln].get("comp", ""))  # forma em 2 linhas invade a composição
            if m:
                res[ln]["comp"] = m.group(1) or "…"
                res[ln]["forma"] = m.group(2) + " " + res[ln].get("forma", "")
            if res[ln].get("spec", "…") == "…":  # linha vazia (só "…") — separador da norma
                res[ln]["vazia"] = True
        return "ident", res, []
    if "Exceeding" not in txt:  # página de propriedades (Su, Sy, limites, notas)
        erros = []
        rx = rx_props(cfg["props"])
        x_su = min(w[0] for w in banda if w[4] == "Tensile") - 8
        cols = colunas(banda, cfg["pre"]) if cfg["pre"] else []
        for ln, ww in rows.items():
            pre = por_coluna([w for w in ww if w[0] < x_su], cols) if cols else {}
            t = " ".join(w[4] for w in sorted((w for w in ww if w[0] >= x_su), key=lambda w: w[0]))
            m = rx.match(t)
            if not m:
                erros.append((ln, t))
                continue
            res[ln] = dict(pre, **dict(zip(cfg["props"], m.groups())))
        return "props", res, erros
    temps = [w for w in banda if re.fullmatch(r"-?\d{2,3}", w[4]) and abs(w[1] - no[1]) < 4 and w[0] > xs + 12]
    temps = sorted(temps, key=lambda w: w[0])
    nomes = [w[4] for w in temps]
    erros = []
    for ln, ww in rows.items():
        # valor de cada coluna = palavras cujo centro x cai mais perto do centro da temperatura
        reg = {}
        for w in ww:
            if not re.fullmatch(r"…|\d+([.,]\d+)?", w[4]):  # títulos internos ("Ferrous Materials (Cont'd)")
                continue
            w = w[:4] + (w[4].replace(",", "."),) + w[5:]  # algumas linhas usam vírgula decimal (ex. Y-1 SB-241, pág. 858)
            xc = (w[0] + w[2]) / 2
            k = min(range(len(temps)), key=lambda i: abs((temps[i][0] + temps[i][2]) / 2 - xc))
            reg.setdefault(nomes[k], []).append(w[4])
        if any(len(v) != 1 for v in reg.values()) or len(reg) != len(nomes):
            erros.append((ln, {k: v for k, v in reg.items()}))
        res[ln] = {k: " ".join(v) for k, v in reg.items()}
    return "S", res, erros


def extrair(tab):
    d = pymupdf.open(stream=open(PDF, "rb").read(), filetype="pdf")
    a, b = FAIXAS[tab]
    regs, grupo, erros = [], None, []
    for p in range(a, b + 1):
        pg = d[p - 1]
        t = pg.get_text()
        if "INTENTIONALLY LEFT BLANK" in t or "Line" not in t:
            continue
        tipo, res, err = ler_pagina(pg, CFG[tab])
        erros += [(p, *e) for e in err]
        if tipo == "ident":
            grupo = {ln: dict(v, linha=ln, pag_ident=p, S={}) for ln, v in res.items()}
            regs.append(grupo)
            continue
        for ln, v in res.items():
            r = grupo.get(ln)
            if r is None:
                erros.append((p, ln, "linha sem identificação"))
                continue
            if tipo == "props":
                r.update(v, pag_props=p)
            else:
                r["S"].update(v)
                r.setdefault("pag_S", []).append(p)
    out = [r for g in regs for r in g.values() if not r.get("vazia")]
    return out, erros


NOTAS_PAG = {"1A": (218, 220), "1B": (346, 348), "3": (488, 489), "U": (718, 718), "Y-1": (924, 924)}
NOME_TAB = {"1A": "1A — S ferrosos", "1B": "1B — S não ferrosos", "3": "3 — S parafusos", "U": "U — Su × temperatura", "Y-1": "Y-1 — Sy × temperatura"}
VALOR = {"1A": "S", "1B": "S", "3": "S", "U": "Su", "Y-1": "Sy"}  # o que as colunas de temperatura trazem
DESCR = {"S": "S = tensão máxima admissível em tração (MPa) na temperatura do metal até o valor indicado; '…' = não permitido / sem valor. "
              "Temp. máx.: limite de aplicação por Seção do código (NP = não permitido; SPT = só suportes).",
         "Su": "Su = resistência à tração (MPa) na temperatura — valores de curva de tendência, para uso em projeto onde o código pede Su(T); não são mínimos garantidos de ensaio.",
         "Sy": "Sy = limite de escoamento (MPa) na temperatura — valores de curva de tendência, para uso em projeto onde o código pede Sy(T)."}
NORMA = "ASME-II-D-2019"


def notas(tab):
    """{código: texto} das notas da tabela (gerais (a)…, G, S, T, W, H…)."""
    d = pymupdf.open(stream=open(PDF, "rb").read(), filetype="pdf")
    a, b = NOTAS_PAG[tab]
    out, pag = {}, {}
    for p in range(a, b + 1):
        ls = [l.strip() for l in d[p - 1].get_text().split("\n")]
        ls = [l for l in ls if l and not re.match(r"^(\d{3}|ASME BPVC|ð19Þ|NOTES|Copyright|--`|Provided by|Licensee|Not for Resale|No reproduction|INTENTIONALLY)", l)]
        cod = None
        for l in ls:
            m = re.match(r"^(\([a-z]\)|[A-Z]{1,2}\d{1,2})(?:\s+(.*))?$", l)
            if m and (m.group(1).startswith("(") or m.group(2) is None or m.group(2)[:1].isupper()):
                cod = m.group(1)
                out[cod] = m.group(2) or ""
                pag[cod] = p
            elif cod:
                out[cod] = (out[cod] + " " + l).strip()
    res = {}
    for k, v in out.items():
        v = re.sub(r"\s+", " ", v)
        partes = re.split(r" NOTES?:? \((\d+)\) ", v)  # "NOTE (1) …" no fim de uma nota geral (Tabela Y-1)
        res[k] = (partes[0], pag[k])
        for i in range(1, len(partes), 2):
            res[f"({partes[i]})"] = (partes[i + 1], pag[k])
    return res


def sem_pag(tabelas):
    """o site não mostra página (os PDFs de referencias/ saem): tira a coluna "Pág." e a frase que a explicava."""
    for t in tabelas:
        if "Pág." in t["colunas"]:
            k = t["colunas"].index("Pág.")
            t["colunas"].pop(k)
            for l in t["linhas"]:
                l.pop(k)
        if t.get("nota"):
            t["nota"] = re.sub(r'Págs\. de identificação: [^;]*; coluna "Pág\." = [^.]*\. ?', "", t["nota"])


def gravar(dados):
    """Gera conteudo/fichas/materiais-asme-ii-d.json (tabelas por especificação + notas)."""
    def norm_spec(sp):
        return sp.replace("–", "-")

    def chave_spec(sp):
        m = re.search(r"(\d+)", sp)
        return (0 if re.match(r"S[ABF]-\d", sp) else 1, int(m.group(1)) if m else 0, sp)

    temps_all = {}
    tabelas, specs = [], set()
    for tab, rr in dados.items():
        lims = {"3": ["III", "VIII-1", "VIII-2", "XII"], "1A": ["I", "III", "VIII-1", "XII"], "1B": ["I", "III", "VIII-1", "XII"]}.get(tab, [])
        v = VALOR[tab]
        com_pno, com_carta, com_sy, com_notas = tab in ("1A", "1B"), tab in ("1A", "1B"), tab != "U", tab != "U"
        por_spec = {}
        for r in rr:
            por_spec.setdefault(norm_spec(r["spec"]), []).append(r)
        for sp in sorted(por_spec, key=chave_spec):
            rs = por_spec[sp]
            specs.add(sp)
            temps = [t for t in sorted(rs[0]["S"], key=int) if any(x["S"].get(t, "…") not in ("…", "") for x in rs)]
            cols = (["Grau / classe / espessura · forma", "Composição nominal", "UNS"] + (["P-No. / grupo"] if com_pno else [])
                    + ["Su mín. (MPa)"] + (["Sy mín. (MPa)"] if com_sy else []) + [f"Temp. máx. {s} (°C)" for s in lims]
                    + (["Carta pressão externa"] if com_carta else []) + (["Notas"] if com_notas else []) + ["Pág."] + [f"{v} a {t} °C" for t in temps])
            linhas, vistos = [], {}
            for x in rs:
                g = x.get("grau") if x.get("grau") not in (None, "…") else x.get("uns")  # sem tipo/grau: identifica pelo UNS
                partes = [v for v in (g, x.get("classe"), x.get("esp")) if v and v != "…"]
                rot = " · ".join(v for v in (" ".join(partes), x.get("forma", "")) if v) or "—"
                vistos[rot] = vistos.get(rot, 0) + 1
                linhas.append([rot, x, x["pag_ident"]])
            for l in linhas:  # rótulos repetidos (ex. 2 conjuntos de S do inox) → acrescenta as notas
                if vistos[l[0]] > 1 and l[1].get("notas", "…") != "…":
                    l[0] = f"{l[0]} · notas {l[1]['notas']}"
            cont = {}
            for l in linhas:
                cont[l[0]] = cont.get(l[0], 0) + 1
            for l in linhas:  # ainda repetido → linha e página da norma
                if cont[l[0]] > 1:
                    l[0] = f"{l[0]} · linha {l[1]['linha']} (p{l[2]})"
            def num(v):
                try:
                    return int(v) if re.fullmatch(r"\d+", v) else float(v)
                except (TypeError, ValueError):
                    return v if v not in (None, "") else "…"
            out = []
            for rot, x, pg in linhas:
                pg_s = ", ".join(str(q) for q in x.get("pag_S", []))
                out.append([rot, x.get("comp", "…"), x.get("uns", "…")] + ([f"{x.get('pno', '…')} / {x.get('grupo', '…')}"] if com_pno else [])
                           + [num(x.get("su"))] + ([num(x.get("sy"))] if com_sy else []) + [x.get(s, "…") for s in lims]
                           + ([x.get("carta", "…")] if com_carta else []) + ([x.get("notas", "…")] if com_notas else []) + [f"{pg}; {v}: {pg_s}"]
                           + [num(x["S"].get(t, "…")) for t in temps])
            pags = sorted({x["pag_ident"] for x in rs})
            formas = sorted({x.get("forma", "") for x in rs})
            tabelas.append({
                "id": f"iid-{tab.lower()}-{sp.lower().replace('/', '-').replace(' ', '-')}",
                "titulo": f"{sp} — {', '.join(formas)} (Tabela {tab})",
                "norma": NORMA, "item": f"Tabela {tab}", "pagina": pags[0], "unidade": "MPa / °C",
                "chave": {"tabela": NOME_TAB[tab], "spec": sp},
                "colunas": cols, "linhas": out,
                "nota": (f"Págs. de identificação: {', '.join(map(str, pags))}; coluna \"Pág.\" = página de identificação e páginas dos valores de cada linha. "
                         + DESCR[v] + " Notas: ver tabela de notas da Tabela " + tab + "."),
            })
            temps_all[tab] = temps
    for tab in dados:
        nn = notas(tab)
        tabelas.append({"id": f"iid-notas-{tab.lower()}", "titulo": f"Notas da Tabela {tab} (códigos G, S, T, W…)", "norma": NORMA,
                        "item": f"Notas da Tabela {tab}", "pagina": NOTAS_PAG[tab][0], "unidade": "", "chave": {}, "consulta": False,
                        "colunas": ["Nota", "Texto (inglês, como na norma)", "Pág."],
                        "linhas": [[k, v, p] for k, (v, p) in nn.items()]})
    sem_pag(tabelas)
    f = "conteudo/fichas/materiais-asme-ii-d.json"
    d = json.load(open(f, encoding="utf-8"))
    d["tabelas"] = tabelas
    kws = [s for s in sorted(specs, key=chave_spec)]
    d["palavras_chave"] = [k for k in d["palavras_chave"] if not re.match(r"^S[ABF][-/]", k)] + kws
    open(f, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("gravado:", len(tabelas), "tabelas,", sum(len(t["linhas"]) for t in tabelas), "linhas")


if __name__ == "__main__":
    out = {}
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    for t in args or ["1A", "1B", "3"]:
        rr, err = extrair(t)
        out[t] = rr
        print(t, len(rr), "linhas;", len(err), "problemas")
        for e in err[:40]:
            print("  ", e)
    json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if "--gravar" in sys.argv:
        gravar(out)
