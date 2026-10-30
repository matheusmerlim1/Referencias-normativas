"""Configuração das fichas de "tabelas e figuras" das normas ABNT de referencias/ (lido por ferramentas/gerar_docs.py).

Mesmo formato de FICHAS em gerar_docs.py. Documentos escaneados usam a cópia OCR de referencias/ocr/ (mesmas páginas).
Títulos/edições conferidos na 1ª página de cada PDF (ou na imagem, nos escaneados).
Duplicatas e edições superadas ficam fora, em EXCLUIDOS.
"""

A = "referencias/extraido/ABNT"
OCR = "referencias/ocr"


def doc(id_, arq, titulo, edicao, escopo="", orgao="ABNT"):
    return {"id": id_, "arq": arq, "titulo": titulo, "edicao": edicao, "escopo": escopo, "orgao": orgao}


EXCLUIDOS = {
    f"{A}/NBR 5410 2004 - INSTALAÇÕES ELÉTRICAS DE BAIXA TENSÃO - EDIÇÃO COMENTADA.pdf":
        "duplicata: NBR 5410:2004 edição comentada (Target, com hiperlinks/comentários); usada a cópia simples da norma (217 p)",
    f"{A}/NBR 14039 2005 - INSTALAÇÕES ELÉTRICAS DE MÉDIA TENSÃO DE 10KV A 36.2KV - COMENTADA.pdf":
        "edição superada: é a NBR 14039:2003 comentada (Target), apesar do '2005' no nome; usada a 2ª edição 31.05.2005 (cópia OCR)",
    f"{A}/NBR 13715 1996 - ESTRUTURAS OFFSHORE - AMARRAS - REQUISITOS OFFSHORE STRUCTURES - STUD-LINK ANCHOR CHAIN - REQUIREMENTS.pdf":
        "edição superada: NBR 13715:1996 (amarras) substituída pela série NBR 13715 — usada a NBR 13715-2:2008 (versão corrigida 2009)",
    f"{A}/abnt-nbr-11900-1991pdf.pdf":
        "edição superada: NBR 11900:1991 (extremidades de laços de cabos de aço), substituída pela série NBR 11900 "
        "(partes 2 e 4 já em normas.json; parte 3 'Olhal com presilha' 2011 incluída aqui)",
}


FICHAS = [
    {"id": "abnt-desenho-tecnico", "titulo": "ABNT — desenho técnico, tolerâncias geométricas e rugosidade", "categoria": "Desenho técnico", "agrupar": "documento",
     "resumo": "Tabelas e figuras das normas ABNT de desenho técnico: NBR 10067, 10068, 10126, 10582, 12298, 13142, 13272, 14611, 8196, 8402, 8403 e 6492 "
               "(arquitetura), mais tolerâncias geométricas (NBR 6409, 14646) e rugosidade (NBR ISO 4287).",
     "docs": [
         doc("NBR-10067", f"{A}/NBR 10067 1995 - PRINCIPIOS GERAIS DE REPRESENTACAO EM DESENHO TECNICO.pdf", "Princípios gerais de representação em desenho técnico", "1995"),
         doc("NBR-10068", f"{A}/NBR 10068 - FOLHA DE DESENHO - LAYOUT E DIMENSÕES.pdf", "Folha de desenho — Leiaute e dimensões", "1987"),
         doc("NBR-10126", f"{A}/NBR 10126 1987 - COTAGEM EM DESENHO TECNICO.pdf", "Cotagem em desenho técnico", "1987"),
         doc("NBR-10582", f"{A}/NBR 10582 - APRESENTAÇÃO DA FOLHA PARA DESENHO TECNICO.pdf", "Apresentação da folha para desenho técnico", "1988"),
         doc("NBR-12298", f"{A}/NBR 12298 1995 - REPRESENTAÇÃO DE ÁREA DE CORTE POR MEIO DE HACHURAS EM DESENHO TÉCNICO.pdf",
             "Representação de área de corte por meio de hachuras em desenho técnico", "1995"),
         doc("NBR-13142", f"{A}/NBR 13142 - DESENHOS TÉCNICO - DOBRAMENTO DE CÓPIA.pdf", "Desenho técnico — Dobramento de cópia", "1999"),
         doc("NBR-13272", f"{A}/NBR 13272 - DESENHO TÉCNICO - ELABORAÇÃO DAS LISTAS DE ITENS.pdf", "Desenho técnico — Elaboração das listas de itens", "1999"),
         doc("NBR-14611", f"{OCR}/NBR-14611-2000.pdf", "Desenho técnico — Representação simplificada em estruturas metálicas (cópia OCR)", "2000"),
         doc("NBR-8196", f"{A}/NBR 8196 DESENHO TÉCNICO - EMPREGO DE ESCALAS.pdf", "Desenho técnico — Emprego de escalas", "1999"),
         doc("NBR-8402", f"{A}/NBR 8402 1994 - EXECUÇÃO DE CARACTER PARA ESCRITA EM DESENHO TÉCNICO.pdf", "Execução de caracter para escrita em desenho técnico", "1994"),
         doc("NBR-8403", f"{A}/NBR 8403 1984 - APLICACAO DE LINHAS EM DESENHOS - TIPOS DE LINHAS - LARGURAS DAS LINHAS.pdf",
             "Aplicação de linhas em desenhos — Tipos de linhas — Larguras das linhas", "1984"),
         doc("NBR-6492", f"{A}/NBR 6492 - REPRESENTAÇÃO DE PROJETOS DE ARQUITETURA.pdf", "Representação de projetos de arquitetura", "1994"),
         doc("NBR-6409", f"{A}/NBR 6409 - TOLERÂNCIAS GEOMÉTRICAS - TOLERÂNCIAS DE FORMA, ORIENTAÇÃO, POSIÇÃO E BATIMENTO.pdf",
             "Tolerâncias geométricas — Tolerâncias de forma, orientação, posição e batimento — Generalidades, símbolos, definições e indicações em desenho", "1997"),
         doc("NBR-14646", f"{A}/NBR 14646 2001 - TOLERANCIAS GEOMETRICAS - REQUISITOS DE MÁXIMO E REQUISITOS DE MÍNIMO MATERIAL.pdf",
             "Tolerâncias geométricas — Requisitos de máximo e requisitos de mínimo material", "2001"),
         doc("NBR-ISO-4287", f"{A}/NBR 4287 2002 - RUGOSIDADE MÉTODO DO PERFIL - TERMOS, DEFINIÇÕES E PARÂMETROS DA RUGOSIDADE.pdf",
             "Especificações geométricas do produto (GPS) — Rugosidade: Método do perfil — Termos, definições e parâmetros da rugosidade", "2002 (confirmada em 2005)"),
     ]},

    {"id": "abnt-eletrica-instalacoes", "titulo": "ABNT — instalações elétricas, aterramento, SPDA e iluminação", "categoria": "Elétrica", "agrupar": "documento",
     "resumo": "Tabelas e figuras de NBR 5410 (baixa tensão), NBR 14039 (média tensão), NBR 5419 (SPDA), NBR 15749 e 15751 (aterramento), "
               "NBR 5444 (símbolos) e iluminação de interiores (NBR ISO/CIE 8995-1 e a antiga NBR 5413).",
     "docs": [
         doc("NBR-5410", f"{A}/NBR 5410 2004 - INSTALAÇÕES ELÉTRICAS DE BAIXA TENSÃO.pdf", "Instalações elétricas de baixa tensão", "2004"),
         doc("NBR-14039", f"{OCR}/NBR-14039-2005.pdf", "Instalações elétricas de média tensão de 1,0 kV a 36,2 kV (cópia OCR)", "2005"),
         doc("NBR-5419", f"{A}/ABNT NBR 5419 2005 - Protecao de Estruturas contra Descargas Atmosfericas.pdf", "Proteção de estruturas contra descargas atmosféricas", "2005"),
         doc("NBR-15749", f"{OCR}/NBR-15749-2009.pdf",
             "Medição de resistência de aterramento e de potenciais na superfície do solo em sistemas de aterramento (cópia OCR)", "2009"),
         doc("NBR-15751", f"{A}/NBR 15751 2009 - SISTEMAS DE ATERRAMENTO DE SUBESTAÇÕES - REQUISITOS.pdf", "Sistemas de aterramento de subestações — Requisitos", "2009"),
         doc("NBR-5444", f"{A}/NBR 5444 1989 - SIMBOLOS GRAFICOS PARA INSTALAÇÕES ELÉTRICAS PREDIAIS.pdf", "Símbolos gráficos para instalações elétricas prediais", "1989"),
         doc("NBR-ISO-CIE-8995-1", f"{A}/NBR 8995-1 - ILUMINAÇÃO DE AMBIENTES DE TRABALHO PARTE1 - INTERIOR.pdf",
             "Iluminação de ambientes de trabalho — Parte 1: Interior", "2013"),
         doc("NBR-5413", f"{A}/NBR 5413 - ILUMINAÇÃO DE INTERIORES.pdf", "Iluminância de interiores (substituída pela NBR ISO/CIE 8995-1)", "1992"),
     ]},

    {"id": "abnt-eletrica-equipamentos", "titulo": "ABNT — equipamentos elétricos, áreas classificadas, graus IP e alarme de incêndio", "categoria": "Elétrica", "agrupar": "documento",
     "resumo": "Tabelas e figuras de NBR IEC 60079-10 e 60079-14 (atmosferas explosivas), NBR IEC 60529 e NBR 6146 (graus de proteção IP), "
               "NBR IEC 60439-1/-3 (conjuntos de manobra BT), projeto da NBR IEC 60947-1 (dispositivos de manobra) e NBR 17240 (detecção e alarme de incêndio).",
     "docs": [
         doc("NBR-IEC-60079-10", f"{OCR}/NBR-IEC-60079-10-2006.pdf", "Equipamentos elétricos para atmosferas explosivas — Parte 10: Classificação de áreas (cópia OCR)", "2006"),
         doc("NBR-IEC-60079-14", f"{A}/NBR 60079-14 2007.pdf",
             "Equipamentos elétricos para atmosferas explosivas — Parte 14: Instalação elétrica em áreas classificadas (exceto minas)", "2006 (válida a partir de 18.01.2007)"),
         doc("NBR-IEC-60529", f"{A}/ABNT NBR IEC 60529 2005 - Graus de Protecao para Involucros - Codigo IP.pdf",
             "Graus de proteção para invólucros de equipamentos elétricos (código IP)", "2005"),
         doc("NBR-6146", f"{A}/NBR 6146 1980 – INVÓLUCROS DE EQUIPAMENTOS ELÉTRICOS - PROTEÇÃO.pdf", "Invólucros de equipamentos elétricos — Proteção", "1980"),
         doc("NBR-IEC-60439-1", f"{A}/NBR 60439-1 2003 - CONJUNTOS DE MANOBRA E CONTROLE DE BT - PARTE 1_CONJUNTOS COM ENSAIO DE TIPO TOTALMENTE TESTADOS (TTA) E CONJUNTOS COM ENSA~cc0468.pdf",
             "Conjuntos de manobra e controle de baixa tensão — Parte 1: Conjuntos com ensaio de tipo totalmente testados (TTA) e parcialmente testados (PTTA)", "2003"),
         doc("NBR-IEC-60439-3", f"{A}/NBR 60439-3_2004 – CONJ. MANOBRA E CONTROLE BAIXA TENSÃO PART 3.pdf",
             "Conjuntos de manobra e controle de baixa tensão — Parte 3: Requisitos particulares para quadros de distribuição em locais acessíveis a pessoas não qualificadas", "2004"),
         doc("NBR-IEC-60947-1", f"{A}/NBR 60947 2005 - DISPOSITIVOS DE MANOBRA E COMANDO DE BAIXA TENSÃO – PARTE 1 REGRAS GERAIS.pdf",
             "Dispositivos de manobra e comando de baixa tensão — Parte 1: Regras gerais (Projeto ABNT 03:017.05-004)", "projeto nov/2005"),
         doc("NBR-17240", f"{OCR}/NBR-17240-5.pdf",
             "Sistemas de detecção e alarme de incêndio — Projeto, instalação, comissionamento e manutenção — Requisitos (cópia OCR)", "2010"),
     ]},

    {"id": "abnt-estruturas", "titulo": "ABNT — estruturas de aço, madeira e PRFV, vento, perfis e ensaio de tração", "categoria": "Estruturas e fabricação", "agrupar": "documento",
     "resumo": "Tabelas e figuras de NBR 8800 (aço e mistas), NBR 14762 (perfis formados a frio), NBR 6123 (vento), NBR 7190-1/-5 (madeira), "
               "NBR 15708-5 (perfis pultrudados), NBR 8261 (perfil tubular) e NBR ISO 6892 (ensaio de tração).",
     "docs": [
         doc("NBR-8800", f"{A}/ABNT NBR 8800 2008 - Projeto de Estruturas de Aco e Mistas de Aco e Concreto.pdf",
             "Projeto de estruturas de aço e de estruturas mistas de aço e concreto de edifícios", "2008"),
         doc("NBR-14762", f"{A}/nbr-14762-2010-dimensionamento-de-estruturas-de-ao-constituidas-por-perfis-formados-a-frio.pdf",
             "Dimensionamento de estruturas de aço constituídas por perfis formados a frio", "2010"),
         doc("NBR-6123", f"{A}/NBR 6123 1988 - Forças devidas ao vento em edificações.pdf", "Forças devidas ao vento em edificações (com Errata 2:2013 nas primeiras páginas)", "1988"),
         doc("NBR-7190-1", f"{A}/nbr-7190-1-2022.pdf", "Projeto de estruturas de madeira — Parte 1: Critérios de dimensionamento", "2022"),
         doc("NBR-7190-5", f"{A}/ABNT NBR 7190-5 2022 - Projeto de Estruturas de Madeira - Metodos de Ensaio de Ligacoes.pdf",
             "Projeto de estruturas de madeira — Parte 5: Métodos de ensaio para determinação da resistência e da rigidez de ligações com conectores mecânicos", "2022"),
         doc("NBR-15708-5", f"{OCR}/NBR-15708-5-2011.pdf", "Indústrias do petróleo e gás natural — Perfis pultrudados — Parte 5: Perfis estruturais (cópia OCR)", "2011"),
         doc("NBR-8261", f"{A}/nbr-8261pdf.pdf",
             "Perfil tubular, de aço-carbono, formado a frio, com e sem costura, de seção circular, quadrada ou retangular para usos estruturais", "1983"),
         doc("NBR-ISO-6892", f"{OCR}/NBR-ISO-6892-2002.pdf",  # texto do original com codificação quebrada → cópia OCR
             "Materiais metálicos — Ensaio de tração à temperatura ambiente (cópia OCR)", "2002"),
     ]},

    {"id": "abnt-tubulacao-gas-medicao", "titulo": "ABNT — dutos, tubos de aço, redes de gás e medição de vazão/pressão", "categoria": "Tubulação e flanges", "agrupar": "documento",
     "resumo": "Tabelas e figuras de NBR 15280-1/-2 (dutos terrestres), NBR 5590 e 6591 (tubos de aço), NBR 15526 e 13932 (redes de gás/GLP), "
               "NBR 12313 (combustão), NBR ISO 5167-1/-2 (placas de orifício, Venturi) e NBR 14105-2 (manômetros digitais).",
     "docs": [
         doc("NBR-15280-1", f"{A}/NBR 15280 1 2009 Dutos Terrestres Projeto..pdf", "Dutos terrestres — Parte 1: Projeto", "2009"),
         doc("NBR-15280-2", f"{A}/abnt-nbr-15280-2-2014pdf.pdf", "Dutos terrestres — Parte 2: Construção e montagem", "2014"),
         doc("NBR-5590", f"{A}/ABNT NBR 5590 2015 - Tubos de aço carbono com ou sem solda longitudinal, pretos ou galvanizados Requisitos.pdf",
             "Tubos de aço-carbono com ou sem solda longitudinal, pretos ou galvanizados — Requisitos", "2015"),
         doc("NBR-6591", f"{OCR}/NBR-6591-2008.pdf",
             "Tubos de aço-carbono com solda longitudinal de seção circular, quadrada, retangular e especial para fins industriais — Especificação (cópia OCR)", "2008"),
         doc("NBR-15526", f"{OCR}/NBR-15526-2007.pdf",
             "Redes de distribuição interna para gases combustíveis em instalações residenciais e comerciais — Projeto e execução (cópia OCR)", "2007"),
         doc("NBR-13932", f"{A}/NBR 13932 1997 - INSTALAÇÕES INTERNAS DE GÁS LIQUEFEITO DE PETRÓLEO GLP - PROJETO E EXECUÇÃO.pdf",
             "Instalações internas de gás liquefeito de petróleo (GLP) — Projeto e execução", "1997"),
         doc("NBR-12313", f"{A}/NBR 12313 - SISTEMA DE COMBUSTÃO - CONTROLE E SEGURANÇA PARA UTILIZAÇÃO DE GASES COMBUSTÍVEIS EM PROCESSOS DE BAIXA E ALTA TEMPERATURA.pdf",
             "Sistema de combustão — Controle e segurança para utilização de gases combustíveis em processos de baixa e alta temperatura", "2000"),
         doc("NBR-ISO-5167-1", f"{OCR}/NBR-5167-1.pdf",
             "Medição de vazão de fluidos por meio de instrumentos de pressão — Parte 1: Placas de orifício, bocais e tubos de Venturi (equiv. ISO 5167-1:1991; cópia OCR)", "1994"),
         doc("NBR-ISO-5167-2", f"{OCR}/NBR-ISO-5167-2-2011.pdf",
             "Medição de vazão de fluidos por dispositivos de pressão diferencial — Parte 2: Placas de orifício (cópia OCR)", "2011"),
         doc("NBR-14105-2", f"{A}/ABNT NBR 14105-2 2015 - Medidores de pressão Parte 2 Medidores digitais de pressão Requisitos de fabricação, classificação, ensaios e utilização.pdf",
             "Medidores de pressão — Parte 2: Medidores digitais de pressão — Requisitos de fabricação, classificação, ensaios e utilização", "2015"),
     ]},

    {"id": "abnt-icamento-cabos-amarras", "titulo": "ABNT — equipamentos de levantamento, cabos de aço, amarras e PEMT", "categoria": "Içamento e movimentação de carga", "agrupar": "documento",
     "resumo": "Tabelas e figuras de NBR 8400 (cálculo de pontes rolantes/guindastes), NBR ISO 2408 e ISO 3108 (cabos de aço), NBR 11900-3 (olhal com presilha), "
               "NBR 13715-2 (amarras offshore) e NBR 16776 (plataformas elevatórias móveis de trabalho).",
     "docs": [
         doc("NBR-8400", f"{A}/NBR 8400 1984 - CÁLCULO DE EQUIPAMENTO PARA LEVANTAMENTO E MOVIMENTAÇÃO DE CARGAS.pdf",
             "Cálculo de equipamento para levantamento e movimentação de cargas", "1984"),
         doc("NBR-ISO-2408", f"{OCR}/NBR-2408-2008.pdf", "Cabos de aço para uso geral — Requisitos mínimos (cópia OCR)", "2008 (versão corrigida 2, 2009)"),
         doc("NBR-ISO-3108", f"{A}/NBR 3108 1995 - CABOS DE AÇO PARA USO GERAL - DETERMINAÇÃO DA CARGA DE RUPTURA REAL.pdf",
             "Cabos de aço para uso geral — Determinação da carga de ruptura real", "1998"),
         doc("NBR-11900-3", f"{OCR}/NBR-11900-3.pdf", "Terminal para cabo de aço — Parte 3: Olhal com presilha (cópia OCR)", "2011"),
         doc("NBR-13715-2", f"{A}/NBR 13715-2 2009 - ESTRUTURAS OCEÂNICAS - AMARRAS - PARTE 2_REQUISITOS E MÉTODOS DE ENSAIO.pdf",
             "Estruturas oceânicas — Amarras — Parte 2: Requisitos e métodos de ensaio", "2008 (versão corrigida 2009)"),
         doc("NBR-16776", f"{OCR}/NBR-16776-2019.pdf",
             "Plataformas elevatórias móveis de trabalho (PEMT) — Projeto, fabricação, manutenção, requisitos de segurança e métodos de ensaio (cópia OCR)", "2019"),
     ]},

    {"id": "abnt-vasos-cilindros-hidraulica", "titulo": "ABNT — vasos de pressão em serviço, cilindros de gás e cilindros hidráulicos", "categoria": "Vasos de pressão e caldeiras", "agrupar": "documento",
     "resumo": "Tabelas e figuras do Projeto ABNT 04:011.07-008 (inspeção de segurança de vasos de pressão em serviço), NBR 12274 (inspeção de cilindros de gás), "
               "NBR 10288 (ensaio hidrostático de cilindros) e NBR 13444 (cilindros hidráulicos 250 bar — dimensões de montagem).",
     "docs": [
         doc("ABNT-PROJ-04.011.07-008", f"{A}/ABNT PROJETO 04 - 011.07 - 008 VASOS DE PRESSÃO EM SERVIÇO - INSPEÇÃO DE SEGURANÇA.pdf",
             "Vasos de pressão em serviço — Inspeção de segurança (Projeto ABNT 04:011.07-008)", "projeto out/2004"),
         doc("NBR-12274", f"{OCR}/NBR-12274.pdf", "Inspeção em cilindros de aço, sem costura, para gases (cópia OCR)", "2003 (versão corrigida 2004)"),
         doc("NBR-10288", f"{A}/NBR 10288 - CILINDRO DE AÇO PARA GASES COMPRIMIDOS - ENSAIO HIDROSTÁTICO PELO MÉTODO DA EXPANSÃO DIRETA.pdf",
             "Cilindro de aço para gases comprimidos — Ensaio hidrostático pelo método da expansão direta", "1994"),
         doc("NBR-13444", f"{A}/NBR 13444 1995 - SISTEMAS HIDRÁULICOS DE POTÊNCIA - CILINDROS HIDRÁULICOS DE HASTE SIMPLES, SÉRIE 250BAR - DIMENSÕES DE MONTAGEM.pdf",
             "Sistemas hidráulicos de potência — Cilindros hidráulicos de haste simples, série 250 bar — Dimensões de montagem", "1995"),
     ]},

    {"id": "abnt-seguranca-gestao-outros", "titulo": "ABNT — segurança de máquinas, espaço confinado, gestão, acústica, saneamento e documentação", "categoria": "Outros", "agrupar": "documento",
     "resumo": "Tabelas e figuras de NBR 16577 (espaço confinado), NBR ISO 12100 (segurança de máquinas), NBR ISO 9001 (qualidade), NBR 7500 (identificação de produtos perigosos), "
               "NBR 10152 (níveis de ruído), NBR 7229 e 13969 (tanques sépticos), NBR 6023 e 10520 (referências e citações).",
     "docs": [
         doc("NBR-16577", f"{A}/ABNT NBR 16577 20217 - Espaço confinado — Prevenção de acidentes procedimentos e medidas de proteção.pdf",
             "Espaço confinado — Prevenção de acidentes, procedimentos e medidas de proteção", "2017 (versão corrigida 06.04.2017)"),
         doc("NBR-ISO-12100", f"{A}/NBR ISO 12100 2014 - SEGURANÇA DE MÁQUINAS PRINCÍPIOS GERAIS DE PROJETO APRECIAÇÃO E REDUÇÃO DE RISCOS.pdf",
             "Segurança de máquinas — Princípios gerais de projeto — Apreciação e redução de riscos", "2013 (válida a partir de 17.01.2014)"),
         doc("NBR-ISO-9001", f"{A}/ABNT NBR ISO 9001 2008 - Sistemas de Gestao da Qualidade - Requisitos.pdf", "Sistemas de gestão da qualidade — Requisitos", "2008"),
         doc("NBR-7500", f"{A}/NBR 7500 SB 54 - IDENTIFICAÇÃO PARA O TRANSPORTE TERRESTRE, MANUSEIO, MOVIMENTAÇÃO E ARMAZENAMENTO DE PRODUTOS.pdf",
             "Identificação para o transporte terrestre, manuseio, movimentação e armazenamento de produtos (Emenda 1:2004 nas págs. 1–12 + norma 2003)", "2003 + Emd.1:2004"),
         doc("NBR-10152", f"{A}/NBR 10152 2017 - Acustica - Niveis de Pressao Sonora em Ambientes Internos a Edificacoes.pdf",
             "Acústica — Níveis de pressão sonora em ambientes internos a edificações", "2017"),
         doc("NBR-7229", f"{A}/NBR 7229 - PROJETO, CONSTRUÇÃO E OPERAÇÃO DE SISTEMAS DE TANQUES SÉPTICOS.pdf",
             "Projeto, construção e operação de sistemas de tanques sépticos", "1993"),
         doc("NBR-13969", f"{A}/NBR 13969 TANQUES SÉPTICOS - UNIDADES DE TRATAMENTO COMPLEMENTAR E DISPOSIÇÃO FINAL DOS EFLUENTES LÍQUIDOS - PROJETO, CONSTRUÇÃO E OPERAÇÃO.pdf",
             "Tanques sépticos — Unidades de tratamento complementar e disposição final dos efluentes líquidos — Projeto, construção e operação", "1997"),
         doc("NBR-6023", f"{A}/NBR 6023 2018 - INFORMAÇÕES E DOCUMENTAÇÃO - REFERÊNCIAS - ELABORAÇÃO.pdf", "Informação e documentação — Referências — Elaboração", "2018"),
         doc("NBR-10520", f"{A}/NBR 10520 2002 - INFORMAÇÃO E DOCUMENTAÇÃO - CITAÇÕES EM DOCUMENTOS - APRESENTAÇÃO.pdf",
             "Informação e documentação — Citações em documentos — Apresentação", "2002"),
     ]},
]
