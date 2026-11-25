from conftest import estado

from eduserver_painel.protocolo import Cor
from eduserver_painel.telas import Limites, TelaStatus, cor_temp, cor_uso, duracao


def test_primeiro_desenho_manda_tudo_e_depois_so_o_que_mudou():
    tela = TelaStatus()
    e = estado()
    tudo = tela.pendentes(e)
    assert {k for k, _ in tudo} >= {"nome", "ip", "hora", "cpu", "cpu_barra", "temp", "rodape"}
    for chave, linha in tudo:
        tela.marcar(chave, linha)
    assert tela.pendentes(e) == []

    mudou = tela.pendentes(estado(cpu=80.0, hora="14:06"))
    assert {k for k, _ in mudou} == {"cpu", "cpu_barra", "hora"}


def test_sem_confirmacao_o_elemento_continua_pendente():
    tela = TelaStatus()
    e = estado()
    primeiro = tela.pendentes(e)
    tela.marcar(*primeiro[0])
    assert len(tela.pendentes(e)) == len(primeiro) - 1


def test_esquecer_redesenha_tudo():
    tela = TelaStatus()
    e = estado()
    for chave, linha in tela.pendentes(e):
        tela.marcar(chave, linha)
    tela.esquecer()
    assert len(tela.pendentes(e)) == len(tela.layout(e))


def test_rodape_do_cartao_substitui_o_tempo_no_ar():
    tela = TelaStatus()
    assert "no ar ha 3d 04h" in tela.layout(estado())["rodape"]
    assert "cartao 04A1B2C3" in tela.layout(estado(), "cartao 04A1B2C3")["rodape"]


def test_temperatura_ausente_no_windows():
    linha = TelaStatus().layout(estado(temp=None))["temp"]
    assert "--" in linha
    assert f"{Cor.CINZA:04X}" in linha


def test_cores():
    assert cor_uso(10) == Cor.VERDE
    assert cor_uso(75) == Cor.AMARELO
    assert cor_uso(95) == Cor.VERMELHO
    limites = Limites(60, 75)
    assert cor_temp(50, limites) == Cor.VERDE
    assert cor_temp(70, limites) == Cor.AMARELO
    assert cor_temp(80, limites) == Cor.VERMELHO


def test_duracao():
    assert duracao(59) == "0h 00min"
    assert duracao(3 * 3600 + 7 * 60) == "3h 07min"
    assert duracao(2 * 86400 + 5 * 3600) == "2d 05h"
