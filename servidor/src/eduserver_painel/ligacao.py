"""Ligação serial com o Nano: manda um comando e espera a resposta.

Um comando por vez (o Nano responde OK, ERR ou HB depois de executar): o buffer da
serial do Nano nunca enche enquanto a tela desenha. HELLO, CARD e RFID chegam
sozinhos e vão para a fila `eventos`.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
from typing import Protocol

from .protocolo import RESPOSTAS, Mensagem, interpretar

log = logging.getLogger(__name__)

# Fabricantes de chip USB-serial comuns em placas Arduino.
VIDS_CONHECIDOS = {
    0x1A86: "CH340",
    0x2341: "Arduino",
    0x2A03: "Arduino",
    0x0403: "FTDI",
}
LINK_UDEV = "/dev/eduserver-painel"  # criado pela regra deploy/99-eduserver-painel.rules


class Transporte(Protocol):
    """O que a ligação usa de uma porta serial (pyserial ou o Nano falso)."""

    @property
    def in_waiting(self) -> int: ...

    def read(self, n: int = 1) -> bytes: ...

    def write(self, dados: bytes) -> int | None: ...

    def close(self) -> None: ...


class LigacaoPerdida(Exception):
    """A porta caiu (cabo, USB, Nano desligado)."""


class SemResposta(Exception):
    """O Nano não respondeu a um comando dentro do prazo."""


def listar_portas() -> list[tuple[str, str]]:
    from serial.tools import list_ports

    portas = []
    for p in list_ports.comports():
        chip = VIDS_CONHECIDOS.get(p.vid or -1, "")
        portas.append((p.device, f"{chip} {p.description}".strip()))
    return portas


def encontrar_porta() -> str | None:
    """A porta do Nano: o link da regra udev ou a primeira com chip conhecido."""
    if os.path.exists(LINK_UDEV):
        return LINK_UDEV
    from serial.tools import list_ports

    candidatas = [p for p in list_ports.comports() if p.vid in VIDS_CONHECIDOS]
    if len(candidatas) > 1:
        log.warning(
            "evento=varias_portas portas=%s usando=%s",
            ",".join(p.device for p in candidatas),
            candidatas[0].device,
        )
    return candidatas[0].device if candidatas else None


def abrir_serial(porta: str, baud: int) -> Transporte:
    import serial

    # Abrir a porta reinicia o Nano (sinal DTR): o HELLO chega ~2 s depois.
    return serial.Serial(porta, baud, timeout=0.2, write_timeout=1.0)


class Ligacao:
    def __init__(self, transporte: Transporte, prazo_resposta_s: float = 1.0):
        self._t = transporte
        self._prazo = prazo_resposta_s
        self._respostas: queue.Queue[Mensagem] = queue.Queue()
        self.eventos: queue.Queue[Mensagem] = queue.Queue()
        self._viva = True
        self._trava_envio = threading.Lock()
        self._leitor = threading.Thread(target=self._ler, name="leitor-serial", daemon=True)
        self._leitor.start()

    @property
    def viva(self) -> bool:
        return self._viva

    def _ler(self) -> None:
        pendente = bytearray()
        while self._viva:
            try:
                dados = self._t.read(1)
                if dados and self._t.in_waiting:
                    dados += self._t.read(self._t.in_waiting)
            except Exception as erro:  # pyserial levanta tipos diferentes por sistema
                if self._viva:
                    self._viva = False
                    self.eventos.put(Mensagem("PERDIDA", str(erro)))
                return
            if not dados:
                continue
            pendente += dados
            while b"\n" in pendente:
                bruta, _, resto = bytes(pendente).partition(b"\n")
                pendente = bytearray(resto)
                linha = bruta.decode("ascii", errors="replace").strip()
                log.debug("<- %s", linha)
                msg = interpretar(linha)
                if msg.tipo in RESPOSTAS:
                    self._respostas.put(msg)
                elif msg.tipo != "VAZIA":
                    self.eventos.put(msg)

    def enviar(self, linha: str, esperar: bool = True) -> Mensagem | None:
        """Manda uma linha. Com esperar, devolve a resposta (OK, ERR ou HB)."""
        with self._trava_envio:
            if not self._viva:
                raise LigacaoPerdida("porta fechada")
            while not self._respostas.empty():  # resposta atrasada de um comando antigo
                self._respostas.get_nowait()
            log.debug("-> %s", linha)
            try:
                self._t.write((linha + "\n").encode("ascii"))
            except Exception as erro:
                self._viva = False
                raise LigacaoPerdida(str(erro)) from erro
            if not esperar:
                return None
            try:
                resposta = self._respostas.get(timeout=self._prazo)
            except queue.Empty:
                raise SemResposta(linha) from None
            if resposta.tipo == "ERR":
                log.warning("evento=erro_nano comando=%r motivo=%s", linha, resposta.texto)
            return resposta

    def fechar(self) -> None:
        self._viva = False
        try:
            self._t.close()
        except Exception:
            pass
        self._leitor.join(timeout=1.0)
