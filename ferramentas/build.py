"""Compila conteudo/ -> dados/dados.js (carregado pelo index.html).

Uso:  python ferramentas/build.py
Valida as fichas e aborta com a lista de erros se algo estiver inconsistente.

Dois tipos de ficha:
- temática (sem "tipo"): um assunto, várias normas (escada-degraus, flange-asme-b16-5…);
- de norma ("tipo": "norma"): UMA norma — campos extras "norma" (id em normas.json), "assunto", "edicao",
  "paginas", "arquivo", "escopo", "pagina_escopo", "definicoes" [{termo, texto, pagina}],
  "referencias_normativas" [códigos], "substitui" (texto ou lista). Requisitos/figuras/tabelas/palavras_chave podem ser vazios.

conteudo/docs/ (fichas-agrupamento antigas, só fonte) NÃO é carregado.

Gera DOIS arquivos (ver "REPOSITÓRIO PÚBLICO NO GITHUB" no CLAUDE.md):
- dados/dados.js       camada PÚBLICA (versionada): fichas temáticas só com figuras de assets/figuras/esquemas/ (as de norma
                       são omitidas, com AVISO), resumos (conteudo/resumos/*.json), normas.json só metadados, catálogo,
                       sinônimos e os SVGs citados por "cota";
- dados/dados_local.js tudo (fichas de norma, recortes de norma, cópias OCR) — no .gitignore; o index.html usa se existir.

Resumo de norma (conteudo/resumos/<slug>.json): {"id": "<id normas.json>", "titulo", "secoes": [{"titulo", "item", "texto",
  "valores": [{"parametro", "valor", "item", "cota"?, "nota"?}], "figuras": ["esquemas/x.svg"]}]}.
Cota: requisito/valor com "cota": "esquemas/<arquivo>.svg#<nome>" -> o SVG tem de ter <g id="cota-<nome>" class="cota">;
  o texto do SVG vai embutido nos dados ("svgs": {arquivo: svg}) porque em file:// não há fetch.
Cotas de TABELA: "cotas": {"<nome exato da coluna>": "esquemas/x.svg#<nome>"} (opcional) e, por convenção, coluna cuja
  1ª palavra é <p> ganha a cota se um SVG de esquemas/ em tabela.figuras tem id="cota-<p>" (o site faz a mesma regra).
  Coluna sem cota em tabela com esquema SVG -> só AVISO.
"""
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CONTEUDO = RAIZ / "conteudo"
FIGURAS = RAIZ / "assets" / "figuras"
SAIDA = RAIZ / "dados" / "dados.js"              # camada pública (versionada)
SAIDA_LOCAL = RAIZ / "dados" / "dados_local.js"  # build completo (camada local, .gitignore)
RESUMOS = CONTEUDO / "resumos"
PREFIXO_PROPRIO = "esquemas/"  # desenhos próprios: as únicas imagens da camada pública
RX_COTA = re.compile(r"^(esquemas/[^#]+\.svg)#([A-Za-z0-9_.\-]+)$")

CAMPOS_FICHA = ["id", "titulo", "categoria", "resumo", "palavras_chave", "requisitos"]
CAMPOS_FICHA_NORMA = ["id", "titulo", "categoria", "norma"]  # ficha "tipo": "norma"
TIPOS_FICHA = {None, "norma"}
# Campo opcional "tabelas": [{"id", "titulo", "norma", "item", "pagina", "unidade", "chave": {"classe": "150"},
#   "colunas": ["NPS", "O — Ø externo", ...], "linhas": [["1/2", 90, ...], ...], "nota"}]
# A 1ª coluna é a chave da linha (ex. NPS). "chave" agrupa tabelas para a calculadora consulta-tabela.
CAMPOS_REQ = ["grupo", "parametro", "valor", "norma", "item", "pagina"]
TIPOS_NOTA = {"atencao", "info", "dica"}
CALCULADORAS = {"escada", "escada-marinheiro", "consulta-tabela"}


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def validar(normas, fichas):
    erros = []
    ids_normas = {n["id"] for n in normas}
    ids_fichas = {f.get("id") for f in fichas}
    for n in normas:
        for c in ("id", "titulo", "arquivo"):
            if not n.get(c):
                erros.append(f"normas.json: norma sem '{c}': {n}")
    normas_com_ficha = {}
    for f in fichas:
        fid = f.get("id", "?")
        tipo = f.get("tipo")
        if tipo not in TIPOS_FICHA:
            erros.append(f"{fid}: 'tipo' inválido '{tipo}' (omita para ficha temática ou use 'norma')")
        for c in (CAMPOS_FICHA_NORMA if tipo == "norma" else CAMPOS_FICHA):
            if not f.get(c):
                erros.append(f"{fid}: campo obrigatório ausente '{c}'")
        for c in ("requisitos", "figuras", "tabelas", "notas", "palavras_chave", "relacionadas", "definicoes", "referencias_normativas"):
            if c in f and not isinstance(f[c], list):
                erros.append(f"{fid}: '{c}' deve ser lista")
        if tipo == "norma":
            nid = f.get("norma")
            if nid and nid not in ids_normas:
                erros.append(f"{fid}: 'norma' desconhecida '{nid}' (cadastre em normas.json)")
            if nid in normas_com_ficha:
                erros.append(f"{fid}: norma '{nid}' já tem a ficha '{normas_com_ficha[nid]}' (uma ficha por norma)")
            normas_com_ficha[nid] = fid
            for c in ("paginas", "pagina_escopo"):
                if f.get(c) is not None and not isinstance(f[c], int):
                    erros.append(f"{fid}: '{c}' deve ser inteiro")
            for i, d in enumerate(f.get("definicoes") or []):
                if not isinstance(d, dict) or not d.get("termo") or not d.get("texto"):
                    erros.append(f"{fid}: definição #{i + 1} precisa de 'termo' e 'texto'")
                elif d.get("pagina") is not None and not isinstance(d["pagina"], int):
                    erros.append(f"{fid}: definição '{d['termo']}' 'pagina' deve ser inteiro")
            for i, r in enumerate(f.get("referencias_normativas") or []):
                if not isinstance(r, str) or not r.strip():
                    erros.append(f"{fid}: referência normativa #{i + 1} deve ser texto (código da norma)")
            if f.get("substitui") is not None and not isinstance(f["substitui"], (str, list)):
                erros.append(f"{fid}: 'substitui' deve ser texto ou lista")
            f.setdefault("requisitos", [])
        for i, r in enumerate(f.get("requisitos", [])):
            for c in CAMPOS_REQ:
                if r.get(c) in (None, ""):
                    erros.append(f"{fid}: requisito #{i + 1} sem '{c}' ({r.get('parametro')})")
            if r.get("norma") and r["norma"] not in ids_normas:
                erros.append(f"{fid}: requisito #{i + 1} cita norma desconhecida '{r['norma']}' (cadastre em normas.json)")
            if r.get("pagina") is not None and not isinstance(r["pagina"], int):
                erros.append(f"{fid}: requisito #{i + 1} 'pagina' deve ser inteiro (página do PDF)")
        for fig in f.get("figuras", []):
            if not (FIGURAS / fig.get("arquivo", "")).is_file():
                erros.append(f"{fid}: figura não encontrada assets/figuras/{fig.get('arquivo')}")
            grupos_f = {r.get("grupo") for r in f.get("requisitos", [])}
            for g in ([fig["grupo"]] if isinstance(fig.get("grupo"), str) else fig.get("grupo", [])):
                if g not in grupos_f:
                    erros.append(f"{fid}: figura {fig.get('arquivo')} indica grupo inexistente '{g}'")
            if fig.get("norma") and fig["norma"] not in ids_normas:
                erros.append(f"{fid}: figura cita norma desconhecida '{fig['norma']}'")
        for n in f.get("notas", []):
            if n.get("tipo") not in TIPOS_NOTA:
                erros.append(f"{fid}: nota com tipo inválido '{n.get('tipo')}' (use {sorted(TIPOS_NOTA)})")
        for rel in f.get("relacionadas", []):
            if rel not in ids_fichas:
                print(f"  aviso: {fid} relaciona '{rel}', que ainda não existe")
        for t in f.get("tabelas", []):
            tid = t.get("id", "?")
            for c in ("id", "titulo", "norma", "item", "pagina", "colunas", "linhas"):
                if t.get(c) in (None, "", []):
                    erros.append(f"{fid}: tabela '{tid}' sem '{c}'")
            if t.get("norma") and t["norma"] not in ids_normas:
                erros.append(f"{fid}: tabela '{tid}' cita norma desconhecida '{t['norma']}'")
            if t.get("pagina") is not None and not isinstance(t["pagina"], int):
                erros.append(f"{fid}: tabela '{tid}' 'pagina' deve ser inteiro")
            # "figuras" opcional: desenhos com as cotas da tabela — caminhos relativos a assets/figuras/ (ou {"arquivo", "legenda"})
            figs_t = t.get("figuras", [])
            if not isinstance(figs_t, list):
                erros.append(f"{fid}: tabela '{tid}' 'figuras' deve ser lista")
                figs_t = []
            for x in figs_t:
                arq = x if isinstance(x, str) else (x.get("arquivo", "") if isinstance(x, dict) else "")
                if not arq or not (FIGURAS / arq).is_file():
                    erros.append(f"{fid}: tabela '{tid}' figura não encontrada assets/figuras/{arq}")
            n_col = len(t.get("colunas", []))
            for k, linha in enumerate(t.get("linhas", [])):
                if len(linha) != n_col:
                    erros.append(f"{fid}: tabela '{tid}' linha {k + 1} tem {len(linha)} valores para {n_col} colunas")
        if f.get("calculadora") == "consulta-tabela" and not f.get("tabelas"):
            erros.append(f"{fid}: calculadora 'consulta-tabela' exige o campo 'tabelas'")
        if f.get("calculadora") and f["calculadora"] not in CALCULADORAS:
            erros.append(f"{fid}: calculadora desconhecida '{f['calculadora']}' (disponíveis: {sorted(CALCULADORAS)})")
    vistos = set()
    for f in fichas:
        if f.get("id") in vistos:
            erros.append(f"id de ficha duplicado: {f.get('id')}")
        vistos.add(f.get("id"))
    return erros


def documentos():
    """Inventários de documentos (referencias.json e catalogo.json, se existirem), em forma enxuta para a busca."""
    docs = []
    for nome, origem in (("referencias.json", "referencias"), ("catalogo.json", "acervo T:")):
        caminho = CONTEUDO / nome
        if not caminho.is_file():
            continue
        for d in ler(caminho):
            if d.get("tipo") == "outro":
                continue
            docs.append({
                "codigo": d.get("codigo", ""), "titulo": d.get("titulo", ""), "orgao": d.get("orgao", ""),
                "edicao": d.get("edicao", ""), "tipo": d.get("tipo", ""), "situacao": d.get("situacao", ""),
                "arquivo": d.get("arquivo", ""), "paginas": d.get("paginas"),
                "assuntos": d.get("assuntos", []), "origem": origem,
            })
    return docs


def validar_resumos(normas, resumos):
    """Resumos próprios de norma (conteudo/resumos/*.json)."""
    erros = []
    ids_normas = {n["id"] for n in normas}
    vistos = {}
    for nome, r in resumos:
        rid = r.get("id")
        if not rid or rid not in ids_normas:
            erros.append(f"resumos/{nome}: 'id' deve ser uma norma de normas.json (veio '{rid}')")
        elif rid in vistos:
            erros.append(f"resumos/{nome}: norma '{rid}' já tem o resumo {vistos[rid]}")
        else:
            vistos[rid] = nome
        secoes = r.get("secoes")
        if not isinstance(secoes, list) or not secoes:
            erros.append(f"resumos/{nome}: 'secoes' deve ser lista não vazia")
            continue
        for i, sec in enumerate(secoes):
            if not isinstance(sec, dict) or not sec.get("titulo"):
                erros.append(f"resumos/{nome}: seção #{i + 1} sem 'titulo'")
                continue
            for c in ("valores", "figuras"):
                if c in sec and not isinstance(sec[c], list):
                    erros.append(f"resumos/{nome}: seção '{sec['titulo']}' '{c}' deve ser lista")
            for k, v in enumerate(sec.get("valores") or []):
                if not isinstance(v, dict) or not v.get("parametro") or v.get("valor") in (None, ""):
                    erros.append(f"resumos/{nome}: seção '{sec['titulo']}' valor #{k + 1} precisa de 'parametro' e 'valor'")
                elif "nota" in v and not (isinstance(v["nota"], str) and v["nota"].strip()):
                    erros.append(f"resumos/{nome}: seção '{sec['titulo']}' valor #{k + 1}: 'nota' deve ser texto não vazio")
            for x in sec.get("figuras") or []:
                arq = x if isinstance(x, str) else (x.get("arquivo", "") if isinstance(x, dict) else "")
                if not figura_propria(arq):
                    erros.append(f"resumos/{nome}: figura '{arq}' fora de assets/figuras/esquemas/ (resumo só usa desenho próprio)")
                elif not (FIGURAS / arq).is_file():
                    erros.append(f"resumos/{nome}: figura não encontrada assets/figuras/{arq}")
    return erros


def cotas_citadas(fichas, resumos):
    """[(origem, ref)] de todo "cota" em requisitos de fichas e em valores de resumos."""
    out = []
    for f in fichas:
        for r in f.get("requisitos", []):
            if r.get("cota"):
                out.append((f.get("id", "?"), r["cota"]))
    for nome, r in resumos:
        for sec in r.get("secoes") or []:
            if not isinstance(sec, dict):
                continue
            for v in sec.get("valores") or []:
                if isinstance(v, dict) and v.get("cota"):
                    out.append((f"resumos/{nome}", v["cota"]))
    return out


def primeira_palavra(coluna):
    """Convenção de cota de tabela: 1ª palavra da coluna ("O — Ø externo" -> "O", "tp" -> "tp"). Igual a app.js."""
    p = str(coluna).strip().split()
    return p[0] if p else ""


def ler_svg(arq):
    texto = (FIGURAS / arq).read_text(encoding="utf-8")
    texto = re.sub(r"<\?xml[^>]*\?>\s*", "", texto)
    texto = re.sub(r"<!DOCTYPE[^>]*>\s*", "", texto)
    return texto.strip()


def tem_id_cota(svg, nome):
    return bool(re.search(r"""\bid\s*=\s*["']cota-""" + re.escape(nome) + r"""["']""", svg))


def cotas_de_tabelas(fichas):
    """(erros, avisos, [(origem, ref)]) das tabelas: mapa "cotas" + convenção cota-<1ª palavra> nos SVG de tabela.figuras."""
    erros, avisos, refs, cache = [], [], [], {}
    for f in fichas:
        if f.get("tipo") == "norma":
            continue
        fid = f.get("id", "?")
        for t in f.get("tabelas", []):
            orig = f"{fid}: tabela '{t.get('id', '?')}'"
            cols = [str(c) for c in t.get("colunas", [])]
            mapa = t.get("cotas")
            if mapa is not None and not isinstance(mapa, dict):
                erros.append(f"{orig} 'cotas' deve ser objeto {{coluna: 'esquemas/x.svg#nome'}}")
                mapa = None
            mapa = mapa or {}
            for col, ref in mapa.items():
                if col not in cols:
                    erros.append(f"{orig} 'cotas' cita a coluna '{col}', que não existe")
                refs.append((orig + f" coluna '{col}'", ref))
            svgs_t = []
            for x in t.get("figuras", []) or []:
                arq = x if isinstance(x, str) else (x.get("arquivo", "") if isinstance(x, dict) else "")
                if figura_propria(arq) and arq.endswith(".svg") and (FIGURAS / arq).is_file():
                    if arq not in cache:
                        cache[arq] = ler_svg(arq)
                    svgs_t.append(arq)
            sem = []
            for col in cols:
                if col in mapa:
                    continue
                w = primeira_palavra(col)
                arq = next((a for a in svgs_t if w and re.fullmatch(r"[A-Za-z0-9_.\-]+", w) and tem_id_cota(cache[a], w)), None)
                if arq:
                    refs.append((orig + f" coluna '{col}' (convenção)", f"{arq}#{w}"))
                elif col != cols[0]:
                    sem.append(col)
            if (svgs_t or mapa) and sem:
                avisos.append(f"{orig}: {len(sem)} coluna(s) sem cota: " + ", ".join(f"'{c}'" for c in sem[:6])
                              + (" …" if len(sem) > 6 else ""))
    return erros, avisos, refs


def svgs_das_cotas(cotas):
    """Valida as cotas e devolve (erros, {arquivo: texto do svg}) — o site desenha o SVG inline (file:// não faz fetch)."""
    erros, svgs = [], {}
    for origem, ref in cotas:
        m = RX_COTA.match(ref) if isinstance(ref, str) else None
        if not m:
            erros.append(f"{origem}: cota '{ref}' fora do formato 'esquemas/<arquivo>.svg#<nome>'")
            continue
        arq, nome = m.groups()
        if arq not in svgs:
            caminho = FIGURAS / arq
            if not caminho.is_file():
                erros.append(f"{origem}: cota '{ref}': arquivo assets/figuras/{arq} não existe")
                continue
            svgs[arq] = ler_svg(arq)
        if not tem_id_cota(svgs[arq], nome):
            erros.append(f"{origem}: cota '{ref}': o SVG não tem o grupo id=\"cota-{nome}\"")
    return erros, svgs


def figura_propria(arq):
    return isinstance(arq, str) and arq.startswith(PREFIXO_PROPRIO)


def ficha_publica(f, omitidas):
    """Cópia da ficha temática sem imagens de norma (recortes/páginas); conta as omitidas em omitidas[ficha]."""
    g = dict(f)
    figs = f.get("figuras", [])
    g["figuras"] = [x for x in figs if figura_propria(x.get("arquivo"))]
    n = len(figs) - len(g["figuras"])
    if f.get("tabelas"):
        tabs = []
        for t in f["tabelas"]:
            if t.get("figuras"):
                t = dict(t)
                antes = len(t["figuras"])
                t["figuras"] = [x for x in t["figuras"]
                                if figura_propria(x if isinstance(x, str) else (x.get("arquivo") if isinstance(x, dict) else None))]
                n += antes - len(t["figuras"])
            tabs.append(t)
        g["tabelas"] = tabs
    if n:
        omitidas[f["id"]] = n
    return g


def gravar(caminho, dados):
    caminho.parent.mkdir(exist_ok=True)
    caminho.write_text(
        "// Gerado por ferramentas/build.py — não edite à mão.\nwindow.UVA_DADOS = "
        + json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )


def main():
    normas = ler(CONTEUDO / "normas.json")
    sinonimos = ler(CONTEUDO / "sinonimos.json")
    arquivos = sorted((CONTEUDO / "fichas").glob("*.json"))
    fichas = []
    for a in arquivos:
        try:
            fichas.append(ler(a))
        except json.JSONDecodeError as e:
            print(f"ERRO: JSON inválido em {a.name}: {e}")
            sys.exit(1)
    resumos = []
    if RESUMOS.is_dir():
        for a in sorted(RESUMOS.glob("*.json")):
            try:
                resumos.append((a.name, ler(a)))
            except json.JSONDecodeError as e:
                print(f"ERRO: JSON inválido em resumos/{a.name}: {e}")
                sys.exit(1)
    erros = validar(normas, fichas) + validar_resumos(normas, resumos)
    erros_tab, avisos_tab, refs_tab = cotas_de_tabelas(fichas)
    erros_cota, svgs = svgs_das_cotas(cotas_citadas(fichas, resumos) + refs_tab)
    erros += erros_tab + erros_cota
    if avisos_tab:
        print(f"  aviso: {len(avisos_tab)} tabela(s) com esquema SVG têm coluna(s) sem cota (mapa 'cotas' ou id cota-<1ª palavra>):")
        for a in avisos_tab[:12]:
            print("   ", a)
        if len(avisos_tab) > 12:
            print(f"    … + {len(avisos_tab) - 12}")
    if erros:
        print("ERROS de validação:")
        for e in erros:
            print("  -", e)
        sys.exit(1)
    lista_resumos = [r for _, r in resumos]
    docs = documentos()

    # ---- camada LOCAL (tudo, como antes): dados/dados_local.js
    # cópias OCR (referencias/ocr/*.pdf) -> PDF original: o site usa para achar o sumário em dados/indice.js
    origem_ocr = RAIZ / "referencias" / "ocr" / "_origem.json"
    local = {"publico": False, "normas": normas, "fichas": fichas, "sinonimos": sinonimos, "documentos": docs,
             "resumos": lista_resumos, "svgs": svgs,
             "ocr_origem": ler(origem_ocr) if origem_ocr.is_file() else {}}
    gravar(SAIDA_LOCAL, local)

    # ---- camada PÚBLICA: dados/dados.js (sem fichas de norma nem imagens de norma; normas só metadados)
    omitidas = {}
    tematicas = [ficha_publica(f, omitidas) for f in fichas if f.get("tipo") != "norma"]
    publico = {
        "publico": True,
        "normas": [{k: n[k] for k in ("id", "titulo", "edicao", "orgao", "escopo") if n.get(k)} for n in normas],
        "fichas": tematicas, "sinonimos": sinonimos,
        "documentos": [d for d in docs if d["origem"] != "referencias"],  # só o catálogo do acervo
        "resumos": lista_resumos, "svgs": svgs, "ocr_origem": {},
    }
    gravar(SAIDA, publico)
    texto_pub = SAIDA.read_text(encoding="utf-8")
    vaza = sorted(set(re.findall(r'"((?:docs|tem|asme-ii)/[^"]+\.(?:png|jpe?g|gif|webp)|[^"/]+\.png)"', texto_pub)))
    if vaza:
        print(f"ERRO: dados.js público ainda cita {len(vaza)} imagem(ns) da camada local, ex.: {vaza[:5]}")
        sys.exit(1)

    n_req = sum(len(f["requisitos"]) for f in fichas)
    n_norma = sum(f.get("tipo") == "norma" for f in fichas)
    tam = lambda p: f"{p.stat().st_size / 1e6:.1f} MB"
    print(f"OK: {len(fichas)} fichas ({len(fichas) - n_norma} temáticas, {n_norma} de norma), {n_req} requisitos, {len(normas)} normas, "
          f"{len(docs)} documentos, {len(lista_resumos)} resumos, {len(svgs)} SVG de cota -> "
          f"{SAIDA_LOCAL.relative_to(RAIZ)} ({tam(SAIDA_LOCAL)})")
    print(f"OK: camada pública: {len(tematicas)} fichas temáticas, {len(lista_resumos)} resumos, "
          f"{len(publico['documentos'])} documentos -> {SAIDA.relative_to(RAIZ)} ({tam(SAIDA)})")
    if omitidas:
        print(f"  AVISO: {sum(omitidas.values())} figura(s) de norma OMITIDAS na versão pública, em {len(omitidas)} ficha(s) temática(s) "
              f"(substituir por desenho próprio em assets/figuras/esquemas/):")
        for fid, n in sorted(omitidas.items(), key=lambda x: -x[1]):
            print(f"    {fid}: {n}")


if __name__ == "__main__":
    main()
