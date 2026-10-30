"""Valores dimensionais dos resumos (conteudo/resumos/) ainda sem "cota" — guia dos lotes de desenhos próprios.

uso: python -P ferramentas/cotas_pendentes.py                 → resumo por órgão + lista ordenada (uso nas temáticas, nº pendente)
     python -P ferramentas/cotas_pendentes.py <slug> [...]    → valores pendentes desses resumos (ex. norma-nr-15), com índice seção.valor
     python -P ferramentas/cotas_pendentes.py --svg           → SVGs de esquemas/ que nenhum resumo/ficha cita

"Dimensional" = valor com número seguido de mm, cm, m, in, pol, ° ou ". Faixas de aplicação ("parede até 5 mm") e
temperaturas com ° entram na contagem — o regex não distingue; quem faz o lote decide e pula o que não é medida.
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


def pendentes(d):
    for i, s in enumerate(d.get("secoes", [])):
        for j, v in enumerate(s.get("valores", [])):
            val = str(v.get("valor", ""))
            if DIM.search(val) and not NAO_DIM.search(val) and not v.get("cota"):
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
    if args:
        for slug in args:
            d = carregar(resumos[slug if slug.startswith("norma-") else "norma-" + slug])
            print(f"## {slug}")
            for k, tit, v in pendentes(d):
                print(f"  {k} [{tit[:40]}] {v.get('parametro', '')[:90]} = {str(v.get('valor', ''))[:70]}")
        return
    uso = uso_tematicas()
    linhas, por_org, com_cota = [], collections.Counter(), 0
    for slug, p in resumos.items():
        d = carregar(p)
        com_cota += sum(1 for s in d.get("secoes", []) for v in s.get("valores", []) if v.get("cota"))
        n = sum(1 for _ in pendentes(d))
        if n:
            linhas.append((uso.get(d.get("id"), 0), n, slug))
            por_org[re.sub(r"^norma-([a-z]+(?:-s[abf])?).*", r"\1", slug)] += n
    print(f"{com_cota} valores com cota; {sum(l[1] for l in linhas)} dimensionais sem cota em {len(linhas)} resumos")
    print("por órgão: " + ", ".join(f"{k} {v}" for k, v in por_org.most_common()))
    for u, n, slug in sorted(linhas, key=lambda l: (-l[0], -l[1], l[2])):
        print(f"  {slug} ({n})" + (f" — {u} req. nas temáticas" if u else ""))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
