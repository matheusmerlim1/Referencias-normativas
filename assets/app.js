/* Projeto Uva — busca de normas com valores.
   Dados: window.UVA_DADOS (gerado por ferramentas/build.py). Sem dependências.
   Dois tipos de ficha: temática (sem "tipo") e de norma ("tipo": "norma", uma por norma). */
(function () {
  "use strict";

  const D = window.UVA_DADOS;
  const app = document.getElementById("app");
  const campo = document.getElementById("q");

  if (!D) {
    app.innerHTML = '<div class="cartao vazio">dados/dados.js não encontrado. Rode <code>python ferramentas/build.py</code>.</div>';
    return;
  }

  const NORMAS = Object.fromEntries(D.normas.map(n => [n.id, n]));
  const FICHAS = Object.fromEntries(D.fichas.map(f => [f.id, f]));
  const TEMATICAS = D.fichas.filter(f => f.tipo !== "norma");
  const FICHA_DA_NORMA = {};
  for (const f of D.fichas) if (f.tipo === "norma" && f.norma) FICHA_DA_NORMA[f.norma] = f;
  /* Camada pública (dados/dados.js, repositório): sem fichas de norma, recortes, texto completo nem índices — só fichas
     temáticas, RESUMOS próprios por norma (conteudo/resumos) e metadados. Camada local (dados_local.js): tudo. */
  const PUBLICO = !!D.publico;
  const RESUMOS = Object.fromEntries((D.resumos || []).map(r => [r.id, r]));
  const SVGS = D.svgs || {};

  // ---------- cotas: "cota": "esquemas/<arquivo>.svg#<nome>" -> SVG inline (texto embutido em D.svgs) com <g id="cota-<nome>"> realçado ----------
  const temCota = r => !!(r && r.cota && SVGS[String(r.cota).split("#")[0]]);
  const attrCota = r => temCota(r) ? ` data-cota="${esc(r.cota)}" data-cv="${esc(r.valor)}" data-cr="${esc(r.parametro)}"` : "";
  const botaoCota = r => temCota(r) ? ` <button type="button" class="btn-cota" title="Mostrar esta cota no esquema">cota</button>` : "";
  const NS_SVG = "http://www.w3.org/2000/svg";
  /** HTML do SVG com a cota <nome> destacada (demais esmaecidas) e o valor escrito junto ao rótulo. */
  function svgCota(ref, valor, sep = " = ") {
    const [arq, nome] = String(ref).split("#");
    const src = SVGS[arq];
    if (!src) return "";
    const box = document.createElement("div");
    box.innerHTML = src;
    const svg = box.querySelector("svg");
    if (!svg) return "";
    const w = parseFloat(svg.getAttribute("width")), h = parseFloat(svg.getAttribute("height"));
    if (!svg.getAttribute("viewBox") && w && h) svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.removeAttribute("width"); svg.removeAttribute("height");
    svg.classList.add("esq-svg");
    let alvo = null;
    svg.querySelectorAll("g.cota, g[id^='cota-']").forEach(g => {
      if (g.id === "cota-" + nome) alvo = g;
      else g.classList.add("cota-esmaecida");
    });
    if (alvo) {
      alvo.classList.add("cota-ativa");
      const ts = alvo.querySelectorAll("text");
      const t = ts[ts.length - 1];
      if (t && valor) {
        const v = String(valor).replace(/\s+/g, " ").trim();
        const sp = document.createElementNS(NS_SVG, "tspan");
        sp.setAttribute("class", "cota-valor");
        sp.textContent = sep + (v.length > 38 ? v.slice(0, 37) + "…" : v);
        t.appendChild(sp);
      }
      alvo.parentNode.appendChild(alvo); // desenhada por cima das outras
    }
    return box.innerHTML;
  }
  /* Cotas de TABELA: "cotas": {"<coluna>": "esquemas/x.svg#nome"} na tabela e, por convenção, coluna cuja 1ª palavra é <p>
     quando um SVG de esquemas/ em tabela.figuras tem id="cota-<p>" (mesma regra do build.py). */
  const RX_NOME_COTA = /^[A-Za-z0-9_.\-]+$/;
  const temIdCota = (arq, nome) => !!SVGS[arq] && new RegExp(`\\bid\\s*=\\s*["']cota-${nome.replace(/[.\-]/g, "\\$&")}["']`).test(SVGS[arq]);
  const cacheCotasTab = new WeakMap();
  /** Por índice de coluna, a ref "esquemas/x.svg#nome" da cota (ou null). */
  function cotasDaTabela(t) {
    if (cacheCotasTab.has(t)) return cacheCotasTab.get(t);
    const mapa = t.cotas && typeof t.cotas === "object" ? t.cotas : {};
    const svgs = (t.figuras || []).map(x => typeof x === "string" ? x : x?.arquivo).filter(a => a && /^esquemas\/.+\.svg$/.test(a) && SVGS[a]);
    const refs = (t.colunas || []).map(c => {
      const r = mapa[c];
      if (r && SVGS[String(r).split("#")[0]]) return r;
      const w = String(c).trim().split(/\s+/)[0] || "";
      if (!RX_NOME_COTA.test(w)) return null;
      const arq = svgs.find(a => temIdCota(a, w));
      return arq ? `${arq}#${w}` : null;
    });
    cacheCotasTab.set(t, refs);
    return refs;
  }
  /** Unidade da coluna: "(mm)", "(pol)", "(kN)"… no fim do nome; senão a da tabela (se curta, ex. "mm"). */
  const unidadeCol = (t, c) => (String(c).match(/\((mm²?|pol|in|m|kN|N|t|kg|°|MPa|%)\)\s*$/) || [])[1]
    || (String(t.unidade || "").length <= 4 ? t.unidade || "" : "");
  /** Atributos data-* da célula k da linha l ("" se a coluna não tem cota ou a célula não tem valor). */
  function attrCotaCel(t, k, l) {
    const ref = cotasDaTabela(t)[k];
    const v = String(l[k] ?? "").trim();
    if (!ref || !v || v === "—" || v === "-") return "";
    const u = unidadeCol(t, t.colunas[k]);
    const val = u && /^[-+−]?[\d.,/ ]+$/.test(v) ? (u === "°" ? v + "°" : `${v} ${u}`) : v;
    // grandeza que não é a própria cota (ex. carga em kN ligada ao ângulo β): "β → 12 kN", e não "β = 12 kN"
    const seta = /^(kN|N|t|kg|MPa|%)$/.test(u) ? ` data-cs=" → "` : "";
    return ` data-cota="${esc(ref)}" data-cv="${esc(val)}" data-cr="${esc(t.colunas[k])}" data-cx="${esc(`${t.colunas[0]} ${l[0]} — ${t.titulo}`)}"${seta}`;
  }

  /** Painel com o esquema da cota: fixo ao lado (desktop) ou numa linha logo abaixo do requisito (tela estreita). */
  let painelCota = null, chaveCota = "";
  const telaEstreita = () => matchMedia("(max-width: 760px)").matches;
  function fecharCota() {
    document.getElementById("tr-painel-cota")?.remove();
    painelCota?.remove();
    chaveCota = "";
    document.querySelectorAll(".cota-sel").forEach(x => x.classList.remove("cota-sel"));
  }
  /** el = linha de requisito (tr), célula de tabela (td) ou valor da Consulta rápida (.kpi), com data-cota/cv/cr[/cx/cs]. */
  function mostrarCota(el) {
    const ref = el.dataset.cota, valor = el.dataset.cv || "", rot = el.dataset.cr || "", ctx = el.dataset.cx || "", sep = el.dataset.cs || " = ";
    const estreita = telaEstreita();
    // no celular o painel entra logo abaixo: depois da linha (tr) ou do bloco de valores (.kpis)
    const ancora = el.tagName === "TD" ? el.closest("tr") : el.classList.contains("kpi") ? (el.closest(".kpis") || el) : el;
    const chave = ref + "|" + valor + "|" + rot + "|" + ctx;
    if (chave === chaveCota && document.body.contains(painelCota) && (!estreita || ancora.nextElementSibling?.id === "tr-painel-cota")) return;
    if (!painelCota) {
      painelCota = document.createElement("div");
      painelCota.className = "cartao painel-cota";
      painelCota.addEventListener("click", e => {
        if (e.target.closest(".pc-fechar")) { fecharCota(); return; }
        const esq = e.target.closest(".esq-cota");
        if (esq) abrirZoom(null, painelCota.querySelector(".pc-leg").innerHTML, esq.innerHTML);
      });
    }
    painelCota.innerHTML = `<div class="pc-topo"><b>${esc(rot)}</b><button type="button" class="pc-fechar" aria-label="Fechar" title="Fechar (Esc)">×</button></div>
      <div class="pc-valor">${esc(valor)}</div>
      <div class="esq-cota" title="Clique para ampliar">${svgCota(ref, valor, sep)}</div>
      <div class="pc-leg meta">${esc(rot)}${esc(sep)}${esc(valor)}${ctx ? `<br>${esc(ctx)}` : ""}<br>Esquema ilustrativo (não é desenho da norma)</div>`;
    chaveCota = chave;
    document.querySelectorAll(".cota-sel").forEach(x => x.classList.remove("cota-sel"));
    el.classList.add("cota-sel");
    document.getElementById("tr-painel-cota")?.remove();
    if (estreita && ancora.tagName === "TR") {
      const linha = document.createElement("tr"), td = document.createElement("td");
      linha.id = "tr-painel-cota"; linha.dataset.t = "";
      td.colSpan = ancora.children.length;
      td.appendChild(painelCota);
      linha.appendChild(td);
      ancora.after(linha);
      painelCota.classList.add("em-linha");
    } else if (estreita) {
      const caixa = document.createElement("div");
      caixa.id = "tr-painel-cota";
      caixa.appendChild(painelCota);
      ancora.after(caixa);
      painelCota.classList.add("em-linha");
    } else {
      painelCota.classList.remove("em-linha");
      document.body.appendChild(painelCota);
    }
  }
  document.addEventListener("click", e => {
    const el = e.target.closest(".com-cota");
    if (!el || e.target.closest("a, .figura, .painel-cota")) return;
    mostrarCota(el);
  });
  document.addEventListener("mouseover", e => {
    const el = e.target.closest(".com-cota");
    if (el && !telaEstreita() && matchMedia("(hover: hover)").matches) mostrarCota(el);
  });
  window.addEventListener("hashchange", fecharCota);
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !document.querySelector(".zoom")) fecharCota(); });

  // ---------- utilidades ----------
  const semAcento = s => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  // nome de linha de tabela sem espaços: "W 100 x 19,0" = "w100x19" (×/* = x, vírgula = ponto, ",0" final some)
  const compacto = s => semAcento(s).replace(/\s+/g, "").replace(/[×*]/g, "x").replace(/,/g, ".").replace(/\.0+(?=x|$)/g, "");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (n, d = 0) => Number(n).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const ordemNatural = (a, b) => String(a).localeCompare(String(b), "pt", { numeric: true, sensitivity: "base" });

  function urlArquivo(a, pagina) {
    if (!a) return null;
    const c = a.replace(/\\/g, "/");
    return (/^[A-Za-z]:\//.test(c) ? "file:///" : "") + encodeURI(c).replace(/#/g, "%23") + (pagina ? "#page=" + pagina : "");
  }
  /* O site é autossuficiente: não mostra item/página nem abre PDF da pasta de originais (que será removida). A página citada nos dados
     só serve de âncora interna (#tp-N) no "Texto completo" da norma (dados/textos/<arquivo>.js, carregado sob demanda). */
  const listaTextos = () => window.UVA_TEXTOS_LISTA || {};
  const temTexto = id => !!(id && listaTextos()[id]);
  /** Link discreto para o trecho da norma no Texto completo (sem mostrar o nº da página). */
  function linkTexto(normaId, pagina, trecho, rotulo = "ver no texto") {
    if (!temTexto(normaId) || !pagina) return "";
    return `<a href="#" class="ir-texto" data-norma="${esc(normaId)}" data-tp="${+pagina}"${trecho ? ` data-tr="${esc(String(trecho).slice(0, 120))}"` : ""} title="Ver este trecho no texto completo da norma">${rotulo}</a>`;
  }
  /** Carrega dados/textos/<arquivo> por <script> (funciona em file://). cb(paginas | null). */
  const _carregando = {};
  function carregarTexto(normaId, cb) {
    const T = window.UVA_TEXTOS || {};
    if (T[normaId]) { cb(T[normaId]); return; }
    const info = listaTextos()[normaId];
    if (!info) { cb(null); return; }
    let c = _carregando[normaId];
    if (!c) {
      c = _carregando[normaId] = [];
      const s = document.createElement("script");
      s.src = "dados/textos/" + encodeURIComponent(info.arquivo);
      const fim = () => {
        const pags = (window.UVA_TEXTOS || {})[normaId] || null;
        delete _carregando[normaId];
        s.remove();
        c.forEach(f => f(pags));
      };
      s.onload = fim; s.onerror = fim;
      document.head.appendChild(s);
    }
    c.push(cb);
  }
  /** Documento do índice (caminho de PDF) -> id da norma (também via cópia OCR <-> original). */
  let _normaArq;
  function normaDoArquivo(arq) {
    if (!_normaArq) {
      _normaArq = new Map();
      for (const n of D.normas) if (n.arquivo) _normaArq.set(normCaminho(n.arquivo), n.id);
      for (const [ocr, orig] of Object.entries(D.ocr_origem || {})) {
        const a = _normaArq.get(normCaminho(ocr)), b = _normaArq.get(normCaminho(orig));
        if (a && !b) _normaArq.set(normCaminho(orig), a);
        if (b && !a) _normaArq.set(normCaminho(ocr), b);
      }
    }
    return _normaArq.get(normCaminho(arq)) || null;
  }
  /** Link para a página da norma (ficha "norma-<slug>" se existir; senão página montada só com normas.json). */
  const linkNorma = id => FICHA_DA_NORMA[id] ? `#/ficha/${FICHA_DA_NORMA[id].id}` : `#/norma/${encodeURIComponent(id)}`;
  const chipNorma = id => `<a class="chip" href="${linkNorma(id)}" title="${esc(NORMAS[id]?.titulo || "Ver a norma")}">${esc(id)}</a>`;

  // ---------- normas: entradas para a lista e a busca (montadas na 1ª vez que forem usadas) ----------
  function orgaoCurto(n) {
    const id = n.id || "", org = String(n.orgao || "").trim();
    if (id.startsWith("NR-")) return "NR";
    if (id.startsWith("NBR-")) return "ABNT";
    const m = org.match(/^[A-Za-z]+/);
    return (m && m[0].length <= 8 ? m[0].toUpperCase() : org.split("(")[0].trim()) || "Outros";
  }
  /** "ASME B16.5 — Pipe Flanges…" -> ["ASME B16.5", "Pipe Flanges…"]; sem ficha: código pelo id. */
  function codigoTitulo(id, f) {
    if (f && f.titulo) {
      const i = f.titulo.indexOf(" — ");
      if (i > 0) return [f.titulo.slice(0, i), f.titulo.slice(i + 3)];
    }
    const n = NORMAS[id] || {};
    let tit = (f && f.titulo) || n.titulo || "";
    const i = tit.indexOf(" — "), num = (id.match(/\d+/) || [""])[0];
    if (i > 0 && i < 40 && num && tit.slice(0, i).includes(num)) tit = tit.slice(i + 3);
    return [id.startsWith("NR-") ? id : id.replace("-", " "), tit];
  }
  const edicaoCurta = e => { const s = String(e || "").split(/\s\(|;/)[0].trim(); return s.length > 28 ? s.slice(0, 27) + "…" : s; };

  /** Fichas temáticas que citam cada norma: id -> [{f, reqs, tabs, figs}] (sem duplicar dados). */
  let _citam;
  function citacoes() {
    if (_citam) return _citam;
    _citam = {};
    for (const f of TEMATICAS) {
      const porN = {};
      const de = n => (porN[n] ||= { f, reqs: [], tabs: [], figs: [] });
      for (const r of f.requisitos || []) de(r.norma).reqs.push(r);
      for (const t of f.tabelas || []) de(t.norma).tabs.push(t);
      for (const g of f.figuras || []) de(g.norma).figs.push(g);
      for (const [n, c] of Object.entries(porN)) (_citam[n] ||= []).push(c);
    }
    return _citam;
  }

  let _entradas, _porId;
  function entradasNormas() {
    if (_entradas) return _entradas;
    const ids = new Set([...D.normas.map(n => n.id), ...Object.keys(FICHA_DA_NORMA)]);
    const cit = citacoes();
    _entradas = [...ids].map(id => {
      const n = NORMAS[id] || {}, f = FICHA_DA_NORMA[id];
      const [codigo, titulo] = codigoTitulo(id, f);
      const assunto = (f && f.assunto) || (cit[id] && cit[id][0].f.categoria) || "Sem assunto";
      const orgao = (f && f.categoria) || orgaoCurto({ id, orgao: n.orgao });
      return {
        id, f, codigo, titulo, orgao, assunto, edicao: (f && f.edicao) || n.edicao || "",
        chave: semAcento(codigo).replace(/^abnt\s+/, ""),
        t: semAcento([codigo, id, titulo, orgao, assunto, f?.resumo, (f?.palavras_chave || []).join(" "), n.escopo, RESUMOS[id]?.titulo].join(" | ")),
      };
    }).sort((a, b) => ordemNatural(a.chave, b.chave));
    _porId = new Map(_entradas.map(e => [e.id, e]));
    return _entradas;
  }
  const entradaDe = id => (entradasNormas(), _porId.get(id));

  /** Código citado em "referências normativas" -> id de norma do acervo (ou null). */
  let _codigos;
  const chaveCodigo = s => semAcento(s).replace(/\s*[:\-–(]\s*(19|20)\d\d\)?\s*$/, "").replace(/^(abnt|ansi\/?|bs en|bs|en|din en)\s+/, "").replace(/[^a-z0-9]/g, "");
  function normaPorCodigo(cod) {
    if (!_codigos) {
      _codigos = new Map();
      for (const e of entradasNormas()) for (const k of [e.id, e.codigo]) if (!_codigos.has(chaveCodigo(k))) _codigos.set(chaveCodigo(k), e.id);
    }
    return _codigos.get(chaveCodigo(cod)) || null;
  }

  // ---------- índice de títulos por página (dados/indice.js) ----------
  let IDX = null;
  const normCaminho = s => String(s || "").replace(/\\/g, "/").toLowerCase();
  /** Seções/tabelas/figuras do PDF da norma: {doc, ents: [[pagina, titulo], ...]} ou null. */
  function sumarioDe(arquivo) {
    const I = window.UVA_INDICE;
    if (!I || !arquivo) return null;
    if (!IDX) {
      IDX = { arq: new Map(), nome: new Map(), ents: null };
      I.docs.forEach((d, i) => { IDX.arq.set(normCaminho(d[0]), i); IDX.nome.set(normCaminho(d[0]).split("/").pop(), i); });
    }
    const a = normCaminho(arquivo), origem = D.ocr_origem || {};
    let i = IDX.arq.get(a);
    if (i == null) { // cópia OCR -> original, ou o índice tem a cópia OCR deste original
      for (const [ocr, orig] of Object.entries(origem)) {
        if (normCaminho(ocr) === a && IDX.arq.has(normCaminho(orig))) { i = IDX.arq.get(normCaminho(orig)); break; }
        if (normCaminho(orig) === a && IDX.arq.has(normCaminho(ocr))) { i = IDX.arq.get(normCaminho(ocr)); break; }
      }
    }
    if (i == null) i = IDX.nome.get(a.split("/").pop());
    if (i == null) return null;
    if (!IDX.ents) {
      IDX.ents = new Map();
      for (const [d, p, t] of I.e) { let l = IDX.ents.get(d); if (!l) IDX.ents.set(d, l = []); l.push([p, t]); }
    }
    return { doc: I.docs[i], ents: IDX.ents.get(i) || [] };
  }

  // ---------- busca ----------
  const GRUPOS = (D.sinonimos.grupos || []).map(g => g.map(semAcento));

  /** Cada termo da consulta vira uma lista de alternativas (o termo + sinônimos). */
  function termosDaConsulta(q) {
    const nq = semAcento(q).trim();
    if (!nq) return [];
    const usados = new Set();
    const termos = [];
    // primeiro, expressões de várias palavras que existam nos sinônimos
    let resto = " " + nq + " ";
    for (const g of GRUPOS) {
      for (const t of g) {
        if (t.includes(" ") && resto.includes(" " + t + " ")) {
          termos.push(g);
          resto = resto.replace(" " + t + " ", " ");
          usados.add(g);
        }
      }
    }
    for (const w of resto.split(/\s+/).filter(w => w.length >= 2)) {
      const g = GRUPOS.find(g => g.some(t => t === w || (w.length >= 4 && t.startsWith(w))));
      termos.push(g && !usados.has(g) ? Array.from(new Set([w, ...g])) : [w]);
    }
    return termos;
  }

  function contem(texto, alternativas) {
    return alternativas.some(a => texto.includes(a));
  }

  function textoReq(r) {
    return semAcento([r.grupo, r.parametro, r.valor, r.nota, r.norma, r.item].join(" "));
  }
  // textos normalizados guardados na 1ª busca (não recalcular a cada tecla)
  const TXT = new WeakMap();
  const txtReq = r => { let t = TXT.get(r); if (t == null) TXT.set(r, t = textoReq(r)); return t; };
  const txtLinha = l => { let t = TXT.get(l); if (t == null) TXT.set(l, t = l.filter(v => typeof v === "string").map(compacto).join(" ")); return t; };
  /** Linhas das tabelas de consulta cujo nome contém a consulta sem espaços ("W 100 x 19" → W100X19.3): [{f, t, l}], nome que começa com ela primeiro. */
  function buscarLinhas(q) {
    const qc = compacto(q);
    if (qc.length < 3 || !/\d/.test(qc)) return [];
    const out = [];
    for (const f of D.fichas) {
      if (f.calculadora !== "consulta-tabela") continue;
      for (const t of f.tabelas || []) if (t.consulta !== false) for (const l of t.linhas) if (txtLinha(l).includes(qc)) out.push({ f, t, l });
    }
    const inicio = x => x.l.some(v => typeof v === "string" && compacto(v).startsWith(qc)) ? 0 : 1;
    return out.sort((a, b) => inicio(a) - inicio(b));
  }
  function txtFicha(f) {
    let t = TXT.get(f);
    if (!t) TXT.set(f, t = {
      titulo: semAcento(f.titulo + (f.norma ? " " + f.norma : "")),
      chaves: semAcento((f.palavras_chave || []).concat((f.tabelas || []).map(x => x.titulo), (f.definicoes || []).map(d => d.termo),
        // consulta-tabela: nomes das linhas sem espaços (ex. "w100x19.3 w4x13", "heb100") para achar o perfil pela busca geral
        f.calculadora === "consulta-tabela" ? (f.tabelas || []).flatMap(t => t.linhas.map(txtLinha)) : []).join(" | ")),
      resumo: semAcento([f.resumo, f.categoria, f.assunto, f.escopo].join(" ")),
    });
    return t;
  }

  function buscar(q) {
    const termos = termosDaConsulta(q);
    if (!termos.length) return [];
    const res = [];
    for (const f of D.fichas) {
      const tf = txtFicha(f);
      const reqs = f.requisitos || [];
      let score = 0;
      let todos = true;
      for (const alt of termos) {
        let s = 0;
        if (contem(tf.titulo, alt)) s += 10;
        if (contem(tf.chaves, alt)) s += 6;
        if (contem(tf.resumo, alt)) s += 2;
        let nReq = 0;
        for (const r of reqs) if (contem(txtReq(r), alt) && ++nReq >= 8) break;
        s += nReq;
        if (!s) { todos = false; break; }
        score += s;
      }
      if (!todos) continue;
      // requisitos que casam com o maior número de termos
      const achados = reqs
        .map(r => ({ r, n: termos.filter(alt => contem(txtReq(r), alt)).length }))
        .filter(x => x.n > 0)
        .sort((a, b) => b.n - a.n);
      res.push({ f, score, achados: achados.map(x => x.r) });
    }
    return res.sort((a, b) => b.score - a.score);
  }

  /* Resumos próprios de norma (conteudo/resumos): valores viram "requisitos" (grupo = seção) para a busca e os achados. */
  const REQS_RES = new WeakMap();
  function reqsResumo(r) {
    let l = REQS_RES.get(r);
    if (!l) REQS_RES.set(r, l = (r.secoes || []).flatMap((s, i) => (s.valores || []).map(v => ({
      grupo: s.titulo, parametro: v.parametro, valor: String(v.valor), nota: v.nota || "", norma: r.id,
      item: v.item || s.item || "", cota: v.cota, secao: i,
    }))));
    return l;
  }
  const txtSecao = s => semAcento([s.item, s.titulo, s.texto, ...(s.valores || []).map(v => [v.parametro, v.valor, v.nota, v.item].join(" "))].join(" "));
  function txtResumo(r) {
    let t = TXT.get(r);
    if (!t) TXT.set(r, t = { titulo: semAcento(r.titulo || ""), secoes: semAcento((r.secoes || []).map(s => [s.titulo, s.texto].join(" ")).join(" | ")) });
    return t;
  }
  /** Resumos que casam com todos os termos: Map(id da norma -> {score, achados}). */
  function buscarResumos(termos) {
    const out = new Map();
    for (const r of D.resumos || []) {
      const t = txtResumo(r), reqs = reqsResumo(r);
      let score = 0, todos = true;
      for (const alt of termos) {
        let s = 0;
        if (contem(t.titulo, alt)) s += 8;
        if (contem(t.secoes, alt)) s += 3;
        let n = 0;
        for (const x of reqs) if (contem(txtReq(x), alt) && ++n >= 8) break;
        s += n;
        if (!s) { todos = false; break; }
        score += s;
      }
      if (!todos) continue;
      const achados = reqs.map(x => ({ x, n: termos.filter(alt => contem(txtReq(x), alt)).length }))
        .filter(y => y.n > 0).sort((a, b) => b.n - a.n).map(y => y.x);
      out.set(r.id, { score, achados });
    }
    return out;
  }

  /** Normas para a consulta: fichas de norma achadas por buscar() + resumos + normas sem ficha achadas pelo código/título. */
  function buscarNormas(q, resFichas) {
    const termos = termosDaConsulta(q);
    if (!termos.length) return [];
    const porId = new Map();
    for (const x of resFichas) if (x.f.tipo === "norma") porId.set(x.f.norma, x);
    for (const [id, x] of buscarResumos(termos)) {
      const y = porId.get(id);
      porId.set(id, y ? { f: y.f, score: y.score + x.score, achados: x.achados.concat(y.achados) } : { f: FICHA_DA_NORMA[id] || null, score: x.score, achados: x.achados });
    }
    for (const e of entradasNormas()) {
      if (porId.has(e.id) || e.f) continue;
      if (termos.every(alt => contem(e.t, alt))) porId.set(e.id, { f: null, score: termos.length * 8, achados: [] });
    }
    return [...porId.entries()].map(([id, x]) => {
      const e = entradaDe(id) || { id, codigo: id, titulo: "", orgao: "", edicao: "", chave: id };
      // código casando com todos os termos (ex. "B16.5", "NBR 5410") sobe para o topo
      const noCodigo = termos.every(alt => contem(semAcento(e.codigo + " " + e.id), alt));
      return { e, score: x.score + (noCodigo ? 1000 : 0), noCodigo, achados: x.achados };
    }).sort((a, b) => b.score - a.score || ordemNatural(a.e.chave, b.e.chave));
  }

  // documentos dos inventários (referências e acervo T:) — busca por código, título e assuntos
  const DOCS = (D.documentos || []).map(d => ({ d, t: semAcento([d.codigo, d.titulo, d.orgao, (d.assuntos || []).join(" ")].join(" ")) }));
  function buscarDocs(q) {
    const termos = termosDaConsulta(q);
    if (!termos.length) return [];
    return DOCS.filter(x => termos.every(alt => contem(x.t, alt)))
      .map(x => x.d)
      // vigentes primeiro; por código; edição mais recente primeiro
      .sort((a, b) => (a.situacao === "superada") - (b.situacao === "superada")
        || a.codigo.localeCompare(b.codigo, "pt", { numeric: true })
        || String(b.edicao || "").localeCompare(String(a.edicao || ""), "pt", { numeric: true }));
  }
  function listaDocs(docs, termos, limite) {
    const mostrar = docs.slice(0, limite);
    return `<div class="cartao resultado"><h3>Documentos no acervo (${docs.length})</h3>
      <ul class="achados">${mostrar.map(d => `<li>
        <span>${docLink(d, marcar(esc(d.codigo), termos))} — ${marcar(esc(d.titulo), termos)}</span>
        <span class="v">${esc(d.edicao || "")}</span>
        <span class="ref">${esc(d.orgao)} · ${esc(d.origem)}${d.paginas ? ` · ${d.paginas} págs.` : ""}${d.situacao === "superada" ? " · <b>superada</b>" : ""}${(d.assuntos || []).length ? ` · ${marcar(esc(d.assuntos.join(", ")), termos)}` : ""}</span></li>`).join("")}</ul>
      ${docs.length > limite ? `<p class="meta">Mostrando ${limite} de ${docs.length}. Refine a busca (ex.: código "B16.5" ou órgão "API").</p>` : ""}
      <p class="meta">Documentos sem valores extraídos. Os do acervo T: abrem o arquivo original.</p></div>`;
  }
  /** Documento do inventário: acervo T: abre o arquivo; os da pasta de originais (removida) vão para a página da norma, se houver. */
  function docLink(d, rotulo) {
    const deRef = d.origem === "referencias" || /^referencias[\\/]/i.test(d.arquivo || "");
    if (!deRef && d.arquivo) return `<a href="${urlArquivo(d.arquivo)}" target="_blank">${rotulo}</a>`;
    const nid = deRef && d.arquivo ? normaDoArquivo(d.arquivo) : null;
    return nid ? `<a href="${linkNorma(nid)}">${rotulo}</a>` : rotulo;
  }

  // índice de títulos por página dos PDFs originais (dados/indice.js, gerado por ferramentas/indexar_referencias.py)
  let INDICE = null;
  function buscarIndice(q) {
    const I = window.UVA_INDICE;
    const termos = termosDaConsulta(q);
    if (!I || !termos.length) return [];
    if (!INDICE) INDICE = {
      docs: I.docs.map(([arquivo, codigo, titulo, edicao]) => ({ arquivo, codigo, titulo, edicao, t: semAcento(codigo + " " + titulo) })),
      e: I.e.map(([d, p, txt]) => ({ d, p, txt, t: semAcento(txt) })),
    };
    const porDoc = new Map();
    for (const x of INDICE.e) {
      const doc = INDICE.docs[x.d];
      // todos os termos no título da seção ou no código/título do documento, e pelo menos um na própria seção
      if (!termos.some(alt => contem(x.t, alt))) continue;
      if (!termos.every(alt => contem(x.t, alt) || contem(doc.t, alt))) continue;
      if (!porDoc.has(x.d)) porDoc.set(x.d, []);
      porDoc.get(x.d).push(x);
    }
    return [...porDoc.entries()]
      .map(([d, ents]) => ({ doc: INDICE.docs[d], ents, n: ents.filter(x => termos.every(alt => contem(x.t, alt))).length }))
      .sort((a, b) => b.n - a.n || b.ents.length - a.ents.length);
  }
  function listaIndice(grupos, termos, limite) {
    if (!grupos.length) return "";
    const total = grupos.reduce((s, g) => s + g.ents.length, 0);
    return `<div class="cartao resultado"><h3>Nas normas do acervo — seções, tabelas e figuras (${total} em ${grupos.length} documentos)</h3>
      ${grupos.slice(0, limite).map(g => {
        const nid = normaDoArquivo(g.doc.arquivo);
        const cod = marcar(esc(g.doc.codigo), termos);
        const tit = x => marcar(esc(x.txt), termos);
        return `<p style="margin:10px 0 2px"><b>${nid ? `<a href="${linkNorma(nid)}">${cod}</a>` : cod}</b> — ${esc(g.doc.titulo)} <span class="meta">${esc(g.doc.edicao)}</span></p>
        <ul class="achados">${g.ents.slice(0, 6).map(x => `<li><span>${temTexto(nid) ? linkTexto(nid, x.p, x.txt, tit(x)) : tit(x)}</span></li>`).join("")}
        ${g.ents.length > 6 ? `<li class="meta">+ ${g.ents.length - 6} no mesmo documento</li>` : ""}</ul>`;
      }).join("")}
      ${grupos.length > limite ? `<p class="meta">Mostrando ${limite} de ${grupos.length} documentos. Refine a busca (ex.: acrescente o código "B31.3").</p>` : ""}
      <p class="meta">Índice automático de títulos — clique para ler o trecho no texto completo da norma.</p></div>`;
  }

  // ---------- busca no texto completo (índice invertido dados/busca/*.js, gerado por ferramentas/indexar_textos.py) ----------
  /* Regra dos termos = indexar_textos.py: sem acento, minúsculas; [a-z0-9] unidos por . - / ; com letra E dígito é código
     sem separadores ("B31.3" → b313); senão quebra nos separadores; palavra ≥ 3 letras fora das stopwords; número puro fora.
     Postagens "D:C:P.P;…" (D = norma, C = ocorrências, P = páginas 0-based em diferenças; "*N" = todas as N páginas). */
  const BT = { stop: null, chaves: null, carregando: {}, post: new Map(), ordem: {} };
  const temBuscaTexto = () => !!(window.UVA_BUSCA_MAPA && window.UVA_BUSCA_MAPA.arquivos);
  /** Texto -> tokens do índice [{t, cod}]. */
  function tokensTexto(s) {
    if (!BT.stop) BT.stop = new Set(window.UVA_BUSCA_MAPA.stop || []);
    const out = [];
    for (const t of semAcento(s).match(/[a-z0-9]+(?:[./-][a-z0-9]+)*/g) || []) {
      if (/\d/.test(t)) {
        if (/[a-z]/.test(t)) { const c = t.replace(/[./-]/g, ""); if (c.length <= 24) out.push({ t: c, cod: true }); }
        continue;
      }
      for (const w of t.split(/[./-]/)) if (w.length >= 3 && w.length <= 40 && !BT.stop.has(w)) out.push({ t: w, cod: false });
    }
    return out;
  }
  /** Sigla + espaço + número vira um código só ("sa 516" → sa516, "nbr 5410" → nbr5410), como no índice. */
  const juntarSiglas = q => String(q).replace(/(^|[^A-Za-z0-9])([A-Za-z]{1,4}) (\d[0-9A-Za-z]*(?:[./-][0-9A-Za-z]+)*)/g,
    (m, a, b, c) => a + b + c.replace(/[./-]/g, ""));
  /** Arquivo de prefixo de um termo: a chave mais longa que é prefixo dele. */
  function chaveDe(t) {
    const A = window.UVA_BUSCA_MAPA.arquivos;
    for (let n = Math.min(t.length, 8); n >= 1; n--) if (A[t.slice(0, n)]) return t.slice(0, n);
    return null;
  }
  /** Chaves a carregar para um token (palavra ≥ 4 letras: também as chaves mais longas que começam com ela). */
  function chavesDe(tok) {
    const k = chaveDe(tok.t), ks = k ? [k] : [];
    if (!tok.cod && tok.t.length >= 4) {
      if (!BT.chaves) BT.chaves = Object.keys(window.UVA_BUSCA_MAPA.arquivos);
      for (const c of BT.chaves) if (c.length > tok.t.length && c.startsWith(tok.t) && ks.length < 8) ks.push(c);
    }
    return ks;
  }
  /** Carrega dados/busca/<prefixo>.js por <script> (funciona em file://). */
  function carregarChaves(ks, cb) {
    const falta = ks.filter(k => !(window.UVA_BUSCA_TXT || {})[k]);
    if (!falta.length) { cb(); return; }
    let n = falta.length;
    const um = () => { if (--n === 0) cb(); };
    for (const k of falta) {
      let c = BT.carregando[k];
      if (c) { c.push(um); continue; }
      c = BT.carregando[k] = [um];
      const s = document.createElement("script");
      s.src = "dados/busca/" + encodeURIComponent(window.UVA_BUSCA_MAPA.arquivos[k]);
      const fim = () => { delete BT.carregando[k]; s.remove(); c.forEach(f => f()); };
      s.onload = fim; s.onerror = fim;
      document.head.appendChild(s);
    }
  }
  /** Postagens dos termos do índice que casam com o token: ele mesmo e, se palavra ≥ 4 letras, os que começam com ele (até 60). */
  function expandir(tok) {
    const B = window.UVA_BUSCA_TXT || {};
    const out = [];
    for (const k of chavesDe(tok)) {
      const obj = B[k];
      if (!obj) continue;
      if (tok.cod || tok.t.length < 4) { if (obj[tok.t] != null) out.push(obj[tok.t]); continue; }
      let ks = BT.ordem[k];
      if (!ks) ks = BT.ordem[k] = Object.keys(obj).sort();
      let lo = 0, hi = ks.length; // 1º termo >= token (busca binária)
      while (lo < hi) { const m = (lo + hi) >> 1; if (ks[m] < tok.t) lo = m + 1; else hi = m; }
      for (let i = lo; i < ks.length && ks[i].startsWith(tok.t) && out.length < 60; i++) out.push(obj[ks[i]]);
    }
    return out;
  }
  /** Postagens -> Map(doc -> {c, n, ps: Set de páginas 0-based | null = todas}). */
  function lerPostagens(s) {
    let m = BT.post.get(s);
    if (m) return m;
    m = new Map();
    for (const parte of s.split(";")) {
      const [d, c, ps] = parte.split(":");
      if (ps[0] === "*") { m.set(parseInt(d, 36), { c: parseInt(c, 36), n: parseInt(ps.slice(1), 36), ps: null }); continue; }
      const set = new Set();
      let p = 0;
      ps.split(".").forEach((x, i) => { p = i ? p + parseInt(x, 36) : parseInt(x, 36); set.add(p); });
      m.set(parseInt(d, 36), { c: parseInt(c, 36), n: set.size, ps: set });
    }
    if (s.length > 3000) BT.post.set(s, m); // só guarda as grandes (termos comuns, digitados de novo a cada tecla)
    return m;
  }
  const unirPags = (a, b) => (a === null || b === null) ? null : new Set([...a, ...b]);
  const cruzarPags = (a, b) => a === null ? b : b === null ? a : new Set([...a].filter(x => b.has(x)));
  /** União (OU) de mapas doc -> {c, n, ps}. */
  function unir(ms) {
    if (ms.length === 1) return ms[0];
    const r = new Map();
    for (const m of ms) for (const [d, x] of m) {
      const y = r.get(d);
      if (!y) { r.set(d, x); continue; }
      const ps = unirPags(y.ps, x.ps);
      r.set(d, { c: y.c + x.c, ps, n: ps ? ps.size : Math.max(y.n, x.n) });
    }
    return r;
  }
  /** Interseção (E) na mesma página: doc -> {ps, n, cs: [ocorrências na norma, por termo]}. */
  function cruzar(ms) {
    if (!ms.length) return new Map();
    const base = [...ms].sort((a, b) => a.size - b.size);
    const r = new Map();
    for (const [d, x] of base[0]) {
      let ps = x.ps, n = x.n, ok = true;
      for (const m of base.slice(1)) {
        const y = m.get(d);
        if (!y) { ok = false; break; }
        ps = cruzarPags(ps, y.ps); n = Math.min(n, y.n);
        if (ps && !ps.size) { ok = false; break; }
      }
      if (ok) r.set(d, { ps, n: ps ? ps.size : n, cs: ms.map(m => m.get(d).c) });
    }
    return r;
  }
  /** Consulta -> grupos [{rot, alts: [[token]]}]: grupos em E; sinônimos = alternativas em OU; tokens da alternativa em E. */
  function planoTexto(q) {
    if (!temBuscaTexto()) return null;
    const grupos = [];
    for (const g of termosDaConsulta(juntarSiglas(q))) {
      const alts = [];
      // palavra com hífen também vale escrita junta ("pré-aquecimento" ≡ "preaquecimento")
      const formas = g.slice(0, 8).flatMap(a => /[a-z]-[a-z]/.test(a) ? [a, a.replace(/([a-z])-(?=[a-z])/g, "$1")] : [a]);
      for (const a of formas) {
        const ts = tokensTexto(a), k = ts.map(t => t.t).join(" ");
        if (ts.length && !alts.some(x => x.map(t => t.t).join(" ") === k)) alts.push(ts);
      }
      if (alts.length) grupos.push({ rot: g[0], alts, formas });
    }
    return grupos.length ? grupos : null;
  }
  /** Busca no índice (assíncrona: carrega os prefixos). cb(null | {res: [{nid, ps, n, cs}], grupos, ms}). */
  function buscarTexto(q, cb) {
    const grupos = planoTexto(q);
    if (!grupos) { cb(null); return; }
    const t0 = performance.now();
    const ks = new Set();
    for (const g of grupos) for (const a of g.alts) for (const t of a) chavesDe(t).forEach(k => ks.add(k));
    carregarChaves([...ks], () => {
      const t1 = performance.now();
      const porGrupo = grupos.map(g => unir(g.alts.map(a => {
        const mt = a.map(t => unir(expandir(t).map(lerPostagens).concat([new Map()])));
        if (mt.length === 1) return mt[0];
        const r = new Map();
        for (const [d, y] of cruzar(mt)) r.set(d, { c: Math.min(...y.cs), ps: y.ps, n: y.n }); // ~ ocorrências da expressão
        return r;
      })));
      const docs = window.UVA_BUSCA_MAPA.docs;
      const soma = x => x.cs.reduce((s, v) => s + v, 0);
      const res = [...cruzar(porGrupo)].map(([d, x]) => ({ nid: docs[d], ps: x.ps, n: x.n, cs: x.cs }))
        .sort((a, b) => b.n - a.n || soma(b) - soma(a));
      cb({ res, grupos, ms: performance.now() - t0, msCarga: t1 - t0 });
    });
  }
  /** Trecho em volta do 1º achado da página (só se o texto da norma já estiver carregado). */
  function trechoTexto(nid, p, palavras, termos) {
    const pags = (window.UVA_TEXTOS || {})[nid];
    if (!pags || !pags[p]) return "";
    const t = pags[p], norm = textosNorm(nid, pags)[p];
    let i = -1;
    for (const w of palavras) {
      const re = regexBusca(w, 8);
      const m = re && re.exec(norm);
      if (m) { i = m.index; break; }
    }
    const a = Math.max(0, i - 90), b = Math.min(t.length, Math.max(i, 0) + 170);
    return `<span class="trecho-txt">${a > 0 ? "…" : ""}${marcar(esc(t.slice(a, b).replace(/\s+/g, " ")), termos)}${b < t.length ? "…" : ""}</span>`;
  }
  /** Seção "No texto completo das normas" da busca global (preenchida depois de carregar os prefixos). */
  function blocoTextoCompleto(q, termos, alvo, limite = 30) {
    buscarTexto(q, r => {
      if (!document.body.contains(alvo) || estadoBusca.q !== q) return; // a busca mudou
      if (!r) { alvo.remove(); return; }
      const { res, grupos } = r;
      window.UVA_BUSCA_TEMPO = { ms: r.ms, msCarga: r.msCarga }; // diagnóstico (tempo de carga + busca)
      if (!res.length) {
        alvo.innerHTML = `<h3>No texto completo das normas</h3><p class="meta">Nenhuma norma com ${grupos.length > 1 ? "todos os termos na mesma página" : "o termo"}.</p>`;
        return;
      }
      // palavras digitadas (para achar/realçar o trecho no texto), das mais raras na norma às mais comuns
      const palavras = q.trim().split(/\s+/).flatMap(w => /\p{L}-\p{L}/u.test(w) ? [w, w.replace(/(\p{L})-(?=\p{L})/gu, "$1")] : [w])
        .filter(w => tokensTexto(w).length);
      const grupoDe = w => { const t = tokensTexto(w)[0].t; return grupos.findIndex(g => g.alts.some(a => a.some(x => x.t === t))); };
      const gw = palavras.map(grupoDe);
      // sinônimos (a norma pode ter só "guardrail" para "guarda-corpo"): tentados depois das palavras digitadas
      const sinon = [...new Set(grupos.flatMap(g => g.formas))].filter(w => !palavras.some(p => semAcento(p) === w)).slice(0, 12);
      const marcas = termos.concat(palavras.map(w => [semAcento(w)])); // realce no trecho (inclui a forma sem hífen)
      const mostrar = res.slice(0, limite);
      alvo.innerHTML = `<h3>No texto completo das normas (${res.length} norma${res.length > 1 ? "s" : ""})</h3>
        <ul class="achados">${mostrar.map(x => {
          const e = entradaDe(x.nid) || { codigo: x.nid, titulo: "" };
          const p = x.ps ? Math.min(...x.ps) : 0;
          const tot = x.cs.reduce((s, v) => s + v, 0);
          const ordem = palavras.map((w, i) => [w, x.cs[gw[i]] ?? 1e9]).sort((a, b) => a[1] - b[1]).map(a => a[0]).concat(sinon);
          const cont = grupos.length > 1
            ? `${fmt(x.n)} página${x.n > 1 ? "s" : ""} com todos os termos · ${grupos.map((g, i) => `${esc(g.rot)} ×${fmt(x.cs[i])}`).join(" · ")}`
            : `${fmt(tot)} ocorrência${tot > 1 ? "s" : ""} em ${fmt(x.n)} página${x.n > 1 ? "s" : ""}`;
          const tr = trechoTexto(x.nid, p, [q, ...ordem], marcas);
          return `<li><span><a href="#" class="ir-texto" data-norma="${esc(x.nid)}" data-tp="${p + 1}" data-tr="${esc(q.slice(0, 120))}" data-q="${esc(q.slice(0, 120))}" data-alt="${esc(ordem.join("|"))}" title="Abrir o texto completo da norma neste trecho"><b>${esc(e.codigo)}</b></a> — ${esc(e.titulo)}${tr ? "<br>" + tr : ""}</span>
            <span class="ref">${cont}</span></li>`;
        }).join("")}</ul>
        ${res.length > limite ? `<p class="meta">Mostrando ${limite} de ${res.length} normas (primeiro as com mais páginas contendo todos os termos). Refine a busca.</p>` : ""}
        <p class="meta">Clique para ler o trecho no texto completo da norma, com o termo realçado.${grupos.length > 1 ? " Termos na mesma página, em qualquer ordem." : ""}</p>`;
    });
  }

  function marcar(html, termos) {
    // marca termos no texto já escapado (fora de tags)
    const alts = termos.flat().filter(t => t.length >= 2).sort((a, b) => b.length - a.length);
    if (!alts.length) return html;
    return html.replace(/(^|>)([^<]+)/g, (m, a, txt) => {
      const base = semAcento(txt);
      const marcas = [];
      for (const t of alts) {
        let i = base.indexOf(t);
        while (i !== -1) {
          if (!marcas.some(([s, e]) => i < e && i + t.length > s)) marcas.push([i, i + t.length]);
          i = base.indexOf(t, i + t.length);
        }
      }
      if (!marcas.length) return m;
      marcas.sort((x, y) => x[0] - y[0]);
      let out = "", pos = 0;
      for (const [s, e] of marcas) { out += txt.slice(pos, s) + "<mark>" + txt.slice(s, e) + "</mark>"; pos = e; }
      return a + out + txt.slice(pos);
    });
  }

  /** <details data-lazy> cujo corpo (.corpo) só é montado quando abre (listas grandes não pesam). */
  function preguicoso(raiz, fabricas) {
    raiz.querySelectorAll("details[data-lazy]").forEach(d => {
      const montar = () => {
        if (d.dataset.montado) return;
        d.dataset.montado = "1";
        d.querySelector(".corpo").innerHTML = fabricas[d.dataset.lazy]();
      };
      if (d.open) montar();
      d.addEventListener("toggle", () => { if (d.open) montar(); });
      d.montar = montar;
    });
  }

  // ---------- telas ----------
  const estadoInicio = { agrupar: "orgao", filtro: "", abertos: new Set() };

  function telaInicio() {
    const porCategoria = {};
    for (const f of TEMATICAS) (porCategoria[f.categoria] ||= []).push(f);
    const nNormas = new Set([...D.normas.map(n => n.id), ...Object.keys(FICHA_DA_NORMA)]).size;
    let h = `<h1>Consulta de normas</h1>
      <p class="meta">${TEMATICAS.length} fichas temáticas · ${nNormas} normas · ${fmt(D.fichas.reduce((s, f) => s + (f.requisitos || []).length, 0))} valores e itens normativos.
      Digite um assunto ou código acima — a busca entende português e inglês, sem acento.</p>
      ${PUBLICO ? `<p class="meta aviso-publico">Versão pública: fichas temáticas, resumos próprios das normas (${(D.resumos || []).length}) e esquemas ilustrativos.
        Texto integral e figuras das normas ficam só na versão local (não distribuída).</p>` : ""}`;
    for (const [cat, fichas] of Object.entries(porCategoria).sort()) {
      h += `<h2>${esc(cat)}</h2><div class="grade">${fichas.map(cartaoFicha).join("")}</div>`;
    }
    h += `<section class="sec-normas" id="sec-normas">
      <h2>Normas <span class="meta" id="normas-conta">(${nNormas})</span></h2>
      <div class="barra-ficha barra-normas">
        <input type="search" id="filtro-normas" placeholder="Filtrar normas — código, título ou assunto (ex.: B16.5, NBR 5410, flange)" aria-label="Filtrar normas" value="${esc(estadoInicio.filtro)}">
        <span class="alternar" role="group" aria-label="Agrupar por">
          <button type="button" class="botao" data-agrupar="orgao" aria-pressed="${estadoInicio.agrupar === "orgao"}">Órgão</button><button type="button" class="botao" data-agrupar="assunto" aria-pressed="${estadoInicio.agrupar === "assunto"}">Assunto</button>
        </span>
      </div>
      <div id="lista-normas"></div></section>`;
    app.innerHTML = h;
    const filtro = document.getElementById("filtro-normas");
    let espera;
    filtro.addEventListener("input", () => {
      clearTimeout(espera);
      espera = setTimeout(() => { estadoInicio.filtro = filtro.value; montarNormas(); }, 150);
    });
    app.querySelectorAll("button[data-agrupar]").forEach(b => b.addEventListener("click", () => {
      estadoInicio.agrupar = b.dataset.agrupar;
      estadoInicio.abertos.clear();
      app.querySelectorAll("button[data-agrupar]").forEach(x => x.setAttribute("aria-pressed", x === b));
      montarNormas();
    }));
    montarNormas();
  }

  function itemListaNorma(e, termos) {
    const n = e.f ? (e.f.requisitos || []).length + (e.f.tabelas || []).length : 0;
    return `<li><a href="${linkNorma(e.id)}"><b>${marcar(esc(e.codigo), termos)}</b> — <span class="tit">${marcar(esc(e.titulo), termos)}</span></a>
      <span class="meta">${esc(edicaoCurta(e.edicao))}${n ? ` · ${n} ite${n > 1 ? "ns" : "m"}` : ""}${RESUMOS[e.id] ? ' · <span class="chip chip-resumo">resumo</span>' : ""}</span></li>`;
  }

  /** Seção "Normas" da página inicial: um <details> por órgão (ou assunto); listas montadas ao abrir. */
  function montarNormas() {
    const alvo = document.getElementById("lista-normas");
    if (!alvo) return;
    const termos = termosDaConsulta(estadoInicio.filtro);
    const todas = entradasNormas();
    const lista = termos.length ? todas.filter(e => termos.every(alt => contem(e.t, alt))) : todas;
    const grupos = {};
    for (const e of lista) (grupos[estadoInicio.agrupar === "orgao" ? e.orgao : e.assunto] ||= []).push(e);
    const chaves = Object.keys(grupos).sort(ordemNatural);
    const abrirTodos = termos.length && lista.length <= 150;
    document.getElementById("normas-conta").textContent = termos.length ? `(${lista.length} de ${todas.length})` : `(${todas.length})`;
    const fab = {};
    alvo.innerHTML = chaves.length ? chaves.map((k, i) => {
      fab[i] = () => `<ul class="lista-normas">${grupos[k].map(e => itemListaNorma(e, termos)).join("")}</ul>`;
      return `<details class="cartao grupo grupo-normas" data-lazy="${i}" data-k="${esc(k)}"${abrirTodos || estadoInicio.abertos.has(k) ? " open" : ""}>
        <summary><span class="g-nome">${esc(k)}</span><span class="g-meta">${grupos[k].length} norma${grupos[k].length > 1 ? "s" : ""}</span></summary>
        <div class="corpo"></div></details>`;
    }).join("") : `<p class="meta">Nenhuma norma com "${esc(estadoInicio.filtro)}".</p>`;
    preguicoso(alvo, fab);
    alvo.querySelectorAll("details.grupo-normas").forEach(d => d.addEventListener("toggle", () => {
      if (termos.length) return;
      d.open ? estadoInicio.abertos.add(d.dataset.k) : estadoInicio.abertos.delete(d.dataset.k);
    }));
  }

  function cartaoFicha(f) {
    const normas = [...new Set((f.requisitos || []).map(r => r.norma))];
    const max = 8;
    return `<a class="cartao ficha-card" href="#/ficha/${f.id}">
      <h3>${esc(f.titulo)}</h3><p>${esc(f.resumo)}</p>
      <div class="chips">${normas.slice(0, max).map(n => `<span class="chip">${esc(n)}</span>`).join("")}${normas.length > max ? `<span class="chip mais">+${normas.length - max}</span>` : ""}</div></a>`;
  }

  const estadoBusca = { q: "", limiteNormas: 12 };
  function telaBusca(q) {
    if (estadoBusca.q !== q) { estadoBusca.q = q; estadoBusca.limiteNormas = 12; }
    const termos = termosDaConsulta(q);
    const todos = buscar(q);
    const res = todos.filter(x => x.f.tipo !== "norma");
    const normas = buscarNormas(q, todos);
    const docs = buscarDocs(q);
    const indice = buscarIndice(q);
    const qs = encodeURIComponent(q);
    const blocoNormas = normas.length ? `<div class="cartao resultado bloco-normas-busca"><h3>Normas (${normas.length})</h3>
      <ul class="achados">${normas.slice(0, estadoBusca.limiteNormas).map(({ e, achados }) => `<li>
        <span><a href="${linkNorma(e.id)}${e.f || RESUMOS[e.id] ? `?q=${qs}` : ""}"><b>${marcar(esc(e.codigo), termos)}</b></a> — ${marcar(esc(e.titulo), termos)}</span>
        <span class="v meta">${esc(edicaoCurta(e.edicao))}</span>
        <span class="ref">${esc(e.orgao)}${e.assunto && e.assunto !== "Sem assunto" ? ` · ${esc(e.assunto)}` : ""}${achados.length ? ` · ${achados.length} achado${achados.length > 1 ? "s" : ""}: ` + achados.slice(0, 3).map(r =>
          marcar(esc(r.parametro.length > 90 ? r.parametro.slice(0, 89) + "…" : r.parametro), termos)).join(" · ") : ""}</span></li>`).join("")}</ul>
      ${normas.length > estadoBusca.limiteNormas ? `<p><button type="button" class="botao" id="mais-normas">Mostrar mais ${Math.min(30, normas.length - estadoBusca.limiteNormas)} de ${normas.length - estadoBusca.limiteNormas}</button></p>` : ""}</div>` : "";
    const linhas = buscarLinhas(q);
    const LIM_LINHAS = 15;
    const blocoLinhas = linhas.length ? `<div class="cartao resultado"><h3>Perfis e linhas de tabela (${linhas.length})</h3>
      <ul class="achados">${linhas.slice(0, LIM_LINHAS).map(({ f, t, l }) => {
        const nums = t.colunas.map((c, k) => [c, l[k]]).filter(([, v], k) => k && typeof v === "number").slice(0, 4);
        return `<li><span><a href="#/ficha/${f.id}?q=${encodeURIComponent(l[0])}"><b>${esc(l[0])}</b></a>${typeof l[1] === "string" ? ` <span class="meta">(${esc(l[1])})</span>` : ""}</span>
          <span class="v">${nums.map(([c, v]) => `${esc(c)}: ${esc(v)}`).join(" · ")}</span>
          <span class="ref">${esc(Object.values(t.chave || {}).join(" · ") || t.titulo)} · ${esc(f.titulo)}</span></li>`;
      }).join("")}</ul>
      ${linhas.length > LIM_LINHAS ? `<p class="meta"><a href="#/ficha/${linhas[0].f.id}?q=${qs}">+ ${linhas.length - LIM_LINHAS} na Consulta rápida da ficha →</a></p>` : ""}</div>` : "";
    const blocoFichas = res.map(({ f, achados }) => {
      const mostrar = achados.slice(0, 6);
      return `<div class="cartao resultado">
        <h3><a href="#/ficha/${f.id}?q=${qs}">${marcar(esc(f.titulo), termos)}</a></h3>
        <div class="meta">${esc(f.categoria)} · ${marcar(esc(f.resumo), termos)}</div>
        ${mostrar.length ? `<ul class="achados">${mostrar.map(r => `<li>
          <span>${marcar(esc(r.parametro), termos)}</span><span class="v">${marcar(esc(r.valor), termos)}</span>
          <span class="ref">${chipNorma(r.norma)}${temTexto(r.norma) ? " · " + linkTexto(r.norma, r.pagina, r.parametro) : ""}</span></li>`).join("")}</ul>` : ""}
        ${achados.length > mostrar.length ? `<p class="meta"><a href="#/ficha/${f.id}?q=${qs}">+ ${achados.length - mostrar.length} valores na ficha →</a></p>` : ""}
      </div>`;
    }).join("");
    const cab = res.length
      ? `<p class="meta">${res.length} ficha(s) temática(s) e ${normas.length} norma(s) para <b>${esc(q)}</b></p>`
      : `<div class="cartao vazio">Nenhuma ficha temática para <b>${esc(q)}</b>${normas.length ? ` — veja as ${normas.length} norma(s) abaixo` : ""}.</div>`;
    // consulta que é um código de norma (ex. "B16.5", "NBR 5410"): normas antes das fichas temáticas
    const codigoPrimeiro = normas.length && normas[0].noCodigo && /\d/.test(q);
    app.innerHTML = cab + blocoLinhas + (codigoPrimeiro ? blocoNormas + blocoFichas : blocoFichas + blocoNormas)
      + listaIndice(indice, termos, res.length ? 10 : 25) + (docs.length ? listaDocs(docs, termos, res.length ? 15 : 40) : "")
      + (temBuscaTexto() ? `<div class="cartao resultado bloco-texto-busca" id="busca-txt"><h3>No texto completo das normas</h3><p class="meta">Procurando no texto das normas…</p></div>` : "");
    const bt = document.getElementById("busca-txt");
    if (bt) blocoTextoCompleto(q, termos, bt);
    document.getElementById("mais-normas")?.addEventListener("click", () => {
      estadoBusca.limiteNormas += 30;
      const y = window.scrollY;
      telaBusca(q);
      window.scrollTo(0, y);
    });
  }

  // estado de cada ficha durante a sessão: normas ocultas, aba ativa, grupos abertos
  const estadoFicha = {};
  const estadoDe = (f) => (estadoFicha[f.id] ||= {
    ocultas: new Set(),
    aba: f.tipo === "norma" && RESUMOS[f.norma] ? "res" : f.tipo === "norma" && temTexto(f.norma) ? "txt"
      : f.calculadora === "consulta-tabela" ? "calc" : (f.requisitos || []).length ? "req" : null, // null = 1ª aba disponível
    abertos: null, // null = padrão (1º grupo aberto)
    resAbertos: null, // seções do Resumo abertas (null = a 1ª)
    txt: { q: "", k: -1 }, // busca no texto completo
    ir: null,              // {p, tr}: trecho do texto completo a mostrar ao abrir a aba
  });
  const FIG_LINHA = new WeakMap(); // ficha -> figurasEmLinha(f)
  let textoPendente = null; // {norma, p, tr}: pedido de outra tela para abrir o texto da norma num trecho

  /** Figuras de recorte que correspondem a requisitos "ver imagem…" (mesma norma, item e página): Map req -> [figuras]. */
  const chaveFig = (n, item, p) => `${n}|${semAcento(item).replace(/\s+/g, " ").trim()}|${p}`;
  function figurasEmLinha(f) {
    const m = new Map();
    const reqs = (f.requisitos || []).filter(r => /^ver imagem/i.test(r.valor || ""));
    if (!reqs.length) return m;
    const porChave = new Map();
    for (const fig of f.figuras || []) {
      const k = chaveFig(fig.norma, fig.item, fig.pagina);
      if (!porChave.has(k)) porChave.set(k, []);
      porChave.get(k).push(fig);
    }
    const reqsChave = new Map();
    for (const r of reqs) {
      const k = chaveFig(r.norma, r.item, r.pagina);
      if (!reqsChave.has(k)) reqsChave.set(k, []);
      reqsChave.get(k).push(r);
    }
    // na mesma chave, pares pela ordem; figuras que sobram vão para o último requisito
    for (const [k, rs] of reqsChave) {
      const figs = porChave.get(k) || [];
      rs.forEach((r, i) => {
        const fs = i < rs.length - 1 ? figs.slice(i, i + 1) : figs.slice(i);
        if (fs.length) m.set(r, fs);
      });
    }
    return m;
  }

  /** Número da figura no texto do item (ex. "Figura 3.1-1" → "3.1-1"). */
  const numFigura = s => {
    const m = semAcento(s).match(/fig(?:ura|ure|\.)?\s*([a-z]?\d+(?:[.\-]\d+)*[a-z]?)/);
    return m ? m[1] : null;
  };
  /** Figuras citadas pelos requisitos do grupo (mesma norma e mesmo nº de figura no item ou na nota). */
  function figurasDoGrupo(f, g) {
    return (f.figuras || []).filter(fig => {
      if (fig.grupo) return [].concat(fig.grupo).includes(g.nome); // grupo indicado na ficha
      const n = numFigura(fig.item);
      if (!n) return false;
      const re = new RegExp("fig(?:ura|ure|\\.|s\\.)?\\s*(?:[\\w.\\-]+\\s*(?:,|e|and)\\s*)*" + n.replace(/[.\-]/g, "\\$&") + "(?![\\d.\\-]*\\d)");
      return g.reqs.some(r => r.norma === fig.norma && re.test(semAcento(r.item + " " + (r.nota || ""))));
    });
  }

  /* Legenda de imagem de página inteira ("Página 12 — Table 4 …", "Página 30 (tabela/desenho em página escaneada)"):
     inteira = é página inteira; titulo = legenda sem o "Página N"; trecho = título procurável no texto completo ("" se não há). */
  const RE_LEG_PAG = /^\s*P[aá]gina\s+\d+\s*(?:[—–-]\s*)?/i;
  function partesLegenda(fig) {
    const leg = fig.legenda || "";
    const m = leg.match(RE_LEG_PAG);
    if (!m) return { inteira: false, titulo: leg, trecho: leg };
    const resto = leg.slice(m[0].length).trim();
    const entre = resto.match(/^\((.*)\)$/);
    return { inteira: true, titulo: entre ? entre[1] : resto || "página inteira", trecho: entre || /sem t[ií]tulo/i.test(resto) ? "" : resto };
  }
  /** Tipo da imagem na ficha de norma (aba Figuras): tab | fig | form | pag. */
  function tipoFig(fig) {
    const { inteira, titulo } = partesLegenda(fig);
    const t = semAcento(titulo), it = semAcento(fig.item || ""), g = [].concat(fig.grupo || []).join(" ");
    if (/^(formula|equa[cç]|eq\.)/.test(t) || /^(formula|equa|eq\.)/.test(it)) return "form";
    if (/^(tabela|table|quadro|tab\.)/.test(t) || /^(tabela|table|quadro)/.test(it)) return "tab";
    if (/^(fig|figura|figure|desenho)\b/.test(t) && !/sem titulo/.test(t) || /^(fig|figura|figure)/.test(it)) return "fig";
    if (inteira) return "pag";
    if (/^Tabelas$/.test(g) || /\btable\b|\btabela\b/.test(t)) return "tab";
    return "fig";
  }
  const TIPOS_FIG = [["tab", "Tabelas"], ["fig", "Figuras"], ["form", "Fórmulas"], ["pag", "Páginas inteiras (escaneadas ou sem título)"]];

  /** rotPag: ficha de norma — legenda sem "Página N" e o nº da página como rótulo discreto (só navegação). */
  function figuraHtml(fig, mini, semNorma, rotPag) {
    const pl = partesLegenda(fig);
    const lk = linkTexto(fig.norma, fig.pagina, pl.trecho);
    const leg = rotPag ? `${fig.pagina ? `<span class="rot-pag">Página ${+fig.pagina}</span> ` : ""}${esc(pl.titulo)}`
      : `${esc(fig.legenda)}<br><b><a href="${linkNorma(fig.norma)}">${esc(fig.norma)}</a></b>`;
    return `<figure class="cartao figura${mini ? " mini" : ""}${semNorma ? " em-linha" : ""}${pl.inteira ? " pag-inteira" : ""}"><img src="assets/figuras/${esc(fig.arquivo)}" alt="${esc(fig.legenda)}" loading="lazy" decoding="async" title="Clique para ampliar">
      <figcaption>${semNorma ? "" : leg}${lk ? `${semNorma ? "" : rotPag ? "<br>" : " · "}${lk}` : ""}</figcaption></figure>`;
  }

  /** Desenhos com as cotas de uma tabela (campo "figuras" da tabela: caminhos relativos a assets/figuras/, ou objetos
      {arquivo, legenda}). Legenda/norma/página vêm da figura de mesmo arquivo em f.figuras; senão, da própria tabela. */
  function figurasDaTabela(f, t) {
    return (t.figuras || []).map(x => {
      const arq = typeof x === "string" ? x : x.arquivo;
      const daFicha = (f.figuras || []).find(g => g.arquivo === arq);
      return { norma: t.norma, pagina: t.pagina, item: t.item, ...(daFicha || {}),
        arquivo: arq, legenda: (typeof x === "object" && x.legenda) || daFicha?.legenda || `Desenho com as cotas — ${t.titulo}` };
    });
  }
  /** Bloco de miniaturas (clique amplia) com os desenhos de cotas da tabela; "" se não houver. */
  function figurasTabelaHtml(f, t) {
    const figs = figurasDaTabela(f, t);
    return figs.length ? `<div class="figuras-grupo figuras-tabela">${figs.map(fig => figuraHtml(fig, true)).join("")}</div>` : "";
  }

  /** Página de norma sem ficha (só normas.json): cabeçalho, escopo, sumário e citações nas fichas temáticas. */
  function fichaSintetica(normaId) {
    const n = NORMAS[normaId];
    if (!n) return null;
    const [cod, tit] = codigoTitulo(normaId, null);
    return {
      id: "norma:" + normaId, tipo: "norma", norma: normaId, titulo: `${cod} — ${tit}`, categoria: orgaoCurto(n),
      resumo: "", edicao: n.edicao, arquivo: n.arquivo, escopo: n.escopo && n.escopo !== n.titulo ? n.escopo : "", requisitos: [],
    };
  }

  /** Nível de um título do sumário pela numeração ("4.2.1 …" → 3). */
  const nivelTitulo = t => { const m = t.match(/^\s*(?:[A-Z]\.)?(\d+(?:\.\d+)*)\s/); return m ? Math.min(m[1].split(".").length, 4) : 1; };

  function telaFicha(f, q) {
    if (!f) { app.innerHTML = `<div class="cartao vazio">Ficha não encontrada. <a href="#/">Voltar ao início</a></div>`; return; }
    const ehNorma = f.tipo === "norma";
    const id = f.id;
    const termos = termosDaConsulta(q || "");
    const est = estadoDe(f);
    const ocultas = est.ocultas;
    const reqsF = f.requisitos || [];
    const normas = [...new Set(reqsF.map(r => r.norma))];
    const grupos = [];
    const porNome = new Map();
    for (const r of reqsF) {
      let g = porNome.get(r.grupo);
      if (!g) { grupos.push(g = { nome: r.grupo, reqs: [] }); porNome.set(r.grupo, g); }
      g.reqs.push(r);
    }
    grupos.forEach((g, i) => { g.id = "g-" + i + "-" + semAcento(g.nome).replace(/[^a-z0-9]+/g, "-").slice(0, 40); g.figs = figurasDoGrupo(f, g); });
    const casaReq = r => termos.length && termos.some(alt => contem(txtReq(r), alt));
    // busca vinda da tela de resultados: abrir os grupos que contêm o termo
    const comTexto = ehNorma && temTexto(f.norma);
    if (termos.length && est.qAplicada !== q) {
      est.qAplicada = q;
      const comAchado = grupos.filter(g => g.reqs.some(casaReq));
      const rs = ehNorma && RESUMOS[f.norma];
      const secsAchado = rs ? (rs.secoes || []).map((s, i) => [s, i]).filter(([s]) => termos.some(alt => contem(txtSecao(s), alt))).map(([, i]) => i) : [];
      if (secsAchado.length) est.resAbertos = new Set(secsAchado);
      // consulta-tabela e a busca é o nome de uma linha (ex. "W4x13", "HEB 200"): abrir direto na Consulta rápida
      const qc = compacto(q);
      const nomeDeLinha = f.calculadora === "consulta-tabela" && /\d/.test(qc) && (f.tabelas || []).some(t => t.consulta !== false &&
        t.linhas.some(l => txtLinha(l).includes(qc)));
      if (nomeDeLinha) est.aba = "calc";
      else if (comAchado.length || !ehNorma) { est.aba = "req"; est.abertos = new Set(comAchado.map(g => g.id)); }
      else if (secsAchado.length) est.aba = "res";
      else if (comTexto) { est.aba = "txt"; est.txt = { q, k: -1, auto: true }; } // sem item achado: procurar no texto
    }
    // pedido vindo de outra tela (requisito de ficha temática, índice da busca): abrir o texto no trecho
    if (textoPendente && ehNorma && textoPendente.norma === f.norma) {
      if (comTexto) {
        est.aba = "txt"; est.ir = { p: textoPendente.p, tr: textoPendente.tr, alt: textoPendente.alt };
        if (textoPendente.q) est.txt = { q: textoPendente.q, k: -1, auto: true, alt: textoPendente.alt };
      }
      textoPendente = null;
    }
    if (!est.abertos) est.abertos = new Set(grupos.length ? [grupos[0].id] : []);
    let emLinha = FIG_LINHA.get(f);
    if (!emLinha) FIG_LINHA.set(f, emLinha = figurasEmLinha(f));
    const figsEmLinha = new Set([].concat(...emLinha.values()));

    const temCalc = f.calculadora && CALCULADORAS[f.calculadora];
    const tabelas = f.tabelas || [];
    const figuras = f.figuras || [];
    const notas = f.notas || [];
    const nAtencao = notas.filter(n => n.tipo === "atencao").length;
    // ficha de norma: sumário (índice do PDF), definições, referências e valores nas fichas temáticas
    const arquivo = ehNorma ? (f.arquivo || NORMAS[f.norma]?.arquivo) : null;
    const sumario = ehNorma ? sumarioDe(arquivo) : null;
    const definicoes = ehNorma ? (f.definicoes || []) : [];
    const refsNorm = ehNorma ? (f.referencias_normativas || []) : [];
    const citam = ehNorma ? (citacoes()[f.norma] || []).filter(c => c.f.id !== f.id) : [];
    const nCitam = citam.reduce((s, c) => s + c.reqs.length + c.tabs.length + c.figs.length, 0);
    const resumo = ehNorma ? RESUMOS[f.norma] : null;
    const abas = [
      resumo && ["res", `Resumo <span class="n">${(resumo.secoes || []).length}</span>`],
      comTexto && ["txt", "Texto completo"],
      temCalc && ["calc", f.calculadora === "consulta-tabela" ? "Consulta rápida" : "Calculadora"],
      reqsF.length && ["req", `${ehNorma ? "Itens" : "Requisitos"} <span class="n">${reqsF.length}</span>`],
      tabelas.length && ["tab", `Tabelas <span class="n">${tabelas.length}</span>`],
      figuras.length && ["fig", `Figuras <span class="n">${figuras.length}</span>`],
      citam.length && ["tem", `Em fichas temáticas <span class="n">${nCitam}</span>`],
      sumario && sumario.ents.length && ["sum", `Sumário <span class="n">${sumario.ents.length}</span>`],
      definicoes.length && ["def", `Definições <span class="n">${definicoes.length}</span>`],
      refsNorm.length && ["ref", `Referências normativas <span class="n">${refsNorm.length}</span>`],
      notas.length && ["notas", `Notas <span class="n${nAtencao ? " alerta" : ""}">${notas.length}</span>`],
    ].filter(Boolean);
    if (!abas.some(a => a[0] === est.aba)) est.aba = abas.length ? abas[0][0] : null;

    const umaNota = n => `<div class="nota ${n.tipo}"><b>${{ atencao: "Atenção:", info: "Info:", dica: "Dica:" }[n.tipo]}</b>${esc(n.texto)}</div>`;
    const ordemNota = { atencao: 0, dica: 1, info: 2 };
    const fab = {}; // corpos montados ao abrir (details[data-lazy])

    // ---- aba Requisitos: grupos recolhíveis, figuras do grupo ao lado da tabela
    const celNorma = r => {
      const lk = linkTexto(r.norma, r.pagina, r.parametro);
      return `<td class="norma">${chipNorma(r.norma)}${lk ? `<span class="ir-texto-req">${lk}</span>` : ""}</td>`;
    };
    const linhaReq = r => {
      const figs = emLinha.get(r);
      if (figs) // recorte de tabela/figura: a imagem entra no próprio item
        return `<tr class="em-linha${casaReq(r) ? " destaque" : ""}" data-t="${esc(txtReq(r))}">
            <td colspan="2"><span class="param-fig">${marcar(esc(r.parametro), termos)}</span>
              ${figs.map(fig => figuraHtml(fig, false, true)).join("")}
              ${r.nota ? `<details class="texto-ext"><summary>Texto extraído (para a busca; vale a imagem)</summary><span class="nota-req">${marcar(esc(r.nota.replace(/^Texto[^:]{0,60}:\s*/, "")), termos)}</span></details>` : ""}</td>
            ${celNorma(r)}</tr>`;
      return `<tr class="${casaReq(r) ? "destaque" : ""}${temCota(r) ? " com-cota" : ""}" data-t="${esc(txtReq(r))}"${attrCota(r)}>
            <td>${marcar(esc(r.parametro), termos)}${botaoCota(r)}${r.nota ? `<span class="nota-req">${marcar(esc(r.nota), termos)}</span>` : ""}</td>
            <td class="valor${r.valor.length > 70 ? " longo" : ""}">${marcar(esc(r.valor), termos)}</td>
            ${celNorma(r)}</tr>`;
    };
    // grupos grandes (ex. 291 recortes de tabela): linhas em lotes, para não criar centenas de <img> ao abrir
    const LIM_REQ = 60;
    const visDe = {}; // g.id -> requisitos visíveis do grupo
    const linhasReq = (gid, de, tudo) => {
      const vis = visDe[gid], ate = tudo ? vis.length : de + LIM_REQ;
      return vis.slice(de, ate).map(linhaReq).join("") + (vis.length > ate
        ? `<tr class="mais-linhas"><td colspan="3"><button type="button" class="botao" data-mais-req="${gid}" data-de="${ate}">Mostrar mais ${Math.min(LIM_REQ, vis.length - ate)} (faltam ${vis.length - ate})</button></td></tr>` : "");
    };
    const abaReq = () => {
      const gruposHtml = grupos.map(g => {
        const vis = g.reqs.filter(r => !ocultas.has(r.norma));
        if (!vis.length) return "";
        visDe[g.id] = vis;
        const nn = [...new Set(vis.map(r => r.norma))];
        const nCasa = vis.filter(casaReq).length;
        const soltas = g.figs.filter(fig => !figsEmLinha.has(fig)); // figuras que não estão em linha num item
        // com achado da busca no grupo: monta tudo (a 1ª linha destacada pode estar além do 1º lote)
        fab[g.id] = () => `${soltas.length ? `<div class="figuras-grupo">${soltas.map(fig => figuraHtml(fig, true)).join("")}</div>` : ""}
          <div class="tabela-wrap"><table class="req"><thead><tr><th>Parâmetro</th><th>Valor</th><th>Norma</th></tr></thead><tbody>
          ${linhasReq(g.id, 0, nCasa > 0)}</tbody></table></div>`;
        return `<details class="grupo cartao" id="${g.id}" data-lazy="${g.id}"${est.abertos.has(g.id) ? " open" : ""}>
          <summary><span class="g-nome">${esc(g.nome)}</span>
            <span class="g-meta">${vis.length} ${ehNorma ? "ite" + (vis.length > 1 ? "ns" : "m") : "valor" + (vis.length > 1 ? "es" : "")}${g.figs.length ? ` · ${g.figs.length} fig.` : ""}${nCasa ? ` · <mark>${nCasa} achado${nCasa > 1 ? "s" : ""}</mark>` : ""}</span>
            ${normas.length > 1 ? `<span class="g-normas">${nn.map(n => `<span class="chip">${esc(n)}</span>`).join("")}</span>` : ""}</summary>
          <div class="corpo"></div></details>`;
      }).join("");
      const chips = `<span class="chips" style="display:inline-flex">${normas.map(n => `<button class="chip" data-norma="${esc(n)}" aria-pressed="${!ocultas.has(n)}">${esc(n)}</button>`).join("")}</span>`;
      return `<div class="barra-ficha">
          <input type="search" id="filtro-local" placeholder="Filtrar nesta ficha — ex.: altura, 1100, NR-12" aria-label="Filtrar nesta ficha">
          <button type="button" class="botao" data-acao="abrir">Expandir tudo</button>
          <button type="button" class="botao" data-acao="fechar">Recolher tudo</button>
        </div>
        ${normas.length < 2 ? "" : normas.length > 12 // muitas normas (ex. especificações ASME II) → lista recolhida
          ? `<details class="filtro-normas"><summary>Normas (${normas.length}) — mostrar/ocultar por norma</summary>${chips}</details>`
          : `<div class="filtro-normas">Normas: ${chips}</div>`}
        <p class="meta" id="filtro-info" hidden></p>
        ${gruposHtml}`;
    };

    // ---- aba Tabelas: agrupadas por norma, com filtro pelo título; corpo montado ao abrir
    const abaTab = () => {
      const porNorma = {};
      tabelas.forEach((t, i) => (porNorma[t.norma] ||= []).push([t, i]));
      const tabelaHtml = ([t, i]) => {
        const cc = cotasDaTabela(t);
        fab["t" + i] = () => `${figurasTabelaHtml(f, t)}<div class="tabela-wrap"><table class="req"><thead><tr>${t.colunas.map((c, k) => `<th${cc[k] ? ' class="th-cota" title="Passe o mouse (ou toque) num valor desta coluna para ver a cota no esquema"' : ""}>${esc(c)}</th>`).join("")}</tr></thead>
          <tbody>${t.linhas.map(l => `<tr>${l.map((v, k) => { const a = cc[k] ? attrCotaCel(t, k, l) : ""; const cl = (k ? "" : "valor") + (a ? " com-cota" : ""); return `<td${cl ? ` class="${cl.trim()}"` : ""}${a}>${esc(v ?? "—")}</td>`; }).join("")}</tr>`).join("")}</tbody></table></div>
          ${t.nota ? `<p class="meta" style="padding:0 12px 10px">${esc(t.nota)}</p>` : ""}
          ${temTexto(t.norma) ? `<p class="meta" style="padding:0 12px 10px">${linkTexto(t.norma, t.pagina, t.titulo)}</p>` : ""}`;
        return `<details class="cartao tabela-dados" data-lazy="t${i}" data-t="${esc(semAcento(t.titulo + " " + t.item))}"><summary><b>${esc(t.titulo)}</b>
          <span class="meta">— ${esc(t.norma)}${t.unidade ? ` · ${esc(t.unidade)}` : ""} · ${t.linhas.length} linhas${t.figuras?.length ? " · com desenho das cotas" : ""}</span></summary>
          <div class="corpo"></div></details>`;
      };
      return `${tabelas.length > 6 ? `<div class="barra-ficha"><input type="search" id="filtro-tab" placeholder="Filtrar tabelas — ex.: NPS 6, classe 300, M12" aria-label="Filtrar tabelas"></div>` : ""}
        ${Object.entries(porNorma).map(([n, ts]) => `<section class="bloco-norma"><h3>${esc(n)} <span class="meta">${ts.length} tabela${ts.length > 1 ? "s" : ""}</span></h3>${ts.map(tabelaHtml).join("")}</section>`).join("")}`;
    };

    // ---- aba Figuras (todas), agrupadas por norma
    // ficha de norma: por tipo (Tabelas / Figuras / Fórmulas / Páginas inteiras), em ordem de página, montadas em lotes (montarFiguras)
    const abaFig = () => {
      if (ehNorma) return `<div class="barra-ficha"><input type="search" id="filtro-fig" placeholder="Filtrar imagens — ex.: table 4, flange, página 120" aria-label="Filtrar imagens" value="${esc(est.figQ || "")}">
          <span class="meta" id="fig-conta"></span></div>
        <div id="grupos-fig"></div>
        <p class="meta">Recortes e páginas inteiras da norma; “Página N” é a página do documento.${comTexto ? " “ver no texto” abre o trecho no texto completo." : ""}</p>`;
      const figPorNorma = {};
      figuras.forEach(fig => (figPorNorma[fig.norma] ||= []).push(fig));
      return Object.entries(figPorNorma).map(([n, fs]) => `${ehNorma ? "" : `<h3 class="titulo-bloco">${esc(n)}</h3>`}<div class="figuras">${fs.map(fig => figuraHtml(fig)).join("")}</div>`).join("");
    };

    // ---- aba Em fichas temáticas (calculada de dados.js, sem duplicar)
    const abaTem = () => citam.map((c, i) => {
      fab["c" + i] = () => `${c.reqs.length ? `<div class="tabela-wrap"><table class="req"><thead><tr><th>Grupo · parâmetro</th><th>Valor</th></tr></thead><tbody>
          ${c.reqs.map(r => { const lk = linkTexto(r.norma, r.pagina, r.parametro); return `<tr class="${casaReq(r) ? "destaque" : ""}"><td><span class="g-tem">${esc(r.grupo)}</span>${marcar(esc(r.parametro), termos)}${r.nota ? `<span class="nota-req">${esc(r.nota)}</span>` : ""}${lk ? `<span class="ir-texto-req">${lk}</span>` : ""}</td>
            <td class="valor${r.valor.length > 70 ? " longo" : ""}">${marcar(esc(r.valor), termos)}</td></tr>`; }).join("")}</tbody></table></div>` : ""}
        ${c.tabs.length ? `<p class="meta lista-tem"><b>Tabelas:</b> ${c.tabs.slice(0, 60).map(t => esc(t.titulo)).join(" · ")}${c.tabs.length > 60 ? ` · + ${c.tabs.length - 60} na ficha` : ""}</p>` : ""}
        ${c.figs.length ? `<div class="figuras-grupo">${c.figs.map(fig => figuraHtml(fig, true)).join("")}</div>` : ""}`;
      return `<details class="grupo cartao" data-lazy="c${i}"${i === 0 ? " open" : ""}>
        <summary><span class="g-nome">${esc(c.f.titulo)}</span>
          <span class="g-meta">${[c.reqs.length && `${c.reqs.length} valor${c.reqs.length > 1 ? "es" : ""}`, c.tabs.length && `${c.tabs.length} tabela${c.tabs.length > 1 ? "s" : ""}`, c.figs.length && `${c.figs.length} fig.`].filter(Boolean).join(" · ")}</span>
          <a class="g-abrir" href="#/ficha/${c.f.id}">abrir a ficha →</a></summary>
        <div class="corpo"></div></details>`;
    }).join("") + `<p class="meta">Valores desta norma transcritos nas fichas temáticas.</p>`;

    // ---- aba Sumário (índice automático de títulos por página do PDF)
    const LIM_SUM = 400;
    // título do sumário -> trecho no Texto completo (âncora tp-N; o número não aparece)
    const linhaSum = ([p, t]) => `<li class="n${nivelTitulo(t)}" data-t="${esc(semAcento(t))}">${comTexto ? `<a href="#" data-tp="${+p}" data-tr="${esc(t.slice(0, 120))}" title="Ver no texto completo">${esc(t)}</a>` : `<span>${esc(t)}</span>`}</li>`;
    const abaSum = () => `<div class="barra-ficha"><input type="search" id="filtro-sum" placeholder="Filtrar o sumário — ex.: scope, tabela 5, bolt" aria-label="Filtrar o sumário"></div>
      <div class="cartao sumario"><ul class="sumario-lista">${sumario.ents.slice(0, LIM_SUM).map(linhaSum).join("")}</ul>
      ${sumario.ents.length > LIM_SUM ? `<p><button type="button" class="botao" id="sum-todos">Mostrar todos (${sumario.ents.length})</button></p>` : ""}</div>
      <p class="meta">Títulos de seções, tabelas e figuras lidos automaticamente da norma — podem faltar ou vir com erro de OCR.${comTexto ? " Clique num título para lê-lo no texto completo." : ""}</p>`;

    // ---- aba Definições
    const abaDef = () => `${definicoes.length > 12 ? `<div class="barra-ficha"><input type="search" id="filtro-def" placeholder="Filtrar definições" aria-label="Filtrar definições"></div>` : ""}
      <dl class="cartao definicoes">${definicoes.map(d => `<div data-t="${esc(semAcento(d.termo + " " + d.texto))}"><dt>${marcar(esc(d.termo), termos)}${comTexto && d.pagina ? ` <span class="meta">${linkTexto(f.norma, d.pagina, d.termo)}</span>` : ""}</dt>
        <dd>${marcar(esc(d.texto), termos)}</dd></div>`).join("")}</dl>`;

    // ---- aba Referências normativas: código do acervo -> página da norma; senão, busca
    const abaRef = () => `<ul class="cartao refs-normativas">${refsNorm.map(cod => {
      const nid = normaPorCodigo(cod);
      const e = nid && entradaDe(nid);
      return nid ? `<li><a href="${linkNorma(nid)}"><b>${esc(cod)}</b></a> <span class="meta">— ${esc(e ? e.titulo : "")}${e && e.edicao ? ` (${esc(edicaoCurta(e.edicao))})` : ""}</span></li>`
        : `<li><a href="#/busca?q=${encodeURIComponent(cod)}">${esc(cod)}</a> <span class="meta">— não está no acervo (buscar)</span></li>`;
    }).join("")}</ul>`;

    // ---- aba Resumo (conteudo/resumos: texto próprio, reescrito; valores; esquemas próprios)
    const abaRes = () => {
      const secs = resumo.secoes || [];
      if (!est.resAbertos) est.resAbertos = new Set([0]);
      const figRes = x => {
        const arq = typeof x === "string" ? x : x.arquivo;
        const leg = (typeof x === "object" && x.legenda) || "Esquema ilustrativo (não é desenho da norma)";
        return `<figure class="cartao figura mini"><img src="assets/figuras/${esc(arq)}" alt="${esc(leg)}" loading="lazy" decoding="async" title="Clique para ampliar"><figcaption>${esc(leg)}</figcaption></figure>`;
      };
      const txtVal = v => semAcento([v.parametro, v.valor, v.nota, v.item].join(" "));
      const linhaVal = v => {
        const r = { cota: v.cota, valor: String(v.valor), parametro: v.parametro };
        const casa = termos.length && termos.some(alt => contem(txtVal(v), alt));
        return `<tr class="${casa ? "destaque" : ""}${temCota(r) ? " com-cota" : ""}" data-t="${esc(txtVal(v))}"${attrCota(r)}>
          <td>${marcar(esc(v.parametro), termos)}${botaoCota(r)}</td>
          <td class="valor${String(v.valor).length > 70 ? " longo" : ""}">${marcar(esc(v.valor), termos)}${v.nota ? `<span class="nota-val">${marcar(esc(v.nota), termos)}</span>` : ""}</td>
          <td class="item-res">${esc(v.item || "")}</td></tr>`;
      };
      return `<div class="barra-ficha">
          <input type="search" id="filtro-res" placeholder="Filtrar no resumo — ex.: altura, ensaio, 1,5" aria-label="Filtrar no resumo">
          ${secs.length > 1 ? `<button type="button" class="botao" data-acao-res="abrir">Expandir tudo</button>
          <button type="button" class="botao" data-acao-res="fechar">Recolher tudo</button>` : ""}
        </div>
        <p class="meta aviso-resumo">Resumo escrito pelo Projeto Uva (texto próprio, simplificado) — não substitui a norma; confirme na edição vigente.</p>
        ${resumo.resumo ? `<p class="cartao texto-res">${marcar(esc(resumo.resumo), termos)}</p>` : ""}
        ${secs.map((s, i) => {
          const vals = s.valores || [], figs = s.figuras || [];
          const nCasa = termos.length ? vals.filter(v => termos.some(alt => contem(txtVal(v), alt))).length : 0;
          return `<details class="grupo cartao sec-resumo" data-sec="${i}" data-t="${esc(semAcento([s.item, s.titulo, s.texto].join(" ")))}"${est.resAbertos.has(i) ? " open" : ""}>
            <summary><span class="g-nome">${s.item ? `<span class="item-sec">${esc(s.item)}</span> ` : ""}${marcar(esc(s.titulo), termos)}</span>
              <span class="g-meta">${[vals.length && `${vals.length} valor${vals.length > 1 ? "es" : ""}`, figs.length && `${figs.length} esquema${figs.length > 1 ? "s" : ""}`].filter(Boolean).join(" · ")}${nCasa ? ` · <mark>${nCasa} achado${nCasa > 1 ? "s" : ""}</mark>` : ""}</span></summary>
            <div class="corpo">
              ${s.texto ? `<p class="texto-res">${marcar(esc(s.texto), termos)}</p>` : ""}
              ${figs.length ? `<div class="figuras-grupo">${figs.map(figRes).join("")}</div>` : ""}
              ${vals.length ? `<div class="tabela-wrap"><table class="req"><thead><tr><th>Parâmetro</th><th>Valor</th><th>Item</th></tr></thead><tbody>${vals.map(linhaVal).join("")}</tbody></table></div>` : ""}
            </div></details>`;
        }).join("")}`;
    };

    const abaNotas = () => `<div class="notas">${[...notas].sort((a, b) => ordemNota[a.tipo] - ordemNota[b.tipo]).map(umaNota).join("")}</div>`;
    const relacionadas = [...new Set([...(f.relacionadas || []), ...citam.map(c => c.f.id)])].filter(r => FICHAS[r] && r !== id);
    // ---- aba Texto completo (montada por montarTexto depois do innerHTML)
    const abaTxt = () => `<div class="barra-ficha barra-texto">
        <input type="search" id="busca-texto" placeholder="Buscar no texto — ex.: hydrostatic test, 1,5" aria-label="Buscar no texto" value="${esc(est.txt.q || "")}">
        <span class="tx-conta meta" id="tx-conta" aria-live="polite"></span>
        <button type="button" class="botao" id="tx-ant" title="Ocorrência anterior (Shift+Enter)">↑ Anterior</button>
        <button type="button" class="botao" id="tx-prox" title="Próxima ocorrência (Enter)">Próxima ↓</button>
      </div>
      <div class="cartao texto-completo" id="texto-completo"><p class="meta tx-carregando">Carregando o texto…</p></div>`;

    const conteudoAba = est.aba ? ({ res: abaRes, txt: abaTxt, calc: () => `<div class="cartao calc" id="calc"></div>`, req: abaReq, tab: abaTab, fig: abaFig, tem: abaTem, sum: abaSum, def: abaDef, ref: abaRef, notas: abaNotas }[est.aba])()
      : `<div class="cartao vazio">Ainda sem itens extraídos desta norma.</div>`;

    // ---- cabeçalho
    let cabecalho;
    if (ehNorma) {
      const n = NORMAS[f.norma] || {};
      const [cod, tit] = codigoTitulo(f.norma, f);
      const subst = [].concat(f.substitui || []);
      const pagEsc = f.pagina_escopo;
      cabecalho = `<div class="cartao cabecalho-ficha cabecalho-norma">
        <div class="categoria">Norma · ${esc(f.categoria)}${f.assunto ? ` · ${esc(f.assunto)}` : ""}</div>
        <h1>${esc(cod)}</h1>
        <p class="titulo-norma">${esc(tit)}</p>
        <div class="meta-norma">
          ${f.edicao || n.edicao ? `<span>Edição <b>${esc(f.edicao || n.edicao)}</b></span>` : ""}
          ${f.paginas ? `<span>${fmt(f.paginas)} págs.</span>` : ""}
          ${subst.length ? `<span>Substitui: ${esc(subst.join("; "))}</span>` : ""}
        </div>
        ${f.escopo ? `<div class="escopo"><b>Escopo</b>${pagEsc && comTexto ? ` <span class="meta">${linkTexto(f.norma, pagEsc, f.escopo.slice(0, 60))}</span>` : ""}<p>${marcar(esc(f.escopo), termos)}</p>${f.nota_escopo ? `<p class="meta">${esc(f.nota_escopo)}</p>` : ""}</div>`
          : f.resumo && f.resumo !== tit ? `<p>${esc(f.resumo)}</p>` : ""}
        ${nAtencao ? `<div class="resumo-ficha meta"><a href="#" data-aba-link="notas" class="alerta-link">⚠ ${nAtencao} nota${nAtencao > 1 ? "s" : ""} de atenção</a></div>` : ""}
      </div>`;
    } else {
      cabecalho = `<div class="cartao cabecalho-ficha">
        <div class="categoria">${esc(f.categoria)}</div>
        <h1>${esc(f.titulo)}</h1>
        <p>${esc(f.resumo)}</p>
        <div class="resumo-ficha meta">${reqsF.length} valores · ${grupos.length} grupos · ${normas.length} normas${tabelas.length ? ` · ${tabelas.length} tabelas` : ""}${figuras.length ? ` · ${figuras.length} figuras` : ""}
          ${nAtencao ? ` · <a href="#" data-aba-link="notas" class="alerta-link">⚠ ${nAtencao} nota${nAtencao > 1 ? "s" : ""} de atenção</a>` : ""}</div>
      </div>`;
    }

    const lateral = [
      est.aba === "req" && grupos.length > 1 && `<div class="cartao"><h3>Grupos</h3><ul class="indice">
        ${grupos.map(g => `<li><a href="#${g.id}" data-rolar="${g.id}">${esc(g.nome)} <span class="meta">${g.reqs.length}</span></a></li>`).join("")}</ul></div>`,
      !ehNorma && `<div class="cartao"><h3>Normas</h3><ul class="normas-lista">
        ${normas.map(n => NORMAS[n]).filter(Boolean).map(n => `<li><b><a href="${linkNorma(n.id)}">${esc(n.id)}</a></b> ${esc(n.edicao)}<br><span class="meta">${esc(n.titulo)}</span></li>`).join("")}</ul></div>`,
      relacionadas.length && `<div class="cartao"><h3>${ehNorma ? "Fichas temáticas" : "Relacionadas"}</h3><ul class="indice">${relacionadas.map(r => `<li><a href="#/ficha/${r}">${esc(FICHAS[r].titulo)}</a></li>`).join("")}</ul></div>`,
    ].filter(Boolean).join("");

    app.innerHTML = `${cabecalho}
      ${abas.length ? `<nav class="abas" role="tablist">${abas.map(([k, rot]) => `<button type="button" role="tab" class="aba" data-aba="${k}" aria-selected="${k === est.aba}">${rot}</button>`).join("")}</nav>` : ""}
      <div class="layout-ficha${lateral ? "" : " sem-lateral"}">
        <div id="conteudo-aba">${conteudoAba}</div>
        ${lateral ? `<aside class="lateral">${lateral}</aside>` : ""}
      </div>`;

    preguicoso(app, fab);
    const conteudo = document.getElementById("conteudo-aba");
    // Itens: "Mostrar mais" (lote seguinte de linhas do grupo)
    const maisReq = (b, tudo) => {
      const tr = b.closest("tr");
      tr.insertAdjacentHTML("afterend", linhasReq(b.dataset.maisReq, +b.dataset.de, tudo));
      tr.remove();
    };
    conteudo.addEventListener("click", e => {
      const b = e.target.closest("button[data-mais-req]");
      if (b) maisReq(b);
    });
    if (est.aba === "fig" && ehNorma) montarFiguras();
    const trocarAba = k => { est.aba = k; telaFicha(f, q); document.querySelector(".abas")?.scrollIntoView({ block: "nearest" }); };
    app.querySelectorAll("button[data-aba]").forEach(b => b.addEventListener("click", () => trocarAba(b.dataset.aba)));
    app.querySelectorAll("a[data-aba-link]").forEach(a => a.addEventListener("click", e => { e.preventDefault(); trocarAba(a.dataset.abaLink); }));
    app.querySelectorAll("button[data-norma]").forEach(b => b.addEventListener("click", () => {
      const n = b.dataset.norma;
      ocultas.has(n) ? ocultas.delete(n) : ocultas.add(n);
      telaFicha(f, q);
    }));
    // grupos: lembrar quais estão abertos
    const detalhes = [...app.querySelectorAll("details.grupo[id]")];
    detalhes.forEach(d => d.addEventListener("toggle", () => { d.open ? est.abertos.add(d.id) : est.abertos.delete(d.id); }));
    app.querySelectorAll("button[data-acao]").forEach(b => b.addEventListener("click", () => {
      const abrir = b.dataset.acao === "abrir";
      detalhes.forEach(d => { if (!d.hidden) d.open = abrir; });
    }));
    // índice lateral: abre o grupo e rola até ele
    app.querySelectorAll("a[data-rolar]").forEach(a => a.addEventListener("click", e => {
      e.preventDefault();
      const alvo = document.getElementById(a.dataset.rolar);
      if (!alvo) return;
      if (alvo.tagName === "DETAILS") alvo.open = true;
      alvo.scrollIntoView({ behavior: "smooth", block: "start" });
    }));
    // filtro local dos requisitos: monta todos os grupos, esconde linhas/grupos sem o texto e abre os que têm
    const filtro = document.getElementById("filtro-local");
    if (filtro) {
      const info = document.getElementById("filtro-info");
      filtro.addEventListener("input", () => {
        const alts = termosDaConsulta(filtro.value);
        if (alts.length) detalhes.forEach(d => {
          if (d.montar) d.montar();
          d.querySelectorAll("button[data-mais-req]").forEach(b => maisReq(b, true)); // filtro vê todas as linhas
        });
        let total = 0;
        detalhes.forEach(d => {
          let n = 0;
          d.querySelectorAll("tbody tr").forEach(tr => {
            const ok = !alts.length || alts.every(alt => alt.some(t => tr.dataset.t.includes(t)));
            tr.hidden = !ok; if (ok) n++;
          });
          d.hidden = alts.length > 0 && n === 0;
          if (alts.length) d.open = n > 0;
          total += n;
        });
        info.hidden = !alts.length;
        info.textContent = `${total} valor(es) com "${filtro.value.trim()}"`;
      });
    }
    const filtroTab = document.getElementById("filtro-tab");
    if (filtroTab) filtroTab.addEventListener("input", () => {
      const alts = termosDaConsulta(filtroTab.value);
      app.querySelectorAll(".bloco-norma").forEach(sec => {
        let n = 0;
        sec.querySelectorAll("details.tabela-dados").forEach(d => {
          const ok = !alts.length || alts.every(alt => alt.some(t => d.dataset.t.includes(t)));
          d.hidden = !ok; if (ok) n++;
        });
        sec.hidden = n === 0;
      });
    });
    // filtros simples por data-t (sumário, definições)
    const sumTodos = () => {
      const b = document.getElementById("sum-todos");
      if (!b) return;
      app.querySelector(".sumario-lista").innerHTML = sumario.ents.map(linhaSum).join("");
      b.remove();
    };
    document.getElementById("sum-todos")?.addEventListener("click", sumTodos);
    const filtrarItens = (input, sel, antes) => input && input.addEventListener("input", () => {
      if (antes) antes();
      const alts = termosDaConsulta(input.value);
      app.querySelectorAll(sel).forEach(el => { el.hidden = alts.length > 0 && !alts.every(alt => alt.some(t => el.dataset.t.includes(t))); });
    });
    filtrarItens(document.getElementById("filtro-sum"), ".sumario-lista li", sumTodos);
    filtrarItens(document.getElementById("filtro-def"), ".definicoes > div");
    // Resumo: seções abertas lembradas; filtro (seção pelo título/texto, linhas pelos valores); expandir/recolher
    const secsRes = [...app.querySelectorAll("details.sec-resumo")];
    secsRes.forEach(d => d.addEventListener("toggle", () => { d.open ? est.resAbertos.add(+d.dataset.sec) : est.resAbertos.delete(+d.dataset.sec); }));
    app.querySelectorAll("button[data-acao-res]").forEach(b => b.addEventListener("click", () => {
      const abrir = b.dataset.acaoRes === "abrir";
      secsRes.forEach(d => { if (!d.hidden) d.open = abrir; });
    }));
    const filtroRes = document.getElementById("filtro-res");
    if (filtroRes) filtroRes.addEventListener("input", () => {
      const alts = termosDaConsulta(filtroRes.value);
      const casa = t => alts.every(alt => alt.some(x => t.includes(x)));
      secsRes.forEach(d => {
        const secCasa = alts.length > 0 && casa(d.dataset.t);
        let n = 0;
        d.querySelectorAll("tbody tr").forEach(tr => {
          const ok = !alts.length || secCasa || casa(tr.dataset.t);
          tr.hidden = !ok; if (ok) n++;
        });
        const ok = !alts.length || secCasa || n > 0;
        d.hidden = !ok;
        if (alts.length) d.open = ok;
      });
    });
    // sumário: título -> trecho no texto completo
    app.querySelector(".sumario-lista")?.addEventListener("click", e => {
      const a = e.target.closest("a[data-tp]");
      if (!a) return;
      e.preventDefault();
      est.ir = { p: +a.dataset.tp, tr: a.dataset.tr || "" };
      trocarAba("txt");
    });
    /** Aba Figuras da ficha de norma: um grupo recolhível por tipo, em ordem de página; imagens criadas em lotes
        (botão "Mostrar mais", disparado sozinho quando chega perto da tela). Filtro por legenda/item/"página N". */
    function montarFiguras() {
      const alvo = document.getElementById("grupos-fig");
      const entrada = document.getElementById("filtro-fig");
      const conta = document.getElementById("fig-conta");
      const LOTE = 36;
      const todas = figuras.map((fig, i) => ({ fig, i, tipo: tipoFig(fig), t: semAcento(`${fig.legenda} ${fig.item} pagina ${fig.pagina} pag ${fig.pagina}`) }))
        .sort((a, b) => (a.fig.pagina || 0) - (b.fig.pagina || 0) || a.i - b.i);
      est.figAbertos ||= new Set([(TIPOS_FIG.find(([k]) => todas.some(x => x.tipo === k)) || [])[0]]);
      let obs = null;
      function desenhar() {
        if (obs) obs.disconnect();
        const alts = termosDaConsulta(est.figQ || "");
        const lista = alts.length ? todas.filter(x => alts.every(alt => alt.some(t => x.t.includes(t)))) : todas;
        conta.textContent = alts.length ? `${lista.length} de ${todas.length} imagens` : `${todas.length} imagens`;
        const porTipo = TIPOS_FIG.map(([k, nome]) => [k, nome, lista.filter(x => x.tipo === k)]).filter(x => x[2].length);
        alvo.innerHTML = porTipo.length ? porTipo.map(([k, nome, xs]) => `<details class="cartao grupo grupo-fig" data-tipo="${k}"${alts.length || est.figAbertos.has(k) ? " open" : ""}>
            <summary><span class="g-nome">${esc(nome)}</span><span class="g-meta">${xs.length}${xs.length > 1 ? ` · páginas ${+xs[0].fig.pagina || "?"}–${+xs[xs.length - 1].fig.pagina || "?"}` : ""}</span></summary>
            <div class="corpo"><div class="figuras"></div></div></details>`).join("")
          : `<p class="meta">Nenhuma imagem com "${esc(est.figQ)}".</p>`;
        obs = "IntersectionObserver" in window ? new IntersectionObserver(ents => {
          for (const e of ents) if (e.isIntersecting) e.target.click();
        }, { rootMargin: "600px 0px" }) : null;
        alvo.querySelectorAll("details.grupo-fig").forEach(d => {
          const xs = porTipo.find(x => x[0] === d.dataset.tipo)[2];
          const grade = d.querySelector(".figuras");
          let feitas = 0;
          const lote = () => {
            const velho = d.querySelector(".mais-fig");
            if (velho) { if (obs) obs.unobserve(velho.firstChild); velho.remove(); }
            grade.insertAdjacentHTML("beforeend", xs.slice(feitas, feitas + LOTE).map(x => figuraHtml(x.fig, false, false, true)).join(""));
            feitas = Math.min(xs.length, feitas + LOTE);
            if (feitas < xs.length) {
              grade.insertAdjacentHTML("afterend", `<p class="mais-fig"><button type="button" class="botao">Mostrar mais ${Math.min(LOTE, xs.length - feitas)} (faltam ${xs.length - feitas})</button></p>`);
              const b = d.querySelector(".mais-fig button");
              b.addEventListener("click", lote);
              if (obs) obs.observe(b);
            }
          };
          if (d.open) lote();
          d.addEventListener("toggle", () => {
            if (!alts.length) d.open ? est.figAbertos.add(d.dataset.tipo) : est.figAbertos.delete(d.dataset.tipo);
            if (d.open && !feitas) lote();
          });
        });
      }
      desenhar();
      let espera;
      entrada.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(() => { est.figQ = entrada.value; desenhar(); }, 200); });
    }

    atual = { f, q, est, irTexto: null };
    if (est.aba === "txt" && comTexto) montarTexto(document.getElementById("conteudo-aba"), f.norma, est);
    if (est.aba === "calc" && temCalc) CALCULADORAS[f.calculadora](document.getElementById("calc"), f, q);
    const primeiro = app.querySelector("tr.destaque");
    if (primeiro && (est.aba === "req" || est.aba === "tem" || est.aba === "res")) primeiro.scrollIntoView({ block: "center" });
  }
  let atual = null; // ficha na tela: {f, q, est, irTexto(p, tr)}

  // ---------- Texto completo da norma (dados/textos/*.js) ----------
  const TXT_NORM = new Map(); // normaId -> textos normalizados (sem acento, minúsculas, mesmo comprimento)
  function normalizarIgual(t) {
    const n = semAcento(t);
    if (n.length === t.length) return n;
    let s = ""; // caso raro (ex. "İ", "ß"): caractere a caractere, mantendo os índices
    for (let i = 0; i < t.length; i++) { const c = semAcento(t[i]); s += c.length === 1 ? c : c.length ? c[0] : t[i]; }
    return s;
  }
  const textosNorm = (nid, pags) => {
    let n = TXT_NORM.get(nid);
    if (!n) TXT_NORM.set(nid, n = pags.map(p => normalizarIgual(p || "")));
    return n;
  };
  /** Expressão da busca: palavras sem acento, qualquer espaço/quebra de linha entre elas. */
  function regexBusca(q, max = 12) {
    const ps = semAcento(q).split(/\s+/).filter(Boolean).slice(0, max).map(w => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    return ps.length ? new RegExp(ps.join("\\s+"), "g") : null;
  }
  const MAX_ACHADOS = 5000;
  let obsTexto = null; // IntersectionObserver do texto na tela (desligado ao montar outro)
  let rolouSozinho = false; // o usuário rolou a página (cancela a correção de posição após um salto no texto)
  ["wheel", "touchmove"].forEach(t => window.addEventListener(t, () => { rolouSozinho = true; }, { passive: true }));
  window.addEventListener("keydown", e => {
    if (/^(Page|Arrow(Up|Down)|Home|End| )/.test(e.key) && !/input|select|textarea/i.test(e.target.tagName)) rolouSozinho = true;
  });

  function montarTexto(raiz, nid, est) {
    const caixa = raiz.querySelector("#texto-completo");
    const entrada = raiz.querySelector("#busca-texto");
    const conta = raiz.querySelector("#tx-conta");
    const st = est.txt;
    carregarTexto(nid, pags => {
      if (!document.body.contains(caixa)) return; // o usuário saiu da aba
      if (!pags) { caixa.innerHTML = `<p class="meta">Texto completo indisponível para esta norma.</p>`; return; }
      const norm = textosNorm(nid, pags);
      let achados = [];     // [{p, i, f}]
      let porPagina = new Map(); // p -> [índices em achados]
      let alvo = null;      // {p, i, f}: trecho pedido (sumário, item)
      const feitas = new Set();
      // estimativa de altura antes de renderizar (rolagem estável): ~ 95 caracteres por linha de 22 px
      const altura = t => Math.max(40, Math.ceil(t.length / 95) * 22 + (t.match(/\n/g) || []).length * 6);
      // imagens (recortes / páginas inteiras) da norma por página: link "ver imagem" no início da página do texto
      const figsPag = new Map();
      for (const fig of FICHA_DA_NORMA[nid]?.figuras || []) if (fig.pagina) {
        if (!figsPag.has(+fig.pagina)) figsPag.set(+fig.pagina, []);
        figsPag.get(+fig.pagina).push(fig);
      }
      const linksFig = p => {
        const fs = figsPag.get(p);
        if (!fs) return "";
        return `<div class="tp-figs"><span class="meta">Imagem desta página:</span> ${fs.map((fig, k) => {
          const pl = partesLegenda(fig);
          const rot = pl.inteira ? (pl.trecho ? "página inteira — " + pl.titulo : "ver imagem da página") : pl.titulo;
          return `<a href="#" data-fig-p="${p}" data-fig-k="${k}" title="${esc(fig.legenda)}">${esc(rot.length > 80 ? rot.slice(0, 79) + "…" : rot)}</a>`;
        }).join(" · ")}</div>`;
      };
      caixa.addEventListener("click", e => {
        const a = e.target.closest("a[data-fig-p]");
        if (!a) return;
        e.preventDefault();
        const fig = figsPag.get(+a.dataset.figP)[+a.dataset.figK];
        const pl = partesLegenda(fig);
        abrirZoom(`assets/figuras/${esc(fig.arquivo)}`, `<span class="rot-pag">Página ${+fig.pagina}</span> ${esc(pl.titulo)}`);
      });
      caixa.innerHTML = pags.map((t, i) => (t && t.trim()) || figsPag.has(i + 1)
        ? `<section class="tp" id="tp-${i + 1}" style="min-height:${altura(t || "")}px"></section>`
        : `<section class="tp vazia" id="tp-${i + 1}"></section>`).join("");
      const secs = caixa.children;

      function renderizar(i) { // i = índice 0-based
        const sec = secs[i], t = pags[i] || "";
        if (!sec || (!t.trim() && !figsPag.has(i + 1))) return;
        const faixas = (porPagina.get(i) || []).map(k => ({ ...achados[k], k }));
        if (alvo && alvo.p === i) {
          for (let j = faixas.length - 1; j >= 0; j--) if (faixas[j].i < alvo.f && faixas[j].f > alvo.i) faixas.splice(j, 1);
          faixas.push({ ...alvo, k: -1 });
          faixas.sort((a, b) => a.i - b.i);
        }
        let h = "", pos = 0;
        for (const x of faixas) {
          h += esc(t.slice(pos, x.i));
          h += x.k < 0 ? `<mark class="tx-alvo">${esc(t.slice(x.i, x.f))}</mark>`
            : `<mark data-k="${x.k}"${x.k === st.k ? ' class="atual"' : ""}>${esc(t.slice(x.i, x.f))}</mark>`;
          pos = x.f;
        }
        sec.innerHTML = `${linksFig(i + 1)}${t.trim() ? `<div class="tp-txt">${h + esc(t.slice(pos))}</div>` : ""}`;
        sec.style.minHeight = "";
        feitas.add(i);
      }
      const obs = "IntersectionObserver" in window ? new IntersectionObserver(ents => {
        for (const e of ents) if (e.isIntersecting) { const i = +e.target.id.slice(3) - 1; obs.unobserve(e.target); if (!feitas.has(i)) renderizar(i); }
      }, { rootMargin: "1200px 0px" }) : null;
      if (obsTexto) obsTexto.disconnect();
      obsTexto = obs;
      if (obs) for (const s of secs) { if (!s.classList.contains("vazia")) obs.observe(s); }
      else for (let i = 0; i < pags.length; i++) renderizar(i); // navegador sem IntersectionObserver
      const reRenderizar = () => feitas.forEach(i => renderizar(i));

      // rolar até o alvo: renderiza antes as páginas logo acima (alturas reais) e corrige a posição por ~1 s,
      // enquanto o observador renderiza as vizinhas — a menos que o usuário role por conta própria
      let corrigir = [];
      function mostrar(el, bloco) {
        if (!el) return;
        const sec = el.closest(".tp");
        let i = sec ? +sec.id.slice(3) - 2 : -1, h = 0;
        while (i >= 0 && h < 1600) { if (!feitas.has(i)) renderizar(i); h += secs[i].offsetHeight; i--; }
        corrigir.forEach(clearTimeout);
        rolouSozinho = false;
        el.scrollIntoView({ block: bloco });
        corrigir = [80, 250, 600, 1200].map(ms => setTimeout(() => {
          if (!rolouSozinho && document.body.contains(el)) el.scrollIntoView({ block: bloco });
        }, ms));
      }
      function irPara(p, tr, alt) { // p = página 1-based; alt = palavras a tentar se o trecho não aparece literal
        const i = Math.min(Math.max(1, p | 0), pags.length) - 1;
        const antes = alvo ? alvo.p : -1;
        alvo = null;
        if (tr) {
          const re = regexBusca(tr, 8);
          // trecho na própria página; se não achar, nas vizinhas (sumário/índice às vezes erram por 1)
          for (const j of [i, i + 1, i - 1]) {
            if (!re || j < 0 || j >= pags.length) continue;
            re.lastIndex = 0;
            const m = re.exec(norm[j]);
            if (m) { alvo = { p: j, i: m.index, f: m.index + m[0].length }; break; }
          }
        }
        if (!alvo && alt) for (const w of alt) { // busca no texto completo: termos fora de ordem/afastados
          const re = regexBusca(w, 8);
          if (!re) continue;
          re.lastIndex = 0;
          const m = re.exec(norm[i]);
          if (m) { alvo = { p: i, i: m.index, f: m.index + m[0].length }; break; }
        }
        const pi = alvo ? alvo.p : i;
        renderizar(pi);
        if (antes >= 0 && antes !== pi && feitas.has(antes)) renderizar(antes); // tira a marca do alvo anterior
        setTimeout(() => {
          mostrar(alvo ? secs[pi].querySelector("mark.tx-alvo") : secs[pi], alvo ? "center" : "start");
        }, 0);
      }

      function buscar(q, auto) {
        st.q = q;
        achados = []; porPagina = new Map(); st.k = -1;
        const re = q.trim().length >= 2 ? regexBusca(q) : null;
        if (re) {
          fora: for (let p = 0; p < norm.length; p++) {
            re.lastIndex = 0;
            let m;
            while ((m = re.exec(norm[p]))) {
              if (!m[0].length) { re.lastIndex++; continue; }
              if (!porPagina.has(p)) porPagina.set(p, []);
              porPagina.get(p).push(achados.length);
              achados.push({ p, i: m.index, f: m.index + m[0].length });
              if (achados.length >= MAX_ACHADOS) break fora;
            }
          }
        }
        if (auto && !achados.length) { st.q = ""; entrada.value = ""; } // termo da busca global sem ocorrência literal
        reRenderizar();
        atualizarConta();
      }
      function atualizarConta() {
        const n = achados.length, mais = n >= MAX_ACHADOS ? "+" : "";
        conta.textContent = !st.q.trim() ? "" : !n ? "nenhuma ocorrência" : st.k < 0 ? `${n}${mais} ocorrência${n > 1 ? "s" : ""}` : `${st.k + 1} de ${n}${mais}`;
      }
      function ir(k) {
        if (!achados.length) return;
        const ant = st.k;
        st.k = (k + achados.length) % achados.length;
        caixa.querySelector(`mark[data-k="${ant}"]`)?.classList.remove("atual");
        const x = achados[st.k];
        if (!feitas.has(x.p)) renderizar(x.p);
        const m = caixa.querySelector(`mark[data-k="${st.k}"]`);
        m?.classList.add("atual");
        mostrar(m, "center");
        atualizarConta();
      }
      let espera;
      entrada.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(() => buscar(entrada.value), 250); });
      entrada.addEventListener("keydown", e => {
        if (e.key !== "Enter") return;
        e.preventDefault();
        clearTimeout(espera);
        if (entrada.value !== st.q) { buscar(entrada.value); ir(0); return; }
        ir(e.shiftKey ? st.k - 1 : st.k + 1);
      });
      raiz.querySelector("#tx-prox").addEventListener("click", () => ir(st.k + 1));
      raiz.querySelector("#tx-ant").addEventListener("click", () => ir(st.k < 0 ? -1 : st.k - 1));

      if (st.q) buscar(st.q, st.auto);
      // palavras que aparecem na página do trecho pedido primeiro (o realce e o "Próxima" começam por ela)
      const naPagina = ws => {
        const pg = est.ir && norm[(est.ir.p | 0) - 1];
        if (!pg) return ws;
        const tem = w => { const re = regexBusca(w, 8); return !!(re && re.test(pg)); };
        return ws.filter(tem).concat(ws.filter(w => !tem(w)));
      };
      // vindo da busca global: se a frase não aparece literal, realça a 1ª palavra (mais rara) que aparece
      if (st.auto && !achados.length && st.alt) for (const w of naPagina(st.alt)) {
        buscar(w, true);
        if (achados.length) { entrada.value = w; break; }
      }
      st.auto = false; st.alt = null;
      if (atual && atual.est === est) atual.irTexto = irPara;
      if (est.ir) { const { p, tr, alt } = est.ir; est.ir = null; irPara(p, tr, alt); }
      else if (achados.length) setTimeout(() => ir(0), 0);
    });
  }

  // links "ver no texto" (requisitos, figuras, tabelas, índice da busca): abre a norma no Texto completo, no trecho
  document.addEventListener("click", e => {
    const a = e.target.closest("a.ir-texto");
    if (!a) return;
    e.preventDefault();
    document.querySelector(".zoom")?.remove();
    const nid = a.dataset.norma, p = +a.dataset.tp, tr = a.dataset.tr || "";
    if (a.dataset.q) { // resultado da busca no texto completo: abre o texto com a busca aplicada e realçada
      const alt = a.dataset.alt ? a.dataset.alt.split("|") : null;
      if (atual && atual.f.tipo === "norma" && atual.f.norma === nid) {
        atual.est.aba = "txt"; atual.est.ir = { p, tr, alt }; atual.est.txt = { q: a.dataset.q, k: -1, auto: true, alt };
        telaFicha(atual.f, atual.q);
      } else {
        textoPendente = { norma: nid, p, tr, q: a.dataset.q, alt };
        location.hash = linkNorma(nid);
      }
      return;
    }
    if (atual && atual.f.tipo === "norma" && atual.f.norma === nid && document.body.contains(app.querySelector("#texto-completo")) && atual.irTexto) {
      atual.irTexto(p, tr); return; // já está no texto desta norma
    }
    if (atual && atual.f.tipo === "norma" && atual.f.norma === nid) {
      atual.est.aba = "txt"; atual.est.ir = { p, tr };
      telaFicha(atual.f, atual.q);
      document.querySelector(".abas")?.scrollIntoView({ block: "nearest" });
      return;
    }
    textoPendente = { norma: nid, p, tr };
    location.hash = linkNorma(nid);
  });

  // figuras (também as que entram depois, em grupos montados ao abrir): clique amplia
  app.addEventListener("click", ev => {
    const img = ev.target.closest(".figura img");
    if (!img) return;
    const fig = img.closest("figure"), cap = fig.querySelector("figcaption").innerHTML;
    // figura em linha num item: a legenda é o próprio parâmetro (alt da imagem)
    abrirZoom(img.src, fig.classList.contains("em-linha") ? esc(img.alt) + (cap ? "<br>" + cap : "") : cap);
  });
  /** Amplia uma imagem (src) ou um SVG inline já destacado (html, ex. esquema de cota). */
  function abrirZoom(src, leg, html) {
    document.querySelector(".zoom")?.remove();
    const z = document.createElement("div");
    z.className = "zoom";
    z.innerHTML = `<figure>${html ? `<div class="zoom-svg">${html}</div>` : `<img src="${src}" alt="">`}<figcaption>${leg}</figcaption></figure>`;
    z.addEventListener("click", e => { if (e.target.tagName !== "A") z.remove(); });
    document.body.appendChild(z);
    const ajustar = () => z.style.setProperty("--cap", z.querySelector("figcaption").offsetHeight + "px"); // legenda sempre visível
    ajustar();
    z.querySelector("img")?.addEventListener("load", ajustar, { once: true }); // largura da figura muda quando a imagem chega
  }
  document.addEventListener("keydown", e => { if (e.key === "Escape") document.querySelector(".zoom")?.remove(); });

  // ---------- calculadoras ----------
  /** Lê limites marcados nos requisitos: "calc": ["perfil:chave", ...] -> {perfil: {chave: req}} */
  function limitesDaFicha(f) {
    const L = {};
    for (const r of f.requisitos) for (const tag of r.calc || []) {
      const [p, k] = tag.split(":");
      (L[p] ||= {})[k] = r;
    }
    return L;
  }

  function verif(valor, req, casas = 0) {
    if (!req) return { st: "", txt: "—" };
    const okMin = req.min == null || valor >= req.min - 1e-9;
    const okMax = req.max == null || valor <= req.max + 1e-9;
    const ok = okMin && okMax;
    return { ok, txt: `<span class="st ${ok ? "ok" : "nok"}" title="${esc(req.norma + " — " + req.valor)}">${ok ? "✓" : "✗"} ${fmt(valor, casas)}</span>` };
  }

  const CALCULADORAS = {
    escada(el, f) {
      const L = limitesDaFicha(f);
      const perfis = f.calculadora_perfis || Object.fromEntries(Object.keys(L).map(p => [p, p]));
      el.innerHTML = `<h2 style="margin-top:0">Calculadora de escada</h2>
        <p class="meta">Informe o desnível; o número de degraus e a pisada são sugeridos pelos limites da norma escolhida (alvo de Blondel g + 2h ≈ 630 mm). Os limites vêm da tabela desta ficha.</p>
        <div class="entradas">
          <label>Desnível total H (mm)<input id="c-H" type="number" min="100" step="10" value="3000"></label>
          <label>Dimensionar por<select id="c-perfil">${Object.entries(perfis).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("")}</select></label>
          <label>Nº de espelhos (opcional)<input id="c-n" type="number" min="1" step="1" placeholder="auto"></label>
          <label>Pisada g (mm, opcional)<input id="c-g" type="number" min="100" step="5" placeholder="auto"></label>
          <label>Largura útil (mm)<input id="c-w" type="number" min="300" step="10" value="800"></label>
        </div>
        <div class="saida"><div><div class="kpis" id="c-kpis"></div><div id="c-verif"></div></div><div class="desenho" id="c-desenho"></div></div>`;
      const $ = s => el.querySelector(s);
      const calcular = () => {
        const H = +$("#c-H").value;
        const P = L[$("#c-perfil").value] || {};
        if (!(H > 0)) return;
        // Sugestão: varre nº de espelhos × pisada e escolhe o que viola menos limites do perfil,
        // desempatando pelo Blondel mais próximo de 630 mm. Valores digitados pelo usuário ficam fixos.
        const fora = (v, r) => (r && ((r.min != null && v < r.min - 1e-9) || (r.max != null && v > r.max + 1e-9)) ? 1 : 0);
        const nFix = +$("#c-n").value, gFix = +$("#c-g").value;
        let melhor = null;
        for (let nn = nFix || 1; nn <= (nFix || 300); nn++) {
          const hh = H / nn;
          if (!nFix && hh < 100) break;
          for (let gg = gFix || 150; gg <= (gFix || 400); gg += 5) {
            const viol = fora(hh, P.h) + fora(gg, P.g) + fora(gg + 2 * hh, P.blondel) + fora(Math.atan(hh / gg) * 180 / Math.PI, P.angulo);
            const custo = viol * 1e4 + Math.abs(gg + 2 * hh - 630);
            if (!melhor || custo < melhor.custo) melhor = { custo, n: nn, g: gg };
          }
        }
        const n = melhor.n;
        const h = H / n;
        const g = melhor.g;
        const w = +$("#c-w").value;
        const ang = Math.atan(h / g) * 180 / Math.PI;
        const blondel = g + 2 * h;
        const comp = (n - 1) * g;
        // lances: pelo limite de altura entre patamares e, se a norma tiver, pelo nº máximo de espelhos por lance
        const lancesDe = p => Math.max(
          L[p]?.patamar?.max ? Math.ceil(H / L[p].patamar.max) : 1,
          L[p]?.espelhos_lance?.max ? Math.ceil(n / L[p].espelhos_lance.max) : 1);
        const lances = lancesDe($("#c-perfil").value);

        const aviso = melhor.custo >= 1e4
          ? `<div class="nota atencao" style="grid-column:1/-1"><b>Atenção:</b>nenhuma combinação de nº de espelhos e pisada atende todos os limites deste perfil para H = ${fmt(H)} mm (ver ✗ abaixo). Ajuste o desnível com um patamar/degrau de piso ou fixe n e g manualmente.</div>`
          : "";
        $("#c-kpis").innerHTML = aviso + [
          ["Espelhos (degraus)", fmt(n)], ["Altura do espelho h", fmt(h, 1) + " mm"],
          ["Pisada g", fmt(g) + " mm"], ["Blondel g + 2h", fmt(blondel) + " mm"],
          ["Ângulo α", fmt(ang, 1) + "°"], ["Projeção horizontal*", fmt(comp) + " mm"],
          ["Lances", fmt(lances)], ["Patamares intermediários", fmt(lances - 1)],
        ].map(([r, v]) => `<div class="kpi"><div class="r">${r}</div><div class="n">${v}</div></div>`).join("");

        const ids = Object.keys(perfis);
        const linhas = [
          ["Altura do espelho h (mm)", p => verif(h, L[p]?.h, 1)],
          ["Pisada g (mm)", p => verif(g, L[p]?.g)],
          ["g + 2h (mm)", p => verif(blondel, L[p]?.blondel)],
          ["Ângulo α (°)", p => verif(ang, L[p]?.angulo, 1)],
          ["Largura (mm)", p => verif(w, L[p]?.largura)],
          ["Patamares intermediários", p => ({ txt: L[p]?.patamar ? `<span title="${esc(L[p].patamar.norma + " — " + L[p].patamar.valor)}">${lancesDe(p) - 1} (a cada ≤ ${fmt(L[p].patamar.max)} mm${L[p].espelhos_lance?.max ? ` e ≤ ${L[p].espelhos_lance.max} espelhos` : ""})</span>` : "—" })],
        ];
        $("#c-verif").innerHTML = `<div class="tabela-wrap"><table class="verif"><thead><tr><th>Verificação</th>${ids.map(p => `<th>${esc(perfis[p].split(" — ")[0])}<br><span style="text-transform:none;font-weight:400">${esc((perfis[p].split(" — ")[1] || "").replace(/\(.*\)/, ""))}</span></th>`).join("")}</tr></thead>
          <tbody>${linhas.map(([nome, fn]) => `<tr><td>${nome}</td>${ids.map(p => `<td>${fn(p).txt}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
          <p class="meta">* Projeção sem os patamares: some o comprimento de cada patamar intermediário. ✓/✗ = atende/não atende o limite da norma da coluna (passe o mouse para ver a norma e o valor).</p>`;
        $("#c-desenho").innerHTML = desenhoEscada(H, n, h, g, ang);
      };
      el.querySelectorAll("input,select").forEach(i => i.addEventListener("input", calcular));
      calcular();
    },
  };

  CALCULADORAS["escada-marinheiro"] = function (el, f) {
    const L = limitesDaFicha(f);
    const perfis = f.calculadora_perfis || Object.fromEntries(Object.keys(L).map(p => [p, p]));
    const ids = Object.keys(perfis);
    el.innerHTML = `<h2 style="margin-top:0">Calculadora de escada marinheiro</h2>
      <p class="meta">Informe a altura a vencer. Para cada norma: passo uniforme das barras (barra superior nivelada com o piso de chegada), plataformas de descanso, gaiola e trava-quedas. Limites lidos da tabela desta ficha.</p>
      <div class="entradas"><label>Altura a vencer H (mm)<input id="m-H" type="number" min="300" step="50" value="7500"></label></div>
      <div id="m-saida"></div>`;
    const $ = s => el.querySelector(s);
    const ref = r => r ? ` title="${esc(r.norma + " — " + r.valor)}"` : "";
    const calcular = () => {
      const H = +$("#m-H").value;
      if (!(H > 0)) return;
      const linhas = { "Passo das barras": [], "Nº de barras": [], "Piso → 1ª barra": [], "Plataformas intermediárias": [], "Gaiola": [], "Gaiola — trecho": [], "Trava-quedas / SPIQ": [], "Montantes acima da saída": [] };
      for (const p of ids) {
        const P = L[p] || {};
        // passo: menor nº de vãos que respeita o passo máximo, dentro da faixa
        const sMin = P.passo?.min ?? 250, sMax = P.passo?.max ?? 300;
        let n = Math.ceil(H / sMax);
        const s = H / n;
        const okPasso = s >= sMin - 1e-9;
        linhas["Passo das barras"].push(`<span class="st ${okPasso ? "ok" : "nok"}"${ref(P.passo)}>${okPasso ? "✓" : "✗"} ${fmt(s, 1)} mm</span>`);
        linhas["Nº de barras"].push(`${fmt(n)}`);
        const prim = P.primeira;
        linhas["Piso → 1ª barra"].push(prim ? `<span class="st ${s <= prim.max ? "ok" : "nok"}"${ref(prim)}>${s <= prim.max ? "✓" : "✗"} ${fmt(s, 0)} (máx. ${fmt(prim.max)})</span>` : "—");
        // plataformas
        let plat = 0, txtPlat;
        const unico = P.lance_unico?.max, entre = P.entre_plataformas?.max;
        if (unico && H <= unico) plat = 0;
        else if (entre) plat = Math.ceil(H / entre) - 1;
        else if (unico) plat = Math.ceil(H / unico) - 1;
        txtPlat = (unico || entre) ? `<span${ref(unico && H <= unico ? P.lance_unico : P.entre_plataformas)}>${plat}${plat ? ` (lances ≤ ${fmt(entre || unico)} mm)` : ` (lance único ≤ ${fmt(unico || entre)} mm)`}</span>` : "—";
        linhas["Plataformas intermediárias"].push(txtPlat);
        // gaiola
        const gs = P.gaiola_se;
        const exige = gs ? H > gs.min : null;
        linhas["Gaiola"].push(gs ? `<span class="st ${exige ? "nok" : "ok"}"${ref(gs)}>${exige ? "Obrigatória" : "Não exigida"}</span> <span class="meta">(&gt; ${fmt(gs.min)} mm)</span>` : "—");
        const gi = P.gaiola_inicio, gt = P.gaiola_topo;
        linhas["Gaiola — trecho"].push(exige && gi ? `<span${ref(gi)}>de ${fmt(gi.min)}${gi.max ? `–${fmt(gi.max)}` : ""} mm do piso</span>${gt ? ` <span${ref(gt)}>até ${fmt(gt.min)}${gt.max ? `–${fmt(gt.max)}` : ""} mm acima da chegada</span>` : ""}` : "—");
        const tq = P.trava_quedas_se;
        linhas["Trava-quedas / SPIQ"].push(tq ? `<span class="st ${H > tq.min ? "nok" : "ok"}"${ref(tq)}>${H > tq.min ? "Obrigatório" : "Não exigido"}</span> <span class="meta">(&gt; ${fmt(tq.min)} mm)</span>` : "—");
        const sd = P.saida;
        linhas["Montantes acima da saída"].push(sd ? `<span${ref(sd)}>${fmt(sd.min)}${sd.max ? `–${fmt(sd.max)}` : ""} mm</span>` : "—");
      }
      $("#m-saida").innerHTML = `<div class="tabela-wrap"><table class="verif"><thead><tr><th></th>${ids.map(p => `<th>${esc(perfis[p].split(" — ")[0])}<br><span style="text-transform:none;font-weight:400">${esc(perfis[p].split(" — ")[1] || "")}</span></th>`).join("")}</tr></thead>
        <tbody>${Object.entries(linhas).map(([k, v]) => `<tr><td>${k}</td>${v.map(x => `<td>${x}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
        <p class="meta">"—" = a norma não define esse limite. Passe o mouse sobre um valor para ver a norma e o limite. Conflitos entre normas: veja as notas de atenção acima.</p>`;
    };
    $("#m-H").addEventListener("input", calcular);
    calcular();
  };

  /* Consulta genérica a tabelas da ficha: filtros pelas chaves de "chave" (ex. classe) + valor da 1ª coluna (ex. NPS).
     Rótulos opcionais em f.consulta = {"rotulos": {"classe": "Classe de pressão"}, "linha": "NPS"}. */
  CALCULADORAS["consulta-tabela"] = function (el, f, q) {
    const tabs = (f.tabelas || []).filter(t => t.consulta !== false); // "consulta": false = só exibida na ficha
    const cfg = f.consulta || {};
    const chaves = [...new Set(tabs.flatMap(t => Object.keys(t.chave || {})))];
    const opcoes = k => [...new Set(tabs.map(t => t.chave?.[k]).filter(v => v != null))]
      .sort((a, b) => String(a).localeCompare(String(b), "pt", { numeric: true }));
    const rotulo = k => cfg.rotulos?.[k] || k;
    // busca por nome ou medida em todas as tabelas (ignora os filtros): "w100x19" acha W100X19.3; "100" acha toda linha
    // com alguma medida 100 (ou 100,x); nomes comparados com compacto()
    const termoBusca = qb => { const termo = compacto(qb); return { termo, n: /^\d+(\.\d+)?$/.test(termo) ? Number(termo) : null }; };
    // 3 = no nome/texto da célula; 2 = medida igual; 1 = mesma parte inteira (só se o termo não tem decimal)
    const nivelCel = (v, { termo, n }) => typeof v === "string" ? (compacto(v).includes(termo) ? 3 : 0)
      : typeof v === "number" && n != null ? (v === n ? 2 : !termo.includes(".") && Math.trunc(v) === n ? 1 : 0) : 0;
    function achar(qb) {
      const tb = termoBusca(qb);
      if (!tb.termo) return [];
      const res = [];
      for (const t of tabs) for (const l of t.linhas) {
        const niveis = l.map(v => nivelCel(v, tb));
        const nivel = Math.max(...niveis);
        if (nivel) res.push({ t, l, nivel, cols: niveis.map((x, k) => x && k ? k : 0).filter(Boolean) });
      }
      return res.sort((a, b) => b.nivel - a.nivel);
    }
    el.innerHTML = `<h2 style="margin-top:0">${esc(cfg.titulo || "Consulta rápida")}</h2>
      <p class="meta">${esc(cfg.ajuda || "Escolha os filtros; aparecem todas as cotas da linha em cada tabela da norma.")}</p>
      <div class="entradas"><label class="ct-busca">Buscar por nome ou medida (todas as séries)
        <input type="search" id="ct-busca" placeholder="ex.: W100x19, W4x13, HEB 200, 100" autocomplete="off"></label></div>
      <div id="ct-achados"></div>
      <div class="entradas">
        ${chaves.map(k => `<label>${esc(rotulo(k))}<select data-chave="${esc(k)}">${opcoes(k).map(v => `<option>${esc(v)}</option>`).join("")}</select></label>`).join("")}
        <label>${esc(cfg.linha || "Linha")}<select id="ct-linha"></select></label>
      </div><div id="ct-saida"></div>`;
    const sels = [...el.querySelectorAll("select[data-chave]")];
    const selLinha = el.querySelector("#ct-linha");
    const casa = (t, lista) => lista.every(s => (t.chave?.[s.dataset.chave] ?? s.value) == s.value);
    const filtradas = () => tabs.filter(t => casa(t, sels));
    // filtros em cascata: cada lista só mostra valores que existem com as escolhas anteriores (ex. série → classe)
    const atualizarChaves = () => sels.forEach((s, i) => {
      const k = s.dataset.chave, atual = s.value;
      const vals = [...new Set(tabs.filter(t => casa(t, sels.slice(0, i))).map(t => t.chave?.[k]).filter(v => v != null))]
        .sort((a, b) => String(a).localeCompare(String(b), "pt", { numeric: true }));
      s.innerHTML = vals.map(v => `<option${String(v) === atual ? " selected" : ""}>${esc(v)}</option>`).join("");
      s.closest("label").hidden = !vals.length; // filtro sem opções para a escolha atual some
    });
    const atualizarLinhas = () => {
      const atual = selLinha.value;
      const vals = [...new Set(filtradas().flatMap(t => t.linhas.map(l => String(l[0]))))];
      selLinha.innerHTML = vals.map(v => `<option${v === atual ? " selected" : ""}>${esc(v)}</option>`).join("");
    };
    const mostrar = () => {
      const alvo = selLinha.value;
      const vistas = new Map(); // arquivo do desenho → id da âncora no 1º bloco que o mostra
      const blocos = filtradas().map(t => {
        const l = t.linhas.find(x => String(x[0]) === alvo);
        if (!l) return "";
        const tb = termoBusca(entBusca.value);
        const kpis = `<div class="kpis" style="grid-template-columns:repeat(auto-fill,minmax(170px,1fr))">${t.colunas.slice(1).map((c, i) => { const a = attrCotaCel(t, i + 1, l); return `<div class="kpi${a ? " com-cota" : ""}${tb.termo && nivelCel(l[i + 1], tb) ? " ct-casa" : ""}"${a}${a ? ' title="Ver esta cota no esquema"' : ""}><div class="r">${esc(c)}</div><div class="n">${esc(l[i + 1] ?? "—")}</div></div>`; }).join("")}</div>`;
        // desenho repetido entre blocos: só no 1º; nos seguintes, rótulo que rola até ele
        const novas = [], ancoras = new Set();
        for (const fig of figurasDaTabela(f, t)) {
          if (vistas.has(fig.arquivo)) ancoras.add(vistas.get(fig.arquivo));
          else { const a = "ct-fig-" + vistas.size; vistas.set(fig.arquivo, a); novas.push({ fig, a }); }
        }
        const ver = ancoras.size ? `<p class="ct-ver-acima">${[...ancoras].map((a, i) => `<a href="#" data-ct-fig="${a}">desenho das cotas${ancoras.size > 1 ? ` ${i + 1}` : ""}: ver acima</a>`).join(" · ")}</p>` : "";
        return `<div class="grupo"><h3>${esc(t.titulo)} <span class="meta">— ${esc(t.norma)}${t.unidade ? ` · ${esc(t.unidade)}` : ""}</span></h3>
          ${novas.length ? `<div class="ct-com-fig"><div>${kpis}${ver}</div><div class="ct-figs">${novas.map(({ fig, a }) => figuraHtml(fig, true).replace("<figure ", `<figure id="${a}" `)).join("")}</div></div>` : kpis + ver}</div>`;
      }).join("");
      el.querySelector("#ct-saida").innerHTML = blocos || `<p class="meta">Sem dados para essa combinação.</p>`;
    };
    // "ver acima": rola até o desenho sem mexer no hash (o hash é a rota)
    el.querySelector("#ct-saida").addEventListener("click", e => { // #ct-saida é recriado a cada chamada: sem ouvinte duplicado
      const a = e.target.closest("a[data-ct-fig]");
      if (!a) return;
      e.preventDefault();
      const fig = el.querySelector("#" + a.dataset.ctFig);
      if (!fig) return;
      fig.scrollIntoView({ behavior: "smooth", block: "center" });
      fig.classList.remove("ct-destaque"); void fig.offsetWidth; fig.classList.add("ct-destaque");
    });
    // resultados da busca: lista série · linha · medidas que batem; clicar escolhe os filtros e a linha
    const entBusca = el.querySelector("#ct-busca"), divAchados = el.querySelector("#ct-achados");
    const LIM_ACHADOS = 200;
    let achados = [];
    const listarAchados = tudo => {
      const qb = entBusca.value.trim();
      achados = achar(qb);
      if (!qb) { divAchados.innerHTML = ""; return; }
      if (!achados.length) { divAchados.innerHTML = `<p class="meta">Nada com “${esc(qb)}”.</p>`; return; }
      const vis = tudo ? achados : achados.slice(0, LIM_ACHADOS);
      const serie = t => Object.values(t.chave || {}).join(" · ") || t.titulo;
      divAchados.innerHTML = `<p class="meta">${achados.length} linha(s) com “${esc(qb)}” — clique para ver todas as medidas.</p>
        <div class="tabela-wrap ct-achados"><table class="req"><thead><tr><th>${esc(cfg.linha || "Linha")}</th><th>Série / tabela</th><th>Medidas que batem</th></tr></thead>
        <tbody>${vis.map(({ t, l, cols }, i) => `<tr data-ct-achado="${i}"><td class="valor">${esc(l[0])}${typeof l[1] === "string" ? ` <span class="meta">(${esc(l[1])})</span>` : ""}</td>
          <td>${esc(serie(t))}</td><td>${cols.filter(k => !(k === 1 && typeof l[1] === "string")).map(k => `${esc(t.colunas[k])} = <b>${esc(l[k])}</b>`).join(" · ") || "—"}</td></tr>`).join("")}
        ${vis.length < achados.length ? `<tr><td colspan="3"><button type="button" class="botao" data-ct-todos>Mostrar todas (${achados.length})</button></td></tr>` : ""}</tbody></table></div>`;
    };
    // mostra o achado i embaixo (filtros e linha escolhidos); rolar = clique do usuário
    const escolher = (i, rolar) => {
      const tr = divAchados.querySelector(`tr[data-ct-achado="${i}"]`);
      const { t, l } = achados[i];
      for (const s of sels) { atualizarChaves(); const v = t.chave?.[s.dataset.chave]; if (v != null) s.value = String(v); }
      atualizarChaves(); atualizarLinhas();
      selLinha.value = String(l[0]);
      mostrar();
      divAchados.querySelectorAll("tr.cota-sel").forEach(x => x.classList.remove("cota-sel"));
      tr?.classList.add("cota-sel");
      if (rolar) el.querySelector("#ct-saida").scrollIntoView({ behavior: "smooth", block: "start" });
    };
    const buscarNaConsulta = () => { listarAchados(); achados.length ? escolher(0, false) : mostrar(); };
    divAchados.addEventListener("click", e => {
      if (e.target.closest("[data-ct-todos]")) { listarAchados(true); return; }
      const tr = e.target.closest("tr[data-ct-achado]");
      if (tr) escolher(+tr.dataset.ctAchado, true);
    });
    let esperaBusca;
    entBusca.addEventListener("input", () => { clearTimeout(esperaBusca); esperaBusca = setTimeout(buscarNaConsulta, 150); });
    sels.forEach(s => s.addEventListener("input", () => { atualizarChaves(); atualizarLinhas(); mostrar(); }));
    selLinha.addEventListener("input", mostrar);
    atualizarChaves(); atualizarLinhas(); mostrar();
    // veio da busca geral (ex. "W4x13"): já abre com a busca preenchida, se ela acha alguma linha
    if (q && achar(q).length) { entBusca.value = q; buscarNaConsulta(); }
  };

  function desenhoEscada(H, n, h, g, ang) {
    const W = 600, Hs = 400, m = 60;
    const comp = (n - 1) * g;
    const s = Math.min((W - 2 * m) / Math.max(comp, 1), (Hs - 2 * m) / H);
    const x0 = m, y0 = Hs - m;
    let d = `M ${x0 - 20} ${y0} L ${x0} ${y0}`;
    let x = x0, y = y0;
    for (let i = 0; i < n; i++) {
      y -= h * s; d += ` L ${x} ${y}`;
      if (i < n - 1) { x += g * s; d += ` L ${x} ${y}`; }
    }
    d += ` L ${x + 30} ${y}`;
    const xt = x, yt = y;
    const h1 = h * s, g1 = g * s;
    return `<svg viewBox="0 0 ${W} ${Hs}" role="img" aria-label="Perfil da escada com cotas">
      <line class="piso" x1="${x0 - 20}" y1="${y0}" x2="${W - 10}" y2="${y0}"/>
      <path class="lin" d="${d}"/>
      <line class="cota" x1="${xt + 45}" y1="${y0}" x2="${xt + 45}" y2="${yt}"/>
      <line class="cota" x1="${xt + 40}" y1="${y0}" x2="${xt + 50}" y2="${y0}"/><line class="cota" x1="${xt + 40}" y1="${yt}" x2="${xt + 50}" y2="${yt}"/>
      <text x="${xt + 52}" y="${(y0 + yt) / 2}">H = ${fmt(H)}</text>
      <line class="cota" x1="${x0}" y1="${y0 + 25}" x2="${xt}" y2="${y0 + 25}"/>
      <line class="cota" x1="${x0}" y1="${y0 + 20}" x2="${x0}" y2="${y0 + 30}"/><line class="cota" x1="${xt}" y1="${y0 + 20}" x2="${xt}" y2="${y0 + 30}"/>
      <text x="${(x0 + xt) / 2 - 40}" y="${y0 + 45}">L = ${fmt(comp)}</text>
      <text x="${x0 - 55}" y="${y0 - h1 / 2 + 4}">h ${fmt(h, 0)}</text>
      <text x="${x0 + 2}" y="${y0 - h1 - 6}">g ${fmt(g)}</text>
      <line class="cota" x1="${x0}" y1="${y0}" x2="${xt}" y2="${yt}" stroke-dasharray="3 3"/>
      <text x="${x0 + 40}" y="${y0 - 8}">α ${fmt(ang, 1)}°</text>
      ${g1 < 6 || h1 < 4 ? "" : ""}
    </svg>`;
  }

  // ---------- rotas ----------
  function rota() {
    const h = decodeURIComponent(location.hash.slice(1));
    const [caminho, qs] = h.split("?");
    const q = new URLSearchParams(qs || "").get("q") || "";
    const partes = caminho.split("/").filter(Boolean);
    window.scrollTo(0, 0);
    if (partes[0] === "ficha" && partes[1]) { campo.value = q; telaFicha(FICHAS[partes[1]], q); }
    else if (partes[0] === "norma" && partes[1]) {
      const nid = partes.slice(1).join("/");
      campo.value = q;
      telaFicha(FICHA_DA_NORMA[nid] || fichaSintetica(nid), q);
    }
    else if (partes[0] === "busca") { campo.value = q; telaBusca(q); }
    else { campo.value = ""; telaInicio(); }
  }

  let espera;
  campo.addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(() => {
      const q = campo.value.trim();
      const alvo = q ? "#/busca?q=" + encodeURIComponent(q) : "#/";
      if (location.hash !== alvo) history.replaceState(null, "", alvo);
      q ? telaBusca(q) : telaInicio();
    }, 180);
  });
  document.getElementById("form-busca").addEventListener("submit", e => {
    e.preventDefault();
    const q = campo.value.trim();
    if (!q) return;
    const todos = buscar(q);
    const tem = todos.find(x => x.f.tipo !== "norma");
    const nor = buscarNormas(q, todos)[0];
    // código de norma digitado (ex. "B16.5") abre a norma; senão a 1ª ficha temática
    const alvo = nor && (nor.noCodigo && /\d/.test(q) || !tem) ? linkNorma(nor.e.id) : tem ? `#/ficha/${tem.f.id}` : null;
    if (alvo) location.hash = `${alvo}?q=${encodeURIComponent(q)}`;
  });
  document.addEventListener("keydown", e => {
    if (e.key === "/" && document.activeElement !== campo && !/input|select|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); campo.focus(); }
  });

  // tema
  const raiz = document.documentElement;
  try { const t = localStorage.getItem("uva-tema"); if (t) raiz.dataset.tema = t; } catch (_) { /* sem storage */ }
  document.getElementById("btn-tema").addEventListener("click", () => {
    const escuro = raiz.dataset.tema ? raiz.dataset.tema === "escuro" : matchMedia("(prefers-color-scheme: dark)").matches;
    raiz.dataset.tema = escuro ? "claro" : "escuro";
    try { localStorage.setItem("uva-tema", raiz.dataset.tema); } catch (_) { /* sem storage */ }
  });

  window.addEventListener("hashchange", rota);
  rota();
})();
