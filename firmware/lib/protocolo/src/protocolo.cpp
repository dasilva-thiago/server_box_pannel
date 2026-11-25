#include "protocolo.h"

#include <string.h>

namespace proto {

namespace {

// Tipos de argumento: d = decimal (0 a 65535), x = hexadecimal (1 a 4 dígitos),
// c = um caractere, * = o resto da linha (pode ser vazio; sempre o último).
struct Spec {
  const char* nome;
  Tipo tipo;
  const char* args;
};

const Spec SPECS[] = {
    {"HB", Tipo::HB, ""},
    {"INFO", Tipo::INFO, ""},
    {"CLS", Tipo::CLS, "x"},
    {"TXT", Tipo::TXT, "ddxc*"},  // y, tamanho, cor, alinhamento, texto
    {"BAR", Tipo::BAR, "dddx"},   // y, altura, porcentagem, cor
    {"BEEP", Tipo::BEEP, "ddd"},  // vezes, ms ligado, ms desligado
    {"LED", Tipo::LED, "d"},      // modo
    {"BL", Tipo::BL, "d"},        // brilho 0 a 255
};

const Spec* procurar(const char* nome) {
  for (const Spec& s : SPECS) {
    if (strcmp(s.nome, nome) == 0) return &s;
  }
  return nullptr;
}

bool converter(char tipo, const char* t, int32_t& v) {
  size_t len = strlen(t);
  if (len == 0) return false;
  v = 0;
  switch (tipo) {
    case 'd':
      if (len > 5) return false;
      for (size_t i = 0; i < len; ++i) {
        if (t[i] < '0' || t[i] > '9') return false;
        v = v * 10 + (t[i] - '0');
      }
      return v <= 65535;
    case 'x':
      if (len > 4) return false;
      for (size_t i = 0; i < len; ++i) {
        char ch = t[i];
        int32_t d;
        if (ch >= '0' && ch <= '9') {
          d = ch - '0';
        } else if (ch >= 'A' && ch <= 'F') {
          d = ch - 'A' + 10;
        } else if (ch >= 'a' && ch <= 'f') {
          d = ch - 'a' + 10;
        } else {
          return false;
        }
        v = v * 16 + d;
      }
      return true;
    case 'c':
      if (len != 1) return false;
      v = static_cast<unsigned char>(t[0]);
      return true;
    default:
      return false;
  }
}

bool dentro(int32_t v, int32_t min, int32_t max) { return v >= min && v <= max; }

bool validar(const Comando& c) {
  switch (c.tipo) {
    case Tipo::TXT:
      return dentro(c.n[0], 0, TELA_ALTURA - 1) && dentro(c.n[1], 1, TAM_MAX) &&
             (c.n[3] == 'E' || c.n[3] == 'C' || c.n[3] == 'D');
    case Tipo::BAR:
      return dentro(c.n[0], 0, TELA_ALTURA - 1) && dentro(c.n[1], 1, TELA_ALTURA) &&
             dentro(c.n[2], 0, 100);
    case Tipo::BEEP:
      // vezes = 0 cala o buzzer.
      return dentro(c.n[0], 0, BEEP_VEZES_MAX) && dentro(c.n[1], 0, BEEP_MS_MAX) &&
             dentro(c.n[2], 0, BEEP_MS_MAX);
    case Tipo::LED:
      return dentro(c.n[0], 0, LED_MODO_MAX);
    case Tipo::BL:
      return dentro(c.n[0], 0, 255);
    default:
      return true;
  }
}

}  // namespace

Resultado interpretar(char* linha, Comando& c) {
  char* p = linha;
  while (*p == ' ') ++p;
  if (*p == '\0') return Resultado::VAZIA;

  char* nome = p;
  while (*p != '\0' && *p != ' ') ++p;
  if (*p != '\0') *p++ = '\0';

  const Spec* s = procurar(nome);
  if (s == nullptr) return Resultado::COMANDO_DESCONHECIDO;

  c.tipo = s->tipo;
  c.qtd = 0;
  c.texto = nullptr;

  for (const char* a = s->args; *a != '\0'; ++a) {
    if (*a == '*') {
      c.texto = p;  // o resto da linha, com os espaços
      return validar(c) ? Resultado::OK : Resultado::ARGS_INVALIDOS;
    }
    // Argumentos separados por um espaço só.
    if (*p == '\0' || *p == ' ') return Resultado::ARGS_INVALIDOS;
    char* ini = p;
    while (*p != '\0' && *p != ' ') ++p;
    bool fim = (*p == '\0');
    *p = '\0';
    int32_t v;
    if (!converter(*a, ini, v)) return Resultado::ARGS_INVALIDOS;
    c.n[c.qtd++] = v;
    if (!fim) ++p;
  }

  if (*p != '\0') return Resultado::ARGS_INVALIDOS;  // sobrou argumento
  return validar(c) ? Resultado::OK : Resultado::ARGS_INVALIDOS;
}

Evento LeitorLinha::alimentar(char ch) {
  if (ch == '\r') return Evento::NADA;
  if (ch == '\n') {
    if (descartando_) {
      descartando_ = false;
      n_ = 0;
      buf_[0] = '\0';
      return Evento::ESTOUROU;
    }
    buf_[n_] = '\0';
    n_ = 0;
    return Evento::LINHA;
  }
  if (descartando_) return Evento::NADA;
  if (n_ >= LINHA_MAX - 1) {
    descartando_ = true;
    return Evento::NADA;
  }
  buf_[n_++] = ch;
  return Evento::NADA;
}

}  // namespace proto
