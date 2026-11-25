// Buzzer ativo de 5 V: nível alto = som. Tom fixo; só a duração e o ritmo mudam.
#pragma once

#include <stdint.h>

namespace buzzer {

void iniciar();

// Toca "vezes" bipes de "ligado_ms", com "desligado_ms" entre eles. Sem bloquear:
// quem toca é atualizar(). vezes = 0 ou ligado_ms = 0 cala o buzzer.
void tocar(uint8_t vezes, uint16_t ligado_ms, uint16_t desligado_ms);

void atualizar();

}  // namespace buzzer
