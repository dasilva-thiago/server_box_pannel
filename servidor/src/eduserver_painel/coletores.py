"""O que o painel mostra: nome, IP, hora, CPU, memória, disco, temperatura, tempo no ar.

Funciona no Linux (o servidor, com Lubuntu) e no Windows (o notebook, na bancada).
A temperatura só existe no Linux; no Windows aparece como "--".
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from datetime import datetime

import psutil


@dataclass(frozen=True)
class Estado:
    nome: str
    ip: str
    hora: str
    cpu: float  # %
    ram: float  # %
    disco: float  # %
    temp: float | None  # °C
    no_ar_s: float


def ip_local() -> str:
    """O IP da placa de rede que leva à rede local. Nenhum pacote sai da máquina:
    "conectar" um socket UDP só escolhe a rota."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
    except OSError:
        return "sem rede"
    finally:
        s.close()
    return "sem rede" if ip.startswith("0.") else ip


# Sensores do processador, em ordem de preferência (Intel, AMD, ARM, ACPI).
_SENSORES = ("coretemp", "k10temp", "cpu_thermal", "acpitz")


def temperatura() -> float | None:
    ler = getattr(psutil, "sensors_temperatures", None)
    if ler is None:  # Windows
        return None
    try:
        sensores = ler()
    except Exception:
        return None
    for nome in _SENSORES:
        leituras = sensores.get(nome) or []
        pacote = [s for s in leituras if (s.label or "").lower().startswith("package")]
        escolhidas = pacote or leituras
        if escolhidas:
            return max(s.current for s in escolhidas)
    todas = [s.current for lista in sensores.values() for s in lista]
    return max(todas) if todas else None


def coletar(disco: str = "/") -> Estado:
    return Estado(
        nome=socket.gethostname(),
        ip=ip_local(),
        hora=datetime.now().strftime("%H:%M"),
        cpu=psutil.cpu_percent(interval=None),
        ram=psutil.virtual_memory().percent,
        disco=psutil.disk_usage(disco).percent,
        temp=temperatura(),
        no_ar_s=time.time() - psutil.boot_time(),
    )
