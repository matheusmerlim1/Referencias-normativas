"""Configuração das fichas de "tabelas e figuras" das normas ISO de referencias/ (lido por ferramentas/gerar_docs.py).

Mesmo formato de FICHAS em gerar_docs.py. Documentos escaneados usam a cópia OCR de referencias/ocr/ (mesmas páginas).
Códigos/edições conferidos na 1ª página de cada PDF (OCR da 1ª página nos escaneados). Quando a cópia é uma adoção
(BS/EN/DIN/DS/IS), o código da adoção vai no título e a edição ISO correspondente em "edicao".
Títulos em inglês, como na norma. Duplicatas e edições superadas ficam fora, em EXCLUIDOS.
"""

A = "referencias/extraido/ISO"
OCR = "referencias/ocr"


def doc(id_, arq, titulo, edicao, escopo="", orgao="ISO"):
    return {"id": id_, "arq": arq, "titulo": titulo, "edicao": edicao, "escopo": escopo, "orgao": orgao}


EXCLUIDOS = {
    f"{A}/iso-3730-1988-id-498836.pdf": "arquivo danificado: imagens das páginas não decodificam (zlib/faxd) e a cópia OCR sai em branco — sem conteúdo aproveitável",
    f"{A}/iso 5167nportugues.pdf":
        "duplicata/edição superada: tradução livre (Marco Antônio Ribeiro) da ISO 5167-1:1991; o conteúdo já está na NBR ISO 5167-1:1994 "
        "(equiv. ISO 5167-1:1991, em normas.json) e a ISO 5167-1:2003 do acervo é a edição mais nova",
}


FICHAS = [
    {"id": "iso-fixadores-parafusos-porcas", "titulo": "ISO — parafusos, porcas e propriedades mecânicas de fixadores", "categoria": "Parafusos e fixação", "agrupar": "documento",
     "resumo": "Tabelas e figuras das normas ISO de parafusos (ISO 4014, 8765, 4762, 12474, 14579, 7379, 7380-1, 10642, 7049, 7053, 1478, 4757), "
               "porcas (ISO 4034, 7040, 10511) e propriedades mecânicas (ISO 3506-2 porcas inox, ISO 898-5 parafusos sem cabeça).",
     "docs": [
         doc("ISO-4014", f"{OCR}/ISO-4014-2001.pdf", "DIN EN ISO 4014:2001 — Hexagon head bolts — Product grades A and B (parafuso sextavado com haste; cópia OCR)", "1999 (DIN EN ISO 4014:2001-03)"),
         doc("ISO-8765", f"{OCR}/ISO-8765-2001.pdf", "BS EN ISO 8765:2001 — Hexagon head bolts with metric fine pitch thread — Product grades A and B (rosca fina; cópia OCR)", "1999 (BS EN ISO 8765:2001)"),
         doc("ISO-4762", f"{OCR}/ISO-4762-2004.pdf", "DIN EN ISO 4762:2004 — Hexagon socket head cap screws (parafuso Allen cilíndrico; cópia OCR)", "2004 (DIN EN ISO 4762:2004-06)"),
         doc("ISO-12474", f"{A}/ISO 12474 2010 - HEXAGON SOCKET HEAD CAP SCREWS WITH METRIC FINE PITCH THREAD.pdf",
             "Hexagon socket head cap screws with metric fine pitch thread (Allen cilíndrico, rosca fina)", "2010 (1ª ed.)"),
         doc("ISO-14579", f"{A}/ISO 14579 2011 - Hexalobular Socket Head Cap Screws.pdf", "Hexalobular socket head cap screws (cabeça cilíndrica, sextavado interno lobular/Torx)", "2011 (2ª ed.)"),
         doc("ISO-7379", f"{A}/ISO 7379 1983 - HEXAGON SOCKET HEAD SHOULDER SCREWS.pdf", "Hexagon socket head shoulder screws (parafuso com ressalto/espiga retificada)", "1983 (1ª ed.)"),
         doc("ISO-7380-1", f"{A}/ISO 7380 2011 - Button head screws Hexagon socket button head screws.pdf",
             "Button head screws — Part 1: Hexagon socket button head screws (cabeça abaulada)", "2011 (1ª ed.)"),
         doc("ISO-10642", f"{OCR}/ISO-10642-2019.pdf",
             "BS EN ISO 10642:2019 — Fasteners — Hexagon socket countersunk head screws with reduced loadability (cabeça escareada; cópia OCR)", "2019"),
         doc("ISO-7049", f"{A}/ISO 7049 2011 - Cross-Recessed Pan Head Tapping Screws.pdf", "Cross-recessed pan head tapping screws (parafuso autoatarraxante, fenda cruzada)", "2011 (2ª ed.)"),
         doc("ISO-7053", f"{A}/ISO 7053 2011 - Hexagon Washer Head Tapping Screws.pdf", "Hexagon washer head tapping screws (autoatarraxante sextavado com flange)", "2011 (2ª ed.)"),
         doc("ISO-1478", f"{A}/iso-1478.pdf", "BS EN ISO 1478:2000 — Tapping screws thread (rosca de parafuso autoatarraxante)", "1999 (BS EN ISO 1478:2000)"),
         doc("ISO-4757", f"{A}/BS EN ISO 4757 1995 - Cross Recesses for Screws.pdf", "BS EN ISO 4757:1995 — Cross recesses for screws (fendas cruzadas H/Z)", "1983 (EN ISO 4757:1994 / BS 1995)"),
         doc("ISO-4034", f"{OCR}/ISO-4034-1999.pdf", "Hexagon nuts — Product grade C (porca sextavada grau C; cópia OCR)", "1999 (3ª ed.)"),
         doc("ISO-7040", f"{A}/ISO 7040 2012 - Prevailing torque type hexagon regular nuts with non-metallic insert classes 5, 8 and 10.pdf",
             "Prevailing torque type hexagon regular nuts (with non-metallic insert) — Property classes 5, 8 and 10 (porca autotravante com anel de náilon)", "2012 (3ª ed.)"),
         doc("ISO-10511", f"{A}/ISO 10511 2012 - Prevailing torque type hexagon thin nuts with non-metallic insert.pdf",
             "Prevailing torque type hexagon thin nuts (with non-metallic insert) (porca baixa autotravante)", "2012 (3ª ed.)"),
         doc("ISO-3506-2", f"{A}/ISO 3506 2 2009 - MECHANICAL PROPERTIES OF CORROSION-RESISTANT STAINLESS STEEL FASTENERS - NUTS.pdf",
             "Mechanical properties of corrosion-resistant stainless steel fasteners — Part 2: Nuts (porcas de aço inox)", "2009 (2ª ed.)"),
         doc("ISO-898-5", f"{A}/ISO 898-5 2012 - Mechanical properties of fasteners - Set screws and similar threaded fasteners with specified hardness classes.pdf",
             "Mechanical properties of fasteners made of carbon steel and alloy steel — Part 5: Set screws and similar threaded fasteners with specified hardness classes "
             "— Coarse thread and fine pitch thread (parafusos sem cabeça)", "2012"),
     ]},

    {"id": "iso-fixadores-pinos-rebites-revestimentos", "titulo": "ISO — pinos, contrapinos, rebites, tolerâncias e revestimentos de fixadores", "categoria": "Parafusos e fixação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 1234 (contrapinos), ISO 8752 (pinos elásticos), ISO 15983 e 14589 (rebites cegos), "
               "ISO 4759-1 (tolerâncias de fixadores, graus A, B e C), ISO 4042 (revestimento eletrolítico) e ISO 10683 (zinco lamelar).",
     "docs": [
         doc("ISO-1234", f"{A}/ISO 1234 1997 - SPLIT PINS.pdf", "Split pins (contrapinos)", "1997 (2ª ed.)"),
         doc("ISO-8752", f"{OCR}/ISO-8752-1997.pdf", "Spring-type straight pins — Slotted, heavy duty (pino elástico, série pesada; cópia OCR)", "1997 (2ª ed.)"),
         doc("ISO-15983", f"{A}/ISO 15983 2002 - Open end blind rivets with break pull mandrel and protruding head A2_A2.pdf",
             "Open end blind rivets with break pull mandrel and protruding head — A2/A2 (rebite cego inox)", "2002 (1ª ed.)"),
         doc("ISO-14589", f"{A}/ISO 14589 2000 - Blind rivets Mechanical testing.pdf", "DS/EN ISO 14589 — Blind rivets — Mechanical testing (ensaios de rebites cegos)", "2000 (DS/EN ISO 14589:2001)"),
         doc("ISO-4759-1", f"{A}/ISO 4759 2000 - Technical supply conditions for threaded steel fasteners.pdf",
             "IS 1367 (Part 2):2002 = ISO 4759-1:2000 — Tolerances for fasteners — Part 1: Bolts, screws, studs and nuts — Product grades A, B and C", "2000 (adoção indiana IS 1367-2:2002)"),
         doc("ISO-4042", f"{OCR}/ISO-4042-2018.pdf"  # texto original 0,1 pt/letra → cópia OCR
            , "Fasteners — Electroplated coating systems (revestimento eletrolítico)", "2018 (3ª ed.)"),
         doc("ISO-10683", f"{OCR}/ISO-10683-2014.pdf"  # texto original 0,1 pt/letra → cópia OCR
            ,
             "Fasteners — Non-electrolytically applied zinc flake coatings (zinco lamelar, tipo Geomet/Dacromet)", "2014 (2ª ed.)"),
     ]},

    {"id": "iso-roscas", "titulo": "ISO — roscas métricas e roscas de tubo", "categoria": "Parafusos e fixação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 261 (plano geral da rosca métrica), ISO 724 (dimensões básicas), ISO 4753 (pontas de parafusos), "
               "ISO 228-1 (rosca de tubo sem vedação na rosca, G) e ISO 7-1 (rosca de tubo com vedação na rosca, R/Rp/Rc).",
     "docs": [
         doc("ISO-261", f"{A}/ISO 261 1998 - General purpose metric screw threads General plans.pdf", "BS ISO 261:1998 — ISO general purpose metric screw threads — General plan", "1998"),
         doc("ISO-724", f"{OCR}/ISO-724-1993.pdf", "ISO general-purpose metric screw threads — Basic dimensions (cópia OCR)", "1993 (2ª ed.)"),
         doc("ISO-4753", f"{A}/ISO 4753 1999 - FASTENERS ENDS OF PARTS WITH EXTERNAL ISO METRIC THREAD.pdf",
             "Fasteners — Ends of parts with external ISO metric thread (pontas de parafusos)", "1999 (2ª ed.)"),
         doc("ISO-228-1", f"{A}/ISO 228-1 2000 - PIPE THREAD WHERE PRESSURE-TIGHT JOINTS ARE NOT MADE ON THE THREADS.pdf",
             "Pipe threads where pressure-tight joints are not made on the threads — Part 1: Dimensions, tolerances and designation (rosca G)", "2000 (4ª ed.)"),
         doc("ISO-7-1", f"{A}/ISO 7-1 - Pipe Threads Where Pressure-Tight Joints are Made on the Threads - Dimensions.pdf",
             "Pipe threads where pressure-tight joints are made on the threads — Part 1: Dimensions, tolerances and designation (rosca R/Rp/Rc)", "1994 (3ª ed.)"),
     ]},

    {"id": "iso-hidraulica", "titulo": "ISO — hidráulica: sistemas, cilindros, conexões de tubo e anéis O-ring", "categoria": "Hidráulica", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 4413 (regras gerais de sistemas hidráulicos), ISO 3320, 6020-1 e 6022 (cilindros: diâmetros e dimensões de montagem 160/250 bar), "
               "ISO 8434-1/-2/-3/-4/-6 (conexões de tubo 24°, 37°, face plana com O-ring, 60°), ISO 3601-1/-3 (O-rings) e ISO 2230 (armazenagem de borracha).",
     "docs": [
         doc("ISO-4413", f"{A}/ISO 4413 1998 - Hydraulic fluid power General rules relating to systems.pdf", "Hydraulic fluid power — General rules relating to systems", "1998 (2ª ed.)"),
         doc("ISO-3320", f"{A}/ISO 3320 2013 - FLUID POWER SYSTEMS AND COMPONENTS - CYLINDER BORES AND PISTON ROD DIAMETERS AND AREA RATIOS - METRIC.pdf",
             "Fluid power systems and components — Cylinder bores and piston rod diameters and area ratios — Metric series", "2013 (3ª ed.)"),
         doc("ISO-6020-1", f"{A}/ISO 6020-1 2007 - HYDRAULIC FLUID POWER - MOUNTING DIMENSIONS FOR SINGLE ROD CYLINDERS, 160BAR SERIES - MEDIUM SERIES.pdf",
             "Hydraulic fluid power — Mounting dimensions for single rod cylinders, 16 MPa (160 bar) series — Part 1: Medium series", "2007 (3ª ed.)"),
         doc("ISO-6022", f"{A}/ISO 6022 2006 - HYDRAULIC FLUID POWER - MOUNTING DIMENSIONS FOR SINGLE ROD CYLINDERS, 250BAR SERIES.pdf",
             "Hydraulic fluid power — Mounting dimensions for single rod cylinders, 25 MPa (250 bar) series", "2006 (2ª ed.)"),
         doc("ISO-8434-1", f"{A}/ISO 8434 1 2007 - Metallic tube connections for fluid power and general use Part 1.pdf",
             "Metallic tube connections for fluid power and general use — Part 1: 24° cone connectors", "2007 (2ª ed.)"),
         doc("ISO-8434-2", f"{A}/ISO 8434 2 2007 - Metallic tube connections for fluid power and general use Part 2.pdf",
             "BS ISO 8434-2:2007 — Metallic tube connections for fluid power and general use — Part 2: 37° flared connectors", "2007"),
         doc("ISO-8434-3", f"{A}/ISO 8434 3 1995 - Metallic tube connections for fluid power and general use Part 3.pdf",
             "Metallic tube connections for fluid power and general use — Part 3: O-ring face seal fittings", "1995 (1ª ed.)"),
         doc("ISO-8434-4", f"{OCR}/ISO-8434-4-2000.pdf"  # fonte com codificação deslocada → cópia OCR
            ,
             "BS EN ISO 8434-4:2000 — Metallic tube connections for fluid power and general use — Part 4: 24° cone connectors with O-ring weld-on nipples "
             "(cópia OCR — o texto do PDF original tem fonte com codificação deslocada)", "1995 (BS EN ISO 8434-4:2000)"),
         doc("ISO-8434-6", f"{A}/ISO 8434 6 2007 - Metallic tube connections for fluid power and general use Part 6.pdf",
             "ISO/DIS 8434-6 — Metallic tube connections for fluid power and general use — Part 6: 60° cone connectors with or without O-ring (PROJETO, não a norma publicada)", "projeto DIS 2007"),
         doc("ISO-3601-1", f"{A}/iso-3601-1.pdf", "Fluid power systems — O-rings — Part 1: Inside diameters, cross-sections, tolerances and designation codes", "2012 (5ª ed.)"),
         doc("ISO-3601-3", f"{A}/ISO 3601-3.pdf", "Fluid power systems — O-rings — Part 3: Quality acceptance criteria", "2005 (2ª ed.)"),
         doc("ISO-2230", f"{OCR}/ISO-2230-2002.pdf", "Rubber products — Guidelines for storage (armazenagem de produtos de borracha; cópia OCR)", "2002 (2ª ed.)"),
     ]},

    {"id": "iso-engrenagens-transmissao", "titulo": "ISO — engrenagens, correntes e correias de transmissão", "categoria": "Engrenagens e transmissão", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 6336-1/-2/-3/-5/-6 (capacidade de carga de engrenagens cilíndricas), ISO 9085 (engrenagens industriais), "
               "ISO 53 (perfil de referência), ISO/TR 13989-2 (engripamento/scuffing), ISO 606 (correntes de rolos e rodas dentadas) e ISO 5294 (polias de correia sincronizada).",
     "docs": [
         doc("ISO-6336-1", f"{A}/ISO 6336-1 2006 - CALCULATION OF LOAD CAPACITY OF SPUR AND HELICAL GEAR - BASIC PRINCIPLES, INTRODUCTION AND GENERAL INFLUENCE FACTORS.pdf",
             "BS ISO 6336-1:2006 — Calculation of load capacity of spur and helical gears — Part 1: Basic principles, introduction and general influence factors", "2006 (corrigendum 2008)"),
         doc("ISO-6336-2", f"{A}/ISO 6336-2 2006 - CALCULATION OF LOAD CAPACITY OF SPUR AND HELICAL GEAR - CALCULATION OF SURFACE DURABILITY pitting.pdf",
             "BS ISO 6336-2:2006 — Calculation of load capacity of spur and helical gears — Part 2: Calculation of surface durability (pitting)", "2006 (corrigendum 2008)"),
         doc("ISO-6336-3", f"{A}/ISO 6336-3 2006 - CALCULATION OF LOAD CAPACITY OF SPUR AND HELICAL GEAR - CALCULATION OF TOOTH BENDING STRENGTH.pdf",
             "BS ISO 6336-3:2006 — Calculation of load capacity of spur and helical gears — Part 3: Calculation of tooth bending strength", "2006 (corrigendum 2008)"),
         doc("ISO-6336-5", f"{A}/ISO 6336-5 2006 - CALCULATION OF LOAD CAPACITY OF SPUR AND HELICAL GEAR - STRENGTH AND QUALITY OF MATERIALS.pdf",
             "BS ISO 6336-5:2003 — Calculation of load capacity of spur and helical gears — Part 5: Strength and quality of materials", "2003"),
         doc("ISO-6336-6", f"{A}/ISO 6336-6 2006 - CALCULATION OF LOAD CAPACITY OF SPUR AND HELICAL GEAR - CALCULATION OF SERVIE LIFE UNDER VARIABLE LOAD.pdf",
             "BS ISO 6336-6:2006 — Calculation of load capacity of spur and helical gears — Part 6: Calculation of service life under variable load", "2006 (corrigendum 1)"),
         doc("ISO-9085", f"{OCR}/ISO-9085-2002.pdf", "Calculation of load capacity of spur and helical gears — Application for industrial gears (cópia OCR)", "2002 (1ª ed.)"),
         doc("ISO-53", f"{OCR}/ISO-53-1998.pdf", "BS ISO 53:1998 — Cylindrical gears for general and heavy engineering — Standard basic rack tooth profile (cópia OCR)", "1998 (2ª ed.)"),
         doc("ISO-TR-13989-2", f"{OCR}/ISO-13989-2-2000.pdf",
             "ISO/TR 13989-2 — Calculation of scuffing load capacity of cylindrical, bevel and hypoid gears — Part 2: Integral temperature method (cópia OCR)", "2000"),
         doc("ISO-606", f"{A}/ISO 606 2004 - Short-pitch transmission precision roller and bush chain, attachments and associatec chain sprockets.pdf",
             "Short-pitch transmission precision roller and bush chains, attachments and associated chain sprockets", "2004 (3ª ed.)"),
         doc("ISO-5294", f"{A}/ISO 5294 2012 - SYNCHRONOUS BELT DRIVES PULLEYS.pdf", "Synchronous belt drives — Pulleys (polias de correia sincronizada)", "2012 (3ª ed.)"),
     ]},

    {"id": "iso-desenho-gps", "titulo": "ISO — desenho técnico, rugosidade e sistema de tolerâncias ISO", "categoria": "Desenho técnico", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 128-40 (cortes e seções), ISO 1302 (indicação de textura de superfície/rugosidade em desenho) "
               "e ISO 286-1 (sistema ISO de tolerâncias e ajustes — bases, afastamentos e ajustes).",
     "docs": [
         doc("ISO-128-40", f"{A}/iso-128-40.pdf", "Technical drawings — General principles of presentation — Part 40: Basic conventions for cuts and sections", "2001 (1ª ed.)"),
         doc("ISO-1302", f"{A}/ISO 1302 2002 - GEOMETRICAL PRODUCT SPECIFICATIONS - INDICATION OF SURFACE TEXTURE IN TECHNICAL PRODUCT DOCUMENTATION.pdf",
             "Geometrical Product Specifications (GPS) — Indication of surface texture in technical product documentation", "2002 (4ª ed.)"),
         doc("ISO-286-1", f"{OCR}/ISO-286-1-2010.pdf",
             "BS EN ISO 286-1:2010 — GPS — ISO code system for tolerances on linear sizes — Part 1: Basis of tolerances, deviations and fits (cópia OCR)", "2010"),
     ]},

    {"id": "iso-materiais", "titulo": "ISO — materiais: serviço com H2S, aços estruturais e ensaio de tração de plásticos", "categoria": "Materiais", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 15156-1 e NACE MR0175/ISO 15156-2 (materiais para ambientes com H2S — princípios gerais e aços-carbono/baixa liga), "
               "ISO 630 (aços estruturais) e ISO 527-1 (propriedades de tração de plásticos).",
     "docs": [
         doc("ISO-15156-1", f"{OCR}/ISO-15156-1-2009.pdf",
             "Petroleum and natural gas industries — Materials for use in H2S-containing environments in oil and gas production — Part 1: General principles for selection of cracking-resistant materials (cópia OCR)", "2009 (2ª ed.)"),
         doc("ISO-15156-2", f"{OCR}/ISO-15156-2-2003.pdf",
             "NACE MR0175/ISO 15156-2 — Petroleum and natural gas industries — Materials for use in H2S-containing environments in oil and gas production — "
             "Part 2: Cracking-resistant carbon and low alloy steels, and the use of cast irons (cópia OCR)", "2003 (1ª ed.)"),
         doc("ISO-630", f"{OCR}/ISO-630-1995.pdf", "Structural steels — Plates, wide flats, bars, sections and profiles (cópia OCR)", "1995 (2ª ed.)"),
         doc("ISO-527-1", f"{A}/ISO 527-1 2012 - Plastics - Determination of Tensile Properties - Part 1 General Principles.pdf",
             "Plastics — Determination of tensile properties — Part 1: General principles", "2012 (2ª ed.)"),
     ]},

    {"id": "iso-offshore-containers-maquinas", "titulo": "ISO — sistemas submarinos, containers, guinchos de amarração e risco de máquinas", "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras de ISO 13628-7 (risers de completação/workover) e do projeto ISO/DIS 13628-15 (estruturas e manifolds submarinos), "
               "ISO 1496-1 e 1496-2 (containers série 1 — carga geral e térmicos), ISO 3730 (guinchos de amarração) e ISO/TR 14121-2 (apreciação de risco de máquinas).",
     "docs": [
         doc("ISO-13628-7", f"{A}/ISO 13628-7 ED1 - PETROLEUM AND NATURAL GAS INDUSTRIES - DESIGN AND OPERATIONS OF SUBSEA PRODUCTION SYSTEMS - COMPLETION WORKOVER RISER SYSTEMS.pdf",
             "Petroleum and natural gas industries — Design and operation of subsea production systems — Part 7: Completion/workover riser systems", "2005 (1ª ed.)"),
         doc("ISO-13628-15", f"{A}/ISO 13628-15 B1946.pdf",
             "ISO/DIS 13628-15 — Petroleum and natural gas industries — Design and operation of subsea production systems — Part 15: Subsea structures and manifolds "
             "(PROJETO DIS, votação 2009-10 a 2010-03; a norma publicada não está no acervo)", "projeto DIS 2009"),
         doc("ISO-1496-1", f"{A}/iso.1496-1.1990.pdf", "Series 1 freight containers — Specification and testing — Part 1: General cargo containers for general purposes", "1990 (5ª ed.)"),
         doc("ISO-1496-2", f"{A}/iso-1496.pdf", "BS ISO 1496-2:1996 — Series 1 freight containers — Specification and testing — Part 2: Thermal containers (com Amd. 1)", "1996 (+ Amd. 1)"),
         doc("ISO-TR-14121-2", f"{OCR}/ISO-14121-2-2012.pdf",
             "ISO/TR 14121-2 — Safety of machinery — Risk assessment — Part 2: Practical guidance and examples of methods (cópia OCR)", "2012 (2ª ed.)"),
     ]},
]
