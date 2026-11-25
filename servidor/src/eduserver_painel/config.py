"""Configuração (TOML). Exemplo comentado em servidor/deploy/config.exemplo.toml."""

from __future__ import annotations

import sys
from dataclasses import dataclass, fields
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # Lubuntu 22.04 vem com o Python 3.10
    import tomli as tomllib


def _disco_padrao() -> str:
    return "C:\\" if sys.platform == "win32" else "/"


@dataclass
class Config:
    # [serial]
    porta: str = "auto"
    baud: int = 115200
    # [painel]
    intervalo_s: float = 2.0
    brilho: int = 200
    disco: str = ""
    reconectar_s: float = 3.0
    # [alertas]
    temp_aviso: float = 60.0
    temp_alerta: float = 75.0
    bipe_intervalo_s: float = 60.0
    # [log]
    log_arquivo: str = ""
    log_nivel: str = "INFO"

    def __post_init__(self) -> None:
        if not self.disco:
            self.disco = _disco_padrao()


# Seção do TOML → {chave do TOML: campo da Config}
_SECOES = {
    "serial": {"porta": "porta", "baud": "baud"},
    "painel": {
        "intervalo_s": "intervalo_s",
        "brilho": "brilho",
        "disco": "disco",
        "reconectar_s": "reconectar_s",
    },
    "alertas": {
        "temp_aviso": "temp_aviso",
        "temp_alerta": "temp_alerta",
        "bipe_intervalo_s": "bipe_intervalo_s",
    },
    "log": {"arquivo": "log_arquivo", "nivel": "log_nivel"},
}


def carregar(caminho: str | Path | None) -> Config:
    cfg = Config()
    if caminho is None:
        return cfg
    with open(caminho, "rb") as f:
        dados = tomllib.load(f)
    tipos = {f.name: f.type for f in fields(Config)}
    for secao, valores in dados.items():
        if secao not in _SECOES:
            raise ValueError(f"seção desconhecida [{secao}] em {caminho}")
        for chave, valor in valores.items():
            campo = _SECOES[secao].get(chave)
            if campo is None:
                raise ValueError(f"chave desconhecida {chave!r} em [{secao}] de {caminho}")
            if tipos[campo] == "float" and isinstance(valor, int):
                valor = float(valor)
            setattr(cfg, campo, valor)
    if not cfg.disco:
        cfg.disco = _disco_padrao()
    return cfg
