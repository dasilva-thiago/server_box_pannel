// Ajustes do firmware do painel. Valores de partida; a bancada (T-BANC) confirma.
#pragma once

#include <stdint.h>

#define FW_VERSAO "0.1.0"

// Versão do protocolo serial (docs/01_protocolo.md). Sobe quando um comando muda.
constexpr uint8_t PROTO_VERSAO = 1;

constexpr unsigned long SERIAL_BAUD = 115200;

// Sem nenhuma linha do servidor por este tempo, o painel mostra "sem sinal" e apaga o
// LED do botão. O servidor manda HB a cada 2 s, então 6 s são 3 batidas perdidas.
constexpr unsigned long SINAL_TIMEOUT_MS = 6000;

// RFID
constexpr unsigned long RFID_INTERVALO_MS = 100;   // de quanto em quanto tempo procura cartão
constexpr unsigned long RFID_REPETE_MS = 2000;     // o mesmo cartão não é avisado de novo antes disso
constexpr unsigned long RFID_CONFERE_MS = 30000;   // confere se o leitor ainda responde

// Tela ST7789 de 240 × 240
constexpr uint32_t TELA_SPI_HZ = 8000000;  // máximo do ATmega328P a 16 MHz; baixe se a imagem falhar
constexpr uint8_t TELA_ROTACAO = 0;        // 0 a 3; ajuste conforme a posição no painel
constexpr bool TELA_INVERSAO = true;       // telas IPS costumam pedir inversão de cores
constexpr uint8_t TELA_BRILHO_INICIAL = 200;

// LED do botão
constexpr uint8_t LED_BRILHO_MAX = 255;
constexpr unsigned long LED_RESPIRA_MS = 3000;  // período de uma "respiração"
constexpr unsigned long LED_PISCA_MS = 500;     // meio período do pisca

// Os limites dos argumentos dos comandos ficam em lib/protocolo/src/protocolo.h.
