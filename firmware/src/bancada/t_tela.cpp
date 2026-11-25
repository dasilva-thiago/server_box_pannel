// T-TELA: a tela liga, as cores estão certas e o texto aparece?
// Usa o mesmo código de tela do painel (src/tela.cpp).
//
// Gravar: pio run -e t_tela -t upload     Ver: pio device monitor
// Ligação: docs/02_pinagem.md. Só a tela (com os divisores) e o regulador de 3,3 V.

#include <Arduino.h>
#include <SPI.h>

#include "../tela.h"
#include "config.h"
#include "pinos.h"

namespace {

constexpr uint16_t PRETO = 0x0000;
constexpr uint16_t BRANCO = 0xFFFF;
constexpr uint16_t VERMELHO = 0xF800;
constexpr uint16_t VERDE = 0x07E0;
constexpr uint16_t AZUL = 0x001F;
constexpr uint16_t AMARELO = 0xFFE0;

void cor_cheia(uint16_t cor, const __FlashStringHelper* nome) {
  Serial.print(F("  tela inteira: "));
  Serial.println(nome);
  tela::limpar(cor);
  delay(1200);
}

}  // namespace

void setup() {
  pinMode(PINO_RFID_SS, OUTPUT);  // se o RFID estiver ligado, fica fora do barramento
  digitalWrite(PINO_RFID_SS, HIGH);
  Serial.begin(SERIAL_BAUD);
  Serial.println(F("\n=== T-TELA ==="));
  SPI.begin();
  tela::iniciar();

  Serial.println(F("1. Cores. Confira se cada cor aparece como o nome diz."));
  cor_cheia(VERMELHO, F("VERMELHO"));
  cor_cheia(VERDE, F("VERDE"));
  cor_cheia(AZUL, F("AZUL"));
  cor_cheia(BRANCO, F("BRANCO"));
  cor_cheia(PRETO, F("PRETO"));
  Serial.println(F("   Cores trocadas ou negativas? Mude TELA_INVERSAO em include/config.h."));

  Serial.println(F("2. Texto nos 4 tamanhos e uma barra de 60 %."));
  tela::limpar(PRETO);
  tela::texto(0, 1, BRANCO, 'E', "tamanho 1: 40 letras por linha");
  tela::texto(16, 2, VERDE, 'E', "tamanho 2: 20");
  tela::texto(40, 3, AMARELO, 'C', "tamanho 3");
  tela::texto(72, 4, VERMELHO, 'D', "tam 4");
  tela::barra(120, 12, 60, VERDE);
  tela::texto(140, 2, BRANCO, 'C', "esquerda");
  tela::texto(160, 2, BRANCO, 'C', "centro");
  tela::texto(180, 2, BRANCO, 'C', "direita");
  Serial.println(F("   O texto ficou de cabeça para baixo ou de lado? Mude TELA_ROTACAO."));

  Serial.println(F("3. Brilho: vai do apagado ao máximo (só funciona com o BL ligado no D3)."));
  for (int v = 0; v <= 255; v += 5) {
    tela::brilho(v);
    delay(40);
  }
  tela::brilho(TELA_BRILHO_INICIAL);
  Serial.println(F("4. Contador a cada segundo. Deixe ligado e veja se a imagem falha."));
}

void loop() {
  static unsigned long n = 0;
  char linha[21];
  snprintf(linha, sizeof(linha), "contador %lu", n++);
  tela::texto(212, 2, BRANCO, 'C', linha);
  delay(1000);
}
