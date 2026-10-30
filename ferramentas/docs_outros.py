"""Configuração das fichas de "tabelas e figuras" dos documentos de referencias/ de órgãos diversos (NR, BS, ASTM, ISA, AGMA, AWS,
MSS, AISC, AISI, ANSI/ASME, AMPLA, DNIT, EEMUA, AS/NZS) — lido por ferramentas/gerar_docs.py.

Mesmo formato de FICHAS em gerar_docs.py. Documentos escaneados usam a cópia OCR de referencias/ocr/ (mesmas páginas).
Códigos/edições conferidos na 1ª página de cada PDF (OCR da 1ª página nos escaneados). Títulos em português para NR, AMPLA e DNIT;
em inglês nos demais, como no documento, com descrição em português entre parênteses.
API, DNV, ABS, BV, IACS e IOGP ficam em docs_offshore.py. Duplicatas e edições superadas ficam fora, em EXCLUIDOS.
"""

E = "referencias/extraido"
OCR = "referencias/ocr"


def doc(id_, arq, titulo, edicao, escopo="", orgao=""):
    return {"id": id_, "arq": arq, "titulo": titulo, "edicao": edicao, "escopo": escopo, "orgao": orgao}


def nr(id_, arq, titulo, edicao):
    return doc(id_, f"{E}/NR/{arq}", titulo, edicao, orgao="NR")


EXCLUIDOS = {
    f"{E}/NR/NR-11 Anexo I - Transporte de Chapas de Rochas Ornamentais.pdf":
        "duplicata: o Anexo I da NR-11 (chapas de rochas ornamentais, redação da Portaria MTPS 505/2016) já está completo nas págs. 4–14 "
        "do arquivo principal 'NR-11 - Transporte, Movimentacao…', usado nesta mesma ficha",
    f"{E}/NR/NR-15 Anexo 3 - Limites de Tolerancia para Exposicao ao Calor.pdf":
        "duplicata: o Anexo 3 da NR-15 (calor, redação da Portaria SEPRT 1.359/2019) já está no arquivo principal "
        "'NR-15 - Atividades e Operacoes Insalubres' (págs. 4–6, mesma redação), usado nesta mesma ficha",
    f"{E}/BS/BS 3506-1 1998.pdf":
        "edição superada: BS EN ISO 3506-1:1998 (= ISO 3506-1:1997); a ISO 3506-1:2009 já está em normas.json (id ISO-3506-1)",
    f"{E}/BS/bs-iso-3601-12008.pdf":
        "edição superada: BS ISO 3601-1:2008 (com corrigendum ago/2008); a ISO 3601-1:2012 (5ª ed.) já está em normas.json (id ISO-3601-1)",
    f"{E}/AWS/AWS A2.4 2020 - Standard Symbols for Welding, Brazing, and Nondestructive Examination (3).pdf":
        "duplicata: mesma AWS A2.4:2020 (8ª ed., 166 págs.); usada a cópia OCR de 'AWS A2.4 2020 - … (2).pdf' (referencias/ocr/AWS-A2.4-2020.pdf)",
    f"{E}/AWS/AWS A2.4 2020 - Standard symbols for welding, brazing, and nondestructive examination.pdf":
        "duplicata: mesma AWS A2.4:2020 (8ª ed., 166 págs.); usada a cópia OCR de 'AWS A2.4 2020 - … (2).pdf' (referencias/ocr/AWS-A2.4-2020.pdf)",
    f"{E}/AS-NZS/AS-NZS 60079.10.1 2009 - Explosive Atmospheres - Part 10.1 Classification of Areas - Explosive Gas Atmospheres - SAMPLE.pdf":
        "documento incompleto: amostra gratuita da AS/NZS 60079.10.1:2009 (8 págs.: capa, prefácio, sumário, introdução e só a 1ª página do "
        "texto) — sem tabelas nem figuras; a classificação de áreas está coberta pela ABNT NBR IEC 60079-10 (normas.json, id NBR-IEC-60079-10)",
}


FICHAS = [
    {"id": "nr-gestao-insalubridade-conforto", "titulo": "NRs — gerenciamento de riscos, insalubridade, periculosidade, conforto e sinalização",
     "categoria": "Segurança do trabalho", "agrupar": "documento",
     "resumo": "Quadros, tabelas e anexos das Normas Regulamentadoras NR-01 (disposições gerais e GRO/PGR), NR-09 (exposições a agentes "
               "físicos, químicos e biológicos), NR-15 (atividades insalubres: ruído, calor, limites de tolerância de agentes químicos, poeiras), "
               "NR-16 (atividades perigosas), NR-21 (trabalho a céu aberto), NR-24 (condições sanitárias e de conforto), NR-25 (resíduos) "
               "e NR-26 (sinalização de segurança).",
     "docs": [
         nr("NR-01", "NR-01-atualizada-2020.pdf", "NR-01 — Disposições gerais e gerenciamento de riscos ocupacionais",
            "Redação da Portaria SEPRT 6.730, de 09/03/2020"),
         nr("NR-09", "NR-09-atualizada-2020.pdf", "NR-09 — Avaliação e controle das exposições ocupacionais a agentes físicos, químicos e biológicos",
            "Redação da Portaria SEPRT 6.735, de 10/03/2020"),
         nr("NR-15", "NR-15 - Atividades e Operacoes Insalubres.pdf", "NR-15 — Atividades e operações insalubres (texto e Anexos 1 a 14, "
            "incl. Anexo 3 calor na redação de 2019)", "Última alteração no arquivo: Portaria SEPRT 1.359, de 09/12/2019"),
         nr("NR-16", "NR-16-atualizada-2019.pdf", "NR-16 — Atividades e operações perigosas (com anexos)",
            "Última alteração no arquivo: Portaria SEPRT 1.357, de 09/12/2019"),
         nr("NR-21", "NR-21 - Trabalhos a Ceu Aberto.pdf", "NR-21 — Trabalhos a céu aberto", "Última alteração: Portaria MTE 2.037, de 15/12/1999"),
         nr("NR-24", "NR-24-atualizada-2019.pdf", "NR-24 — Condições sanitárias e de conforto nos locais de trabalho",
            "Redação da Portaria SEPRT 1.066, de 23/09/2019"),
         nr("NR-25", "NR-25 - Residuos Industriais.pdf", "NR-25 — Resíduos industriais", "Última alteração: Portaria SIT 253, de 04/08/2011"),
         nr("NR-26", "NR-26 - Sinalizacao de Seguranca.pdf", "NR-26 — Sinalização de segurança", "Última alteração: Portaria MTE 704, de 28/05/2015"),
     ]},

    {"id": "nr-eletricidade-inflamaveis-espacos", "titulo": "NRs — eletricidade, movimentação de materiais, fornos, explosivos, inflamáveis, incêndio e espaço confinado",
     "categoria": "Segurança do trabalho", "agrupar": "documento",
     "resumo": "Quadros, tabelas, figuras e anexos das Normas Regulamentadoras NR-10 (instalações e serviços em eletricidade: zonas de risco "
               "e controlada), NR-11 (transporte, movimentação e armazenagem de materiais, com Anexo I de chapas de rochas ornamentais), "
               "NR-14 (fornos), NR-19 (explosivos), NR-20 (inflamáveis e combustíveis), NR-23 (proteção contra incêndios) "
               "e NR-33 (espaços confinados).",
     "docs": [
         nr("NR-10", "NR-10 - Seguranca em Instalacoes e Servicos em Eletricidade.pdf",
            "NR-10 — Segurança em instalações e serviços em eletricidade", "Redação da Portaria MTE 598/2004 com alteração da Portaria SEPRT 915, de 30/07/2019"),
         nr("NR-11", "NR-11 - Transporte, Movimentacao, Armazenagem e Manuseio de Materiais.pdf",
            "NR-11 — Transporte, movimentação, armazenagem e manuseio de materiais (inclui o Anexo I — chapas de rochas ornamentais)",
            "Última alteração: Portaria MTPS 505, de 29/04/2016"),
         nr("NR-14", "NR-14 - Fornos.pdf", "NR-14 — Fornos", "Redação da Portaria SSMT 12, de 06/06/1983"),
         nr("NR-19", "NR-19 - Explosivos.pdf", "NR-19 — Explosivos (com anexos)", "Redação da Portaria SIT 228, de 24/05/2011"),
         nr("NR-20", "NR-20 - Seguranca e Saude no Trabalho com Inflamaveis e Combustiveis.pdf",
            "NR-20 — Segurança e saúde no trabalho com inflamáveis e combustíveis (com anexos)",
            "Última alteração no arquivo: Portaria SEPRT 1.360, de 09/12/2019"),
         nr("NR-23", "NR-23 - Protecao Contra Incendios.pdf", "NR-23 — Proteção contra incêndios", "Redação da Portaria SIT 221, de 06/05/2011"),
         nr("NR-33", "nr-33-atualizada-2022-_retificada.pdf", "NR-33 — Segurança e saúde nos trabalhos em espaços confinados (texto retificado)",
            "Redação da Portaria MTP 1.690, de 15/06/2022 (em vigor 03/10/2022)"),
     ]},

    {"id": "astm-ensaios-materiais", "titulo": "ASTM — ensaios mecânicos, de corrosão, de plásticos e de aderência; forjados A694",
     "categoria": "Ensaios e inspeção", "agrupar": "documento",
     "resumo": "Tabelas e figuras de normas ASTM de ensaio: tração de metais (E8M), verificação de força de máquinas de ensaio (E4), "
               "pite e fresta em inox com cloreto férrico (G48), tração de plásticos (D638), condicionamento de plásticos (D618), "
               "contração de moldagem (D955), índice de fluidez (D1238), aderência pull-off de revestimentos (D4541), "
               "tubos e barras de PRFV para ferramentas de linha viva (F711) e forjados para flanges de alta pressão (A694/A694M).",
     "docs": [
         doc("ASTM-E8M", f"{OCR}/ASTM-E8M.pdf", "ASTM E8M-04 — Standard Test Methods for Tension Testing of Metallic Materials [Metric] "
             "(ensaio de tração de materiais metálicos; cópia OCR)", "2004", orgao="ASTM"),
         doc("ASTM-E4", f"{OCR}/ASTM-E4-2003.pdf", "ASTM E4-03 — Standard Practices for Force Verification of Testing Machines "
             "(verificação/calibração de força de máquinas de ensaio; cópia OCR)", "2003", orgao="ASTM"),
         doc("ASTM-G48", f"{OCR}/ASTM-G48-1999.pdf", "ASTM G48-99 — Standard Test Methods for Pitting and Crevice Corrosion Resistance of Stainless Steels "
             "and Related Alloys by Use of Ferric Chloride Solution (corrosão por pite e fresta; cópia OCR)", "1999", orgao="ASTM"),
         doc("ASTM-D638", f"{E}/ASTM/170915687-ASTM-D638-02a.pdf", "ASTM D638-02a — Standard Test Method for Tensile Properties of Plastics "
             "(tração de plásticos, corpos de prova tipo I–V)", "2002 (D638-02a)", orgao="ASTM"),
         doc("ASTM-D618", f"{OCR}/ASTM-D618.pdf", "ASTM D618-13 — Standard Practice for Conditioning Plastics for Testing "
             "(condicionamento de plásticos para ensaio; cópia OCR)", "2013", orgao="ASTM"),
         doc("ASTM-D955", f"{E}/ASTM/ASTM D955 00 - Standard test method of measuring shrinkage from mold dimensions of thermoplastics.pdf",
             "ASTM D955-00 — Standard Test Method of Measuring Shrinkage from Mold Dimensions of Thermoplastics (contração de moldagem)", "2000", orgao="ASTM"),
         doc("ASTM-D1238", f"{E}/ASTM/102333991-d1238.pdf", "ASTM D1238-04c — Standard Test Method for Melt Flow Rates of Thermoplastics by Extrusion Plastometer "
             "(índice de fluidez/MFI)", "2004 (D1238-04c)", orgao="ASTM"),
         doc("ASTM-D4541", f"{E}/ASTM/ASTM_D_4541_2002[1].pdf", "ASTM D4541-02 — Standard Test Method for Pull-Off Strength of Coatings Using Portable Adhesion Testers "
             "(aderência de pintura por arrancamento/pull-off)", "2002", orgao="ASTM"),
         doc("ASTM-F711", f"{E}/ASTM/ASTM F711 2017 - Fiberglass-Reinforced Plastic Rod and Tube Used in Live Line Tools.pdf",
             "ASTM F711-17 — Standard Specification for Fiberglass-Reinforced Plastic (FRP) Rod and Tube Used in Live Line Tools "
             "(barras e tubos de PRFV para ferramentas de linha viva)", "2017", orgao="ASTM"),
         doc("ASTM-A694", f"{E}/ASTM/A694A694.PDF", "ASTM A694/A694M-00 — Standard Specification for Carbon and Alloy Steel Forgings for Pipe Flanges, Fittings, "
             "Valves, and Parts for High-Pressure Transmission Service (forjados F42–F70 para dutos de alta pressão)", "2000", orgao="ASTM"),
     ]},

    {"id": "isa-valvulas-controle", "titulo": "ISA 75 — válvulas de controle: dimensionamento, ensaios, ruído, cavitação e dimensões",
     "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras da série ISA-75 de válvulas de controle: equações de dimensionamento (75.01.01 / IEC 60534-2-1), "
               "procedimento de ensaio de capacidade (75.02), medição de ruído aerodinâmico (75.07), dimensões face a face de válvulas globo "
               "flangeadas classes 900–2500 (75.08.06) e face ao centro de válvulas angulares classes 150–600 (75.08.08) "
               "e avaliação de cavitação (RP75.23).",
     "docs": [
         doc("ISA-75.01.01", f"{E}/ISA/ISA 75.01.01.pdf", "ANSI/ISA-75.01.01 (IEC 60534-2-1 Mod)-2007 — Flow Equations for Sizing Control Valves "
             "(equações de dimensionamento de válvulas de controle, Cv/Kv)", "2007", orgao="ISA"),
         doc("ISA-75.02", f"{E}/ISA/ISA 75.02 1996.pdf", "ANSI/ISA-75.02-1996 — Control Valve Capacity Test Procedures (ensaio de capacidade de vazão)",
             "1996", orgao="ISA"),
         doc("ISA-75.07", f"{E}/ISA/ISA 75.07 1997.pdf", "ISA-75.07-1997 — Laboratory Measurement of Aerodynamic Noise Generated by Control Valves "
             "(medição de ruído aerodinâmico)", "1997", orgao="ISA"),
         doc("ISA-75.08.06", f"{E}/ISA/ISA 75.08.06 Face-to-Face_Dimensions_for_Flanged_Globe-Style_Control_Valve_Bodies_Classes_900_1500_and_2500.pdf",
             "ANSI/ISA-75.08.06-2002 (R2007) — Face-to-Face Dimensions for Flanged Globe-Style Control Valve Bodies (Classes 900, 1500, and 2500) "
             "(antiga ISA-75.16; dimensões face a face)", "2002 (reafirmada 2007)", orgao="ISA"),
         doc("ISA-75.08.08", f"{E}/ISA/ISA 75.08.08 1999.pdf", "ISA-75.08.08-1999 — Face-to-Centerline Dimensions for Flanged Globe-Style Angle Control Valve Bodies "
             "(Classes 150, 300, and 600) (antiga ANSI/ISA-75.22; dimensões face ao centro de válvulas angulares; cópia de minuta 'Draft Standard … (R200X)')",
             "1999 (minuta de reafirmação)", orgao="ISA"),
         doc("ISA-RP75.23", f"{E}/ISA/ISA 75.23.pdf", "ISA-RP75.23-1995 — Considerations for Evaluating Control Valve Cavitation "
             "(prática recomendada para avaliação de cavitação, índices sigma)", "1995", orgao="ISA"),
     ]},

    {"id": "agma-engrenagens", "titulo": "AGMA — engrenagens: classificação de dentes, fatores geométricos, geometria e componentes de redutores",
     "categoria": "Engrenagens e transmissão", "agrupar": "documento",
     "resumo": "Tabelas e figuras de normas e folhas de informação da AGMA: fatores e métodos de cálculo de capacidade de dentes retos e "
               "helicoidais (2001-D04), projeto e seleção de componentes de redutores fechados — eixos, chavetas, rolamentos, parafusos (6101-F19, métrica), "
               "projeto preliminar de engrenagens de volume mínimo (901-A92), fatores geométricos I e J (908-B89) "
               "e especificação da geometria de engrenagens cilíndricas (913-A98).",
     "docs": [
         doc("AGMA-2001-D04", f"{E}/AGMA/AGMA 2001-D04 - FUNDAMENTAL RATING FACTORS AND CALCULATION METHODS FOR INVOLUTE SPUR AND GEAR TEETH.pdf",
             "ANSI/AGMA 2001-D04 — Fundamental Rating Factors and Calculation Methods for Involute Spur and Helical Gear Teeth "
             "(capacidade de carga — pitting e flexão; revisão da 2001-C95)", "2004", orgao="AGMA"),
         doc("AGMA-6101-F19", f"{OCR}/AGMA-6101-F19.pdf", "ANSI/AGMA 6101-F19 — Design and Selection of Components for Enclosed Gear Drives (Metric Edition) "
             "(edição métrica da 6001-F19; revisão da 6101-E08; cópia OCR)", "2019", orgao="AGMA"),
         doc("AGMA-901-A92", f"{OCR}/AGMA-901-A92.pdf", "AGMA 901-A92 — A Rational Procedure for the Preliminary Design of Minimum Volume Gears "
             "(folha de informação, não é norma; cópia OCR)", "1992", orgao="AGMA"),
         doc("AGMA-908-B89", f"{E}/AGMA/AGMA 908-B89 - GEOMETRY FACTORS FOR DETERMINING THE PITTING RESISTANCE AND BENDING OF SPUR.pdf",
             "AGMA 908-B89 — Geometry Factors for Determining the Pitting Resistance and Bending Strength of Spur, Helical and Herringbone Gear Teeth "
             "(fatores geométricos I e J; folha de informação; revisão da AGMA 226.01)", "1989 (abril)", orgao="AGMA"),
         doc("AGMA-913-A98", f"{E}/AGMA/AGMA 913-A98 - METHOD FOR SPECIFYING THE GEOMETRY OF SPUR AND HELICAL GEARS.pdf",
             "AGMA 913-A98 — Method for Specifying the Geometry of Spur and Helical Gears (folha de informação)", "1998", orgao="AGMA"),
     ]},

    {"id": "aws-simbologia-soldagem", "titulo": "AWS A2.4 e A1.1 — simbologia de soldagem e END, prática métrica",
     "categoria": "Soldagem", "agrupar": "documento",
     "resumo": "Tabelas e figuras da AWS A2.4:2020 (símbolos de soldagem, brasagem e ensaios não destrutivos: seta, linha de referência, "
               "símbolos básicos e suplementares, dimensões, exemplos) e da AWS A1.1:1998 (guia de prática métrica para a indústria de soldagem: "
               "unidades SI, conversões, arredondamento).",
     "docs": [
         doc("AWS-A2.4", f"{OCR}/AWS-A2.4-2020.pdf", "AWS A2.4:2020 — Standard Symbols for Welding, Brazing, and Nondestructive Examination "
             "(8ª ed., substitui a A2.4:2012; cópia OCR)", "2020", orgao="AWS"),
         doc("AWS-A1.1", f"{OCR}/AWS-A1.1-1998.pdf", "ANSI/AWS A1.1:1998 — Metric Practice Guide for the Welding Industry "
             "(substitui a A1.1-89; cópia OCR)", "1998", orgao="AWS"),
     ]},

    {"id": "mss-flanges-valvulas-cuni", "titulo": "MSS SP e EEMUA 234 — flanges de duto, acabamento de face, marcação, válvulas de bronze e tubulação Cu-Ni",
     "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de MSS SP-44 (flanges de aço para dutos NPS 12–60), SP-6 (acabamento das faces de vedação de flanges), "
               "SP-25 (sistema de marcação de válvulas, conexões, flanges e uniões), SP-80 (válvulas gaveta, globo, angular e retenção de bronze) "
               "e EEMUA 234 (especificação de tubulação de cobre-níquel 90/10 para offshore: tubos, conexões, flanges).",
     "docs": [
         doc("MSS-SP-44", f"{E}/MSS/MSS SP-44 2001 - STEEL PIPELINE FLANGES.pdf", "MSS SP-44-1996 (reafirmada 2001) — Steel Pipeline Flanges "
             "(flanges de aço para dutos)", "1996 (R2001)", orgao="MSS"),
         doc("MSS-SP-6", f"{E}/MSS/MSS SP-6 1996 - SNTANDARD FINISHES FOR CONTACT FACES OF PIPE FLANGES AND CONNECTING-END FLANGES OF VALVES AND FITTINGS.pdf",
             "MSS SP-6-1996 — Standard Finishes for Contact Faces of Pipe Flanges and Connecting-End Flanges of Valves and Fittings "
             "(rugosidade/acabamento da face de vedação)", "1996", orgao="MSS"),
         doc("MSS-SP-25", f"{OCR}/MSS-SP-25-1998.pdf", "MSS SP-25-1998 — Standard Marking System for Valves, Fittings, Flanges and Unions "
             "(marcação; cópia OCR)", "1998", orgao="MSS"),
         doc("MSS-SP-80", f"{E}/MSS/MSS SP-80 1997 - BRONZE GATE, GLOBE, ANGLE AND CHECK VALVES.pdf",
             "MSS SP-80-1997 — Bronze Gate, Globe, Angle and Check Valves (válvulas de bronze)", "1997", orgao="MSS"),
         doc("EEMUA-234", f"{OCR}/EEMUA-901.pdf", "EEMUA Publication 234 — 90/10 Copper Nickel Alloy Piping for Offshore Applications — Specification "
             "(incorpora as EEMUA 144, 145 e 146; tubos, conexões e flanges de Cu-Ni 90/10; cópia OCR)", "2015 (Edition 1)", orgao="EEMUA"),
     ]},

    {"id": "bs-tubulacao-valvulas-roscas", "titulo": "BS — roscas de tubo (BS 21, BS 2779), flanges BS 4504 e projeto de corpo de válvula EN 12516-1",
     "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de BS 21 (roscas de tubo com vedação na rosca — cônica/paralela Whitworth, longscrew e calibradores), "
               "BS 2779 (roscas de tubo sem vedação na rosca — classes A/B), BS 4504-3.1 (flanges circulares de aço PN) "
               "e BS EN 12516-1 (resistência de corpo de válvula de aço — método tabular, espessuras mínimas).",
     "docs": [
         doc("BS-21", f"{E}/BS/BS 21 1985 - PIPE THREADS FOR TUBES AND FITTINGS WHERE PRESSURE-TIGHT JOINTS ARE MADE ON THE THREADS METRIC DIMENSIONS.pdf",
             "BS 21:1985 — Pipe threads for tubes and fittings where pressure-tight joints are made on the threads (metric dimensions) "
             "(rosca R/Rp/Rc, equivalente à ISO 7-1; com Amd. 1; posteriormente substituída pela BS EN 10226-1)", "1985 (+ Amd. 1)", orgao="BS"),
         doc("BS-2779", f"{E}/BS/BS 2779 1986.pdf", "BS 2779:1986 — Pipe threads for tubes and fittings where pressure-tight joints are not made on the threads "
             "(metric dimensions) (rosca G, equivalente à ISO 228-1; posteriormente substituída pela BS EN ISO 228-1)", "1986", orgao="BS"),
         doc("BS-4504-3.1", f"{OCR}/BS-4504-1989.pdf", "BS 4504: Section 3.1:1989 — Circular flanges for pipes, valves and fittings (PN designated) — "
             "Specification for steel flanges (flanges de aço PN; 1ª revisão da BS 4504-1:1969; cópia OCR)", "1989", orgao="BS"),
         doc("BS-EN-12516-1", f"{E}/BS/BS 12516-1 2005 - Industrial-Valves-Shell-Design-Strength.pdf",
             "BS EN 12516-1:2005 — Industrial valves — Shell design strength — Part 1: Tabulation method for steel valve shells "
             "(espessura mínima de corpo de válvula de aço por PN/classe)", "2005", orgao="BS"),
     ]},

    {"id": "bs-acos-fixadores-desenho-maritimo", "titulo": "BS/EN/ISO — aços estruturais EN 10025, chavetas, fixadores não ferrosos, vistas em desenho e defensas",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras de BS EN 10025-1 e -2 (produtos laminados a quente de aço estrutural: condições gerais e aços não ligados S235–S450), "
               "BS 4235-1 (chavetas paralelas e inclinadas métricas), BS EN 28839 / ISO 8839 (propriedades mecânicas de fixadores de metais "
               "não ferrosos), BS ISO 128-30 (convenções básicas de vistas em desenho técnico) e BS 6349-4 (projeto de defensas e "
               "sistemas de amarração em obras marítimas).",
     "docs": [
         doc("BS-EN-10025-1", f"{E}/BS/BS 10025-1 2004 - HotRolledProducts_TDP.pdf", "BS EN 10025-1:2004 — Hot rolled products of structural steels — "
             "Part 1: General technical delivery conditions (substitui a EN 10025:1990 e EN 10113-1)", "2004", orgao="BS"),
         doc("BS-EN-10025-2", f"{OCR}/BS-10025-2-2004.pdf", "BS EN 10025-2:2004 — Hot rolled products of structural steels — Part 2: Technical delivery conditions "
             "for non-alloy structural steels (S235, S275, S355, S450; cópia OCR)", "2004", orgao="BS"),
         doc("BS-4235-1", f"{E}/BS/bs-4235-1-1972-specification-for-metric-keys-and-keyways-parallel-and-taper-keys.pdf",
             "BS 4235-1:1972 — Specification for metric keys and keyways — Part 1: Parallel and taper keys (chavetas; confirmada jul/1986, com Amd. 1–3)",
             "1972 (confirmada 1986)", orgao="BS"),
         doc("ISO-8839", f"{E}/BS/BS EN 28839 1992 ISO 8839 1986 - Mechanical properties of fasteners Bolts, screws, studs and nuts made of non-ferrous metals.pdf",
             "BS EN 28839:1992 (ISO 8839:1986) — Mechanical properties of fasteners — Bolts, screws, studs and nuts made of non-ferrous metals "
             "(cobre, latão, bronze, alumínio)", "1986 (BS EN 28839:1992)", orgao="BS"),
         doc("ISO-128-30", f"{E}/BS/bs-iso-00128-30-2001pdf.pdf", "BS ISO 128-30:2001 — Technical drawings — General principles of presentation — "
             "Part 30: Basic conventions for views (vistas: 1º e 3º diedro, vistas parciais, locais, auxiliares)", "2001 (1ª ed.)", orgao="BS"),
         doc("BS-6349-4", f"{E}/BS/BS 6349-4 2014 - Maritime Works - Design of Fendering and Mooring Systems.pdf",
             "BS 6349-4:2014 — Maritime works — Part 4: Code of practice for design of fendering and mooring systems (defensas e amarração)",
             "2014", orgao="BS"),
     ]},

    {"id": "estruturas-aco-aisc-aisi", "titulo": "AISC 1989 (ASD) e AISI S100 — estruturas de aço laminado e perfis formados a frio",
     "categoria": "Estruturas e fabricação", "agrupar": "documento",
     "resumo": "Tabelas e figuras da especificação AISC de edifícios de aço — tensões admissíveis (ASD) e projeto plástico, 1989, com comentários "
               "— e da AISI S100-16 (com Suplemento 1 de 2018), especificação norte-americana de perfis de aço formados a frio.",
     "docs": [
         doc("AISC-ASD-1989", f"{E}/AISC/AISC 1989 - Specification for Structural Steel Buildings - Allowable Stress Design and Plastic Design.pdf",
             "AISC — Specification for Structural Steel Buildings — Allowable Stress Design and Plastic Design, June 1, 1989, with Commentary "
             "(9ª ed. do Manual, parte 5)", "1989 (1º de junho)", orgao="AISC"),
         doc("AISI-S100", f"{E}/AISI/AISI S100-16W S1-18 2016 - DESIGN OF COLD-FORMED STEEL STRUCTURAL MEMBERS.pdf",
             "AISI S100-16w/S1-18 — North American Specification for the Design of Cold-Formed Steel Structural Members, 2016 Edition with Supplement 1 "
             "(perfis formados a frio)", "2016 (+ Suplemento 1, 2018)", orgao="AISI"),
     ]},

    {"id": "outros-energia-trilho-arruelas", "titulo": "Fornecimento de energia em 15 kV (AMPLA), trilho ferroviário (DNIT PIM 01) e arruelas lisas ASME B18.22.1",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras do padrão de fornecimento de energia elétrica em tensão primária 15 kV da AMPLA (subestações, entrada de serviço, "
               "medição), do procedimento de inspeção de materiais DNIT PIM 01 (trilho para linha férrea: perfis, tolerâncias, inspeção) "
               "e da ASME B18.22.1 (arruelas lisas tipo A e B, polegada).",
     "docs": [
         doc("AMPLA-TP-15KV", f"{E}/AMPLA/AMPLA 2011 Rev 05 - Fornecimento de Energia Eletrica em Tensao Primaria 15 kV.pdf",
             "AMPLA — Padrão de Fornecimento de Energia Elétrica: Fornecimento de energia elétrica em tensão primária 15 kV", "Edição 01, Rev. 05 (dez/2011)",
             orgao="AMPLA"),
         doc("DNIT-PIM-01", f"{E}/DNIT/DNIT PIM 01 2015 - Trilho para Linha Ferrea.pdf",
             "DNIT — PIM 01: Procedimento de inspeção de materiais — Trilho para linha férrea (Contrato DIF/DNIT 127/2008)", "2015", orgao="DNIT"),
         doc("ASME-B18.22.1", f"{OCR}/ASME-B18.22.1-1965.pdf", "ASME B18.22.1-1965 (R1998) — Plain Washers (arruelas lisas tipo A e B; antiga ANSI B27.2; "
             "reprodução do livro IFI; cópia OCR)", "1965 (reafirmada 1998)", orgao="ANSI"),
     ]},
]
