"""Texto completo de cada norma → dados/textos/<id-da-ficha>.js (um arquivo por norma, carregado sob demanda pelo site).

Os PDFs de referencias/ vão ser removidos: o site precisa ter o CONTEÚDO, não só item/página. Por norma de conteudo/normas.json:
  - fonte = o PDF de "arquivo"; se houver cópia OCR (referencias/ocr/_origem.json) e ela render mais palavras, usa a cópia;
  - texto por página, em parágrafos (blocos do PDF; linhas do bloco unidas, hífen de fim de linha desfeito);
  - cabeçalho/rodapé/marca d'água = linha que se repete em ≥ 40 % das páginas (mín. 4) → removida, MAS:
      linha sem letras (nº de tabela "1,25", "…", "300.4") e rótulos de conteúdo (NOTE, Table, Figure, Key, (a)…) só saem se
      estiverem na MARGEM (10 % de cima/baixo, 8 % dos lados); no corpo da página, só sai linha repetida com ≥ 20 caracteres
      ou que também aparece na margem (cabeçalho de coluna de tabela repetido — "Size", "Tolerance" — fica); nº de página
      solto idem (só na margem);
  - espaço entre palavras reconstruído pelo vão entre letras quando o PDF não tem o caractere (texto justificado ASME B31.3/B16.5);
  - ligaduras expandidas (ﬁ → fi); fonte Symbol em área privada (U+F0xx) → caractere certo (≤ ≥ ± × °…), peças de
    chave/colchete grandes (U+F8E5–F8FF, U+F0E6–F0FE) descartadas; fontes MathematicalPi/MathTechnical (ASME 2007) pelo
    nome do glifo (/Differences); linha só de lixo (fonte sem mapa: >30 % de caracteres de controle) descartada;
    corridas de U+FFFD / NUL (pontilhado de sumário) removidas; "palavras" de pontilhado lidas pelo OCR ("ccsssee…") removidas;
    títulos espaçados ("C H A P T E R", "S E C T I O N", lista fixa de palavras) juntados.
Saída: window.UVA_TEXTOS["ID"] = ["pág. 1", "pág. 2", …] (índice = página − 1; parágrafos separados por "\\n\\n")
       e dados/textos/_lista.js: window.UVA_TEXTOS_LISTA = {"ID": {"arquivo", "paginas", "chars"}}.

uso: python -P ferramentas/extrair_textos.py [ID ...]      (sem ids: todas; ~10–20 min)
     env UVA_TEXTOS_SAIDA=<pasta> grava noutra pasta (teste), sem tocar em dados/textos.
"""
import collections
import json
import os
import re
import sys

import pymupdf

SAIDA = os.environ.get("UVA_TEXTOS_SAIDA", "dados/textos")
RX_PAL = re.compile(r"[A-Za-zÀ-ÿ]{3,}")
FLAGS = pymupdf.TEXTFLAGS_BLOCKS & ~pymupdf.TEXT_PRESERVE_LIGATURES  # sem ligaduras: "ﬁ" vira "fi"

# rótulos que são CONTEÚDO mesmo repetidos em muitas páginas (só saem se estiverem na margem)
RX_CONTEUDO = re.compile(r"^(notes?|notas?|table|tabela|quadro|figure|figura|fig\.|key|legenda|where|onde|guidance note|"
                         r"general notes?|continued|\(?cont|\(\w{1,3}\)|\w\)|-+e-n-d-)", re.I)
RX_NUMPAG = re.compile(r"[-–—\s]*\d{1,4}[-–—\s]*|Page \d+ of \d+|Página \d+( de \d+)?|[ivxlc]{1,6}", re.I)

# fonte Symbol (Adobe) mapeada na área privada U+F020–F0FF
_SYM = (" !∀#∃%&∋()∗+,−./0123456789:;<=>?≅ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ[∴]⊥_‾αβχδεφγηιϕκλμνοπθρστυϖωξψζ{|}∼")
SYMBOL = {0xF020 + i: c for i, c in enumerate(_SYM)}
SYMBOL.update({0xF0A0: "€", 0xF0A1: "ϒ", 0xF0A2: "′", 0xF0A3: "≤", 0xF0A4: "⁄", 0xF0A5: "∞", 0xF0A6: "ƒ", 0xF0A7: "♣",
               0xF0A8: "♦", 0xF0A9: "♥", 0xF0AA: "♠", 0xF0AB: "↔", 0xF0AC: "←", 0xF0AD: "↑", 0xF0AE: "→", 0xF0AF: "↓",
               0xF0B0: "°", 0xF0B1: "±", 0xF0B2: "″", 0xF0B3: "≥", 0xF0B4: "×", 0xF0B5: "∝", 0xF0B6: "∂", 0xF0B7: "•",
               0xF0B8: "÷", 0xF0B9: "≠", 0xF0BA: "≡", 0xF0BB: "≈", 0xF0BC: "…", 0xF0BD: "|", 0xF0BE: "—", 0xF0BF: "↵",
               0xF0C0: "ℵ", 0xF0C4: "⊗", 0xF0C5: "⊕", 0xF0C6: "∅", 0xF0C7: "∩", 0xF0C8: "∪", 0xF0C9: "⊃", 0xF0CA: "⊇",
               0xF0CB: "⊄", 0xF0CC: "⊂", 0xF0CD: "⊆", 0xF0CE: "∈", 0xF0CF: "∉", 0xF0D0: "∠", 0xF0D1: "∇", 0xF0D2: "®",
               0xF0D3: "©", 0xF0D4: "™", 0xF0D5: "∏", 0xF0D6: "√", 0xF0D7: "⋅", 0xF0D8: "¬", 0xF0D9: "∧", 0xF0DA: "∨",
               0xF0DB: "⇔", 0xF0DC: "⇐", 0xF0DD: "⇑", 0xF0DE: "⇒", 0xF0DF: "⇓", 0xF0E0: "◊", 0xF0E1: "〈", 0xF0E2: "®",
               0xF0E3: "©", 0xF0E4: "™", 0xF0E5: "∑", 0xF0F1: "〉", 0xF0F2: "∫"})
for _c in list(range(0xF0E6, 0xF0F1)) + list(range(0xF0F3, 0xF100)) + list(range(0xF8E5, 0xF900)):
    SYMBOL[_c] = ""  # peças de parêntese/chave/colchete grandes
# glifos "H#####" das fontes Linotype MathematicalPi (ASME 2007), conferidos pelo contexto
PI = {"H11547": "×", "H11003": "×", "H9251": "α", "H9252": "β", "H9253": "γ", "H9254": "δ", "H9258": "θ", "H9261": "λ",
      "H9262": "μ", "H9263": "ν", "H9266": "π", "H9267": "ρ", "H9268": "σ", "H9270": "τ", "H9274": "ψ", "H9275": "ω",
      "H9280": "ε", "H9278": "φ", "H9004": "Δ", "H9018": "Σ", "H5129": "ℓ", "H11001": "+", "H11002": "−", "H11005": "=", "H11034": "°",
      "H20906": "√", "H20849": "(", "H20850": ")", "H20898": "[", "H20899": "]"}
RX_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f]")
RX_ESPACADO = re.compile(r"\b(" + "|".join(" ".join(w) for w in (
    "CHAPTER", "SECTION", "APPENDIX", "APPENDICES", "PART", "CONTENTS", "ANNEX", "INDEX", "FOREWORD", "PREFACE", "TABLE",
    "FIGURE", "NOTES", "NOTE", "MANDATORY", "NONMANDATORY", "SUBSECTION", "ARTICLE", "INTERNATIONAL", "CODE", "STANDARD")) + r")\b")
RX_PONTILHADO = re.compile(r"[�\x00]{2,}|(?:\. ?){6,}")


def slug(nid):
    return "norma-" + re.sub(r"[^a-z0-9]+", "-", nid.lower()).strip("-")


def abre(p):
    return pymupdf.open(stream=open(p, "rb").read(), filetype="pdf")


def palavras(d, n=12):
    """palavras "boas" por página nas primeiras n páginas (texto quebrado 1 letra/linha rende pouco)."""
    k = min(n, len(d))
    return sum(len(RX_PAL.findall(d[i].get_text())) for i in range(k)) / max(k, 1)


def chave(l):
    return re.sub(r"\d+", "#", l.strip().lower())


def _difs(d, cache, x):
    """/Differences da fonte (xref) → {código: nome do glifo}."""
    if x not in cache:
        q = {}
        try:
            e = d.xref_get_key(x, "Encoding")
            o = d.xref_object(int(e[1].split()[0])) if e[0] == "xref" else (e[1] if e[0] == "dict" else "")
            m = re.search(r"/Differences\s*\[(.*?)\]", o, re.S)
            if m:
                c = 0
                for t in m.group(1).split():
                    if t[0] != "/":
                        c = int(t)
                    else:
                        q[c] = t[1:]
                        c += 1
        except Exception:
            pass
        cache[x] = q
    return cache[x]


def _texto_span(s):
    """texto do span (rawdict) com espaço onde o PDF não tem o caractere de espaço mas há um vão entre as letras
    (texto justificado com Tw/posicionamento: "cold-formedtoacenterline" → "cold-formed to a centerline").
    Só quando o vão típico entre letras é ~0 (fonte com espaçamento entre letras fica como está)."""
    cs = s["chars"]
    if len(cs) < 3:
        return "".join(c["c"] for c in cs)
    lim = 0.12 * s["size"]
    gaps = [cs[i + 1]["bbox"][0] - cs[i]["bbox"][2] for i in range(len(cs) - 1)]
    if max(gaps) <= lim or sorted(gaps)[len(gaps) // 2] > 0.04 * s["size"]:
        return "".join(c["c"] for c in cs)
    out = [cs[0]["c"]]
    for i, g in enumerate(gaps):
        c = cs[i + 1]["c"]
        if g > lim and c != " " and out[-1] != " ":
            out.append(" ")
        out.append(c)
    return "".join(out)


def _span(s, pg, d, cache, fx):
    t, f = _texto_span(s), s["font"]
    if "MathTechnicalP" in f:
        t = t.replace("p", "=")  # ASME 2007: sinal de igual desenhado com o glifo "p"
    if RX_CTRL.search(t):
        if fx[0] is None:
            fx[0] = collections.defaultdict(list)
            for g in pg.get_fonts(full=True):
                fx[0][g[3].split("+")[-1]].append(g[0])
        dif = {}
        for x in fx[0].get(f, []):
            dif.update(_difs(d, cache, x))
        out = []
        for ch in t:
            if RX_CTRL.match(ch):
                nome = dif.get(ord(ch))
                u = PI.get(nome) if nome else None
                if u is None and nome:
                    v = pymupdf.glyph_name_to_unicode(nome)
                    u = chr(v) if v and v != 0xFFFD else None
                out.append(u if u is not None else ("�" if nome else ch))  # sem nome: lixo, sai no normaliza
            else:
                out.append(ch)
        t = "".join(out)
    return t


def paginas(d):
    """por página: lista de blocos; bloco = lista de (texto da linha, está na margem?)."""
    out, cache = [], {}
    for pg in d:
        W, H = pg.rect.width, pg.rect.height
        fx = [None]
        pars = []
        for b in pg.get_text("rawdict", flags=FLAGS)["blocks"]:
            if b.get("type", 0) != 0:
                continue  # bloco de imagem
            ls = []
            for l in b["lines"]:
                t = "".join(_span(s, pg, d, cache, fx) for s in l["spans"]).strip()
                if not t:
                    continue
                x0, y0, x1, y1 = l["bbox"]
                margem = y1 < 0.10 * H or y0 > 0.90 * H or x1 < 0.08 * W or x0 > 0.92 * W
                ls.append((t, margem))
            if ls:
                pars.append(ls)
        out.append(pars)
    return out


def _letras(k):
    return len(re.findall(r"[a-zà-ÿ]", k))


def _lixo_ocr(m):
    w = m.group(0)
    return "" if (sum(c in "cesaonrmuvwti" for c in w) >= 0.9 * len(w) and len(set(w)) <= 0.35 * len(w)) else w


def normaliza(s):
    s = "".join(SYMBOL.get(ord(c), c) if 0xF000 <= ord(c) <= 0xF8FF else c for c in s)
    s = s.replace("昀؀", "fi")  # ligadura "fi" com ToUnicode quebrado (NBR 7190-1)
    s = RX_PONTILHADO.sub(" … ", s)
    s = re.sub(r"[A-Za-zÀ-ÿ]{15,}", _lixo_ocr, s)
    s = RX_ESPACADO.sub(lambda m: m.group(1).replace(" ", ""), s)
    s = RX_CTRL.sub("", s)  # controle sem glifo conhecido = ruído (símbolo de glifo nomeado e não mapeado já virou "�")
    return re.sub(r"[ \t]+", " ", s).strip()


def limpa(pags):
    cont = collections.Counter()
    for pars in pags:
        cont.update({chave(l) for ls in pars for l, _ in ls})
    lim = max(4, 0.4 * len(pags))
    rep = {k for k, v in cont.items() if v >= lim and len(pags) >= 6}
    na_margem = {chave(l) for pars in pags for ls in pars for l, mg in ls if mg}
    res = []
    for pars in pags:
        txt = []
        for ls in pars:
            boas = []
            for l, mg in ls:
                k = chave(l)
                if k in rep and (mg or (_letras(k) >= 3 and not RX_CONTEUDO.match(l) and (len(l) >= 20 or k in na_margem))):
                    continue  # cabeçalho/rodapé/marca d'água
                if mg and RX_NUMPAG.fullmatch(l):
                    continue  # nº de página
                if len(l) >= 5 and len(RX_CTRL.findall(l)) > 0.3 * len(l):
                    continue  # fonte sem mapa de caracteres (lixo)
                boas.append(l)
            if not boas:
                continue
            s = boas[0]
            for l in boas[1:]:
                if re.search(r"[a-zà-ÿ]-$", s) and l[:1].islower():
                    s = s[:-1] + l  # hífen de fim de linha
                else:
                    s += " " + l
            s = normaliza(s)
            if s:
                txt.append(s)
        res.append("\n\n".join(txt))
    return res


def main(sel):
    normas = json.load(open("conteudo/normas.json", encoding="utf-8"))
    origem = json.load(open("referencias/ocr/_origem.json", encoding="utf-8")) if os.path.exists("referencias/ocr/_origem.json") else {}
    ft = "conteudo/completar/texto_fonte.json"  # {id: PDF} fonte do texto que vence a de normas.json (OCR melhor, cópia nativa em T:)
    fonte_txt = json.load(open(ft, encoding="utf-8")) if os.path.exists(ft) else {}
    copia = {}
    for o, a in origem.items():
        copia.setdefault(a.replace("\\", "/"), o)
    os.makedirs(SAIDA, exist_ok=True)
    lp = f"{SAIDA}/_lista.js"
    lista = {}
    if os.path.exists(lp):
        lista = json.loads(open(lp, encoding="utf-8").read().split("=", 1)[1].rstrip().rstrip(";"))
    tot = 0
    for n in normas:
        nid, arq = n["id"], (n.get("arquivo") or "").replace("\\", "/")
        if sel and nid not in sel:
            continue
        if not arq or not os.path.exists(arq):
            print("  SEM ARQUIVO", nid, arq)
            continue
        try:
            d = abre(arq)
            fonte = arq
            alt = copia.get(arq)
            if fonte_txt.get(nid) and os.path.exists(fonte_txt[nid]):  # OCR refeito / cópia nativa (só para o TEXTO)
                d, fonte = abre(fonte_txt[nid]), fonte_txt[nid]
            elif alt and os.path.exists(alt):
                d2 = abre(alt)
                if palavras(d2) > 1.2 * palavras(d):
                    d, fonte = d2, alt
            txt = limpa(paginas(d))
        except Exception as e:
            print("  ERRO", nid, e)
            continue
        f = slug(nid) + ".js"
        js = ("window.UVA_TEXTOS = window.UVA_TEXTOS || {}; window.UVA_TEXTOS[" + json.dumps(nid) + "] = "
              + json.dumps(txt, ensure_ascii=False, separators=(",", ":")) + ";\n")
        open(f"{SAIDA}/{f}", "w", encoding="utf-8").write(js)
        c = sum(len(t) for t in txt)
        lista[nid] = {"arquivo": f, "paginas": len(txt), "chars": c}
        tot += c
        print(f"  {nid}: {len(txt)} págs., {c / 1e3:.0f} mil caracteres{' (OCR)' if fonte != arq else ''}", flush=True)
    open(lp, "w", encoding="utf-8").write("window.UVA_TEXTOS_LISTA = " + json.dumps(lista, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{len(lista)} normas com texto; {tot / 1e6:.1f} MB nesta rodada")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
