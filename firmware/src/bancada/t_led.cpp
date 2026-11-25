// T-LED, passo 2: o LED do botão Power acende pelo D5 nos quatro modos?
// Usa o mesmo código do painel (src/led.cpp).
//
// ANTES, o passo 1 (server_box/docs/06 HW-7 §7.3a): medir a corrente do LED com o
// multímetro em mA, em série, ligado no 5V do Nano. Acima de 15 mA, ponha um resistor
// do kit (220 ou 470 Ω) em série com o LED antes de ligar no D5.
//
// Gravar: pio run -e t_led -t upload     Ver: pio device monitor
// Ligação: LED+ do botão no D5, LED− no GND. A chave do botão NÃO entra aqui.

#include <Arduino.h>

#include "../led.h"
#include "config.h"

namespace {

struct Etapa {
  led::Modo modo;
  const char* nome;
  unsigned long duracao_ms;
};

const Etapa ETAPAS[] = {
    {led::Modo::ACESO, "aceso (sistema no ar)", 4000},
    {led::Modo::APAGADO, "apagado (sem sinal)", 2000},
    {led::Modo::RESPIRA, "respirando (ligando ou desligando)", 9000},
    {led::Modo::PISCA, "piscando", 4000},
};

uint8_t atual = 0;
unsigned long marca = 0;

void comecar(uint8_t i) {
  atual = i;
  marca = millis();
  Serial.println(ETAPAS[i].nome);
  led::modo(ETAPAS[i].modo);
}

}  // namespace

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.println(F("\n=== T-LED (passo 2) ==="));
  led::iniciar();
  comecar(0);
}

void loop() {
  led::atualizar();
  if (millis() - marca >= ETAPAS[atual].duracao_ms) {
    comecar((atual + 1) % (sizeof(ETAPAS) / sizeof(ETAPAS[0])));
  }
}
