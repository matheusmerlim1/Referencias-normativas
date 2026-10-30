"""Gera conteudo/referencias.json a partir de referencias/extraido/_manifesto.json.

Uso:  python -P ferramentas/inventariar_referencias.py
(rodar depois de ferramentas/extrair_referencias.py)

Para cada documento único extraído: código/título/edição (do nome do arquivo e, se
preciso, da 1ª página), nº de páginas, se tem texto extraível (PDF escaneado = false),
assuntos (palavras-chave no título + primeiras páginas) e se o mesmo documento já
existe em T:\\ENG\\Literature (por tamanho idêntico, ou código normalizado + mesma edição).
T:\\ é só leitura. Os PDFs são abertos como stream (acentos no caminho).
"""
import json
import os
import re
import unicodedata
from collections import defaultdict

import pymupdf

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTO = os.path.join(RAIZ, "referencias", "extraido", "_manifesto.json")
SAIDA = os.path.join(RAIZ, "conteudo", "referencias.json")
ACERVO_T = r"T:\ENG\Literature"

pymupdf.TOOLS.mupdf_display_errors(False)


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------- códigos
SEP = r"[\s\-_\.]*"
PADROES = [
    # (regex, formatador)
    (re.compile(r"\bNR" + SEP + r"(\d{1,2})(?!\d)", re.I), lambda m: f"NR-{int(m.group(1)):02d}"),
    (re.compile(r"\bN[\-_ ](\d{3,4})\b"), lambda m: f"N-{int(m.group(1)):04d}"),
    (re.compile(r"\bNORSOK" + SEP + r"([A-Z])" + SEP + r"(\d{3})", re.I), lambda m: f"NORSOK {m.group(1).upper()}-{m.group(2)}"),
    (re.compile(r"\bNBR" + SEP + r"(ISO|IEC)?" + SEP + r"(\d{3,5})(?:[\-\.](\d{1,2}))?(?!\d)", re.I),
     lambda m: "ABNT NBR " + (m.group(1).upper() + " " if m.group(1) else "") + m.group(2) + (f"-{m.group(3)}" if m.group(3) else "")),
    (re.compile(r"\bDNV(?:GL)?" + SEP + r"(OS|RP|ST|SE|CG)" + SEP + r"([A-Z])" + SEP + r"(\d{3})", re.I),
     lambda m: f"DNV-{m.group(1).upper()}-{m.group(2).upper()}{m.group(3)}"),
    (re.compile(r"\bDNV(?:GL)?" + r"[\s\-_]*(\d\.\d{1,2}-\d|\d-\d{1,2})(?!\d)", re.I), lambda m: f"DNV {m.group(1)}"),
    (re.compile(r"\b(?:ASME|ANSI)?[\s\-_]*\b([BY])[\s]?(\d{1,2}(?:\.\d{1,2}){1,3}M?)", re.I),
     lambda m: f"ASME {m.group(1).upper()}{m.group(2).upper()}"),
    (re.compile(r"\bASME" + SEP + r"(PCC|P)" + SEP + r"(\d+(?:\.\d+)?)", re.I), lambda m: f"ASME {m.group(1).upper()}-{m.group(2)}" if m.group(1).upper() == "PCC" else f"ASME P{m.group(2)}"),
    (re.compile(r"\bAPI" + SEP + r"(RP|SPEC|STD|TR|MPMS)?" + SEP + r"(\d{1,4}[A-Z]{0,3}(?:-\d)?)(?![\dA-Za-z])", re.I),
     lambda m: "API " + (m.group(1).upper() + " " if m.group(1) else "") + m.group(2).upper()),
    (re.compile(r"\bAWS" + SEP + r"([A-D]\d{1,2}\.\d{1,2}M?)", re.I), lambda m: f"AWS {m.group(1).upper()}"),
    (re.compile(r"\bMSS" + SEP + r"SP" + SEP + r"(\d{1,3})", re.I), lambda m: f"MSS SP-{m.group(1)}"),
    (re.compile(r"\bISA" + SEP + r"(\d{2,3}(?:\.\d{2}){1,3})", re.I), lambda m: f"ISA {m.group(1)}"),
    (re.compile(r"\bAGMA" + SEP + r"(\d{3,4}-?[A-Z]\d{2})", re.I), lambda m: f"AGMA {m.group(1).upper()}"),
    (re.compile(r"\bAISI" + SEP + r"(S\d{3})", re.I), lambda m: f"AISI {m.group(1).upper()}"),
    (re.compile(r"\bIACS" + SEP + r"(?:Rec|No)?" + SEP + r"(\d{1,3})", re.I), lambda m: f"IACS Rec {m.group(1)}"),
    (re.compile(r"\bIOGP" + SEP + r"(?:Report)?" + SEP + r"(\d{2,4})", re.I), lambda m: f"IOGP {m.group(1)}"),
    (re.compile(r"\bEEMUA" + SEP + r"(\d{3})", re.I), lambda m: f"EEMUA {m.group(1)}"),
    (re.compile(r"\bBV" + SEP + r"(NR\s?\d{3})", re.I), lambda m: f"BV {m.group(1).upper().replace(' ', '')}"),
    (re.compile(r"\bZ(359)" + SEP + r"(\d{1,2})", re.I), lambda m: f"ANSI/ASSP Z359.{m.group(2)}"),
    (re.compile(r"\b(?:EN|DIN|BS)?[\s\-_]*ISO" + SEP + r"(?:TR" + SEP + r")?(\d{1,5})(?:[\s\-_]+(\d{1,2}))?(?![\d])", re.I),
     lambda m: f"ISO {m.group(1)}" + (f"-{m.group(2)}" if m.group(2) else "")),
    (re.compile(r"\bDIN" + SEP + r"(?:EN" + SEP + r")?(\d{2,5})(?:[\s\-_]+(\d{1,2}))?(?![\d])", re.I),
     lambda m: f"DIN {m.group(1)}" + (f"-{m.group(2)}" if m.group(2) else "")),
    (re.compile(r"\bBS" + SEP + r"(?:EN" + SEP + r")?(\d{2,5})(?:[\s\-_]+(\d{1,2}))?(?![\d])", re.I),
     lambda m: f"BS {m.group(1)}" + (f"-{m.group(2)}" if m.group(2) else "")),
    (re.compile(r"\b(?:NACE\s*)?MR\s?0175", re.I), lambda m: "NACE MR0175"),
    (re.compile(r"\bASTM" + SEP + r"([A-G])\s?(\d{1,4}M?)", re.I), lambda m: f"ASTM {m.group(1).upper()}{m.group(2).upper()}"),
    (re.compile(r"(?:^|[\s/_\-])([A-G])[\s_]?(\d{2,4}M?)(?:[\s_\-]|$)"), lambda m: f"ASTM {m.group(1)}{m.group(2)}"),
]


def achar_codigo(texto, orgao=None):
    """Devolve (codigo, match) ou (None, None). ASTM 'nu' só no órgão ASTM."""
    t = sem_acento(texto)
    for rx, fmt in PADROES:
        m = rx.search(t)
        if not m:
            continue
        cod = fmt(m)
        if cod.startswith("ASTM") and "ASTM" not in t.upper() and orgao != "ASTM":
            continue
        if cod.startswith("ASME B") and orgao in ("ISO", "DIN", "BS"):
            continue
        return cod, m
    return None, None


def chave(cod):
    if not cod:
        return None
    c = cod.upper().replace("ABNT ", "").replace("ANSI/ASSP ", "ANSI ")
    c = re.sub(r"\b(RP|SPEC|STD|TR)\b", "", c) if c.startswith("API") else c
    c = re.sub(r"\bDNV(GL)?\b", "DNV", c)
    return re.sub(r"[^A-Z0-9]", "", c)


RE_ANO = re.compile(r"(?<!\d)(19[5-9]\d|20[0-2]\d)(?!\d)")
RE_ED = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th|ª)\b|\bED\.?\s?(\d{1,2})", re.I)


def achar_edicao(texto, m=None):
    t = texto if m is None else texto[:m.start()] + " " + texto[m.end():]
    anos = RE_ANO.findall(t)
    e = RE_ED.search(t)
    partes = []
    if anos:
        partes.append(anos[0])
    if e:
        partes.append(f"{e.group(1) or e.group(2)}ª ed.")
    return " / ".join(partes) or None


# ---------------------------------------------------------------- assuntos
ASSUNTOS = {
    "escada": r"\bescadas?\b|\bstairs?\b|stairway|step ?ladder|\bdegraus?\b",
    "escada marinheiro": r"marinheiro|fixed ladder|vertical ladder|\bladder|escada vertical|safety cage|gaiola",
    "guarda-corpo": r"guarda[- ]?corpo|guard[- ]?rail|handrail|corrim[aã]o|toe ?board|parapeito|rodap[eé] de prote",
    "passarela/plataforma": r"passarela|walkway|working platform|plataforma de trabalho|means of access|meios de acesso|acesso permanente|gangway|catwalk",
    "rampa": r"\brampa|\bramp\b",
    "grating": r"grating|grade de piso|gradil|piso gradeado",
    "flange": r"flange",
    "junta/gaxeta": r"gasket|junta de veda",
    "parafuso/porca/arruela": r"\bbolts?\b|\bscrews?\b|\bnuts?\b|washers?|parafuso|\bporcas?\b|arruela|fasteners?|\brivets?\b|rebite|\bstuds?\b|locknut",
    "rosca": r"thread|rosca",
    "solda": r"weld|solda|brazing",
    "tubulação": r"piping|\bpipes?\b|tubula|\btubos?\b|line pipe|pipeline|\bdutos?\b",
    "válvula": r"valve|v[aá]lvula",
    "vaso de pressão/caldeira": r"pressure vessel|vaso de press|boiler|caldeira",
    "içamento/movimentação de carga": r"lifting|hoist|sling|linga|cinta|rigging|hook|gancho|crane|guindaste|levantamento|eleva[çc][aã]o de carga|shackle|manilha|offshore container|portable offshore unit|winch|olhal|eyebolt|cabo de a[çc]o|wire rope",
    "estrutura metálica": r"structural steel|estrutura(s)? de a[çc]o|estruturas met|steel structure|cold-formed|perfis|perfil|offshore steel structure|fixed offshore platform|steel buildings|structural design|structural safety",
    "pintura/revestimento": r"paint|pintura|coating|revestimento|galvaniz|corros",
    "materiais/ensaios": r"tension test|tensile|ensaio|test method|mechanical properties|propriedades mec|H2S|sour service|materials? (for|and)|\bmateriais\b",
    "tolerâncias/desenho técnico": r"toler|desenho t[eé]cnico|dimensioning|drawing|cotagem|escala|rugosidade|surface texture|hachura|linhas|folha de desenho",
    "elétrica": r"el[eé]tric|electric|aterramento|explosiv|atmosfera|60079|baixa tens|m[eé]dia tens|ilumina|lighting|lumin",
    "trabalho em altura/queda": r"trabalho em altura|queda|fall protection|trava-?quedas|fall arrest|anchorage|ancoragem",
    "ergonomia/fatores humanos": r"ergonom|human factor|fatores humanos",
    "segurança de máquinas": r"safety of machinery|seguran[çc]a (no trabalho )?(em|de) m[aá]quinas|risk assessment|aprecia[çc][aã]o",
    "offshore/naval": r"offshore|marine|naval|vessel|ship|subsea|mooring|amarra|plataforma de petr",
    "engrenagens/transmissão": r"gear|engrenag|spline|pulley|chain|keyway|circlip",
    "hidráulica": r"hydraulic|hidr[aá]ulic|fluid power|tube connection|tube fitting",
    "medição de vazão": r"orifice|5167|venturi|vaz[aã]o",
    "perfuração/poço": r"drill|wellhead|christmas tree|casing|tubing|blowout|BOP|choke|well control|riser",
    "segurança do trabalho (NR)": r"\bNR-\d|insalubr|inflam|espa[çc]o confinado|confined space|ru[ií]do|inc[eê]ndio",
}
ASSUNTOS_RX = {k: re.compile(v, re.I) for k, v in ASSUNTOS.items()}

TIPO_OUTRO = re.compile(r"manual|cartilha|perguntas|respostas|guia t[eé]cnico|\(apresenta|meeting notes|explaining|"
                        r"contents only|an[aá]lise c[oó]digo|folheto|proct|entradas_coletivas|validad|it-dde|interpretations|interpretation|"
                        r"\bINTER\b|ballot", re.I)


def tipo_doc(nome, orgao):
    if orgao == "LIGHT":
        return "catalogo" if re.search(r"fabricantes|recon", nome, re.I) else "outro"
    if re.search(r"fabricantes|cat[aá]logo|catalog", nome, re.I):
        return "catalogo"
    if re.search(r"an[aá]lise c[oó]digo|handbook", nome, re.I):
        return "livro"
    if TIPO_OUTRO.search(nome):
        return "outro"
    return "norma"


LIXO = re.compile(r"copyright|licen[sç]|not for resale|provided by|\bihs\b|reproduction|document provided|downloaded|"
                  r"order number|single user|no reproduction|www\.|http|^\s*page|^\W*$|^\d+$|this is a preview|"
                  r"v[aá]lida a partir|n[uú]mero de refer|reference number|todos os direitos|edi[çc][aã]o|edition|"
                  r"este texto n[aã]o substitui|entra em vigor|revisado em|minist[eé]rio|portaria|treze de maio|"
                  r"^(british standard|deutsche norm|international( standard)?|norma internacional|recommended practice|"
                  r"offshore standards?|det norske veritas( as)?|incorporating|by authority of|an american national standard|"
                  r"a n a m e r i c a n.*|designation:.*|draft.*|price group.*|translation by.*|adoption notice.*|"
                  r"(recommended practice|offshore standard) det norske veritas( as)?|british standard .{0,30})\s*$", re.I)


def titulo_da_pagina(txt):
    linhas = [l.strip() for l in txt.splitlines()]
    boas = [l for l in linhas if len(re.findall(r"[A-Za-zÀ-ÿ]", l)) >= 12 and not LIXO.search(l)]
    return " ".join(boas[:2])[:200] if boas else None


def abrir(p):
    with open(p, "rb") as f:
        return pymupdf.open(stream=f.read(), filetype="pdf")


def info_pdf(p):
    try:
        doc = abrir(p)
    except Exception as e:  # noqa: BLE001
        return {"erro": repr(e)}
    n = len(doc)
    # amostra: 3 primeiras + até 15 páginas espaçadas pelo miolo. Uma página "tem texto" com >= 150 letras
    # (cabeçalho/rodapé de PDF escaneado não passa disso). texto_extraivel = >= 50% das páginas da amostra.
    amostra = sorted(set(list(range(min(n, 3))) + [int(k * (n - 1) / 14) for k in range(15)])) if n else []
    com_texto = vazias = 0
    textos = {}
    for i in amostra:
        try:
            t = doc[i].get_text()
        except Exception:  # noqa: BLE001
            t = ""
        textos[i] = t
        com_texto += len(re.findall(r"[A-Za-z]", t)) >= 150
        try:
            if not t.strip() and not doc[i].get_images() and not doc[i].get_drawings():
                vazias += 1
        except Exception:  # noqa: BLE001
            pass
    pct = round(100 * com_texto / len(amostra)) if amostra else 0
    inicio = "\n".join(textos.get(i, "") for i in range(min(n, 3)))
    return {"paginas": n, "texto_extraivel": pct >= 50, "texto_pct": pct, "p1": textos.get(0, ""), "inicio": inicio,
            "vazio": bool(amostra) and vazias / len(amostra) >= 0.5}


def mesmo_conteudo(a, b, n=1 << 20):
    """Mesmo tamanho já conferido; confirma pelo 1º MB e pelo último MB (evita colisão de tamanho)."""
    try:
        with open(a, "rb") as fa, open(b, "rb") as fb:
            if fa.read(n) != fb.read(n):
                return False
            fa.seek(-min(n, os.path.getsize(a)), 2)
            fb.seek(-min(n, os.path.getsize(b)), 2)
            return fa.read(n) == fb.read(n)
    except OSError:
        return False


def indexar_T():
    por_tam, por_chave = defaultdict(list), defaultdict(list)
    if not os.path.isdir(ACERVO_T):
        print("AVISO: T:\\ENG\\Literature inacessível — no_acervo_T fica null")
        return por_tam, por_chave
    for r, _, fs in os.walk(ACERVO_T):
        for f in fs:
            if not f.lower().endswith(".pdf"):
                continue
            p = os.path.join(r, f)
            try:
                por_tam[os.path.getsize(p)].append(p)
            except OSError:
                pass
            cod, m = achar_codigo(f)
            if cod:
                por_chave[chave(cod)].append((p, achar_edicao(f, m)))
    return por_tam, por_chave


def main():
    manifesto = json.load(open(MANIFESTO, encoding="utf-8"))
    copias = defaultdict(list)
    for r in manifesto:
        if r.get("status") == "duplicata_de":
            copias[r["arquivo"]].append(f'{r["zip"]}:{r["entrada"]}')
    por_tam, por_chave = indexar_T()
    saida = []
    for r in manifesto:
        if r.get("status") not in ("extraido", "ja_existia"):
            continue
        rel, orgao, zipn = r["arquivo"], r["orgao"], r["zip"]
        caminho = os.path.join(RAIZ, rel)
        nome = os.path.splitext(os.path.basename(r["entrada"]))[0]
        pasta = "/".join(r["entrada"].split("/")[:-1])
        ext = os.path.splitext(rel)[1].lower()
        reg = {"codigo": None, "titulo": None, "orgao": orgao, "edicao": None, "tipo": tipo_doc(r["entrada"], orgao),
               "arquivo": rel, "zip": zipn, "paginas": None, "texto_extraivel": None, "no_acervo_T": None, "assuntos": []}
        info = info_pdf(caminho) if ext == ".pdf" else {}
        if "erro" in info:
            reg["erro"] = info["erro"]
        reg["paginas"] = info.get("paginas")
        reg["texto_extraivel"] = info.get("texto_extraivel") if ext == ".pdf" else True
        if 0 < info.get("texto_pct", 100) < 80:
            reg["texto_pct_paginas"] = info["texto_pct"]  # % da amostra com texto (parcialmente escaneado?)
        if info.get("vazio"):
            reg["problema"] = "maioria das páginas em branco (sem texto, imagem ou desenho) — arquivo inutilizável"
        if "erro" in info:
            reg["problema"] = "PDF não abre no pymupdf: " + info["erro"]

        # código: nome do arquivo; BPVC usa a pasta; senão 1ª página
        cod, m = achar_codigo(nome, orgao)
        if "BPVC" in pasta or "Boiler" in pasta or "SECTION VIII DIVISION I" in pasta:
            sec = re.search(r"ASME ([IVX]+)(?: PART ([A-D]))?(?:\s*D(\d))?", pasta.split("/")[-1])
            secao = (sec.group(1) + (f"-{sec.group(2)}" if sec.group(2) else "") + (f" Div.{sec.group(3)}" if sec.group(3) else "")) if sec else "VIII Div.1"
            mm = re.match(r"(S[A-F])\s?-?(\d+)", nome)
            if mm:
                cod = f"ASME BPVC {secao} {mm.group(1)}-{mm.group(2)}"
            elif "VOL" in nome.upper():
                cod = f"ASME BPVC {secao} Interpretations {nome.title()}"
            else:
                cod = f"ASME BPVC {secao} {re.sub(r'^ASME (SEC VIII D1 )?', '', nome)}"
            reg["edicao"] = "2007" if "2007" in pasta else None
            reg["tipo"] = "outro" if "INTER" in pasta.upper() or "VOL" in nome.upper() else "norma"
        if not cod and info.get("p1"):
            cod, _ = achar_codigo(info["p1"][:600], orgao)
        reg["codigo"] = cod or nome

        # título
        # título = nome do arquivo sem código/ano/edição; se sobrar pouco, 1ª página
        resto = nome[:m.start()] + " " + nome[m.end():] if m is not None else nome
        resto = re.sub(r"\b(ABNT|NBR|ASME|ANSI|API|ISO|DIN|BS|EN|DNV(GL)?|AWS|NR|MSS|ISA|IACS|AGMA|AISI|AISC|ABS|BV)\b",
                       " ", resto)
        resto = re.sub(r"(?<!\d)(19|20)\d\d(?!\d)|\b\d{1,2}(st|nd|rd|th|ª)\b|\bED\s?\d+(st|nd|rd|th)?\b|\(\d\)|\d{6,}",
                       " ", resto, flags=re.I)
        resto = re.sub(r"^[\s\-–_.,]+|[\s\-–_.,]+$", "", re.sub(r"\s+", " ", resto))
        if len(re.findall(r"[A-Za-zÀ-ÿ]", resto)) >= 10 and " " in resto:
            tit = resto
        else:
            tit = titulo_da_pagina(info.get("p1", "")) or (resto if len(re.findall(r"[A-Za-z]", resto)) >= 5 else nome)
        reg["titulo"] = re.sub(r"\s+", " ", tit).strip(" -_")

        if not reg["edicao"]:
            reg["edicao"] = achar_edicao(nome, m)
            if not reg["edicao"] and info.get("p1"):
                anos = RE_ANO.findall(info["p1"][:1500])
                reg["edicao"] = max(anos) if anos else None

        # assuntos
        base = f'{nome} {reg["titulo"]} {pasta}'
        texto = base + " " + info.get("inicio", "")[:6000]
        reg["assuntos"] = [k for k, rx in ASSUNTOS_RX.items() if rx.search(base)] or \
                          [k for k, rx in ASSUNTOS_RX.items() if len(rx.findall(texto)) >= 3][:4]

        # acervo T
        tam = r["tamanho"]
        igual = next((p for p in por_tam.get(tam, []) if mesmo_conteudo(p, caminho)), None)
        if igual:
            reg["no_acervo_T"] = igual
        else:
            k = chave(reg["codigo"])
            cands = por_chave.get(k, []) if k and not reg["codigo"].startswith("ASME BPVC") else []
            ano = (reg["edicao"] or "")[:4]
            mesmo = [p for p, ed in cands if ano and ed and ed[:4] == ano]
            if mesmo:
                reg["no_acervo_T"] = mesmo[0]
            elif cands:
                reg["acervo_T_outras_edicoes"] = sorted({p for p, _ in cands})[:3]
        if copias.get(rel):
            reg["copias_identicas"] = copias[rel]
        saida.append(reg)

    saida.sort(key=lambda d: (d["orgao"].upper(), str(d["codigo"]).upper(), d["arquivo"]))
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    n = len(saida)
    print(f"{n} documentos -> {SAIDA}")
    print("sem texto (escaneados):", sum(1 for d in saida if d["texto_extraivel"] is False))
    print("no acervo T:", sum(1 for d in saida if d["no_acervo_T"]))
    print("erros:", [d["arquivo"] for d in saida if d.get("erro")])


if __name__ == "__main__":
    main()
