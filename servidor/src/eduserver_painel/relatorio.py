"""Relatório da bancada (T-BANC): lê o log do serviço e diz se passou.

Critérios em docs/04_bancada.md: pelo menos 48 h, nenhuma desconexão, nenhum
reinício do Nano, nenhum comando sem resposta e o RFID sem se perder.

Aceita o arquivo de log do serviço (--log) e a saída do journalctl
(journalctl -u eduserver-painel -o short-iso > bancada.log).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

_DATA = re.compile(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})")
_EVENTO = re.compile(r"evento=(\w+)")
_CAMPO = re.compile(r"(\w+)=(\S+)")


@dataclass
class Relatorio:
    inicio: datetime | None = None
    fim: datetime | None = None
    conexoes: int = 0
    desconexoes: int = 0
    hello_repetidos: int = 0
    hb: int = 0
    falhas: int = 0
    lat_max_ms: float = 0.0
    cartoes: int = 0
    rfid_problemas: int = 0
    alertas_temp: int = 0
    motivos_desconexao: list[str] = field(default_factory=list)

    @property
    def horas(self) -> float:
        if self.inicio is None or self.fim is None:
            return 0.0
        return (self.fim - self.inicio).total_seconds() / 3600


def analisar(linhas: Iterable[str]) -> Relatorio:
    r = Relatorio()
    for linha in linhas:
        ev = _EVENTO.search(linha)
        if not ev:
            continue
        data = _DATA.search(linha)
        if data:
            quando = datetime.fromisoformat(f"{data.group(1)} {data.group(2)}")
            # Menor e maior horário: aceita logs juntados fora de ordem.
            r.inicio = quando if r.inicio is None else min(r.inicio, quando)
            r.fim = quando if r.fim is None else max(r.fim, quando)
        campos = dict(_CAMPO.findall(linha[ev.start() :]))
        evento = ev.group(1)
        if evento == "conectado":
            r.conexoes += 1
        elif evento == "desconectado":
            r.desconexoes += 1
            r.motivos_desconexao.append(campos.get("motivo", "?"))
        elif evento == "hello_repetido":
            r.hello_repetidos += 1
        elif evento == "resumo":
            r.hb += int(campos.get("hb", 0))
            r.falhas += int(campos.get("falhas", 0))
            r.lat_max_ms = max(r.lat_max_ms, float(campos.get("lat_max_ms", 0)))
        elif evento == "cartao":
            r.cartoes += 1
        elif evento == "rfid" and campos.get("estado") in ("perdido", "reiniciado", "ausente"):
            r.rfid_problemas += 1
        elif evento == "alerta_temperatura":
            r.alertas_temp += 1
    return r


def avaliar(r: Relatorio, horas_min: float = 48.0) -> list[str]:
    """Motivos de reprovação; lista vazia = aprovado."""
    motivos = []
    if r.horas < horas_min:
        motivos.append(f"duração de {r.horas:.1f} h, abaixo de {horas_min:.0f} h")
    if r.desconexoes:
        motivos.append(f"{r.desconexoes} desconexão(ões): {', '.join(r.motivos_desconexao[:5])}")
    if r.hello_repetidos:
        motivos.append(f"o Nano reiniciou ou ficou sem sinal {r.hello_repetidos} vez(es)")
    if r.falhas:
        motivos.append(f"{r.falhas} comando(s) sem resposta")
    if r.rfid_problemas:
        motivos.append(f"o RFID se perdeu ou reiniciou {r.rfid_problemas} vez(es)")
    if r.hb == 0:
        motivos.append("nenhuma batida registrada (o log tem as linhas evento=resumo?)")
    return motivos


def imprimir(r: Relatorio, motivos: list[str]) -> str:
    linhas = [
        "=== Relatório da bancada (T-BANC) ===",
        f"Período:        {r.inicio} a {r.fim} ({r.horas:.1f} h)",
        f"Conexões:       {r.conexoes}   desconexões: {r.desconexoes}",
        f"Batidas (HB):   {r.hb}   sem resposta: {r.falhas}",
        f"Maior latência: {r.lat_max_ms:.0f} ms",
        f"Nano reiniciou: {r.hello_repetidos}",
        f"Cartões lidos:  {r.cartoes}   problemas no RFID: {r.rfid_problemas}",
        f"Alertas de temperatura: {r.alertas_temp}",
        "",
        "APROVADO" if not motivos else "REPROVADO:",
    ]
    linhas += [f"  - {m}" for m in motivos]
    return "\n".join(linhas)
