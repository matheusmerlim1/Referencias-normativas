"""Configuração da ficha-fonte de recortes (tabelas/figuras) das normas usadas SÓ nas fichas temáticas — lido por gerar_docs.py.

Essas normas (NRs, ASME B16.5/B31.3, AWS D1.1, ISO 898-1…) têm valores transcritos nas fichas temáticas mas não passavam pelo
recortador; aqui ganham os recortes, como as demais. Dados (arquivo, título, edição, órgão) vêm de conteudo/normas.json.
Fora: ASME-II-D-2019 (1262 págs.; as tabelas já estão transcritas em materiais-asme-ii-d / propriedades-fisicas-asme-ii-d).
"""
import json
import os

IDS = """ABS-ERGO ANSI-Z359.14 API-9A API-RP-14E API-RP-2A API-RP-8B ASME-B16.20 ASME-B16.21 ASME-B16.25 ASME-B16.47 ASME-B16.5
ASME-B18.2.6 ASME-B30.10 ASME-B30.20 ASME-B30.26 ASME-B30.7 ASME-B31.3 ASME-B36.10M ASME-VIII-1-APP-S ASME-VIII-1-UCS ASME-VIII-1-UG
ASME-VIII-1-UW ASTM-F1166 AWS-D1.1 DIN-1025-1 DIN-1025-2 DIN-1025-3 DNV-OS-C101 DNV-OS-H205 DNV-ST-E271 DNV-ST-E273 EN-10034
EQN-PE-FD-00-S-SP-00001 EQN-VERTICAL-LADDER GUIA-PADEYE-TP2016 IMCA-M179 ISO-13920 ISO-14122-2 ISO-14122-3 ISO-16047 ISO-3266
ISO-3506-1 ISO-4017 ISO-4032 ISO-4033 ISO-7089 ISO-7091 ISO-7093-1 ISO-898-1 ISO-898-2 ISO-9013 NBR-11900-2 NBR-11900-4 NBR-13541-1
NBR-13541-2 NBR-13543 NBR-14628 NBR-14718 NBR-15516-1 NBR-15516-2 NBR-15637-1 NBR-15708-2 NBR-15708-3 NBR-16325-2 NBR-6158 NBR-6327
NBR-7007 NBR-ISO-2768-1 NBR-ISO-2768-2 NORSOK-L-005 NORSOK-R-002 NR-12 NR-13-PR NR-13 NR-17 NR-18 NR-34 NR-35 NR-37""".split()

# o recortador usa o órgão-base (ASME/ABNT/DIN mudam a regra de "norma curta")
BASE = {"ABNT": "ABNT", "DIN": "DIN", "ASME": "ASME"}

_N = {n["id"]: n for n in json.load(open(os.path.join(os.path.dirname(__file__), "..", "conteudo", "normas.json"), encoding="utf-8"))}


def _doc(i):
    n = _N[i]
    o = (n.get("orgao") or "").split(" ")[0]
    return {"id": i, "arq": n["arquivo"], "titulo": n["titulo"], "edicao": n.get("edicao", ""), "escopo": n.get("escopo", ""),
            "orgao": BASE.get(o, o), "sem_paginas_inteiras": i in SO_TEXTO}


# só texto: as caixas em volta das alterações (NR-35) e as faixas cinza das perguntas (NR-13-PR) viravam "página inteira"
SO_TEXTO = {"NR-35", "NR-13-PR"}

EXCLUIDOS = {}

FICHAS = [
    {"id": "recortes-normas-tematicas", "titulo": "Tabelas e figuras das normas das fichas temáticas",
     "categoria": "Normas das fichas temáticas", "agrupar": "documento",
     "resumo": "Recortes (imagem) das tabelas e figuras das normas cujos valores estão transcritos nas fichas temáticas.",
     "docs": [_doc(i) for i in IDS if i in _N]},
]
