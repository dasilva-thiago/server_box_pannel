from __future__ import annotations

import pytest

from eduserver_painel.coletores import Estado
from eduserver_painel.config import Config
from eduserver_painel.painel import Painel
from eduserver_painel.simulador import NanoFalso


def estado(**mudancas) -> Estado:
    base = dict(
        nome="eduserver",
        ip="192.168.0.10",
        hora="14:05",
        cpu=23.0,
        ram=45.0,
        disco=61.0,
        temp=52.0,
        no_ar_s=3 * 86400 + 4 * 3600,
    )
    base.update(mudancas)
    return Estado(**base)


class Cenario:
    """Painel ligado a um Nano falso, com o estado do servidor controlado pelo teste."""

    def __init__(self, desenhar: bool = False):
        self.nano = NanoFalso(desenhar=desenhar)
        self.estado = estado()
        self.cfg = Config(intervalo_s=0.05, reconectar_s=0.01)
        self.painel = Painel(self.cfg, lambda: self.nano, coletor=lambda: self.estado)

    def enviadas_desde(self, n: int) -> list[str]:
        return self.nano.recebidas[n:]


@pytest.fixture
def cenario():
    c = Cenario()
    yield c
    c.painel.fechar()
