"""Linha de comando: eduserver-painel {rodar, portas, simular, relatorio}."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time

from . import __version__
from .config import Config, carregar

log = logging.getLogger("eduserver_painel")


def _configurar_log(cfg: Config, verboso: bool) -> None:
    nivel = logging.DEBUG if verboso else getattr(logging, cfg.log_nivel.upper(), logging.INFO)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    tela = logging.StreamHandler()
    tela.setFormatter(formato)
    raiz.addHandler(tela)
    if cfg.log_arquivo:
        arquivo = logging.FileHandler(cfg.log_arquivo, encoding="utf-8")
        arquivo.setFormatter(formato)
        raiz.addHandler(arquivo)


def _cmd_rodar(args: argparse.Namespace) -> int:
    from .ligacao import abrir_serial, encontrar_porta
    from .painel import Painel

    cfg = carregar(args.config)
    if args.porta:
        cfg.porta = args.porta
    if args.log:
        cfg.log_arquivo = args.log
    _configurar_log(cfg, args.verboso)
    log.info("evento=inicio versao=%s", __version__)

    def abrir():
        porta = cfg.porta if cfg.porta != "auto" else encontrar_porta()
        if porta is None:
            raise OSError("nenhum Nano encontrado (veja: eduserver-painel portas)")
        log.info("evento=abrindo porta=%s", porta)
        return abrir_serial(porta, cfg.baud)

    parar = threading.Event()

    def ao_sinal(numero, _quadro):
        log.info("evento=sinal numero=%s", numero)
        parar.set()

    signal.signal(signal.SIGINT, ao_sinal)
    signal.signal(signal.SIGTERM, ao_sinal)
    Painel(cfg, abrir).rodar(parar)
    return 0


def _cmd_portas(_args: argparse.Namespace) -> int:
    from .ligacao import encontrar_porta, listar_portas

    portas = listar_portas()
    if not portas:
        print("Nenhuma porta serial. O Nano está ligado na USB? (o cabo passa dados?)")
        return 1
    escolhida = encontrar_porta()
    for device, descricao in portas:
        marca = "  <- seria usada no modo auto" if device == escolhida else ""
        print(f"{device:20} {descricao}{marca}")
    return 0


def _cmd_simular(args: argparse.Namespace) -> int:
    """Roda o serviço contra o Nano falso e salva a tela num PNG."""
    from .coletores import coletar
    from .painel import Painel
    from .simulador import NanoFalso

    cfg = carregar(args.config)
    _configurar_log(cfg, args.verboso)
    nano = NanoFalso()
    if nano.imagem is None:
        print("A prévia precisa do Pillow: pip install pillow (ou uv sync --extra sim).")
        return 1
    painel = Painel(cfg, lambda: nano)
    painel.conectar()
    # Primeira medida de CPU é sempre 0: espera um pouco e coleta de verdade.
    coletar(cfg.disco)
    time.sleep(0.5)
    painel.ciclo()
    if args.cartao:
        nano.aproximar_cartao(args.cartao)
        painel.tratar_eventos(0.3)
        painel.ciclo()
    nano.salvar_png(args.saida)
    painel.fechar()
    print(f"Prévia salva em {args.saida} (desenho aproximado; a fonte do Nano é outra).")
    return 0


def _cmd_relatorio(args: argparse.Namespace) -> int:
    from .relatorio import analisar, avaliar, imprimir

    with open(args.arquivo, encoding="utf-8", errors="replace") as f:
        r = analisar(f)
    motivos = avaliar(r, args.horas)
    print(imprimir(r, motivos))
    return 0 if not motivos else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="eduserver-painel", description=__doc__)
    ap.add_argument("--versao", action="version", version=__version__)
    sub = ap.add_subparsers(dest="comando", required=True)

    r = sub.add_parser("rodar", help="liga o painel (o serviço)")
    r.add_argument("--config", help="arquivo TOML (padrão: valores de fábrica)")
    r.add_argument("--porta", help="porta do Nano, ex.: COM5 ou /dev/ttyUSB0 (padrão: auto)")
    r.add_argument("--log", help="também grava o log neste arquivo (para o relatório)")
    r.add_argument("-v", "--verboso", action="store_true", help="mostra cada linha trocada")
    r.set_defaults(func=_cmd_rodar)

    s = sub.add_parser("portas", help="lista as portas seriais e qual seria usada")
    s.set_defaults(func=_cmd_portas)

    s = sub.add_parser("simular", help="prévia da tela num PNG, sem o Nano")
    s.add_argument("saida", nargs="?", default="tela.png")
    s.add_argument("--config")
    s.add_argument("--cartao", help="simula a leitura deste UID, ex.: 04A1B2C3")
    s.add_argument("-v", "--verboso", action="store_true")
    s.set_defaults(func=_cmd_simular)

    s = sub.add_parser("relatorio", help="relatório da bancada (T-BANC) a partir do log")
    s.add_argument("arquivo")
    s.add_argument("--horas", type=float, default=48.0, help="duração mínima (padrão 48)")
    s.set_defaults(func=_cmd_relatorio)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
