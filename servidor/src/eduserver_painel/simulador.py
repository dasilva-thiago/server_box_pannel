"""Nano falso: responde ao protocolo como o firmware e desenha a tela num PNG.

Serve para os testes (sem hardware) e para ver as telas antes da bancada
(eduserver-painel simular tela.png). O desenho é APROXIMADO: a fonte do PC não é a
fonte 5 × 7 do Nano. As posições, as cores e o corte do texto seguem o firmware.
"""

from __future__ import annotations

import threading

from . import protocolo as p

# Mesma tabela do firmware (firmware/lib/protocolo/src/protocolo.cpp).
_SPECS = {
    "HB": "",
    "INFO": "",
    "CLS": "x",
    "TXT": "ddxc*",
    "BAR": "dddx",
    "BEEP": "ddd",
    "LED": "d",
    "BL": "d",
}
_CINZA_ESCURO = 0x2104
_MARGEM = 8


class _Erro(Exception):
    pass


def _converter(tipo: str, tok: str) -> int:
    if tipo == "d":
        if not tok.isdigit() or not tok.isascii() or len(tok) > 5 or int(tok) > 65535:
            raise _Erro("args")
        return int(tok)
    if tipo == "x":
        if not 1 <= len(tok) <= 4 or any(c not in "0123456789abcdefABCDEF" for c in tok):
            raise _Erro("args")
        return int(tok, 16)
    if tipo == "c":
        if len(tok) != 1:
            raise _Erro("args")
        return ord(tok)
    raise _Erro("args")


def interpretar_comando(linha: str) -> tuple[str, list[int], str | None]:
    """Interpreta como o firmware. Levanta _Erro('comando') ou _Erro('args')."""
    resto = linha.lstrip(" ")
    if not resto:
        raise _Erro("vazia")
    nome, _, resto = resto.partition(" ")
    spec = _SPECS.get(nome)
    if spec is None:
        raise _Erro("comando")
    nums: list[int] = []
    texto = None
    for a in spec:
        if a == "*":
            texto = resto
            break
        if not resto or resto[0] == " ":
            raise _Erro("args")
        tok, _, resto = resto.partition(" ")
        nums.append(_converter(a, tok))
    else:
        if resto:
            raise _Erro("args")
    _validar(nome, nums)
    return nome, nums, texto


def _validar(nome: str, n: list[int]) -> None:
    def dentro(v: int, a: int, b: int) -> bool:
        return a <= v <= b

    ok = True
    if nome == "TXT":
        ok = dentro(n[0], 0, p.ALTURA - 1) and dentro(n[1], 1, p.TAM_MAX) and chr(n[3]) in "ECD"
    elif nome == "BAR":
        ok = dentro(n[0], 0, p.ALTURA - 1) and dentro(n[1], 1, p.ALTURA) and dentro(n[2], 0, 100)
    elif nome == "BEEP":
        ok = (
            dentro(n[0], 0, p.BEEP_VEZES_MAX)
            and dentro(n[1], 0, p.BEEP_MS_MAX)
            and dentro(n[2], 0, p.BEEP_MS_MAX)
        )
    elif nome == "LED":
        ok = dentro(n[0], 0, 3)
    elif nome == "BL":
        ok = dentro(n[0], 0, 255)
    if not ok:
        raise _Erro("args")


def rgb888(cor: int) -> tuple[int, int, int]:
    r = (cor >> 11) & 0x1F
    g = (cor >> 5) & 0x3F
    b = cor & 0x1F
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31)


class NanoFalso:
    """Faz o papel da porta serial (Transporte) com um Nano do outro lado."""

    def __init__(self, desenhar: bool = True, rfid: str = "92"):
        self._saida = bytearray()
        self._entrada = bytearray()
        self._cond = threading.Condition()
        self._fechado = False
        self._rfid = rfid
        self.mudo = False  # não responde nada (simula Nano travado)
        self.recebidas: list[str] = []
        self.led = p.Led.APAGADO
        self.brilho = 200
        self.bipes: list[tuple[int, int, int]] = []
        self._fundo = p.Cor.PRETO
        self.imagem = None
        if desenhar:
            try:
                from PIL import Image, ImageDraw

                self.imagem = Image.new("RGB", (p.LARGURA, p.ALTURA), (0, 0, 0))
                self._draw = ImageDraw.Draw(self.imagem)
            except ImportError:
                self.imagem = None
        self.reiniciar()

    # Interface de porta serial ------------------------------------------------

    @property
    def in_waiting(self) -> int:
        with self._cond:
            return len(self._saida)

    def read(self, n: int = 1) -> bytes:
        with self._cond:
            self._cond.wait_for(lambda: self._saida or self._fechado, timeout=0.2)
            dados = bytes(self._saida[:n])
            del self._saida[:n]
            return dados

    def write(self, dados: bytes) -> int:
        if self._fechado:
            raise OSError("porta fechada")
        self._entrada += dados
        while b"\n" in self._entrada:
            linha, _, resto = bytes(self._entrada).partition(b"\n")
            self._entrada = bytearray(resto)
            self._tratar(linha.decode("ascii").rstrip("\r"))
        return len(dados)

    def close(self) -> None:
        with self._cond:
            self._fechado = True
            self._cond.notify_all()

    # Ações do "mundo" -----------------------------------------------------------

    def reiniciar(self) -> None:
        """Como ligar o Nano: manda o HELLO."""
        self._responder(f"HELLO fw=sim proto={p.PROTO_VERSAO} rfid={self._rfid}")

    def aproximar_cartao(self, uid: str) -> None:
        self._responder(f"CARD {uid}")

    def salvar_png(self, caminho: str, escala: int = 2) -> None:
        if self.imagem is None:
            raise RuntimeError("instale o Pillow: pip install eduserver-painel[sim]")
        from PIL import Image

        img = self.imagem.resize((p.LARGURA * escala, p.ALTURA * escala), Image.NEAREST)
        img.save(caminho)

    # Firmware simulado ----------------------------------------------------------

    def _responder(self, linha: str) -> None:
        with self._cond:
            self._saida += (linha + "\n").encode("ascii")
            self._cond.notify_all()

    def _tratar(self, linha: str) -> None:
        self.recebidas.append(linha)
        if self.mudo:
            return
        if len(linha) > p.LINHA_MAX:
            self._responder("ERR linha_longa")
            return
        try:
            nome, n, texto = interpretar_comando(linha)
        except _Erro as erro:
            if str(erro) != "vazia":
                self._responder(f"ERR {erro}")
            return
        if nome == "HB":
            self._responder("HB")
            return
        if nome == "INFO":
            self.reiniciar()
            return
        if nome == "LED":
            self.led = n[0]
        elif nome == "BL":
            self.brilho = n[0]
        elif nome == "BEEP":
            self.bipes.append((n[0], n[1], n[2]))
        elif self.imagem is not None:
            self._desenhar(nome, n, texto or "")
        self._responder("OK")

    def _desenhar(self, nome: str, n: list[int], texto: str) -> None:
        d = self._draw
        if nome == "CLS":
            self._fundo = n[0]
            d.rectangle((0, 0, p.LARGURA - 1, p.ALTURA - 1), fill=rgb888(n[0]))
        elif nome == "TXT":
            y, tam, cor, al = n[0], n[1], n[2], chr(n[3])
            texto = texto[: p.letras_por_linha(tam)]
            w = len(texto) * 6 * tam
            x = (p.LARGURA - w) // 2 if al == "C" else (p.LARGURA - w if al == "D" else 0)
            d.rectangle((0, y, p.LARGURA - 1, y + 8 * tam - 1), fill=rgb888(self._fundo))
            fonte = _fonte(7 * tam)
            for i, ch in enumerate(texto):
                d.text((x + i * 6 * tam, y), ch, fill=rgb888(cor), font=fonte)
        elif nome == "BAR":
            y, h, pct, cor = n
            total = p.LARGURA - 2 * _MARGEM
            cheio = total * pct // 100
            d.rectangle((0, y, p.LARGURA - 1, y + h - 1), fill=rgb888(self._fundo))
            if cheio:
                d.rectangle((_MARGEM, y, _MARGEM + cheio - 1, y + h - 1), fill=rgb888(cor))
            if cheio < total:
                d.rectangle(
                    (_MARGEM + cheio, y, _MARGEM + total - 1, y + h - 1),
                    fill=rgb888(_CINZA_ESCURO),
                )


_FONTES: dict[int, object] = {}


def _fonte(tamanho: int):
    """Uma fonte monoespaçada do sistema, se houver; senão a do Pillow."""
    if tamanho not in _FONTES:
        from PIL import ImageFont

        for nome in ("consola.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"):
            try:
                _FONTES[tamanho] = ImageFont.truetype(nome, tamanho)
                break
            except OSError:
                continue
        else:
            _FONTES[tamanho] = ImageFont.load_default(size=tamanho)
    return _FONTES[tamanho]
