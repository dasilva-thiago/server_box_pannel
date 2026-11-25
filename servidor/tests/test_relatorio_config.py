import pytest

from eduserver_painel.config import carregar
from eduserver_painel.relatorio import analisar, avaliar

LOG_BOM = """\
2026-11-25 08:00:00 INFO evento=inicio versao=0.1.0
2026-11-25 08:00:01 INFO evento=conectado
2026-11-25 08:00:03 INFO evento=hello fw=0.1.0 proto=1 rfid=92
2026-11-25 08:10:03 INFO evento=resumo hb=300 falhas=0 lat_max_ms=21
2026-11-26 10:00:00 INFO evento=cartao uid=04A1B2C3
2026-11-27 08:10:03 INFO evento=resumo hb=300 falhas=0 lat_max_ms=35
"""


def test_bancada_aprovada():
    r = analisar(LOG_BOM.splitlines())
    assert r.horas == pytest.approx(48 + 10 / 60 + 3 / 3600, abs=0.01)
    assert r.hb == 600
    assert r.lat_max_ms == 35
    assert r.cartoes == 1
    assert avaliar(r) == []


def test_bancada_reprovada_por_desconexao_e_reinicio():
    log = LOG_BOM + (
        "2026-11-26 03:00:00 WARNING evento=desconectado motivo=porta_fechada\n"
        "2026-11-26 03:00:05 WARNING evento=hello_repetido fw=0.1.0 proto=1 rfid=92\n"
        "2026-11-26 04:00:00 WARNING evento=rfid estado=perdido\n"
    )
    motivos = avaliar(analisar(log.splitlines()))
    assert len(motivos) == 3
    assert "porta_fechada" in motivos[0]


def test_saida_do_journalctl():
    linha = (
        "2026-11-25T08:10:03-0300 eduserver eduserver-painel[812]: "
        "2026-11-25 08:10:03 INFO evento=resumo hb=300 falhas=1 lat_max_ms=40"
    )
    r = analisar([linha])
    assert r.falhas == 1
    assert r.inicio is not None


def test_config_do_toml(tmp_path):
    arq = tmp_path / "c.toml"
    arq.write_text(
        '[serial]\nporta = "COM5"\n[painel]\nintervalo_s = 3\n[alertas]\ntemp_alerta = 80\n',
        encoding="utf-8",
    )
    cfg = carregar(arq)
    assert cfg.porta == "COM5"
    assert cfg.intervalo_s == 3.0
    assert cfg.temp_alerta == 80.0
    assert cfg.disco  # padrão do sistema


def test_config_recusa_chave_errada(tmp_path):
    arq = tmp_path / "c.toml"
    arq.write_text("[painel]\nintervalo = 3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="intervalo"):
        carregar(arq)


def test_config_de_exemplo_carrega():
    from pathlib import Path

    exemplo = Path(__file__).parent.parent / "deploy" / "config.exemplo.toml"
    cfg = carregar(exemplo)
    assert cfg.porta == "auto"
    assert cfg.intervalo_s == 2.0
