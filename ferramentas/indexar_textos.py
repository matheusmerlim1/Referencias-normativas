"""Índice invertido do texto completo das normas (dados/textos/*.js) → dados/busca/*.js, para a busca global do site.

uso:  python -P ferramentas/indexar_textos.py            (~15 s; rodar depois de ferramentas/extrair_textos.py)
      python -P ferramentas/indexar_textos.py --stats    (só mede: não grava nada)

Funciona offline via file:// (só <script>, nada de fetch):
  dados/busca/_mapa.js   window.UVA_BUSCA_MAPA = {"docs": ["ID", ...], "arquivos": {"ab": "ab.js", "con": "con.js", ...}, ...}
  dados/busca/<pref>.js  window.UVA_BUSCA_TXT["<pref>"] = {"termo": "postagens", ...}
O prefixo começa com 1 caractere; o que passaria de LIM_ARQ bytes é dividido em prefixos de 2 (3, 4…) caracteres.
O site carrega só os arquivos dos prefixos dos termos digitados (o termo pertence ao arquivo de prefixo mais longo que casa).

Termos (mesma regra em assets/app.js → tokensTexto/juntarSiglas; as stopwords vão em _mapa.js "stop"):
  - texto sem acento e minúsculo (NFD, tira U+0300–U+036F);
  - token = [a-z0-9]+ unidos por . - / ; se tiver letra E dígito é CÓDIGO e perde os separadores
    ("B31.3" → b313, "SA-516" → sa516, "M12" → m12); senão é quebrado nos separadores ("guarda-corpo" → guarda, corpo);
  - palavra: ≥ 3 letras, fora das stopwords PT/EN, ≤ 40 caracteres; número puro não entra;
  - sigla em MAIÚSCULAS (1–4 letras) + espaço + número também vira código ("SA 516" → sa516, "NBR 5410" → nbr5410).
Postagens de um termo: "D:C:P.P.P;D:C:P..." — D = índice da norma em docs (base 36), C = ocorrências na norma (base 36),
P = páginas (0-based) em base 36, a 1ª absoluta e as demais como diferença para a anterior.
Se o termo está em mais de MAX_PAGS_DOC páginas de uma norma, guarda só "D:C:*N" (N = nº de páginas, base 36):
o site trata o termo como presente em todas as páginas dessa norma ao cruzar termos (E lógico).
"""
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict

TEXTOS = "dados/textos"
SAIDA = "dados/busca"
LIM_ARQ = 800_000        # bytes por arquivo de prefixo (meta ≤ ~2 MB; menor = busca carrega menos)
MAX_PAGS_DOC = 3000      # acima disto, só a contagem de páginas daquela norma (termo muito comum)

STOP = set("""
a o e de da do das dos em no na nos nas um uma uns umas por para pelo pela pelos pelas com sem sob sobre entre ate
ao aos as os que se ou mas mais menos como quando onde qual quais cujo cuja seu sua seus suas ele ela eles elas este
esta estes estas esse essa esses essas isto isso aquele aquela aqueles aquelas nao sim ser sao foi foram sera serao
deve devem pode podem ter tem tendo sendo estar esta estao ja tambem apenas outro outra outros outras cada todo toda
todos todas mesmo mesma muito pouco desta deste dessa desse nesta neste nessa nesse pela dela dele delas deles lhe
the and for are was were been being with without from into onto upon this that these those then than there their
they them its it's not but all any each other such shall should may might must can could will would has have had
having which who whom whose what when where why how also only both either neither nor per via under over above below
between within about after before during through until while than one two three use used using see ref
""".split())

RX_TOK = re.compile(r"[a-z0-9]+(?:[./-][a-z0-9]+)*")
RX_SIGLA = re.compile(r"(?<![A-Za-z0-9])([A-Z]{1,4}) (\d[0-9A-Za-z]*(?:[./-][0-9A-Za-z]+)*)")
RX_LETRA = re.compile(r"[a-z]")
RX_DIG = re.compile(r"\d")
RX_SEP = re.compile(r"[./-]")


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if not 0x300 <= ord(c) <= 0x36F).lower()


def termos(texto):
    """Lista de termos (com repetição) de um texto — mesma regra do app.js."""
    out = []
    n = sem_acento(texto)
    for t in RX_TOK.findall(n):
        if RX_DIG.search(t):
            if RX_LETRA.search(t):
                c = RX_SEP.sub("", t)
                if len(c) <= 24:
                    out.append(c)
            continue
        for w in RX_SEP.split(t):
            if 3 <= len(w) <= 40 and w not in STOP:
                out.append(w)
    for a, b in RX_SIGLA.findall(texto):
        c = sem_acento(a + RX_SEP.sub("", b))
        if len(c) <= 24:
            out.append(c)
    return out


def b36(n):
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + s
    return s


def ler_lista():
    s = open(f"{TEXTOS}/_lista.js", encoding="utf-8").read()
    return json.loads(s.split("=", 1)[1].strip().rstrip(";"))


def ler_texto(arq):
    s = open(f"{TEXTOS}/{arq}", encoding="utf-8").read()
    m = re.search(r"window\.UVA_TEXTOS\[(\".*?\")\] = ", s)
    return json.loads(m.group(1)), json.loads(s[m.end():].rstrip().rstrip(";"))


def main():
    so_medir = "--stats" in sys.argv
    t0 = time.time()
    lista = ler_lista()
    docs = sorted(lista)
    # termo -> {doc: [contagem, [páginas]]}
    idx = defaultdict(dict)
    npags = 0
    for d, nid in enumerate(docs):
        nid2, pags = ler_texto(lista[nid]["arquivo"])
        assert nid2 == nid, (nid, nid2)
        for p, txt in enumerate(pags):
            if not txt:
                continue
            npags += 1
            cont = defaultdict(int)
            for t in termos(txt):
                cont[t] += 1
            for t, c in cont.items():
                e = idx[t].get(d)
                if e is None:
                    idx[t][d] = [c, [p]]
                else:
                    e[0] += c
                    e[1].append(p)
        if d % 100 == 0:
            print(f"  {d}/{len(docs)} normas, {len(idx)} termos, {time.time() - t0:.0f} s", flush=True)

    # postagens compactas
    post = {}
    cortados = 0
    for t, porDoc in idx.items():
        partes = []
        for d in sorted(porDoc):
            c, ps = porDoc[d]
            if len(ps) > MAX_PAGS_DOC:
                partes.append(f"{b36(d)}:{b36(c)}:*{b36(len(ps))}")
                cortados += 1
                continue
            ant, ds = 0, []
            for i, p in enumerate(ps):
                ds.append(b36(p if i == 0 else p - ant))
                ant = p
            partes.append(f"{b36(d)}:{b36(c)}:{'.'.join(ds)}")
        post[t] = ";".join(partes)
    del idx

    # arquivos por prefixo: 2 letras; divide em 3/4 se passar do limite
    def tam(t):
        return len(t.encode("utf-8")) + len(post[t]) + 6

    def agrupar(ts, n):
        g = defaultdict(list)
        for t in ts:
            g[t[:n]].append(t)
        return g

    arquivos = {}
    pendentes = [(k, v, 1) for k, v in agrupar(post, 1).items()]
    while pendentes:
        k, ts, n = pendentes.pop()
        tot = sum(tam(t) for t in ts)
        curtos = [t for t in ts if len(t) <= n]
        if tot > LIM_ARQ and n < 5 and len(ts) > len(curtos):
            sub = agrupar([t for t in ts if len(t) > n], n + 1)
            # termos do tamanho do prefixo ficam no arquivo do prefixo (pequeno)
            if curtos:
                arquivos[k] = curtos
            for k2, v2 in sub.items():
                pendentes.append((k2, v2, n + 1))
        else:
            arquivos[k] = ts

    nome = lambda k: re.sub(r"[^a-z0-9]", "_", k) + ".js"
    total = sum(tam(t) for t in post)
    maior = max(arquivos, key=lambda k: sum(tam(t) for t in arquivos[k]))
    print(f"{len(docs)} normas, {npags} páginas com texto, {len(post)} termos, {cortados} postagens resumidas (> {MAX_PAGS_DOC} págs.)")
    print(f"índice ≈ {total / 1e6:.1f} MB em {len(arquivos)} arquivos; maior: {maior} ({sum(tam(t) for t in arquivos[maior]) / 1e6:.2f} MB)")
    if so_medir:
        return
    os.makedirs(SAIDA, exist_ok=True)
    for f in os.listdir(SAIDA):
        if f.endswith(".js"):
            os.remove(f"{SAIDA}/{f}")
    for k, ts in arquivos.items():
        corpo = json.dumps({t: post[t] for t in sorted(ts)}, ensure_ascii=False, separators=(",", ":"))
        open(f"{SAIDA}/{nome(k)}", "w", encoding="utf-8").write(
            f"window.UVA_BUSCA_TXT = window.UVA_BUSCA_TXT || {{}}; window.UVA_BUSCA_TXT[{json.dumps(k)}] = {corpo};\n")
    mapa = {"docs": docs, "arquivos": {k: nome(k) for k in sorted(arquivos)}, "max_pags_doc": MAX_PAGS_DOC, "stop": sorted(STOP),
            "paginas": [lista[n]["paginas"] for n in docs]}
    open(f"{SAIDA}/_mapa.js", "w", encoding="utf-8").write(
        "window.UVA_BUSCA_MAPA = " + json.dumps(mapa, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"gravado em {SAIDA}/ ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
