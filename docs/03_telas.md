# 03 · Telas

**Revisão S1 (25/11/2026).** Código: `servidor/src/eduserver_painel/telas.py` (status e
desligando) e `firmware/src/tela.cpp` (aguardando e sem sinal).

Para ver a tela sem o Nano: `uv run eduserver-painel simular tela.png` (o desenho é
aproximado: a fonte do PC não é a do Nano).

## Status (a tela normal)

```
 y    ┌────────────────────────────────────────┐
   6  │               eduserver                │ nome da máquina, tam 2, ciano
  32  │             192.168.0.10               │ IP, tam 2, branco
  60  │                 14:05                  │ hora, tam 4, branco
 104  │ CPU     23 %                           │ tam 2
 122  │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │ barra: verde < 70 %, amarela < 90 %, vermelha
 136  │ RAM     45 %                           │
 154  │ ███████████████░░░░░░░░░░░░░░░░░░░░░   │
 168  │ DISCO   61 %                           │
 186  │ ████████████████████░░░░░░░░░░░░░░░░   │
 200  │ TEMP    52 C                           │ verde < 60, amarela < 75, vermelha (e bipe)
 224  │          no ar ha 3d 04h               │ tam 1, cinza; ou "cartao 04A1B2C3" por 5 s
      └────────────────────────────────────────┘
```

O servidor só manda o que mudou: num ciclo normal, a CPU e, a cada minuto, a hora.

## Telas do próprio Nano

| Tela | Quando | LED |
|---|---|---|
| "eduServer / aguardando o servidor..." | Nano acabou de ligar | respira |
| "SEM SINAL / o servidor nao responde" | 6 s sem nenhuma linha do servidor | apagado |
| "desligando / ate logo" (mandada pelo servidor) | O serviço está parando (desligamento) | respira |

## Bipes

| Padrão | Quando |
|---|---|
| 1 curto (80 ms) | Cartão lido |
| 3 curtos (150/150 ms) | Temperatura ≥ limite de alerta (no máximo 1 por minuto) |

## Cartão (versão 1)

Por enquanto o cartão só é **mostrado** no rodapé por 5 s, **bipa** e fica **registrado**
no log (`evento=cartao uid=…`). As ações do cartão serão decididas depois, com o
usuário.
