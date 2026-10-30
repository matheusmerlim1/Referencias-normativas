"""Gera conteudo/normas_info.json: dados descritivos de cada norma de conteudo/normas.json,
lidos do próprio PDF (nunca inventados):

  { "<id>": { "paginas": int,
              "escopo": "texto do item Escopo/Scope/Objetivo (≤ 900 car.)", "pagina_escopo": int,
              "definicoes": [{"termo", "texto" (≤ 300 car.), "pagina"}],   # até 40
              "referencias_normativas": ["ISO 898-1", ...], "pagina_referencias": int,   # até 60
              "substitui": "frase curta (opcional)",
              "fonte": "ocr" (só quando o texto veio de OCR) } }

Páginas = físicas (1-based).  Sem texto no original → cópia OCR (referencias/ocr/_origem.json);
sem cópia → OCR em memória (Tesseract) só das primeiras páginas.
Lê só as primeiras 30 páginas (escopo/referências) e 60 (definições).
Página em 2 colunas (ASTM/ASME/API/OCR) é remontada coluna a coluna (palavras + calha vertical).

Uso:  python -P ferramentas/info_normas.py            → grava conteudo/normas_info.json e imprime estatísticas
      python -P ferramentas/info_normas.py <id> ...   → só imprime o resultado dessas normas (não grava)
"""
import json
import multiprocessing as mp
import os
import re
import sys
from collections import defaultdict

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recursos import procs  # noqa: E402

pymupdf.TOOLS.mupdf_display_errors(False)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "conteudo", "normas_info.json")
MAX_PAG = 30          # escopo / referências
MAX_PAG_DEF = 60      # definições
MAX_ESCOPO = 900
MAX_DEF = 300
N_DEF = 40
N_REF = 60
N_OCR = 14            # páginas lidas por OCR em memória quando o PDF não tem texto nem cópia OCR
TESSDATA = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tessdata")

# ---------------------------------------------------------------- títulos de seção
# prefixo de numeração: "1", "1.1", "1.", "U-1", "Section 1", "A 300" (DNV antigo), "C." , "I"
NUM = (r"(?:(?:section|se[cç][aã]o|article|art\.?|cap[ií]tulo|part)\s+)?"
       r"(?:[A-Z]{1,4}-)?(?:\d{1,2}(?:\.\d{1,2}){0,2}|\d{3}(?:\.\d{1,2}){0,2}|[A-Z]\s?\d{3}|[IVX]{1,4}|[A-Z])?[.)]?(?:\s*[-–—]\s)?")
T_ESCOPO = (r"objetivo e campo de aplica[cç][aã]o|campo de aplica[cç][aã]o|escopo e campo de aplica[cç][aã]o|escopo|objetivos?|objeto"
            r"|[aâ]mbito(?: de aplica[cç][aã]o)?|scope(?: and (?:field of )?application| and purpose| and applicability)?"
            r"|anwendungsbereich|geltungsbereich|fi\w{1,3}d of application|domaine d.application|purpose(?: and scope)?|general scope|application and scope|applicability")
T_DEF = (r"terms,? definitions,? (?:and )?(?:symbols|abbreviations)[^.]{0,40}|terms(?:,)? (?:and|&) definitions"
         r"|definitions(?: and (?:abbreviations|symbols|acronyms))?|termos,? defini[cç][oõ]es[^.]{0,40}|termos e defini[cç][oõ]es"
         r"|defini[cç][oõ]es(?: e (?:abreviaturas|siglas|s[ií]mbolos))?|gloss[aá]rio|glossary|begriffe(?: und [^.]{0,30})?"
         r"|terminology|terminologia(?: e defini[cç][oõ]es)?")
T_REF = (r"normative references?|refer[eê]ncias? normativas?|referenced documents|referenced standards|references|refer[eê]ncias"
         r"|normative verweisungen|documentos complementares|documentos de refer[eê]ncia"
         r"|reference documents|applicable documents|codes and standards|referenced publications|references? (?:and|&) standards")

RE_ESCOPO = re.compile(rf"^\s*{NUM}\s*(?:{T_ESCOPO})\s*[*:.—–-]?\s*(.*)$", re.I)
RE_DEF = re.compile(rf"^\s*{NUM}\s*(?:{T_DEF})\s*[*:.—–-]?\s*$", re.I)
RE_REF = re.compile(rf"^\s*{NUM}\s*(?:{T_REF})\s*[*:.—–-]?\s*$", re.I)
RE_COM_NUM = re.compile(r"^\s*(?:(?:section|se[cç][aã]o|article|part)\s+)?(?:[A-Z]{1,4}-)?(?:\d{1,2}(?:\.\d{1,2})?|[A-Z]\s?\d{3}|[A-H])[.)]?\s", re.I)
RE_NUM_1 = re.compile(r"^\s*(?:(?:section|se[cç][aã]o|article|part)\s+)?(?:[A-Z]{1,4}-)?(?:1|\d{1,2}\.1|I|A\s?\d00|\d00\.1)[.)]?(?:\s*[-–—])?\s", re.I)
# título numerado de nível 1 (fim de seção): "2 Normative references", "4. Ordering", "U-2 GENERAL"
RE_SECAO = re.compile(r"^\s*(?:[A-Z]{1,4}-)?(\d{1,2})\.?\s+([A-ZÀ-Ý][^\s.].{0,70})$")
RE_SECAO_SO_NUM = re.compile(r"^\s*(?:[A-Z]{1,4}-)?(\d{1,2})\.?\s*$")
RE_INICIO_FRASE = re.compile(r"^(?:\d+(?:\.\d+)*\s+)?(this|these|the |esta|este|estas|estes|a presente|o presente|diese|dieser|this part|"
                             r"o objetivo|a finalidade|the purpose|it |cette)", re.I)


def eh_sumario(linhas, forte=False):
    """Página de sumário: várias linhas com pontilhado; ou (forte=False) título Contents/Sumário + lista de títulos."""
    pont = sum(1 for l in linhas if re.search(r"(\.\s?){4,}\s*\d|…{2,}\s*\d", l))
    if pont >= 4:
        return True
    if forte:
        return False
    if any(re.fullmatch(r"(contents|sum[aá]rio|table of contents?|[ií]ndice|inhalt|inhaltsverzeichnis|sommaire)", l, re.I) for l in linhas[:15]):
        fim_num = sum(1 for l in linhas if re.search(r"\s\d{1,4}\s*$", l) or re.fullmatch(r"\s*\d{1,4}\s*", l))
        titulos = sum(1 for l in linhas if len(l) < 90 and (RE_SECAO.match(l) or re.match(r"^(anexo|annex|appendix|ap[eê]ndice)\b", l, re.I)))
        return fim_num >= 6 or pont >= 2 or titulos >= 5
    return False


def limpa_linhas(texto):
    out = []
    texto = re.sub(r"Este texto n[ãa]o substitui o publicado no D\.?O\.?U\.?", " ", texto)
    for l in texto.splitlines():
        l = l.replace(chr(0xa0), " ").replace("­", "").replace("\t", " ").replace("ﬁ", "fi").replace("ﬂ", "fl").strip()
        l = re.sub(r"\s{2,}", " ", l)
        l = re.sub(r"^[}{|\[\]]+\s*", "", l)  # lixo de OCR na margem ("} 1 Scope")
        if l:
            out.append(l)
    # nº de página isolado no topo/rodapé
    out = [l for i, l in enumerate(out) if not (re.fullmatch(r"\d{1,4}", l) and (i < 2 or i >= len(out) - 2))]
    # "1.1" / "3" numa linha e o título/termo na seguinte → "1.1 SCOPE"
    res = []
    i = 0
    while i < len(out):
        l = out[i]
        if re.fullmatch(r"(?:[A-Z]{1,3}-)?\d{1,2}(?:\.\d{1,3}){0,3}\.?", l) and i + 1 < len(out) and re.match(r"[A-Za-zÀ-ÿ]", out[i + 1]):
            res.append(l + " " + out[i + 1])
            i += 2
            continue
        res.append(l)
        i += 1
    return res


def junta(linhas):
    s = ""
    for l in linhas:
        if s.endswith("-") and len(s) > 1 and s[-2].isalpha() and l[:1].islower():
            s = s[:-1] + l
        else:
            s = (s + " " + l) if s else l
    return re.sub(r"\s+", " ", s).strip()


def corta(s, n):
    if len(s) <= n:
        return s
    c = s[:n]
    p = max(c.rfind(". "), c.rfind("; "))
    if p > n * 0.5:
        return c[: p + 1]
    return c[: c.rfind(" ")].rstrip(",;:") + " …"


def ruido(l):
    """Cabeçalho/rodapé/marca d'água/lixo de OCR: linhas a ignorar dentro do corpo."""
    ls = l.lower()
    tok = l.split()
    if len(tok) >= 5 and sum(len(t) == 1 for t in tok) >= 0.6 * len(tok):
        return True  # marca d'água "E e m p a r ..."
    nb = l.replace(" ", "")
    if nb and len(l) <= 40 and sum(c.isalnum() for c in nb) < 0.6 * len(nb):
        return True
    if len(l) <= 40 and re.fullmatch(r"(?:abnt |bs |din |una |)(?:en |iso |nbr |iec |)*(?:en |iso |nbr |iec |din |astm |api |asme )[\w./ -]{1,18}?\s?:\s?\d{4}(?:-\d\d)?(?: ?\([ef]\))?", ls):
        return True  # cabeçalho "EN ISO 4014:2000 (E)"
    return bool(
        re.fullmatch(r"[\divxlc\-–— ]{1,8}", ls)
        or re.search(r"copyright|licensed to|no reproduction|impresso por|exemplar para uso|document provided by|"
                     r"not for resale|uso exclusivo|reproduction or networking|downloaded|provided by ihs|ihs markit|"
                     r"licensee=|www\.|^page \d+|^p[aá]gina \d+|^abnt nbr [\d\-:]+$|^nbr [\d\-:]+$|^© |"
                     r"direitos reservados|all rights reserved|det norske veritas|dnv gl as|^dnv as$|\bedition (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}|edition .{3,60} page \d+|^\d+ / \d+$", ls)
    )


# ---------------------------------------------------------------- leitura
def abre(caminho):
    with open(os.path.join(RAIZ, caminho) if not os.path.isabs(caminho) else caminho, "rb") as f:
        return pymupdf.open(stream=f.read(), filetype="pdf")


def texto_pagina(pg, tp=None, colunas=False):
    """Texto da página; se houver calha vertical central (2 colunas), remonta coluna esquerda → direita."""
    kw = {"textpage": tp} if tp is not None else {}
    try:
        words = pg.get_text("words", **kw)
    except Exception:
        words = []
    w = pg.rect.width
    if colunas:  # OCR: descarta lixo nas margens laterais (carimbo/marca d'água vertical lido pelo Tesseract)
        words = [x for x in words if x[2] > 0.06 * w and x[0] < 0.94 * w]
    if colunas and len(words) > 60:
        corpo = [x for x in words if x[1] > pg.rect.height * 0.06 and x[3] < pg.rect.height * 0.95]
        # cobertura horizontal das palavras na faixa central
        melhor = None
        for g in range(int(w * 0.40), int(w * 0.60), 2):
            cruza = sum(1 for x in corpo if x[0] < g - 1 and x[2] > g + 1)
            if melhor is None or cruza < melhor[1]:
                melhor = (g, cruza)
        if melhor:
            g, cruza = melhor
            esq = sum(1 for x in corpo if x[2] <= g)
            dir_ = sum(1 for x in corpo if x[0] >= g)
            if cruza <= 0.03 * len(corpo) and esq > 0.25 * len(corpo) and dir_ > 0.25 * len(corpo):
                return _monta_colunas(words, g)
        return _monta_colunas(words, None)  # OCR: 1 coluna, mas linhas remontadas pela posição
    return pg.get_text("text", **kw)


def _monta_colunas(words, g):
    # linhas por proximidade vertical (no OCR cada palavra pode vir como "linha" própria)
    ws = sorted(words, key=lambda x: ((x[1] + x[3]) / 2, x[0]))
    grupos = []
    for x in ws:
        yc, h = (x[1] + x[3]) / 2, max(x[3] - x[1], 1)
        if grupos and abs(grupos[-1][0] - yc) < 0.45 * h:
            grupos[-1][1].append(x)
        else:
            grupos.append([yc, [x]])
    items = []
    for yc, gw in grupos:
        gw.sort(key=lambda x: x[0])
        if g is None:
            items.append((0, min(x[1] for x in gw), gw[0][0], " ".join(x[4] for x in gw)))
            continue
        esq = [x for x in gw if x[2] <= g + 1]
        dir_ = [x for x in gw if x[0] >= g - 1]
        meio = [x for x in gw if x not in esq and x not in dir_]
        y = min(x[1] for x in gw)
        # linha que atravessa a calha sem vão (título/parágrafo de largura total)
        if meio or (esq and dir_ and dir_[0][0] - esq[-1][2] < 9):
            items.append((2, y, gw[0][0], " ".join(x[4] for x in gw)))
            continue
        if esq:
            items.append((0, y, esq[0][0], " ".join(x[4] for x in esq)))
        if dir_:
            items.append((1, y, dir_[0][0], " ".join(x[4] for x in dir_)))
    # linhas que cruzam a calha (títulos) dividem a página em faixas; em cada faixa: esquerda, depois direita
    cortes = sorted(y for lado, y, _, _ in items if lado == 2)
    out = []
    faixas = [-1e9] + cortes + [1e9]
    for i in range(len(faixas) - 1):
        y0, y1 = faixas[i], faixas[i + 1]
        if i > 0:
            out += [t for lado, y, _, t in items if lado == 2 and y == y0][:1]
        for lado in (0, 1):
            seg = sorted((y, x, t) for l2, y, x, t in items if l2 == lado and y0 <= y < y1)
            out += [t for _, _, t in seg]
    return "\n".join(out)


def paginas_texto(doc, n, colunas=False):
    pags = []
    for i in range(min(n, len(doc))):
        try:
            pags.append(limpa_linhas(texto_pagina(doc[i], colunas=colunas)))
        except Exception:
            pags.append([])
    return pags


def qtd_texto(pags):
    return sum(len(" ".join(p)) for p in pags)


# ---------------------------------------------------------------- escopo
def acha_escopo(pags, pt=False):
    """1º título numerado 1/1.1 ("1 Escopo"); depois qualquer título (em norma ABNT, prefere o português)."""
    cands = []
    for numerado in (True, False):
        for ip, linhas in enumerate(pags[:MAX_PAG_DEF]):
            if eh_sumario(linhas, forte=True):
                continue
            for il, l in enumerate(linhas):
                if len(l) > 120 or re.search(r"(\.\s?){4,}", l):
                    continue
                m = RE_ESCOPO.match(l)
                if not m or (numerado and not RE_NUM_1.match(l)):
                    continue
                resto = m.group(1).strip()
                if resto and not RE_INICIO_FRASE.match(resto):
                    continue  # "Objetivo: Preservar…" num anexo, "Scope of work" etc.
                corpo = coleta(pags, ip, il + 1, resto, MAX_ESCOPO + 300)
                if re.search(r"\b(?:deste|neste|this|of this) (?:anexo|annex|appendix|ap[eê]ndice|section|chapter|se[cç][aã]o|cap[ií]tulo)\b", corpo[:120], re.I):
                    continue  # escopo de um anexo, não da norma
                if len(corpo) >= 40 and not re.match(r"^(\.|…|\d+$)", corpo):
                    corpo = re.sub(r"^[1-9]0[1-9]\s+", "", corpo)  # DNV antigo: "401 The standard covers…"
                    if len(re.findall(r"(?:^|\s)\d{1,2}(?:\.\d{1,2})+\s+[A-ZÀ-Ý]", corpo[:300])) >= 2 and corpo[:300].count(". ") < 1:
                        continue  # lista de títulos (sumário sem pontilhado)
                    cands.append((corta(corpo, MAX_ESCOPO), ip + 1, l))
            if numerado and cands:
                break
        if cands:
            break
    if not cands:
        return None, None
    if pt:
        for c in cands:
            if re.search(r"escopo|objetivo|objeto|campo|[aâ]mbito", c[2], re.I):
                return c[0], c[1]
    return cands[0][0], cands[0][1]


def coleta(pags, ip, il, inicial, limite):
    """Junta linhas a partir de (ip, il) até o próximo título de seção de nível 1 (subitens 1.x continuam)."""
    out = [inicial] if inicial else []
    tam = len(inicial)
    p0 = ip
    while ip < len(pags) and ip <= p0 + 2:
        for l in pags[ip][il:]:
            if ruido(l):
                continue
            mn = RE_SECAO_SO_NUM.match(l)
            if mn and int(mn.group(1)) >= 2:
                return junta(out)
            m = RE_SECAO.match(l)
            if m and len(m.group(2)) < 70 and not m.group(2).rstrip().endswith((",", ";")) and int(m.group(1)) != 1:
                return junta(out)
            if RE_DEF.match(l) or RE_REF.match(l) or (out and RE_ESCOPO.match(l) and len(l) < 40):
                return junta(out)
            if re.match(r"^(note|nota|notes|notas|anmerkung)\b", l, re.I) and tam > 200:
                return junta(out)
            out.append(l)
            tam += len(l)
            if tam > limite:
                return junta(out)
        ip += 1
        il = 0
    return junta(out)


def secoes(pags, regex, n_pag):
    """Candidatos (página, linha) a título de seção, na ordem de preferência: numerados ("3 Termos e definições")
    e depois os demais. Quem chama usa o 1º que render conteúdo (o do sumário rende vazio)."""
    vistos = set()
    for numerado in (True, False):
        for ip, linhas in enumerate(pags[:n_pag]):
            if eh_sumario(linhas, forte=True):
                continue
            for il, l in enumerate(linhas):
                if numerado and not RE_COM_NUM.match(l):
                    continue
                if len(l) < 70 and regex.match(l) and not re.search(r"(\.\s?){4,}", l) and (ip, il) not in vistos:
                    vistos.add((ip, il))
                    yield ip, il


def coleta_secao(pags, ip, il, limite, max_pag=4):
    """Linhas da seção até o próximo título de seção de nível 1."""
    out = []
    tam = 0
    p0 = ip
    while ip < len(pags) and ip <= p0 + max_pag:
        for l in pags[ip][il:]:
            if ruido(l):
                continue
            mn = RE_SECAO_SO_NUM.match(l)
            if mn and out and int(mn.group(1)) >= 2:
                return out
            m = RE_SECAO.match(l)
            if m and out and len(m.group(2)) < 60 and not RE_COD.match(m.group(2)) and not re.match(r"^[A-Z]{1,3}\s?\d", m.group(2)):
                return out
            if out and (RE_DEF.match(l) or (RE_ESCOPO.match(l) and len(l) < 40)):
                return out
            out.append((l, ip + 1))
            tam += len(l)
            if tam > limite:
                return out
        ip += 1
        il = 0
    return out


# ---------------------------------------------------------------- referências normativas
RE_COD = re.compile(
    r"\b(?:ABNT\s+NBR\s+(?:ISO\s+|IEC\s+|NM\s+)?|NBR\s+(?:ISO\s+|IEC\s+|NM\s+)?|ISO/IEC\s+|ISO/TS\s+|ISO/TR\s+|IEC\s+|EN\s+ISO\s+|DIN\s+EN\s+(?:ISO\s+)?|"
    r"DIN\s+(?:ISO\s+)?|BS\s+EN\s+(?:ISO\s+)?|BS\s+|EN\s+|ISO\s+|ASME\s+(?:B|Y|PTC|BPVC|PCC|STS|BTH|NM|NQA)?\s*|ANSI/ASME\s+|ANSI\s+|"
    r"ASTM\s+|API\s+(?:RP\s+|Spec\s+|Std\s+|TR\s+|MPMS\s+|Publ\.?\s+|Bull\s+)?|AWS\s+|MSS\s+SP-?|AISC\s+|NACE\s+(?:MR|TM|SP|RP)?\s*|SSPC[- ](?:SP|PA)?\s*|"
    r"DNV(?:\s?GL)?[- ](?:OS|ST|RP|CG|RU|SE|OSS)[- ]|NORSOK\s+|IEEE\s+|NFPA\s+|NR[- ]|SAE\s+|AGMA\s+|ISA[- ]|IACS\s+|EEMUA\s+|CEN/TS\s+)"
    r"[A-Z]{0,3}[\s-]?\d[\d.]*(?:[-–/.][A-Z]?\d+[A-Z]?)*(?:/[A-Z]\s?\d+M?)?",
)
# lista ASTM/ASME sem prefixo:  "ASTM Standards:" seguido de "A 153/A 153M Specification for…"
RE_CTX = re.compile(r"^(?:\d{1,2}(?:\.\d{1,2})*\.?\s+)?(ASTM|ASME|ANSI|API|AWS|ISO|MSS|SAE|AISC|NACE|SSPC|ABNT|DIN|BS|AMS|IEC|Federal|Military)\b[^:]{0,40}(?:Standards?|Documents?|Specifications?|Codes?|Publications?)?:?\s*$")
RE_NU = re.compile(r"^([A-H]\s?\d{1,4}(?:\.\d+)?(?:/[A-H]\s?\d{1,4}M?)?|[A-Z]\d{1,3}\.\d+[A-Z]?(?:\.\d+)*M?|SA-\d+|SB-\d+|SFA-\d\.\d+)\b")


def normaliza_cod(c):
    return re.sub(r"[^A-Z0-9]", "", c.upper().replace("DNVGL", "DNV").replace("ABNTNBR", "NBR"))


def acha_referencias(pags, nid):
    for n, (ip, il) in enumerate(secoes(pags, RE_REF, MAX_PAG)):
        refs = _refs_em(pags, ip, il, nid)
        if refs:
            return refs, ip + 1
        if n > 8:
            break
    return [], None


def _refs_em(pags, ip, il, nid):
    linhas = coleta_secao(pags, ip, il + 1, 8000)
    proprio = normaliza_cod(nid.replace("-", " "))
    refs, vistos = [], set()

    def add(c):
        c = re.sub(r"\s+", " ", c).strip().rstrip(".,;:-–").replace("–", "-")
        if not re.search(r"\d", c) or len(c) < 4:
            return
        k = normaliza_cod(c)
        if k == proprio or k in vistos:
            return
        vistos.add(k)
        refs.append(c)

    ctx = None
    for l, _ in linhas:
        mc = RE_CTX.match(l)
        if mc:
            ctx = mc.group(1)
            continue
        mn = RE_NU.match(l)
        if ctx and mn and not RE_COD.match(l):
            add(f"{ctx} {mn.group(1)}")
        for m in RE_COD.finditer(l):
            add(m.group(0))
        if len(refs) >= N_REF:
            break
    return refs[:N_REF]


# ---------------------------------------------------------------- definições
RE_ITEM = re.compile(r"^(?:[A-Z]{1,3}-?)?([1-9]\d?(?:\.\d{1,3}){1,3})\.?(?:\s+(\D.*))?$")
RE_DP = re.compile(r"^([A-Za-zÀ-ÿ][^:;.]{1,60}?)\s*(?::|—|–|\s-)\s+(\S.{3,})$")
# "Activation Distance. The distance…" / "*alloy flux. A flux…" (ANSI, AWS)
RE_DP2 = re.compile(r"^\*?([A-Za-zÀ-ÿ][\w\-()/ ,’'&]{1,55}?)\.\s+([A-ZÀ-Ý].{3,})$")
RE_TERMO_RUIM = re.compile(r"^(table|tabela|tab\.|figure|figura|note|nota|see |ver |the |a |an |o |os |as |in |for |if |where |when |"
                           r"[ivx]+\s*[-–)]|\d|[a-z]\)|recommended practice|page |verbal forms|terms$|termos$|.$|..$|esta |este |this |these |it |"
                           r"discussion|example|exemplo|guidance|anexo|annex|appendix|ap[eê]ndice|definitions?\b|defini[cç][oõ]es\b|terms\b|termos\b|[A-Z]{1,5}\s?\d)", re.I)


def defs_tabela(doc, ip, n_pag=10):
    """Definições em tabela "Term | Definition" (DNV, ABS…): termo = linha na coluna da esquerda (pela posição x)."""
    out = []
    xt = xd = None
    atual = None
    for p in range(ip, min(ip + n_pag, len(doc))):
        try:
            d = doc[p].get_text("dict")
        except Exception:
            break
        linhas = []
        for b in d["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"]).replace("\xa0", " ").strip()
                if t:
                    linhas.append((round(ln["bbox"][1], 1), ln["bbox"][0], t))
        linhas.sort()
        for i, (y, x, t) in enumerate(linhas):
            if re.fullmatch(r"(term|termo)s?", t, re.I):
                prox = [u for u in linhas[i + 1:i + 3] if re.fullmatch(r"definition|description|defini[cç][aã]o|descri[cç][aã]o", u[2], re.I)]
                if prox:
                    # cabeçalhos centrados: colunas reais pelos x0 das linhas seguintes (termo = menor x, definição = x mais comum à direita)
                    xs = [round(u[1]) for u in linhas[i + 2:i + 40] if not ruido(u[2])]
                    if xs:
                        xt = min(xs)
                        dir_ = [v for v in xs if v > xt + 25]
                        xd = max(set(dir_), key=dir_.count) if dir_ else prox[0][1]
                    else:
                        xt, xd = x, prox[0][1]
                    atual = None
                continue
            if xt is None or ruido(t) or re.fullmatch(r"definition|description|defini[cç][aã]o", t, re.I):
                continue
            if re.match(r"^(table|tabela)\s+\d", t, re.I):
                atual = None
                if out and not re.search(r"defini|terms|abbreviat|symbol|verbal", t, re.I):
                    return out
                continue
            if (RE_SECAO.match(t) or re.match(r"^\d+(\.\d+)+\s+[A-Z]", t)) and len(t) < 70:
                if re.search(r"term|defini|abbreviat|symbol|verbal|acronym", t, re.I):
                    atual = None
                    continue
                if out:
                    return out
                xt = None
                continue
            if x < (xt + xd) / 2:
                atual = {"termo": t, "texto": [], "pagina": p + 1, "ok": True}
                out.append(atual)
            elif atual is not None:
                if atual["texto"] and atual["pagina"] != p + 1 and False:
                    pass
                atual["texto"].append(t)
    return out


def acha_definicoes(pags, doc=None):
    for n, (ip, il) in enumerate(secoes(pags, RE_DEF, MAX_PAG_DEF)):
        defs = _defs_em(pags, doc, ip, il)
        if defs:
            return defs
        if n > 8:
            break
    return []


def _defs_em(pags, doc, ip, il):
    # tabela "Term / Definition" logo após o título
    prox = (pags[ip][il + 1:il + 30] + (pags[ip + 1][:20] if ip + 1 < len(pags) else []))[:40]
    if doc is not None and any(re.fullmatch(r"(term|termo)s?", l, re.I) for l in prox) and \
            any(re.fullmatch(r"definition|description|defini[cç][aã]o|descri[cç][aã]o", l, re.I) for l in prox):
        return _filtra_defs(defs_tabela(doc, ip))
    defs = []
    atual = None
    nivel_sec = None
    p, i0 = ip, il + 1
    fim = False
    while not fim and p < len(pags) and p <= ip + 12 and len(defs) < N_DEF + 20:
        for l in pags[p][i0:]:
            if ruido(l):
                continue
            ms = RE_SECAO.match(l)
            mi = RE_ITEM.match(l)
            if (ms and not mi and len(ms.group(2)) < 60 and not RE_DP.match(l)) or (RE_SECAO_SO_NUM.match(l) and defs) or RE_REF.match(l):
                fim = True
                break
            mdp = RE_DP.match(l)
            if not mdp and not mi and nivel_sec is None:
                m2 = RE_DP2.match(l)
                if m2 and len(m2.group(1).split()) <= 6 and (atual is None or re.search(r"[.;)]$", (atual["texto"] or [""])[-1])):
                    atual = {"termo": m2.group(1).strip(), "texto": [m2.group(2)], "pagina": p + 1, "ok": True}
                    defs.append(atual)
                    continue
            if mi:
                num, resto = mi.group(1), mi.group(2) or ""
                top = num.split(".")[0]
                if nivel_sec is None:
                    nivel_sec = top
                elif top != nivel_sec:
                    fim = True
                    break
                atual = {"termo": resto.strip(), "texto": [], "pagina": p + 1, "ok": True}
                mt = re.match(r"^(.{2,60}?)(?:\s*(?::|–)\s+|\s*—\s*)(.+)$", atual["termo"])
                if mt:
                    atual["termo"], t = mt.groups()
                    atual["texto"].append(t)
                elif len(resto) > 60:
                    atual["ok"] = False  # frase, não termo (ex. "3.2 The bending stress number…")
                defs.append(atual)
            elif mdp and (atual is None or not atual.get("num_style")) and \
                    (atual is None or not atual["texto"] or re.search(r"[.;:)]$", atual["texto"][-1].rstrip()) or mdp.group(1)[0].isupper()):
                if mdp.group(1)[0].islower() and atual is not None and atual["texto"] and not re.search(r"[.;)]$", atual["texto"][-1]):
                    atual["texto"].append(l)
                    continue
                atual = {"termo": mdp.group(1).strip(), "texto": [mdp.group(2)], "pagina": p + 1, "ok": True}
                defs.append(atual)
            elif atual is not None:
                if not atual["termo"] and not atual["texto"]:
                    atual["termo"] = l
                else:
                    atual["texto"].append(l)
        p += 1
        i0 = 0
    return _filtra_defs(defs)


def _filtra_defs(defs):
    out = []
    for d in defs:
        termo = d["termo"].strip(" :—–-")
        texto = re.split(r"\s(?:NOTE|NOTA|Note|Nota|EXAMPLE|EXEMPLO)\s?\d*\b", junta(d["texto"]))[0].strip()
        if not d["ok"] or not termo or not texto or len(termo) > 80 or len(texto) < 8:
            continue
        if RE_TERMO_RUIM.match(termo) or re.search(r"(\.\s?){4,}", termo + texto) or termo.endswith("-") or                 re.search(r"\b(and|or|of|the|as|to|in|a|an|for|with|by|e|ou|de|da|do|em|para|und|der)$", termo, re.I) or                 re.search(r"table of contents|sum[aá]rio", texto, re.I) or len(termo.split()) > 6 or                 re.match(r"(section|chapter|se[cç][aã]o|cap[ií]tulo)\s+\d", texto, re.I) or                 (len(texto) < 80 and RE_COD.search(texto)) or re.search(r"\d+(\.\d+)+\s*$", texto):
            continue
        out.append({"termo": termo, "texto": corta(texto, MAX_DEF), "pagina": d["pagina"]})
        if len(out) >= N_DEF:
            break
    return out if len(out) >= 1 else []


# ---------------------------------------------------------------- substitui
RE_SUBST = re.compile(
    r"((?:\b(?:Esta|Este|This|These|It|A presente|O presente|Diese)\b[^.]{0,160}?\b(?:cancela|substitui|supersedes?|cancels|replaces|ersetzt)"
    r"|\b(?:Supersedes|Ersetzt|Replaces|Cancela e substitui)\b)[^.]{3,200}?(?:\.(?!\d)|$))")


def acha_substitui(pags):
    for linhas in pags[:8]:
        txt = junta(l for l in linhas if not ruido(l))
        for m in RE_SUBST.finditer(txt):
            s = m.group(1).strip()
            if re.search(r"n[aã]o substitui o publicado|until superseded|may be superseded", s, re.I):  # aviso das NRs ("Este texto não substitui o publicado no DOU")
                continue
            if len(s) > 15:
                s = re.split(r"\s(?:Esta Norma (?:é|e) |Document comprises|In case of doubt|Normas T[eé]cnicas|Palavras-chave|V[aá]lida a partir)", s)[0].strip()
                return corta(s, 300)
    return None


# ---------------------------------------------------------------- por norma
def processa(args):
    nid, arquivo, ocr = args
    res = {"paginas": 0}
    try:
        doc = abre(arquivo)
        res["paginas"] = len(doc)
        pags = paginas_texto(doc, MAX_PAG_DEF, colunas=arquivo.startswith("referencias/ocr/"))
        fonte = None
        if ocr and qtd_texto(pags[:15]) < 60 * min(len(pags), 15):
            try:
                p2 = paginas_texto(abre(ocr), MAX_PAG_DEF, colunas=True)
                if qtd_texto(p2) > qtd_texto(pags) * 1.5:
                    pags, fonte = p2, "ocr"
            except Exception:
                pass
        if fonte is None and qtd_texto(pags[:10]) < 500:
            # escaneado sem cópia OCR: OCR em memória só das primeiras páginas (mesma numeração física)
            idioma = "por" if re.search(r"NBR|ABNT|/NR", arquivo) else "eng"
            p2 = []
            for i in range(min(N_OCR, len(doc))):
                try:
                    pg = doc[i]
                    tp = pg.get_textpage_ocr(language=idioma, dpi=200, full=True, tessdata=TESSDATA)
                    p2.append(limpa_linhas(texto_pagina(pg, tp, colunas=True)))
                except Exception:
                    p2.append([])
            if qtd_texto(p2) > qtd_texto(pags):
                pags, fonte = p2, "ocr"
        pt = bool(re.search(r"NBR|ABNT|/NR[- ]|Regulamentadora", arquivo))
        esc, pe = acha_escopo(pags, pt)
        if esc:
            res["escopo"], res["pagina_escopo"] = esc, pe
        defs = acha_definicoes(pags, doc if fonte is None else None)
        if defs:
            res["definicoes"] = defs
        refs, pr = acha_referencias(pags, nid)
        if refs:
            res["referencias_normativas"] = refs
            res["pagina_referencias"] = pr
        s = acha_substitui(pags)
        if s:
            res["substitui"] = s
        if fonte or arquivo.startswith("referencias/ocr/"):
            res["fonte"] = "ocr"
    except Exception as e:  # noqa
        res["erro"] = f"{type(e).__name__}: {e}"[:200]
    return nid, res


def orgao(n):
    o = (n.get("orgao") or "").split()[0].strip("(),")
    return {"MTE": "NR", "Ministério": "NR"}.get(o, o)


def main():
    normas = json.load(open(os.path.join(RAIZ, "conteudo", "normas.json"), encoding="utf-8"))
    origem = json.load(open(os.path.join(RAIZ, "referencias", "ocr", "_origem.json"), encoding="utf-8"))
    ocr_de = {a.replace("\\", "/"): o for o, a in origem.items()}
    so = sys.argv[1:]
    tarefas = [(n["id"], n["arquivo"], ocr_de.get(n["arquivo"].replace("\\", "/")))
               for n in normas if not so or n["id"] in so]
    with mp.Pool(procs(400)) as pool:  # no máximo 1/6 da RAM livre (ferramentas/recursos.py)
        resultados = dict(pool.imap_unordered(processa, tarefas, chunksize=1))
    if so:
        for nid in so:
            print(json.dumps({nid: resultados.get(nid)}, ensure_ascii=False, indent=1))
        return
    info = {n["id"]: resultados[n["id"]] for n in normas if n["id"] in resultados}
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, separators=(",", ":"))
    est = defaultdict(lambda: [0, 0, 0, 0])
    for n in normas:
        r = info.get(n["id"], {})
        e = est[orgao(n)]
        e[0] += 1
        e[1] += bool(r.get("escopo"))
        e[2] += bool(r.get("definicoes"))
        e[3] += bool(r.get("referencias_normativas"))
    tot = [sum(v[i] for v in est.values()) for i in range(4)]
    print(f"{'órgão':12} {'n':>4} {'escopo':>7} {'defin.':>7} {'refs':>5}")
    for k, v in sorted(est.items(), key=lambda kv: -kv[1][0]):
        print(f"{k[:12]:12} {v[0]:4} {v[1]:7} {v[2]:7} {v[3]:5}")
    print(f"{'TOTAL':12} {tot[0]:4} {tot[1]:7} {tot[2]:7} {tot[3]:5}")
    print("definições:", sum(len(r.get("definicoes", [])) for r in info.values()),
          " referências:", sum(len(r.get("referencias_normativas", [])) for r in info.values()),
          " substitui:", sum(1 for r in info.values() if r.get("substitui")),
          " OCR:", sum(1 for r in info.values() if r.get("fonte")),
          " erros:", sum(1 for r in info.values() if "erro" in r))
    print(f"{SAIDA}: {os.path.getsize(SAIDA) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
