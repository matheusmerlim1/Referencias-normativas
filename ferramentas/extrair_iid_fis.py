"""Extrai as propriedades físicas do ASME II-D 2019 (métrico), Subparte 2, e grava a ficha propriedades-fisicas-asme-ii-d.

- TE-1…TE-5 (expansão térmica: A instantâneo, B médio desde 20 °C, C dilatação mm/m) e TCD (condutividade TC e difusividade TD):
  tabelas com GRUPOS de colunas; a sub-linha "A B C" / "TC TD" define as colunas e o nome de cada grupo vem das palavras
  do cabeçalho mais próximas na horizontal.
- TM-1…TM-5 (módulo de elasticidade) e PRD (Poisson e densidade): linhas "material + valores" no texto corrido.

uso: python -P ferramentas/extrair_iid_fis.py [--gravar]
"""
import glob
import json
import re
import sys

import pymupdf

PDF = glob.glob("referencias/extraido/ASME/ASME SECTION II PART D 2019*.pdf")[0]
NORMA = "ASME-II-D-2019"
NUM = re.compile(r"^[−-]?\d+(\.\d+)?$|^\.\.\.$|^…$")
FRAC = {"1/2": "½", "1/4": "¼", "3/4": "¾", "1/3": "⅓", "1/5": "⅕"}


def frac(t):
    return re.sub(r"\b([1-9])?([13])/([2-5])", lambda m: (m.group(1) or "") + FRAC.get(f"{m.group(2)}/{m.group(3)}", m.group(0)[len(m.group(1) or ""):]), t)


def doc():
    return pymupdf.open(stream=open(PDF, "rb").read(), filetype="pdf")


def linhas_y(ws, tol=3):
    """agrupa palavras em linhas pela coordenada y."""
    out = []
    for w in sorted(ws, key=lambda w: (w[1], w[0])):
        if out and abs(out[-1][0] - w[1]) <= tol:
            out[-1][1].append(w)
        else:
            out.append([w[1], [w]])
    return [(y, sorted(l, key=lambda w: w[0])) for y, l in out]


def grupos_pagina(pg):
    """→ blocos {sub: ["A","B","C"], grupos: [nome...], linhas: [[T, v...]]} da página (TE / TCD).
    Página com 2 tabelas lado a lado (TE-5): processa cada metade."""
    ws = [w for w in pg.get_text("words") if "``" not in w[4] and w[4] not in ("ð19Þ", "(Cont'd)", "(Cont’d)")]
    tabs = [w for w in ws if w[4] == "Table"]
    if len(tabs) >= 2 and abs(tabs[0][1] - tabs[1][1]) < 3:
        meio = pg.rect.width / 2 - 10
        return blocos(pg, [w for w in ws if w[0] < meio]) + blocos(pg, [w for w in ws if w[0] >= meio])
    return blocos(pg, ws)


def blocos(pg, ws):
    ls = linhas_y(ws)
    out, y_ini = [], 0
    tabs = [w[1] for w in ws if w[4] == "Table"]
    for i, (y, l) in enumerate(ls):
        l = [w for w in l if w[4] not in ("Temperature,", "°C", "Temp.,", "°C,")]  # "Temperature, °C" fica na mesma linha de "A B C"
        tx = [w[4] for w in l]
        if not (set(tx) <= {"A", "B", "C"} or set(tx) <= {"TC", "TD"}) or len(tx) < 2:
            continue
        m = 3 if tx[0] == "A" else 2
        sub = tx[:m]
        xs = [(w[0] + w[2]) / 2 for w in l]
        ng = len(xs) // m
        centros = [sum(xs[k * m:(k + 1) * m]) / m for k in range(ng)]
        x_esq = l[0][0] - 25
        topo = max([t for t in tabs if t < y] or [0]) + 14
        topo = max(topo, y_ini)
        cab = [w for w in ws if topo < w[1] < y - 1 and (w[0] + w[2]) / 2 > x_esq
               and w[4] not in ("Temperature,", "°C", "Temp.,", "Expansion", "Thermal")]
        nomes = [[] for _ in range(ng)]
        for _, lc in linhas_y(cab, 2.5):
            for w in lc:
                k = min(range(ng), key=lambda k: abs(centros[k] - (w[0] + w[2]) / 2))
                nomes[k].append(w[4])
        # linhas de temperatura: 1ª palavra numérica na coluna de temperatura (à esquerda da 1ª subcoluna)
        x_t = l[0][0] - 8
        temps = []
        for y2, l2 in ls[i + 1:]:
            esq = [w for w in l2 if w[2] < x_t]
            if esq:
                if not re.fullmatch(r"[−-]?\d+", esq[0][4]):
                    break
                temps.append((y2, esq[0][4].replace("−", "-")))
        y_fim = temps[-1][0] + 6 if temps else y
        dados = {t: [None] * (ng * m) for _, t in temps}
        for w in ws:  # cada valor vai para a linha de temperatura mais próxima (grupos podem vir desalinhados, ex. pág. 928)
            if not (y < w[1] <= y_fim) or w[2] < x_t or not NUM.match(w[4]):
                continue
            yt, t = min(temps, key=lambda q: abs(q[0] - w[1]))
            j = min(range(len(xs)), key=lambda j: abs(xs[j] - (w[0] + w[2]) / 2))
            dados[t][j] = w[4]
        y_ini = y_fim
        out.append({"sub": sub, "grupos": [frac(re.sub(r"\s+", " ", " ".join(n)).replace("(In- cluding", "(Including")) for n in nomes],
                    "linhas": [[t] + dados[t] for _, t in temps], "y": y})
    return out


def tab_grupos(paginas, nome_tab):
    d = doc()
    out = []
    for p in paginas:
        for b in grupos_pagina(d[p - 1]):
            m = len(b["sub"])
            for k, g in enumerate(b["grupos"]):
                linhas = [[l[0]] + [num(v) for v in l[1 + k * m:1 + (k + 1) * m]] for l in b["linhas"]]
                out.append({"tab": nome_tab, "grupo": g, "pag": p, "sub": b["sub"], "linhas": linhas})
    return out


def num(v):
    if v in (None, "...", "…"):
        return "…"
    v = v.replace("−", "-")
    return int(v) if re.fullmatch(r"-?\d+", v) else float(v)


def tab_linhas(paginas, ncol=None, inicio=None, fim=("NOTES", "GENERAL NOTE", "NOTE:")):
    """Tabelas 'material + valores' (TM, PRD). ncol=None: temperaturas lidas do cabeçalho."""
    d = doc()
    ls = []
    for p in paginas:
        t = d[p - 1].get_text().split("\n")
        if inicio:
            k = next((i for i, x in enumerate(t) if x.strip().startswith(inicio)), None)
            if k is None:
                continue
            t = t[k:]
        t = [x.strip() for x in t]
        for k, x in enumerate(t):
            vizinhos = t[max(0, k - 1):k] + t[k + 1:k + 2]
            if re.fullmatch(r"\d{3}", x) and any(v.startswith("ASME BPVC") for v in vizinhos):  # nº da página impressa
                continue
            if x and not re.match(r"^(ASME BPVC|ð19Þ|Copyright|Provided by|Licensee|Not for Resale|No reproduction|--`)", x):
                ls.append((p, x))
    temps = []
    i = 0
    if ncol is None:
        while i < len(ls) and not re.fullmatch(r"[−-]?\d+", ls[i][1]):
            i += 1
        while i < len(ls) and re.fullmatch(r"[−-]?\d+", ls[i][1]):
            temps.append(ls[i][1].replace("−", "-"))
            i += 1
        ncol = len(temps)
    rows, buf, sec = [], [], ""
    while i < len(ls):
        p, x = ls[i]
        if x.startswith(fim) or re.match(r"^Table (TM|PRD|TE)", x) and rows:
            if x.startswith(fim):
                break
        if NUM.match(x):
            vals = [x]
            while len(vals) < ncol and i + 1 < len(ls) and NUM.match(ls[i + 1][1]):
                i += 1
                vals.append(ls[i][1])
            if buf:
                nome = " ".join(buf)
                cab = [b for b in buf if re.search(r"(Base|Materials|Alloys)( \(Cont'd\))?$", b)]
                if cab:
                    sec = re.sub(r" \(Cont'd\)$", "", cab[-1])
                    nome = " ".join(b for b in buf if b not in cab)
                rows.append({"sec": sec, "nome": frac(nome), "pag": p, "vals": [num(v) for v in vals]})
            buf = []
        elif not (re.match(r"^(Table |Moduli|Modulus|Poisson|Material Grade|Grade/UNS)", x) or x in ("Material", "Materials", "Ratio", "Density,", "kg/m3", "Poisson’s")
                  or "Value Given" in x):
            buf.append(x)
        i += 1
    return temps, rows


def notas_grupos(paginas, fim=None):
    """{"(n)": texto} das notas numeradas a partir de "NOTES" (listas de ligas de cada grupo)."""
    d = doc()
    t = "\n".join(d[p - 1].get_text() for p in paginas)
    t = t[t.index("NOTES"):]
    if fim and fim in t:
        t = t[:t.index(fim)]
    ls = [x.strip() for x in t.split("\n")]
    ls = [x for k, x in enumerate(ls) if x and not re.match(r"^(ASME BPVC|ð19Þ|Copyright|Provided by|Licensee|Not for Resale|No reproduction|--`|NOTES|Table T|Moduli|Thermal|Nominal Coeff)", x)
          and not (re.fullmatch(r"\d{3}", x) and k + 1 < len(ls) and ls[k + 1].startswith("ASME"))]
    out, cod = {}, None
    for x in ls:
        m = re.match(r"^\((\d+)\)\s*(.*)$", x)
        if m:
            cod = f"({m.group(1)})"
            out[cod] = [m.group(2)] if m.group(2) else []
        elif cod:
            out[cod].append(x)
    res = {}
    for k, v in out.items():
        txt = v[0] if v else ""
        resto = v[1:]
        res[k] = frac((txt + " " + "; ".join(resto)).strip().replace(":;", ":").replace("  ", " "))
    return res


def gravar():
    TE = [("TE-1", range(927, 932), "TE-1 — expansão térmica (ferrosos)"), ("TE-2", [932], "TE-2 — expansão térmica (alumínio)"),
          ("TE-3", [933], "TE-3 — expansão térmica (cobre)"), ("TE-4", range(934, 944), "TE-4 — expansão térmica (níquel)"),
          ("TE-5", [944], "TE-5 — expansão térmica (titânio)"), ("TCD", range(945, 957), "TCD — condutividade e difusividade térmica")]
    COLS = {("A", "B", "C"): ["A — coef. instantâneo (10⁻⁶ mm/mm/°C)", "B — coef. médio de 20 °C até T (10⁻⁶ mm/mm/°C)", "C — dilatação linear de 20 °C até T (mm/m)"],
            ("TC", "TD"): ["TC — condutividade térmica (W/m·°C)", "TD — difusividade térmica (10⁻⁶ m²/s)"]}
    tabelas = []
    for tab, pags, rot in TE:
        juntos = {}
        for g in tab_grupos(pags, tab):
            nome = re.sub(r"^Coefficients for ", "", g["grupo"]).strip()
            k = (nome, tuple(g["sub"]))
            if k in juntos:  # TE-5: mesma tabela continua na metade direita da página
                juntos[k]["linhas"] += g["linhas"]
            else:
                juntos[k] = dict(g, grupo=nome)
        for (nome, sub), g in juntos.items():
            tabelas.append({"id": f"iid-{tab.lower()}-{len(tabelas)}", "titulo": f"{tab} — {nome}", "norma": NORMA, "item": f"Tabela {tab}",
                            "pagina": g["pag"], "unidade": "", "chave": {"tabela": rot, "grupo": nome},
                            "colunas": ["Temperatura (°C)"] + COLS[sub], "linhas": g["linhas"]})
    TM = [("TM-1", range(959, 962), "TM-1 — módulo E (ferrosos)"), ("TM-2", [962], "TM-2 — módulo E (alumínio)"), ("TM-3", [963], "TM-3 — módulo E (cobre)"),
          ("TM-4", [964], "TM-4 — módulo E (níquel)"), ("TM-5", [965], "TM-5 — módulo E (titânio e zircônio)")]
    for tab, pags, rot in TM:
        temps, rows = tab_linhas(pags)
        tabelas.append({"id": f"iid-{tab.lower()}", "titulo": f"{tab} — módulo de elasticidade E (× 10³ MPa = GPa)", "norma": NORMA, "item": f"Tabela {tab}",
                        "pagina": pags[0], "unidade": "GPa", "chave": {"tabela": rot},
                        "colunas": ["Material"] + [f"E a {t} °C" for t in temps],
                        "linhas": [[(r["sec"] + " — " if r["sec"] else "") + r["nome"]] + r["vals"] for r in rows]})
    _, rows = tab_linhas([965, 966], ncol=2, inicio="Table PRD")
    tabelas.append({"id": "iid-prd", "titulo": "PRD — coeficiente de Poisson e densidade", "norma": NORMA, "item": "Tabela PRD", "pagina": 965,
                    "unidade": "", "chave": {"tabela": "PRD — Poisson e densidade"}, "colunas": ["Material", "Classe", "Coef. de Poisson", "Densidade (kg/m³)"],
                    "linhas": [[r["nome"], r["sec"], r["vals"][0], r["vals"][1]] for r in rows]})
    for tab, pags, fim, pag in (("TE-1", [931, 932], "Table TE-2", 931), ("TE-3", [933], None, 933), ("TCD", [957, 958], None, 957), ("TM-1", [959, 960, 961], None, 959)):
        nn = notas_grupos(pags, fim)
        tabelas.append({"id": f"iid-notas-{tab.lower()}", "titulo": f"Notas da Tabela {tab} — composição de cada grupo", "norma": NORMA,
                        "item": f"Notas da Tabela {tab}", "pagina": pag, "unidade": "", "chave": {}, "consulta": False,
                        "colunas": ["Nota", "Texto (inglês, como na norma)"], "linhas": [[k, v] for k, v in nn.items()]})
    f = "conteudo/fichas/propriedades-fisicas-asme-ii-d.json"
    d = json.load(open(f, encoding="utf-8"))
    d["tabelas"] = tabelas
    open(f, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("gravado:", len(tabelas), "tabelas,", sum(len(t["linhas"]) for t in tabelas), "linhas")


if __name__ == "__main__":
    if "--gravar" in sys.argv:
        gravar()
    else:
        for tab, pags in (("TE-1", range(927, 932)), ("TE-2", [932]), ("TE-3", [933]), ("TE-4", range(934, 944)), ("TE-5", [944]), ("TCD", range(945, 957))):
            for g in tab_grupos(pags, tab):
                print(g["tab"], g["pag"], g["sub"], len(g["linhas"]), "|", g["grupo"][:90])
