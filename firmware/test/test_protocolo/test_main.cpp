// Testes do protocolo no PC: pio test -e nativo (precisa de gcc; roda no CI).
#include <protocolo.h>
#include <string.h>
#include <unity.h>

using proto::Comando;
using proto::Evento;
using proto::LeitorLinha;
using proto::Resultado;
using proto::Tipo;

namespace {

Resultado ler(const char* texto, Comando& c) {
  static char buf[proto::LINHA_MAX];
  strncpy(buf, texto, sizeof(buf) - 1);
  buf[sizeof(buf) - 1] = '\0';
  return proto::interpretar(buf, c);
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_hb_e_info() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::OK, ler("HB", c));
  TEST_ASSERT_EQUAL(Tipo::HB, c.tipo);
  TEST_ASSERT_EQUAL(Resultado::OK, ler("INFO", c));
  TEST_ASSERT_EQUAL(Tipo::INFO, c.tipo);
}

void test_linha_vazia() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::VAZIA, ler("", c));
  TEST_ASSERT_EQUAL(Resultado::VAZIA, ler("   ", c));
}

void test_comando_desconhecido() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::COMANDO_DESCONHECIDO, ler("XYZ 1", c));
  TEST_ASSERT_EQUAL(Resultado::COMANDO_DESCONHECIDO, ler("hb", c));  // maiúsculas
}

void test_cls_hexa() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::OK, ler("CLS F800", c));
  TEST_ASSERT_EQUAL(Tipo::CLS, c.tipo);
  TEST_ASSERT_EQUAL_INT32(0xF800, c.n[0]);
  TEST_ASSERT_EQUAL(Resultado::OK, ler("CLS 0", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("CLS 1FFFF", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("CLS G0", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("CLS", c));
}

void test_txt_com_espacos_no_texto() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::OK, ler("TXT 30 2 FFFF C ip  192.168.0.10", c));
  TEST_ASSERT_EQUAL(Tipo::TXT, c.tipo);
  TEST_ASSERT_EQUAL_INT32(30, c.n[0]);
  TEST_ASSERT_EQUAL_INT32(2, c.n[1]);
  TEST_ASSERT_EQUAL_INT32(0xFFFF, c.n[2]);
  TEST_ASSERT_EQUAL_INT32('C', c.n[3]);
  TEST_ASSERT_EQUAL_STRING("ip  192.168.0.10", c.texto);
}

void test_txt_vazio_apaga_a_faixa() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::OK, ler("TXT 30 2 FFFF E", c));
  TEST_ASSERT_EQUAL_STRING("", c.texto);
  TEST_ASSERT_EQUAL(Resultado::OK, ler("TXT 30 2 FFFF E ", c));
  TEST_ASSERT_EQUAL_STRING("", c.texto);
}

void test_txt_limites() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT 240 2 FFFF E x", c));  // y fora
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT 0 5 FFFF E x", c));    // tamanho
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT 0 0 FFFF E x", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT 0 2 FFFF X x", c));    // alinhamento
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT 0 2 FFFF EE x", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT 0 2 FFFF", c));        // falta argumento
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT  0 2 FFFF E x", c));   // dois espaços
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("TXT -1 2 FFFF E x", c));
}

void test_bar() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::OK, ler("BAR 120 8 61 07E0", c));
  TEST_ASSERT_EQUAL_INT32(61, c.n[2]);
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BAR 120 8 101 07E0", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BAR 120 0 50 07E0", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BAR 120 8 50 07E0 9", c));  // sobrou
}

void test_beep_led_bl() {
  Comando c;
  TEST_ASSERT_EQUAL(Resultado::OK, ler("BEEP 3 150 150", c));
  TEST_ASSERT_EQUAL(Resultado::OK, ler("BEEP 0 0 0", c));  // cala
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BEEP 11 100 100", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BEEP 1 2001 0", c));
  TEST_ASSERT_EQUAL(Resultado::OK, ler("LED 2", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("LED 4", c));
  TEST_ASSERT_EQUAL(Resultado::OK, ler("BL 255", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BL 256", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BL 99999", c));
  TEST_ASSERT_EQUAL(Resultado::ARGS_INVALIDOS, ler("BL 123456", c));
}

Evento alimentar_texto(LeitorLinha& l, const char* s) {
  Evento ultimo = Evento::NADA;
  for (; *s; ++s) {
    Evento e = l.alimentar(*s);
    if (e != Evento::NADA) ultimo = e;
  }
  return ultimo;
}

void test_leitor_junta_linhas_e_ignora_cr() {
  LeitorLinha l;
  TEST_ASSERT_EQUAL(Evento::NADA, alimentar_texto(l, "H"));
  TEST_ASSERT_EQUAL(Evento::LINHA, alimentar_texto(l, "B\r\n"));
  TEST_ASSERT_EQUAL_STRING("HB", l.linha());
  TEST_ASSERT_EQUAL(Evento::LINHA, alimentar_texto(l, "INFO\n"));
  TEST_ASSERT_EQUAL_STRING("INFO", l.linha());
}

void test_leitor_63_cabe_64_estoura() {
  LeitorLinha l;
  char linha[70];
  memset(linha, 'a', 63);
  linha[63] = '\n';
  linha[64] = '\0';
  TEST_ASSERT_EQUAL(Evento::LINHA, alimentar_texto(l, linha));
  TEST_ASSERT_EQUAL(63, strlen(l.linha()));

  memset(linha, 'a', 64);
  linha[64] = '\n';
  linha[65] = '\0';
  TEST_ASSERT_EQUAL(Evento::ESTOUROU, alimentar_texto(l, linha));
  // Depois do estouro, a próxima linha chega inteira.
  TEST_ASSERT_EQUAL(Evento::LINHA, alimentar_texto(l, "HB\n"));
  TEST_ASSERT_EQUAL_STRING("HB", l.linha());
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_hb_e_info);
  RUN_TEST(test_linha_vazia);
  RUN_TEST(test_comando_desconhecido);
  RUN_TEST(test_cls_hexa);
  RUN_TEST(test_txt_com_espacos_no_texto);
  RUN_TEST(test_txt_vazio_apaga_a_faixa);
  RUN_TEST(test_txt_limites);
  RUN_TEST(test_bar);
  RUN_TEST(test_beep_led_bl);
  RUN_TEST(test_leitor_junta_linhas_e_ignora_cr);
  RUN_TEST(test_leitor_63_cabe_64_estoura);
  return UNITY_END();
}
