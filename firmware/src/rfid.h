// Leitor RFID MFRC522 (13,56 MHz), pelo SPI.
#pragma once

#include <stdint.h>

namespace rfid {

enum class Leitura : uint8_t {
  NADA,
  CARTAO,      // cartão novo: o UID está no buffer
  PERDIDO,     // o leitor parou de responder e não voltou com o reinício
  REINICIADO,  // o leitor parou de responder e voltou depois do reinício
  VOLTOU,      // o leitor estava ausente e agora responde
};

void iniciar();

// Registrador de versão do chip: 0x91 ou 0x92 = MFRC522 legítimo, 0x88 = clone,
// 0x12 = falsificado que costuma funcionar; 0x00 ou 0xFF = sem comunicação.
uint8_t versao();

// Chamar sempre no loop. uid_hex precisa de 21 bytes (até 10 bytes de UID em hexa).
Leitura atualizar(char* uid_hex);

}  // namespace rfid
