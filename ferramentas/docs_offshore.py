"""Configuração das fichas de "tabelas e figuras" dos documentos offshore/óleo e gás de referencias/ — API, DNV, ABS, BV, IACS e IOGP
(lido por ferramentas/gerar_docs.py).

Mesmo formato de FICHAS em gerar_docs.py. Documentos escaneados usam a cópia OCR de referencias/ocr/ (mesmas páginas).
Códigos/edições conferidos na 1ª página de cada PDF (OCR da 1ª página nos escaneados). Títulos em inglês, como no documento;
descrição em português entre parênteses. Duplicatas, edições superadas e fragmentos sem conteúdo ficam fora, em EXCLUIDOS.
"""

API = "referencias/extraido/API"
DNV = "referencias/extraido/DNV"
ABS = "referencias/extraido/ABS"
BV = "referencias/extraido/BV"
OCR = "referencias/ocr"


def doc(id_, arq, titulo, edicao, escopo="", orgao="API"):
    return {"id": id_, "arq": arq, "titulo": titulo, "edicao": edicao, "escopo": escopo, "orgao": orgao}


EXCLUIDOS = {
    f"{API}/16d.pdf":
        "duplicata escaneada: API Spec 16D 2ª ed. (jul/2004, reafirmada ago/2013), mesmas 110 págs.; usada a cópia com texto "
        "'API 16D CONTROL SYSTEM FOR WELL CONTROL EQUIPMENT (2)'",
    f"{API}/17D_e2.pdf":
        "duplicata danificada: PDF não abre (árvore de páginas corrompida); 268 páginas = API Spec 17D 2ª ed. (mai/2011); usada a cópia com texto "
        "'API 17D ED2nd 2011 ISO 13628-4'",
    f"{API}/API RP 14C 2001 - Recommended pratctice for analysis, design, installation, and testing of basic surface safety systems for offshore production~90256c.pdf":
        "duplicata escaneada: API RP 14C 7ª ed. (mar/2001); usada a cópia com texto (~4ef62a, reafirmada mar/2007)",
    f"{API}/API 570 - Piping Inspection Code.pdf":
        "fragmento: só 4 págs. (resumo de escopo e sumário do API 570), sem tabelas nem figuras",
    f"{API}/API 1509 Appendix F 2011 - Guidelines for SAE Viscosity-Grade Engine Testing.pdf":
        "fora de escopo: só o Apêndice F (jan/2011) do API 1509 — licenciamento de óleo de motor (critérios de ensaio por grau SAE); "
        "não é norma de projeto/fabricação",
    f"{ABS}/ABS - ERGONOMIC NOTATIONS SEPTEMBER 2021.pdf":
        "coberta por outra cópia: ABS Guide for Ergonomic Notations, set/2021, já em normas.json (id ABS-ERGO, cópia de T:) e incorporado às fichas de acesso",
    f"{ABS}/ABS-Machinery Rules-July-2007.pdf":
        "edição superada: ABS Rules for Building and Classing Steel Vessels 2007 — Part 4 Vessel Systems and Machinery; usada a edição "
        "jul/2022 (Rules for Building and Classing Marine Vessels, Part 4 — mesma Parte, título novo)",
    f"{DNV}/DNV-RP-H103.pdf":
        "edição superada: DNV-RP-H103 abr/2011 (Modelling and Analysis of Marine Operations); a DNVGL-RP-N103 jul/2017 do acervo "
        "diz 'supersedes the February 2014 edition of DNV-RP-H103' — usada a RP-N103",
}


FICHAS = [
    # ------------------------------------------------------------------ API
    {"id": "api-pocos-cabeca-bop-submarino", "titulo": "API — cabeça de poço, árvore de natal, BOP, choke/kill e equipamento submarino",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras das normas API de equipamento de controle de poço: Spec 6A (cabeça de poço e árvore de natal, flanges API), "
               "Std 6X (cálculo de equipamento de pressão), TR 6AF (capacidade de flanges API sob cargas combinadas), Spec 16A (equipamento "
               "drill-through), 16C (choke e kill), 16D (sistemas de controle de BOP/diverter), Std 53 (sistemas de BOP), Spec 17D "
               "(cabeça de poço e árvore submarinas) e TR 17TR7 (verificação e validação de conectores submarinos).",
     "docs": [
         doc("API-6A", f"{API}/API 6A ED21th 2018 ISO 10423 2020 - SPECIFICATION FOR WELLHEAD AND CHRISTMAS TREE EQUIPMENT.pdf",
             "API Spec 6A — Specification for Wellhead and Tree Equipment (cabeça de poço e árvore de natal; flanges, conexões, PSL, classes de material)",
             "21ª ed., nov/2018 + Errata 1 (abr/2019), Errata 2 (jun/2020) e Addendum 1 (jul/2020)"),
         doc("API-6X", f"{API}/API STD 6X 2019 2nd Ed - Design Calculations for Pressure-Containing Equipment.pdf",
             "API Std 6X — Design Calculations for Pressure-containing Equipment (cálculo de equipamento de contenção de pressão)", "2ª ed., fev/2019"),
         doc("API-TR-6AF", f"{API}/API TR 6AF 2008 - Capabilities of API Flanges Under Combinations of Load.pdf",
             "API TR 6AF — Technical Report on Capabilities of API Flanges Under Combinations of Load (capacidade de flanges API 6A/6BX sob pressão, "
             "tração e momento)", "3ª ed., set/2008"),
         doc("API-16A", f"{API}/16A4thEd.pdf",
             "API Spec 16A — Specification for Drill-through Equipment (BOP, conectores e carretéis drill-through; MINUTA para votação do comitê, "
             "não a edição publicada)", "4ª ed., minuta (ballot draft) 2015"),
         doc("API-16C", f"{OCR}/API-16C.pdf",
             "API Spec 16C — Specification for Choke and Kill Systems (sistemas de choke e kill; cópia OCR)", "1ª ed., jan/1993 (ANSI/API Spec 16C-93)"),
         doc("API-16D", f"{API}/API 16D CONTROL SYSTEM FOR WELL CONTROL EQUIPMENT (2).pdf",
             "API Spec 16D — Specification for Control Systems for Drilling Well Control Equipment and Control Systems for Diverter Equipment "
             "(sistemas de controle de BOP e diverter; acumuladores)", "2ª ed., jul/2004, reafirmada ago/2013"),
         doc("API-53", f"{API}/API 53 2012 - BLOWOUT PREVENTION EQUIPMENT SYSTEMS FOR DRILLING WELLS (2).pdf",
             "API Std 53 — Blowout Prevention Equipment Systems for Drilling Wells (sistemas de BOP: instalação, testes e manutenção)", "4ª ed., nov/2012"),
         doc("API-17D", f"{API}/API 17D ED2nd 2011 ISO 13628-4 - DESIGN AND OPERATION OF SUBSEA PRODUCTION SYSTEMS - SUBSEA WEEL HEAD AND TREE EQUIPMENT.pdf",
             "ANSI/API Spec 17D — Design and Operation of Subsea Production Systems — Subsea Wellhead and Tree Equipment "
             "(cabeça de poço e árvore de natal molhada; idêntica à ISO 13628-4)", "2ª ed., mai/2011"),
         doc("API-17TR7", f"{API}/API 17TR7 1st 2017 - VERIFICATION AND VALIDATION OF SUBSEA CONNECTORS.pdf",
             "API TR 17TR7 — Verification and Validation of Subsea Connectors (verificação e validação de conectores submarinos)", "1ª ed., abr/2017"),
     ]},

    {"id": "api-tubulares-perfuracao", "titulo": "API — revestimento, coluna de perfuração, roscas e equipamento de sonda",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras das normas API de tubulares e equipamento de perfuração: Spec 5CT (revestimento e coluna de produção), "
               "5D (tubo de perfuração), 5B (roscas de revestimento, tubing e line pipe — rosqueamento e calibração), 7-1 e 7-2 (elementos da "
               "coluna e roscas com ressalto rotativo — só os addenda), 7K (equipamento de perfuração e intervenção), 8C (equipamento de "
               "içamento de sonda PSL 1/2), 10D (centralizadores de mola) e uma apresentação sobre inspeção de tubos (AADE 2012).",
     "docs": [
         doc("API-5CT", f"{OCR}/API-5CT-2005.pdf",
             "API Spec 5CT — Specification for Casing and Tubing (revestimento e tubing; idêntica à ISO 11960:2004; cópia OCR)",
             "8ª ed., jul/2005 (vigência jan/2006)"),
         doc("API-5D", f"{API}/API 5D ED4th 2000 - SPECIFICATION FOR DRILL PIPE.pdf",
             "API Spec 5D — Specification for Drill Pipe (tubo de perfuração)", "4ª ed., ago/1999 (vigência jan/2000)"),
         doc("API-5B", f"{OCR}/68894235-API-Specification-5B-15th-Ed-Apr-2008-Specification-for-Threading-Gauging-and-Thread-Inspection-of-Casing-Tubing-and-Line-Pipe-Threads-2008.pdf",
             "API Spec 5B — Specification for Threading, Gauging and Thread Inspection of Casing, Tubing, and Line Pipe Threads "
             "(roscas API de revestimento/tubing/line pipe; cópia OCR — o texto do PDF original tem fonte com codificação ilegível)",
             "15ª ed., abr/2008 (vigência out/2008)"),
         doc("API-7-1-AD3", f"{API}/API Spec 7-1 2006 Addendum 3 2011 - Specification for Rotary Drill Stem Elements.pdf",
             "ANSI/API Spec 7-1 — Specification for Rotary Drill Stem Elements — Addendum 3 (elementos da coluna de perfuração: válvulas de kelly, "
             "estabilizadores…; a cópia contém SÓ o Addendum 3, não a norma completa)", "1ª ed., mar/2006 — Addendum 3, abr/2011"),
         doc("API-7-2-AD1", f"{API}/API Spec 7-2 2008 Addendum 1 2010 - Threading and Gauging of Rotary Shouldered Thread Connections.pdf",
             "ANSI/API Spec 7-2 — Threading and Gauging of Rotary Shouldered Thread Connections — Addendum 1 (roscas com ressalto rotativo; "
             "a cópia contém SÓ o Addendum 1 — tabelas e figuras revisadas)", "1ª ed., jun/2008 — Addendum 1, dez/2010"),
         doc("API-7K", f"{API}/API SPEC 7K 2004 - SPECIFICATION FOR DRILLING AND WELL SERVICING EQUIPMENT.pdf",
             "API Spec 7K — Specification for Drilling and Well Servicing Equipment (mesa rotativa, cunhas, mangueiras de lama, bombas…)",
             "3ª ed., out/2001 + Addendum 1 (set/2002) e Addendum 2 (abr/2004)"),
         doc("API-8C", f"{API}/API SPEC 8C 2012 - DRILLING AND PRODUCTION HOISTING EQUIPMENT PSL1 AND PSL2.pdf",
             "API Spec 8C — Drilling and Production Hoisting Equipment (PSL 1 and PSL 2) (equipamento de içamento de sonda: ganchos, elevadores, "
             "links, swivel, blocos)", "5ª ed., abr/2012"),
         doc("API-10D", f"{OCR}/API-10D-1995.pdf",
             "API Spec 10D — Specification for Bow-Spring Casing Centralizers (centralizadores de revestimento de mola; contém a ISO 10427:1993; cópia OCR)",
             "5ª ed., jan/1995"),
         doc("API-PIPE-INSP-2012", f"{OCR}/API-Standards-for-Pipe-Inspections-2012-AADE-NOV-2012.pdf",
             "API Standards for Pipe Inspections — H. Prejean (NOV), AADE Denver (APRESENTAÇÃO sobre Spec 5DP, 7-1, 7-2 e inspeção de "
             "drill pipe; não é texto de norma; cópia OCR)", "set/2012 (apresentação)"),
     ]},

    {"id": "api-tubos-valvulas-solda-dutos", "titulo": "API — tubos para dutos, válvulas, ensaio de fogo e soldagem de dutos",
     "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de API Spec 5L (tubos para dutos — line pipe, PSL 1/2), Spec 6D (válvulas de duto — só um excerto), "
               "Std 600 (válvulas gaveta de aço), Std 608 (válvulas esfera), Std 607 e 6FA (ensaio de fogo de válvulas) e Std 1104 "
               "(soldagem de dutos e Apêndice A — critérios alternativos de aceitação de soldas circunferenciais).",
     "docs": [
         doc("API-5L", f"{API}/API 5L 2013 - SPECIFICATION FOR LINE PIPE.pdf",
             "API Spec 5L — Specification for Line Pipe (tubos para dutos PSL 1 e PSL 2: química, tração, dimensões, tolerâncias, ensaios)",
             "45ª ed., dez/2012 (vigência jul/2013)"),
         doc("API-6D", f"{API}/API 6D 2016 - Specification for Pipeline and Piping Valves.pdf",
             "API Spec 6D — Specification for Pipeline and Piping Valves (EXCERTO de 2 págs.: 5.8 alívio de cavidade, 5.9 drenos/respiros/linhas de selante)",
             "excerto (cópia de 2016)"),
         doc("API-6D-2015", f"{OCR}/API-6D-2015.pdf",  # texto completo (escaneado) — a triagem o tinha como superado pelo excerto
             "API Spec 6D — Specification for Pipeline and Piping Valves (texto completo; cópia OCR)", "2015 (conforme o nome do arquivo)"),
         doc("API-600", f"{API}/API 600 9th - Steel Gate Valves Flanged and Butt-Welding Ends.pdf",
             "API Std 600 — Steel Gate Valves — Flanged and Butt-welding Ends, Bolted Bonnets (válvula gaveta de aço; espessuras mínimas, haste)",
             "12ª ed., mar/2009 (vigência set/2009)"),
         doc("API-608", f"{OCR}/API-608.pdf",
             "API Std 608 — Metal Ball Valves — Flanged, Threaded, and Welding End (válvula esfera metálica; cópia OCR)", "2ª ed., set/1995"),
         doc("API-607", f"{API}/api-607-2016-fire-test-for-quarter-turn-valves-and-soft-seated-valves.pdf",
             "API Std 607 — Fire Test for Quarter-turn Valves and Valves Equipped with Nonmetallic Seats (ensaio de fogo de válvulas de 1/4 de volta)",
             "7ª ed., jun/2016"),
         doc("API-6FA", f"{API}/api-6fa4ed-2018-specification-for-fire-test-for-valves.pdf",
             "API Std 6FA — Standard for Fire Test for Valves (ensaio de fogo de válvulas API 6A/6D)", "4ª ed., jun/2018"),
         doc("API-1104", f"{API}/API 1104 ED20th 2005 - WELDING OF PIPELINES AND RELATED FACILITIES.pdf",
             "API Std 1104 — Welding of Pipelines and Related Facilities (qualificação de procedimento e soldador, END e aceitação de soldas de dutos)",
             "20ª ed., nov/2005"),
         doc("API-1104-AD2007", f"{API}/API 1104 - WELDING OF PIPELINES AND RELATED FACILITIES - APPENDIX A - ALTERNATIVE ACCEPTANCE STANDARDS FOR GIRTH WELDS (2).pdf",
             "API Std 1104 — Errata/Addendum: Appendix A — Alternative Acceptance Standards for Girth Welds (substitui o Apêndice A da 20ª ed.; "
             "critérios de aceitação por adequação ao uso/ECA)", "jul/2007 (errata/addendum da 20ª ed.)"),
     ]},

    {"id": "api-inspecao-alivio-pressao", "titulo": "API — inspeção de vasos e tanques em serviço e dispositivos de alívio de pressão",
     "categoria": "Vasos de pressão e caldeiras", "agrupar": "documento",
     "resumo": "Tabelas e figuras de API 510 (inspeção, reavaliação, reparo e alteração de vasos de pressão em serviço), API 653 (inspeção, "
               "reparo, alteração e reconstrução de tanques) e API RP 520 Parte I (dimensionamento e seleção de dispositivos de alívio de pressão).",
     "docs": [
         doc("API-510", f"{API}/API 510 2006 - Pressure Vessel Inspection Code.pdf",
             "API 510 — Pressure Vessel Inspection Code: In-Service Inspection, Rating, Repair, and Alteration (inspeção de vasos em serviço)",
             "9ª ed., jun/2006"),
         doc("API-653", f"{API}/API 653 2003 - Tank Inspection, Repair, Alteration and Reconstruction.pdf",
             "API Std 653 — Tank Inspection, Repair, Alteration, and Reconstruction (inspeção e reparo de tanques de armazenamento)",
             "3ª ed., dez/2001 + Addendum 1 (set/2003)"),
         doc("API-RP-520-I", f"{OCR}/API-RP-520-2002.pdf",
             "API RP 520 Part I — Sizing, Selection, and Installation of Pressure-Relieving Devices in Refineries — Part I: Sizing and Selection "
             "(dimensionamento de válvulas de segurança e alívio e discos de ruptura; cópia OCR)", "7ª ed., jan/2000"),
         doc("API-RP-520-II", f"{OCR}/API-RP-520-II.pdf",  # outra parte da norma (instalação), não edição antiga da Parte I
             "API RP 520 Part II — Sizing, Selection, and Installation of Pressure-Relieving Devices — Part II: Installation (cópia OCR)",
             "s/d (ver o PDF)"),
     ]},

    {"id": "api-equipamentos-rotativos", "titulo": "API — bombas centrífugas, selos mecânicos e redutores",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras de API Std 610 (bombas centrífugas para petróleo, petroquímica e gás natural), Std 682 (sistemas de selagem "
               "de eixo — selos mecânicos e planos de selagem) e Std 613 (redutores/engrenagens de uso especial).",
     "docs": [
         doc("API-610", f"{OCR}/API-610-2010.pdf",
             "API Std 610 — Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries (idêntica à ISO 13709:2009; cópia OCR — a capa "
             "escaneada é a da 10ª ed., mas o texto é da 11ª: cita IEC 60034-2-1:2007)", "11ª ed., set/2010"),
         doc("API-682", f"{API}/API 682 2014 4th Ed - Pumps - Shaft Sealing Systems for Centrifugal and Rotary Pumps.pdf",
             "API Std 682 — Pumps — Shaft Sealing Systems for Centrifugal and Rotary Pumps (selos mecânicos e planos de selagem)", "4ª ed., mai/2014"),
         doc("API-613", f"{API}/API 613 - SPECIAL PURPOSE GEAR UNITS FOR PETROLEUM, CHEMICAL AND GAS INDUSTRY SERVICES (2).pdf",
             "API Std 613 — Special Purpose Gear Units for Petroleum, Chemical and Gas Industry Services (redutores de uso especial)", "5ª ed., fev/2003"),
     ]},

    {"id": "api-seguranca-processo-offshore", "titulo": "API — sistemas de segurança e análise de riscos de plataformas de produção",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras de API RP 14C (análise, projeto, instalação e teste de sistemas básicos de segurança de superfície — SAT, "
               "SAFE chart, dispositivos de segurança por componente) e API RP 14J (projeto e análise de perigos de instalações de produção offshore).",
     "docs": [
         doc("API-RP-14C", f"{API}/API RP 14C 2001 - Recommended pratctice for analysis, design, installation, and testing of basic surface safety systems for offshore production~4ef62a.pdf",
             "API RP 14C — Recommended Practice for Analysis, Design, Installation, and Testing of Basic Surface Safety Systems for Offshore Production Platforms",
             "7ª ed., mar/2001, reafirmada mar/2007"),
         doc("API-RP-14J", f"{API}/API RP 14J ED2nd 2001 - RECOMMENDED PRACTICE FOR DESIGN AND HAZARDS ANALYSIS FOR OFFSHORE PRODUCTION FACILITIES.pdf",
             "API RP 14J — Recommended Practice for Design and Hazards Analysis for Offshore Production Facilities", "2ª ed., mai/2001"),
     ]},

    # ------------------------------------------------------------------ DNV
    {"id": "dnv-estruturas-offshore", "titulo": "DNV — projeto estrutural offshore (WSD), fadiga, cargas acidentais e ambientais",
     "categoria": "Estruturas e fabricação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de DNVGL-OS-C201 (projeto estrutural de unidades offshore — método WSD), DNVGL-RP-C203 (fadiga de estruturas "
               "de aço offshore: curvas S-N, SCF de juntas tubulares), DNV-RP-C204 (projeto contra cargas acidentais: impacto, explosão, incêndio) "
               "e DNV-RP-C205 (condições e cargas ambientais: onda, vento, corrente).",
     "docs": [
         doc("DNV-OS-C201", f"{DNV}/DNVGL-OS-C201 2017 - Structural Design of Offshore Units - WSD Method.pdf",
             "DNVGL-OS-C201 — Structural design of offshore units — WSD method", "jul/2017", orgao="DNV"),
         doc("DNV-RP-C203", f"{DNV}/DNVGL-RP-C203 2019 Amended 2020 - Fatigue Design of Offshore Steel Structures.pdf",
             "DNVGL-RP-C203 — Fatigue design of offshore steel structures", "set/2019, emenda jan/2020", orgao="DNV"),
         doc("DNV-RP-C204", f"{DNV}/DNV-RP-C204.pdf",
             "DNV-RP-C204 — Structural design against accidental loads", "set/2019, emenda set/2021", orgao="DNV"),
         doc("DNV-RP-C205", f"{DNV}/DNV-RP-C205 2014 - Environmental Conditions and Environmental Loads.pdf",
             "DNV-RP-C205 — Environmental Conditions and Environmental Loads (cópia impressa de slidepdf.com)", "abr/2014", orgao="DNV"),
     ]},

    {"id": "dnv-operacoes-maritimas-icamento", "titulo": "DNV — operações marítimas, lastro/estabilidade e equipamentos de içamento",
     "categoria": "Içamento e movimentação de carga", "agrupar": "documento",
     "resumo": "Tabelas e figuras de DNV-OS-H101 (operações marítimas — geral: períodos de referência, limites meteoceanográficos, fatores alfa), "
               "DNV-OS-H102 (operações marítimas — cargas de projeto e fabricação), DNVGL-RP-N103 (modelagem e análise de operações marítimas: "
               "içamento em zona de splash, coeficientes hidrodinâmicos), DNV-RP-H104 (lastro, estabilidade e estanqueidade em operações) "
               "e DNV Standard for Certification 2.22 (equipamentos de içamento: guindastes offshore, fatores dinâmicos).",
     "docs": [
         doc("DNV-OS-H101", f"{DNV}/DNV OS-H101 2011 - MARINE OPERATIONS, GENERAL.pdf",
             "DNV-OS-H101 — Marine Operations, General", "out/2011", orgao="DNV"),
         doc("DNV-OS-H102", f"{DNV}/DNV-OS-H102.pdf",
             "DNV-OS-H102 — Marine Operations, Design and Fabrication", "jan/2012", orgao="DNV"),
         doc("DNV-RP-N103", f"{DNV}/DNVGL-RP-N103 2017 - Modelling and Analysis of Marine Operations.pdf",
             "DNVGL-RP-N103 — Modelling and analysis of marine operations (substitui a DNV-RP-H103)", "jul/2017", orgao="DNV"),
         doc("DNV-RP-H104", f"{DNV}/DNV-RP-H104.pdf",
             "DNV-RP-H104 — Ballast, Stability, and Watertight Integrity — Planning and Operating Guidance", "set/2011", orgao="DNV"),
         doc("DNV-2.22", f"{DNV}/DNV 2-22 - LIFTING APPLIANCES.pdf",
             "DNV Standard for Certification No. 2.22 — Lifting Appliances (guindastes e equipamentos de içamento)", "jun/2013", orgao="DNV"),
     ]},

    {"id": "dnv-dutos-processo-protecao-catodica", "titulo": "DNV — dutos submarinos, vãos livres, sistemas de processo e proteção catódica",
     "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de DNV-OS-F101 (sistemas de dutos submarinos), DNV-RP-F105 (dutos em vão livre — VIV e fadiga), "
               "DNV-OS-E201 (sistemas de processamento de óleo e gás) e DNV-RP-B401 (projeto de proteção catódica: densidades de corrente, "
               "anodos galvânicos).",
     "docs": [
         doc("DNV-OS-F101", f"{DNV}/DNV OS-F101 2000 - SUBMARINE PIPELINE SYSTEMS.pdf",
             "DNV-OS-F101 — Submarine Pipeline Systems", "2000, reimpressão com emendas e correções até jan/2003", orgao="DNV"),
         doc("DNV-RP-F105", f"{DNV}/DNV-RP-F105 2006 SPANNING oIPELINES.pdf",
             "DNV-RP-F105 — Free Spanning Pipelines", "fev/2006", orgao="DNV"),
         doc("DNV-OS-E201", f"{DNV}/DNV OS-E201 2005 - OIL AND GAS PROCESSING SYSTEMS.pdf",
             "DNV-OS-E201 — Oil and Gas Processing Systems", "out/2005", orgao="DNV"),
         doc("DNV-RP-B401", f"{DNV}/DNV-RP-B401.pdf",
             "DNV-RP-B401 — Cathodic Protection Design", "out/2010, emenda abr/2011", orgao="DNV"),
     ]},

    # ------------------------------------------------------------------ ABS
    {"id": "abs-mvr-parte-4-maquinas", "titulo": "ABS — Marine Vessel Rules, Parte 4: sistemas e máquinas (2022)",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras das ABS Rules for Building and Classing Marine Vessels, Parte 4 (jul/2022): motores e turbinas, eixos e "
               "propulsão, caldeiras e vasos de pressão, tubulação e sistemas de bombeamento, combate a incêndio, sistemas elétricos e automação.",
     "docs": [
         doc("ABS-MVR-4-2022", f"{ABS}/ABS 2022 - Rules for building and classing Marine vessels Part 4 Vessel systems and machinery.pdf",
             "ABS Rules for Building and Classing Marine Vessels — Part 4: Vessel Systems and Machinery", "jul/2022", orgao="ABS"),
     ]},

    {"id": "abs-materiais-soldagem-parte-2", "titulo": "ABS — Rules for Materials and Welding, Parte 2 (2023)",
     "categoria": "Materiais", "agrupar": "documento",
     "resumo": "Tabelas e figuras das ABS Rules for Materials and Welding — Part 2 (jul/2023): aços de casco e de alta resistência, "
               "forjados, fundidos, tubos, correntes, alumínio, ensaios de materiais, qualificação de soldagem e consumíveis.",
     "docs": [
         doc("ABS-MW-2-2023", f"{ABS}/ABS 2023 Rules for materials and welding Part 2.pdf",
             "ABS Rules for Materials and Welding — Part 2", "jul/2023", orgao="ABS"),
     ]},

    {"id": "abs-guias-offshore", "titulo": "ABS — guias: equipamentos de içamento, amarras de ancoragem, fatores humanos e dispersão de gás",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras dos guias ABS: Guide for Certification of Lifting Appliances (2021 — guindastes, fatores de projeto e ensaios), "
               "Guide for the Certification of Offshore Mooring Chain (2009 — graus R3–R5, ensaios de prova e ruptura), Guidance Notes on the "
               "Implementation of Human Factors Engineering into the Design of Offshore Installations (2014) e Guidance Notes on Gas Dispersion "
               "Studies of Gas Fueled Vessels (2019).",
     "docs": [
         doc("ABS-LIFT-2021", f"{ABS}/ABS 2021 - Guide for certification of lifting appliances.pdf",
             "ABS Guide for Certification of Lifting Appliances", "dez/2021", orgao="ABS"),
         doc("ABS-CHAIN-2009", f"{ABS}/ABS - GUIDE FOR THE CERTIFICATION OF OFFSHORE MOORING CHAIN.pdf",
             "ABS Guide for the Certification of Offshore Mooring Chain (amarras de ancoragem offshore)", "3ª ed., dez/2009", orgao="ABS"),
         doc("ABS-HFE-2014", f"{ABS}/ABS - GUIDANCE NOTES ON THE IMPLEMENTATION OF HUMAN FACTORS ENGINEERING INTO THE DESIGN OF OFFSHORE INSTALLATIONS.pdf",
             "ABS Guidance Notes on the Implementation of Human Factors Engineering into the Design of Offshore Installations", "jul/2014", orgao="ABS"),
         doc("ABS-GASDISP-2019", f"{ABS}/ABS 2019 - Guidance Notes on Gas Dispersion Studies of Gas Fueled Vessels.pdf",
             "ABS Guidance Notes on Gas Dispersion Studies of Gas Fueled Vessels (CFD de dispersão de gás ventilado por PRV)", "nov/2019", orgao="ABS"),
     ]},

    # ------------------------------------------------------------------ BV / IACS / IOGP
    {"id": "bv-nr445-unidades-offshore", "titulo": "Bureau Veritas NR445 — regras de classificação de unidades offshore (2025)",
     "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras das BV Rules for the Classification of Offshore Units NR445 (jun/2025): Parte A (classificação e vistorias), "
               "Parte B (segurança estrutural: estabilidade, cargas ambientais, estrutura), Parte C (instalações: máquinas e tubulação, elétrica, "
               "automação, segurança/incêndio) e Parte D (notações de serviço: FPSO/FSO e outras).",
     "docs": [
         doc("BV-NR445-A", f"{BV}/BV NR445 2025 Part A - Classification and Surveys.pdf",
             "BV NR445 — Rules for the Classification of Offshore Units — Part A: Classification and Surveys", "jun/2025 (NR445 A DT R09)", orgao="BV"),
         doc("BV-NR445-B", f"{BV}/BV NR445 2025 Part B - Structural Safety.pdf",
             "BV NR445 — Rules for the Classification of Offshore Units — Part B: Structural Safety", "jun/2025 (NR445 B DT R07)", orgao="BV"),
         doc("BV-NR445-C", f"{BV}/BV NR445 2025 Part C - Facilities.pdf",
             "BV NR445 — Rules for the Classification of Offshore Units — Part C: Facilities", "jun/2025 (NR445 C DT R07)", orgao="BV"),
         doc("BV-NR445-D", f"{BV}/BV NR445 2025 Part D - Service Notations.pdf",
             "BV NR445 — Rules for the Classification of Offshore Units — Part D: Service Notations", "jun/2025 (NR445 D DT R09)", orgao="BV"),
     ]},

    {"id": "iacs-iogp-qualidade-construcao-fatores-humanos", "titulo": "IACS Rec. 47 (qualidade de construção e reparo naval) e IOGP 454 (fatores humanos)",
     "categoria": "Estruturas e fabricação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de IACS Recommendation No. 47 — Shipbuilding and Repair Quality Standard (tolerâncias de fabricação, "
               "alinhamento, chanfros e soldas de estruturas navais, novas e em reparo) e IOGP Report 454 — Human factors engineering in projects.",
     "docs": [
         doc("IACS-REC-47", "referencias/extraido/IACS/IACS Rec 47 Rev 10 Corr 1 2025 - Shipbuilding and Repair Quality Standard.pdf",
             "IACS Rec. No. 47 — Shipbuilding and Repair Quality Standard (Part A: new construction; Part B: repair)",
             "Rev.10 set/2021, Corr.1 out/2025", orgao="IACS"),
         doc("IOGP-454", "referencias/extraido/IOGP/IOGP 454 2020.pdf",
             "IOGP Report 454 — Human factors engineering in projects", "2ª ed., jun/2020", orgao="IOGP"),
     ]},
]
