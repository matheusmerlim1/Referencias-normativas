"""Extrai as tabelas da ASME B16.5-2017 (dimensões, furação/parafusos, P-T) do texto por página
gerado por dump.py e grava o campo "tabelas" de conteudo/fichas/flange-asme-b16-5.json.
Também confere as tabelas em mm contra as equivalentes em polegadas (Apêndice Obrigatório II)
e as P-T em bar contra as em psi.

Uso:  python -P ferramentas/extrair_b165.py [<arquivo .txt do dump>] [--gravar]
      (padrão: %TEMP%/uva_b165/ASME_B16_5_2017_-_PIPE_F_c7763c.txt; sem --gravar só verifica)
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHA = os.path.join(RAIZ, "conteudo", "fichas", "flange-asme-b16-5.json")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
TXT = args[0] if args else os.path.join(os.environ.get("TEMP", "/tmp"), "uva_b165", "ASME_B16_5_2017_-_PIPE_F_c7763c.txt")
GRAVAR = "--gravar" in sys.argv

paginas = {}
cur = None
for ln in open(TXT, encoding="utf-8").read().splitlines():
    m = re.fullmatch(r"=====PAGE (\d+)=====", ln.strip())
    if m:
        cur = int(m.group(1)); paginas[cur] = []
    elif cur is not None and ln.strip():
        paginas[cur].append(ln.strip())

# ---------------- NPS ----------------
NPS_TODOS = ["1∕2", "3∕4", "1", "11∕4", "11∕2", "2", "21∕2", "3", "31∕2", "4", "5", "6", "8", "10", "12",
             "14", "16", "18", "20", "22", "24"]
ESPERADO = {
    "150": NPS_TODOS, "300": NPS_TODOS, "400": NPS_TODOS, "600": NPS_TODOS,
    "900": [n for n in NPS_TODOS if n not in ("31∕2", "22")],
    "1500": [n for n in NPS_TODOS if n not in ("31∕2", "22")],
    "2500": NPS_TODOS[:NPS_TODOS.index("12") + 1][:8] + ["4", "5", "6", "8", "10", "12"],
}


def frac(t):
    """'11∕8' -> '1 1/8'; '5∕8' -> '5/8'; '2' -> '2'."""
    m = re.fullmatch(r"(\d+)∕(\d+)", t)
    if not m:
        return t
    num, den = m.groups()
    if len(num) > 1:
        return f"{num[:-1]} {num[-1]}/{den}"
    return f"{num}/{den}"


def frac_val(s):
    p = s.split()
    v = 0.0
    for x in p:
        if "/" in x:
            a, b = x.split("/"); v += int(a) / int(b)
        else:
            v += float(x)
    return v


def valor(t):
    """Token da tabela -> valor JSON."""
    if t == "…":
        return "—"
    m = re.fullmatch(r"Note \((\d+)\)", t)
    if m:
        return f"Nota ({m.group(1)})"
    if "∕" in t:
        return frac(t)
    s = t.replace(",", "").replace(" ", "")
    if re.fullmatch(r"\d+\.\d*O\d*", s):   # letra O no lugar de zero (erro tipográfico do PDF)
        TIPOS.append(f"token {t!r} lido como {s.replace('O', '0')}")
        s = s.replace("O", "0")
    if re.fullmatch(r"\d+", s):
        return int(s)
    if re.fullmatch(r"\d+\.\d+", s):
        return float(s)
    raise ValueError(f"token inesperado: {t!r}")


TIPOS = []
PARA = ("GENERAL NOTE", "NOTES", "NOTE:", "ASME B16.5-2017", "Dit document")


def tokens_dados(pg):
    tk = paginas[pg]
    i = next(k for k, t in enumerate(tk) if re.search(r"Dimensions of Class|Templates for Drilling", t))
    i += 1
    n = 1
    while i < len(tk) and tk[i] == str(n):
        i += 1; n += 1
    while i < len(tk) and tk[i] not in NPS_TODOS:
        i += 1
    fim = i
    while fim < len(tk) and not tk[fim].startswith(PARA):
        fim += 1
    return tk[i:fim]


# Células EM BRANCO no PDF (nem valor nem "…"), conferidas na imagem da página: (tabela, NPS) -> coluna (0 = NPS)
LACUNAS = {
    ("20", "20"): 14,     # Tabela 20, pág. 121, NPS 20, coluna 14 (Q) vazia
}
LACUNAS_ACHADAS = []


def parse_tabela(pags, classe, ncol, tab=None):
    tk = [t for p in pags for t in tokens_dados(p)]
    esperado = ESPERADO[classe]
    linhas, aviso, i = [], None, 0
    for k, nps in enumerate(esperado):
        if i >= len(tk) or tk[i] != nps:
            raise ValueError(f"classe {classe} págs {pags}: esperado NPS {nps}, achado {tk[i:i+3]}")
        i += 1
        txt = None
        while i < len(tk) and tk[i].startswith("Use Class"):
            txt = tk[i]; aviso = tk[i]; i += 1
        prox = esperado[k + 1] if k + 1 < len(esperado) else None
        if txt or (i < len(tk) and tk[i] == prox) or i >= len(tk):
            linhas.append([frac(nps), None] + ["—"] * (ncol - 2))   # "use class X": preenchido abaixo
            continue
        lac = LACUNAS.get((tab, frac(nps)))
        n = ncol - 1 - (1 if lac else 0)
        vals = [valor(t) for t in tk[i:i + n]]
        i += n
        if lac:
            vals.insert(lac - 1, "—"); LACUNAS_ACHADAS.append(f"Tabela {tab} NPS {frac(nps)} coluna {lac}: em branco no PDF -> '—'")
        linhas.append([frac(nps)] + vals)
    if i != len(tk):
        raise ValueError(f"classe {classe} págs {pags}: sobraram tokens {tk[i:i+10]}")
    if aviso:
        m = re.search(r"Use Class (\d+) dimensions in these sizes( \[Note \((\d+)\)\])?", aviso)
        txt = f"Usar dimensões da Classe {m.group(1)}" + (f" (Nota {m.group(3)})" if m.group(3) else "")
        for l in linhas:
            if l[1] is None:
                l[1] = txt
    return linhas


# ---------------- colunas ----------------
C = {
    "O": "O — Ø externo do flange", "tf": "tf — espessura mín. do flange", "tfL": "tf — espessura mín. (lap joint)",
    "X": "X — Ø do cubo (base)", "Ah": "Ah — Ø do cubo no início do chanfro (WN)",
    "Y_SOSW": "Y — compr. pelo cubo: roscado/SO/SW", "Y_SO": "Y — compr. pelo cubo: roscado/SO",
    "Y_T": "Y — compr. pelo cubo: roscado", "Y_L": "Y — compr. pelo cubo: lap joint", "Y_WN": "Y — compr. pelo cubo: WN",
    "T": "T — compr. mín. de rosca (roscado)",
    "B_SOSW": "B — furo mín.: SO/SW", "B_SO": "B — furo mín.: SO", "B_L": "B — furo mín.: lap joint",
    "B_WNSW": "B — furo: WN/SW", "B_WN": "B — furo: WN",
    "r": "r — raio do canto do furo (lap joint)", "Q": "Q — rebaixo mín. (roscado)", "D": "D — profundidade do encaixe (SW)",
}
DIM = {  # classe: (tabela mm, págs mm, tabela pol, págs pol, colunas)
    "150": ("8", [94, 95], "II-8", [184, 185], "O tf tfL X Ah Y_SOSW Y_L Y_WN T B_SOSW B_L B_WNSW r D"),
    "300": ("11", [103, 104], "II-11", [191, 192], "O tf tfL X Ah Y_SOSW Y_L Y_WN T B_SOSW B_L B_WNSW r Q D"),
    "400": ("14", [111, 112], "II-14", [199, 200], "O tf X Ah Y_SO Y_L Y_WN T B_SO B_L B_WN r Q"),
    "600": ("16", [114, 115], "II-16", [202, 203], "O tf X Ah Y_SOSW Y_L Y_WN T B_SOSW B_L B_WNSW r Q D"),
    "900": ("18", [117, 118], "II-18", [205, 206], "O tf X Ah Y_SO Y_L Y_WN T B_SO B_L B_WN r Q"),
    "1500": ("20", [120, 121], "II-20", [208, 209], "O tf X Ah Y_SOSW Y_L Y_WN T B_SOSW B_L B_WNSW r Q D"),
    "2500": ("22", [123], "II-22", [211], "O tf X Ah Y_T Y_L Y_WN T B_L B_WN r Q"),
}
FUR = {
    "150": ("7", 93, "II-7", 183), "300": ("10", 102, "II-10", 190), "400": ("13", 110, "II-13", 198),
    "600": ("15", 113, "II-15", 201), "900": ("17", 116, "II-17", 204), "1500": ("19", 119, "II-19", 207),
    "2500": ("21", 122, "II-21", 210),
}
FUR_COL_BAIXA = ["NPS", "O — Ø externo do flange", "W — Ø do círculo de furação", "Ø do furo (pol)", "Nº de parafusos",
                 "Ø do parafuso/estojo (pol)", "L — estojo, RF 2 mm", "L — estojo, RTJ", "L — parafuso de máquina, RF 2 mm"]
FUR_COL_ALTA = ["NPS", "O — Ø externo do flange", "W — Ø do círculo de furação", "Ø do furo (pol)", "Nº de parafusos",
                "Ø do parafuso/estojo (pol)", "L — estojo, RF 7 mm", "L — estojo, macho-fêmea/lingueta-ranhura",
                "L — estojo, RTJ"]
# colunas em polegada nas tabelas de furação (não convertem) e colunas arredondadas a 5 mm na versão métrica
COL_POL = {3, 5}

NOTAS_DIM = ("Dimensões em mm. Flanges com face com ressalto (RF) de {rf}: tf NÃO inclui o ressalto (6.4.1). "
             "Tolerâncias: seção 7. Faces: 6.4 e Tabelas 4/5. Furação: Tabela {fur}. "
             "{nota_extra}Equivalente em polegadas: Tabela {tpol} (Apêndice Obrigatório II).")

EXTRA = {  # observações sobre o próprio texto da norma (ver relatório do script)
    "400": " Atenção: NPS 22: Ah impresso como 22.0 na Tabela 14 (mm) — erro da norma; a Tabela II-14 dá 22.0 in = 558,8 mm, "
           "que é o valor correto (igual às demais classes).",
    "1500": " NPS 20: a coluna Q está em branco no PDF (mostrada como —).",
}
PAG_FIM_NOTAS = {"150": 96, "300": 105}  # notas das Tabelas 8 e 11 continuam na página seguinte
tabelas, relatorio = [], []
conferidos, diverg = 0, []


def confere(tid, col, lin_mm, lin_in, tol_fn):
    global conferidos
    for a, b in zip(lin_mm, lin_in):
        assert a[0] == b[0], (tid, a[0], b[0])
        for j in range(1, len(a)):
            x, y = a[j], b[j]
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if j in col.get("pol", ()):  # já em polegadas (Nº de parafusos também cai aqui)
                    ok = x == y
                else:
                    tol = tol_fn(j, y)
                    ok = abs(x / 25.4 - y) <= tol
                conferidos += 1
                if not ok:
                    diverg.append(f"{tid} NPS {a[0]} [{col['nomes'][j]}]: {x} mm = {x/25.4:.3f} in × tabela pol {y}")
            else:
                conferidos += 1
                if str(x) != str(y):
                    diverg.append(f"{tid} NPS {a[0]} [{col['nomes'][j]}]: {x!r} × tabela pol {y!r}")


def tol_padrao(j, y):  # valores em mm com 0,1 mm ou 1 mm de resolução
    return max(0.03, 0.015 * abs(y))


for cl, (tmm, pmm, tin, pin_, cols) in DIM.items():
    nomes = ["NPS"] + [C[c] for c in cols.split()]
    lm = parse_tabela(pmm, cl, len(nomes), tmm)
    li = parse_tabela(pin_, cl, len(nomes), tin)
    ji_O = 1
    confere(f"Tabela {tmm}", {"nomes": nomes}, lm, li,
            lambda j, y: 0.1 if j == ji_O else tol_padrao(j, y))   # O arredondado a 5 mm
    if cl == "400":  # erro tipográfico da norma (ver EXTRA): marcar a célula depois da conferência mm × pol
        jah = next(j for j, n in enumerate(nomes) if n.startswith("Ah"))
        lin = next(l for l in lm if str(l[0]) == "22")
        assert lin[jah] in (22.0, 22), lin[jah]
        lin[jah] = "22.0 (sic; correto 558.8 — ver nota)"
    notas = {"150": "Nota (8): a especificar pelo comprador. ", "300": "", "400": "Nota (5): a especificar pelo comprador. ",
             "600": "Nota (4): a especificar pelo comprador. ", "900": "Nota (5): a especificar pelo comprador. ",
             "1500": "Nota (4): a especificar pelo comprador. ", "2500": "Nota (4): a especificar pelo comprador. "}
    B_STD = "B (WN/SW, col. 13) = Ø interno do tubo de parede Standard (ASME B36.10M; igual a Sch 40 até NPS 10), fornecido salvo especificação do comprador; tolerâncias 7.5.2. "
    if cl == "150":
        notas["150"] = B_STD.replace("; tolerâncias", " — Nota (7); tolerâncias") + notas["150"]
    if cl == "300":
        notas["300"] = B_STD.replace("; tolerâncias", " — Nota (6); tolerâncias") + "Nota (7): a especificar pelo comprador (NPS 14–24). "
    tabelas.append({
        "id": f"b165-cl{cl}-dim", "titulo": f"Classe {cl} — dimensões do flange", "norma": "ASME-B16.5",
        "item": f"Tabela {tmm}", "pagina": pmm[0], "unidade": "mm", "chave": {"serie": "ASME B16.5", "classe": cl},
        "colunas": nomes, "linhas": lm,
        "nota": NOTAS_DIM.format(rf="2 mm" if cl in ("150", "300") else "7 mm", fur=FUR[cl][0], tpol=tin,
                                 nota_extra=notas[cl]) + (f" Páginas {pmm[0]}–{PAG_FIM_NOTAS.get(cl, pmm[-1])}." if len(pmm) > 1 else "") + EXTRA.get(cl, ""),
    })
    relatorio.append(f"b165-cl{cl}-dim: {len(lm)} × {len(nomes)} (Tabela {tmm}, págs {pmm}) × {tin} págs {pin_}")

for cl, (tmm, pmm, tin, pin_) in FUR.items():
    nomes = FUR_COL_BAIXA if cl in ("150", "300") else FUR_COL_ALTA
    lm = parse_tabela([pmm], cl, len(nomes), tmm)
    li = parse_tabela([pin_], cl, len(nomes), tin)
    # O, W: O e comprimentos L arredondados a 5 mm na versão métrica; W com 0,1 mm
    confere(f"Tabela {tmm}", {"nomes": nomes, "pol": {3, 4, 5}}, lm, li,
            lambda j, y: 0.1 if j in (1, 6, 7, 8) else tol_padrao(j, y))
    tabelas.append({
        "id": f"b165-cl{cl}-fur", "titulo": f"Classe {cl} — furação e parafusos", "norma": "ASME-B16.5",
        "item": f"Tabela {tmm}", "pagina": pmm, "unidade": "mm (Ø de furo e de parafuso em polegadas)",
        "chave": {"serie": "ASME B16.5", "classe": cl}, "colunas": nomes, "linhas": lm,
        "nota": ("Furos em múltiplos de 4, igualmente espaçados, a cavaleiro das linhas de centro — cada linha de centro passa entre um par de furos, nenhum furo sobre ela (6.5). "
                 "L do estojo não inclui as pontas (6.10.2); comprimentos não tabelados: Apêndice Não Obrigatório C. "
                 f"Spot facing: 6.6. Equivalente em polegadas: Tabela {tin}."),
    })
    relatorio.append(f"b165-cl{cl}-fur: {len(lm)} × {len(nomes)} (Tabela {tmm}, pág {pmm}) × {tin} pág {pin_}")

# ---------------- P-T ----------------
PT_EXTRA = {"1.1": " A Tabela 1A (pág. 22) também inclui no Grupo 1.1: 3½Ni — A350 Gr. LF3 (ausente do cabeçalho da Tabela 2-1.1); e classifica A537 Cl. 1 como C–Mn–Si."}
PT = {"1.1": (41, 133), "2.2": (56, 148), "2.3": (57, 149), "2.8": (62, 154)}
CLASSES = ["150", "300", "400", "600", "900", "1500", "2500"]


def parse_pt(pg):
    tk = paginas[pg]
    titulo = next(t for t in tk if "Pressure–Temperature Ratings for Group" in t)
    ip = tk.index("Plates"); it = next(k for k, t in enumerate(tk) if t.startswith("Temp."))
    mats = tk[ip + 1:it]
    assert len(mats) % 4 == 0, (pg, mats)
    i = tk.index("Class") + 1
    assert tk[i:i + 7] == CLASSES, (pg, tk[i:i + 7])
    i += 7
    fim = next(k for k in range(i, len(tk)) if tk[k].startswith(PARA))
    dados = tk[i:fim]
    assert len(dados) % 8 == 0, (pg, len(dados))
    linhas = []
    for k in range(0, len(dados), 8):
        r = dados[k:k + 8]
        t = r[0].replace(" to ", " a ")
        linhas.append([t] + [("—" if x == "…" else float(x.replace(",", ""))) for x in r[1:]])
    notas = " ".join(tk[fim:next((k for k in range(fim, len(tk)) if tk[k].startswith(("ASME B16.5-2017", "Dit"))), len(tk))])
    return titulo, [mats[k:k + 4] for k in range(0, len(mats), 4)], linhas, notas


for g, (pb, pp) in PT.items():
    tit, mats, lb, notas = parse_pt(pb)
    _, _, lp, _ = parse_pt(pp)
    # 1ª linha: −29 a 38 °C  ×  −20 a 100 °F ;  bar × 14,5038 ≈ psi (tolerância 1 %, arredondamentos)
    for c in range(1, 8):
        bar, psi = lb[0][c], lp[0][c]
        conferidos += 1
        if isinstance(bar, float) and abs(bar * 14.5038 - psi) > 0.01 * psi + 1:
            diverg.append(f"P-T {g} classe {CLASSES[c-1]} 1ª linha: {bar} bar = {bar*14.5038:.0f} psi × {psi}")
    # 538 °C = 1000 °F
    rb = next((l for l in lb if l[0] == "538"), None); rp = next((l for l in lp if l[0] == "1,000" or l[0] == "1000"), None)
    if rb and rp:
        for c in range(1, 8):
            conferidos += 1
            if isinstance(rb[c], float) and abs(rb[c] * 14.5038 - rp[c]) > 0.01 * rp[c] + 1:
                diverg.append(f"P-T {g} 538 °C classe {CLASSES[c-1]}: {rb[c]} bar × {rp[c]} psi")
    lista = "; ".join(f"{m[0]}: " + ", ".join(x for x in m[1:] if x != "…") for m in mats)
    tabelas.append({
        "id": f"b165-pt-{g.replace('.', '-')}", "titulo": f"Pressão–temperatura — Grupo {g}", "norma": "ASME-B16.5",
        "item": f"Tabela 2-{g}", "pagina": pb, "unidade": "bar (pressão manométrica máx. de trabalho)",
        "chave": {"grupo": g}, "consulta": False,
        "colunas": ["Temperatura (°C)"] + [f"Classe {c}" for c in CLASSES], "linhas": lb,
        "nota": (f"Materiais do grupo {g} (designação nominal: forjado, fundido, chapa — mesma relação da Tabela 1A): {lista}. "
                 f"Interpolação linear entre temperaturas é permitida; entre classes, não (2.1). "
                 f"Notas da norma: {notas}  Em psi/°F: Tabela II-2-{g}, pág. {pp}." + PT_EXTRA.get(g, "")),
    })
    relatorio.append(f"b165-pt-{g}: {len(lb)} × 8 (Tabela 2-{g}, pág {pb}) × II-2-{g} pág {pp}")

# consistência interna: Ah (Ø do tubo) igual em todas as classes para o mesmo NPS
ah = {}
for t in tabelas:
    if t["id"].endswith("-dim"):
        j = t["colunas"].index(C["Ah"])
        for l in t["linhas"]:
            if isinstance(l[j], (int, float)):
                ah.setdefault(l[0], set()).add(l[j])
for nps, s in ah.items():
    if len(s) > 1:
        diverg.append(f"Ah diferente entre classes p/ NPS {nps}: {sorted(s)}")

print("\n".join(relatorio + LACUNAS_ACHADAS + TIPOS))
print(f"\nValores conferidos mm×pol / bar×psi: {conferidos}; divergências: {len(diverg)}")
print("\n".join("  - " + d for d in diverg))

if GRAVAR:
    ficha = json.load(open(FICHA, encoding="utf-8")) if os.path.exists(FICHA) else {"id": "flange-asme-b16-5"}
    # mantém as tabelas de outras normas (B16.47, B16.20, B16.21, NORSOK) já gravadas na ficha
    ficha["tabelas"] = tabelas + [t for t in ficha.get("tabelas", []) if t.get("norma") != "ASME-B16.5"]
    with open(FICHA, "w", encoding="utf-8") as f:
        json.dump(ficha, f, ensure_ascii=False, indent=2)
    print("gravado:", FICHA)
