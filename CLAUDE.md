# Projeto Uva — Buscador de normas com valores

Página web de consulta de normas técnicas. O engenheiro busca um assunto (ex.: "escada") e vê, **sem abrir o PDF**, quais normas se aplicam e os **valores, cotas, tolerâncias e notas** necessários para projetar e construir — cada valor com a norma e o item de origem, e desenho próprio com a cota destacada.

- Repositório PÚBLICO: https://github.com/matheusmerlim1/Referencias-normativas (branch `main`, autor git matheusmerlim1).
- Site publicado (GitHub Pages, camada pública): https://matheusmerlim1.github.io/Referencias-normativas/
- Local: `index.html` com duplo clique carrega `dados/dados_local.js` (completo) se existir; `?publico=1` força a camada pública.
- **De onde continuar: seção "PRÓXIMOS PASSOS" no fim deste arquivo.** Diário completo de 08–30/out: `HISTORICO.md`.

Autor: Matheus (Friplan). Projeto anterior relacionado (só busca de texto em PDF): `P:\Matheus\ferramenta_busca_pdf`.

## Regras do projeto
- **MEMÓRIA (29/out/2026, pedido do usuário):** o projeto usa no MÁXIMO 1/6 da RAM disponível. Antes de rodar algo pesado
  (OCR, extração, pools, agentes), ver `python -P ferramentas/recursos.py [MB_por_processo]`; scripts paralelos usam
  `from recursos import procs` → `mp.Pool(procs(MB))` (info_normas.py já usa). No máximo 1 agente por vez.
- **REPOSITÓRIO PÚBLICO NO GITHUB (28/out/2026, pedido do usuário):** nada protegido por direito autoral das normas vai para o repo.
  CAMADA PÚBLICA (versionada): código (index.html, assets/app.js/style.css, ferramentas/), fichas TEMÁTICAS (valores + norma/item;
  notas escritas por nós), desenhos PRÓPRIOS (assets/figuras/esquemas/*.svg), RESUMOS próprios por norma (conteudo/resumos/<slug>.json),
  normas.json/catalogo.json (metadados), dados/dados.js gerado SÓ com a camada pública.
  CAMADA LOCAL (no .gitignore; o site usa se existir): referencias/, dados/textos/, dados/busca/, conteudo/docs/,
  conteudo/fichas/norma-*.json, assets/figuras/docs/, assets/figuras/tem/, assets/figuras/asme-ii/, assets/figuras/*.png (recortes),
  dados/dados_local.js (build completo).
  - RESUMO de norma = texto REESCRITO por nós (simplificado, sem copiar frases; termos técnicos e valores numéricos podem — são fatos),
    organizado por seção, com os valores/cotas e item. Schema `conteudo/resumos/<slug>.json`:
    `{"id": "<id normas.json>", "titulo": "...", "secoes": [{"titulo": "...", "item": "5.2", "texto": "paráfrase curta",
      "valores": [{"parametro": "...", "valor": "...", "item": "...", "nota": "opcional: leitura da figura, vigência, erro da norma, condição"}], "figuras": ["esquemas/<arquivo>.svg"]}]}`
  - DESENHO PRÓPRIO = SVG feito por nós em assets/figuras/esquemas/ (nunca cópia/traçado de figura da norma), legenda
    "Esquema ilustrativo (não é desenho da norma) — …". Cada cota num grupo `<g id="cota-<nome>" class="cota">…<text>rótulo</text></g>`;
    requisito/valor aponta a cota com `"cota": "esquemas/<arquivo>.svg#<nome>"` → o site mostra o esquema com ESSA cota destacada
    e o valor escrito nela.
  - Imagens de norma (recortes/páginas) NUNCA em fichas temáticas da camada pública — substituir por desenho próprio.
- **SITE AUTOSSUFICIENTE (27/out/2026):** os PDFs de `referencias/` (incl. `referencias/ocr/`) vão ser REMOVIDOS. O site NÃO exibe
  item, página nem link de PDF; todo conteúdo tem de estar no projeto: texto completo por norma (`dados/textos/`, de
  `ferramentas/extrair_textos.py`), recortes PNG (assets/figuras/docs/), páginas com desenho sem título (gerar_docs guarda inteiras),
  figuras/esquemas SVG das fichas temáticas (assets/figuras/esquemas/, assets/figuras/tem/ = cópias fixas de recortes de docs/).
  Busca global no texto completo: `python -P ferramentas/indexar_textos.py` (~15 s; rodar após extrair_textos) → dados/busca/
  (índice invertido por prefixo, 13 MB). `norma`/`item`/`pagina` continuam nos JSON (rastreabilidade interna, validação), mas os TEXTOS das fichas não citam página.
  Ferramentas que leem PDF (gerar_docs, recortes, info_normas, extrair_textos, crop) só funcionam enquanto referencias/ existir.
- **Objetivo é CONSULTA** (tirar dúvidas, o máximo de informação de cada norma). NÃO criar calculadoras novas — o usuário já tem
  ferramentas de cálculo (ex. içamento). As existentes (escada, escada-marinheiro, consulta-tabela) ficam. Esforço vai para
  cobertura: requisitos, tabelas, figuras, definições, notas de conflito. Tags `calc` não são necessárias em fichas novas.
- **Escrever somente dentro desta pasta** (`C:\Users\MatheusPinheiroRapos\Desktop\ENGENHARIA\Projeto Uva`). `T:\ENG\Literature`, `P:\Matheus\...` e demais pastas são **somente leitura** (consulta).
- Todo valor numa ficha sai do texto da norma, nunca de memória, e tem `norma` + `item` + `pagina`.
- `pagina` = página física do PDF (1-based), a mesma que `arquivo.pdf#page=N` abre — não o número impresso no rodapé.
- Valores lidos de figura (e não de texto) são sinalizados no campo `nota`.
- Quando normas divergem, a ficha mostra todas e traz uma nota de `atencao` explicando o contexto de cada uma.

## Estrutura
```
index.html                 site (abre com duplo clique; funciona offline via file://)
assets/app.js              busca, renderização das fichas, calculadoras
assets/style.css           estilos (tema claro/escuro)
assets/figuras/esquemas/   desenhos PRÓPRIOS SVG com grupos id="cota-<nome>" (PÚBLICO; 230 arquivos)
assets/figuras/docs|tem|asme-ii/, assets/figuras/*.png   recortes/páginas das normas (LOCAL, .gitignore)
conteudo/resumos/<slug>.json  resumo PRÓPRIO por norma (779; slug = nome da ficha de norma, ex. norma-nr-12) (PÚBLICO)
conteudo/completar/*.json  listas de auditoria aplicadas por completar_escaneadas.py (páginas a acrescentar/excluir/girar/forçar; texto_fonte.json)
dados/textos/, dados/busca/  texto completo por norma e índice de busca (LOCAL; extrair_textos.py / indexar_textos.py)
HISTORICO.md               diário detalhado de tudo que foi feito (08–30/out/2026)
conteudo/normas.json       registro das normas usadas nas fichas (id, título, edição, órgão, escopo, caminho do PDF)
conteudo/fichas/*.json     fichas TEMÁTICAS (uma por tema, curadas à mão) + fichas de NORMA norma-<id>.json ("tipo": "norma", GERADAS — não editar à mão)
conteudo/docs/*.json       fonte das fichas de norma: recortes por documento (gerar_docs.py / gerar_asme_ii.py) — o build NÃO lê
conteudo/normas_info.json  GERADO por ferramentas/info_normas.py — escopo, páginas, definições, referências normativas de cada norma
ferramentas/separar_normas.py  docs/ + normas.json + normas_info.json → conteudo/fichas/norma-*.json (rodar após gerar_docs/info_normas)
conteudo/sinonimos.json    grupos de termos equivalentes para a busca (PT/EN)
conteudo/catalogo.json     inventário deduplicado do acervo T:\ENG\Literature (agente catalogador-acervo)
dados/dados.js             GERADO por ferramentas/build.py — camada PÚBLICA (versionada); dados/dados_local.js = completo (local, .gitignore)
dados/indice.js            GERADO por ferramentas/indexar_referencias.py — títulos de seções/tabelas/figuras por página dos PDFs de referencias/
conteudo/triagem_referencias.json  GERADO por ferramentas/triagem_referencias.py — situação/prioridade de cada documento de referencias/
ferramentas/build.py       valida conteudo/ (fichas, resumos, cotas, SVG) e gera dados/dados_local.js (completo) + dados/dados.js (público)
ferramentas/verificar_autossuficiente.py [--publico]  0 erros = site não depende de referencias/; --publico = nada protegido no que o git versiona
ferramentas/recursos.py    RAM livre e limite de 1/6 (procs(MB) p/ pools)
ferramentas/gerar_docs.py + recortes.py + docs_*.py   recortes de tabela/figura por documento → conteudo/docs/ (config das fichas-fonte em docs_*.py)
ferramentas/completar_escaneadas.py <lista> [--gravar|--limpar]  aplica as listas de conteudo/completar/ (idempotente; rodar de novo se regerar uma ficha)
ferramentas/info_normas.py  escopo/definições/referências → normas_info.json; separar_normas.py → fichas norma-*.json
ferramentas/extrair_*.py, ocr_celulas.py, ocr_lote.py  extratores específicos (B16.5, II-D, OCR célula a célula, OCR em lote)
ferramentas/notas_iid_pt.py  notas da II-D em português (aplicar depois de extrair_iid*.py --gravar, que regrava o inglês)
ferramentas/dump.py        extrai texto de PDF por página (para curadoria)
ferramentas/crop.py        recorta figura de PDF como PNG
ferramentas/ocr.py         gera cópia pesquisável (OCR Tesseract) de PDF escaneado → referencias/ocr/ (mesmas páginas)
ferramentas/conferir.py    confere nº de cada requisito/tabela contra o texto da página citada (revisão barata, sem agente)
.claude/agents/            agentes do projeto (ver abaixo)
```

## Comandos
```
python ferramentas/build.py                                   # validar + gerar dados (rodar após qualquer mudança em conteudo/ ou esquemas/)
python -P ferramentas/verificar_autossuficiente.py --publico  # tem de dar "0 pendência(s)" antes de todo commit
python -P ferramentas/recursos.py 600                         # quantos processos de 600 MB cabem em 1/6 da RAM
python -P ferramentas/cotas_pendentes.py [slug…|--svg|--sem-desenho]  # pendências de cota; --svg = esquemas sem uso; --sem-desenho = resumos sem desenho
python -P ferramentas/gerar_docs.py <ficha> --gravar ; python -P ferramentas/separar_normas.py --gravar   # mudar recortes (apagar antes assets/figuras/docs/<ficha>/)
python -P ferramentas/dump.py <pasta_tmp> "<glob do pdf>"     # texto do PDF por página
python -P ferramentas/crop.py "<glob do pdf>" <pág> "x0,y0,x1,y1" 200 assets/figuras/<nome>.png
python -P ferramentas/ocr.py "<glob do pdf>" referencias/ocr/<nome>.pdf [eng|por]   # Tesseract em %LOCALAPPDATA%\Programs\Tesseract-OCR
python -P ferramentas/conferir.py <ficha> <id-norma>           # lista o que não bate (figura/fórmula/OCR → conferir na imagem)
python -P ferramentas/triagem_referencias.py                  # situação dos documentos de referencias/ (rodar após incorporar normas)
python -P ferramentas/indexar_referencias.py                  # índice de títulos por página → dados/indice.js (~3 min)
```
Depois do build, abrir `index.html` no navegador (ou F5 se já aberto).
Skill `lote-norma` (`.claude/skills/`): passo a passo do método barato para incorporar uma norma (índice → dump das páginas → script → build → conferir).

## Schema da ficha (`conteudo/fichas/<id>.json`)
Modelo de referência: `conteudo/fichas/escada-degraus.json`.
```jsonc
{
  "id": "escada-degraus",                 // = nome do arquivo, kebab-case
  "titulo": "Escada de degraus (fixa)",
  "categoria": "Acessos e circulação",    // agrupa no índice do site
  "resumo": "1–2 frases: o que é e o que a ficha cobre",
  "palavras_chave": ["escada", "degrau", "stair", ...],   // PT + EN, sinônimos, termos de campo
  "relacionadas": ["guarda-corpo", ...],  // ids de outras fichas
  "calculadora": "escada",                // opcional; precisa existir em app.js e em CALCULADORAS no build.py
  "figuras": [{ "arquivo": "x.png", "legenda": "...", "norma": "NR-12", "item": "Anexo III, Figura 4", "pagina": 38,
                "grupo": "Degrau (espelho e piso)" }],   // grupo opcional (texto ou lista); sem ele, a figura vai para o grupo cujo requisito cita "Fig. N" da mesma norma
  "requisitos": [{
    "grupo": "Degrau (espelho e piso)",   // seções da ficha, na ordem do projeto
    "parametro": "Altura entre degraus (h) — escada COM espelho",
    "valor": "0,20 m a 0,25 m",           // texto como na norma
    "min": 200, "max": 250, "unidade": "mm",  // numéricos opcionais (dimensões em mm) p/ calculadoras
    "norma": "NR-12",                     // id existente em normas.json
    "item": "Anexo III, 12 d)",
    "pagina": 38,
    "nota": "opcional: exceções, condições, origem em figura"
  }],
  "notas": [{ "tipo": "atencao|info|dica", "texto": "..." }]
}
```

### Tabelas de dados (opcional, para normas tabulares como ASME B16.5)
```jsonc
"tabelas": [{ "id": "b165-cl150-dim", "titulo": "Classe 150 — dimensões", "norma": "ASME-B16.5", "item": "Tabela 8", "pagina": 95,
  "unidade": "mm", "chave": { "classe": "150" },          // agrupa para a calculadora consulta-tabela
  "colunas": ["NPS", "O — Ø externo do flange", ...],    // 1ª coluna = chave da linha
  "linhas": [["1/2", 90, ...], ...], "nota": "...",
  "consulta": false,                                     // opcional: só exibir, fora da consulta (ex. tabela P–T)
  "figuras": ["tem/x.png", "esquemas/y.svg"],            // opcional: desenhos com as cotas (letras = colunas), relativos a assets/figuras/; legenda = a de f.figuras com o mesmo arquivo
  "cotas": { "O — Ø externo": "esquemas/y.svg#O" } }],   // opcional: coluna → cota do SVG (célula/valor mostra o esquema com a cota destacada e o valor); sem entrada, vale a convenção id="cota-<1ª palavra da coluna>" num SVG de "figuras"; build valida e embute o SVG
"calculadora": "consulta-tabela",
"consulta": { "titulo": "...", "rotulos": { "classe": "Classe" }, "linha": "NPS", "ajuda": "..." }
```
O build valida nº de valores por linha = nº de colunas.

## Agentes do projeto (`.claude/agents/`)
| Agente | Quando usar |
|---|---|
| `curador-normas` | Criar ficha nova ou acrescentar uma norma a uma ficha (extrai valores do PDF) |
| `revisor-fichas` | Auditar ficha contra o PDF (valor, unidade, item, página). Só relata, não edita |
| `catalogador-acervo` | Inventariar/deduplicar `T:\ENG\Literature` em `conteudo/catalogo.json` |
| `dev-site` | Interface: busca, layout, novas calculadoras |

Fluxo recomendado para um tema novo: `curador-normas` → `revisor-fichas` → corrigir → `build.py`.
Vários curadores podem rodar em paralelo (um tema cada); só o coordenador edita `normas.json`.

## Acervo (T:\ENG\Literature) — mapa rápido
- `03 - Standards\` — NRs atuais (12, 17, 18, 34, 37), ABS Marine Vessel Rules 2022, ISA 75.x, NBR 15708-6.
- `00 - Miscellaneous\` — ~8.100 arquivos: ASTM, ASME (Sec. II, VIII), API, ABNT, SSPC, AWS D1.1/A2.4, DNV-ST-E273, **Petrobras N-xxxx** (`PETROBRAS\NORMAS`, nomes só com número; títulos no `0 - CATALOGO DE NORMAS PETROBRAS`), specs Equinor (`EQUINOR\`), ABS Ergonomic Notations 2021.
  - Pastas duplicadas: `00 - Miscellaneous\1 - NORMAS\...` ≡ `00 - Miscellaneous\Standards\1 - NORMAS\NORMAS ESTRANGEIRAS\...`.
  - Pastas com "SUPERADO/SUPERADA" = edições antigas.
- `01 - Books\`, `02 - Brochures\` (catálogos de fabricantes), `04 - Work Instruction\`.

## Armadilhas técnicas (Windows)
- `pymupdf.open(caminho)` falha com acentos no caminho → abrir como stream: `pymupdf.open(stream=open(p,"rb").read(), filetype="pdf")` (já feito em dump.py/crop.py).
- Caminhos > 260 caracteres falham: use pastas temporárias curtas para os .txt.
- Passar caminhos com acento por argumento do bash quebra a codificação → passe um **glob** com `*` no lugar do trecho acentuado.
- `python -I` ignora o site-packages do usuário (onde está o pymupdf) → use `python -P`.
- Rodar Python com `PYTHONIOENCODING=utf-8` para imprimir acentos.
- O índice SQLite grande de `P:\Matheus\ferramenta_busca_pdf\indexes` está corrompido; os demais são pequenos — não reaproveitar.
- ABS Ergonomic Notations: os desenhos das figuras ESTÃO no PDF como imagem, em geral no topo da página seguinte à tabela de cotas (ex.: Fig. 3 → pág. 24, Fig. 15 → pág. 37). A página física do PDF é o nº do rodapé + 1.
- Desenhos de engenharia (Equinor/Maersk) costumam ter cotas como vetor sem texto: `get_text()` volta vazio — renderize com crop.py a 200+ dpi e leia a imagem.

## ESTADO ATUAL (30/out/2026)
- 802 fichas = 23 TEMÁTICAS (curadas, públicas) + 779 de NORMA (`norma-*.json`, geradas, locais); 22 839 requisitos; 779 normas.
- 779/779 RESUMOS próprios (`conteudo/resumos/`), 6 543 valores; 902 valores ligados a cota.
- 284 SVG próprios em `assets/figuras/esquemas/`; as 23 temáticas NÃO têm mais figura de norma (tudo trocado por SVG).
- Catálogo do acervo T: 3 933 documentos únicos (`conteudo/catalogo.json`) → buscáveis no site como "Documentos no acervo".
- Triagem de `referencias/`: 775/775 documentos relevantes incorporados (100 %). Auditoria de imagens encerrada (28/out).
- `verificar_autossuficiente.py` = 0 erros → `referencias/` (6,7 GB) PODE ser removida — o usuário decide. Sem ela param as
  ferramentas que leem PDF (gerar_docs, recortes, info_normas, extrair_textos, crop, dump, ocr).
- Tamanhos: dados/dados.js público 8,5 MB; dados_local.js 25 MB; assets/figuras 351 MB (quase tudo local); dados/ 122 MB.
- Commits: c2d79d0 camada pública · 76007e2 resumos das 779 normas · aae2ef7 cotas lote 1 · depois: CLAUDE.md reorganizado.

## O QUE JÁ FOI FEITO (resumo; detalhes em HISTORICO.md)
- **Site** (app.js/style.css/index.html): busca com sinônimos PT/EN e por prefixo no texto completo; home com temáticas + "Normas"
  por órgão/assunto; ficha em abas (Consulta rápida | Requisitos | Tabelas | Figuras | Notas); página da norma com Resumo (1ª aba),
  Escopo, Itens, Tabelas, Figuras, Em fichas temáticas, Sumário, Definições, Referências normativas; consulta-tabela com filtros em
  cascata; botão "cota" (SVG inline com a cota em laranja e " = valor"); calculadoras escada / escada-marinheiro / consulta-tabela.
- **Fichas temáticas (23)**: escada-degraus, escada-marinheiro, escada-portatil, guarda-corpo, passarela-plataforma-rampa,
  grating-piso-grade, ancoragem-linha-de-vida, habitabilidade-plataforma, icamento-unidade-portatil, lingadas-acessorios, guincho,
  guindaste-ponte-rolante, tolerancias-fabricacao-estrutural, tolerancias-gerais-ajustes, solda-estrutural, tubulacao-processo,
  flange-asme-b16-5 (B16.5/B16.47/NORSOK L-005/juntas), parafusos-porcas-arruelas, perfis-laminados, vaso-pressao-asme-viii,
  nr-13-caldeiras-vasos, materiais-asme-ii-d, propriedades-fisicas-asme-ii-d. Todas revisadas contra o PDF.
- **Fichas por norma (779)**: recortes de tabelas/figuras, páginas inteiras de escaneadas/desenhos, itens, escopo, definições —
  geradas de `conteudo/docs/` (fichas-fonte por bloco: ASME, ABNT, ISO, DIN, offshore, outros, recortes-normas-tematicas).
- **OCR**: Tesseract 5.4 (eng+por); `referencias/ocr/` (1,8 GB) + `ocr/v2/` (refeitos); `_origem.json` mapeia OCR → original.
- **Camada pública**: .gitignore, README.md, build com 2 saídas (para se dados.js público citar imagem local), --publico no
  verificador, notas copiadas em inglês reescritas (II-D, B16.5), resumos reescritos, GitHub Pages no ar.
- **Cotas nos resumos — LOTE 1 FEITO** (aae2ef7): acessos/ergonomia/NRs — ASTM F1166, ABS-ERGO, NR-12/13/18/24/34/35/37,
  EQN PE-FD-00-S-SP-00001, EQN vertical ladder, NBR 14718, NBR 15708-2, ISO 14122-2/-3 → 212 valores, +18 SVG.
- **Cotas nos resumos — LOTE 2 FEITO** (30/out, içamento): DNV-OS-H205, ABS-LIFT, NBR 11900-2/-3, 13715-2, ISO 2408, E271,
  Z359.14, NORSOK R-002, B30.7/10/26, ISO 3266, NBR 13543/6327/15516-1/-2/16325-2, guia padeye → 52 valores, +6 SVG, 3 SVG ampliados.
  Encaixes aproximados (rever se quiser): banda/inclinação → guindaste-ponte-rolante-banda-trim#banda; ISO 3266 ±5° →
  interface-olhal-manilha#desvio-plano. Sobraram p/ outros lotes: API 9A (ensaios), NBR 16776 (plataforma elevatória).
- **Cotas nos resumos — LOTE 3 FEITO** (30/out, tubulação/flange/solda/vaso/estrutura): B31.3 (8), AWS D1.1 (11), B16.5/25/47/20/21,
  API 14E, VIII-1 UG/UW, B18.2.6, ISO 13920, DNV-OS-C101, EN 10034, API 1104 → 59 valores, +5 SVG, 8 SVG ampliados. Sem pendência
  dimensional: B16.9/11/34/48, B31.4/8, B36.10M, IX, VIII-2, ISO 4032. Agora: 1013 valores com cota; ~974 dimensionais sem cota em 312
  resumos (muitos são faixa de aplicação/condição — o regex não distingue).
- **Cotas nos resumos — LOTE 4 FEITO** (30/out; coordenador + 1 agente): NRs 10/11/15/16/17/19/21 (93 valores, +7 SVG resumo-nr-*,
  NR-10 ganhou cota-rr-rc) e 36 NBR/IEC (211 valores, +26 SVG: desenho técnico, SPDA, gás, esgoto, vento, IP, PEMT, tubos com
  costura, placa de orifício, ensaio de tração…). Agora: 1317 valores com cota; ~688 com unidade sem cota em 294 resumos; 274 SVG.
  Scripts reaproveitáveis (scratchpad da sessão, podem sumir): aplicar.py preserva o formato do JSON (indent 1, valores compactos).
- **Cotas nos resumos — LOTE 5 FEITO** (30/out; coordenador + 1 agente): ISO/DIN (50 valores; +4 SVG: fixadores-pontas-rosca,
  fixadores-rebite-anel-o-rosca-conica, hidraulica-cilindro-instalacao, engrenagem-perfil-referencia) e specs ASME II SA/SB
  (54 valores; +7 SVG asme-ii-*: ensaios de tubo, dobramento, Charpy, UT de chapa, arame, fundido, tubo em U). A maioria dos
  "pendentes" das specs era °F/%/ksi/escopo. Removidos 17 SVG da 1ª geração sem cota e sem uso. Ferramenta nova cotas_pendentes.py.
  Agora: 1 421 valores com cota; 232 dimensionais sem cota em 155 resumos (pela ferramenta, que já ignora °C, m/s, m², m³); 268 SVG.
- **Cotas nos resumos — LOTE 6 FEITO = FECHAMENTO** (30/out; coordenador + 1 agente). Regra nova do usuário: "tente sempre botar
  algum desenho para simplificar a norma" → FAIXAS/LIMIARES de grandeza geométrica também ganham cota (Ø 4–42 mm → cota no Ø);
  só fica sem desenho o que não tem geometria (registrado com motivo em conteudo/cotas_dispensadas.json, 83 valores).
  cotas_pendentes.py = 0 pendentes; 1 570 valores com cota. Todo resumo de asme/api/dnv/abs/bv/astm/isa… ganhou ≥ 1 esquema
  (genéricos por família: asme-ii-chapa-espessura, tubulacao-processo-tubo-diametros-parede, asme-ii-arame-diametro, end-metodos,
  valvula-dimensoes, poco-bop-arvore, bomba-centrifuga-selo, ensaios-laboratorio…). 284 SVG.

## PRÓXIMOS PASSOS (continuar daqui)
Lotes 1–6 feitos (30/out): 0 valores dimensionais sem cota. Próximo: LOTE 7 = 128 resumos SEM NENHUM desenho (ISO 42, DIN 29,
   NBR 25, NR 8, BS 8, AGMA 5, MSS 4…) → `cotas_pendentes.py --sem-desenho`; dar a cada um ≥ 1 esquema próprio (conceito da peça/ensaio). Commit + push ao fim de cada lote (pedido do usuário).
1. **Cotas nos resumos** — faltam ~1 049 valores dimensionais sem cota em 316 resumos. Um agente por vez, por lote. O agente:
   reutiliza SVG existentes (acrescenta grupo `cota-<nome>` sem quebrar os que já existem), só cria SVG novo DO ZERO (só rótulos,
   nunca números; rodapé "Esquema ilustrativo (não é desenho da norma) — sem escala."), põe `"cota"` no valor e o SVG em `figuras`
   da seção; pula o que não é medida geométrica (carga, tempo, pressão, lux, faixa de aplicação, tamanho de objeto); não altera
   textos/valores. Coordenador: build + `--publico` = 0 → olhar os SVG novos (Edge headless --screenshot) → commit + push.
   - ~~Lote 2 — içamento~~ (FEITO): DNV-ST-E273 (3), DNV-ST-E271 (6), DNV-2.22 (5), ABS-LIFT-2021 (6), NBR-8400 (4), NORSOK-R-002 (5),
     ASME-B30.26 (5), B30.10 (2), B30.7, ISO-3266 (3), NBR-15637-1, 15516-1/-2, 13543, 6327, 11900-4, 16325-2, 14628,
     ANSI-Z359.14 (4), DNV-OS-H205 (7).
   - ~~Lote 3 — tubulação/flange/solda/vaso~~ (FEITO): ASME-B31.3 (18), AWS-D1.1 (22), B16.5 (8), B16.25 (6), B16.47 (6), B16.20 (4),
     API-RP-14E (8), NORSOK-L-005, ASME-VIII-1-UG (4)/UW (6)/UCS (7), B18.2.6 (5), ISO-898-1, ISO-9013, ISO-13920, API-RP-2A,
     DNV-OS-C101 (4).
   - ~~Lote 4~~ (FEITO: NRs + NBR). **Lote 5+**: resto por uso — NR-15 (23), NR-17 (17), NR-11 (12) e as demais.
   - Sobras do lote 1 (4 em F1166, 4 em NR-37, 9 em NR-12…): o agente julgou não-geométricas; não refazer.
   - Contagem de pendentes: `python -P ferramentas/cotas_pendentes.py` (ordem = uso nas temáticas; ignora °C, m/s, m², m³);
     `… cotas_pendentes.py norma-nr-15` lista os valores com índice seção.valor; `--svg` lista esquemas que ninguém cita.
2. **Figuras nos resumos** (baixa prioridade): só ~28 resumos têm `figuras`; normas sem valor dimensional podem ganhar esquema de conceito.
3. **Decisão do usuário**: remover `referencias/` (pode; ver Estado).
4. Backlog antigo (baixa prioridade; detalhes em HISTORICO.md): ficha vaso-pressao migrar de VIII-1 2001 para 2007; UCS-66, UG-37;
   B16.9/B16.11/B36.19M; NR-13 tubulações; ISO 4759/4042; MSS SP-44, API 6AF; NBR 6409/ISO 1302; IPE/W/cantoneiras; composição
   química das specs SA/SB; aba "Acervo" no site; fichas de pintura (N-xxxx/SSPC) e andaime.

Rotina de commit: `python ferramentas/build.py` → `python -P ferramentas/verificar_autossuficiente.py --publico` (0) →
`git status` (só camada pública; o usuário às vezes tem OUTRAS sessões editando o projeto ao mesmo tempo → `git add` só dos
seus caminhos, nunca `git add -A`, e confira com ListAgents) → commit terminando em "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" → `git push origin main`.
Agentes: no máximo 1 por vez (RAM); o usuário pede economia de créditos.
