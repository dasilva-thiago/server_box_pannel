// T-BUZZER: o buzzer toca os padrões que o painel usa?
// Usa o mesmo código do painel (src/buzzer.cpp).
//
// Gravar: pio run -e t_buzzer -t upload     Ver: pio device monitor
// Ligação: buzzer VCC no 5V, GND no GND, I/O no D4 (direto, sem divisor).

#include <Arduino.h>

#include "../buzzer.h"
#include "config.h"

namespace {

struct Padrao {
  const char* nome;
  uint8_t vezes;
  uint16_t ligado;
  uint16_t desligado;
};

// Os mesmos padrões do serviço do servidor (servidor/src/eduserver_painel/painel.py).
const Padrao PADROES[] = {
    {"cartao lido: 1 curto", 1, 80, 0},
    {"aviso: 2 curtos", 2, 100, 120},
    {"alerta: 3 curtos", 3, 150, 150},
    {"longo: 1 de 1 s", 1, 1000, 0},
};

uint8_t atual = 0;
unsigned long marca = 0;

}  // namespace

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.println(F("\n=== T-BUZZER ==="));
  Serial.println(F("Um padrão a cada 3 s. Sem som: confira 5V, GND e o I/O no D4."));
  buzzer::iniciar();
  marca = millis() - 3000;
}

void loop() {
  buzzer::atualizar();
  if (millis() - marca < 3000) return;
  marca = millis();
  const Padrao& p = PADROES[atual];
  Serial.println(p.nome);
  buzzer::tocar(p.vezes, p.ligado, p.desligado);
  atual = (atual + 1) % (sizeof(PADROES) / sizeof(PADROES[0]));
}
