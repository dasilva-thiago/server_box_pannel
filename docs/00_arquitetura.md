# 00 · Arquitetura

**Revisão S1 (25/11/2026).** Decisão 36 do `server_box`.

## Por que um repositório separado

- O `server_box` tem ≈ 2 GB de fotos e escaneamentos. O software precisa ser clonado
  no servidor, e esse peso não precisa ir junto.
- A caixa termina quando a impressão sair; o software continua mudando depois.
- O CI compila o firmware e roda os testes a cada commit, sem misturar com o CAD.
- O plano B (caixa sem periféricos) não usa nada daqui.

O `server_box` continua mandando nas decisões de hardware: a pinagem mestre fica no
`server_box/docs/04` §4a, e o [02_pinagem.md](02_pinagem.md) é uma cópia.

## Quem faz o quê

**O servidor decide; o Nano obedece.**

| Lado | Faz | Não faz |
|---|---|---|
| Nano (`firmware/`) | Desenha faixas de texto e barras; lê o cartão e avisa o UID; toca bipes; acende o LED; mostra "sem sinal" quando o servidor some; reinicia sozinho se travar (watchdog, só com o bootloader novo) | Decidir o que mostrar, guardar estado, interpretar o cartão |
| Servidor (`servidor/`) | Coleta o estado do sistema; monta as telas e manda só o que mudou; decide alertas e bipes; trata o cartão; reconecta; grava o log da bancada | Desenhar pixel por pixel |

**Por quê:**
- O Nano tem 2 KB de RAM. Lógica no servidor é lógica que cabe. O painel completo
  ocupa **55 % da flash e 34 % da RAM** (compilado em 25/11/2026).
- Mudar uma tela ou uma ação não exige gravar o Nano de novo.
- Se o Nano não der conta, trocar pelo RP2040 (N2, `server_box` HW-7 §7.2) só muda o
  firmware: o protocolo e o servidor ficam iguais.

## Estados do painel

```
liga o Nano ──► AGUARDANDO ──(1ª linha do servidor)──► COM SINAL ◄──┐
  LED respira    "aguardando o servidor"                 LED aceso    │ (linha do servidor:
                                                             │        │  Nano manda HELLO,
                                          6 s sem nenhuma linha       │  servidor redesenha)
                                                             ▼        │
                                                         SEM SINAL ───┘
                                                         LED apagado, "SEM SINAL"

serviço parando (desligamento) ──► "desligando", LED respira ──► 6 s depois: SEM SINAL
```

O LED aceso quer dizer "o sistema está no ar" (decisão 33), não "tem energia": a porta
USB pode continuar com 5 V com a placa desligada (UNKNOWN, T-LED passo 3).

## Escolhas de ferramenta

| Parte | Escolha | Motivo |
|---|---|---|
| Firmware | PlatformIO, framework Arduino | Versões das bibliotecas fixadas no `platformio.ini`; dois ambientes para os dois bootloaders do Nano; testes no PC; CI |
| Bibliotecas | Adafruit ST7789 1.11.0 + GFX 1.12.1; MFRC522 1.4.12 | Comuns, testadas, cabem no Nano |
| Servidor | Python ≥ 3.10, `pyserial` e `psutil`; configuração em TOML | Roda no Lubuntu (22.04 traz o 3.10) e no Windows |
| Instalação | systemd + regra udev | Nome fixo para a porta; ModemManager longe dela |

## Testar sem instalar outro sistema

- O **serviço roda no Windows** do notebook, com o Nano na USB: é assim a bancada.
- Sem o Nano, o **simulador** (`eduserver-painel simular`) faz o papel dele e gera a
  prévia da tela em PNG.
- O que é só do Linux (systemd, udev, temperatura) é testado **no próprio servidor**
  (Lubuntu), que é o destino final, e o **CI** roda os testes no Ubuntu e no Windows.
  Nenhuma máquina virtual é necessária.

## Riscos tratados no código

| Risco | Tratamento |
|---|---|
| O buffer de recepção do Nano (64 bytes) enche enquanto a tela desenha | Um comando por vez: o servidor espera o OK; buffer aumentado para 128 |
| Abrir a porta reinicia o Nano | O servidor espera o HELLO (4 s) e, se não vier, pergunta com INFO |
| Watchdog no bootloader antigo deixa o Nano reiniciando sem parar | Watchdog só no ambiente `painel` (Optiboot) |
| Tela e RFID dividem o SPI | Cada um com seu CS; os dois desligados do barramento antes do `SPI.begin()` |
| RFID que para depois de horas | Conferência a cada 30 s; reinício automático; aviso `RFID reiniciado` |
| ModemManager e brltty mexem no CH340 no Ubuntu | Regra udev ignora a porta no ModemManager; o instalador avisa do brltty |
| CH340 tem identificador genérico | Link `/dev/eduserver-painel`; depois do T-BANC, trocar pela posição no hub |
| Cartão MIFARE se copia | Nenhuma ação perigosa por cartão nesta versão |
