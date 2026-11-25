// Pinagem do painel frontal (Arduino Nano, ATmega328P, lógica de 5 V).
//
// Fonte: server_box/docs/04_interfaces_eletricas.md §4a (revisão E15). Este arquivo é
// uma cópia: mudou lá, muda aqui (e o docs/02_pinagem.md deste repositório).
//
// A tela (ST7789) e o RFID (MFRC522) trabalham em 3,3 V. Todo sinal que SAI do Nano
// para eles passa por um divisor 470 Ω + 1 kΩ (server_box/docs/06 HW-7 §7.2.1):
//
//   pino do Nano ──[ 470 Ω ]──┬──► pino da tela ou do RFID
//                             └──[ 1 kΩ ]── GND
//
// O MISO (RFID → Nano) vai direto. A tela e o RFID recebem 3,3 V de um regulador
// externo (AMS1117-3.3), nunca do pino 3V3 do Nano (CH340, registro R50).
#pragma once

#include <stdint.h>

// Barramento SPI: fixo no hardware do ATmega328P, dividido pela tela e pelo RFID.
//   D13 SCK  -> tela SCL e RFID SCK   (divisor)
//   D11 MOSI -> tela SDA e RFID MOSI  (divisor)
//   D12 MISO <- RFID MISO             (direto)

constexpr uint8_t PINO_RFID_SS = 10;   // RFID SDA (seleção do chip)   divisor
constexpr uint8_t PINO_RFID_RST = 9;   // RFID RST                      divisor
constexpr uint8_t PINO_TELA_DC = 8;    // tela DC (dado ou comando)     divisor
constexpr uint8_t PINO_TELA_RST = 7;   // tela RST                      divisor
constexpr uint8_t PINO_TELA_CS = 6;    // tela CS (seleção do chip)     divisor
constexpr uint8_t PINO_LED_BOTAO = 5;  // LED do botão Power, PWM (decisão 33). Direto
constexpr uint8_t PINO_BUZZER = 4;     // buzzer ativo de 5 V, nível alto = som. Direto
constexpr uint8_t PINO_TELA_BL = 3;    // tela BL (luz de fundo), PWM   divisor
