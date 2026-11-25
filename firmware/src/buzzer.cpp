#include "buzzer.h"

#include <Arduino.h>

#include "pinos.h"

namespace buzzer {

namespace {

uint8_t restantes_ = 0;
uint16_t ligado_ms_ = 0;
uint16_t desligado_ms_ = 0;
bool tocando_ = false;
unsigned long marca_ = 0;

void saida(bool som) {
  tocando_ = som;
  digitalWrite(PINO_BUZZER, som ? HIGH : LOW);
  marca_ = millis();
}

}  // namespace

void iniciar() {
  pinMode(PINO_BUZZER, OUTPUT);
  digitalWrite(PINO_BUZZER, LOW);
}

void tocar(uint8_t vezes, uint16_t ligado_ms, uint16_t desligado_ms) {
  if (vezes == 0 || ligado_ms == 0) {
    restantes_ = 0;
    saida(false);
    return;
  }
  restantes_ = vezes;
  ligado_ms_ = ligado_ms;
  desligado_ms_ = desligado_ms;
  saida(true);
}

void atualizar() {
  if (restantes_ == 0) return;
  const unsigned long passou = millis() - marca_;
  if (tocando_) {
    if (passou >= ligado_ms_) {
      --restantes_;
      saida(false);
    }
  } else if (passou >= desligado_ms_) {
    saida(true);
  }
}

}  // namespace buzzer
