# 05 · Decisões do software do painel

**Revisão S1 (25/11/2026).** Registro próprio deste repositório. As decisões de
**hardware** (peças, pinagem mestre, portas da placa-mãe) continuam no `server_box`
(`docs/00_ESTADO_DO_PROJETO.md` §4 e `docs/06_decisoes_de_hardware.md`); aqui ficam as
decisões de **software**, numeradas **S-n**. Cada uma diz de onde veio, o que foi
decidido e o que muda. Decisão revista não é apagada: ganha a nota "revista em S-m".

| # | Data | Decisão | Origem |
|---|---|---|---|
| S-1 | 25/11/2026 | Repositório separado | `server_box` decisão 36 |
| S-2 | 25/11/2026 | O servidor decide, o Nano obedece | Proposta do Claude, aprovada |
| S-3 | 25/11/2026 | Protocolo de texto, um comando por vez | Proposta do Claude, aprovada |
| S-4 | 25/11/2026 | Firmware no PlatformIO, bibliotecas fixadas | Proposta do Claude, aprovada |
| S-5 | 25/11/2026 | Pinagem com CS e BL da tela, 8 divisores | Usuário confirmou; R85 |
| S-6 | 25/11/2026 | Watchdog só com o bootloader novo | Risco técnico |
| S-7 | 25/11/2026 | Sinal de vida: batida de 2 s, "sem sinal" em 6 s | `server_box` decisão 33 |
| S-8 | 25/11/2026 | Uma tela de status só | Revê a decisão 24 do `server_box` |
| S-9 | 25/11/2026 | Cartão na versão 1: mostrar, bipar e registrar | Usuário |
| S-10 | 25/11/2026 | Serviço em Python, systemd e udev, no Lubuntu | Usuário (Lubuntu) |
| S-11 | 25/11/2026 | Testar sem instalar outro sistema | Usuário |
| S-12 | 25/11/2026 | Critérios do T-BANC | `server_box` fase 1B |

---

## S-1 · Repositório separado

- **Contexto:** o `server_box` tem ≈ 2 GB de fotos e escaneamentos; o software precisa
  ser clonado no servidor e continua mudando depois que a caixa for impressa.
- **Decisão:** o software do painel fica em `server_box_pannel`. A pinagem mestre fica no
  `server_box/docs/04` §4a; aqui, cópias ([02_pinagem.md](02_pinagem.md) e
  `firmware/include/pinos.h`).
- **Consequência:** mudou a pinagem lá, muda aqui no mesmo dia. O plano B (caixa sem
  periféricos) não usa nada deste repositório.

## S-2 · O servidor decide, o Nano obedece

- **Contexto:** o Nano tem 32 KB de programa e 2 KB de RAM.
- **Decisão:** o firmware só desenha faixas de texto e barras, lê o cartão, bipa, acende o
  LED e mostra as telas próprias ("aguardando" e "sem sinal"). Toda a lógica (o que
  mostrar, quando alertar, o que fazer com o cartão) fica no serviço do servidor.
- **Consequência:** mudar uma tela não exige gravar o Nano. Trocar o Nano pelo RP2040
  (N2, `server_box` HW-7 §7.2) só muda o firmware.

## S-3 · Protocolo de texto, um comando por vez

- **Decisão:** linhas ASCII de até 63 caracteres a 115200 baud; todo comando tem resposta,
  e o servidor só manda o próximo depois dela. Versão 1, contrato em
  [01_protocolo.md](01_protocolo.md).
- **Por quê:** o buffer de recepção do Nano enche em ≈ 5 ms enquanto a tela desenha. Com
  um comando por vez (e o buffer aumentado para 128 bytes), nunca transborda.
- **Consequência:** mudou um comando, sobe `PROTO_VERSAO` nos dois lados e nos testes.

## S-4 · Firmware no PlatformIO, bibliotecas fixadas

- **Decisão:** PlatformIO com o framework Arduino; Adafruit GFX 1.12.1, Adafruit ST7789
  1.11.0 e MFRC522 1.4.12, com versão exata no `platformio.ini`.
- **Resultado (25/11):** painel completo com 55 % da flash e 34 % da RAM. O Nano cabe.
- **Consequência:** cada teste da bancada é um ambiente (`t_tela`, `t_rfid`, `t_buzzer`,
  `t_led`) e usa o mesmo código de módulo do painel.

## S-5 · Pinagem com CS e BL da tela, 8 divisores

- **Contexto:** os rótulos da tela, lidos na foto em resolução total (`server_box`
  registro R85), são GND VCC SCL SDA RST DC CS BL.
- **Decisão:** CS da tela no D6 e BL no D3 (PWM), além da pinagem confirmada pelo usuário.
  Oito sinais saem do Nano para peças de 3,3 V, cada um com um divisor 470 Ω + 1 kΩ.
- **Consequência:** 16 resistores (o kit tem 20 de cada valor). A mini protoboard de 170
  pontos precisa comportar isso (PER10, na fase 2 do `server_box`).

## S-6 · Watchdog só com o bootloader novo

- **Contexto:** no bootloader antigo dos clones do Nano, um reinício pelo watchdog deixa
  o Nano reiniciando sem parar.
- **Decisão:** dois ambientes: `painel` (Optiboot, com watchdog de 4 s) e `painel_antigo`
  (sem watchdog). O primeiro envio diz qual bootloader o Nano tem.

## S-7 · Sinal de vida: batida de 2 s, "sem sinal" em 6 s

- **Contexto:** decisão 33 do `server_box`: o LED do botão diz "o sistema está no ar".
- **Decisão:** o servidor manda `HB` a cada 2 s. Sem nenhuma linha por 6 s, o Nano mostra
  "SEM SINAL" e apaga o LED. Ao ligar, o LED respira até o servidor assumir; ao parar o
  serviço, a tela mostra "desligando" e o LED respira.

## S-8 · Uma tela de status só

- **Contexto:** a decisão 24 do `server_box` previa o visor trocando de tela sozinho
  (IP, temperatura, disco, hora).
- **Decisão:** tudo cabe numa tela de 240 × 240: nome, IP, hora, CPU, RAM, disco,
  temperatura e tempo no ar ([03_telas.md](03_telas.md)). O aviso urgente continua:
  temperatura em vermelho e 3 bipes.
- **Consequência:** a troca automática de telas fica para quando houver mais o que mostrar.

## S-9 · Cartão na versão 1: mostrar, bipar e registrar

- **Decisão do usuário:** primeiro fazer as funções básicas funcionarem; as ações do
  cartão e do RFID serão decididas depois, com mais cuidado.
- **Hoje:** o UID aparece no rodapé por 5 s, o buzzer dá um bipe e o log registra
  `evento=cartao`. Nenhuma ação.
- **Para a decisão futura:** cartão MIFARE se copia com facilidade (não é segurança);
  ação perigosa (desligar o servidor) fica desligada por padrão; registro de presença
  guarda dado pessoal de aluno (guardar o UID cifrado, não o puro).

## S-10 · Serviço em Python, systemd e udev, no Lubuntu

- **Contexto:** o servidor usa Lubuntu (22.04 traz o Python 3.10).
- **Decisão:** Python ≥ 3.10 com `pyserial` e `psutil`, configuração em TOML, serviço
  systemd com usuário próprio, regra udev com o nome fixo `/dev/eduserver-painel` e o
  ModemManager longe da porta. O instalador avisa do `brltty`, que toma o CH340 no Ubuntu.
- **Pendente:** trocar a regra udev pela posição física no hub, depois do T-BANC (o
  identificador do CH340 é igual em qualquer clone).

## S-11 · Testar sem instalar outro sistema

- **Decisão do usuário:** nada de outro sistema operacional nem máquina virtual no
  notebook ou no PC.
- **Como:** o serviço roda no Windows com o Nano na USB (é a bancada); o simulador faz o
  papel do Nano e gera a prévia da tela em PNG; o que é só do Linux roda no próprio
  Lubuntu; o CI roda os testes no Ubuntu e no Windows, com Python 3.10 e 3.12.

## S-12 · Critérios do T-BANC

- **Decisão:** pelo menos 48 h no servidor; nenhuma desconexão; nenhum reinício do Nano
  nem "sem sinal"; nenhum comando sem resposta; o RFID sem se perder; nenhum reinício de
  USB no log do kernel. O relatório (`eduserver-painel relatorio`) confere os quatro
  primeiros. Roteiro em [04_bancada.md](04_bancada.md).
