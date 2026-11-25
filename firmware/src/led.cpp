#include "led.h"

#include <Arduino.h>

#include "config.h"
#include "pinos.h"

namespace led {

namespace {

Modo modo_ = Modo::APAGADO;
int16_t escrito_ = -1;  // último valor de PWM escrito (-1 = nenhum)

void escrever(uint8_t valor) {
  if (valor == escrito_) return;
  escrito_ = valor;
  analogWrite(PINO_LED_BOTAO, valor);
}

}  // namespace

void iniciar() {
  pinMode(PINO_LED_BOTAO, OUTPUT);
  escrever(0);
}

void modo(Modo m) {
  modo_ = m;
  atualizar();
}

void atualizar() {
  const unsigned long agora = millis();
  switch (modo_) {
    case Modo::APAGADO:
      escrever(0);
      break;
    case Modo::ACESO:
      escrever(LED_BRILHO_MAX);
      break;
    case Modo::RESPIRA: {
      // Onda triangular, elevada ao quadrado: o olho acha a subida mais natural.
      const unsigned long meio = LED_RESPIRA_MS / 2;
      const unsigned long fase = agora % LED_RESPIRA_MS;
      const unsigned long tri = fase < meio ? fase : LED_RESPIRA_MS - fase;  // 0..meio
      const uint32_t nivel = static_cast<uint32_t>(tri) * 255 / meio;       // 0..255
      escrever(static_cast<uint8_t>(nivel * nivel / 255 * LED_BRILHO_MAX / 255));
      break;
    }
    case Modo::PISCA:
      escrever((agora / LED_PISCA_MS) % 2 ? LED_BRILHO_MAX : 0);
      break;
  }
}

}  // namespace led
