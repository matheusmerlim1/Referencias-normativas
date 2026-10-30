"""Valores dimensionais dos resumos (conteudo/resumos/) ainda sem "cota" — guia dos lotes de desenhos próprios.

uso: python -P ferramentas/cotas_pendentes.py                 → resumo por órgão + lista ordenada (uso nas temáticas, nº pendente)
     python -P ferramentas/cotas_pendentes.py <slug> [...]    → valores pendentes desses resumos (ex. norma-nr-15), com índice seção.valor
     python -P ferramentas/cotas_pendentes.py --svg           → SVGs de esquemas/ que nenhum resumo/ficha cita
     python -P ferramentas/cotas_pendentes.py --sem-desenho   → resumos sem nenhum desenho (nem "figuras" nem "cota")

"Dimensional" = valor com número seguido de mm, cm, m, in, pol, ° ou " (fora °C, m/s, m², m³). O regex não distingue
faixa de aplicação ("parede até 5 mm") de medida: quem faz o lote decide e, se o valor NÃO leva desenho, registra em
conteudo/cotas_dispensadas.json → {"norma-<slug>": {"<parametro exato>": "motivo"}} — a ferramenta deixa de listá-lo.
"""
import collections
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIM = re.compile(r'\d\s*(mm|cm|m|in\.?|pol|°|")(\b|$|\s|,|;|\))')
NAO_DIM = re.compile(r'°\s*C|°C|\bm/s|m/s²|m³|m²')  # temperatura, velocidade, aceleração, área, volume


def carregar(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


DISPENSADAS = os.path.join(RAIZ, "conteudo", "cotas_dispensadas.json")


def dispensadas():
    return carregar(DISPENSADAS) if os.path.exists(DISPENSADAS) else {}


def pendentes(d, disp=None):
    disp = disp or {}
    for i, s in enumerate(d.get("secoes", [])):
        for j, v in enumerate(s.get("valores", [])):
            val = str(v.get("valor", ""))
            if DIM.search(val) and not NAO_DIM.search(val) and not v.get("cota") and v.get("parametro") not in disp:
                yield f"{i}.{j}", s.get("titulo", ""), v


def uso_tematicas():
    uso = collections.Counter()
    for p in glob.glob(os.path.join(RAIZ, "conteudo", "fichas", "*.json")):
        if not os.path.basename(p).startswith("norma-"):
            uso.update(r.get("norma") for r in carregar(p).get("requisitos", []))
    return uso


def main(args):
    resumos = {os.path.basename(p)[:-5]: p for p in glob.glob(os.path.join(RAIZ, "conteudo", "resumos", "*.json"))}
    if args and args[0] == "--svg":
        citados = set()
        for p in list(resumos.values()) + glob.glob(os.path.join(RAIZ, "conteudo", "fichas", "*.json")):
            citados.update(re.findall(r"esquemas/([\w.\-]+\.svg)", open(p, encoding="utf-8").read()))
        for p in sorted(glob.glob(os.path.join(RAIZ, "assets", "figuras", "esquemas", "*.svg"))):
            if os.path.basename(p) not in citados:
                print(os.path.basename(p))
        return
    if args and args[0] == "--sem-desenho":
        for slug, p in sorted(resumos.items()):
            d = carregar(p)
            if not any(s.get("figuras") or any(v.get("cota") for v in s.get("valores", [])) for s in d.get("secoes", [])):
                print(f"{slug} — {d.get('titulo', '')[:90]}")
        return
    if args:
        for slug in args:
            slug = slug if slug.startswith("norma-") else "norma-" + slug
            d = carregar(resumos[slug])
            print(f"## {slug}")
            for k, tit, v in pendentes(d, dispensadas().get(slug)):
                print(f"  {k} [{tit[:40]}] {v.get('parametro', '')[:90]} = {str(v.get('valor', ''))[:70]}")
        return
    uso, disp = uso_tematicas(), dispensadas()
    orfas = [(s, p) for s, ps in disp.items() for p in ps
             if s not in resumos or not any(v.get("parametro") == p for x in carregar(resumos[s]).get("secoes", []) for v in x.get("valores", []))]
    for s, p in orfas:
        print(f"AVISO: cotas_dispensadas.json cita parâmetro inexistente: {s} / {p[:60]}")
    linhas, por_org, com_cota = [], collections.Counter(), 0
    for slug, p in resumos.items():
        d = carregar(p)
        com_cota += sum(1 for s in d.get("secoes", []) for v in s.get("valores", []) if v.get("cota"))
        n = sum(1 for _ in pendentes(d, disp.get(slug)))
        if n:
            linhas.append((uso.get(d.get("id"), 0), n, slug))
            por_org[re.sub(r"^norma-([a-z]+(?:-s[abf])?).*", r"\1", slug)] += n
    print(f"{com_cota} valores com cota; {sum(map(len, disp.values()))} dispensados (cotas_dispensadas.json); "
          f"{sum(l[1] for l in linhas)} dimensionais sem cota em {len(linhas)} resumos")
    print("por órgão: " + ", ".join(f"{k} {v}" for k, v in por_org.most_common()))
    for u, n, slug in sorted(linhas, key=lambda l: (-l[0], -l[1], l[2])):
        print(f"  {slug} ({n})" + (f" — {u} req. nas temáticas" if u else ""))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
