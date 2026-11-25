# eduServer Box: painel frontal

Software do painel frontal do **eduServer Box** (plano A): a tela de 1,54", o leitor
RFID, o buzzer e o LED do botão Power, ligados a um Arduino Nano que conversa com o
servidor pela USB.

O projeto da caixa (medidas, CAD, decisões de hardware) fica em outro repositório,
`server_box`. Este aqui só tem o software.

```
SERVIDOR (Lubuntu)                                 NANO (firmware/)
eduserver-painel (servidor/)                       só obedece e avisa
 ├─ coleta: nome, IP, hora, CPU, RAM, disco, temp  ├─ desenha o que mudou na tela
 ├─ decide o que aparece e quando bipar ◄─ USB ──► ├─ avisa o UID do cartão lido
 ├─ manda uma batida (HB) a cada 2 s   (serial)    ├─ toca o bipe pedido
 └─ reconecta sozinho se o Nano cair               ├─ acende o LED do botão
                                                   └─ 6 s sem batida: "SEM SINAL", LED apaga
```

## Pastas

| Pasta | O quê |
|---|---|
| `firmware/` | Programa do Nano (PlatformIO): o painel e os testes da bancada (`src/bancada/`) |
| `servidor/` | Serviço em Python: roda no Lubuntu (systemd) e no Windows (para a bancada) |
| `docs/` | Arquitetura, protocolo, pinagem, telas e o roteiro da bancada |

## Começo rápido

**Gravar o Nano** (VS Code com a extensão PlatformIO, ou pela linha de comando):

```
cd firmware
uvx --from platformio pio run -e t_buzzer -t upload     # um teste da bancada
uvx --from platformio pio device monitor                 # ver o que ele diz
uvx --from platformio pio run -e painel -t upload        # o programa do painel
```

**Rodar o serviço no Windows**, com o Nano na USB (sem instalar outro sistema):

```
cd servidor
uv run eduserver-painel portas                  # descobre a COM do Nano
uv run eduserver-painel rodar --porta COM5
uv run eduserver-painel simular tela.png        # prévia da tela, sem o Nano
```

**Instalar no servidor (Lubuntu):** `sudo bash servidor/deploy/instalar.sh`.

O passo a passo completo, um módulo por vez, está em
[docs/04_bancada.md](docs/04_bancada.md).

## Documentos

- [00 Arquitetura](docs/00_arquitetura.md): por que é assim, e o que fica em cada lado
- [01 Protocolo](docs/01_protocolo.md): o contrato entre o servidor e o Nano
- [02 Pinagem](docs/02_pinagem.md): ligação de cada fio, com os divisores de tensão
- [03 Telas](docs/03_telas.md): o que aparece na tela, e onde
- [04 Bancada](docs/04_bancada.md): testes módulo a módulo e o T-BANC de 48 h
