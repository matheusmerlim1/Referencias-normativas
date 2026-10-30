# Projeto Uva — consulta de normas técnicas com valores

Página web para consulta rápida de normas técnicas de engenharia (acessos, guarda-corpo, içamento, solda, tubulação,
flanges, parafusos, tolerâncias, vasos de pressão…). Você busca um assunto (ex.: "escada", "filete", "B16.5") e vê
quais normas se aplicam e os **valores, cotas, tolerâncias e notas** de cada uma, lado a lado, com a norma e o item de origem.

## Como abrir

Dê duplo clique em `index.html`. Não precisa de servidor, instalação nem internet (JavaScript puro, sem frameworks;
funciona em `file://`).

## Camada pública × camada local

Este repositório traz só conteúdo próprio do projeto:

| Camada | O que tem | Onde |
|---|---|---|
| **Pública** (versionada) | código do site e das ferramentas; fichas temáticas (valores + norma/item, notas escritas por nós); resumos próprios por norma (texto reescrito); desenhos próprios em SVG ("esquema ilustrativo — não é desenho da norma"); metadados das normas e do catálogo | `index.html`, `assets/`, `ferramentas/`, `conteudo/fichas/<tema>.json`, `conteudo/resumos/`, `assets/figuras/esquemas/`, `dados/dados.js` |
| **Local** (no `.gitignore`) | PDFs, texto completo das normas, recortes de tabelas/figuras, fichas por norma | `referencias/`, `dados/textos/`, `dados/busca/`, `dados/dados_local.js`, `conteudo/docs/`, `conteudo/fichas/norma-*.json`, `assets/figuras/docs/`, `tem/`, `asme-ii/`, `assets/figuras/*.png` |

O `index.html` carrega `dados/dados_local.js` se existir (versão completa, de uso interno); senão abre a versão pública
(`dados/dados.js`). Para ver a versão pública numa máquina que tem a local: `index.html?publico=1`.

## Como gerar os dados

```
python ferramentas/build.py
```

Valida `conteudo/` (fichas, resumos, cotas dos esquemas) e gera `dados/dados.js` (público) e `dados/dados_local.js` (completo).
O build avisa quantas figuras de norma ainda estão nas fichas temáticas (são omitidas na versão pública).

Antes de publicar, confira que nada protegido entrou na camada versionada:

```
python -P ferramentas/verificar_autossuficiente.py --publico
```

## Aviso

Os valores vêm das normas citadas em cada linha (norma + item) e foram transcritos/resumidos para consulta.
**Não substituem a norma**: confirme sempre o texto e a edição vigente antes de projetar, fabricar ou emitir documento.
As normas são propriedade dos respectivos órgãos (ABNT, ASME, ISO, API, DNV, AWS, MTE…) e não são distribuídas aqui.
