#include "tela.h"

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <string.h>

#include "config.h"
#include "pinos.h"

namespace tela {

namespace {

Adafruit_ST7789 tft(PINO_TELA_CS, PINO_TELA_DC, PINO_TELA_RST);

constexpr int16_t LARGURA = 240;
constexpr int16_t MARGEM = 8;               // margem das barras
constexpr uint16_t CINZA_ESCURO = 0x2104;   // parte vazia da barra
uint16_t fundo_ = ST77XX_BLACK;

}  // namespace

void iniciar() {
  pinMode(PINO_TELA_BL, OUTPUT);
  brilho(TELA_BRILHO_INICIAL);
  tft.init(LARGURA, LARGURA);
  tft.setSPISpeed(TELA_SPI_HZ);
  tft.setRotation(TELA_ROTACAO);
  tft.invertDisplay(TELA_INVERSAO);
  tft.setTextWrap(false);
  limpar(ST77XX_BLACK);
}

void limpar(uint16_t fundo) {
  fundo_ = fundo;
  tft.fillScreen(fundo_);
}

void texto(uint16_t y, uint8_t tamanho, uint16_t cor, char alinhamento, const char* s) {
  const int16_t largura_letra = 6 * tamanho;  // fonte padrão: 5 × 7 px + 1 de espaço
  const int16_t altura = 8 * tamanho;
  size_t n = strlen(s);
  const size_t cabe = LARGURA / largura_letra;
  if (n > cabe) n = cabe;
  const int16_t w = static_cast<int16_t>(n) * largura_letra;

  int16_t x = 0;
  if (alinhamento == 'C') {
    x = (LARGURA - w) / 2;
  } else if (alinhamento == 'D') {
    x = LARGURA - w;
  }

  // Apaga só o que fica fora do texto; o texto é desenhado já com o fundo, sem piscar.
  if (x > 0) tft.fillRect(0, y, x, altura, fundo_);
  tft.setTextSize(tamanho);
  tft.setTextColor(cor, fundo_);
  tft.setCursor(x, y);
  for (size_t i = 0; i < n; ++i) tft.write(s[i]);
  if (x + w < LARGURA) tft.fillRect(x + w, y, LARGURA - x - w, altura, fundo_);
}

void barra(uint16_t y, uint16_t altura, uint8_t porcentagem, uint16_t cor) {
  const int16_t total = LARGURA - 2 * MARGEM;
  const int16_t cheio = static_cast<int16_t>(static_cast<int32_t>(total) * porcentagem / 100);
  tft.fillRect(0, y, MARGEM, altura, fundo_);
  tft.fillRect(MARGEM, y, cheio, altura, cor);
  tft.fillRect(MARGEM + cheio, y, total - cheio, altura, CINZA_ESCURO);
  tft.fillRect(LARGURA - MARGEM, y, MARGEM, altura, fundo_);
}

void brilho(uint8_t valor) { analogWrite(PINO_TELA_BL, valor); }

void tela_aguardando() {
  limpar(ST77XX_BLACK);
  texto(76, 3, ST77XX_CYAN, 'C', "eduServer");
  texto(124, 2, ST77XX_WHITE, 'C', "aguardando");
  texto(144, 2, ST77XX_WHITE, 'C', "o servidor...");
}

void tela_sem_sinal() {
  limpar(ST77XX_BLACK);
  texto(76, 3, ST77XX_RED, 'C', "SEM SINAL");
  texto(124, 2, ST77XX_WHITE, 'C', "o servidor");
  texto(144, 2, ST77XX_WHITE, 'C', "nao responde");
}

}  // namespace tela
