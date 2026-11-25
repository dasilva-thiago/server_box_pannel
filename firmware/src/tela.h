// Tela ST7789 de 1,54" (240 × 240), pelo SPI.
#pragma once

#include <stdint.h>

namespace tela {

void iniciar();

// Pinta a tela inteira com a cor de fundo (RGB565). A cor vale para os textos seguintes.
void limpar(uint16_t fundo);

// Escreve uma faixa de texto na altura y, de lado a lado: o que havia na faixa some.
// alinhamento: 'E' esquerda, 'C' centro, 'D' direita. Texto que não cabe é cortado.
void texto(uint16_t y, uint8_t tamanho, uint16_t cor, char alinhamento, const char* s);

// Barra de porcentagem de lado a lado (com margem), na altura y.
void barra(uint16_t y, uint16_t altura, uint8_t porcentagem, uint16_t cor);

// Brilho da luz de fundo, 0 a 255.
void brilho(uint8_t valor);

// Telas próprias do firmware (sem o servidor).
void tela_aguardando();
void tela_sem_sinal();

}  // namespace tela
