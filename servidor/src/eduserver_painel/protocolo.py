"""Protocolo serial do painel, lado do servidor (contrato em docs/01_protocolo.md).

Cada função devolve uma linha pronta para mandar, sem o '\\n'. Argumento fora do
limite levanta ValueError aqui, antes de chegar ao Nano.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

PROTO_VERSAO = 1
LINHA_MAX = 63  # caracteres, sem o '\n'
LARGURA = 240
ALTURA = 240
TAM_MAX = 4
BEEP_VEZES_MAX = 10
BEEP_MS_MAX = 2000


class Cor:
    """Cores em RGB565, o formato da tela."""

    PRETO = 0x0000
    BRANCO = 0xFFFF
    CINZA = 0x8410
    VERMELHO = 0xF800
    VERDE = 0x07E0
    AZUL = 0x001F
    CIANO = 0x07FF
    AMARELO = 0xFFE0
    LARANJA = 0xFD20


class Led:
    """Modos do LED do botão Power (decisão 33)."""

    APAGADO = 0
    ACESO = 1
    RESPIRA = 2
    PISCA = 3


def rgb565(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def ascii_seguro(texto: str) -> str:
    """A fonte do Nano só tem ASCII: tira os acentos e troca o resto por '?'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in sem_acento)


def letras_por_linha(tamanho: int) -> int:
    return LARGURA // (6 * tamanho)


def _faixa(nome: str, valor: int, minimo: int, maximo: int) -> int:
    if not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise ValueError(f"{nome} = {valor!r} fora de {minimo}..{maximo}")
    return valor


def _linha(texto: str) -> str:
    if len(texto) > LINHA_MAX:
        raise ValueError(f"linha com {len(texto)} caracteres (máximo {LINHA_MAX}): {texto!r}")
    return texto


def hb() -> str:
    return "HB"


def info() -> str:
    return "INFO"


def cls(cor: int) -> str:
    return _linha(f"CLS {_faixa('cor', cor, 0, 0xFFFF):04X}")


def txt(y: int, tamanho: int, cor: int, texto: str, alinhamento: str = "E") -> str:
    """Faixa de texto de lado a lado na altura y. Texto que não cabe é cortado."""
    _faixa("y", y, 0, ALTURA - 1)
    _faixa("tamanho", tamanho, 1, TAM_MAX)
    _faixa("cor", cor, 0, 0xFFFF)
    if alinhamento not in ("E", "C", "D"):
        raise ValueError(f"alinhamento {alinhamento!r} (use E, C ou D)")
    texto = ascii_seguro(texto)[: letras_por_linha(tamanho)]
    linha = f"TXT {y} {tamanho} {cor:04X} {alinhamento}"
    if texto:
        linha += " " + texto
    return _linha(linha)


def bar(y: int, altura: int, porcentagem: float, cor: int) -> str:
    _faixa("y", y, 0, ALTURA - 1)
    _faixa("altura", altura, 1, ALTURA)
    _faixa("cor", cor, 0, 0xFFFF)
    pct = max(0, min(100, round(porcentagem)))
    return _linha(f"BAR {y} {altura} {pct} {cor:04X}")


def beep(vezes: int, ligado_ms: int, desligado_ms: int = 0) -> str:
    _faixa("vezes", vezes, 0, BEEP_VEZES_MAX)
    _faixa("ligado_ms", ligado_ms, 0, BEEP_MS_MAX)
    _faixa("desligado_ms", desligado_ms, 0, BEEP_MS_MAX)
    return _linha(f"BEEP {vezes} {ligado_ms} {desligado_ms}")


def led(modo: int) -> str:
    return _linha(f"LED {_faixa('modo', modo, 0, 3)}")


def bl(brilho: int) -> str:
    return _linha(f"BL {_faixa('brilho', brilho, 0, 255)}")


# Mensagens do Nano para o servidor ------------------------------------------------

RESPOSTAS = frozenset({"OK", "ERR", "HB"})  # respondem a um comando
EVENTOS = frozenset({"HELLO", "CARD", "RFID"})  # chegam sozinhas


@dataclass(frozen=True)
class Mensagem:
    tipo: str  # HELLO, CARD, RFID, HB, OK, ERR, VAZIA ou "?" (desconhecida)
    texto: str = ""
    campos: dict[str, str] = field(default_factory=dict)


def interpretar(linha: str) -> Mensagem:
    linha = linha.strip()
    if not linha:
        return Mensagem("VAZIA")
    nome, _, resto = linha.partition(" ")
    resto = resto.strip()
    if nome == "HELLO":
        campos = dict(p.split("=", 1) for p in resto.split() if "=" in p)
        return Mensagem("HELLO", resto, campos)
    if nome in ("CARD", "RFID", "ERR"):
        return Mensagem(nome, resto)
    if nome in ("HB", "OK"):
        return Mensagem(nome)
    return Mensagem("?", linha)
