// Protocolo serial do painel (docs/01_protocolo.md), lado do Nano.
//
// C++ puro, sem Arduino: o mesmo código roda no Nano e nos testes do PC (env nativo).
#pragma once

#include <stdint.h>

namespace proto {

// Uma linha tem no máximo 63 caracteres, sem contar o '\n'.
constexpr uint8_t LINHA_MAX = 64;  // com o '\0'
constexpr uint8_t NUM_MAX = 5;

// Limites dos argumentos. Fora deles, o comando é recusado (ERR args).
constexpr uint16_t TELA_LARGURA = 240;
constexpr uint16_t TELA_ALTURA = 240;
constexpr uint8_t TAM_MAX = 4;  // tamanho do texto: 1 = 6 × 8 px por letra, 4 = 24 × 32
constexpr uint8_t BEEP_VEZES_MAX = 10;
constexpr uint16_t BEEP_MS_MAX = 2000;
constexpr uint8_t LED_MODO_MAX = 3;

enum class Tipo : uint8_t { HB, INFO, CLS, TXT, BAR, BEEP, LED, BL };

enum class Resultado : uint8_t {
  OK,
  VAZIA,                 // linha em branco: ignorar, sem resposta
  COMANDO_DESCONHECIDO,  // responder "ERR comando"
  ARGS_INVALIDOS,        // responder "ERR args"
};

// Comando interpretado. Os números ficam em n[] na ordem da tabela do protocolo;
// texto aponta para dentro da própria linha (só no TXT).
struct Comando {
  Tipo tipo;
  uint8_t qtd;
  int32_t n[NUM_MAX];
  const char* texto;
};

// Interpreta uma linha (sem o '\n'). Altera a linha: troca os espaços por '\0'.
Resultado interpretar(char* linha, Comando& c);

enum class Evento : uint8_t { NADA, LINHA, ESTOUROU };

// Junta os caracteres que chegam pela serial em linhas.
class LeitorLinha {
 public:
  // LINHA: linha() tem uma linha completa. ESTOUROU: a linha passou de 63 caracteres
  // e foi descartada inteira (até o próximo '\n').
  Evento alimentar(char ch);
  char* linha() { return buf_; }

 private:
  char buf_[LINHA_MAX] = {};
  uint8_t n_ = 0;
  bool descartando_ = false;
};

}  // namespace proto
