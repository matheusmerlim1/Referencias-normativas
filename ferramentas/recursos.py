"""Limite de memória do projeto: usar no MÁXIMO 1/6 da RAM disponível (regra do usuário, 29/out/2026).

  from recursos import procs, limite_mb
  with mp.Pool(procs(400)) as pool: ...        # 400 MB estimados por processo
uso: python -P ferramentas/recursos.py [MB_por_processo]   → mostra RAM livre, limite e nº de processos permitido
"""
import ctypes
import os
import sys

FRACAO = 6  # usar no máximo 1/FRACAO da RAM disponível


class _MemStatus(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def ram_livre_mb():
    """RAM física disponível agora, em MB (Windows: GlobalMemoryStatusEx; outros: /proc/meminfo)."""
    if os.name == "nt":
        m = _MemStatus()
        m.dwLength = ctypes.sizeof(_MemStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPhys // 2**20
    with open("/proc/meminfo") as f:
        for l in f:
            if l.startswith("MemAvailable:"):
                return int(l.split()[1]) // 1024
    return 1024


def limite_mb():
    """Memória que o projeto pode usar: 1/6 da RAM disponível."""
    return ram_livre_mb() // FRACAO


def procs(mb_por_proc, maximo=None):
    """Nº de processos paralelos dentro do limite (mínimo 1; nunca mais que os núcleos − 1)."""
    n = max(1, limite_mb() // max(1, mb_por_proc))
    n = min(n, max(1, (os.cpu_count() or 2) - 1), maximo or n)
    return int(n)


if __name__ == "__main__":
    mb = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    print(f"RAM livre {ram_livre_mb()} MB; limite do projeto (1/{FRACAO}) {limite_mb()} MB; "
          f"processos de {mb} MB permitidos: {procs(mb)}")
