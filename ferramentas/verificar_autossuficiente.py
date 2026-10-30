"""Confere se o site funciona SEM referencias/ (os PDFs vão ser removidos): rodar depois do build e ANTES de apagar a pasta.

  - toda imagem citada pelas fichas (conteudo/fichas/*.json) existe em assets/figuras/ e não está dentro de referencias/;
  - toda norma de normas.json tem texto completo em dados/textos/ (e o índice de busca existe);
  - app.js / index.html não carregam nada de referencias/ (links de PDF só para T:\\, catálogo do acervo);
  - textos das fichas temáticas não citam página ("p. 12", "pág. 34").
uso: python -P ferramentas/verificar_autossuficiente.py

Modo --publico (antes de cada commit no repositório público; ver "REPOSITÓRIO PÚBLICO" no CLAUDE.md):
  python -P ferramentas/verificar_autossuficiente.py --publico
  lista todo arquivo NÃO ignorado pelo .gitignore que pareça conteúdo de norma:
  - imagem/PDF fora de assets/figuras/esquemas/ (exceto as próprias em PROPRIAS) e SVG com imagem embutida (<image>);
  - JSON com texto copiado: "Texto (para busca…"/"Texto extraído…", ou trecho > 400 caracteres em inglês (heurística —
    conferir à mão se é texto nosso);
  e confere que dados/dados.js (público) não cita imagens da camada local nem traz fichas de norma.
  Sai com código 1 se achar algo.
"""
import fnmatch
import glob
import json
import os
import re
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROPRIAS = {"capa.png"}  # imagens nossas fora de esquemas/ (logo)
EXT_IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".pdf"}
EN = set("the of and shall be is are to in with for or which this that by on not when where than shall be used may must".split())
PT = set("de da do das dos que para com não em ou os uma um ser é por no na pela pelo são deve".split())
RX_COPIA = re.compile(r"^\s*Texto (\(para busca|extra[ií]do)", re.I)


def regras_gitignore():
    """[(regex, só_diretório)] do .gitignore (subconjunto usado aqui: *, **, / no início/fim, sem '!')."""
    regras = []
    if not os.path.exists(".gitignore"):
        return regras
    for linha in open(".gitignore", encoding="utf-8"):
        p = linha.strip()
        if not p or p.startswith("#") or p.startswith("!"):
            continue
        so_dir = p.endswith("/")
        p = p.rstrip("/")
        ancorado = p.startswith("/") or "/" in p
        p = p.lstrip("/")
        rx = "".join(".*" if c == "**" else "[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c)
                     for c in re.findall(r"\*\*|\*|\?|[^*?]+", p))
        regras.append((re.compile(("^" if ancorado else r"(^|.*/)") + rx + "$"), so_dir))
    return regras


def ignorado(rel, eh_dir, regras):
    """rel = caminho relativo com '/'; também ignorado se algum diretório-pai for."""
    partes = rel.split("/")
    for i in range(1, len(partes) + 1):
        sub, sub_dir = "/".join(partes[:i]), (i < len(partes) or eh_dir)
        for rx, so_dir in regras:
            if so_dir and not sub_dir:
                continue
            if rx.match(sub):
                return True
    return False


def ingles(s):
    ws = re.findall(r"[a-zà-ú]+", s.lower())
    en = sum(w in EN for w in ws)
    pt = sum(w in PT for w in ws)
    return en >= 8 and en > 2 * pt


def strings(x, caminho=""):
    """(caminho, chave, texto) de todas as strings de um JSON."""
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, str):
                yield f"{caminho}.{k}", k, v
            else:
                yield from strings(v, f"{caminho}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if isinstance(v, str):
                yield f"{caminho}[{i}]", "", v
            else:
                yield from strings(v, f"{caminho}[{i}]")


def verificar_publico():
    regras = regras_gitignore()
    if not regras:
        print("ERRO: .gitignore não existe — tudo seria versionado.")
        return 1
    imagens, svg_raster, copias, longos, ilegiveis = [], [], [], [], []
    n_arq = 0
    for raiz, dirs, arqs in os.walk("."):
        rel_raiz = os.path.relpath(raiz, ".").replace("\\", "/")
        rel_raiz = "" if rel_raiz == "." else rel_raiz + "/"
        dirs[:] = [d for d in dirs if d != ".git" and not ignorado(rel_raiz + d, True, regras)]
        for a in arqs:
            rel = rel_raiz + a
            if ignorado(rel, False, regras):
                continue
            n_arq += 1
            ext = os.path.splitext(a)[1].lower()
            if ext in EXT_IMG and rel not in PROPRIAS and not rel.startswith("assets/figuras/esquemas/"):
                imagens.append(rel)
            elif ext == ".svg":
                t = open(rel, encoding="utf-8", errors="replace").read()
                if re.search(r"<image\b", t):
                    svg_raster.append(rel)
                if not rel.startswith("assets/figuras/esquemas/"):
                    imagens.append(rel)
            elif ext == ".json":
                try:
                    d = json.load(open(rel, encoding="utf-8"))
                except (ValueError, UnicodeDecodeError) as e:
                    ilegiveis.append(f"{rel}: {e}")
                    continue
                for cam, k, s in strings(d):
                    if k in ("texto", "nota", "legenda") and RX_COPIA.search(s):
                        copias.append(f"{rel}{cam}: {s[:90]!r}")
                    elif len(s) > 400 and ingles(s):
                        longos.append(f"{rel}{cam} ({len(s)} car.): {s[:90]!r}")
    # dados.js público
    pub = []
    if os.path.exists("dados/dados.js"):
        txt = open("dados/dados.js", encoding="utf-8").read()
        for m in sorted(set(re.findall(r'"((?:docs|tem|asme-ii)/[^"]+\.(?:png|jpe?g|gif|webp)|[^"/]+\.(?:png|jpe?g))"', txt))):
            pub.append(f"dados/dados.js cita imagem da camada local: {m}")
        try:
            D = json.loads(txt.split("=", 1)[1].strip().rstrip(";"))
            if not D.get("publico"):
                pub.append("dados/dados.js não é o build público (falta \"publico\": true) — rodar ferramentas/build.py")
            n_norma = sum(f.get("tipo") == "norma" for f in D.get("fichas", []))
            if n_norma:
                pub.append(f"dados/dados.js traz {n_norma} fichas de norma (camada local)")
            if D.get("ocr_origem"):
                pub.append("dados/dados.js traz ocr_origem (caminhos de referencias/)")
        except ValueError as e:
            pub.append(f"dados/dados.js ilegível: {e}")
    else:
        pub.append("dados/dados.js não existe — rodar ferramentas/build.py")

    def bloco(titulo, itens, lim=40):
        print(f"\n{titulo}: {len(itens)}")
        for x in itens[:lim]:
            print("  -", x)
        if len(itens) > lim:
            print(f"  … + {len(itens) - lim}")
    print(f"--publico: {n_arq} arquivos versionáveis (fora do .gitignore)")
    bloco("Imagens/PDF fora de assets/figuras/esquemas/", imagens)
    bloco("SVG com imagem raster embutida (<image>) — pode ser cópia de figura", svg_raster)
    bloco('Texto copiado de norma ("Texto (para busca…" / "Texto extraído…")', copias)
    bloco("Trechos > 400 caracteres em inglês (conferir se é texto nosso)", longos)
    bloco("JSON ilegível", ilegiveis)
    bloco("dados/dados.js (público)", pub)
    total = len(imagens) + len(svg_raster) + len(copias) + len(longos) + len(ilegiveis) + len(pub)
    print(f"\n{total} pendência(s) —", "OK para versionar" if not total else "NÃO publicar ainda (corrigir ou mover para a camada local)")
    return 1 if total else 0


if "--publico" in sys.argv:
    sys.exit(verificar_publico())

erros, avisos = [], []
normas = json.load(open("conteudo/normas.json", encoding="utf-8"))
lista = {}
if os.path.exists("dados/textos/_lista.js"):
    lista = json.loads(open("dados/textos/_lista.js", encoding="utf-8").read().split("=", 1)[1].strip().rstrip(";"))

n_fig = 0
RX_PAG = re.compile(r"\b(p\.|pág\.|págs\.)\s*\d", re.I)
for p in sorted(glob.glob("conteudo/fichas/*.json")):
    f = json.load(open(p, encoding="utf-8"))
    for g in f.get("figuras", []):
        n_fig += 1
        a = "assets/figuras/" + g["arquivo"]
        if not os.path.exists(a):
            erros.append(f"{os.path.basename(p)}: imagem falta {a}")
    if f.get("tipo") != "norma":
        textos = [r.get(k, "") for r in f.get("requisitos", []) for k in ("valor", "nota", "parametro")] \
            + [g.get("legenda", "") for g in f.get("figuras", [])] + [n.get("texto", "") for n in f.get("notas", [])] \
            + [t.get("nota", "") for t in f.get("tabelas", [])]
        for t in textos:
            m = RX_PAG.search(t or "")
            if m:
                avisos.append(f"{os.path.basename(p)}: cita página: …{t[max(0, m.start() - 40):m.end() + 20]}…")

sem_texto = [n["id"] for n in normas if n["id"] not in lista]
for n in sem_texto:
    erros.append(f"norma sem texto completo: {n}")
for nid, v in lista.items():
    if not os.path.exists("dados/textos/" + v["arquivo"]):
        erros.append(f"arquivo de texto falta: {v['arquivo']}")
if not os.path.exists("dados/busca/_mapa.js"):
    erros.append("índice de busca no texto (dados/busca/) não existe — rodar indexar_textos.py")

for arq in ("index.html", "assets/app.js"):
    s = open(arq, encoding="utf-8").read()
    for m in re.finditer(r"referencias/", s):
        avisos.append(f"{arq}: menciona 'referencias/' (conferir se é só filtro de link): …{s[max(0, m.start() - 60):m.end() + 30]}…")

print(f"fichas: {len(glob.glob('conteudo/fichas/*.json'))}; imagens citadas: {n_fig}; normas: {len(normas)}; com texto: {len(lista)}")
for e in erros[:60]:
    print("ERRO", e)
for a in avisos[:40]:
    print("aviso", a)
print(f"{len(erros)} erros, {len(avisos)} avisos —", "OK p/ remover referencias/" if not erros else "NÃO remover referencias/ ainda")
