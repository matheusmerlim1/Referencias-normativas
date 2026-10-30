"""Acrescenta PÁGINA INTEIRA (imagem) nas fichas-fonte (conteudo/docs/) para páginas de normas ESCANEADAS com tabela/desenho
que nenhum recorte cobriu — o gerar_docs pula páginas escaneadas na passagem "desenho sem título" e o OCR de tabela não basta.
A lista vem da auditoria (detector por imagem: grade H/V, números curtos no OCR, tinta fora das palavras, legenda):
  {"faltando": [{"norma", "pagina", "motivo", "arquivo_ocr"}, ...]}
("girar": graus anti-horário p/ página de lado; "forcar": acrescenta mesmo se a página já tem recorte — recorte truncado)
ou legendas de tabela/figura sem recorte (texto nativo): {"faltando": [{"norma", "pagina", "legenda"}]} — PDF de normas.json.
Idempotente: página que já tem figura da mesma norma é pulada. Depois: separar_normas.py --gravar e build.py.
uso: python -P ferramentas/completar_escaneadas.py <lista.json> [--gravar]
"""
import glob
import json
import os
import re
import sys

import pymupdf
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import recortes as R  # noqa: E402

# falsos positivos conferidos na imagem (capa, comitê, texto com moldura)
EXCLUIR = {("ISO-4014", 3), ("BS-4504-3.1", 41), ("ASME-B18.2.3.7M", 7), ("ASME-B16.34", 202)}
if os.path.exists("conteudo/completar/excluir.json"):  # capas, avisos, formulários, slides, texto puro (auditoria das miniaturas)
    EXCLUIR |= {(x["norma"], x["pagina"]) for x in json.load(open("conteudo/completar/excluir.json", encoding="utf-8"))}

gravar = "--gravar" in sys.argv
docs = {p.replace("\\", "/"): json.load(open(p, encoding="utf-8")) for p in glob.glob("conteudo/docs/*.json")}
if sys.argv[1] == "--limpar":  # tira das fichas-fonte as páginas inteiras acrescentadas (-esc/-leg) que estão em EXCLUIR
    n = 0
    for p, d in docs.items():
        sai = [g for g in d["figuras"] if (g["norma"], g["pagina"]) in EXCLUIR and re.search(r"-(esc|leg)\.png$", g["arquivo"])]
        if not sai:
            continue
        ks = {(g["norma"], g["pagina"]) for g in sai}
        d["figuras"] = [g for g in d["figuras"] if g not in sai]
        d["requisitos"] = [r for r in d["requisitos"] if not ((r["norma"], r["pagina"]) in ks and r["item"] == f"pág. {r['pagina']}")]
        n += len(sai)
        if gravar:
            for g in sai:
                if os.path.exists("assets/figuras/" + g["arquivo"]):
                    os.remove("assets/figuras/" + g["arquivo"])
            open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print(f"{n} páginas inteiras excluídas" + ("" if gravar else " (simulação)"))
    sys.exit()
lista = json.load(open(sys.argv[1], encoding="utf-8"))["faltando"]
normas = {n["id"]: n for n in json.load(open("conteudo/normas.json", encoding="utf-8"))}
TEM = "conteudo/docs/recortes-normas-tematicas.json"  # norma sem ficha-fonte (ex. ASME II-D, só transcrita nas temáticas)


def doc_da_norma(n):
    cand = [p for p, d in docs.items() if any(r["norma"] == n for r in d["requisitos"])]
    cand.sort(key=lambda p: "recortes-normas-tematicas" in p)  # prefere a ficha-fonte do órgão
    return cand[0] if cand else None


pdfs, novos, mudou = {}, 0, set()
for x in lista:
    n, pag = x["norma"], x["pagina"]
    p = doc_da_norma(n)
    if (n, pag) in EXCLUIR or n not in normas:
        continue
    novo = not p
    p = p or TEM
    d = docs[p]
    # pula página que já tem imagem inteira; com "legenda" (tabela/figura sem recorte) a página pode ter OUTRO recorte
    if any(g["norma"] == n and g["pagina"] == pag and (g["item"].startswith("pág.") or not (x.get("legenda") or x.get("forcar"))) for g in d["figuras"]):
        continue
    grupos = [r["grupo"] for r in d["requisitos"] if r["norma"] == n]
    g = max(set(grupos), key=grupos.count) if grupos else f"{n.replace('ASME-', 'ASME ')} — {normas[n]['titulo']}"
    if novo and not grupos:
        d["requisitos"].append({"grupo": g, "parametro": "Documento", "valor": normas[n]["titulo"], "norma": n, "item": "—", "pagina": 1})
    fid = os.path.basename(p)[:-5]
    slug = re.sub(r"[^a-z0-9]+", "-", f"{n}-p{pag}-p-{pag}-{'leg' if x.get('legenda') else 'esc'}".lower()).strip("-")
    arq = f"docs/{fid}/{slug}.png"
    arq_pdf = x.get("arquivo_ocr") or normas[n]["arquivo"]
    if gravar:
        if arq_pdf not in pdfs:
            pdfs[arq_pdf] = pymupdf.open(stream=open(arq_pdf, "rb").read(), filetype="pdf")
        pdf = pdfs[arq_pdf]
        os.makedirs(f"assets/figuras/docs/{fid}", exist_ok=True)
        R.salvar_1bit(pdf, {"pagina": pag, "bbox": pdf[pag - 1].rect + (20, 30, -20, -40)}, f"assets/figuras/{arq}")
        if x.get("girar"):  # página de lado: graus anti-horário (PIL)
            Image.open(f"assets/figuras/{arq}").rotate(x["girar"], expand=True).save(f"assets/figuras/{arq}", optimize=True)
    tit = f"Página {pag} — {x['legenda']}" if x.get("legenda") else f"Página {pag} (tabela/desenho em página escaneada)"
    d["figuras"].append({"arquivo": arq, "legenda": tit, "norma": n, "item": f"pág. {pag}", "pagina": pag, "grupo": g})
    reqs = d["requisitos"]
    pos = max([i + 1 for i, r in enumerate(reqs) if r["norma"] == n and r["grupo"] == g and r["pagina"] <= pag]
              or [max(i + 1 for i, r in enumerate(reqs) if r["norma"] == n and r["grupo"] == g)])
    reqs.insert(pos, {"grupo": g, "parametro": tit, "valor": "ver imagem neste grupo", "norma": n, "item": f"pág. {pag}",
                      "pagina": pag, "nota": "Página inteira (tabela/figura sem recorte localizável)." if x.get("legenda")
                      else "Página inteira (tabela/desenho em página escaneada; o texto OCR da tabela não basta)."})
    novos += 1
    mudou.add(p)

for p in mudou:
    if gravar:
        open(p, "w", encoding="utf-8").write(json.dumps(docs[p], ensure_ascii=False, indent=1) + "\n")
print(f"{novos} páginas inteiras novas em {len(mudou)} fichas-fonte" + ("" if gravar else " (simulação; --gravar para gravar)"))
