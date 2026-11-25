// Firmware do painel frontal do eduServer Box.
//
// O Nano só obedece e avisa: desenha o que o servidor manda, toca o bipe pedido,
// acende o LED do botão e avisa quando um cartão é lido. Quem decide tudo é o
// serviço do servidor (servidor/). Protocolo: docs/01_protocolo.md.
//
// Sem nenhuma linha do servidor por SINAL_TIMEOUT_MS, o painel mostra "sem sinal" e
// apaga o LED do botão (decisão 33): o LED aceso quer dizer "o sistema está no ar".

#include <Arduino.h>
#include <SPI.h>
#include <protocolo.h>

#ifdef USAR_WDT
#include <avr/wdt.h>
#endif

#include "buzzer.h"
#include "config.h"
#include "led.h"
#include "pinos.h"
#include "rfid.h"
#include "tela.h"

namespace {

enum class Sinal : uint8_t { AGUARDANDO, COM_SINAL, SEM_SINAL };

proto::LeitorLinha leitor;
Sinal sinal = Sinal::AGUARDANDO;
unsigned long ultimo_sinal = 0;

void enviar_hello() {
  Serial.print(F("HELLO fw=" FW_VERSAO " proto="));
  Serial.print(PROTO_VERSAO);
  Serial.print(F(" rfid="));
  Serial.println(rfid::versao(), HEX);
}

// Qualquer linha do servidor conta como sinal de vida.
void marcar_sinal() {
  ultimo_sinal = millis();
  if (sinal == Sinal::SEM_SINAL) {
    // O servidor voltou: o HELLO pede que ele redesenhe tudo.
    enviar_hello();
  }
  sinal = Sinal::COM_SINAL;
}

void verificar_sinal() {
  if (sinal != Sinal::COM_SINAL || millis() - ultimo_sinal < SINAL_TIMEOUT_MS) return;
  sinal = Sinal::SEM_SINAL;
  buzzer::tocar(0, 0, 0);
  led::modo(led::Modo::APAGADO);
  tela::tela_sem_sinal();
}

void executar(const proto::Comando& c) {
  switch (c.tipo) {
    case proto::Tipo::HB:
      Serial.println(F("HB"));
      return;
    case proto::Tipo::INFO:
      enviar_hello();
      return;
    case proto::Tipo::CLS:
      tela::limpar(c.n[0]);
      break;
    case proto::Tipo::TXT:
      tela::texto(c.n[0], c.n[1], c.n[2], static_cast<char>(c.n[3]), c.texto);
      break;
    case proto::Tipo::BAR:
      tela::barra(c.n[0], c.n[1], c.n[2], c.n[3]);
      break;
    case proto::Tipo::BEEP:
      buzzer::tocar(c.n[0], c.n[1], c.n[2]);
      break;
    case proto::Tipo::LED:
      led::modo(static_cast<led::Modo>(c.n[0]));
      break;
    case proto::Tipo::BL:
      tela::brilho(c.n[0]);
      break;
  }
  // Resposta depois de desenhar: o servidor espera o OK antes de mandar a próxima
  // linha, e o buffer da serial nunca enche enquanto a tela está ocupada.
  Serial.println(F("OK"));
}

void tratar_linha(char* linha) {
  marcar_sinal();
  proto::Comando c;
  switch (proto::interpretar(linha, c)) {
    case proto::Resultado::OK:
      executar(c);
      break;
    case proto::Resultado::VAZIA:
      break;
    case proto::Resultado::COMANDO_DESCONHECIDO:
      Serial.println(F("ERR comando"));
      break;
    case proto::Resultado::ARGS_INVALIDOS:
      Serial.println(F("ERR args"));
      break;
  }
}

void tratar_rfid() {
  char uid[21];
  switch (rfid::atualizar(uid)) {
    case rfid::Leitura::CARTAO:
      Serial.print(F("CARD "));
      Serial.println(uid);
      break;
    case rfid::Leitura::PERDIDO:
      Serial.println(F("RFID perdido"));
      break;
    case rfid::Leitura::REINICIADO:
      Serial.println(F("RFID reiniciado"));
      break;
    case rfid::Leitura::VOLTOU:
      Serial.println(F("RFID ok"));
      break;
    case rfid::Leitura::NADA:
      break;
  }
}

}  // namespace

void setup() {
#ifdef USAR_WDT
  MCUSR = 0;
  wdt_disable();
#endif
  // Os dois chips do SPI começam desligados do barramento.
  pinMode(PINO_RFID_SS, OUTPUT);
  digitalWrite(PINO_RFID_SS, HIGH);
  pinMode(PINO_TELA_CS, OUTPUT);
  digitalWrite(PINO_TELA_CS, HIGH);

  Serial.begin(SERIAL_BAUD);
  buzzer::iniciar();
  led::iniciar();
  led::modo(led::Modo::RESPIRA);  // ligando: respira até o servidor assumir

  SPI.begin();
  tela::iniciar();
  tela::tela_aguardando();
  rfid::iniciar();

  enviar_hello();

#ifdef USAR_WDT
  // Se o programa travar por mais de 4 s, o Nano reinicia sozinho.
  wdt_enable(WDTO_4S);
#endif
}

void loop() {
#ifdef USAR_WDT
  wdt_reset();
#endif
  while (Serial.available() > 0) {
    switch (leitor.alimentar(static_cast<char>(Serial.read()))) {
      case proto::Evento::LINHA:
        tratar_linha(leitor.linha());
        break;
      case proto::Evento::ESTOUROU:
        marcar_sinal();
        Serial.println(F("ERR linha_longa"));
        break;
      case proto::Evento::NADA:
        break;
    }
  }
  tratar_rfid();
  buzzer::atualizar();
  led::atualizar();
  verificar_sinal();
}
