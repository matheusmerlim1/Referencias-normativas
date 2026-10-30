"""Confere se cada número de requisito/tabela de uma norma aparece no texto da página citada (±1 pág.).
Uso: python -P ferramentas/conferir.py <id-da-ficha> <id-da-norma>
Itens listados = conferir à mão (em geral valores de figura/fórmula, que não estão no texto do PDF)."""
import json,re,sys,pymupdf
ficha,normaid=sys.argv[1],sys.argv[2]
N={n['id']:n for n in json.load(open('conteudo/normas.json',encoding='utf-8'))}
d=json.load(open(f'conteudo/fichas/{ficha}.json',encoding='utf-8'))
pdf=pymupdf.open(stream=open(N[normaid]['arquivo'],'rb').read(),filetype='pdf')
txt=lambda p: pdf[p-1].get_text() if 1<=p<=len(pdf) else ''
norm=lambda s: s.replace(',', '.').replace('\u2009','').replace(' ','')
def nums(s): return set(x.rstrip('.') for x in re.findall(r'\d+(?:[.,]\d+)?',s))
def check(label,s,pag,item):
    if not s: return
    T=norm(txt(pag-1)+txt(pag)+txt(pag+1))
    miss=[n for n in nums(s) if norm(n) not in T]
    it=[x for x in re.findall(r'\d+\.\d+(?:\.\d+)*',item) if x not in T and x not in txt(pag).replace(' ','')]
    if miss or it: print(label,'p',pag,'| faltam:',miss,'| item?',it,'|',s[:110])
for i,r in enumerate(d['requisitos']):
    if r['norma']==normaid: check(f'R{i}',r['valor'],r['pagina'],r['item'])
for t in d.get('tabelas',[]):
    if t['norma']==normaid:
        cells=' '.join(str(c) for l in t['linhas'] for c in l)
        check('T:'+t['id'],cells,t['pagina'],t['item'])
