"""Desenho das telas (240 × 240). Layout em docs/03_telas.md.

A tela de status lembra o que já foi desenhado e só manda o que mudou: num ciclo
normal, só a CPU e o relógio mudam.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import protocolo as p
from .coletores import Estado
from .protocolo import Cor


@dataclass(frozen=True)
class Limites:
    temp_aviso: float = 60.0
    temp_alerta: float = 75.0


def cor_uso(pct: float) -> int:
    if pct < 70:
        return Cor.VERDE
    if pct < 90:
        return Cor.AMARELO
    return Cor.VERMELHO


def cor_temp(temp: float | None, limites: Limites) -> int:
    if temp is None:
        return Cor.CINZA
    if temp < limites.temp_aviso:
        return Cor.VERDE
    if temp < limites.temp_alerta:
        return Cor.AMARELO
    return Cor.VERMELHO


def duracao(segundos: float) -> str:
    s = int(segundos)
    dias, s = divmod(s, 86400)
    horas, s = divmod(s, 3600)
    minutos = s // 60
    if dias:
        return f"{dias}d {horas:02d}h"
    return f"{horas}h {minutos:02d}min"


class TelaStatus:
    FUNDO = Cor.PRETO

    def __init__(self, limites: Limites | None = None):
        self.limites = limites or Limites()
        self._desenhado: dict[str, str] = {}

    def esquecer(self) -> None:
        """A tela foi limpa (CLS, Nano reiniciado): tudo precisa ser desenhado de novo."""
        self._desenhado.clear()

    def layout(self, e: Estado, rodape: str | None = None) -> dict[str, str]:
        """Todos os elementos da tela, por nome."""
        d = {
            "nome": p.txt(6, 2, Cor.CIANO, e.nome, "C"),
            "ip": p.txt(32, 2, Cor.BRANCO, e.ip, "C"),
            "hora": p.txt(60, 4, Cor.BRANCO, e.hora, "C"),
        }
        y = 104
        for chave, rotulo, valor in (
            ("cpu", "CPU", e.cpu),
            ("ram", "RAM", e.ram),
            ("disco", "DISCO", e.disco),
        ):
            pct = round(valor)
            d[chave] = p.txt(y, 2, Cor.BRANCO, f" {rotulo:<6}{pct:>3} %", "E")
            d[chave + "_barra"] = p.bar(y + 18, 8, pct, cor_uso(pct))
            y += 32
        temp = "--" if e.temp is None else f"{e.temp:.0f}"
        d["temp"] = p.txt(200, 2, cor_temp(e.temp, self.limites), f" TEMP  {temp:>3} C", "E")
        d["rodape"] = p.txt(224, 1, Cor.CINZA, rodape or f"no ar ha {duracao(e.no_ar_s)}", "C")
        return d

    def pendentes(self, e: Estado, rodape: str | None = None) -> list[tuple[str, str]]:
        """O que mudou desde o último desenho confirmado."""
        return [
            (k, linha)
            for k, linha in self.layout(e, rodape).items()
            if self._desenhado.get(k) != linha
        ]

    def marcar(self, chave: str, linha: str) -> None:
        """O Nano confirmou (OK) este elemento."""
        self._desenhado[chave] = linha


def tela_desligando() -> list[str]:
    return [
        p.cls(Cor.PRETO),
        p.txt(96, 3, Cor.AMARELO, "desligando", "C"),
        p.txt(130, 2, Cor.BRANCO, "ate logo", "C"),
    ]
