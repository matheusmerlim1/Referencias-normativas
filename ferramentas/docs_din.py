"""Configuração das fichas de "tabelas e figuras" das normas DIN de referencias/ (lido por ferramentas/gerar_docs.py).

Mesmo formato de FICHAS em gerar_docs.py. Documentos escaneados usam a cópia OCR de referencias/ocr/ (mesmas páginas).
Códigos/edições conferidos na 1ª página de cada PDF (OCR da 1ª página nos escaneados). Títulos em inglês (ou alemão,
quando a cópia é a versão alemã), como no documento; descrição em português entre parênteses.
Duplicatas e edições superadas ficam fora, em EXCLUIDOS.
"""

A = "referencias/extraido/DIN"
OCR = "referencias/ocr"


def doc(id_, arq, titulo, edicao, escopo="", orgao="DIN"):
    return {"id": id_, "arq": arq, "titulo": titulo, "edicao": edicao, "escopo": escopo, "orgao": orgao}


EXCLUIDOS = {
    f"{A}/DIN 125-2 1990 - PRODUCT GRADE A WASHERS.pdf":
        "edição superada: DIN 125-2:1990-03 substituída pela DIN EN ISO 7090:2000-11 (a própria 7090 diz que, com a DIN EN ISO 7089, "
        "substitui DIN 125-1 e DIN 125-2 de março/1990) — usada a DIN EN ISO 7090 desta mesma ficha",
    f"{A}/DIN 17221 1972 - HOT ROLLED STEELS FOR QUNCHED AND TEMPERED SPRINGS - QUALITY SPECIFICATIONS.pdf":
        "edição superada: DIN 17221:1972-12 (havia ainda a edição 1988-12), substituída pela DIN EN 10089:2003-04 "
        "(a 10089 diz 'Supersedes DIN 17221, December 1988 edition') — usada a DIN EN 10089",
    f"{A}/din-iso-70491990-8.pdf":
        "edição superada: DIN ISO 7049:1990-08 (versão alemã, idêntica à ISO 7049:1983); a ISO 7049:2011 (2ª ed.) já está em "
        "normas.json (id ISO-7049, ficha iso-fixadores-parafusos-porcas)",
    f"{A}/DIN 7504 1995 - Self-drilling tapping screws Dimensions.pdf":
        "duplicata incompleta: só as 2 primeiras páginas (recortadas) da DIN 7504:1995-09; usada a cópia completa de 6 páginas "
        "'DIN 7504 1995 - Self-drilling tapping screws Dimensions, requirements and testing'",
    f"{A}/DIN 3017-1.pdf":
        "duplicata: DIN 3017-1:1998-05 versão alemã (mesma edição, 6 págs.); usada a tradução inglesa da mesma edição "
        "(din-3017-1-may-1998-english, cópia OCR)",
}


FICHAS = [
    {"id": "din-parafusos-porcas", "titulo": "DIN — parafusos, porcas e uniões parafusadas", "categoria": "Parafusos e fixação", "agrupar": "documento",
     "resumo": "Tabelas e figuras das normas DIN de parafusos (DIN 912, 931-1, 933, 961, 6921, 7985, 7504, 914, DIN EN ISO 4026, 7050 e 2702), "
               "porcas (DIN 934, 979) e da diretriz de projeto de uniões parafusadas DIN 25201-2 (veículos ferroviários).",
     "docs": [
         doc("DIN-912", f"{OCR}/DIN-912-1983.pdf", "DIN 912:1983 — Hexagon socket head cap screws (modified version of ISO 4762) "
             "(parafuso cilíndrico com sextavado interno/Allen; cópia OCR)", "1983-12"),
         doc("DIN-931-1", f"{OCR}/DIN-931-1-1987.pdf", "DIN 931-1:1987 — M1,6 to M39 hexagon head bolts — Product grades A and B "
             "(parafuso sextavado com haste parcialmente roscada; a norma manda usá-la junto com a ISO 4014; cópia OCR)", "1987-09"),
         doc("DIN-933", f"{OCR}/DIN-933-1987.pdf", "DIN 933:1987 — M1,6 to M52 hexagon head screws threaded up to the head — Product grades A and B "
             "(parafuso sextavado rosca total; a norma manda usá-la junto com a ISO 4017; cópia OCR)", "1987-09"),
         doc("DIN-961", f"{OCR}/DIN-961-1990.pdf", "DIN 961:1990 — M8 x 1 to M52 x 3 hexagon head bolts with fine pitch thread — Product grades A and B "
             "(parafuso sextavado rosca total, rosca fina; cópia OCR)", "1990-01"),
         doc("DIN-6921", f"{OCR}/DIN-6921-1983.pdf", "DIN 6921:1983 — Hexagon flange bolts (parafuso sextavado flangeado; cópia OCR)", "1983-06"),
         doc("DIN-7985", f"{A}/DIN 7985 1986 - Cross-Recessed Raised Cheese Head Screws.pdf",
             "DIN 7985:1986 — Cross recessed raised cheese head screws (parafuso cabeça cilíndrica abaulada, fenda cruzada Phillips/Pozidriv)", "1986-07"),
         doc("DIN-7504", f"{OCR}/DIN-7504-1995.pdf", "DIN 7504:1995 — Self-drilling tapping screws — Dimensions, requirements and testing "
             "(parafuso autobrocante; cópia OCR)", "1995-09"),
         doc("DIN-914", f"{OCR}/ISO-4027-1980.pdf", "DIN 914:1980 — Hexagon socket set screws with cone point (ISO 4027 modified) "
             "(parafuso sem cabeça/prisioneiro com sextavado interno e ponta cônica; cópia OCR)", "1980-12"),
         doc("DIN-EN-ISO-4026", f"{A}/DIN EN ISO 4026 2003 - Hexagon socket set screws with flat point.pdf",
             "DIN EN ISO 4026:2004 — Gewindestifte mit Innensechskant mit Kegelstumpf / Hexagon socket set screws with flat point (ISO 4026:2003) "
             "(parafuso sem cabeça com sextavado interno e ponta plana; versão alemã; substitui DIN 913:1980)", "2003 (DIN EN ISO 4026:2004-05)"),
         doc("DIN-EN-ISO-7050", f"{A}/din-en-iso-7050-2011.pdf",
             "DIN EN ISO 7050:2011 — Senk-Blechschrauben mit Kreuzschlitz / Cross-recessed countersunk (flat) head tapping screws (ISO 7050:2011) "
             "(parafuso autoatarraxante cabeça escareada, fenda cruzada; versão alemã)", "2011 (DIN EN ISO 7050:2011-11)"),
         doc("DIN-EN-ISO-2702", f"{A}/din-en-iso-2702-2011.pdf",
             "DIN EN ISO 2702:2011 — Heat-treated steel tapping screws — Mechanical properties (ISO 2702:2011) "
             "(propriedades mecânicas de parafusos autoatarraxantes de aço temperado)", "2011 (DIN EN ISO 2702:2011-08)"),
         doc("DIN-934", f"{OCR}/DIN-934-1987.pdf", "DIN 934:1987 — Hexagon nuts with metric coarse and fine pitch thread — Product grades A and B "
             "(porca sextavada; a norma manda usá-la junto com ISO 4032, 8673 e 8674; cópia OCR)", "1987-10"),
         doc("DIN-979", f"{OCR}/DIN-979-1987.pdf", "DIN 979:1987 — Hexagon thin slotted nuts and castle nuts with metric coarse and fine pitch thread — "
             "Product grades A and B (porca castelo baixa; cópia OCR)", "1987-10"),
         doc("DIN-25201-2", f"{A}/DIN 25201-2 2006 - Design guide for railway vehicles and their components Bolted joints Part 2 Design Mecahanical applicatio.pdf",
             "DIN 25201-2:2006 — Konstruktionsrichtlinie für Schienenfahrzeuge und deren Komponenten — Schraubenverbindungen — Teil 2: Konstruktion — "
             "Maschinenbauliche Anwendungen (diretriz de projeto de uniões parafusadas em veículos ferroviários — aplicações mecânicas; versão alemã)", "2006-04"),
     ]},

    {"id": "din-arruelas-rebites-condicoes-tecnicas", "titulo": "DIN — arruelas, rebites e condições técnicas de fornecimento de fixadores", "categoria": "Parafusos e fixação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de arruelas (DIN 127 B pressão, DIN 6797 dentada, DIN EN ISO 7090 lisa chanfrada), rebites cegos (DIN 7337) "
               "e da série DIN 267 de condições técnicas de fornecimento de fixadores (parte 2 execução e tolerâncias, 3 conversão de classes "
               "de resistência, 10 galvanização a quente, 27 parafusos com revestimento adesivo/trava-rosca).",
     "docs": [
         doc("DIN-127", f"{A}/ARRUELA DE PRESSÃO MÉDIA - DIN 127 B.pdf",
             "Arruela de pressão média DIN 127 B — tabela de fabricante (dimensões em polegada e métricas; não é o texto da norma)", "s/d (tabela de fabricante)"),
         doc("DIN-6797", f"{OCR}/DIN-6797-1988.pdf", "DIN 6797:1988 — Toothed lock washers (arruela dentada; cópia OCR)", "1988-07"),
         doc("DIN-EN-ISO-7090", f"{OCR}/ISO-7090-2000.pdf", "DIN EN ISO 7090:2000 — Plain washers, chamfered — Normal series — Product grade A (ISO 7090:2000) "
             "(arruela lisa chanfrada; substitui DIN 125-1 e 125-2; cópia OCR)", "2000 (DIN EN ISO 7090:2000-11)"),
         doc("DIN-7337", f"{OCR}/DIN-7337-1991.pdf", "DIN 7337:1991 — Break mandrel blind rivets (rebite cego com haste de ruptura, cabeça chata e escareada; cópia OCR)", "1991-08"),
         doc("DIN-267-2", f"{OCR}/DIN-267-2-1984.pdf", "DIN 267-2:1984 — Fasteners — Technical delivery conditions — Design and dimensional accuracy "
             "(execução e exatidão dimensional, tolerâncias de rosca; cópia OCR)", "1984-11"),
         doc("DIN-267-3", f"{A}/DIN 267 3 1983 - FASTENERS TECHNICAL DELIVERY CONDITIONS PROPERTY CLASSES FOR CARBON STEEL AND ALLOY STEEL BOLTS.pdf",
             "DIN 267-3:1983 — Fasteners — Technical delivery conditions — Property classes for carbon steel and alloy steel bolts and screws — "
             "Conversion of property classes (conversão das classes de resistência antigas para as da DIN ISO 898-1)", "1983-08"),
         doc("DIN-267-10", f"{OCR}/DIN-267-10-1988.pdf", "DIN 267-10:1988 — Fasteners — Technical delivery conditions — Hot-dip galvanized parts "
             "(fixadores galvanizados a quente M6–M36, limites de rosca antes da galvanização; cópia OCR)", "1988-01"),
         doc("DIN-267-27", f"{A}/DIN 267 27 2004 - TECHNICAL DELIVERY CONDITIONS FOR FASTENERS ADHESIVE-COATED STEEL SCREW, BOLTS AND STUDS.pdf",
             "DIN 267-27:2004 — Technical delivery conditions for fasteners — Part 27: Adhesive-coated steel screws, bolts and studs "
             "(parafusos com revestimento adesivo/trava-química pré-aplicada)", "2004-01"),
     ]},

    {"id": "din-aneis-chavetas-estrias", "titulo": "DIN — anéis de retenção, chavetas, travas de rolamento e eixos estriados", "categoria": "Engrenagens e transmissão", "agrupar": "documento",
     "resumo": "Tabelas e figuras de elementos de ligação eixo-cubo: anéis elásticos de retenção para eixos (DIN 471) e furos (DIN 472), "
               "arruelas e chapas de trava de porcas de rolamento (DIN 5406), chavetas paralelas e rasgos (DIN 6885 folhas 1–3) "
               "e eixos estriados com flanco evolvente (DIN 5480-1).",
     "docs": [
         doc("DIN-471", f"{OCR}/DIN-471-1981.pdf", "DIN 471:1981 — Circlips (retaining rings) for shafts — Normal type and heavy type (anel elástico para eixo; cópia OCR)", "1981-09"),
         doc("DIN-472", f"{OCR}/DIN-472-1981.pdf", "DIN 472:1981 — Circlips (retaining rings) for bores — Normal type and heavy type (anel elástico para furo; cópia OCR)", "1981-09"),
         doc("DIN-5406", f"{OCR}/DIN-5406-1993.pdf", "DIN 5406:1993 — Lockwashers and locking plates for use with rolling bearings "
             "(arruela de trava MB/MBL e chapa de trava para porca de rolamento; cópia OCR)", "1993-02"),
         doc("DIN-6885-1", f"{OCR}/DIN-6885-1968.pdf", "DIN 6885 Sheet 1:1968 — Drive type fastenings without taper action — Feather keys, keyways, deep pattern "
             "(chaveta paralela forma alta e rasgos; tradução inglesa da folha 1; cópia OCR)", "1968-08"),
         doc("DIN-6885", f"{OCR}/DIN-6885-1968-2.pdf", "DIN 6885 Blatt 1–3 — Mitnehmerverbindungen ohne Anzug — Paßfedern, Nuten "
             "(chavetas paralelas e rasgos: folha 1 forma alta, folha 2 forma alta para máquinas-ferramenta, folha 3 forma baixa; originais em alemão, "
             "2 págs. cada, páginas giradas; cópia OCR)",
             "Blatt 1: 1968-08; Blatt 2: 1967-12; Blatt 3: 1956-02"),
         doc("DIN-5480-1", f"{A}/DIN 5480-1 2006 - SPLINED CONNECTIONS WITH INVLOUTE SPLINES BASED ON REFERENCE DIAMETERS - PRINCIPLES.pdf",
             "DIN 5480-1:2006 — Splined connections with involute splines based on reference diameters — Part 1: Principles "
             "(eixo estriado com flanco evolvente — fundamentos; substitui DIN 5480-1:1991 e 5480-14:1986)", "2006-03"),
     ]},

    {"id": "din-engrenagens", "titulo": "DIN — engrenagens cilíndricas: perfil de referência, conceitos, tolerâncias e folga", "categoria": "Engrenagens e transmissão", "agrupar": "documento",
     "resumo": "Tabelas e figuras de DIN 867 (perfil de referência da cremalheira), DIN 3960 (conceitos e parâmetros de engrenagens cilíndricas "
               "de dentes evolventes), DIN 3961 (tolerâncias de dentes), DIN 3964 (desvios de distância entre eixos e posição de eixos na carcaça) "
               "e DIN 3967 (folga entre flancos, afastamentos e tolerâncias de espessura de dente).",
     "docs": [
         doc("DIN-867", f"{OCR}/DIN-867-1986.pdf", "DIN 867:1986 — Basic rack tooth profiles for involute teeth of cylindrical gears for general engineering and heavy engineering "
             "(perfil de referência; cópia OCR)", "1986-02"),
         doc("DIN-3960", f"{OCR}/DIN-3960-1987.pdf", "DIN 3960:1987 — Concepts and parameters associated with cylindrical gears and cylindrical gear pairs with involute teeth "
             "(definições, fórmulas e parâmetros de engrenagens cilíndricas; cópia OCR)", "1987-03"),
         doc("DIN-3961", f"{OCR}/DIN-3961-1978.pdf", "DIN 3961:1978 — Tolerances for cylindrical gear teeth — Bases (tolerâncias de dentes, famílias de tolerância; cópia OCR)", "1978-08"),
         doc("DIN-3964", f"{OCR}/DIN-3964-1980.pdf", "DIN 3964:1980 — Deviations of shaft centre distances and shaft position tolerances of casings for cylindrical gears "
             "(desvio de distância entre eixos e paralelismo na carcaça; cópia OCR)", "1980-11"),
         doc("DIN-3967", f"{A}/DIN 3967 1978 - BACKLASH TOOTH THICKNESS ALLOWANCES.pdf",
             "DIN 3967:1978 — System of gear fits — Backlash, tooth thickness allowances, tooth thickness tolerances — Principles "
             "(sistema de ajustes de engrenagens: folga entre flancos e afastamentos de espessura de dente)", "1978-08"),
     ]},

    {"id": "din-acos-molas-beneficiamento", "titulo": "DIN — aços para beneficiamento e para molas", "categoria": "Materiais", "agrupar": "documento",
     "resumo": "Tabelas de composição química, propriedades mecânicas, temperabilidade e tratamento térmico de DIN EN 10083-3 (aços-liga para "
               "têmpera e revenimento), DIN EN 10089 (aços laminados a quente para molas temperadas e revenidas) e DIN 17222 (fitas laminadas a frio para molas).",
     "docs": [
         doc("DIN-EN-10083-3", f"{A}/DIN 10083-3 2007 STEELS FOR QUENCHING AND TEMPERING.pdf",
             "DIN EN 10083-3:2007 — Steels for quenching and tempering — Part 3: Technical delivery conditions for alloy steels "
             "(aços-liga para beneficiamento, ex. 42CrMo4, 34CrNiMo6)", "2007 (DIN EN 10083-3:2007-01)"),
         doc("DIN-EN-10089", f"{OCR}/DIN-10089-2003.pdf", "DIN EN 10089:2003 — Hot-rolled steels for quenched and tempered springs — Technical delivery conditions "
             "(aços para molas, ex. 51CrV4, 54SiCr6; substitui DIN 17221:1988; cópia OCR)", "2002 (DIN EN 10089:2003-04)"),
         doc("DIN-17222", f"{OCR}/DIN-17222-1979.pdf", "DIN 17222:1979 — Cold rolled steel strips for springs — Technical conditions of delivery "
             "(fitas de aço laminadas a frio para molas; cópia OCR)", "1979-08"),
     ]},

    {"id": "din-conexoes-tubo-abracadeiras", "titulo": "DIN — conexões para tubo (anilha) e abraçadeiras de mangueira", "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de conexões de compressão com anel de corte DIN 2353 / ISO 8434-1 (catálogo de fabricante, tubos de 4 a 42 mm) "
               "e de abraçadeiras de mangueira DIN 3017-1 (rosca sem-fim, forma A) e DIN 3017-2 (com mordentes/orelhas de aperto).",
     "docs": [
         doc("DIN-2353", f"{A}/DIN 2353 Tube Fittings.pdf",
             "HSME — Catalog No. DIN-3: DIN 2353 Tube Fittings (DIN 2353 & ISO 8434-1, tubo métrico 4–42 mm OD) "
             "(catálogo de fabricante de conexões com anilha/anel de corte, válvulas de retenção e esfera; não é o texto da norma)", "2015-07 (catálogo)"),
         doc("DIN-3017-1", f"{OCR}/DIN-3017-1-1998.pdf", "DIN 3017-1:1998 — Hose clamps — Part 1: Clamps with worm gear drive — Shape A "
             "(abraçadeira de mangueira com rosca sem-fim; tradução inglesa; cópia OCR)", "1998-05"),
         doc("DIN-3017-2", f"{OCR}/DIN-3017-2-2002.pdf", "DIN 3017-2:2002 — Schlauchschellen — Teil 2: Schellen mit Spannbacken / Hose clamps — Part 2: Clamps with fastening lugs "
             "(abraçadeira com orelhas de aperto e parafuso; versão alemã; cópia OCR)", "2002-06"),
     ]},
]
