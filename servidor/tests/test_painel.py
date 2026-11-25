import threading

import pytest
from conftest import Cenario, estado

from eduserver_painel.ligacao import LigacaoPerdida
from eduserver_painel.protocolo import Led


def test_conectar_limpa_a_tela_e_acende_o_led(cenario):
    cenario.painel.conectar()
    assert cenario.nano.recebidas[:3] == ["CLS 0000", "BL 200", "LED 1"]
    assert cenario.nano.led == Led.ACESO
    assert cenario.painel.fw["proto"] == "1"


def test_ciclo_desenha_tudo_e_depois_so_a_batida(cenario):
    cenario.painel.conectar()
    n = len(cenario.nano.recebidas)
    cenario.painel.ciclo()
    primeiro = cenario.enviadas_desde(n)
    assert primeiro[0] == "HB"
    assert any(linha.startswith("TXT 60 4") and linha.endswith("14:05") for linha in primeiro)

    n = len(cenario.nano.recebidas)
    cenario.painel.ciclo()
    assert cenario.enviadas_desde(n) == ["HB"]

    cenario.estado = estado(cpu=90.0)
    n = len(cenario.nano.recebidas)
    cenario.painel.ciclo()
    assert [linha.split()[0] for linha in cenario.enviadas_desde(n)] == ["HB", "TXT", "BAR"]


def test_cartao_bipa_e_aparece_no_rodape(cenario):
    cenario.painel.conectar()
    cenario.painel.ciclo()
    cenario.nano.aproximar_cartao("04A1B2C3")
    cenario.painel.tratar_eventos(0.3)
    assert cenario.nano.bipes == [(1, 80, 0)]
    n = len(cenario.nano.recebidas)
    cenario.painel.ciclo()
    assert any("cartao 04A1B2C3" in linha for linha in cenario.enviadas_desde(n))


def test_nano_reiniciado_redesenha_tudo(cenario):
    cenario.painel.conectar()
    cenario.painel.ciclo()
    cenario.nano.reiniciar()  # HELLO de novo
    n = len(cenario.nano.recebidas)
    cenario.painel.tratar_eventos(0.3)
    cenario.painel.ciclo()
    depois = cenario.enviadas_desde(n)
    assert depois[0] == "CLS 0000"
    assert sum(1 for linha in depois if linha.startswith("TXT")) >= 7


def test_nano_mudo_derruba_a_ligacao_depois_de_tres_falhas(cenario):
    cenario.painel.conectar()
    cenario.painel.lig._prazo = 0.05
    cenario.nano.mudo = True
    with pytest.raises(LigacaoPerdida):
        cenario.painel.ciclo()


def test_alerta_de_temperatura_bipa_uma_vez_por_intervalo(cenario):
    cenario.estado = estado(temp=80.0)
    cenario.painel.conectar()
    cenario.painel.ciclo()
    cenario.painel.ciclo()
    assert cenario.nano.bipes == [(3, 150, 150)]


def test_despedida_mostra_desligando_e_o_led_respira(cenario):
    cenario.painel.conectar()
    cenario.painel.despedida()
    assert any("desligando" in linha for linha in cenario.nano.recebidas)
    assert cenario.nano.led == Led.RESPIRA


def test_rodar_para_com_o_sinal_e_se_despede():
    c = Cenario()
    parar = threading.Event()
    t = threading.Thread(target=c.painel.rodar, args=(parar,))
    t.start()
    threading.Event().wait(0.3)
    parar.set()
    t.join(timeout=3)
    assert not t.is_alive()
    assert c.nano.led == Led.RESPIRA
    assert c.nano.recebidas.count("HB") >= 2


def test_previa_em_png(tmp_path):
    pytest.importorskip("PIL")
    c = Cenario(desenhar=True)
    c.painel.conectar()
    c.painel.ciclo()
    destino = tmp_path / "tela.png"
    c.nano.salvar_png(str(destino))
    c.painel.fechar()
    from PIL import Image

    img = Image.open(destino)
    assert img.size == (480, 480)
    assert img.getbbox() is not None  # desenhou alguma coisa
