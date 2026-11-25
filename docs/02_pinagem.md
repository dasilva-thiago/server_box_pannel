# 02 · Pinagem

**Revisão S1 (25/11/2026).** Cópia do `server_box/docs/04_interfaces_eletricas.md` §4a
(revisão E15), que é o documento mestre. No código: `firmware/include/pinos.h`.

Rótulos da tela lidos na foto do módulo (`server_box` registro R85):
**GND VCC SCL SDA RST DC CS BL**. Rótulos do RFID: os do módulo RC522 comum
(**SDA SCK MOSI MISO IRQ GND RST 3.3V**); confira no seu antes de ligar.

## Tabela

| Pino do Nano | Vai para | Divisor? | Observação |
|---|---|---|---|
| D13 (SCK) | tela **SCL** e RFID **SCK** | sim (1, dividido pelos dois) | barramento SPI |
| D11 (MOSI) | tela **SDA** e RFID **MOSI** | sim (1, dividido pelos dois) | barramento SPI |
| D12 (MISO) | RFID **MISO** | **não** | o Nano entende os 3,3 V do RFID |
| D10 | RFID **SDA** | sim | seleção do RFID |
| D9 | RFID **RST** | sim | |
| D8 | tela **DC** | sim | |
| D7 | tela **RST** | sim | |
| D6 | tela **CS** | sim | seleção da tela |
| D3 | tela **BL** | sim | brilho (PWM). Sem o fio, a luz fica sempre acesa |
| D5 | **LED+** do botão Power | não | PWM; T-LED antes (corrente) |
| D4 | buzzer **I/O** | não | buzzer de 5 V |
| 5V | regulador **VIN**, buzzer **VCC** | — | |
| GND | todos os GND | — | um GND comum para tudo |
| — | RFID **IRQ** | — | não ligar |

**Divisores:** 8 (D13, D11, D10, D9, D8, D7, D6, D3), cada um com 1 resistor de 470 Ω e
1 de 1 kΩ do kit: **16 resistores** (o kit tem 20 de cada valor).

## Um divisor

```
   pino do Nano (5 V)
         │
      [470 Ω]
         │
         ├──────────► pino da tela ou do RFID (≈ 3,4 V)
         │
      [1 kΩ]
         │
        GND
```

## Alimentação

```
 Nano 5V ──┬──► regulador AMS1117-3.3  VIN
           │                           VOUT (3,3 V) ──┬──► tela VCC
           │                                          └──► RFID 3.3V
           └──► buzzer VCC
 Nano GND ─────► regulador GND, tela GND, RFID GND, buzzer GND, LED−
```

Nunca use o pino **3V3 do Nano** para a tela ou o RFID: no Nano com CH340 ele não
aguenta (`server_box` HW-7 §7.2.1, registro R50).

A tela tem um regulador próprio na placa (U7, registro R53). Com 3,3 V na entrada, ele
entrega um pouco menos para o vidro, o que costuma funcionar. Se a imagem ficar fraca
ou falhar no T-TELA, anote: é um ponto para a bancada decidir.

## Barramento SPI dividido

```
             ┌───────────── divisor ──────┬──► tela SCL
 D13 SCK ────┘                            └──► RFID SCK
             ┌───────────── divisor ──────┬──► tela SDA
 D11 MOSI ───┘                            └──► RFID MOSI
 D12 MISO ◄──────────────────────────────────── RFID MISO   (direto)
 D6 ──── divisor ──► tela CS        D10 ──── divisor ──► RFID SDA
```

Só um chip fala por vez: o firmware escolhe pelo CS (tela) ou pelo SDA (RFID).

## Consumo (estimativa, a medir no T-BANC)

| Peça | mA (aprox.) |
|---|---|
| Nano | 20 |
| Tela com luz de fundo | 20 a 40 |
| RFID | 13 a 26 (pico < 30) |
| Buzzer tocando | ≈ 30 |
| LED do botão | ≤ 15 (T-LED) |
| **Total** | **≈ 100 a 140** |

Cabe com folga numa porta USB 2.0 (500 mA) dividida pelo hub.
