"""Triagem de conteudo/referencias.json → conteudo/triagem_referencias.json (+ resumo no terminal).

Para cada documento: situação (incorporada / pendente / superada / sem texto / fora de escopo), prioridade pelo assunto
e edição mais nova do mesmo código no acervo. Rodar de novo depois de incorporar normas (lê conteudo/normas.json).
Uso: python -P ferramentas/triagem_referencias.py
"""
import collections
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONT = RAIZ / "conteudo"

# prioridade por assunto (1 = alta: temas das fichas / backlog; 3 = baixa)
PRIORIDADE = {
    "guarda-corpo": 1, "passarela/plataforma": 1, "escada": 1, "grating": 1, "trabalho em altura/queda": 1,
    "segurança de máquinas": 1, "ergonomia/fatores humanos": 1, "içamento/movimentação de carga": 1,
    "flange": 1, "tubulação": 1, "solda": 1, "parafuso/porca/arruela": 1, "tolerâncias/desenho técnico": 1,
    "estrutura metálica": 1, "pintura/revestimento": 1, "junta/gaxeta": 1, "segurança do trabalho (NR)": 1,
    "offshore/naval": 2, "válvula": 2, "vaso de pressão/caldeira": 2, "rosca": 2, "materiais/ensaios": 2,
    "hidráulica": 3, "medição de vazão": 3, "engrenagens/transmissão": 3, "perfuração/poço": 3, "elétrica": 3,
}


# documentos substituídos por norma mais nova já cadastrada (código no inventário → id em normas.json)
SUBSTITUIDAS = {"DNV 2.7-1": "DNV-ST-E271", "DNV 2.7-3": "DNV-ST-E273"}
# edição antiga cujo código no inventário difere do da edição nova (trecho do caminho → motivo)
SUPERADAS_ARQ = {
    "ASME SECTION VIII DIVISION I/": "VIII-1 2001 (+A02), em partes — superada pela VIII D1 2007 do acervo",
    "ASME II PART D - 2007/ASME SECTION II PART D": "II-D 2007 — superada pela II-D 2019 (métrica) do acervo",
    "ASME B31.8 2003 - Gas Transmission and Distribution Piping Systems (2)": "cópia idêntica da B31.8 2003",
}
# cópia idêntica de arquivo já incorporado (caminho do inventário → caminho incorporado)
COPIAS_ARQ = {"ASME II PART B - 2007/SA 494-SA 494M.pdf": "ASME II PART A - 2007/SA 494-SA 494M.pdf"}
# documento sem texto incorporado pela cópia OCR com nome diferente do código (trecho do caminho → arquivo OCR)
OCR_ARQ = {"ASME Section VIII Division 2 - Appendix 4": "referencias/ocr/ASME-VIII-2-Ap4.pdf"}
# índices/resumos de mudanças/introduções dos volumes do BPVC — sem requisitos
FORA_ARQ = ("/SUMMARY", "/INTRODUCTION")


def ano(ed):
    anos = [int(a) for a in re.findall(r"(?<!\d)(19[5-9]\d|20[0-4]\d)(?!\d)", str(ed or ""))]
    return max(anos) if anos else 0


def main():
    refs = json.loads((CONT / "referencias.json").read_text(encoding="utf-8"))
    normas = json.loads((CONT / "normas.json").read_text(encoding="utf-8"))
    usados = {n["arquivo"] for n in normas}
    # cópia OCR incorporada → o original conta como incorporado (referencias/ocr/_origem.json: ocr → original)
    origem = RAIZ / "referencias" / "ocr" / "_origem.json"
    if origem.exists():
        usados |= {orig for ocr_, orig in json.loads(origem.read_text(encoding="utf-8")).items() if ocr_ in usados}
    # duplicatas/edições antigas decididas nas configurações de lote (ferramentas/docs_*.py → EXCLUIDOS)
    excluidos = {}
    import importlib.util
    for cfg in (RAIZ / "ferramentas").glob("docs_*.py"):
        spec = importlib.util.spec_from_file_location(cfg.stem, cfg)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        excluidos.update({k.replace("\\", "/"): v for k, v in getattr(mod, "EXCLUIDOS", {}).items()})
    # cópias OCR: referencias/ocr/<COD>-<ANO>.pdf → casar pelo código
    ocr_cod = {re.sub(r"\W", "", Path(n["arquivo"]).stem.rsplit("-", 1)[0]).upper()
               for n in normas if n["arquivo"].startswith("referencias/ocr/")}

    def chave(c):  # "ABNT NBR 15708-2" / "NBR-15708-2" / "DNVGL-ST-E273" → "15708-2" / "STE273"
        c = re.sub(r"^(ABNT|DNVGL|DNV|ANSI/)\s*", "", c.upper()).replace("NBR", "")
        return re.sub(r"[\s_]", "", c).replace("-", "") .lstrip("-")
    ids_normas = {chave(n["id"]) for n in normas}

    grupos = collections.defaultdict(list)
    for d in refs:
        if d["tipo"] == "norma":
            grupos[d["codigo"]].append(d)
    mais_nova = {c: max(v, key=lambda d: (ano(d["edicao"]), d.get("paginas") or 0)) for c, v in grupos.items()}

    saida = []
    for d in refs:
        assuntos = d.get("assuntos") or []
        prio = min((PRIORIDADE.get(a, 3) for a in assuntos), default=3)
        cod = d["codigo"]
        ocr = d["texto_extraivel"] is False and re.sub(r"\W", "", cod).upper().replace("ABNT", "") in {
            o.replace("ABNT", "") for o in ocr_cod}
        if d["arquivo"] in usados or ocr or any(k in d["arquivo"] and v in usados for k, v in OCR_ARQ.items()):
            sit = "incorporada"
        elif any(d["arquivo"].endswith(k) and any(u.endswith(v) for u in usados) for k, v in COPIAS_ARQ.items()):
            sit = "coberta por outra cópia"
        elif d["arquivo"] in excluidos:
            sit = "superada no acervo" if re.search(r"(?i)antig|superad|substitu|anterior|edição", excluidos[d["arquivo"]]) else "coberta por outra cópia"
        elif any(k in d["arquivo"] for k in SUPERADAS_ARQ):
            sit = "superada no acervo"
        elif any(k in d["arquivo"] for k in FORA_ARQ):
            sit = "fora de escopo"
        elif d["tipo"] == "norma" and (chave(cod) in ids_normas or cod in SUBSTITUIDAS):
            sit = "coberta por outra cópia"
        elif d["tipo"] != "norma":
            sit = "fora de escopo"
        elif mais_nova.get(cod) is not d and ano(mais_nova[cod]["edicao"]) > ano(d["edicao"]):
            sit = "superada no acervo"
        elif not d["texto_extraivel"]:
            sit = "sem texto (OCR)"
        else:
            sit = "pendente"
        saida.append({"codigo": cod, "titulo": d["titulo"], "orgao": d["orgao"], "edicao": d["edicao"],
                      "paginas": d.get("paginas"), "assuntos": assuntos, "prioridade": prio, "situacao": sit,
                      "arquivo": d["arquivo"]})
    saida.sort(key=lambda x: (x["situacao"] != "incorporada", x["prioridade"], x["orgao"], x["codigo"]))
    (CONT / "triagem_referencias.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    sit = collections.Counter(x["situacao"] for x in saida)
    print("Situação:", dict(sit))
    tab = collections.Counter((x["prioridade"], x["situacao"]) for x in saida)
    for p in (1, 2, 3):
        print(f"Prioridade {p}:", {s: n for (pp, s), n in sorted(tab.items()) if pp == p})
    print("\nPendentes prioridade 1 por assunto:")
    pa = collections.Counter(a for x in saida if x["situacao"] == "pendente" and x["prioridade"] == 1
                             for a in x["assuntos"] if PRIORIDADE.get(a) == 1)
    for a, n in pa.most_common():
        print(f"  {a}: {n}")


if __name__ == "__main__":
    main()
