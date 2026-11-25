# 04 · Bancada (fase 1B do server_box)

**Revisão S1 (25/11/2026).** Um módulo por vez, na protoboard grande. Só passe para o
próximo quando o anterior funcionar. A ligação de cada fio está no
[02_pinagem.md](02_pinagem.md).

## 0. Preparar (uma vez, no notebook)

1. **Driver do CH340:** ligue o Nano na USB. No Gerenciador de Dispositivos, em
   "Portas (COM e LPT)", deve aparecer "USB-SERIAL CH340 (COMx)". Se aparecer com um
   ponto de exclamação, instale o driver CH341SER do site do fabricante (WCH).
2. **Gravar programas:** no VS Code, instale a extensão **PlatformIO IDE** e abra a
   pasta `firmware/`. Ou, sem a extensão, pela linha de comando:
   `uvx --from platformio pio run -e <ambiente> -t upload` dentro de `firmware/`.
3. **Qual bootloader o seu Nano tem:** grave o `t_buzzer` (passo 1). Se der
   `not in sync` ou `programmer is not responding`, o bootloader é o antigo: troque a
   linha `board = nanoatmega328new` da seção `[placa]` do `platformio.ini` para
   `board = nanoatmega328` e, no passo 6, use `painel_antigo` em vez de `painel`.

## 1. T-BUZZER (o mais simples, sem divisor)

```
 buzzer VCC ── Nano 5V      buzzer GND ── Nano GND      buzzer I/O ── Nano D4
```

Grave `t_buzzer` e abra o monitor (`pio device monitor`). A cada 3 s, um padrão: 1 curto,
2 curtos, 3 curtos, 1 longo. **Passa:** os quatro tocam como o monitor diz.

## 2. T-LED (com o botão na mão)

- **Passo 1, antes de ligar no D5:** corrente do LED com o multímetro em mA, em série,
  ligado no 5V do Nano (`server_box` HW-7 §7.3a). Acima de 15 mA, um resistor de 220 ou
  470 Ω em série.
- **Passo 2:** LED+ no D5, LED− no GND. Grave `t_led`. **Passa:** aceso, apagado,
  respirando e piscando, como o monitor diz.
- **Passo 3 (depois, no servidor):** com a placa-mãe desligada, a porta USB do hub
  continua com 5 V? (o LED do hub acende?)

## 3. T-TELA

Monte o regulador e os divisores da tela (D13, D11, D8, D7, D6 e D3) como no
[02_pinagem.md](02_pinagem.md). Grave `t_tela`.

**Passa:** as cinco cores aparecem com o nome certo; o texto aparece nos 4 tamanhos;
o brilho sobe; o contador anda sem falhar por 10 min.

| Sintoma | O que mudar |
|---|---|
| Tela branca ou preta, sem nada | Fios do SPI, do DC, do CS e do RST; os 3,3 V no VCC |
| Cores negativas ou trocadas | `TELA_INVERSAO` em `include/config.h` |
| Imagem de lado ou de cabeça para baixo | `TELA_ROTACAO` (0 a 3) |
| Imagem com riscos ou falhas | Baixe `TELA_SPI_HZ` para 4000000 (os divisores deixam o sinal mais lento) |

## 4. T-RFID

Sem desmontar a tela, ligue o RFID (divisores em D10 e D9; SCK e MOSI pegam os mesmos
divisores da tela; MISO direto no D12). Grave `t_rfid`.

1. **Versão do chip:** o monitor mostra `0x91`, `0x92`, `0x88` ou `0x12` (funciona) ou
   `0x00`/`0xFF` (sem comunicação: confira os fios).
2. **Leitura:** encoste um cartão: aparece `Cartão: <UID>`.
3. **Presença (a medida do T-RFID):** segure o cartão parado e anote a porcentagem de
   cada posição, com o ganho normal e com o máximo (digite `+` e Enter):

| Posição do cartão | Ganho normal | Ganho máximo |
|---|---|---|
| Direto no leitor | | |
| Através de 2 mm de plástico | | |
| Através da tela (posição B, decisão 25) | | |

**Passa a posição B:** 100 % (ou perto) através da tela. Se não passar, o RFID vai ao
lado da tela; antes de desistir, a lâmina de ferrite (`server_box` 06 §8.3b).

## 5. Painel completo no Windows

Tudo ligado (tela, RFID, buzzer e LED). Grave `painel` (ou `painel_antigo`). A tela
mostra "aguardando o servidor" e o LED respira. Depois, no notebook:

```
cd servidor
uv run eduserver-painel portas                  # anote a COM do Nano
uv run eduserver-painel rodar --porta COM5
```

**Passa:** a tela de status aparece e o LED acende; um cartão bipa e aparece no
rodapé; ao fechar o programa (Ctrl+C), a tela mostra "desligando"; 6 s depois,
"SEM SINAL" e o LED apaga; rodando de novo, a tela volta.

## 6. T-BANC: 48 h no servidor

No Lubuntu, com o hub na porta escolhida no T-USBC:

```
git clone <este repositório> && cd server_box_pannel
sudo bash servidor/deploy/instalar.sh
journalctl -u eduserver-painel -f            # acompanhar
```

Depois de 48 h (ou mais):

```
journalctl -u eduserver-painel -o short-iso > bancada.log
/opt/eduserver-painel/venv/bin/eduserver-painel relatorio bancada.log
journalctl -k | grep -i -E "usb.*(disconnect|reset)"   # a USB reiniciou?
```

**Critérios (o relatório confere os quatro primeiros):**

1. pelo menos **48 h** de log;
2. **nenhuma desconexão** (`evento=desconectado`);
3. **nenhum reinício** do Nano nem "sem sinal" (`evento=hello_repetido`);
4. **nenhum comando sem resposta** e o RFID sem se perder;
5. **nenhum** `disconnect` ou `reset` de USB no log do kernel ligado ao hub ou ao Nano;
6. durante o teste, passe um cartão algumas vezes por dia: todos aparecem no relatório.
