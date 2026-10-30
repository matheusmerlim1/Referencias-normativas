"""Inventário deduplicado do acervo T:\\ENG\\Literature -> conteudo/catalogo.json

Uso (da pasta do projeto, com PYTHONIOENCODING=utf-8):
    python -P ferramentas/catalogar.py extrair   # 1) texto das 2 primeiras págs (cache) + OCR das digitalizadas
    python -P ferramentas/catalogar.py           # 2) gera conteudo/catalogo.json a partir do cache

O acervo é SOMENTE LEITURA: o script só lê T:\\ENG\\Literature e grava
conteudo/catalogo.json. O cache de texto fica em %TEMP%\\uva_cat (caminho curto,
limite de 260 caracteres do Windows). O OCR usa o motor nativo do Windows
(ferramentas/ocr_windows.ps1) — só para PDFs digitalizados sem camada de texto.

Regras
- Ignora Thumbs.db, desktop.ini, *.crdownload e as pastas de miniaturas ".ts".
- Deduplica por (nome do arquivo, tamanho) e, entre nomes diferentes, por tamanho + MD5; arquivos Office (.doc/.xls...) com o
  mesmo nome e diferença <= 1 KB também são cópias (só muda o cabeçalho).
  "arquivo" = caminho mais curto cujo conteúdo NÃO está zerado (há cópias
  corrompidas, cheias de bytes 0, em 00 - Miscellaneous/1 - NORMAS/ASME);
  os demais caminhos vão para "copias".
- Sequências de páginas TIF (ex. "API STD 610_001.tif" ... "_056.tif") viram UMA
  entrada (arquivo = 1ª página).
- Caminho (ou cópia) com SUPERADO/SUPERADA/Cancelada -> situacao "superada".
  Petrobras das pastas Normas_PORT_*_2025 e NRs de "03 - Standards" -> "vigente".
- "paginas": do cache de texto ou abrindo só o xref (nome curto 8.3); "em_referencias": true quando
  código+ano existe em conteudo/referencias.json ou o caminho está no "no_acervo_T" de lá.
- Títulos: do nome do arquivo; se o nome for só código, da 1ª página (texto ou
  OCR); Petrobras pelo "0 - CATALOGO DE NORMAS PETROBRAS" + capa de cada N.
"""
import collections
import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

RAIZ = r"T:\ENG\Literature"
BS = chr(92)
LONG = BS + BS + "?" + BS          # prefixo de caminho longo do Windows
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(PROJ, "conteudo", "catalogo.json")
TMP = os.path.join(tempfile.gettempdir(), "uva_cat")
CACHE = os.path.join(TMP, "pag1.json")
OCR = os.path.join(TMP, "ocr.json")
NPAG = os.path.join(TMP, "npag.json")      # nº de páginas dos PDFs fora do cache de texto (livros/catálogos)
REFS = os.path.join(PROJ, "conteudo", "referencias.json")
OFFICE = (".doc", ".docx", ".xls", ".xlsx", ".xlsm")


# ----------------------------------------------------------------- varredura
def ignorar(p):
    n = os.path.basename(p).lower()
    return n in ("thumbs.db", "desktop.ini") or n.endswith(".crdownload") or (BS + ".ts" + BS) in p


def varrer():
    out = []
    for dp, dn, fn in os.walk(LONG + RAIZ):
        for f in fn:
            p = os.path.join(dp, f)
            q = p[len(LONG):]
            if ignorar(q):
                continue
            s = -1
            for _ in range(3):          # rede (T:) às vezes falha: tenta de novo
                try:
                    s = os.path.getsize(p)
                    break
                except OSError:
                    pass
            out.append((q, s))
    return out


def zerado(p):
    try:
        b = open(LONG + p, "rb").read(4096)
    except OSError:
        return True
    return b.count(0) == len(b)


def agrupar(arquivos):
    """Lista de unidades: {"paths": [canônico, cópias...], "seq": nº de páginas TIF (0 se não for sequência)}."""
    seq = collections.defaultdict(list)
    for p, s in arquivos:
        m = re.match(r"^(.*)_(\d{3})\.tif$", os.path.basename(p), re.I)
        if m:
            seq[(os.path.dirname(p), m.group(1).lower())].append((p, s))
    em_seq = set()
    seq_units = {}
    for (d, pref), L in seq.items():
        if len(L) < 5:
            continue
        L.sort()
        chave = ("seq:" + pref, len(L), sum(s for _, s in L))
        seq_units.setdefault(chave, []).append(L[0][0])
        em_seq.update(p for p, _ in L)
    g = collections.defaultdict(list)
    for p, s in arquivos:
        if p not in em_seq:   # tamanho desconhecido (-1) nunca junta com outro arquivo
            g[(os.path.basename(p).lower(), s if s >= 0 else p)].append(p)
    por_nome = collections.defaultdict(list)
    for (n, s) in list(g):
        if n.endswith(OFFICE) and isinstance(s, int):
            por_nome[n].append(s)
    for n, tams in por_nome.items():
        tams.sort()
        for a, b in zip(tams, tams[1:]):
            if (n, a) in g and abs(b - a) <= 1024:
                g[(n, b)].extend(g.pop((n, a)))
    unidades = []
    for v in list(g.values()) + list(seq_units.values()):
        v = sorted(v, key=lambda x: (len(x), x))
        if len(v) > 1 and zerado(v[0]):
            boas = [x for x in v if not zerado(x)]
            if boas:
                v.remove(boas[0])
                v.insert(0, boas[0])
        unidades.append({"paths": v, "seq": 0})
    for (k, n, _), v in seq_units.items():
        for u in unidades:
            if u["paths"][0] in v:
                u["seq"] = n
    return juntar_identicos(unidades)


def resumo_hash(p, completo=False):
    h = hashlib.md5()
    with open(LONG + p, "rb") as f:
        if completo:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        else:
            h.update(f.read(65536))
            try:
                f.seek(-65536, 2)
            except OSError:
                f.seek(0)
            h.update(f.read())
    return h.hexdigest()


def juntar_identicos(unidades):
    """Arquivos de NOMES diferentes com o mesmo conteúdo (tamanho + MD5) viram uma unidade.
    Arquivos zerados (corrompidos) e planilhas/docs Office não entram (o tamanho igual é coincidência)."""
    por_tam = collections.defaultdict(list)
    for u in unidades:
        p = u["paths"][0]
        if u["seq"] or p.lower().endswith(OFFICE):
            continue
        try:
            t = os.path.getsize(LONG + p)
        except OSError:
            continue
        if t > 0:
            por_tam[t].append(u)
    remover = set()
    for t, us in por_tam.items():
        if len(us) < 2:
            continue
        grupos = collections.defaultdict(list)
        for u in us:
            if zerado(u["paths"][0]):
                continue
            try:
                grupos[resumo_hash(u["paths"][0])].append(u)
            except OSError:
                pass
        for g in grupos.values():
            if len(g) < 2:
                continue
            full = collections.defaultdict(list)
            for u in g:
                full[resumo_hash(u["paths"][0], True)].append(u)
            for g2 in full.values():
                if len(g2) < 2:
                    continue
                todos = sorted({x for u in g2 for x in u["paths"]}, key=lambda x: (len(x), x))
                g2[0]["paths"] = todos
                g2[0]["hash"] = True
                remover.update(id(u) for u in g2[1:])
    return [u for u in unidades if id(u) not in remover]


def curto(p):
    """Nome curto 8.3 (sem acentos) — pymupdf.open(caminho) falha com acento; assim não precisa ler o arquivo todo."""
    buf = ctypes.create_unicode_buffer(1024)
    n = ctypes.windll.kernel32.GetShortPathNameW(LONG + p, buf, 1024)
    return buf.value if n else LONG + p


def contar_paginas(unidades, cache):
    """Nº de páginas dos PDFs que não estão no cache de texto (só abre o xref, barato). Cache em NPAG."""
    import pymupdf
    npag = json.load(open(NPAG, encoding="utf-8")) if os.path.exists(NPAG) else {}
    novos = 0
    for u in unidades:
        p = u["paths"][0]
        if not p.lower().endswith(".pdf") or cache.get(p, {}).get("np") or p in npag:
            continue
        try:
            with pymupdf.open(curto(p)) as d:
                npag[p] = len(d)
        except Exception:  # noqa: BLE001
            npag[p] = 0
        novos += 1
    if novos:
        json.dump(npag, open(NPAG, "w", encoding="utf-8"), ensure_ascii=False)
    return npag


# ---------------------------------------------------------- referencias/
def chave_ref(codigo):
    """Código normalizado para comparar acervo T: × referencias/ ('ASME BPVC II-A SA-106' ≡ 'ASME SA-106')."""
    c = sem_acento(codigo or "").upper()
    c = re.sub(r"^ASME BPVC II-[ABCD] ", "ASME ", c)
    c = re.sub(r"\b(ABNT|STD|RP|SPEC|STANDARD)\b", " ", c)
    c = re.sub(r"\bPART\b", "", c)
    return re.sub(r"[^A-Z0-9]", "", c)


def referencias():
    """(conjunto de (código, ano), conjunto de caminhos T: citados em 'no_acervo_T')."""
    if not os.path.exists(REFS):
        return set(), set()
    pares, caminhos = set(), set()
    for r in json.load(open(REFS, encoding="utf-8")):
        a = ano_de(str(r.get("edicao") or ""))
        if a:
            pares.add((chave_ref(r.get("codigo")), a))
        if r.get("no_acervo_T"):
            caminhos.add(r["no_acervo_T"].replace(BS, "/").lower())
    return pares, caminhos


# ------------------------------------------------------------ extração texto
def extrair(unidades):
    import pymupdf
    os.makedirs(os.path.join(TMP, "png"), exist_ok=True)
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    for u in unidades:
        p = u["paths"][0]
        ext = os.path.splitext(p)[1].lower()
        rel = p[len(RAIZ) + 1:]
        if ext not in (".pdf", ".tif") or p in cache or rel.startswith(("01 - Books", "02 - Brochures")):
            continue
        rec = {"txt": "", "np": 0, "png": ""}
        try:
            doc = pymupdf.open(stream=open(LONG + p, "rb").read(), filetype="pdf" if ext == ".pdf" else "tif")
            rec["np"] = len(doc)
            txt = "".join(doc[i].get_text() + "\n=====\n" for i in range(min(2, len(doc))))
            rec["txt"] = txt[:3000]
            corpo = txt.replace("Copyright by the SSPC:&The Society for Protective Coatings", "")
            if len("".join(corpo.split())) < 60 and len(doc):
                png = os.path.join(TMP, "png", "%05d.png" % len(cache))
                doc[0].get_pixmap(dpi=150).save(png)
                rec["png"] = png
        except Exception as e:  # noqa: BLE001
            rec["err"] = str(e)[:200]
            rec["zerado"] = zerado(p)
        cache[p] = rec
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    pngs = [r["png"] for r in cache.values() if r.get("png")]
    feitos = json.load(open(OCR, encoding="utf-8-sig")) if os.path.exists(OCR) else {}
    falta = [x for x in pngs if x not in feitos]
    if falta:
        lista = os.path.join(TMP, "ocr_lista.txt")
        open(lista, "w", encoding="utf-8").write("\n".join(falta))
        ps1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_windows.ps1")
        novo = os.path.join(TMP, "ocr_novo.json")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, lista, novo], check=True)
        feitos.update(json.load(open(novo, encoding="utf-8-sig")))
        json.dump(feitos, open(OCR, "w", encoding="utf-8"), ensure_ascii=False)
    print("cache:", len(cache), "OCR:", len(feitos))


def texto_pag1(p, cache, ocr):
    r = cache.get(p)
    if not r:
        return ""
    t = r.get("txt", "")
    if r.get("png"):
        t = ocr.get(r["png"], "") + "\n=====\n" + t
    return t


# ---------------------------------------------------------------- utilidades
def limpa(s):
    return re.sub(r"\s+", " ", s or "").strip(" -_.,;:")


def titulo_caixa(s):
    """'TÍTULO EM CAIXA ALTA' -> 'Título em caixa alta'."""
    if not s or s.upper() != s or len(re.sub(r"[^A-Za-zÀ-ú]", "", s)) < 10:
        return s
    w = s.lower()
    return w[:1].upper() + w[1:]


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


ANO = r"(?:19[5-9]\d|20[0-3]\d)"


def ano_de(s):
    m = re.findall(r"(?<!\d)(" + ANO + r")(?!\d)", s or "")
    return m[-1] if m else ""


def revisao(s):
    m = re.search(r"(?:Rev\.?\s*|REV[._ ]|_)([A-Z0-9]{1,2})(?:\b|_)", s)
    if m:
        return "Rev. " + m.group(1)
    m = re.search(r"\br(\d{2})\b", s)
    return ("Rev. " + m.group(1)) if m else ""


# ---------------------------------------------------------- Petrobras
def catalogo_petrobras():
    import pymupdf
    p = os.path.join(RAIZ, "00 - Miscellaneous", "PETROBRAS", "NORMAS", "0 - CATALOGO DE NORMAS PETROBRAS.pdf")
    try:
        doc = pymupdf.open(stream=open(LONG + p, "rb").read(), filetype="pdf")
    except OSError:
        return {}
    linhas = [l.strip() for pg in doc for l in pg.get_text().splitlines()]
    out = {}
    i = 0
    while i < len(linhas):
        m = re.match(r"^N-(\d{4})(?: ([A-Z]))?$", linhas[i])
        if not m:
            i += 1
            continue
        j = i + 1
        tit = []
        while j < len(linhas) and not re.match(r"^(PR|E|M|PD|T|S|C)$", linhas[j]) and not re.match(r"^N-\d{4}", linhas[j]):
            tit.append(linhas[j])
            j += 1
        data = linhas[j + 2] if j + 2 < len(linhas) and re.match(r"^[a-z]{3}/\d{4}$", linhas[j + 2]) else ""
        t = " ".join(tit)
        t = re.sub(r"\(Classifica[çc][ãa]o:.*", "", t)
        t = re.sub(r"^\d+ª (Emenda|Errata) - ", "", t)
        t = re.sub(r" - REVALIDADA EM \S+", "", t)
        t = limpa(t)
        num = "N-" + m.group(1)
        if t and not t.startswith(("ENGLISH", "ESPAÑOL")) and num not in out:
            out[num] = {"titulo": titulo_caixa(t), "rev": m.group(2) or "", "data": data}
        i = j
    return out


def petrobras_capa(txt):
    """(título, revisão, data) a partir da capa de uma N-xxxx."""
    capa = txt.split("=====")[0]
    m = re.search(r"REV\.\s*([A-Z])\b", capa)
    rev = m.group(1) if m else ""
    m = re.search(r"\b(\d{2}) ?/ ?(\d{4})\b", capa)
    data = (m.group(1) + "/" + m.group(2)) if m else ""
    tipos = ("Especificação", "Procedimento", "Padronização", "Método", "Terminologia", "Simbologia",
             "Classificação", "Revalidação", "Emenda", "Errata", "Confirmação", "Cancelamento", "Cabe à")
    lixo = re.compile(r"^(-P[ÚU]BLICO-|-INTERNO-|-RESERVADO-|N-\s?\d+|REV\.|\d+ ?/ ?\d{4}|PROPRIEDADE|CONTEC|Comissão|Técnica|SC ?- ?\d+|\d+ páginas)")
    tit = []
    for l in (x.strip() for x in capa.splitlines()):
        if not l:
            continue
        if l.startswith(tipos):
            break
        if lixo.match(l):
            tit = []
            continue
        tit.append(l)
    return limpa(" ".join(tit)), rev, data


# ---------------------------------------------------------- títulos de referência
# Usados só quando o nome do arquivo é apenas o código e a 1ª página não tem texto
# extraível (designações públicas e estáveis dessas normas).
NR_TITULOS = {
    "01": "Disposições gerais e gerenciamento de riscos ocupacionais", "03": "Embargo e interdição",
    "04": "Serviços especializados em segurança e medicina do trabalho (SESMT)",
    "05": "Comissão interna de prevenção de acidentes (CIPA)", "06": "Equipamentos de proteção individual (EPI)",
    "07": "Programa de controle médico de saúde ocupacional (PCMSO)", "08": "Edificações",
    "09": "Programa de prevenção de riscos ambientais / agentes físicos, químicos e biológicos",
    "10": "Segurança em instalações e serviços em eletricidade", "12": "Segurança no trabalho em máquinas e equipamentos",
    "13": "Caldeiras, vasos de pressão, tubulações e tanques metálicos de armazenamento",
    "15": "Atividades e operações insalubres", "17": "Ergonomia",
    "18": "Segurança e saúde no trabalho na indústria da construção", "19": "Explosivos",
    "20": "Segurança e saúde no trabalho com inflamáveis e combustíveis", "22": "Segurança e saúde ocupacional na mineração",
    "23": "Proteção contra incêndios", "26": "Sinalização de segurança", "30": "Segurança e saúde no trabalho aquaviário",
    "32": "Segurança e saúde no trabalho em serviços de saúde", "33": "Segurança e saúde nos trabalhos em espaços confinados",
    "34": "Condições e meio ambiente de trabalho na indústria da construção, reparação e desmonte naval",
    "35": "Trabalho em altura", "37": "Segurança e saúde em plataformas de petróleo",
}

SSPC_TITULOS = {
    "SP 1": "Solvent Cleaning", "SP 2": "Hand Tool Cleaning", "SP 3": "Power Tool Cleaning",
    "SP 5": "White Metal Blast Cleaning", "SP 6": "Commercial Blast Cleaning", "SP 7": "Brush-Off Blast Cleaning",
    "SP 8": "Pickling", "SP 10": "Near-White Blast Cleaning", "SP 11": "Power Tool Cleaning to Bare Metal",
    "SP 13": "Surface Preparation of Concrete", "SP 14": "Industrial Blast Cleaning",
    "VIS 1": "Visual Standard for Abrasive Blast Cleaned Steel",
    "VIS 2": "Standard Method of Evaluating Degree of Rusting on Painted Steel Surfaces",
    "VIS 3": "Visual Standard for Power- and Hand-Tool Cleaned Steel",
}

ASME_TITULOS = {
    "B1.20.1": "Pipe Threads, General Purpose (Inch)", "B16.1": "Cast Iron Pipe Flanges and Flanged Fittings",
    "B16.3": "Malleable Iron Threaded Fittings", "B16.5": "Pipe Flanges and Flanged Fittings",
    "B16.5a": "Pipe Flanges and Flanged Fittings (Addenda)", "B16.9": "Factory-Made Wrought Buttwelding Fittings",
    "B16.10": "Face-to-Face and End-to-End Dimensions of Valves",
    "B16.11": "Forged Fittings, Socket-Welding and Threaded",
    "B16.20": "Metallic Gaskets for Pipe Flanges - Ring-Joint, Spiral-Wound, and Jacketed",
    "B16.21": "Nonmetallic Flat Gaskets for Pipe Flanges", "B16.25": "Buttwelding Ends",
    "B16.34": "Valves - Flanged, Threaded, and Welding End", "B16.36": "Orifice Flanges",
    "B16.39": "Malleable Iron Threaded Pipe Unions", "B18.2.1": "Square and Hex Bolts and Screws (Inch Series)",
    "B18.2.2": "Square and Hex Nuts (Inch Series)", "B31.1": "Power Piping", "B31.3": "Process Piping",
    "B31.4": "Pipeline Transportation Systems for Liquid Hydrocarbons and Other Liquids",
    "B31.8": "Gas Transmission and Distribution Piping Systems", "B36.10": "Welded and Seamless Wrought Steel Pipe",
    "B36.10M": "Welded and Seamless Wrought Steel Pipe", "B36.19M": "Stainless Steel Pipe",
    "PCC-2": "Repair of Pressure Equipment and Piping", "PTC 22": "Performance Test Code on Gas Turbines",
    "PTC 46": "Performance Test Code on Overall Plant Performance",
}

API_TITULOS = {
    "5L": "Specification for Line Pipe", "6A": "Specification for Wellhead and Christmas Tree Equipment",
    "6D": "Specification for Pipeline Valves", "6FA": "Specification for Fire Test for Valves",
    "12F": "Specification for Shop Welded Tanks for Storage of Production Liquids",
    "12J": "Specification for Oil and Gas Separators",
    "14C": "Analysis, Design, Installation and Testing of Basic Surface Safety Systems for Offshore Production Platforms",
    "14G": "Fire Prevention and Control on Open Type Offshore Production Platforms",
    "17A": "Design and Operation of Subsea Production Systems", "17E": "Specification for Subsea Umbilicals",
    "2A-WSD": "Planning, Designing and Constructing Fixed Offshore Platforms - Working Stress Design",
    "500": "Classification of Locations for Electrical Installations at Petroleum Facilities (Division)",
    "505": "Classification of Locations for Electrical Installations at Petroleum Facilities (Zone)",
    "510": "Pressure Vessel Inspection Code",
    "520-I": "Sizing, Selection, and Installation of Pressure-Relieving Devices - Part I Sizing and Selection",
    "520-II": "Sizing, Selection, and Installation of Pressure-Relieving Devices - Part II Installation",
    "521": "Pressure-relieving and Depressuring Systems", "526": "Flanged Steel Pressure Relief Valves",
    "550": "Manual on Installation of Refinery Instruments and Control Systems", "552": "Transmission Systems",
    "560": "Fired Heaters for General Refinery Service", "570": "Piping Inspection Code",
    "582": "Welding Guidelines for the Chemical, Oil, and Gas Industries",
    "594": "Check Valves: Flanged, Lug, Wafer and Butt-welding", "598": "Valve Inspection and Testing",
    "600": "Steel Gate Valves - Flanged and Butt-welding Ends, Bolted Bonnets",
    "602": "Compact Steel Gate Valves - Flanged, Threaded, Welding, and Extended-Body Ends",
    "607": "Fire Test for Quarter-turn Valves and Valves Equipped with Nonmetallic Seats",
    "609": "Butterfly Valves: Double Flanged, Lug- and Wafer-Type",
    "610": "Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries",
    "613": "Special Purpose Gear Units for Petroleum, Chemical and Gas Industry Services",
    "614": "Lubrication, Shaft-sealing and Control-oil Systems and Auxiliaries",
    "616": "Gas Turbines for the Petroleum, Chemical, and Gas Industry Services",
    "620": "Design and Construction of Large, Welded, Low-pressure Storage Tanks", "650": "Welded Tanks for Oil Storage",
    "653": "Tank Inspection, Repair, Alteration, and Reconstruction",
    "682": "Pumps - Shaft Sealing Systems for Centrifugal and Rotary Pumps",
    "686": "Recommended Practice for Machinery Installation and Installation Design",
    "1104": "Welding of Pipelines and Related Facilities",
    "1110": "Pressure Testing of Steel Pipelines for the Transportation of Gas, Petroleum Gas, Hazardous Liquids, Highly Volatile Liquids or Carbon Dioxide",
    "2000": "Venting Atmospheric and Low-pressure Storage Tanks", "2001": "Fire Protection in Refineries",
    "2201": "Safe Hot Tapping Practices in the Petroleum and Petrochemical Industries",
}

ASME_SECOES = {"I": "Seção I - Caldeiras de potência", "II": "Seção II - Materiais", "V": "Seção V - Ensaios não destrutivos",
               "VIII-1": "Seção VIII Div. 1 - Vasos de pressão", "VIII-2": "Seção VIII Div. 2 - Vasos de pressão (regras alternativas)",
               "IX": "Seção IX - Qualificação de soldagem e brasagem"}


# ---------------------------------------------------------- título da 1ª página
TIPOS_EN = r"(?:Standard\s+)?(?:Specifications?|Test\s+Methods?|Practices?|Guide|Terminology|Classification|Method|Recommended Practice)\s+(?:for|of|on)\b"


def titulo_astm(txt):
    """'Standard Specification for ...' / 'SPECIFICATION FOR ...' (ASTM, ASME SA/SB/SFA, AWS)."""
    t = txt.split("=====")[0].replace("ﬁ", "fi").replace("ﬂ", "fl")
    m = re.search(r"(" + TIPOS_EN + r".*?)(?:\d\s*\n|\n\s*This (?:standard|specification)|\n\s*1\.\s*Scope|\n\s*INTRODUCTION|\(Identical|\n\s*1\.\s)", t, re.S | re.I)
    if not m:
        return ""
    s = limpa(m.group(1))
    s = re.sub(r"\s*\d+$", "", s)
    if len(s) > 220:
        s = s[:220].rsplit(" ", 1)[0] + "…"
    return titulo_caixa(s)


def titulo_generico(txt):
    for l in (limpa(x) for x in txt.split("=====")[0].splitlines()):
        if re.search(TIPOS_EN, l, re.I) and 15 < len(l) < 200:
            return titulo_caixa(l)
    return ""


def titulo_abnt(txt):
    linhas = [limpa(l) for l in txt.split("=====")[0].splitlines() if limpa(l)]
    for i, l in enumerate(linhas):
        if re.match(r"^(ABNT\s*)?(NBR|NB|MB|EB)[\s-]*\d", l, re.I):
            for x in linhas[i + 1:i + 5]:
                if len(x) > 6 and re.search(r"[a-zà-ú]{4}", x, re.I) and not re.search(
                        r"ABNT|Origem|CB-|Palavra|Copyright|\d{2}\.\d{3}|página|^Procedimento$|^Especificação$|^Método|^Terminologia$|^Padronização$|Associação|Registrada|^(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)", x, re.I):
                    return titulo_caixa(x[:200])
    return ""


def titulo_cliente(txt):
    t = txt.split("=====")[0]
    m = re.search(r"(?:TITLE|TÍTULO|TITULO)\s*:?\s*\n?\s*([^\n]{6,150})", t)
    if m and not re.search(r"^(ÍNDICE|INDEX|SHEET|FOLHA|REV|:)", m.group(1).strip(), re.I):
        return titulo_caixa(limpa(m.group(1)))
    return ""


# ---------------------------------------------------------- assuntos (PT)
ASSUNTOS = [
    (r"escada|ladder|stair|degrau", "escada"),
    (r"guarda.?corpo|guardrail|handrail|corrim", "guarda-corpo"),
    (r"passarela|walkway|plataforma de trabalho|grating|grade.{0,3}de piso|floor grat|grades? cogumelo|\bpiso\b", "passarela/piso"),
    (r"andaime|scaffold|millslock|orguel|metax", "andaime"),
    (r"flange", "flanges"),
    (r"gasket|\bjuntas?\b", "juntas"),
    (r"\bbolt|screw|parafus|\bnuts?\b|porca|washer|arruela|rivet|rebite|circlip|chumbador|anchor|fastener|torque|preload|nord.?lock|\bthread|rosca", "parafusos"),
    (r"sold|weld|brazing|electrode|filler metal|eletrodo|brasagem|\bSFA\b|AWS A5|Section IX|Seção IX|\bQW", "solda"),
    (r"\bpipe|piping|tubula|tubing|\btubes?\b|\btubos?\b|line list|lista de linhas|isom", "tubulação"),
    (r"valv|válvula", "válvulas"),
    (r"fitting|conex|\bunions?\b|buttweld", "conexões"),
    (r"paint|pintura|coating|revestimento|blast clean|jato|surface prep|xylan|lining|\bSSPC\b", "pintura"),
    (r"lifting|içamento|icamento|rigging|sling|linga|shackle|manilha|eyebolt|olhal|padeye|talha|hoist|guindaste|crane|cabos? de aço|wire rope|gancho|\bcintas?\b|elevação|roundsling", "içamento"),
    (r"pressure vessel|vasos? de press|boiler|caldeira|Section VIII|Seção VIII|BPVC VIII", "vaso de pressão"),
    (r"\btanks?\b|tanque", "tanques"),
    (r"\bpumps?\b|bomba|compressor|turbin|gear unit|machinery", "máquinas"),
    (r"structur|estrutur|offshore unit|steel construction|steel buildings|perfis|perfil|shapes|skid", "estruturas"),
    (r"ergonom|fatores humanos|human factor", "ergonomia"),
    (r"segurança|safety|\bEPI\b|incêndio|\bfire\b|hidrante|escape|drops|queda|CIPA|SESMT|insalubr|altura", "segurança"),
    (r"insulation|isolamento|tracing", "isolamento térmico"),
    (r"inspe|\btest|ensaio|nondestructive|não destrutiv|radiograph|ultrason|\bexam", "inspeção/ensaios"),
    (r"toler|desenho|drawing|cotagem|projeç|hachura|escalas|\bsymbol|símbolo|simbolo", "desenho técnico"),
    (r"instrument|P&ID|\bISA\b", "instrumentação"),
    (r"electr|elétric|eletric|eletricidade|\bcables?\b|IEC 60", "elétrica"),
    (r"corros|sour serv|anticorros|galvan|\bzinc", "corrosão"),
    (r"quality|qualidade|ISO 900|17025|19011", "qualidade"),
    (r"ambient|environment|resíduo|ISO 1400", "meio ambiente"),
    (r"\bsteel|\baço\b|\baco\b|alloy|stainless|inox|forging|casting|\bplates?\b|\bsheet|\bbars?\b|chapa|\bwire\b", "materiais"),
    (r"copper|nickel|alumin|titanium|zirconium|bronze|brass|cobre|níquel", "metais não ferrosos"),
    (r"concret|\bsolos?\b|\bsoil|fundaç", "civil"),
    (r"\bhoses?\b|mangueira|hidráulic|hydraulic|cilindro", "hidráulica"),
]


def assuntos(txt, padrao=()):
    out = []
    for a in padrao:
        if a not in out:
            out.append(a)
    for rx, a in ASSUNTOS:
        if a not in out and re.search(rx, txt, re.I):
            out.append(a)
    return out[:4] if out else ["geral"]


# ---------------------------------------------------------- fabricantes
FABRICANTES = ["Parker", "Swagelok", "Hennings", "Prysmian", "Crosby", "Gunnebo", "Igus", "Polimold", "3M", "SIVA", "Scafom",
               "Millslock", "Wurth", "Nord-lock", "Xylan", "Rexroth", "SKF", "Aquatic", "Ancora", "Gerdau", "Paulisteel",
               "Açotubo", "Elesa Ganter", "Robustec", "Acro", "Tellep", "Neade", "Bertolini", "Acoplatec", "Rotex", "Grayloc",
               "Previsão", "POLAR", "Quality Fix", "Rohr", "Orguel", "Mills", "Santa Clara", "CIMAF", "TecnoTêxtil", "tecnotextil",
               "Liebherr", "TakLift", "Edfer", "NORSK", "Tube-Mac", "WIKA", "SPU", "ALMEQ", "GranIHC", "Gran IHC", "Metax",
               "TechCon", "Hilti", "Ciser", "Aperam", "Prysmian", "Tellep", "Gunnebo", "Crosby"]


def fabricante(nome, rel):
    alvo = nome + " " + rel
    for f in FABRICANTES:
        if re.search(r"(?<![A-Za-z])" + re.escape(f) + r"(?![A-Za-z])", alvo, re.I):
            return {"Millslock": "Mills", "GranIHC": "Gran IHC", "Rotex": "KTR (Rotex)", "tecnotextil": "TecnoTêxtil",
                    "NORSK": "Norsk (flanges)", "S-BT": "Hilti"}.get(f, f)
    if "CATÁLOGOS FIBRA" in rel or re.search(r"GIHC|FEP-|ET-GM|ESCADA_?MARINHEIRO|EscadaMarinheiro|LDM-", nome):
        return "Gran IHC"
    if re.search(r"S-BT-HL", nome):
        return "Hilti"
    if "talhas" in rel.lower():
        return "Talhas manuais (fabricante n/i)"
    if re.search(r"cilindro|contraflange|rotulas", nome, re.I):
        return "Cilindros hidráulicos (fabricante n/i)"
    return "Fabricantes diversos"


# ---------------------------------------------------------- classificação
def classificar(u, cache, ocr, petro, npag=None, refs=(set(), set())):
    p = u["paths"][0]
    rel = p[len(RAIZ) + 1:].replace(BS, "/")
    todos = " | ".join(x[len(RAIZ) + 1:].replace(BS, "/") for x in u["paths"])
    nome = os.path.basename(p)
    s, ext = os.path.splitext(nome)
    ext = ext.lower()
    pasta = os.path.dirname(rel)
    sU = s.upper()
    e = {"codigo": "", "titulo": "", "orgao": "", "edicao": "", "tipo": "norma", "situacao": "desconhecida",
         "arquivo": "", "copias": [], "assuntos": []}
    padrao_ass = []
    memo = {}

    def pag1():
        if "t" not in memo:
            memo["t"] = texto_pag1(p, cache, ocr)
        return memo["t"]

    sup = re.search(r"SUPERAD|S U P E R A D A|cancelad|\(canc", todos, re.I)

    # ------------------------------------------------ sequência TIF (API 610)
    if u["seq"]:
        base = re.sub(r"_\d{3}$", "", s)
        e.update(codigo="API Std 610", orgao="API", edicao=ano_de(pasta),
                 titulo="%s (parcial — %d páginas digitalizadas em TIF: %s_001…_%03d.tif)" % (API_TITULOS["610"], u["seq"], base, u["seq"]))
    elif ext in (".ttf", ".otf"):
        e.update(codigo=s, titulo="Fonte tipográfica " + s, orgao="Diversos", tipo="outro")
    # ------------------------------------------------ Petrobras N
    elif re.match(r"^N-\d{2,4}(?!\d)", s) and "PETROBRAS" in rel:
        m = re.match(r"^N-(\d{2,4})(.*)$", s)
        num = "N-%04d" % int(m.group(1))
        resto = m.group(2)
        anexo = re.search(r"ANEXO\s+([A-Z])\b", resto, re.I)
        mrev = re.match(r"^[ _]+(?:rev\.\s*)?([A-Z])(?=\b|_|$)", resto)
        rev = mrev.group(1) if mrev else ""
        tn = re.search(r" - +(.+)$", resto)
        tp, rp, dp = petrobras_capa(pag1()) if not anexo else ("", "", "")
        cat = petro.get(num, {})
        rev = rev or rp
        titulo = cat.get("titulo", "")
        if not titulo or (rev and cat.get("rev") and rev != cat["rev"] and len(tp) > 8):
            titulo = tp or titulo
        if not titulo and tn:
            titulo = limpa(tn.group(1))
        ed = ("Rev. " + rev) if rev else ""
        if dp:
            ed = (ed + " (" + dp + ")") if ed else dp
        # lixo de capa: "PÚBLICA", "PÚBL 18 pági ICA nas, 4 formulários e Índice de Revisões", "9 Páginas e Formulário…", "AGO / 2002"
        titulo = re.sub(r"\s*\(Classifica[çc][ãa]o:?\s*P[ÚU]BLICA\)", "", titulo)
        titulo = re.sub(r"^P[ÚU]BL.*?ICA\b.*?Revis[õo]es\s+", "", titulo)
        titulo = re.sub(r"^P[ÚU]BLICA\s+", "", titulo)
        titulo = re.sub(r"^\d+\s+P[áa]ginas?(?:,\s*\d+\s+\w+)?\s+e\s+(?:Formul[áa]rio de Registro de Impactos|[ÍI]ndice de Revis[õo]es)\s+", "", titulo)
        titulo = re.sub(r"^[A-Z]{3}\s*/\s*\d{4}\s+", "", titulo)
        titulo = titulo_caixa(limpa(titulo))
        cod = num + (" Anexo " + anexo.group(1).upper() if anexo else "")
        if anexo:
            titulo = (titulo + " — " if titulo else "") + "Anexo " + anexo.group(1).upper()
        e.update(codigo=cod, titulo=titulo, orgao="Petrobras", edicao=ed)
        if "_2025" in todos:
            e["situacao"] = "vigente"
    elif s.startswith("0 - CATALOGO DE NORMAS PETROBRAS"):
        e.update(codigo="Catálogo N", titulo="Catálogo de Normas Técnicas Petrobras - ordem numérica", orgao="Petrobras",
                 edicao="nov/2021", tipo="outro")
    # ------------------------------------------------ ASTM
    elif "/ASTM" in "/" + pasta or re.match(r"^ASTM[_ ]", s, re.I):
        m = re.match(r"^(?:ASTM[_ -]?)?([A-GD])[ -]?(\d+(?:\.\d+)?)(?:[-_ ](\d{2,4}))?", s, re.I)
        cod = ("ASTM %s%s" % (m.group(1).upper(), m.group(2))) if m else "ASTM " + s
        t = pag1()
        md = re.search(r"Designation:\s*[A-G]\s*\d+[\w./]*\s*[–-]\s*(\d{2,4}[a-z]?)", t)
        ed = md.group(1) if md else (m.group(3) if m and m.group(3) else "")
        e.update(codigo=cod, titulo=titulo_astm(t), orgao="ASTM", edicao=ed)
        if re.search(r"a6-a6m", s, re.I):
            e.update(codigo="ASTM A6/A6M", titulo=e["titulo"] or "General Requirements for Rolled Structural Steel Bars, Plates, Shapes, and Sheet Piling")
    # ------------------------------------------------ SSPC
    elif "/SSPC" in "/" + pasta:
        m = re.match(r"^SSPC(PAINT|PS|SP|VIS|GUIDE|PA|QP|AB|TU|CHAPTER)-?([\w.]*)$", sU)
        serie, n = (m.group(1), m.group(2)) if m else ("", s)
        n = re.sub(r"^0+(?=\d)", "", n)
        if serie == "CHAPTER":
            cod = "SSPC GPP cap. " + n
            tit = "Good Painting Practice (SSPC Painting Manual vol. 1) - capítulo " + n
        else:
            nome_s = {"PAINT": "Paint", "GUIDE": "Guide"}.get(serie, serie)
            cod = "SSPC-%s %s" % (nome_s, n) if n != "COM" else "SSPC-%s (comentários)" % nome_s
            tit = SSPC_TITULOS.get("%s %s" % (serie, n), "") or titulo_generico(pag1()) or titulo_astm(pag1())
            if n == "COM":
                tit = tit or "Comentários (commentary) da série %s" % nome_s
        e.update(codigo=cod, titulo=tit, orgao="SSPC")
        padrao_ass = ["pintura"]
    # ------------------------------------------------ ASME BPVC (pastas de seções)
    elif re.search(r"/(ASME|Ansi-Asme)/(ASME ?(Sec|I |II |V |VIII|IX)|ASME  I)", "/" + pasta):
        e["orgao"] = "ASME"
        ed = ano_de(pasta)
        sec_c = re.search(r"PART C|II-C|Part C", pasta, re.I)
        msfa = re.search(r"(?:SFA[ -]?|^A)(5\.\d+)$", re.sub(r"^ASME ", "", sU))
        if (msfa and sec_c) or re.match(r"^(ASME )?SFA[ -]?5", sU):
            n = msfa.group(1) if msfa else re.search(r"5\.\d+", sU).group(0)
            e.update(codigo="ASME SFA-" + n, titulo=titulo_astm(pag1()))
            padrao_ass = ["solda"]
        elif re.match(r"^(\d{3}-)?S?[AB]-?\d", sU) and re.search(r"PART [AB]|II-[AB]|Part [AB]", pasta, re.I):
            mm = re.search(r"S?([AB])-?(\d{1,4})", sU)
            e.update(codigo="ASME S%s-%s" % (mm.group(1), mm.group(2)), titulo=titulo_astm(pag1()))
        elif re.match(r"^SA-JIS|^AJIS|^AE ?N?10028|^AEN|^AG40", sU):
            mm = re.sub(r"^S?A-?", "", sU)
            e.update(codigo="ASME SA/" + mm.replace("JIS", "JIS ").replace("EN", "EN ").replace("AE", "EN ").strip(), titulo=titulo_astm(pag1()))
        elif re.match(r"^ASME 814", sU):
            e.update(codigo="ASME SA-814", titulo=titulo_astm(pag1()))
        else:
            sec = "II"
            alvo = pasta + " " + s
            if re.search(r"VIII|8d2", alvo, re.I):
                sec = "VIII-2" if re.search(r"D2|DIV\. 2|8d2", alvo, re.I) else "VIII-1"
            elif re.search(r"Sec IX|IX -|ASME IX|QW|QB", alvo):
                sec = "IX"
            elif re.search(r"Sec V\b|ASME V\b|SECTION V\b|Sec V -", alvo):
                sec = "V"
            elif re.search(r"Sec[- ]+I\b|ASME  ?I\b|ASME I Ed", alvo):
                sec = "I"
            parte = re.sub(r"^\d{2,3}-", "", s).strip()
            if re.match(r"^(ASME|Asme)", parte) and re.search(r"Ed\.|ASME8D2|VIII D[12]$|^ASME I+ |Sec I - 20|IX 20|V - 20", parte, re.I) and not re.search(r"\d+-\d+|\d+ a \d+|pag", parte, re.I):
                parte = ""
            if re.match(r"^ASME II ([A-D]\d?) Ed", s):
                parte = "Parte " + re.match(r"^ASME II ([A-D]\d?)", s).group(1)
            sub = re.search(r"(?:PART|Part|SEÇÃO II-|II-)\s?([A-D])\b", pasta) if sec == "II" else None
            secl = "II-" + sub.group(1).upper() if sub else sec
            e["codigo"] = "ASME BPVC %s%s" % (secl, (" — " + parte) if parte else "")
            e["titulo"] = "ASME Boiler and Pressure Vessel Code, " + ASME_SECOES[sec] + \
                (" — Parte " + sub.group(1).upper() if sub else "") + ((" — " + parte) if parte else "")
            if sec == "IX":
                padrao_ass = ["solda"]
        e["edicao"] = ed
    # ------------------------------------------------ ASME / ANSI avulsas
    elif re.match(r"^(\[ASME\] |ASME|AMSE|ANSI B|asme)", s):
        s2 = s.replace("_", " ")
        m = re.search(r"(A112[\d.]+M?(?:\.\d)?|B\d+(?:\.\d+)*a?M?|PCC-\d|PTC \d+|112[\d.]+M?|3287|3977\.1|V&V|vampv)", s2, re.I)
        c = m.group(1) if m else ""
        if c.startswith("112"):
            c = "A" + c
        c = c[:1].upper() + c[1:]
        tit = ASME_TITULOS.get(c) or ASME_TITULOS.get(re.sub(r"M$", "", c), "")
        tn = re.search(r" - ([A-Za-z].{8,})$", s2)
        if tn and not re.search(r"SUPERAD|traduzida|^ERRATA", tn.group(1), re.I):
            tit = titulo_caixa(limpa(tn.group(1)))
        if not tit:
            tit = titulo_generico(pag1())
        e.update(codigo="ASME " + c if c else "ASME " + s2, titulo=tit, orgao="ASME", edicao=ano_de(s2.replace(c, "")))
        if "traduzida" in s:
            e["titulo"] += " (tradução PT)"
        if "Guidebook" in s:
            e.update(codigo="Guidebook ASME IX", titulo="Guidebook to ASME Section IX - Welding Qualifications", tipo="livro")
            padrao_ass = ["solda"]
        if re.search(r"vampv", s, re.I):
            e.update(codigo="ASME V&V 10", titulo="Guide for Verification and Validation in Computational Solid Mechanics", edicao="2006")
        if "FLANGE" in s:
            e["titulo"] = ASME_TITULOS["B16.5"]
    # ------------------------------------------------ API
    elif re.match(r"^(API|api|rp |RP |spec|Spec)", s) and ("/API" in "/" + pasta or "Standards" in pasta or sU.startswith("API")):
        t = re.sub(r"^(API[- ]?)?(STD |RP |spec\.? |Spec\.? )?", "", s, flags=re.I).strip()
        m = re.match(r"^(\d+ ?[A-Z]{1,2}\b|\d+[A-Z]*|2A[- ]?WSD)", t, re.I)
        num = m.group(1).replace(" ", "").upper() if m else t.split(" ")[0]
        if num.startswith("2A"):
            num = "2A-WSD"
        tipo_api = "RP " if re.search(r"\bRP\b", s, re.I) else ("Spec " if re.search(r"spec", s, re.I) else ("Std " if "STD" in s else ""))
        part = re.search(r"(?:part|PT)\s*(I{1,2})\b", s, re.I)
        key = "520-" + part.group(1).upper() if num == "520" and part else num
        cod = "API " + tipo_api + num + ((" Part " + part.group(1).upper()) if key.startswith("520-") else "")
        tit = API_TITULOS.get(key, API_TITULOS.get(num, ""))
        if re.search(r"ERRATA", s, re.I):
            tit += " (errata)"
        if "Seç 1" in s:
            tit += " - Part I, Section 1"
        if re.search(r"pg \d", s):
            tit += " (" + re.search(r"pg [\d-]+", s).group(0) + ")"
        e.update(codigo=cod, titulo=tit.strip(), orgao="API", edicao=ano_de(s.replace(num, "", 1)))
    # ------------------------------------------------ ABENDI
    elif "/Abende" in "/" + pasta:
        c = re.sub(r"\s*-?\s*(rev.*|\d{4}.*|REVISADO.*)$", "", s, flags=re.I).strip()
        e.update(codigo="ABENDI " + c, orgao="ABENDI", edicao=ano_de(s), titulo=titulo_abnt(pag1()) or titulo_generico(pag1()))
        padrao_ass = ["inspeção/ensaios"]
    # ------------------------------------------------ ABNT
    elif re.match(r"^(\[NBR\] |NBR|NB |MB |EB |NM |NBR_)", s):
        s2 = s.replace("[NBR] ", "NBR ").replace("_", " ").replace("NBR-ISO-", "NBR ISO ")
        mo = re.search(r"\(NBR (\d+)\)", s2)
        mm = re.match(r"^(NBR|NB|MB|EB|NM)\s*((?:ISO[- ]IEC|ISO|IEC)\s*)?(\d+(?:[-.]\d+)*(?: [IV]+\b)?)", s2)
        nota = ""
        if mo:
            cod = "ABNT NBR " + mo.group(1)
            nota = " (antiga %s %s)" % (mm.group(1), mm.group(3)) if mm else ""
        elif mm:
            pre = (mm.group(2) or "").strip().replace("-", "/").replace(" ", "/")
            cod = "ABNT %s %s%s" % (mm.group(1), pre + " " if pre else "", mm.group(3))
        else:
            cod = "ABNT " + s2
        mt = re.search(r" - ([A-Za-zÀ-ú].{3,})$", s2)
        tit = limpa(mt.group(1)) if mt and not re.match(r"^(Constran|MAI|SUPERAD)", mt.group(1)) else ""
        if not tit:
            tit = titulo_abnt(pag1())
        resto = s2.replace(mm.group(0), "", 1) if mm else s2
        resto = re.sub(r"\(NBR \d+\)", "", resto)
        ed = ano_de(resto)
        m2 = re.match(r"^[- ]+(\d{2})(?:\D|$)", resto)
        if not ed and m2 and int(m2.group(1)) > 50:
            ed = "19" + m2.group(1)
        e.update(codigo=re.sub(r"\s+", " ", cod), titulo=(tit + nota).strip(), orgao="ABNT", edicao=ed)
        mp = re.search(r"\(pg\.? ?([\d a-]+)\)", s2)
        if mp:
            e["titulo"] += " (págs. " + mp.group(1).strip() + ")"
        if re.search(r"antiga 12246", s2):
            e["titulo"] += " (antiga NBR 12246)"
        if "Constran" in s2:
            e["titulo"] += " (cópia Constran)"
    # ------------------------------------------------ NR (MTE)
    elif re.match(r"^(NR[-_ ]?\d|MANUAL NR|ENC Altera)", s):
        m = re.search(r"NR[-_ ]?(\d{1,2})", s)
        n = "%02d" % int(m.group(1))
        tn = re.search(r"\d{4} - (.+)$", s)
        tit = titulo_caixa(limpa(tn.group(1))) if tn else NR_TITULOS.get(n, "")
        if not tn and re.search(r"anexo II", s, re.I):
            tit = NR_TITULOS.get(n, "") + " - Anexo II (plataformas e instalações de apoio)"
        if "MANUAL" in s:
            tit = "Manual da NR-35 - Trabalho em altura"
        if s.startswith("ENC"):
            tit = "E-mail: alteração da NR-18 - aprovação do Anexo I (plataforma de trabalho aéreo)"
        if "Consulte Ambiental" in s:
            tit += " (versão Consulte Ambiental)"
        if "Atualizada 2011" in s:
            tit += " (atualizada 2011)"
        e.update(codigo="NR-" + n, titulo=tit, orgao="MTE", edicao=ano_de(s) if "Portaria" not in s else "2002")
        if rel.startswith("03 - Standards"):
            e["situacao"] = "vigente"
        if ext in (".htm",) or "MANUAL" in s:
            e["tipo"] = "outro"
    elif s == "Legislacao":
        e.update(codigo="Legislação (NRs)", titulo="Planilha de legislação (NRs)", orgao="MTE", tipo="outro")
    # ------------------------------------------------ AWS
    elif re.match(r"^(ANSI-)?AWS", s):
        m = re.search(r"([A-D]\d+\.\d+M?)", s)
        c = m.group(1) if m else s
        tn = re.search(r"\d{4} - (.+)$", s)
        tit = titulo_caixa(limpa(tn.group(1))) if tn else (titulo_astm(pag1()) or titulo_generico(pag1()))
        e.update(codigo="AWS " + c, titulo=tit, orgao="AWS", edicao=ano_de(s.replace(c, "")))
        if c == "A3.0" and not tit:
            e["titulo"] = "Standard Welding Terms and Definitions"
        padrao_ass = ["solda"]
    # ------------------------------------------------ DNV
    elif re.match(r"^(DNV|dnv|DNF)", s):
        m = re.search(r"(OS|ST|RP)[- ]?([A-Z]?\d{3,4}(?:-\d)?)", s, re.I)
        c = "DNV-%s-%s" % (m.group(1).upper(), m.group(2).upper()) if m else s
        if "0027" in s:
            c = "DNV Standard for Certification 2.7-? / Marine Lifting"
        if re.search(r"rp-n-pdf", s, re.I):
            c = "DNVGL-RP-N (série)"
        tit = ""
        for l in (limpa(x) for x in pag1().split("=====")[0].splitlines()):
            if len(l) > 12 and re.search(r"[a-z]{4}", l) and not re.search(r"DNV|edition|©|www|copyright|\d{4}-\d{2}|OFFSHORE STANDARD|STANDARD$|RECOMMENDED PRACTICE$|The electronic|pdf", l, re.I):
                tit = l
                break
        if "E273" in s and not tit:
            tit = "Portable offshore units"
        if "PROJETO DE SKID" in s:
            tit = (tit + " (cópia 'projeto de skid')").strip()
        if "Marine-Lifting" in s and not tit:
            tit = "Marine Lifting"
        e.update(codigo=c, titulo=titulo_caixa(tit), orgao="DNV", edicao=ano_de(s) or ano_de(pag1()[:400]))
    # ------------------------------------------------ ISA
    elif re.match(r"^isa", s, re.I):
        m = re.search(r"75[.-](\d+)(?:[.-](\d+))?", s)
        if "CODIFICA" in s:
            c, tit = "ISA 5.1 (codificação)", "Codificação de instrumentação ISA (2009)"
        else:
            c = "ISA 75.%s%s" % (m.group(1), "." + m.group(2) if m.group(2) else "") if m else s
            tit = titulo_generico(pag1())
            if not tit:
                tt = [limpa(x) for x in pag1().split("=====")[0].splitlines() if len(limpa(x)) > 15 and re.search(r"[a-z]{4}", x)]
                tit = tt[0] if tt else ""
        e.update(codigo=c, titulo=tit, orgao="ISA", edicao=ano_de(s.replace("75.", "")))
        padrao_ass = ["válvulas", "instrumentação"]
    # ------------------------------------------------ MSS
    elif re.match(r"^MSS|^mss", s):
        m = re.search(r"SP[- ]?(\d+)", s, re.I)
        tit = titulo_generico(pag1())
        if not tit:
            tt = [limpa(x) for x in pag1().split("=====")[0].splitlines() if len(limpa(x)) > 15 and re.search(r"[a-z]{4}", x) and not re.search(r"MSS|Manufacturers|Copyright|Standardization Society", x)]
            tit = titulo_caixa(tt[0]) if tt else ""
        e.update(codigo="MSS SP-%s" % m.group(1).lstrip("0"), titulo=tit, orgao="MSS", edicao=ano_de(s))
    # ------------------------------------------------ NORSOK
    elif re.search(r"NORSOK", s, re.I) or "Standards/Norsok" in rel:
        m = re.search(r"([LMNPR])-(SR-)?(\d{3})", s)
        c = "NORSOK %s-%s%s" % (m.group(1), m.group(2) or "", m.group(3)) if m else "NORSOK " + s
        tn = re.search(r"\(([^()]+)\)", s) or re.search(r"\d{3}(?:-CR)?\s+([A-Za-z].+)$", s)
        tit = limpa(tn.group(1)) if tn else ""
        if not tit:
            tt = [limpa(x) for x in pag1().split("=====")[0].splitlines() if len(limpa(x)) > 10 and re.search(r"[a-z]{4}", x) and not re.search(r"NORSOK|standard|Rev\.|Edition|reserved|Copyright", x, re.I)]
            tit = tt[0] if tt else ""
        if "Lifting" in s:
            tit = "Lifting Equipment"
        if "Template" in s:
            c, tit = "NORSOK (modelo)", "Template de documento NORSOK"
        e.update(codigo=c, titulo=tit, orgao="NORSOK", edicao=ano_de(s))
        if ext == ".zip":
            e["titulo"] = "Pipes and Valves (arquivo compactado)"
    # ------------------------------------------------ ISO / DIN / BS avulsas
    elif re.match(r"^(\[ISO\] |ISO|DIN|BS |EN-ISO|pdfcoffee\.com_(iso|din)|NBR_ISO)", s, re.I):
        s2 = s.replace("pdfcoffee.com_", "").replace("[ISO] ", "ISO ").replace("_", " ").replace("NBR ISO", "ISO")
        m = re.match(r"^(BS EN ISO|DIN EN ISO|DIN|ISO|BS|EN-ISO)[- ]?(\d+(?:-\d)?)", s2, re.I)
        org = m.group(1).upper().replace("-", " ") if m else "ISO"
        c = "%s %s" % (org, m.group(2)) if m else s2
        if s.startswith("NBR_ISO"):
            c = "ABNT NBR ISO 724"
        tn = re.search(r"(?:\d{4}|MODIFIED|DIN EN)\s*-?\s*_?\s*([A-Za-z—].{6,})$", s2)
        tit = limpa(tn.group(1).lstrip("— ")) if tn else ""
        if re.search(r"pdf|pr [0-9a-f]{6}|stainless-steel", tit):
            tit = ""
        if re.search(r"din-25201", s, re.I):
            tit = "Stainless steel wedge lock washers"
        if not tit:
            tit = titulo_generico(pag1())
        if not tit:
            for l in (limpa(x) for x in pag1().split("=====")[0].splitlines()):
                if 12 < len(l) < 160 and re.search(r"[a-z]{4}", l) and not re.search(r"ISO|DIN|Copyright|©|www|pdf|Reference|edition|Edição|Licensed|Ausgabe|Normenausschuss", l, re.I):
                    tit = l
                    break
        orgao = "DIN" if org.startswith("DIN") else ("BSI" if org.startswith("BS") else "ISO")
        if c.startswith("ABNT"):
            orgao, tit = "ABNT", tit or "Rosca métrica ISO de uso geral (perfil básico)"
        e.update(codigo=c, titulo=titulo_caixa(tit), orgao=orgao, edicao=ano_de(s2.replace(m.group(2), "", 1) if m else s2))
        if "BS 1873" in s:
            e["titulo"] = "Steel globe and globe stop and check valves (flanged and butt-welding ends) for the petroleum, petrochemical and allied industries"
    elif re.match(r"^NFPA", s):
        e.update(codigo="NFPA 15", titulo="Standard for Water Spray Fixed Systems for Fire Protection", orgao="NFPA", edicao=ano_de(pag1()[:600]))
    elif "/JIS" in "/" + pasta:
        if "JIS" in s:
            e.update(codigo="JIS B2220", titulo="Steel pipe flanges", orgao="JIS")
        else:
            e.update(codigo="Glossário JIS", titulo="Glossário de terminologia (pasta JIS)", orgao="JIS", tipo="outro")
    elif "/Ohsas" in "/" + pasta:
        m = re.search(r"1800[12]", s)
        material = re.search(r"Apostila|Curso|Coleta|Livio", s)
        e.update(codigo="OHSAS " + m.group(0) if m else "OHSAS (material de apoio)", titulo=limpa(s), orgao="OHSAS",
                 edicao=ano_de(s), tipo="outro" if (material or not m) else "norma")
        padrao_ass = ["segurança"]
    elif pasta.endswith("/Sa"):
        norma = re.match(r"^(Norma )?SA ?8000", s)
        e.update(codigo="SA 8000", titulo=limpa(s), orgao="SAI", edicao=ano_de(s), tipo="norma" if norma else "outro")
        padrao_ass = ["segurança"]
    elif "energia nuclear" in pasta:
        m = re.match(r"^Nrm(\d+)", s)
        if m:
            tit = ""
            for l in (limpa(x) for x in pag1().split("=====")[0].splitlines()):
                if 12 < len(l) < 160 and re.search(r"[a-zà-ú]{4}", l) and not re.search(r"CNEM|Norma|Resolução|Comissão|Nuclear$|D\.O\.U|\d{2}/\d{2}", l):
                    tit = l
                    break
            e.update(codigo="CNEM NE " + m.group(1), titulo=tit, orgao="CNEM")
        else:
            e.update(codigo=limpa(s)[:60], titulo=limpa(s), orgao="CNEM", tipo="outro")
    elif "/IMCA" in "/" + pasta:
        s2 = s.replace("-", " ").replace("pdf free", "").replace(" amp ", " & ")
        m = re.search(r"\b([A-Z]{1,4}) ?(\d{3})\b", s2.upper())
        e.update(codigo="IMCA " + (m.group(1) + " " + m.group(2) if m else limpa(s2)[:40]), titulo=limpa(s2), orgao="IMCA", edicao=ano_de(s))
        padrao_ass = ["içamento"] if re.search(r"lift|sling|grommet|rigging", s, re.I) else []
    elif "/WSTDA" in "/" + pasta:
        e.update(codigo="WSTDA RS-1", titulo="Synthetic polyester roundslings (recommended standard specification)", orgao="WSTDA", edicao="2010")
        padrao_ass = ["içamento"]
    elif "/IACAS" in "/" + pasta:
        e.update(codigo="IACAS Guide 40", titulo="IACAS - Guide 40", orgao="IACAS")
    elif pasta.endswith("/EN"):
        e.update(codigo="EPRS BRI(2021)694206", titulo="Briefing do Serviço de Pesquisa do Parlamento Europeu (2021)", orgao="UE", tipo="outro")
    elif "Naval Lloyds" in pasta:
        e.update(codigo="LR MQPS 0-1", titulo="Lloyd's Register - procedimento de qualificação (PQR)", orgao="Lloyd's Register")
        padrao_ass = ["solda"]
    elif re.match(r"^ANSI[- ]", s):
        mp = {"AISC": ("ANSI/AISC 360-10", "Specification for Structural Steel Buildings", "AISC"),
              "IEEE": ("ANSI/IEEE C2", "National Electrical Safety Code", "IEEE"),
              "ARI": ("ANSI/ARI Std 560", "Absorption Water Chilling and Water Heating Packages", "AHRI"),
              "ASQC": ("ANSI/ASQC Z1.4", "Sampling Procedures and Tables for Inspection by Attributes", "ASQ")}
        k = next((k for k in mp if k in s), None)
        if k:
            e.update(codigo=mp[k][0], titulo=mp[k][1], orgao=mp[k][2], edicao=ano_de(s))
        else:
            e.update(codigo=s, titulo=limpa(s), orgao="ANSI")
    elif s.startswith("IOGP"):
        e.update(codigo="IOGP 454", titulo="Human factors engineering in projects", orgao="IOGP", edicao="2020")
    elif s.startswith("ABS - ERGONOMIC"):
        e.update(codigo="ABS Ergonomic Notations", titulo="Guide for Ergonomic Notations", orgao="ABS", edicao="set/2021")
    elif "MARINE VESSELS RULES ABS" in rel:
        m = re.search(r"Part_?(\w+?)_", s)
        parte = ("Part " + m.group(1)) if m else "Notices and General Information"
        e.update(codigo="ABS MVR " + parte, titulo="Rules for Building and Classing Marine Vessels - " + parte, orgao="ABS", edicao="jan/2022")
    elif s.startswith("SISTEMA INTERNACIONAL"):
        e.update(codigo="SI 9ª ed.", titulo="Sistema Internacional de Unidades - SI (9ª edição)", orgao="INMETRO", edicao="2025", tipo="outro")
    elif re.match(r"^NOTA T[ÉE]CNICA", s):
        e.update(codigo="NT ANP-RJ 10/2023", titulo="Disseminação de melhores práticas da indústria em Fatores Humanos", orgao="ANP", edicao="2023", tipo="outro")
        padrao_ass = ["ergonomia"]
    elif s.startswith("EN-ISO-9013"):
        e.update(codigo="EN ISO 9013", titulo="Thermal cutting - Classification of thermal cuts - Geometrical product specification and quality tolerances", orgao="ISO", edicao="2017")
    elif "/AISC" in "/" + pasta or re.search(r"^\[(ANSI-)?AISC\]|^AISC|Specification for Structural Steel Buildings|load and resistance factor design", s, re.I):
        is_norma = bool(re.search(r"360|Specification", s))
        e.update(codigo="AISC 360" if is_norma else "AISC Manual", titulo=limpa(re.sub(r"^\[.*?\]\s*", "", s).replace("_", " ")),
                 orgao="AISC", edicao=ano_de(s), tipo="norma" if is_norma else "livro")
        if re.search(r"14th", s):
            e["edicao"] = "14ª ed."
        if re.search(r"15th|v15", s):
            e["edicao"] = "15ª ed."
    # ------------------------------------------------ Especificações Petrobras (ETs, diretrizes, padrões, plataformas)
    elif re.search(r"^(I-)?ET[- ]|^i-et-|^(I-)?DR-ENGP|^PE-\d|^P56-ET|^1 - ET|^I-LI|^ET P-56|^FDOC|^\[PETROBRAS\]", s, re.I) or \
            re.search(r"PETROBRAS/(ETs|DIRETRIZES)|^00 - Miscellaneous/(P\d\d|PRA-1)", rel):
        m = re.search(r"((?:I-)?(?:ET|LI|DR)-[\w.&-]+?|PE-[\w&]+-\d+|FDOC-\d+)(?=[ _(]|$)", s, re.I)
        c = m.group(1) if m else limpa(s)[:60]
        tn = re.search(r" - +(.+)$", s)
        tit = titulo_caixa(limpa(tn.group(1))) if tn and not re.match(r"^(ANEXO|C$|\d)", tn.group(1)) else ""
        if not tit:
            tit = titulo_cliente(pag1())
        e.update(codigo=c.upper() if c.lower().startswith("i-et") else c, titulo=tit, orgao="Petrobras", edicao=revisao(s),
                 tipo="especificacao")
        if re.match(r"^(I-)?DR-ENGP", s) and not e["titulo"]:
            e["titulo"] = "Diretriz de engenharia Petrobras " + c
        if re.match(r"^PE-", s) and not e["titulo"]:
            e["titulo"] = limpa(re.sub(r"^PE-[\w&]+-\d+[_ -]*", "", s)) or "Padrão Petrobras " + c
        if "ANEXO A" in s:
            e["titulo"] = (e["titulo"] + " — Anexo A").strip(" —")
        if "PEP-001" in s and "Pintura" in s:
            e["titulo"] = "Pintura e revestimentos"
        if s.startswith("FDOC"):
            e.update(titulo="Diretrizes de elaboração de documentos Petrobras", tipo="outro")
        if s.startswith("[PETROBRAS]"):
            e.update(codigo="PDI FPSO P-32", titulo="pdi-fpso-p-32", tipo="outro")
        if "P57" in rel:
            e.update(orgao="SBM", codigo=re.match(r"^\w+", s).group(0), titulo=limpa(re.sub(r"^\w+\s*-?\s*", "", s)) + " (P-57)")
        else:
            pl = re.search(r"/(P\d\d(?: e P20)?|PRA-1)", "/" + rel)
            if pl:
                e["titulo"] = (e["titulo"] + " (" + pl.group(1).replace("P", "P-", 1) + ")").strip()
        if ext in (".xls", ".xlsx", ".xlsm") or re.search(r"lista", s, re.I):
            e["titulo"] = e["titulo"] or limpa(s)
        if ext == ".zip":
            e["tipo"] = "outro"
    elif re.match(r"^00 - Miscellaneous/EQUINOR", rel):
        m = re.match(r"^([\w.]+-[\w.-]+?)(?:_[\w]+)?(?=\s|$)", s)
        c = m.group(1) if m else limpa(s)[:60]
        tn = re.search(r"\s+-?\s*([A-Za-z][A-Za-z ,&/()-]{5,})$", s.replace("_I_", " "))
        tit = limpa(tn.group(1)) if tn else titulo_cliente(pag1())
        e.update(codigo=c, titulo=titulo_caixa(tit), orgao="Equinor", edicao=revisao(s), tipo="especificacao")
        if re.match(r"^GIHC", s):
            e.update(orgao="Gran IHC", titulo=e["titulo"] or "Procedimento Gran IHC")
        if ext in (".png", ".docx", ".xlsx"):
            e.update(tipo="outro", titulo=e["titulo"] or limpa(s))
    elif re.match(r"^00 - Miscellaneous/MODEC", rel):
        m = re.match(r"^(\d{4}-[\w-]+?)(?: -|\s|\(|=|$)", s)
        c = m.group(1) if m else limpa(s)[:60]
        tn = re.search(r"(?: - |\(|\s)([A-Za-z].+?)\)?$", s[len(c):]) if m else None
        tit = limpa(tn.group(1)) if tn else (titulo_cliente(pag1()) if m else limpa(s))
        e.update(codigo=c, titulo=titulo_caixa(tit), orgao="MODEC", edicao=revisao(s), tipo="especificacao")
        if "FPSO FLUMINENSE" in rel:
            e["titulo"] += " (FPSO Fluminense)"
        mv = re.search(r"/(MV-\d+)", rel)
        if mv and mv.group(1) not in e["titulo"]:
            e["titulo"] += " (" + mv.group(1) + ")"
        if ext in (".png", ".msg", ".docx", ".xlsm") or re.search(r"PITs|ANEXO I", s):
            e["tipo"] = "outro"
    elif re.match(r"^00 - Miscellaneous/SBM", rel):
        m = re.match(r"^((?:PE|PO|OO|SP|SZ|SO|SS|LP)[A-Z0-9]{6,}(?:-\d+)?|SOF \d+ A\d|ESS - ES45000 SPT92022 A2|SPEC 01X01|APP III-CDR HI39490 SPV92828|MDS SPF92087A1)", s)
        c = m.group(1) if m else limpa(s)[:60]
        tit = limpa(s[len(c):]) if m else limpa(s)
        if not tit:
            tit = titulo_cliente(pag1())
        sub = re.search(r"SBM/(?:c\) Procedimentos SBM/)?([^/]+)", rel)
        nomes = {"CDI": "Cidade de Ilhabela", "CDM": "Cidade de Maricá", "CDP": "Cidade de Paraty", "CDS": "Cidade de Saquarema",
                 "ESS": "Espírito Santo", "Cidade Ilha Bela": "Cidade de Ilhabela", "Cidade de Paraty": "Cidade de Paraty"}
        if sub and sub.group(1) in nomes:
            tit = (tit + " (" + nomes[sub.group(1)] + ")").strip()
        e.update(codigo=c, titulo=titulo_caixa(tit), orgao="SBM", edicao=revisao(s) if not m else "", tipo="especificacao")
    elif re.match(r"^00 - Miscellaneous/(3R-3|GRAN SERVICES)", rel):
        m = re.match(r"^(GS-[\w-]+?) r(\d+)", s)
        e.update(codigo=m.group(1) if m else limpa(s)[:60], titulo=limpa(re.sub(r"^GS-[\w-]+ r\d+ - ", "", s)),
                 orgao="Gran Services", edicao=("Rev. " + m.group(2)) if m else "", tipo="especificacao" if m else "outro")
    elif re.match(r"^00 - Miscellaneous/Trident", rel):
        e.update(codigo="Trident - poliacetal", titulo="Procedimento poliacetal", orgao="Trident", tipo="especificacao")
    elif rel.startswith("04 - Work Instruction"):
        if s.startswith("FDOC"):
            e.update(codigo="FDOC-003800", titulo="Diretrizes de elaboração de documentos Petrobras", orgao="Petrobras", tipo="outro")
        else:
            e.update(codigo=s, titulo=limpa(s), orgao="Friplan", tipo="outro")
    # ------------------------------------------------ Livros / apostilas
    elif rel.startswith("01 - Books") or "Tubulação Industrial/" in rel and not re.search(r"Swagelok|WIKA", rel) or \
            re.search(r"Wire Rope Splicing|curso rigging|Rigging Avançado|Exerc[íi]cios|Resolu[çc][ãa]o dos|^artigo -", s, re.I):
        s2 = s.replace("[ISO] ", "ISO ").replace("[NBR] ", "NBR ")
        mn = re.match(r"^(NBR ISO|NBR|DIN|ISO)[ -]?(\d+(?:-\d+)?)", s2)
        if mn:
            org = {"NBR": "ABNT", "NBR ISO": "ABNT", "DIN": "DIN", "ISO": "ISO"}[mn.group(1)]
            tn = re.search(r" - (.+)$", s2)
            e.update(codigo=("ABNT " if org == "ABNT" else "") + mn.group(1) + " " + mn.group(2), titulo=limpa(tn.group(1)) if tn else "",
                     orgao=org, edicao=ano_de(s2.replace(mn.group(2), "", 1)))
            fix = {"8800": "Projeto de estruturas de aço e de estruturas mistas de aço e concreto de edifícios",
                   "898-1": "Mechanical properties of fasteners made of carbon steel and alloy steel - Part 1: Bolts, screws and studs",
                   "4014": "Hexagon head bolts - Product grades A and B", "4017": "Hexagon head screws - Product grades A and B"}
            if mn.group(2) in fix:
                e["titulo"] = fix[mn.group(2)]
        elif s.startswith("[ASME] B16.5"):
            e.update(codigo="ASME B16.5", titulo=ASME_TITULOS["B16.5"], orgao="ASME")
        elif re.search(r"asme-vampv", s, re.I):
            e.update(codigo="ASME V&V 10", titulo="Guide for Verification and Validation in Computational Solid Mechanics", orgao="ASME", edicao="2006")
        elif s.startswith("TP2016-001"):
            e.update(codigo="TP2016-001 Rev01", titulo="Padeye Guide", orgao="Diversos", tipo="livro")
            padrao_ass = ["içamento"]
        else:
            m = re.match(r"^\[([^\]]+)\]\s*(.+)$", s)
            autor = m.group(1) if m else ""
            t = m.group(2) if m else s
            e.update(codigo=limpa(t.replace("_", " "))[:60], titulo=limpa(t.replace("_", " ")), orgao=autor.title() if autor else "Livros e apostilas",
                     edicao=ano_de(s), tipo="livro")
            if ext in (".png", ".txt", ".rar", ".xlsx"):
                e["tipo"] = "outro"
            if not rel.startswith("01 - Books"):
                e["orgao"] = "Livros e apostilas"
    # ------------------------------------------------ Catálogos de fabricantes e diversos
    elif rel.startswith("02 - Brochures") or re.search(r"Andaime tubular|COMPRA TÉCNICA|PERFIS METÁLICOS|Swagelok|WIKA|/RIGGING|/Manuais", "/" + rel) or \
            re.match(r"^(Nord-Lock|Surface Protection|Tabela_Nord)", s):
        f = fabricante(s, rel)
        e.update(codigo=limpa(s.replace("_", " "))[:60], titulo=limpa(s.replace("_", " ")), orgao=f, edicao=ano_de(s), tipo="catalogo")
        if re.search(r"Certificad|Ensaio|Treinamento|Portf[óo]lio|Plano de Rigging|Apresenta[çc][ãa]o|Mem[óo]ria de C|LDM-", s, re.I):
            e["tipo"] = "outro"
        if "BOOK ANDAIMES" in rel:
            m = re.search(r"ANDAIMESTÍPICOS-([\w-]+?)-R(\d+)", s)
            e.update(orgao="Gran Services", tipo="especificacao", codigo="DE-GRANSERVICES-ANDAIMES TÍPICOS-" + (m.group(1) if m else ""),
                     titulo="Book de andaimes típicos - desenho " + (m.group(1) if m else s), edicao=("R" + m.group(2)) if m else "")
        if "/Manuais" in "/" + rel:
            e.update(orgao="PONCAD", tipo="outro")
        if re.search(r"GIHC-PROD-ET|GS-PROD-ET|ET-GM", s):
            e["tipo"] = "especificacao"
    elif "Reference tables" in rel:
        e.update(codigo=limpa(s), titulo="Tabela de referência (planilha) - " + limpa(s), orgao="Friplan", tipo="outro")
    else:
        e.update(codigo=limpa(s)[:60], titulo=limpa(s), orgao="Diversos", tipo="outro")

    # ------------------------------------------------ pós-processamento
    if ext in (".jpg", ".png", ".zip", ".rar", ".msg", ".csv", ".txt", ".htm", ".ttf"):
        e["tipo"] = "outro"
    if sup:
        e["situacao"] = "superada"
    rec = cache.get(p, {})
    if rec.get("zerado"):
        e["titulo"] = (e["titulo"] + " " if e["titulo"] else "") + "[ARQUIVO CORROMPIDO: conteúdo zerado, sem cópia íntegra]"
    e["orgao"] = e["orgao"] or "Diversos"
    e["titulo"] = limpa(e["titulo"])
    e["codigo"] = limpa(e["codigo"])
    e["arquivo"] = p.replace(BS, "/")
    e["copias"] = [x.replace(BS, "/") for x in u["paths"][1:]]
    e["assuntos"] = assuntos(" ".join([e["codigo"], e["titulo"], rel]), padrao_ass)
    n = rec.get("np") or (npag or {}).get(p) or u["seq"]
    if n:
        e["paginas"] = n
    pares, caminhos = refs
    a = ano_de(e["edicao"])
    if (a and (chave_ref(e["codigo"]), a) in pares) or any(x.lower() in caminhos for x in [e["arquivo"]] + e["copias"]):
        e["em_referencias"] = True
    if not e["copias"]:
        del e["copias"]
    return e


# ---------------------------------------------------------------- principal
def main():
    arquivos = varrer()
    unidades = agrupar(arquivos)
    if len(sys.argv) > 1 and sys.argv[1] == "extrair":
        extrair(unidades)
        return
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    ocr = json.load(open(OCR, encoding="utf-8-sig")) if os.path.exists(OCR) else {}
    petro = catalogo_petrobras()
    npag = contar_paginas(unidades, cache)
    refs = referencias()
    cat = [classificar(u, cache, ocr, petro, npag, refs) for u in unidades]
    # Petrobras N: revisão mais antiga que a revisão vigente (pastas Normas_PORT_*_2025) -> superada
    vig = {}
    for e in cat:
        m = re.match(r"Rev\. ([A-Z])", e["edicao"])
        if e["orgao"] == "Petrobras" and e["situacao"] == "vigente" and m:
            vig[e["codigo"]] = max(vig.get(e["codigo"], ""), m.group(1))
    for e in cat:
        m = re.match(r"Rev\. ([A-Z])", e["edicao"])
        if e["orgao"] == "Petrobras" and e["situacao"] == "desconhecida" and m and e["codigo"] in vig:
            e["situacao"] = "superada" if m.group(1) < vig[e["codigo"]] else "vigente"

    def chave(e):
        c = re.sub(r"\d+", lambda m: m.group(0).zfill(6), sem_acento(e["codigo"]).upper())
        return (sem_acento(e["orgao"]).upper(), c, e["edicao"], e["arquivo"])

    cat.sort(key=chave)
    with open(SAIDA, "w", encoding="utf-8") as f:   # compacto: uma entrada por linha
        f.write("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in cat) + "\n]\n")
    print("arquivos considerados:", len(arquivos), "| entradas:", len(cat), "| cópias removidas:", len(arquivos) - len(cat),
          "| por conteúdo idêntico (nome diferente):", sum(1 for u in unidades if u.get("hash")),
          "| tamanho ilegível:", sum(1 for _, s in arquivos if s < 0))
    print("superadas:", sum(1 for e in cat if e["situacao"] == "superada"), "| em referencias/:", sum(1 for e in cat if e.get("em_referencias")),
          "| com nº de páginas:", sum(1 for e in cat if e.get("paginas")))
    print("por órgão:", collections.Counter(e["orgao"] for e in cat).most_common())
    print("por tipo:", collections.Counter(e["tipo"] for e in cat).most_common())
    print("sem título:", sum(1 for e in cat if not e["titulo"]))


if __name__ == "__main__":
    main()
