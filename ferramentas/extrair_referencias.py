"""Extração segura dos .zip de referencias/ para referencias/extraido/<ORGAO>/.

Uso:  python -P ferramentas/extrair_referencias.py            (extrai / atualiza)
      python -P ferramentas/extrair_referencias.py --so-testar (só integridade + duplicatas)

- Testa cada zip (zipfile.testzip) e não extrai os corrompidos.
- Zips com conteúdo idêntico (mesmos arquivos por tamanho+CRC+SHA-256) são extraídos uma única vez;
  arquivos repetidos (dentro do mesmo zip ou entre zips) também são gravados uma vez só
  e registrados como cópia no manifesto.
- Bloqueia zip-slip (caminho absoluto, unidade "C:", "..", destino fora da pasta) e
  ignora executáveis/scripts (só registra).
- Nomes: respeita o flag UTF-8 do zip; sem o flag, tenta cp437 -> utf-8.
  Caracteres inválidos no Windows são trocados por "_". Caminhos que passariam de
  MAX_PATH_SEGURO caracteres têm o nome do arquivo encurtado (prefixo + hash) e o
  mapeamento vai para o manifesto.
- Idempotente: se o destino já existe com o mesmo tamanho, não regrava. NÃO apaga os zips.
Saída: referencias/extraido/_manifesto.json (lista de entradas com status).
"""
import hashlib
import json
import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_ZIPS = os.path.join(RAIZ, "referencias")
DESTINO = os.path.join(RAIZ, "referencias", "extraido")
MANIFESTO = os.path.join(DESTINO, "_manifesto.json")
MAX_PATH_SEGURO = 240  # margem abaixo de 260 (MAX_PATH)

BLOQUEADAS = {
    ".exe", ".bat", ".cmd", ".com", ".ps1", ".psm1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
    ".msi", ".msp", ".dll", ".sys", ".scr", ".lnk", ".url", ".hta", ".cpl", ".jar", ".reg", ".pif",
    ".sh", ".py", ".pyw", ".docm", ".xlsm", ".pptm", ".dotm", ".iso", ".img", ".vhd", ".chm",
}
RE_ZIP = re.compile(r"^(?P<nome>.+?)-\d{8}T\d{6}Z-\d+-\d+\.zip$", re.I)
INVALIDOS = re.compile(r'[<>:"|?*\x00-\x1f]')


def orgao_do_zip(nome_zip):
    m = RE_ZIP.match(nome_zip)
    nome = m.group("nome") if m else os.path.splitext(nome_zip)[0]
    nome = nome.strip()
    if nome.upper().startswith("ASME"):
        return "ASME"
    return nome


def nome_entrada(info):
    n = info.filename
    if not (info.flag_bits & 0x800):
        try:
            n = n.encode("cp437").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return n.replace("\\", "/")


def caminho_relativo(nome, orgao):
    """Partes do caminho seguro relativo a extraido/<orgao>/, ou None se zip-slip."""
    if nome.startswith("/") or re.match(r"^[A-Za-z]:", nome):
        return None
    partes = [p for p in nome.split("/") if p not in ("", ".")]
    if any(p == ".." for p in partes):
        return None
    if partes and partes[0].strip().upper() == orgao.upper():
        partes = partes[1:]  # "ABNT/x.pdf" no zip ABNT -> extraido/ABNT/x.pdf
    limpas = []
    for p in partes:
        p = INVALIDOS.sub("_", p).rstrip(" .") or "_"
        if p.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}:
            p = "_" + p
        limpas.append(p)
    return limpas


def encurtar(partes, base):
    """Garante len(caminho absoluto) <= MAX_PATH_SEGURO encurtando o nome do arquivo."""
    cheio = os.path.join(base, *partes)
    if len(cheio) <= MAX_PATH_SEGURO:
        return partes, False
    stem, ext = os.path.splitext(partes[-1])
    h = hashlib.md5("/".join(partes).encode("utf-8")).hexdigest()[:6]
    sobra = MAX_PATH_SEGURO - (len(cheio) - len(partes[-1])) - len(ext) - 7
    if sobra < 10:  # pasta longa demais: encurta também as pastas
        partes = [p[:20] for p in partes[:-1]] + [partes[-1]]
        cheio = os.path.join(base, *partes)
        sobra = MAX_PATH_SEGURO - (len(cheio) - len(partes[-1])) - len(ext) - 7
    novo = stem[:max(sobra, 8)].rstrip(" .-_") + "~" + h + ext
    return partes[:-1] + [novo], True


def sha256_entrada(zf, info):
    h = hashlib.sha256()
    with zf.open(info) as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    so_testar = "--so-testar" in sys.argv
    zips = sorted(f for f in os.listdir(PASTA_ZIPS) if f.lower().endswith(".zip"))
    print(f"{len(zips)} zips em {PASTA_ZIPS}")

    # 1) integridade + assinatura de conteúdo
    corrompidos, assinaturas = [], {}
    for z in zips:
        try:
            with zipfile.ZipFile(os.path.join(PASTA_ZIPS, z)) as zf:
                ruim = zf.testzip()
                assinaturas[z] = frozenset((i.file_size, i.CRC) for i in zf.infolist() if not i.is_dir())
            if ruim:
                corrompidos.append((z, ruim))
        except Exception as e:  # noqa: BLE001 — zip ilegível também é "corrompido"
            corrompidos.append((z, repr(e)))
    print("Corrompidos:", corrompidos or "nenhum")

    # 2) duplicatas de zip (conteúdo idêntico) e subconjuntos
    idem, pular = [], set()
    for i, a in enumerate(zips):
        for b in zips[i + 1:]:
            if a in assinaturas and b in assinaturas and assinaturas[a] and assinaturas[a] == assinaturas[b]:
                idem.append((a, b))
                pular.add(b)
            elif assinaturas.get(a) and assinaturas.get(b) and (assinaturas[a] < assinaturas[b] or assinaturas[b] < assinaturas[a]):
                print(f"Subconjunto: {a if assinaturas[a] < assinaturas[b] else b} está contido em {b if assinaturas[a] < assinaturas[b] else a}")
    for a, b in idem:
        print(f"Idênticos: {a} == {b}  (extrai só o 1º)")
    if so_testar:
        return

    # 3) extração
    os.makedirs(DESTINO, exist_ok=True)
    vistos = {}  # (size, crc) -> [(sha, rel_destino)]
    manifesto = []
    for z in zips:
        if any(z == c[0] for c in corrompidos):
            manifesto.append({"zip": z, "status": "zip_corrompido"})
            continue
        orgao = orgao_do_zip(z)
        base = os.path.join(DESTINO, orgao)
        if z in pular:
            par = next(a for a, b in idem if b == z)
            manifesto.append({"zip": z, "status": "zip_identico_a", "ref": par})
            continue
        with zipfile.ZipFile(os.path.join(PASTA_ZIPS, z)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                nome = nome_entrada(info)
                reg = {"zip": z, "entrada": nome, "orgao": orgao, "tamanho": info.file_size}
                manifesto.append(reg)
                ext = os.path.splitext(nome)[1].lower()
                if ext in BLOQUEADAS:
                    reg["status"] = "bloqueado_executavel"
                    continue
                partes = caminho_relativo(nome, orgao)
                if not partes:
                    reg["status"] = "bloqueado_zip_slip"
                    continue
                partes, encurtado = encurtar(partes, base)
                alvo = os.path.realpath(os.path.join(base, *partes))
                if os.path.commonpath([alvo, os.path.realpath(DESTINO)]) != os.path.realpath(DESTINO):
                    reg["status"] = "bloqueado_zip_slip"
                    continue
                rel = os.path.relpath(alvo, RAIZ).replace("\\", "/")
                if encurtado:
                    reg["nome_encurtado"] = True
                # duplicata de conteúdo?
                chave = (info.file_size, info.CRC)
                sha = None
                if chave in vistos:
                    sha = sha256_entrada(zf, info)
                    igual = next((r for s, r in vistos[chave] if s == sha), None)
                    if igual:
                        reg["status"] = "duplicata_de"
                        reg["arquivo"] = igual
                        continue
                # conteúdo: PDF disfarçado de executável?
                with zf.open(info) as f:
                    cabeca = f.read(4)
                if cabeca[:2] == b"MZ":
                    reg["status"] = "bloqueado_executavel"
                    reg["nota"] = "cabeçalho MZ (executável Windows)"
                    continue
                if os.path.exists(alvo) and os.path.getsize(alvo) == info.file_size:
                    reg["status"] = "ja_existia"
                else:
                    os.makedirs(os.path.dirname(alvo), exist_ok=True)
                    tmp = alvo + ".part"
                    with zf.open(info) as src, open(tmp, "wb") as dst:
                        for b in iter(lambda: src.read(1 << 20), b""):
                            dst.write(b)
                    os.replace(tmp, alvo)
                    reg["status"] = "extraido"
                reg["arquivo"] = rel
                vistos.setdefault(chave, []).append((sha or sha256_entrada(zf, info), rel))
    with open(MANIFESTO, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(r["status"] for r in manifesto))
    print(Counter(r["orgao"] for r in manifesto if r.get("status") in ("extraido", "ja_existia")))
    for r in manifesto:
        if r.get("nome_encurtado") and r["status"] in ("extraido", "ja_existia"):
            print("ENCURTADO:", r["entrada"], "->", r["arquivo"])
        if r.get("status", "").startswith("bloqueado"):
            print("BLOQUEADO:", r["zip"], r["entrada"], r["status"])


if __name__ == "__main__":
    main()
