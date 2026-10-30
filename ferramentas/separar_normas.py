"""Gera UMA ficha por norma (conteudo/fichas/norma-<id>.json, "tipo": "norma").

Fontes:
  conteudo/docs/*.json       fichas-agrupamento geradas por gerar_docs.py / gerar_asme_ii.py (recortes de tabelas/figuras por documento)
  conteudo/normas.json       registro das normas (título, edição, órgão, arquivo, escopo)
  conteudo/escopo_manual.json escopo transcrito à mão onde info_normas.py não acha (NRs sem item "Objetivo")
  conteudo/normas_info.json  escopo, definições, referências normativas, nº de páginas (ferramentas/info_normas.py), se existir
  conteudo/fichas/*.json     fichas temáticas: dão o "assunto" e as "relacionadas" de cada norma
Toda norma de normas.json ganha ficha; os valores das fichas temáticas NÃO são copiados (o site os mostra na página da norma).

uso: python -P ferramentas/separar_normas.py [--gravar]      (sem --gravar: só conta)
"""
import glob
import json
import os
import re
import sys

DOCS = "conteudo/docs"
FICHAS = "conteudo/fichas"
GRUPO_TIPO = {"Tabela": "Tabelas", "Fig.": "Figuras", "pág.": "Páginas com desenho ou tabela (sem título localizável)"}


def orgao(n):
    """órgão-base p/ agrupar no índice ("ABNT (ABNT/CB-50…)" → ABNT, "MTE (Brasil)" → NR, "DNV GL" → DNV); o nome completo fica em "orgao"."""
    o, nid = n.get("orgao") or "", n["id"]
    if nid.startswith("NR-"):
        return "NR"
    if nid.startswith(("EQN-",)):
        return "Equinor"
    for b in ("ABNT", "ASME", "ASTM", "ABS", "ANSI", "API", "DNV", "ISO", "NORSOK", "DIN", "AWS", "BS", "BV", "IMCA"):
        if o.split(" ")[0].split("/")[0] == b or o.startswith(b + " "):
            return b
    return o if o and "(" not in o else "Outros"


def slug(nid):
    return "norma-" + re.sub(r"[^a-z0-9]+", "-", nid.lower()).strip("-")


def ler(p):
    return json.load(open(p, encoding="utf-8"))


def main(gravar):
    normas = ler("conteudo/normas.json")
    info = ler("conteudo/normas_info.json") if os.path.exists("conteudo/normas_info.json") else {}
    # escopo transcrito à mão (ferramentas não acham: NR sem item "Objetivo"…) — só vale onde normas_info não tem escopo
    for arq in ("conteudo/escopo_manual.json", "conteudo/escopo_manual_agente.json"):
        for k, v in (ler(arq) if os.path.exists(arq) else {}).items():
            if not info.get(k, {}).get("escopo") or k in ("ASME-I-2007", "BV-NR445-B", "DNV-2.22"):  # estes: escopo de subitem
                info.setdefault(k, {}).update(v)
    tematicas = [ler(p) for p in sorted(glob.glob(f"{FICHAS}/*.json"))]
    tematicas = [f for f in tematicas if f.get("tipo") != "norma"]
    agrup = [ler(p) for p in sorted(glob.glob(f"{DOCS}/*.json"))]

    # requisitos/figuras de cada norma nas fichas-agrupamento; grupo original guardado p/ livros de código (UG-, UW-…)
    por = {}
    for f in agrup:
        normas_f = {r["norma"] for r in f["requisitos"]}
        so_um = len(normas_f) == 1  # ficha de um documento só (VIII-1, IX…): os grupos já são as partes do código
        for r in f["requisitos"]:
            e = por.setdefault(r["norma"], {"req": [], "fig": [], "assunto": f["categoria"], "origem": f["id"], "kw": f.get("palavras_chave", [])})
            r = dict(r)
            if not so_um and r["item"] != "—":
                r["grupo"] = GRUPO_TIPO.get(r["item"].split(" ")[0], r["grupo"])
            e["req"].append(r)
        for g in f.get("figuras", []):
            g = dict(g)
            if not so_um:
                g["grupo"] = GRUPO_TIPO.get(g["item"].split(" ")[0], g.get("grupo"))
            por.setdefault(g["norma"], {"req": [], "fig": [], "assunto": f["categoria"], "origem": f["id"], "kw": []})["fig"].append(g)

    citada = {}  # norma -> fichas temáticas que a citam
    for f in tematicas:
        for n in {r["norma"] for r in f.get("requisitos", [])} | {t["norma"] for t in f.get("tabelas", []) if t.get("norma")} \
                | {g["norma"] for g in f.get("figuras", []) if g.get("norma")}:
            citada.setdefault(n, []).append(f)

    novos, n_req, n_fig = [], 0, 0
    for n in normas:
        nid = n["id"]
        e = por.get(nid, {"req": [], "fig": [], "assunto": None, "kw": []})
        tem = citada.get(nid, [])
        inf = info.get(nid, {})
        assunto = e["assunto"] or (tem[0]["categoria"] if tem else None)
        # código legível: só o 1º hífen vira espaço ("ISO-898-1" → "ISO 898-1", "NBR-14718" → "NBR 14718"); NR/DNV ficam como estão
        cod = nid if re.match(r"^(NR|DNV|DNVGL|EQN)-", nid) else nid.replace("-", " ", 1)
        tit = n.get("titulo", "")
        seg = tit.split(" — ", 1)
        if len(seg) == 2 and re.split(r"[^A-Za-z0-9]+", nid)[-1].lower() in re.sub(r"[^a-z0-9]", "", seg[0].lower()):
            tit = seg[1]  # título já começa pelo código ("SA-106 — Specification…"): não repetir
        escopo = (inf.get("escopo") or n.get("escopo") or "").strip()
        if escopo == n.get("titulo"):
            escopo = ""
        ordem = []
        for r in e["req"]:  # ordem dos grupos: "Documento" primeiro, depois como vieram
            if r["grupo"] not in ordem:
                ordem.append(r["grupo"])
        reqs = sorted(e["req"], key=lambda r: (r["item"] != "—", ordem.index(r["grupo"])))
        d = {"id": slug(nid), "tipo": "norma", "norma": nid, "titulo": f"{cod} — {tit}".strip(" —"),
             "categoria": orgao(n), "orgao": n.get("orgao"), "assunto": assunto,
             "resumo": (escopo[:280] + ("…" if len(escopo) > 280 else "")) if escopo else n.get("titulo", ""),
             "palavras_chave": sorted({nid, cod, n.get("orgao") or ""} - {""}),
             "relacionadas": sorted({f["id"] for f in tem}),
             "edicao": n.get("edicao"), "paginas": inf.get("paginas"), "arquivo": n.get("arquivo"),
             "escopo": escopo or None, "pagina_escopo": inf.get("pagina_escopo"), "nota_escopo": inf.get("nota_escopo"),
             "definicoes": inf.get("definicoes") or None, "referencias_normativas": inf.get("referencias_normativas") or None,
             "substitui": inf.get("substitui") or None,
             "figuras": e["fig"], "requisitos": reqs}
        d = {k: v for k, v in d.items() if v not in (None, [], "")}
        d.setdefault("figuras", [])
        d.setdefault("requisitos", [])
        novos.append(d)
        n_req += len(reqs)
        n_fig += len(e["fig"])
    print(f"{len(novos)} fichas de norma; {n_req} itens; {n_fig} imagens; com escopo {sum('escopo' in d for d in novos)}; "
          f"com definições {sum('definicoes' in d for d in novos)}; citadas em fichas temáticas {sum(bool(d.get('relacionadas')) for d in novos)}")
    if gravar:
        for p in glob.glob(f"{FICHAS}/norma-*.json"):
            os.remove(p)  # regera todas (norma removida/renomeada não deixa arquivo órfão)
        for d in novos:
            open(f"{FICHAS}/{d['id']}.json", "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        print("gravadas em", FICHAS)


if __name__ == "__main__":
    main("--gravar" in sys.argv)
