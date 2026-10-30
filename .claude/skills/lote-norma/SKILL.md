---
name: lote-norma
description: Incorporar uma norma (ou lote de normas) de referencias/ numa ficha do Projeto Uva pelo método barato, sem agentes — achar páginas pelo índice, extrair só essas páginas, gravar os requisitos por script, build e conferir. Use ao criar ficha nova ou acrescentar norma a uma ficha.
---

# Lote de norma (método barato)

1. **Achar o documento e as páginas** — sem abrir o PDF inteiro:
   - situação/prioridade: `conteudo/triagem_referencias.json` (grep pelo código da norma);
   - títulos de seção/tabela/figura por página: `grep -i "<termo>" dados/indice.js` → arquivo + página física.
2. **Extrair só as páginas** (pasta curta; glob no lugar de acento):
   `PYTHONIOENCODING=utf-8 python -P ferramentas/dump.py <scratchpad>/d "<glob do pdf>"` e ler só os .txt das páginas achadas.
   Sem texto → `ferramentas/ocr.py` (Tesseract) antes. Tabela/figura que é imagem → `crop.py` a 200 dpi e ler a imagem.
3. **Gravar** com um script no scratchpad (não editar JSON grande à mão): carregar a ficha, acrescentar
   `requisitos`/`tabelas`/`figuras`/`notas`, salvar. Cada valor: `norma` (id em normas.json), `item`, `pagina` = página FÍSICA.
   Valor lido de figura → dizer em `nota`. Divergência entre normas → nota `atencao`. Norma nova → registrar em `conteudo/normas.json`.
4. `python ferramentas/build.py` (valida e gera dados/dados.js).
5. `python -P ferramentas/conferir.py <ficha> <id-norma>` — só sobra o que é figura/fórmula/OCR; conferir esses na imagem.
6. `python -P ferramentas/triagem_referencias.py` e atualizar "Situação" no CLAUDE.md em 1–3 linhas (nº de fichas/req./normas).

Regras: valores só do texto da norma (nunca de memória); escrever só nesta pasta; sem agentes (economia).
