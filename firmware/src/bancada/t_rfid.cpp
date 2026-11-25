// T-RFID: o leitor responde? Lê o cartão? Lê através da tela (posição B, decisão 25)?
//
// Gravar: pio run -e t_rfid -t upload     Ver: pio device monitor
// Ligação: docs/02_pinagem.md. Só o RFID (com os divisores) e o regulador de 3,3 V.
//
// A cada 2 s, mostra a PRESENÇA: em quantas das últimas 20 procuras o cartão respondeu.
// Para comparar posições (cartão direto no leitor, através de 2 mm de plástico,
// através da tela), segure o cartão parado e anote a porcentagem de cada uma.
// No monitor, digite + (ganho máximo da antena) ou - (ganho normal) e Enter.

#include <Arduino.h>
#include <MFRC522.h>
#include <SPI.h>

#include "config.h"
#include "pinos.h"

namespace {

MFRC522 leitor(PINO_RFID_SS, PINO_RFID_RST);

uint8_t procuras = 0;
uint8_t presencas = 0;
unsigned long ultimo_poll = 0;
unsigned long ultimo_relatorio = 0;
char ultimo_uid[21] = "";

void mostrar_versao() {
  const uint8_t v = leitor.PCD_ReadRegister(MFRC522::VersionReg);
  Serial.print(F("Versão do chip: 0x"));
  Serial.print(v, HEX);
  switch (v) {
    case 0x91:
    case 0x92:
      Serial.println(F(" (MFRC522 legítimo)"));
      break;
    case 0x88:
      Serial.println(F(" (clone, costuma funcionar)"));
      break;
    case 0x12:
      Serial.println(F(" (falsificado, costuma funcionar)"));
      break;
    case 0x00:
    case 0xFF:
      Serial.println(F(" -> SEM COMUNICAÇÃO."));
      Serial.println(F("   Confira: 3,3 V e GND no RFID; SCK no D13, MOSI no D11, MISO no D12,"));
      Serial.println(F("   SDA no D10, RST no D9; os divisores nos fios que saem do Nano."));
      break;
    default:
      Serial.println(F(" (desconhecido; tente ler um cartão mesmo assim)"));
  }
}

void mostrar_ganho() {
  Serial.print(F("Ganho da antena: "));
  Serial.println(leitor.PCD_GetAntennaGain() == MFRC522::RxGain_max ? F("MÁXIMO (48 dB)")
                                                                     : F("normal"));
}

void ler_teclado() {
  while (Serial.available() > 0) {
    const char ch = Serial.read();
    if (ch == '+') {
      leitor.PCD_SetAntennaGain(MFRC522::RxGain_max);
      mostrar_ganho();
    } else if (ch == '-') {
      leitor.PCD_SetAntennaGain(MFRC522::RxGain_33dB);
      mostrar_ganho();
    }
  }
}

void procurar() {
  // WakeupA acorda até cartão que já foi lido: serve para medir a presença contínua.
  byte atqa[2];
  byte tamanho = sizeof(atqa);
  const MFRC522::StatusCode st = leitor.PICC_WakeupA(atqa, &tamanho);
  ++procuras;
  if (st != MFRC522::STATUS_OK && st != MFRC522::STATUS_COLLISION) return;
  ++presencas;

  if (!leitor.PICC_ReadCardSerial()) return;
  char uid[21];
  uint8_t k = 0;
  for (uint8_t i = 0; i < leitor.uid.size && i < 10; ++i) {
    snprintf(&uid[k], 3, "%02X", leitor.uid.uidByte[i]);
    k += 2;
  }
  uid[k] = '\0';
  if (strcmp(uid, ultimo_uid) != 0) {
    strcpy(ultimo_uid, uid);
    Serial.print(F("Cartão: "));
    Serial.print(uid);
    Serial.print(F("  tipo: "));
    Serial.println(leitor.PICC_GetTypeName(leitor.PICC_GetType(leitor.uid.sak)));
  }
  leitor.PICC_HaltA();
}

}  // namespace

void setup() {
  pinMode(PINO_TELA_CS, OUTPUT);  // se a tela estiver ligada, fica fora do barramento
  digitalWrite(PINO_TELA_CS, HIGH);
  Serial.begin(SERIAL_BAUD);
  Serial.println(F("\n=== T-RFID ==="));
  SPI.begin();
  leitor.PCD_Init();
  delay(10);
  mostrar_versao();
  mostrar_ganho();
  Serial.println(F("Aproxime um cartão. Presença a cada 2 s. Digite + ou - para o ganho."));
}

void loop() {
  ler_teclado();
  const unsigned long agora = millis();
  if (agora - ultimo_poll >= 100) {
    ultimo_poll = agora;
    procurar();
  }
  if (agora - ultimo_relatorio >= 2000) {
    ultimo_relatorio = agora;
    Serial.print(F("presença: "));
    Serial.print(presencas);
    Serial.print('/');
    Serial.print(procuras);
    Serial.print(F(" ("));
    Serial.print(procuras ? 100 * presencas / procuras : 0);
    Serial.println(F(" %)"));
    if (presencas == 0) ultimo_uid[0] = '\0';  // tirou o cartão: o próximo aparece de novo
    procuras = 0;
    presencas = 0;
  }
}
