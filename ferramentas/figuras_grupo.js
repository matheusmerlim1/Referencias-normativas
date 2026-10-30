// relata figuras que não caem em nenhum grupo (mesma regra do app.js). uso: node figgrupo.js (cwd = projeto)
global.window = {};
require(process.cwd() + "/dados/dados_local.js");  // build completo (o dados.js público não tem figuras de norma)
const D = window.UVA_DADOS;
const semAcento = s => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const numFigura = s => { const m = semAcento(s).match(/fig(?:ura|ure|\.)?\s*([a-z]?\d+(?:[.\-]\d+)*[a-z]?)/); return m ? m[1] : null; };
for (const f of D.fichas) {
  const gs = {};
  f.requisitos.forEach(r => (gs[r.grupo] ||= []).push(r));
  const sem = [];
  for (const fig of f.figuras || []) {
    const ok = Object.entries(gs).filter(([g, reqs]) => {
      if (fig.grupo) return [].concat(fig.grupo).includes(g);
      const n = numFigura(fig.item);
      if (!n) return false;
      const re = new RegExp("fig(?:ura|ure|\\.|s\\.)?\\s*(?:[\\w.\\-]+\\s*(?:,|e|and)\\s*)*" + n.replace(/[.\-]/g, "\\$&") + "(?![\\d.\\-]*\\d)");
      return reqs.some(r => r.norma === fig.norma && re.test(semAcento(r.item + " " + (r.nota || ""))));
    });
    if (!ok.length) sem.push(fig.arquivo + " [" + fig.item + "]");
  }
  console.log(f.id, (f.figuras || []).length, "fig; sem grupo:", sem.length, sem.join(" | "));
}
