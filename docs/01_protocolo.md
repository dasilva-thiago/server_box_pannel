# 01 · Protocolo serial

**Versão 1 (revisão S1, 25/11/2026).** Implementado em
`firmware/lib/protocolo/` (Nano) e `servidor/src/eduserver_painel/protocolo.py`.
Mudou um comando: suba a versão nos dois lados e nos testes.

## Regras gerais

- Serial a **115200 baud**, 8N1. Texto ASCII, uma mensagem por linha, terminada em
  `\n` (o `\r` é ignorado).
- Linha com no máximo **63 caracteres** (sem o `\n`). Mais que isso: o Nano descarta a
  linha inteira e responde `ERR linha_longa`.
- Argumentos separados por **um** espaço. Nomes em maiúsculas.
- **Um comando por vez:** todo comando tem resposta (`OK`, `ERR …`, `HB` ou `HELLO`), e o
  servidor só manda o próximo depois dela (prazo: 1 s). Assim o buffer do Nano nunca
  enche enquanto a tela desenha.
- Qualquer linha do servidor conta como sinal de vida. Sem nenhuma por **6 s**, o Nano
  mostra "SEM SINAL" e apaga o LED do botão.
- Cores em **RGB565**, 4 dígitos hexadecimais (`F800` vermelho, `07E0` verde, `001F`
  azul, `FFFF` branco, `0000` preto).

## Servidor → Nano

| Comando | Argumentos | O que faz | Resposta |
|---|---|---|---|
| `HB` | — | Batida (a cada 2 s) | `HB` |
| `INFO` | — | Pede a identificação | `HELLO …` |
| `CLS cor` | cor de fundo | Pinta a tela inteira; a cor vira o fundo dos textos seguintes | `OK` |
| `TXT y tam cor al texto` | y 0–239; tam 1–4; cor; al `E`/`C`/`D`; texto (pode ter espaços, pode ser vazio) | Faixa de texto de lado a lado na altura y, com altura 8 × tam: o que havia na faixa some. Texto que não cabe é cortado | `OK` |
| `BAR y alt pct cor` | y 0–239; alt 1–240; pct 0–100; cor | Barra de porcentagem de lado a lado (margem de 8 px) | `OK` |
| `BEEP n lig desl` | n 0–10; lig e desl 0–2000 ms | Toca n bipes, sem travar o Nano. `BEEP 0 0 0` cala | `OK` |
| `LED modo` | 0 apagado, 1 aceso, 2 respira, 3 pisca | LED do botão Power | `OK` |
| `BL brilho` | 0–255 | Luz de fundo da tela | `OK` |

Tamanhos de texto (fonte 5 × 7 do Nano, 6 × 8 px por letra com o espaço):

| tam | Letra (px) | Letras por linha |
|---|---|---|
| 1 | 6 × 8 | 40 |
| 2 | 12 × 16 | 20 |
| 3 | 18 × 24 | 13 |
| 4 | 24 × 32 | 10 |

Só ASCII: o servidor tira os acentos (`ascii_seguro`) antes de mandar.

## Nano → servidor

| Mensagem | Quando |
|---|---|
| `HELLO fw=0.1.0 proto=1 rfid=92` | Ao ligar; em resposta ao `INFO`; ao voltar do "sem sinal". O servidor redesenha tudo. `rfid` é o registrador de versão do chip em hexa (`91`/`92` legítimo, `88` clone, `0` ou `FF` sem leitor) |
| `OK` | Comando executado |
| `ERR comando` / `ERR args` / `ERR linha_longa` | Comando desconhecido / argumento inválido / linha longa demais |
| `HB` | Resposta ao `HB` |
| `CARD 04A1B2C3` | Cartão novo no leitor (UID em hexa, até 10 bytes). O mesmo cartão não se repete antes de 2 s |
| `RFID perdido` / `RFID reiniciado` / `RFID ok` | O leitor parou de responder; parou e voltou com o reinício; voltou depois de ausente |

`HELLO`, `CARD` e `RFID` chegam a qualquer momento, inclusive enquanto o servidor
espera a resposta de um comando: o servidor separa respostas de eventos.

## Exemplo

```
Nano: HELLO fw=0.1.0 proto=1 rfid=92
Serv: CLS 0000                         Nano: OK
Serv: BL 200                           Nano: OK
Serv: LED 1                            Nano: OK
Serv: HB                               Nano: HB
Serv: TXT 60 4 FFFF C 14:05            Nano: OK
Serv: BAR 122 8 23 07E0                Nano: OK
Nano: CARD 04A1B2C3
Serv: BEEP 1 80 0                      Nano: OK
```
