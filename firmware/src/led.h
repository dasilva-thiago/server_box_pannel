// LED do botão Power, aceso pelo Nano (decisão 33). Nunca ligado à placa-mãe.
#pragma once

#include <stdint.h>

namespace led {

// Os números são os do comando LED do protocolo.
enum class Modo : uint8_t { APAGADO = 0, ACESO = 1, RESPIRA = 2, PISCA = 3 };

void iniciar();
void modo(Modo m);
void atualizar();

}  // namespace led
