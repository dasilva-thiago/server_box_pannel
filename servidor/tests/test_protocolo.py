import pytest

from eduserver_painel import protocolo as p
from eduserver_painel.protocolo import Cor
from eduserver_painel.simulador import _Erro, interpretar_comando


def test_comandos_basicos():
    assert p.hb() == "HB"
    assert p.cls(Cor.VERMELHO) == "CLS F800"
    assert p.bar(120, 8, 61.4, Cor.VERDE) == "BAR 120 8 61 07E0"
    assert p.beep(3, 150, 150) == "BEEP 3 150 150"
    assert p.led(p.Led.RESPIRA) == "LED 2"
    assert p.bl(200) == "BL 200"


def test_txt_tira_acento_e_corta_no_tamanho():
    assert p.txt(30, 2, Cor.BRANCO, "Ação", "C") == "TXT 30 2 FFFF C Acao"
    longo = p.txt(0, 2, Cor.BRANCO, "x" * 50)
    assert longo.endswith(" " + "x" * 20)  # tamanho 2: 20 letras
    assert p.txt(0, 1, Cor.BRANCO, "") == "TXT 0 1 FFFF E"


def test_txt_troca_caractere_estranho():
    assert p.ascii_seguro("52°C\n") == "52C?"


def test_bar_limita_a_porcentagem():
    assert p.bar(0, 8, 130, 0).split()[3] == "100"
    assert p.bar(0, 8, -5, 0).split()[3] == "0"


@pytest.mark.parametrize(
    "chamada",
    [
        lambda: p.txt(240, 2, 0, "x"),
        lambda: p.txt(0, 5, 0, "x"),
        lambda: p.txt(0, 2, 0, "x", "X"),
        lambda: p.beep(11, 100, 100),
        lambda: p.led(4),
        lambda: p.bl(256),
        lambda: p.cls(0x10000),
    ],
)
def test_argumento_fora_do_limite(chamada):
    with pytest.raises(ValueError):
        chamada()


def test_toda_linha_do_servidor_e_aceita_pelo_firmware_simulado():
    """O que o servidor gera passa na mesma validação do firmware."""
    linhas = [
        p.hb(),
        p.info(),
        p.cls(Cor.PRETO),
        p.txt(239, 1, Cor.BRANCO, "y" * 99, "D"),
        p.txt(0, 4, Cor.AMARELO, "tam 4"),
        p.txt(0, 2, Cor.BRANCO, ""),
        p.bar(232, 8, 100, Cor.VERMELHO),
        p.beep(0, 0, 0),
        p.led(3),
        p.bl(0),
    ]
    for linha in linhas:
        assert len(linha) <= p.LINHA_MAX
        interpretar_comando(linha)


@pytest.mark.parametrize(
    "linha, motivo",
    [
        ("XYZ", "comando"),
        ("hb", "comando"),
        ("TXT  0 2 FFFF E x", "args"),
        ("TXT 0 2 FFFF", "args"),
        ("BAR 0 8 50 07E0 9", "args"),
        ("BL 99999", "args"),
    ],
)
def test_firmware_simulado_recusa_como_o_firmware(linha, motivo):
    with pytest.raises(_Erro, match=motivo):
        interpretar_comando(linha)


def test_interpretar_mensagens_do_nano():
    hello = p.interpretar("HELLO fw=0.1.0 proto=1 rfid=92\r\n")
    assert hello.tipo == "HELLO"
    assert hello.campos == {"fw": "0.1.0", "proto": "1", "rfid": "92"}
    assert p.interpretar("CARD 04A1B2C3").texto == "04A1B2C3"
    assert p.interpretar("ERR args").tipo == "ERR"
    assert p.interpretar("RFID perdido").texto == "perdido"
    assert p.interpretar("OK").tipo == "OK"
    assert p.interpretar("").tipo == "VAZIA"
    assert p.interpretar("lixo").tipo == "?"
