#include "rfid.h"

#include <Arduino.h>
#include <MFRC522.h>
#include <string.h>

#include "config.h"
#include "pinos.h"

namespace rfid {

namespace {

MFRC522 leitor(PINO_RFID_SS, PINO_RFID_RST);

uint8_t versao_ = 0;
bool ok_ = false;
unsigned long ultimo_poll_ = 0;
unsigned long ultima_conferencia_ = 0;
char ultimo_uid_[21] = "";
unsigned long ultimo_aviso_ = 0;

bool versao_valida(uint8_t v) { return v != 0x00 && v != 0xFF; }

void para_hex(uint8_t b, char* destino) {
  static const char DIGITOS[] = "0123456789ABCDEF";
  destino[0] = DIGITOS[b >> 4];
  destino[1] = DIGITOS[b & 0x0F];
}

}  // namespace

void iniciar() {
  leitor.PCD_Init();
  versao_ = leitor.PCD_ReadRegister(MFRC522::VersionReg);
  ok_ = versao_valida(versao_);
}

uint8_t versao() { return versao_; }

Leitura atualizar(char* uid_hex) {
  const unsigned long agora = millis();

  // De tempos em tempos, confere se o leitor ainda responde. Alguns módulos param
  // depois de horas ligados; um reinício costuma trazer de volta.
  if (agora - ultima_conferencia_ >= RFID_CONFERE_MS) {
    ultima_conferencia_ = agora;
    const bool antes = ok_;
    if (!versao_valida(leitor.PCD_ReadRegister(MFRC522::VersionReg))) {
      iniciar();
      if (antes) return ok_ ? Leitura::REINICIADO : Leitura::PERDIDO;
      if (ok_) return Leitura::VOLTOU;
    }
  }

  if (!ok_ || agora - ultimo_poll_ < RFID_INTERVALO_MS) return Leitura::NADA;
  ultimo_poll_ = agora;

  if (!leitor.PICC_IsNewCardPresent() || !leitor.PICC_ReadCardSerial()) return Leitura::NADA;

  char uid[21];
  uint8_t k = 0;
  for (uint8_t i = 0; i < leitor.uid.size && i < 10; ++i) {
    para_hex(leitor.uid.uidByte[i], &uid[k]);
    k += 2;
  }
  uid[k] = '\0';
  leitor.PICC_HaltA();
  leitor.PCD_StopCrypto1();

  // O mesmo cartão, de novo em pouco tempo: é o mesmo gesto, não avisa outra vez.
  const bool repetido = strcmp(uid, ultimo_uid_) == 0 && agora - ultimo_aviso_ < RFID_REPETE_MS;
  ultimo_aviso_ = agora;
  if (repetido) return Leitura::NADA;

  strcpy(ultimo_uid_, uid);
  strcpy(uid_hex, uid);
  return Leitura::CARTAO;
}

}  // namespace rfid
