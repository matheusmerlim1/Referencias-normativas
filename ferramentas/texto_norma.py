"""Mostra o texto completo extraído de uma norma (dados/textos/, camada local) — para escrever o resumo próprio.

uso: python -P ferramentas/texto_norma.py <ID> [pág-inicial [pág-final]]     (ID de normas.json, ex. PETROBRAS-N-0013)
     python -P ferramentas/texto_norma.py <ID> --paginas                   → só o nº de páginas e caracteres por página
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def paginas(nid):
    slug = "norma-" + re.sub(r"[^a-z0-9]+", "-", nid.lower()).strip("-")
    p = os.path.join(RAIZ, "dados", "textos", slug + ".js")
    t = open(p, encoding="utf-8").read()
    return json.loads(t[t.index("] = [") + 4:].rstrip().rstrip(";"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    nid = sys.argv[1]
    pgs = paginas(nid)
    if "--paginas" in sys.argv:
        print(f"{nid}: {len(pgs)} págs., {sum(map(len, pgs))} caracteres")
        print(" ".join(f"{k}:{len(p)}" for k, p in enumerate(pgs, 1)))
        sys.exit()
    ini = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    fim = int(sys.argv[3]) if len(sys.argv) > 3 else len(pgs)
    for k in range(ini, fim + 1):
        print(f"=== pág. {k}\n{pgs[k - 1]}")
