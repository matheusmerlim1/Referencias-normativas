"""Gera as fichas das especificações ASME II Partes A, B e C (2007) do acervo referencias/.

Para cada especificação: título, "Identical with ASTM…", escopo (item 1.1) e TODAS as tabelas (localizadas por
ferramentas/tabelas_asme_ii.py) recortadas como imagem preto e branco 150 dpi em assets/figuras/asme-ii/<parte>/.
Cada especificação vira um grupo da ficha e uma norma em conteudo/normas.json (id ASME-SA-106, ASME-SB-171, ASME-SFA-5.1…).
O texto de cada tabela entra na nota do requisito só para a busca achar (a ordem pode variar; vale a imagem).

uso: python -P ferramentas/gerar_asme_ii.py [A|B|C ...] [--gravar]   (sem --gravar: só lista)
"""
import glob
import io
import json
import os
import re
import sys

import pymupdf
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import tabelas_asme_ii as T

BASE = "referencias/extraido/ASME/ASME BPVC -2007"
PARTES = {
    "A": {"pasta": "ASME II PART A - 2007", "ficha": "especificacoes-asme-ii-a", "titulo": "Especificações ASME II Parte A — aços (SA)",
          "desc": "materiais ferrosos: chapas, tubos, forjados, fundidos, barras e parafusos"},
    "B": {"pasta": "ASME II PART B - 2007", "ficha": "especificacoes-asme-ii-b", "titulo": "Especificações ASME II Parte B — não ferrosos (SB)",
          "desc": "alumínio, cobre, níquel, titânio, zircônio e outras ligas não ferrosas"},
    "C": {"pasta": "ASME II PART C - 2007", "ficha": "especificacoes-asme-ii-c", "titulo": "Especificações ASME II Parte C — consumíveis de soldagem (SFA)",
          "desc": "eletrodos, varetas, arames e fluxos de soldagem e brasagem (AWS A5.x)"},
}


def codigo(arq):
    """'SA 1008-SA 1008M.pdf' → 'SA-1008/SA-1008M'; 'SA-EN 10028-2.pdf' → 'SA/EN 10028-2'."""
    n = os.path.splitext(os.path.basename(arq))[0]
    m = re.match(r"^(S[ABF]A?)-([A-Z]{2,4}[- ].+)$", n)
    if m:
        return f"{m.group(1)}/{m.group(2).replace('CSA-', 'CSA ')}"
    partes = n.split("-S")
    partes = [partes[0]] + ["S" + p for p in partes[1:]]
    return "/".join(re.sub(r"^(SFA|SA|SB|SF) ?(?=\d)", r"\1-", p.strip()) for p in partes)


def ident(cod):
    return "ASME-" + re.sub(r"[^A-Za-z0-9.]+", "-", cod.split("/")[0] if not cod.startswith(("SA/", "SB/")) else cod).strip("-")


def cabecalho(d):
    """título, 'Identical with…' e escopo 1.1 da 1ª página."""
    t = d[0].get_text()
    ls = [l.strip() for l in t.split("\n") if l.strip()]
    tit, ident_astm, i = [], "", 0
    while i < len(ls) and not ls[i].startswith(("SPECIFICATION", "STANDARD", "TEST METHOD", "PRACTICE", "GUIDE")):
        i += 1
    while i < len(ls) and ls[i].upper() == ls[i] and not re.match(r"^S[ABF]A?-", ls[i]) and not ls[i].startswith("("):
        tit.append(ls[i])
        i += 1
    m = re.search(r"\((Identical with[^)]*)\)", t.replace("\n", " "))
    if m:
        ident_astm = re.sub(r"\s+", " ", m.group(1))
    txt = re.sub(r"-\n(?=[a-z])", "", t)
    m = re.search(r"\n1\.1\s+(.*?)(?=\n1\.2\s|\nNOTE|\n2\.\s*\n|$)", txt, re.S)
    escopo = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    escopo = escopo.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return " ".join(tit).title().replace(" For ", " for ").replace(" And ", " and ").replace(" Of ", " of ").replace(" In ", " in ") or "", ident_astm, escopo


def salvar_1bit(d, t, arq, dpi=150):
    m = pymupdf.Matrix(dpi / 72, dpi / 72)
    if t.get("girar"):
        m = m.prerotate(90)
    pix = d[t["pagina"] - 1].get_pixmap(matrix=m, clip=t["bbox"], colorspace=pymupdf.csGRAY)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).point(lambda v: 255 if v > 150 else 0).convert("1")
    im.save(arq, "PNG", optimize=True)


def processar(parte, gravar):
    cfg = PARTES[parte]
    pasta_fig = f"assets/figuras/asme-ii/{parte.lower()}"
    if gravar:
        os.makedirs(pasta_fig, exist_ok=True)
    reqs, figs, normas, kws = [], [], [], []
    arqs = sorted(glob.glob(f"{BASE}/{cfg['pasta']}/*.pdf"),
                  key=lambda a: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", codigo(a).replace("/", " "))])  # pelo nº da spec
    for arq in arqs:
        nome = os.path.basename(arq)
        if nome.startswith(("INTRODUCTION", "SUMMARY")):
            continue
        cod = codigo(arq)
        nid = ident(cod)
        d, ts = T.tabelas(arq)
        tit, iastm, esc = cabecalho(d)
        grupo = f"{cod} — {tit}" if tit else cod
        kws.append(cod.split("/")[0])
        normas.append({"id": nid, "titulo": f"{cod} — {tit}", "edicao": f"2007 (BPVC Seção II, Parte {parte})", "orgao": "ASME",
                       "escopo": (esc[:300] + ("…" if len(esc) > 300 else "")) or tit, "arquivo": arq.replace("\\", "/")})
        if esc:
            reqs.append({"grupo": grupo, "parametro": "Escopo (1.1)", "valor": esc, "norma": nid, "item": "1.1", "pagina": 1,
                         **({"nota": iastm} if iastm else {})})
        elif iastm:
            reqs.append({"grupo": grupo, "parametro": "Origem", "valor": iastm, "norma": nid, "item": "título", "pagina": 1})
        if not ts:
            reqs.append({"grupo": grupo, "parametro": "Tabelas", "valor": "nenhuma tabela \"TABLE N\" localizada automaticamente — requisitos no texto; abrir o PDF",
                         "norma": nid, "item": "—", "pagina": 1, "nota": f"{len(d)} páginas."})
        for t in ts:
            slug = re.sub(r"[^a-z0-9]+", "-", f"{cod.split('/')[0]}-p{t['pagina']}-t{t['num']}".lower()).strip("-")
            n_ant = sum(1 for f in figs if f["arquivo"].startswith(f"asme-ii/{parte.lower()}/{slug}"))
            if n_ant:  # mesma tabela 2× na página (fim + "CONT'D", ou duas colunas)
                slug += f"-{n_ant + 1}"
            arq_png = f"asme-ii/{parte.lower()}/{slug}.png"
            if gravar:
                salvar_1bit(d, t, f"assets/figuras/{arq_png}")
            tt = re.sub(r"\s+", " ", t["titulo"]).strip()
            figs.append({"arquivo": arq_png, "legenda": f"{cod} — {tt}", "norma": nid, "item": tt.split(" ")[0] + " " + t["num"],
                         "pagina": t["pagina"], "grupo": grupo})
            reqs.append({"grupo": grupo, "parametro": tt.title().replace("Table", "Tabela"), "valor": "ver imagem da tabela neste grupo",
                         "norma": nid, "item": f"Table {t['num']}", "pagina": t["pagina"],
                         "nota": "Texto da tabela (para busca; ordem pode variar, vale a imagem): " + t["texto"][:450] + ("…" if len(t["texto"]) > 450 else "")})
        print(parte, cod, "|", tit[:60], "|", len(ts), "tabelas", "| escopo" if esc else "| SEM escopo")
    return cfg, reqs, figs, normas, kws


def gravar_ficha(parte, cfg, reqs, figs, normas, kws):
    f = f"conteudo/docs/{cfg['ficha']}.json"  # fonte; ver ferramentas/separar_normas.py
    d = {"id": cfg["ficha"], "titulo": cfg["titulo"], "categoria": "Materiais",
         "resumo": f"Especificações de material do ASME BPVC Seção II, Parte {parte} (2007) — {cfg['desc']}: escopo de cada especificação e TODAS as suas tabelas "
                   "(composição química, propriedades mecânicas, tolerâncias, ensaios) em imagem, com página.",
         "palavras_chave": ["especificação de material", "ASME II", f"Parte {parte}", "composição química", "chemical requirements", "tensile requirements",
                            "propriedades mecânicas", "ASTM"] + kws,
         "relacionadas": ["materiais-asme-ii-d", "propriedades-fisicas-asme-ii-d"] + [x for x in ("especificacoes-asme-ii-a", "especificacoes-asme-ii-b", "especificacoes-asme-ii-c") if x != cfg["ficha"]],
         "figuras": figs, "requisitos": reqs,
         "notas": [{"tipo": "atencao", "texto": "Edição 2007 da Seção II. Tensões admissíveis, Su/Sy em temperatura e propriedades físicas estão nas fichas da Parte D (2019) — ver Relacionadas."},
                   {"tipo": "info", "texto": "As tabelas estão como IMAGEM recortada da norma (sem transcrição). O texto anexado a cada tabela serve só para a busca."}]}
    open(f, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    p = "conteudo/normas.json"
    nn = json.load(open(p, encoding="utf-8"))
    ids = {x["id"]: x for x in nn}
    for x in normas:
        if x["id"] in ids:
            ids[x["id"]].update({k: v for k, v in x.items() if k != "id" and not ids[x["id"]].get(k)})
        else:
            nn.append(x)
    json.dump(nn, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("gravado", f, len(reqs), "req.,", len(figs), "figuras,", len(normas), "normas")


if __name__ == "__main__":
    gravar = "--gravar" in sys.argv
    for parte in [a for a in sys.argv[1:] if not a.startswith("--")] or ["A", "B", "C"]:
        res = processar(parte, gravar)
        if gravar:
            gravar_ficha(parte, *res)
