"""OCR em lote dos documentos "sem texto (OCR)" de um órgão (lidos da triagem), dividido entre N processos.

uso: python -P ferramentas/ocr_lote.py <ORGAO|TODOS> <n_partes> <parte> [idioma|-] [--mapa]   (--mapa: só lista ocr <= original)    ex.: ABNT 3 0   (rodar as 3 partes em paralelo)
Saída: referencias/ocr/<CODIGO>-<ANO>.pdf (mesmas páginas). Pula o que já existe. Caminhos com acento são lidos daqui
(não pelo argumento do bash). Usa ferramentas/ocr.py (cinza; OCR em RGB).
"""
import json
import os
import re
import subprocess
import sys

orgao, n, k = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
idioma_fixo = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None  # "-" = automático por órgão


def idioma(x):
    return idioma_fixo or ("por" if x["orgao"] in ("ABNT", "NR", "AMPLA", "DNIT") else "eng")
t = json.load(open("conteudo/triagem_referencias.json", encoding="utf-8"))
alvo = sorted([x for x in t if (orgao == "TODOS" or x["orgao"] == orgao) and x["situacao"] == "sem texto (OCR)"], key=lambda x: x["arquivo"])
nomes, vistos = [], {}
for x in alvo:  # nome da cópia OCR; 2º arquivo com o mesmo código/ano ganha "-2" (ex. duas DIN 6885 1968)
    ano = re.findall(r"(19[5-9]\d|20[0-4]\d)", str(x.get("edicao") or "") + " " + os.path.basename(x["arquivo"]))
    nome = re.sub(r"[^A-Za-z0-9.]+", "-", x["codigo"].replace("ABNT ", "")).strip("-") + (f"-{ano[0]}" if ano else "")
    vistos[nome] = vistos.get(nome, 0) + 1
    nomes.append(nome + (f"-{vistos[nome]}" if vistos[nome] > 1 else ""))
if len(sys.argv) > 5 and sys.argv[5] == "--mapa":
    for x, nome in zip(alvo, nomes):
        print(f"referencias/ocr/{nome}.pdf  <=  {x['arquivo']}")
    sys.exit()
pular = [p for p in os.environ.get("OCR_PULAR", "").split(";") if p]  # trechos de caminho a NÃO processar (cópias)
for i, x in enumerate(alvo):
    if i % n != k or any(p in x["arquivo"] for p in pular):
        continue
    saida = f"referencias/ocr/{nomes[i]}.pdf"
    if os.path.exists(saida):
        print("já existe", saida, flush=True)
        continue
    glob_seguro = re.sub(r"[^\x00-\x7f\[\]]", "*", x["arquivo"])  # acentos → '*' (glob)
    r = subprocess.run([sys.executable, "-P", "ferramentas/ocr.py", glob_seguro, saida, idioma(x)], capture_output=True, text=True)
    if r.returncode == 0:  # mapa ocr → original (a triagem usa para marcar o original como incorporado)
        mp = "referencias/ocr/_origem.json"
        om = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
        om[saida] = x["arquivo"]
        json.dump(om, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(("OK " if r.returncode == 0 else "FALHOU ") + saida + ("" if r.returncode == 0 else " | " + r.stdout[-200:] + r.stderr[-300:]), flush=True)
