"""O serviço do painel: conecta no Nano, desenha o status, trata cartões e alertas.

As linhas de log com "evento=" alimentam o relatório da bancada (relatorio.py).
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable

from . import protocolo as p
from .coletores import Estado, coletar
from .config import Config
from .ligacao import Ligacao, LigacaoPerdida, SemResposta, Transporte
from .protocolo import Led, Mensagem
from .telas import Limites, TelaStatus, tela_desligando

log = logging.getLogger(__name__)

# Padrões de bipe (vezes, ms ligado, ms desligado). Os mesmos do teste t_buzzer.
BIPE_CARTAO = (1, 80, 0)
BIPE_ALERTA = (3, 150, 150)

FALHAS_SEGUIDAS_MAX = 3  # comandos sem resposta seguidos antes de reconectar
RODAPE_CARTAO_S = 5.0
RESUMO_S = 600.0  # de quanto em quanto tempo o log ganha um resumo das batidas
ESPERA_HELLO_S = 4.0


class NanoNaoRespondeu(Exception):
    """A porta abriu, mas nenhum HELLO chegou."""


class Painel:
    def __init__(
        self,
        cfg: Config,
        abrir: Callable[[], Transporte],
        coletor: Callable[[], Estado] | None = None,
        relogio: Callable[[], float] = time.monotonic,
    ):
        self.cfg = cfg
        self._abrir = abrir
        self._coletor = coletor or (lambda: coletar(cfg.disco))
        self._relogio = relogio
        self.tela = TelaStatus(Limites(cfg.temp_aviso, cfg.temp_alerta))
        self.lig: Ligacao | None = None
        self.fw: dict[str, str] = {}
        self._helos = 0
        self._falhas_seguidas = 0
        self._rodape: tuple[str, float] | None = None
        self._ultimo_alerta = -1e9
        self._zerar_resumo()

    # Conexão ---------------------------------------------------------------------

    def conectar(self) -> None:
        self.lig = Ligacao(self._abrir())
        self._helos = 0
        self._falhas_seguidas = 0
        log.info("evento=conectado")
        hello = self._esperar_hello()
        self._ao_hello(hello)

    def _esperar_hello(self) -> Mensagem:
        assert self.lig is not None
        for tentativa in range(2):
            limite = self._relogio() + (ESPERA_HELLO_S if tentativa == 0 else 2.0)
            while (resta := limite - self._relogio()) > 0:
                try:
                    msg = self.lig.eventos.get(timeout=min(resta, 0.5))
                except queue.Empty:
                    continue
                if msg.tipo == "HELLO":
                    return msg
                if msg.tipo == "PERDIDA":
                    raise LigacaoPerdida(msg.texto)
            # Alguns adaptadores não reiniciam o Nano ao abrir a porta: pergunta.
            self.lig.enviar(p.info(), esperar=False)
        raise NanoNaoRespondeu("nenhum HELLO depois de abrir a porta")

    def _ao_hello(self, msg: Mensagem) -> None:
        """Primeiro HELLO, ou o Nano reiniciou ou voltou do "sem sinal": redesenha tudo."""
        self._helos += 1
        self.fw = msg.campos
        if self._helos == 1:
            log.info("evento=hello %s", msg.texto)
        else:
            log.warning("evento=hello_repetido %s", msg.texto)
        if msg.campos.get("proto") != str(p.PROTO_VERSAO):
            log.error(
                "evento=protocolo_diferente nano=%s servidor=%s",
                msg.campos.get("proto"),
                p.PROTO_VERSAO,
            )
        if msg.campos.get("rfid", "0").upper() in ("0", "FF"):
            log.warning("evento=rfid estado=ausente")
        self.tela.esquecer()
        self._comando(p.cls(TelaStatus.FUNDO))
        self._comando(p.bl(self.cfg.brilho))
        self._comando(p.led(Led.ACESO))

    def fechar(self) -> None:
        if self.lig is not None:
            self.lig.fechar()
            self.lig = None

    # Comandos ---------------------------------------------------------------------

    def _comando(self, linha: str) -> Mensagem | None:
        """Manda e conta as falhas. Três seguidas: a ligação é dada como perdida."""
        assert self.lig is not None
        try:
            resposta = self.lig.enviar(linha)
        except SemResposta:
            self._falhas_seguidas += 1
            self._resumo["falhas"] += 1
            log.warning("evento=sem_resposta comando=%r", linha)
            if self._falhas_seguidas >= FALHAS_SEGUIDAS_MAX:
                raise LigacaoPerdida(f"{FALHAS_SEGUIDAS_MAX} comandos sem resposta") from None
            return None
        self._falhas_seguidas = 0
        return resposta

    def ciclo(self) -> None:
        """Uma batida: HB, coleta e desenho do que mudou."""
        t0 = self._relogio()
        if self._comando(p.hb()) is not None:
            latencia = (self._relogio() - t0) * 1000
            self._resumo["hb"] += 1
            self._resumo["lat_max_ms"] = max(self._resumo["lat_max_ms"], latencia)

        estado = self._coletor()
        for chave, linha in self.tela.pendentes(estado, self._rodape_atual()):
            resposta = self._comando(linha)
            if resposta is not None and resposta.tipo == "OK":
                self.tela.marcar(chave, linha)

        self._alertas(estado)
        if self._relogio() - self._resumo_desde >= RESUMO_S:
            self.registrar_resumo()

    def _rodape_atual(self) -> str | None:
        if self._rodape and self._relogio() < self._rodape[1]:
            return self._rodape[0]
        self._rodape = None
        return None

    def _alertas(self, e: Estado) -> None:
        if e.temp is None or e.temp < self.cfg.temp_alerta:
            return
        if self._relogio() - self._ultimo_alerta < self.cfg.bipe_intervalo_s:
            return
        self._ultimo_alerta = self._relogio()
        log.warning("evento=alerta_temperatura temp=%.0f", e.temp)
        self._comando(p.beep(*BIPE_ALERTA))

    # Eventos do Nano --------------------------------------------------------------

    def tratar_eventos(self, espera_s: float) -> None:
        """Trata o que chegar do Nano por até espera_s segundos."""
        assert self.lig is not None
        limite = self._relogio() + espera_s
        while True:
            resta = limite - self._relogio()
            try:
                msg = self.lig.eventos.get(timeout=max(0.0, min(resta, 0.2)))
            except queue.Empty:
                if resta <= 0:
                    return
                continue
            self.tratar(msg)

    def tratar(self, msg: Mensagem) -> None:
        if msg.tipo == "HELLO":
            self._ao_hello(msg)
        elif msg.tipo == "CARD":
            # Por enquanto o cartão só é mostrado e registrado; as ações vêm depois.
            log.info("evento=cartao uid=%s", msg.texto)
            self._rodape = (f"cartao {msg.texto}", self._relogio() + RODAPE_CARTAO_S)
            self._comando(p.beep(*BIPE_CARTAO))
        elif msg.tipo == "RFID":
            nivel = logging.INFO if msg.texto == "ok" else logging.WARNING
            log.log(nivel, "evento=rfid estado=%s", msg.texto)
        elif msg.tipo == "PERDIDA":
            raise LigacaoPerdida(msg.texto)
        else:
            log.debug("mensagem desconhecida: %s", msg.texto)

    # Laço principal ---------------------------------------------------------------

    def despedida(self) -> None:
        """Serviço parando (desligamento do servidor ou Ctrl+C): avisa na tela."""
        if self.lig is None or not self.lig.viva:
            return
        try:
            for linha in tela_desligando():
                self.lig.enviar(linha)
            self.lig.enviar(p.led(Led.RESPIRA))
        except (LigacaoPerdida, SemResposta):
            pass

    def rodar(self, parar: threading.Event) -> None:
        while not parar.is_set():
            try:
                self.conectar()
                proximo = self._relogio()
                while not parar.is_set():
                    if self._relogio() >= proximo:
                        self.ciclo()
                        proximo = self._relogio() + self.cfg.intervalo_s
                    self.tratar_eventos(min(0.2, max(0.0, proximo - self._relogio())))
                self.despedida()
            except (LigacaoPerdida, NanoNaoRespondeu, OSError) as erro:
                log.warning("evento=desconectado motivo=%s", str(erro).replace(" ", "_"))
            except Exception as erro:
                # serial.SerialException e afins; um erro de programa também cai aqui,
                # com o traceback no log, para o serviço não morrer.
                log.exception(
                    "evento=desconectado motivo=%s:%s",
                    type(erro).__name__,
                    str(erro).replace(" ", "_"),
                )
            finally:
                self.fechar()
            parar.wait(self.cfg.reconectar_s)
        self.registrar_resumo()
        log.info("evento=parado")

    # Resumo para o relatório da bancada -----------------------------------------

    def _zerar_resumo(self) -> None:
        self._resumo = {"hb": 0, "falhas": 0, "lat_max_ms": 0.0}
        self._resumo_desde = self._relogio()

    def registrar_resumo(self) -> None:
        r = self._resumo
        log.info(
            "evento=resumo hb=%d falhas=%d lat_max_ms=%.0f",
            r["hb"],
            r["falhas"],
            r["lat_max_ms"],
        )
        self._zerar_resumo()
