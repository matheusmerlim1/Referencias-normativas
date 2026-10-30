# Projeto Uva — Buscador de normas com valores

Página web local de consulta de normas técnicas. O engenheiro busca um assunto (ex.: "escada") e vê, **sem abrir o PDF**, quais normas se aplicam e os **valores, cotas, tolerâncias e notas** necessários para projetar e construir — cada valor com norma, item e página (link que abre o PDF na página).

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
assets/figuras/*.png       recortes de figuras das normas (nome: <norma>-<item>-<assunto>.png)
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
ferramentas/build.py       valida conteudo/ e gera dados/dados.js
ferramentas/dump.py        extrai texto de PDF por página (para curadoria)
ferramentas/crop.py        recorta figura de PDF como PNG
ferramentas/ocr.py         gera cópia pesquisável (OCR Tesseract) de PDF escaneado → referencias/ocr/ (mesmas páginas)
ferramentas/conferir.py    confere nº de cada requisito/tabela contra o texto da página citada (revisão barata, sem agente)
.claude/agents/            agentes do projeto (ver abaixo)
```

## Comandos
```
python ferramentas/build.py                                   # validar + gerar dados/dados.js (rodar após qualquer mudança em conteudo/)
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

## Situação e próximos passos
Feito (08/out/2026):
- Estrutura, build/validação, site com busca (sinônimos PT/EN), filtro por norma, links PDF#página.
- 4 fichas, ~300 valores, todas revisadas pelo `revisor-fichas` contra o PDF e corrigidas:
  `escada-degraus` (+ calculadora `escada`), `escada-marinheiro` (+ calculadora `escada-marinheiro`, perfis NR-12/NR-18/ABS/Peregrino II/FPSO),
  `guarda-corpo`, `passarela-plataforma-rampa`.
- Padrões Equinor do FPSO Peregrino usados: spec PE-FD-00-S-SP-00001 (pág. 6 = guarda-corpo 20006-001; pág. 7 = escada de degraus 20007-001;
  pág. 8 = escada marinheiro 20008-001).
- 09/out/2026: ASTM F1166-07 e ISO 14122-2:2016 (de `referencias/`) incorporadas às 4 fichas de acesso → 487 valores, 10 normas.
  Tudo revisado pelo `revisor-fichas` (incl. FPSO 20007-001) e corrigido. Chave de calculadora nova: `espelhos_lance` (máx. espelhos por lance).
  Erros da própria F1166 anotados nas notas: 11.2.2 "less than 544 kg"; 11.13.4.1 "985 mm (38 in.)"; Fig. 90 "15.2 m min."; Fig. 96 "3660 mm (120 in)".
- Busca também em documentos: `build.py` junta `conteudo/referencias.json` (e `catalogo.json`, quando existir) em `dados.js` → lista "Documentos no acervo" com link para o arquivo (sem valores).

Campo opcional de requisito usado pelas calculadoras: `"calc": ["perfil:chave"]` (ex. `"nr12-ce:h"`), com nomes de perfil em `calculadora_perfis` na ficha.

Referências (`referencias/`, 09/out/2026): 30 zips íntegros; 1216 documentos únicos extraídos em `referencias/extraido/<ORGAO>/`
(duplicatas: os 2 zips NORSOK e os 2 zips ASME BPVC 2007 são idênticos; manifesto em `_manifesto.json`). 131 PDFs sem texto (precisam OCR).
Reexecutar: `python -P ferramentas/extrair_referencias.py` e `python -P ferramentas/inventariar_referencias.py`.
Fontes NOVAS prioritárias (texto extraível, página física):
- Acessos: ASTM F1166-07 (`ASTM/astm-f1166pdf-2.pdf`: escadas p92–99, rampas p101, vertical p102–107, guarda-corpo p108–110, passarelas p111, plataformas p114);
  ISO 14122-2:2016 (`BS/bs-en-iso-14122-2-2016.pdf`, p12–18); NBR 14718:2019 guarda-corpo edificação (p12–19); NBR 15708-2:2020 guarda-corpo PRFV (p8–13);
  NR-35 2025 Anexo III escadas (`NR/nr-35-atualizada-2025.pdf` p16–19); DNV-OS-C101 cargas de passarela (p26); API RP 2A 11.1.5 tolerâncias (p103).
- Escaneadas (OCR antes): ISO 14122-3:2001 (escadas/guarda-corpo), ISO 14122-2:2001, NBR 15708-3:2014 (grating).
- Outros temas: ASME B16.5 2017, B16.47, NORSOK L-005 (flanges); ASME B31.3 2018; ISO 13920:2023; DNV 2.7-1 / ST-E271 / ASME B30.x (içamento); ISO 898/4014/4032, ASME B18.2.x, ISO 16047 (parafusos/torque).
- Não existem nos zips: ISO 14122-1/4, NBR 9077, NBR 9050, NORSOK S-002/C-002.

Backlog:
- Recortar as figuras do ABS; perfil ASTM F1166 nas calculadoras (opcional).
- Ficha `flange-asme-b16-5` (09/out/2026): 14 tabelas dim./furação (classes 150–2500) + 4 tabelas P–T (grupos 1.1, 2.2, 2.3, 2.8),
  geradas por `ferramentas/extrair_b165.py` (sem argumento = só verifica; `--gravar` = reescreve o campo `tabelas`), conferidas mm × pol (2.987 valores).
  9 divergências são da própria norma (T ~1 mm; Tabela 14 NPS 22 Ah = 22.0). Ø de furo/parafuso ficam em polegadas, como na norma.
- 13/out/2026: fichas `icamento-unidade-portatil` (DNV-ST-E273/E271, NORSOK R-002 Anexo F/J, H205) e `lingadas-acessorios`
  (ASME B30.26/B30.10, NBR 15637-1, 15516-1/2, 13543, 11900-2/4, 6327, IMCA M179) revisadas pelo `revisor-fichas`: nenhum valor errado;
  itens/páginas, notas de conflito e algumas omissões corrigidos → 836 requisitos.
  Omissões FECHADAS em 26/out (+16 req. içamento, Tab. F.6 RDAF; +4 req. e Tab. 4 NBR 15516-1 em lingadas) — eram em `icamento-unidade-portatil`: bolsas de empilhadeira (E273 3.9.3/Tab. 3-6 p45; E271 4.4.6 p31), proteção superior
  (E271 4.1.4 p25–26), defletores ≤ 35°, vento 1,0 kN/m² e amarração (E273 3.7 p42–43), empilhamento/deck intermediário (E271 4.4.2–4.4.3),
  teste 1,6(R+S)g (E271 4.6.5 p38), Charpy de componentes (E271 8.4 p56; NORSOK F.7.2.4.5–6), RDAF/Tab. F.6 (NORSOK F.7.6 p187),
  munhão 1,3D (H205 5.1.4.7 p35). Em `lingadas-acessorios`: ensaios NBR 11900-2 5.1–5.3, Tab. 4 fatores de prova NBR 15516-1 (p19).
- 13/out/2026: integração de `referencias/` por prioridade. Feito: NBR 14718:2019 (+62 req., Tab. 1, 7 fig.) e NBR 15708-2:2015
  (+59 req., Tab. 1–2, 5 fig.; não há edição 2020 — o "2020" é a data de impressão) em `guarda-corpo`, ambas revisadas e corrigidas.
  NBR 15708-1:2014 (materiais/Barcol/tolerâncias do PRFV) não existe no acervo. Recortes a refazer (estético): fig8-fig9 da 14718, fig4 da 15708-2.
  NR-35 2025 (Portaria 1.860/2025; Anexo III em vigor 02/01/2026) nas 4 fichas de acesso + ficha NOVA `escada-portatil`
  (NR-35/NR-18/NR-34, 70 req.), revisadas e corrigidas → 8 fichas, 1067 req., 32 normas. Sugestão futura: ficha `ancoragem-linha-de-vida`
  (NR-35 Anexos I e II). Faltam na escada-portatil as definições "meio de acesso"/"posto de trabalho" (Glossário NR-35 p21).
  DNV-OS-C101 (Jul/2024 amd. Jul/2025; cargas de convés em t/m², γf, espessuras mín., S/200; comparação com a 2019) nas 4 fichas
  de acesso (+33 req.), revisada e corrigida → 1100 req., 33 normas. A C101 não dá carga de guarda-corpo (remete à ICLL / DNV-RU-SHIP
  Pt.3 Ch.11) — DNV-OS-C102 (FPSO) não está no acervo.
  API RP 2A 22ª ed. (2014; seção 11 da 21ª = 14 da 22ª) → ficha NOVA `tolerancias-fabricacao-estrutural` (83 req., 6 tab., 3 fig.;
  categoria "Estruturas e fabricação") — revisada em 14/out sem agente: script confere todo nº de requisito/tabela
  contra o texto da página citada (`ferramentas/conferir.py <ficha> <norma>`); Fig. 14.1 e Eq. 9.1 conferidas na imagem; 14.1.5.x conferido à mão. Nenhum erro. → 9 fichas, 1183 req., 34 normas.
  Usuário pediu (13/out/2026): NÃO usar agentes, economizar créditos.
  14/out/2026 (sem agentes): Tesseract 5.4 instalado (winget, eng+por). OCR em referencias/ocr/: ISO-14122-3-2001, ISO-14122-2-2001,
  NBR-15708-3-2014. ISO 14122-3:2001 → escada-degraus (+28 req., Tab. 1 step ladder) e guarda-corpo (+11); superada pela 2016 (fora do acervo).
  ISO 14122-2:2001 não incorporada (a 2016 já está). NBR 15708-3 → ficha NOVA `grating-piso-grade` (26 req., Tab. 1 e A.1).
  Pontos de OCR duvidoso (≤/≥, expoentes, tabelas) conferidos na imagem. → 10 fichas, 1248 req., 36 normas.
  14/out/2026: FOCO em referencias/ (pedido do usuário; flange e outros temas depois). Triagem: 24 incorporadas, 25 cobertas por
  outra cópia, 82 superadas, 98 sem texto, 231 fora de escopo, 756 pendentes (406 prioridade 1: solda 166, tubulação 97, parafusos 72,
  tolerâncias 55, pintura 32, flange 29, NRs 25, estrutura 18, içamento 13). Caminho escolhido: 1º índice automático de títulos por
  página (busca do site → "Nas normas do acervo", abre PDF#page) para TODOS — FEITO: 976 docs, 128 mil títulos, 6,7 MB; 2º extração de valores à mão nos prioritários, por lote.
  Lote 1 (içamento) FEITO 14/out: ISO 3266 (eyebolts, Tab. 2 e 4) + ASME B30.20 (balancim/BTH-1, ensaio 125 %) + API 9A (só
  tolerância de Ø — ed. 1995) em `lingadas-acessorios`; ASME B30.7 → ficha NOVA `guincho`. DNV 2.7-1/2.7-3 = edições antigas da E271/E273.
  Ficaram p/ ficha futura "guindaste/ponte rolante": NBR 8400, DNV 2-22, ABS Lifting Appliances 2021, API 8C. → 11 fichas, 1298 req., 40 normas.
  Lote 2 FEITO 14/out: ficha NOVA `ancoragem-linha-de-vida` (35 req.): NR-35 (copiados da escada-marinheiro), NBR 16325-2:2014 (tipo C,
  12 kN, ZLQ Anexo C), NBR 14628:2010 (retrátil 6 kN / 2 m), ANSI Z359.14-2021 (8 kN máx./6 kN médio). → 12 fichas, 1333 req., 43 normas.
  Lote 3 14/out: ABS Ergonomic 2021 já coberto (125 valores, cópia de T:); NR-37 trocada para a edição 2023 de referencias/ (inclui
  Portaria 4.219/2022; mesmas páginas/itens). ABS HFE Guidance 2014 e IOGP 454 = guias de processo (poucos valores) — não incorporados.
  Candidato: ficha de habitabilidade/plataforma (NR-37: pé-direito 2,40/2,20 m, 3,60 m²/pessoa, sanitários, 150 lux, extintores 1×1 m).
  Lote solda 14/out: ficha NOVA `solda-estrutural` (AWS D1.1:2020, 31 req.: pré-aquecimento Tab. 5.8, filete mín. Tab. 7.7, tolerâncias 7.21/7.22,
  perfis Tab. 7.9, aceitação visual Tab. 8.1 — tabelas são IMAGEM no PDF, conferidas renderizando; texto OCR numera "1.21" = 7.21).
  ISO 13920:2023 (Tab. 1–3) em `tolerancias-fabricacao-estrutural`. → 13 fichas, 1370 req., 45 normas.
  Resto de "solda" = partes avulsas ASME VIII Div.1 (UW, UCS, apêndices) e Sec. V/IX → lote "vaso de pressão" futuro; B16.25 → lote tubulação.
  Lote tubulação 14–15/out: ficha NOVA `tubulacao-processo` (categoria "Tubulação e flanges", consulta por NPS):
  ASME B36.10M-2000 (escaneada; Tab. 1 por OCR validada mm × pol → 44 tabelas por NPS), ASME B16.25-2022 (chanfros, Figs. 2-1/3.1-1/3.1-2/3.2-2/3.2-3,
  Tab. 3.3-1 → 36 tabelas por NPS com o MESMO rótulo de linha das B36.10M, para a consulta mostrar tubo + extremidade juntos; C conferido pela eq. 4.2;
  erros da própria norma anotados na nota de cada tabela), ASME B31.3-2018 (59 req.: preparação/alinhamento, pré-aquec. Tab. 330.1.1, TTAT Tab. 331.1.1,
  exame 341.4, aceitação Tab. 341.3.2, MT/PT/UT, testes 345; a 2020 do acervo é sem texto), API RP 14E 1991 (velocidades, erosional, Tab. 2.1/2.3).
  conferir.py: só faltas explicadas (OCR S/5, figura, conversões). → 14 fichas, 1468 req., 49 normas.
  Pendentes p/ tubulação: B16.9 (conexões), B16.11 (OCR), B36.19M (inox, não está no acervo), B31.3 projeto (eq. 304.1.2, Tab. 302.3.4 Ej / A-1),
  NR-13 (tubulações), API 5L, B31.4/B31.8, DNV-OS-F101.
  Lote parafusos 19/out: ficha NOVA `parafusos-porcas-arruelas` (categoria "Parafusos e fixação", consulta por ROSCA: "M12", "1/2"…; 31 req., 17 tab.):
  ISO 898-1:2013 (Tab. 3 props; Tab. 4/5 Fm/Fp M3–M39 validadas As × tensão), 898-2:2012 (Tab. 1/2/4), 3506-1:2009 (inox, Tab. 2–4),
  ISO 4017/4032/4033 (dimensões, extrator de "runs" por coluna), arruelas ISO 7089 (escaneada)/7091/7093-1 lidas da IMAGEM,
  ASME SA-193 Tab. 2, SA-194 Tab. 3/6, SA-325 Tab. 3–5, B18.2.6 Tab. 1, ISO 16047 (K, µtot), VIII-1 Ap. S (S = 45 000/√d). → 15 fichas, 1499 req., 64 normas.
  Nenhuma norma do acervo traz torque de aperto tabelado (nota de atenção na ficha). Pendentes: ISO 261/724 (passos — já nas tabelas),
  SA-320 (L7), SA-354/449/540, B18.2.1/2.2 (polegada), B18.2.6 porcas/arruelas estruturais, ISO 4759 (tolerâncias), 4042/10683 (revestimentos),
  DIN avulsas sem texto (931/933/934/912 — OCR), ISO 4014/4762/8765 (sem texto).
  Próximos lotes: tolerâncias 54, pintura 30, flange 29 (+ resto de tubulação e parafusos acima).
  23/out: SITE reorganizado — ficha em ABAS (Consulta rápida | Requisitos | Tabelas | Figuras | Notas; fichas com consulta-tabela abrem na Consulta);
  grupos de requisitos recolhíveis (1º aberto; busca abre os grupos com achados), filtro local "Filtrar nesta ficha", Expandir/Recolher tudo,
  figuras em miniatura DENTRO do grupo (campo "grupo" da figura ou "Fig. N" citado no item/nota), tabelas agrupadas por norma com filtro, zoom com legenda.
  +26 figuras: B31.3 (328.3.2, 328.4.2, 328.4.3, 328.5.2A/B/C, 341.3.2), AWS D1.1 (7.3, 7.4 A–F), ISO 4017/4032/7089, B18.2.6 Tab. 1,
  ISO 898-1 (Tab. 20, Fig. 11), NBR 16325-2 (Fig. 3, 8, C.1), Z359.14 Fig. B2, B30.7 Fig. 7-0.2, NBR 15708-3 (Fig. 1, 2, 3, B.1). Todas as figuras têm grupo.
  Sem figuras ainda: escada-portatil (NR-35/18/34 não têm desenhos no acervo). Verificação de figura×grupo: `node ferramentas/figuras_grupo.js` (mesma regra do app.js).
  Lote flange 23–26/out: ficha `flange-asme-b16-5` vira "Flanges ASME B16.5 e B16.47, juntas e flange compacto" (95 req., 80 tab., 7 fig.).
  Consulta com 3 filtros em CASCATA (app.js): Norma/série (ASME B16.5 | B16.47 Série A | Série B | NORSOK L-005) → Classe → NPS;
  chave das tabelas = {"serie", "classe"} (extrair_b165.py agora grava "serie" e preserva tabelas de outras normas).
  ASME B16.47-1996 + Addenda a-1998 (ESCANEADA, pol): Tab. 5–15 lidas por `ferramentas/ocr_celulas.py` (OCR célula a célula: grade por
  traço contínuo, bordas virtuais, Tesseract psm 7 só dígitos) + validação (furos múltiplos de 4, O>BC>R, X>A, monotonia, 2ª leitura a 300 dpi)
  + imagem; Ø parafuso = furo − 1/8. Rating 1.1 da pág. do Addenda (p14; corrige 850–1000 °F). B16.20-2012 (espiralada Tab. 9–14 por classe,
  RTJ Tab. 4), B16.21-2016 (Tab. 4, 5, 7, 8), NORSOK L-005 2006 (Tab. 2–6, A.1–A.6 WN, Tab. 8 TORQUE µ=0,12 — único torque tabelado do acervo).
  → 15 fichas, 1544 req., 68 normas. Pendentes flange: MSS SP-44, API TR 6AF, B16.36, B16.1, ratings B16.47 de outros grupos (p15–18, 46–62).
  Lote tolerâncias 26/out: ficha NOVA `tolerancias-gerais-ajustes` (19 req., 28 tab., 2 fig.; consulta Tabela → Ajuste → Faixa):
  NBR ISO 2768-1/-2:2001 (Tab. 1–3 / 1–4; simetria com células mescladas conferida na imagem), NBR 6158:1995 (Tab. 1 IT1–IT18 até 3150 mm;
  Tab. 2 afastamentos fundamentais c…s até 500 mm LIDOS DA IMAGEM; 16 ajustes furo-base calculados pela regra da norma ei = es − IT,
  g6 conferido 12/12 com a Tab. 30), ISO 9013:2017 (Tab. 4–8, A.1, Fig. 12 e A.1). → 16 fichas, 1563 req., 72 normas.
  Pendentes: NBR 6409/14646 (GD&T — símbolos), ISO 1302/NBR 4287 (rugosidade), furos não-H (Tab. 3) e eixos j/js/t…zc, ISO 286 2010 (OCR).
  Lote perfis 26/out: ficha NOVA `perfis-laminados` (14 req., 7 tab., 2 fig.; consulta Série → Perfil): DIN 1025-2 HEB 100–1000, DIN 1025-3 HEA
  100–1000 (lida da IMAGEM, OCR ruim), DIN 1025-1 I 80–550 (tabela girada: ROT=270 no ocr_celulas.py; anotação vermelha no PDF tapa linhas 120–160
  → lidas da imagem) — 68 perfis, TODAS as linhas validadas pela física (m = 0,785A, Wx = 2Ix/h, ix = √(Ix/A), Wy, iy, sx = Ix/Sx, A pela geometria
  nos de mesa paralela). EN 10034 (Tab. 1–3, massa ±4 %, comprimento), NBR 7007 (MR 250, AR 350…, CE ≤ 0,55). → 17 fichas, 1577 req., 77 normas.
  ocr_celulas.py: env WL (whitelist; use "0123456789, " p/ decimais com vírgula), DPI, ROT, VFRAC, LIM. Faltam: IPE/IPBv, W, cantoneiras/U (não há no acervo).
  Lote içamento (lacunas) 26/out: E273 3.7.2–3.7.3 (transporte FH = MGW·g, FV 1,3/0,7, vento 1,0 kN/m², lashing 1,3) e 3.9.3/Tab. 3-6; E271 4.1.4, 4.4.2 (FT = 0,5Pψg),
  4.4.3, 4.4.4, 4.4.6, 4.6.5 (1,6(R+S)g), 8.4; NORSOK F.7.2.4.5–6, F.7.6 RDAF (√ confirmada pela Tab. F.6); H205 5.1.4.7; NBR 11900-2 5.1–5.3, 6.2. → 1597 req.
  Lote vaso de pressão 26/out: ficha NOVA `vaso-pressao-asme-viii` (21 req., 3 tab.): ASME VIII-1 2001+A02 partes UG (UG-16, 27, 28, 32, 80, 99, 100, 125),
  UW (UW-11, 12, 13, 33, 35 — tabelas lidas da imagem), UCS (Tab. UCS-56). → 18 fichas, 1618 req., 80 normas. Pendentes: UCS-66 (MDMT), UG-37 (reforço de aberturas),
  UHA, apêndices (2 flanges, 13 retangulares), Sec. V/IX.
  Lote NR-13 26/out: ficha NOVA `nr-13-caldeiras-vasos` (94 req., 4 tab., 2 fig.): NR-13 redação 2018 + Portaria SEPRT 915/2019 (enquadramento, categorias
  de caldeira A/B e vaso I–V, dispositivos, placa/prontuário, instalação, Anexo I capacitação, prazos de inspeção com/sem SPIE, SIS/SGC, tubulações, tanques,
  glossário + tabela SIL) e Perguntas e Respostas MTE fev/2019 (id `NR-13-PR`). A NR-13 2018 do acervo = superada. → 19 fichas, 1712 req., 82 normas.
  Lote materiais 1 (26/out): ficha NOVA `materiais-asme-ii-d` (categoria "Materiais"; consulta Tabela → Especificação → Grau/classe/espessura·forma):
  ASME II-D 2019 MÉTRICO (`referencias/extraido/ASME/ASME SECTION II PART D 2019 ... METRIC.pdf`, 1262 págs.) — Tab. 1A (1613 linhas, p74–217),
  1B (1355, p222–345), 3 parafusos (237, p464–487) → 284 tabelas por spec + 3 tabelas de notas (G/H/S/T/W, textos em inglês); 14 req. (Ap. Obrig. 1
  critérios ST/3,5 e 2/3 SY, ×0,85 com costura, 0,9 SYRY inox; Ap. 2 parafusos ST/4, ST/5; notas gerais). Gerado por `ferramentas/extrair_iid.py --gravar`
  (palavras → linha pelo nº de linha mais próximo; ident. por x do cabeçalho; props por regex; S por temperatura). Na Tab. 3 de 2019 os cabeçalhos
  estão DESLOCADOS (sob "Size" vem o UNS etc.) — tratado no CFG. Validação: Su > Sy, S40 ≤ critério, S não cresce (só SA-268 TP409 cresce — está
  assim na norma, nota de atenção), todo código de nota tem texto, SA-516 70 conferido na imagem. dados.js 2,0 → 4,4 MB. → 20 fichas, 1726 req., 83 normas.
  Lote materiais 2 (26/out): + Tab. U (Su × T, 2199 linhas, p618–717) e Y-1 (Sy × T, 2245 linhas, p720–923) na mesma ficha (consulta "U —"/"Y-1 —";
  em U, como na Tab. 3, os cabeçalhos estão deslocados; em Y-1 forma/spec/grau ficam ~12 pt à esquerda do cabeçalho; linha com VÍRGULA decimal na
  pág. 858) → 798 tabelas. Conferência linha a linha: os 126 313 valores S/Su/Sy aparecem na página citada da própria linha (conferir.py não serve
  aqui — ele olha só a página da tabela). Ficha NOVA `propriedades-fisicas-asme-ii-d` (`ferramentas/extrair_iid_fis.py --gravar`): TE-1…TE-5
  (A/B/C por grupo; validado C ≈ B·(T−20)/1000 em 1 323 linhas — 6 divergências são da norma, nota), TCD (63 grupos), TM-1…TM-5, PRD (114),
  notas com a composição de cada grupo; 12 req. → 21 fichas, 1742 req., 83 normas; dados.js 6,9 MB. CSS: label[hidden] some e select não estoura.
  Faltam na Parte D: 2A/2B/4/5A/5B (Sm, Div. 2 / Sec. III), Y-2, cartas de pressão externa (CS-1… e tabelas A×B p1047–1099), apêndices.
  Lote materiais 3 (26/out): Partes A/B/C 2007 (348 especificações SA/SB/SFA) → 3 fichas NOVAS `especificacoes-asme-ii-a|b|c` geradas por
  `ferramentas/gerar_asme_ii.py [A B C] --gravar` (~1 min): por spec = grupo com título, "Identical with ASTM…", escopo 1.1 e TODAS as tabelas
  (2 267) recortadas em IMAGEM 1 bit 150 dpi (`assets/figuras/asme-ii/<a|b|c>/`, 23 MB) — SEM transcrição; o texto da tabela vai na nota
  só para a busca. Localizador `ferramentas/tabelas_asme_ii.py` (corpo 10 pt × tabela ≤ 9 pt; título "TABLE N"; largura pela regra
  horizontal; tabela de lado → página inteira girada 90°; 2 tabelas lado a lado → coluna). Cada spec = norma `ASME-SA-106`, `ASME-SB-…`,
  `ASME-SFA-5.1` em normas.json (422 normas). 25 specs sem "TABLE" (requisitos no texto) têm aviso "abrir o PDF". app.js: >12 normas → chips
  recolhidos. Triagem: 411 incorporadas / 877 relevantes (47 % dos docs, 26 % das págs.). dados.js 10 MB.
  Pendentes (370): sem assunto 63, solda 40, parafusos 39, offshore/naval 27 (4 289 págs., ABS/DNV), materiais 24, elétrica 19, tolerâncias 18,
  tubulação 17, NR 14, flange 14, vaso 14 (Sec. VIII D1/D2/D3 2007, I, V, IX), hidráulica 14. Por órgão: ASME 144, ABNT 58, ISO 50, API 27.
  Screenshot headless com "?q=" sai em branco (artefato do scroll suave) — conferir pelo --dump-dom.
  BLOCO ASME FECHADO (26/out): 0 pendentes ASME (421 incorporadas, 67 superadas, 31 cópias, 228 fora de escopo).
  `ferramentas/recortes.py` (genérico: corpo = moda das linhas de PROSA, sem rodapé 5 pt; "TABLE/Table/FIG./Figure" em negrito
  ou maiúsculas — citação no texto não conta; Seção IX "QW-451.1"+título; tabela termina em prosa/parágrafo em negrito; figura =
  desenhos/imagens entre legenda e próxima prosa na coluna do título completo, senão PÁGINA INTEIRA; página de lado girada, exceto
  se o PDF já tem /Rotate 90; texto quebrado 0,1 pt → página inteira; cópia OCR sem negrito aceita "Table 15"+título) e
  `ferramentas/gerar_docs.py [ficha] --gravar` (config FICHAS no topo; grupos por prefixo UG-/QW-/Apêndice N ou por documento;
  imagens 1 bit em assets/figuras/docs/<ficha>/) → 11 fichas NOVAS: asme-viii-1-2007 (348), asme-viii-2-2007 (498, +Ap. 4 OCR),
  asme-viii-3-2007 (125), asme-i-2007 (114), asme-ix-2007 (126), asme-x-2007 (76), asme-v-2007 (391, + 40 artigos SE/SD/SA/SB),
  asme-b16-conexoes-valvulas (242: B16.1/9/10/11/34/36/48), asme-b1-b18-roscas-fixadores (335), asme-b31-dutos (82: B31.4 OCR, B31.8),
  asme-outros (360: Y14.5, P30.1; PCC-2 do acervo = só sumário). OCR (referencias/ocr/, 570 MB) de B16.11, B16.34-2009, B31.4-2019
  (texto original ilegível), B1.20.1, B1.5, B1.8, B18.2.2, B18.2.3.7M, B18.2.4.1M, B18.3-2012, B18.3.1M, VIII-2 Ap. 4.
  ocr.py: página CINZA, mas o OCR roda em RGB (pdfocr_tobytes com pixmap de 1 canal grava camada de texto VAZIA) e a imagem
  embutida é trocada pela cinza. Triagem: SUPERADAS_ARQ (VIII-1 2001 em partes → VIII D1 2007; II-D 2007 → 2019), FORA_ARQ
  (SUMMARY/INTRODUCTION), COPIAS_ARQ, OCR_ARQ. Caminhos em normas.json sempre com "/" (glob do Windows devolve "\").
  2 agentes (a pedido do usuário): um achou a causa do OCR vazio; outro auditou 60 recortes → correções (VIII-2: tabelas curtas
  116/190 → 21/287; páginas inteiras 143 → 59; Y14.5 de cabeça para baixo; colunas). → 35 fichas, 7134 req., 490 normas,
  dados.js 12,5 MB, figuras 74 MB. Geral: 473/787 docs relevantes (60 %; 42 % das págs.). Pendentes: ABNT 72, ISO 67, DIN 44,
  API 38, NR 17, DNV 14, BS 12, ASTM 10, ABS 8. A ficha vaso-pressao-asme-viii continua com a VIII-1 2001 (migrar p/ 2007 depois).
  BLOCO ABNT FECHADO (26/out, com 2 agentes a pedido): 0 pendentes ABNT (86 incorporadas, 7 cópias, 4 superadas). Config dos lotes em
  `ferramentas/docs_abnt.py` (FICHAS + EXCLUIDOS; gerar_docs importa docs_*.py; triagem lê os EXCLUIDOS) → 8 fichas NOVAS:
  abnt-desenho-tecnico (333), abnt-eletrica-instalacoes (278), abnt-eletrica-equipamentos (154), abnt-estruturas (301: 8800, 14762,
  6123, 7190-1/-5, 15708-5, 8261, ISO 6892), abnt-tubulacao-gas-medicao (187), abnt-icamento-cabos-amarras (197: 8400, ISO 2408/3108,
  11900-3, 13715-2, 16776), abnt-vasos-cilindros-hidraulica (26), abnt-seguranca-gestao-outros (202). Códigos/edições corrigidos pelo
  agente (17240:2010, não "17240-5"; 14039 "2005 comentada" = edição 2003; ISO/CIE 8995-1:2013…). OCR de 15 NBR por
  `ferramentas/ocr_lote.py ABNT 3 <k>` (grava `referencias/ocr/_origem.json` ocr→original; a triagem usa) — referencias/ocr 881 MB.
  recortes.py p/ ABNT: "Tabela/Figura/Quadro" (nº "B.1", "1.A)"); título "N — Título" aceito sem negrito; "Figura" procura ACIMA da
  legenda; tabela cresce por grade/moldura (traços e caixas encostados, não atravessa legenda "Figura"); prosa com acento; sumário
  (pág. com "Sumário"/≥3 linhas "título … pág." / ≥5 legendas sem desenho) e índice ("Figura 2;") ignorados; 1 página inteira por página.
  → 43 fichas, 8872 req., 558 normas, dados.js 14,2 MB, figuras 94 MB. Geral: 547/787 docs relevantes (69,5 %; 53 % das págs.).
  Pendentes: ISO 65, DIN 44, API 38, NR 17, DNV 14, BS 12, ASTM 10, ABS 8, ISA 6, AGMA 5, AWS 4, BV 4.
  BLOCOS ISO e DIN FECHADOS (26/out, 2 agentes: config + auditoria): 0 pendentes ISO (78 inc., 14 cópias, 1 superada) e DIN (44 inc.,
  4 superadas, 2 cópias). `ferramentas/docs_iso.py` → 8 fichas iso-* (fixadores 2, roscas, hidráulica, engrenagens, desenho-gps, materiais,
  offshore-containers-máquinas); `ferramentas/docs_din.py` → 6 fichas din-* (parafusos-porcas, arruelas-rebites-condições, anéis-chavetas-
  estrias, engrenagens, aços-molas, conexões-abraçadeiras). Excluídos com motivo: ISO 3730 (arquivo danificado), tradução não oficial da
  5167, DIN 125-2/17221/ISO 7049:1990 (superadas), cópias parciais. OCR: 20 ISO (+4042/10683 0,1 pt, 8434-4 fonte deslocada) e 31 DIN
  (`ocr_lote.py ORG 3 k [idioma] [--mapa]`; nomes repetidos ganham "-2"). referencias/ocr = 1,3 GB.
  recortes.py (auditoria ISO): "Figure N —" (ISO) procura acima; "Table 1 -" + título na linha seguinte; página escaneada (imagem ≥80 %
  ou tiras finas unidas) conta como OCR; distâncias × largura/612 (cópias OCR de 1 860 pt); tabela para em título de seção numerado em
  negrito. gerar_docs: normas curtas (ISO ≤ 25 págs., DIN ≤ 80) → páginas com desenho/grade sem item viram página inteira (sem capa,
  aviso, sumário, prefácio, bibliografia; escaneada: dígitos > 0,35 × letras, ou sem texto; DIN: toda escaneada e a 1ª página conta).
  Limitações conhecidas: figuras raster em cópias OCR saem como página inteira; 2ª linha de legenda às vezes cortada; figura que começa
  na página anterior; DIN 3960 (172 p. escaneadas) só 7 itens.
  → 57 fichas, 10 327 req., 660 normas, dados.js 15,7 MB, figuras 115 MB. Geral: 653/784 relevantes (83 %; 62 % das págs.).
  Pendentes (131): API 38, NR 17, DNV 14, BS 12, ASTM 10, ABS 8, ISA 6, AGMA 5, AWS 4, BV 4, MSS 4, AISC/AISI/ANSI/DNIT 1.
  BLOCO FINAL FECHADO (26/out, agentes): os 131 pendentes → `ferramentas/docs_offshore.py` (API, DNV, ABS, BV, IACS/IOGP) e
  `ferramentas/docs_outros.py` (NR, ASTM, ISA, AGMA, AWS, MSS, BS, AISC/AISI, energia/trilho/arruelas) → 25 fichas NOVAS
  (api-* 6, dnv-* 3, abs-* 3, bv-nr445, iacs-iogp, nr-* 2, astm, isa, agma, aws, mss, bs-* 2, estruturas-aco-aisc-aisi, outros-energia-trilho-arruelas).
  OCR de todos os sem texto: `ocr_lote.py TODOS 3 k -` (idioma por órgão); `referencias/ocr/_origem.json` (ocr → original) lido pela triagem.
  Excluídos: API 17D_e2 (danificado, OCR falhou), ISO 3730 (danificado), duplicatas.
  → 82 fichas, 14 562 req., 779 normas, dados.js 20,2 MB, figuras 169 MB, referencias/ocr 1,8 GB.
  TRIAGEM FINAL: incorporada 775, coberta por outra cópia 113, superada 82, fora de escopo 246 → 775/775 relevantes (100 %; 100 % das págs.).
  Fichas por documento (recortes de tabela/figura + itens) — os valores numéricos estruturados continuam só nas fichas temáticas.
  Auditoria do bloco final (agente) → recortes.py: negrito também pelo NOME da fonte (Bold/Black); `secao_l()` (nº "3.4.4" sozinho em
  negrito — BV; "2.4.7 Título" em fonte ≥ corpo+2 — DNV) encerra tabela/figura; DNV "Guidance note"/"---e-n-d---" encerram; sumário ABS
  (pontilhado na linha seguinte) e citação "TABLE 2." ignorados; figura: desenho = só elementos não-texto com envoltória ≥ 15×15
  (antes linha de texto bastava → página inteira); "Figure 30—…" sem espaço = legenda embaixo; figura acima não sobe além de item já
  recortado; página inteira descartada se os recortes cobrem > 45 % da página; PNG em cinza (16 níveis) só se > 15 % de cinza médio.
  Bloco final regerado: páginas inteiras 851 → 577 (resto = escaneados API 610/682, AWS A2.4, RP 520-I); figuras 167 MB.
  gerar_docs NÃO apaga imagens antigas: apagar assets/figuras/docs/<ficha>/ antes de regerar.
  27/out: as 58 fichas por documento regeradas com o recortes.py novo. Ajustes após comparar com o backup: página inteira só é
  descartada se a MESMA figura (nº-base, "26" ≡ "26-a)") já tem recorte; nº sozinho em negrito ("0.5" de cota) não conta como seção
  na busca acima da legenda; "TABLE 2." sozinho só é título se a linha de baixo é título (negrito/maiúsculas; em cópia OCR, inicial
  maiúscula); sumário ABS com título em 2–3 linhas e pontilhado no fim. Comparar sempre item a item com backup antes de aceitar.
  CATÁLOGO DO ACERVO T: FEITO (27/out, agente catalogador-acervo): `conteudo/catalogo.json` (1,9 MB) por `ferramentas/catalogar.py`
  — 8 369 arquivos → 3 933 documentos únicos (4 436 cópias; espelho "1 - NORMAS" em `copias`; MD5 entre nomes diferentes);
  ASME 1 267, ASTM 881, Petrobras 585, ABNT 215, SSPC 175, API 69…; superada 1 019 / vigente 344 / desconhecida 2 570;
  278 já em referencias/ (`em_referencias`); 214 sem título. Build: 4 822 documentos buscáveis; dados.js 21,9 MB. Cache em %TEMP%\uva_cat.
  REVISÕES (27/out, agente revisor-fichas) aplicadas: perfis-laminados (DIN 1025-1: I 100 t 6,8; I 180 r2 4,1; I 200 s 7,5; I 220 r2 4,9
  — regra r1 = s; tolerâncias I → EN 10024 DIN 1025-1 item 5 p3; NBR 7007 Tab. 1 p6); vaso-pressao-asme-viii (+UCS-57 RT total
  P-No.1 > 1 1/4 in; UCS-56(d)(3)(5) e nota 3; UG-16(c); UG-32(f)); nr-13 ("Exclusão" → "Dispensa (13.2.2)" — inspeção por PH continua);
  parafusos (ISO 4017 c máx. — rótulos TROCADOS na cópia p12–15; ISO 4033 M14; Ap. S 1,5P × UG-99 1,3; nota de torque → NORSOK L-005);
  tolerancias (NBR 6158 4.3.4 — resto do texto não extrai, abrir p8). Sem erro: NR-13 valores, 2768, 6158 Tab. 1/2 e 16 ajustes (400 linhas).
  UMA FICHA POR NORMA (27/out, pedido do usuário; agentes dev-site + extrator de info): 61 fichas-agrupamento movidas p/ conteudo/docs/;
  `separar_normas.py --gravar` → 779 `norma-<id>.json` (slug = "norma-" + id minúsculo, não-alfanumérico → "-"; código legível: 1º hífen
  vira espaço, NR/DNV ficam; título sem repetir o código). Itens/figuras agrupados em Tabelas / Figuras / Páginas (livros de código mantêm
  UG-, UW-…). Site: home com fichas temáticas + "Normas" por órgão/assunto (recolhido, filtro); página da norma com Escopo, Itens, Tabelas,
  Figuras, Em fichas temáticas (calculado em tempo de execução), Sumário (UVA_INDICE; cópia OCR via ocr_origem), Definições, Referências
  normativas (link p/ a norma se existir). Rotas #/ficha/norma-<slug> e #/norma/<ID>. dados.js compacto: 16,7 MB. → 800 fichas (21 temáticas + 779).
  Fluxo p/ mudar recortes: gerar_docs.py --gravar (→ conteudo/docs) → separar_normas.py --gravar → build.py.
  `info_normas.py` (~15 s; com ids = só imprime): escopo 702, definições 293 (3 111), referências normativas 574, "substitui" 129;
  `fonte: "ocr"` em 101 (texto pode ter ruído). Só do PDF (normas.json escopo é fallback no separar). Faltas: NRs sem "Objetivo"
  (NR-12/15/16…), livros (ABS MVR, BV Parte C), DIN antigas; escopo de subitem em ASME I, BV NR445-B, DNV 2.22; refs só nas 1as 30 págs.
  27/out (3 agentes): `ferramentas/docs_tematicas.py` → ficha-fonte `recortes-normas-tematicas` (77 normas que só tinham valores
  nas temáticas: NRs, B16.5, B31.3, AWS D1.1, ISO 898…; 2 500 recortes; fora II-D). Opção de doc `sem_paginas_inteiras` (gerar_docs)
  p/ documentos só de texto (NR-35, NR-13-PR: caixas/faixas cinza viravam "página inteira"). OCR NBR 13541-1/-2 (normas.json → ocr).
  Escopo à mão: `conteudo/escopo_manual.json` (10 NRs sem "Objetivo", item inicial) e `escopo_manual_agente.json` (37 normas;
  ASME I/BV NR445-B/DNV 2.22 substituem o de subitem) — lidos pelo separar_normas → escopo em 772/779. Categoria da ficha de norma
  = órgão-base (orgao() no separar; nome completo em "orgao"). Agentes fecharam: NR-13 Anexo II SPIE + 13.4.4.11 (106 req.);
  ISO 9013 Tab. 3 Δa, págs. 28/19, Fig. A.1 refeita; ISO 898-1 Tab. 6/7 (rosca fina), B18.2.6 Tab. 3/4/5 (porca pesada, F436,
  chanfrada), ISO 16047 fórmula 10.2/10.4. → 17 075 req., dados.js 18,6 MB, figuras 210 MB.
  27/out (tarde, agentes): fichas NOVAS guindaste-ponte-rolante (179 req.: NBR 8400, DNV 2.22, ABS Lifting, NR-11; API 2C e
  B30.2/4/5 não estão no acervo) e habitabilidade-plataforma (168 req.: NR-37, NR-24, NR-17, NR-15, ASTM F1166, NBR 8995-1, 10152).
  Auditoria dos recortes → recortes.py: traço de espessura 0 engrossado (Rect | Rect vazio ignorava traços → tabela sem a última
  coluna, figura vetorial "sem desenho"); tabela alarga pelos traços; legenda acima/abaixo por VOTO no documento (voto_legenda);
  fallback não pega desenho encostado em outra legenda; figura RASTER pega a imagem encostada na legenda; título para em seção e
  em linha de cabeçalho de tabela; nº "4.4-Bevel" → "4.4"; legenda repetida no cabeçalho da página descartada.
  gerar_docs: página com desenho não coberto por recorte → página inteira ("desenho sem título localizável").
  Imagens com medidas (pedido do usuário; 3 agentes): todo grupo com cota nas fichas temáticas tem desenho da norma ou esquema SVG
  ("Esquema ilustrativo (não é desenho da norma)", item "Esquema"). Textos das fichas sem citação de página (agentes; ~1 200 trechos).
  28/out: gerar_docs.desenho_pagina (página com desenho não coberto → página inteira) refinado: cobertura por ELEMENTO (≥ 60 % dentro de
  um recorte), faixas de cabeçalho/rodapé de 60 pt ignoradas, elementos repetidos em ≥ 3 págs. (vinhetas) ignorados, área ≥ 12 % da página.
  Poda das 2 540 "desenho sem título" → 1 868 removidas, 672 ficam. NR-15 Tab. 6/6A recuperadas (dedupe de legenda no cabeçalho exige
  outro texto na mesma linha). → 802 fichas, 18 120 req., 15 201 imagens de norma; figuras 230 MB, dados 106 MB;
  verificar_autossuficiente.py: 0 erros → referencias/ PODE ser removida.
  28/out (4 agentes): `ferramentas/completar_escaneadas.py <lista> --gravar` acrescenta PÁGINA INTEIRA nas fichas-fonte (conteudo/docs) a partir
  de listas de auditoria guardadas em `conteudo/completar/` — escaneadas.json (579 págs. de normas escaneadas com tabela/desenho sem
  imagem; gerar_docs pula escaneadas) e legendas.json (966 págs. com legenda de tabela/figura sem recorte: II-D 433 — gráficos de
  pressão externa, tabelas 2A/2B/5A…; FIG. das specs II-A/B/C; legendas sem negrito, "Table 4--Título", título longo). SE REGERAR
  uma ficha com gerar_docs, rodar de novo completar_escaneadas com as listas (é idempotente). cortados.json (394, "forcar": recorte
  de tabela TRUNCADO em cópia OCR — recortes.py encerra cedo); excluir.json (62 capas/avisos/formulários/slides); "girar" em
  escaneadas.json (121 páginas de lado). → 19 998 req., figuras 274 MB.
  28/out (tarde): listas a mais em conteudo/completar/ — truncadas_nativo (144), tabelas_sem_titulo (578), desenhos_perdidos (9),
  formulas (1 553, texto nativo; revisadas — score < 12 e SA/SB conferidos), formulas_escaneadas (242), outros_escaneadas (14),
  figuras_incompletas (51 + 32 escaneadas). excluir.json (213: capas, formulários, checklists, "Changes", propaganda) e
  `completar_escaneadas.py --limpar --gravar` tira das fichas-fonte as páginas excluídas. 2ª poda (sumário/SAMPLE ONLY/Guidance note DNV
  em desenho_pagina) → 522 "desenho sem título" restantes. extrair_textos.py REESCRITO (agente): rawdict, ligaduras, fontes de
  símbolo/matemáticas ASME 2007 ("p" → "="), linhas só de números mantidas (antes sumiam ~750 mil números de tabelas);
  `conteudo/completar/texto_fonte.json` {id: PDF} força a fonte do TEXTO (OCR refeito em referencias/ocr/v2/: AWS D1.1, API 682,
  B16.34, B1.5, API 5B…; tessdata_best psm 1 ou 400 dpi+binarização). → 22 318 req., 19 644 imagens, figuras 337 MB, textos 70 MB.
  Depois: tabelas_escaneadas_restantes (92), podas_recuperadas (136: páginas podadas com fórmula/tabela/figura real),
  nbr15280_1 (14; a marca d'água ABNT engana os detectores). COTAS: tabelas das fichas temáticas têm "figuras" (desenho com as letras
  das colunas; da norma em tem/ ou esquema SVG) — exibido na Consulta rápida (1º bloco; "ver acima" nos seguintes) e na aba Tabelas.
  Conferido tabela × desenho por agente (238 tabelas). → 22 560 req.
  continuacoes_tabela (279: tabela que continua na página seguinte sem título; 2 agentes). FIM DA AUDITORIA (28/out): 802 fichas,
  22 839 req., figuras 349 MB, dados 110 MB; verificador 0 erros → referencias/ PODE ser removida (as ferramentas que leem PDF param).
  >>> CONTINUAR AMANHÃ (29/out) — REPOSITÓRIO PÚBLICO (regra no topo das Regras). Estado em 28/out 17h:
  - Os 4 agentes PARARAM às 16h35 no limite da API (reset 19h). Feito até lá (conferido 16h45):
    (1) SITE: build.py já gera dados/dados_local.js (completo, 21,6 MB) + dados/dados.js (PÚBLICO, 5,0 MB: 23 temáticas +
        3 832 docs do catálogo) e AVISA as figuras de norma omitidas; index.html carrega o local se existir ("?publico=1" força
        o público) — testado: as duas versões abrem. app.js estava no meio da aba "Resumo"/busca de resumos (node --check OK);
        FALTA: terminar Resumo, destaque de cota (SVG inline embutido no dados.js), .gitignore, README.md, verificar --publico.
    (2–4) DESENHOS: 64 SVG em esquemas/; "cota" só em grating 4, habitabilidade 2, guincho 1, materiais 1 — quase tudo por fazer.
        Figuras de NORMA ainda nas temáticas (omitidas no público): 403 — tubulacao 85, flange 68, tolerancias-gerais 38,
        lingadas 32, guarda-corpo 23, parafusos 22, escada-marinheiro 21, icamento 19, perfis 14, tol.-fabricação 13, guindaste 11,
        passarela 11, solda 10, vaso 10, escada-degraus 8, ancoragem 5, nr-13 5, grating 4, habitabilidade 2, guincho 1, materiais 1.
    Retomar: mesmos 4 escopos (site; acessos; tubulação/fixação/estrutura; içamento/equipamentos) — prompts = regra do topo +
    "substituir cada figura de norma por SVG próprio desenhado do zero; 'cota' em todo requisito dimensional; sem valores no SVG".
    Conferir: `grep -c '"cota"' conteudo/fichas/<id>.json`; o build lista as figuras de norma restantes.
  - 29/out: SITE FEITO (agente): aba Resumo (1ª aba da norma), busca nos resumos, botão "cota" (SVG inline com a cota em laranja e
    " = valor"; painel fixo no desktop, linha abaixo no celular), .gitignore (+ dados/indice.js, normas_info.json,
    escopo_manual_agente.json = texto de norma), README.md, `verificar_autossuficiente.py --publico` (lê o .gitignore; sai 1 se houver
    pendência). build PARA se dados.js público citar imagem local. figuras_grupo.js lê dados_local.js. Pendências --publico:
    notas da II-D copiadas em inglês em materiais-asme-ii-d.json (tabelas 793–797) → reescrever. Resumos: piloto NRs em andamento.
  - 29/out 08h20 (todos os agentes parados no limite de 5 h até 12h50): figuras de norma nas temáticas 403 → 68 (só flange-asme-b16-5);
    163 SVG de cota; resumos 5 (NR-11, 12, 17, 18, 37 — faltam NR-13, 13-PR, 15, 24, 34, 35 do piloto). Em curso ao parar: agente
    tubulação/flange (falta flange), acessos (conferir fichas de acesso: o build já não lista figuras de norma nelas), site (mapa
    tabelas[].cotas {coluna: esquemas/x.svg#nome}, criado pelo agente de içamento — build já avisa colunas sem cota), notas II-D (reescrever).
    Retomar com SendMessage aos mesmos agentes ou novos com o mesmo escopo.
  - Notas da II-D REESCRITAS em português (materiais-asme-ii-d + propriedades-fisicas; 226 textos). extrair_iid*.py --gravar
    regravaria o inglês: aplicar depois o mapa `ferramentas/notas_iid_pt.py` (PT["1a:G5"] etc.).
  - 29/out 10h: 89 resumos. Usuário pediu MENOS RAM → 1 agente por vez. Parados (retomar em sequência, pulando o que já tem arquivo):
    lote 3 (ISO/ABNT/DNV/outros citados nas temáticas), especificações ASME-SA (formato curto), NBR restantes. Rodando: lote 2 (ASME/API/AWS/ASTM).
  - 30/out: REPOSITÓRIO PÚBLICO criado e enviado: https://github.com/matheusmerlim1/Referencias-normativas (branch main; 1º commit
    c2d79d0 = camada pública; autor git matheusmerlim1). Antes de cada commit: build + `verificar_autossuficiente.py --publico` = 0.
    Resumos: 714/779 (faltam ~65: ABS/BV/IACS/IOGP/ISA…, agente em curso). Depois: desenhos próprios com cotas nos resumos (só 78 têm cota).
  - 30/out: resumos 779/779 (commit 76007e2); GitHub Pages no ar (https://matheusmerlim1.github.io/Referencias-normativas/).
    COTAS NOS RESUMOS por lotes (1 agente): LOTE 1 FEITO (aae2ef7: acessos/ergonomia/NRs, 212 valores, +18 SVG). PAUSADO a pedido do
    usuário. Faltavam ~1 030 valores dimensionais sem cota em ~307 resumos. Próximos: lote 2 içamento (DNV-ST-E273/E271, DNV 2.22,
    ABS-LIFT, NBR 8400, NORSOK R-002, B30.x, ISO 3266, NBR lingadas); lote 3 tubulação/flange/solda (B31.3, B16.5/16.25/16.47/16.20,
    AWS D1.1, API RP 14E, VIII-1); depois o resto por uso. Sem valores no SVG; build + --publico = 0 antes de cada commit.
  - PRÓXIMO: (a) terminar o que os 4 agentes não terminaram; (b) RESUMOS próprios por norma (conteudo/resumos/<slug>.json, texto
    REESCRITO + valores/itens + esquemas) — 779 normas, por lotes de ~2–4 agentes, prioridade: as 91 citadas nas temáticas
    (NRs, B16.5, B31.3, AWS D1.1, ISO 898…), depois por órgão; ler o texto em dados/textos (local) e escrever com palavras próprias;
    (c) git init + 1º commit SÓ da camada pública (conferir `git status` contra o .gitignore e o --publico antes);
    gh CLI NÃO está logado — o usuário cria o repositório público (ou `gh auth login`) e passa o endereço; aí push.
  - referencias/ ainda existe (auditoria de imagens terminou; pode ser removida — o usuário decide; ver linha acima).
  Pendentes das revisões (antigos, agora FECHADOS): NR-13 Anexo II SPIE e 13.4.4.11; ISO 9013 páginas (p19/p28 segundo o revisor — não confirmado), Tab. 3 Δa,
  recorte Fig. A.1; ISO 898-1 Tab. 6/7 (rosca fina); ISO 16047 fórmula completa; B18.2.6 porcas/F436.
  Partes A/B/C 2007 (≈100 SA, 66 SB, 30 SFA): composição química e ensaios por spec — próximo; SA-516/240/285 NÃO estão na Parte A do acervo.
  Método barato: idx.js/índice p/ achar páginas → dump só das páginas → script em scratchpad com helpers (uva.py) → build → conferir.py.
  Depois: temas novos (B16.47, NORSOK L-005, B31.3, ISO 13920, parafusos/torque).
- Catálogo do acervo T: FEITO 27/out (`conteudo/catalogo.json`); falta a aba "Acervo" no site, se desejado.
- Agentes: em 13/out o usuário pediu para não usar; desde 26–27/out pede agentes (≈ 2 em paralelo, escopo estreito; coordenador aplica correções).
- Integrar as normas de `referencias/` (zips extraídos para `referencias/extraido/`, inventário em `conteudo/referencias.json`) — prioridade ISO 14122-1..4, NORSOK, NBR.
- Fichas novas: andaime, flanges (ASME B16.5), solda (AWS D1.1), parafusos/torque, tubulação (N-0057/N-0115), pintura (N-2…/SSPC), grating, olhais de içamento (DNV-ST-E273).
- Catálogo completo do acervo (`conteudo/catalogo.json`) e aba "Acervo" no site.
- Busca em texto completo (fallback) para temas sem ficha: índice por página dos PDFs principais.
