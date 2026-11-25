# eduServer Box, painel frontal: instruções para o Claude

Software do painel frontal (plano A) do eduServer Box. O projeto da caixa fica no
repositório irmão `server_box` (`../server_box`), que é a fonte das decisões de
hardware: `docs/04_interfaces_eletricas.md` (pinagem, documento mestre),
`docs/06_decisoes_de_hardware.md` (HW-6 a HW-8) e `docs/00_ESTADO_DO_PROJETO.md`
(decisão 36: este repositório).

## Leia primeiro
1. `README.md` e `docs/00_arquitetura.md`.
2. `docs/01_protocolo.md`: contrato entre o servidor e o Nano. Mudou um comando: sobe
   a versão (`PROTO_VERSAO` em `firmware/include/config.h` e em
   `servidor/src/eduserver_painel/protocolo.py`) e muda os dois lados e os testes.
3. `docs/02_pinagem.md`: cópia da pinagem do `server_box/docs/04` §4a. Mudou lá, muda
   aqui e no `firmware/include/pinos.h`.

## Regras
- **Fale com o usuário em português do Brasil.** Código, comentários e documentos em
  português.
- **Commits só com as credenciais do usuário.** Nunca adicione `Co-Authored-By` do
  Claude nem outra atribuição ao Claude em commit ou PR.
- **Nada liga na placa-mãe além de uma porta USB.** O Nano nunca toca no botão Power
  nem em pino da placa-mãe (server_box HW-1). Nunca recomende soldar na placa-mãe.
- Tela e RFID são de 3,3 V: todo sinal que sai do Nano para eles passa por divisor
  (470 Ω + 1 kΩ), e a alimentação vem do regulador externo, nunca do 3V3 do Nano.
- O usuário é iniciante em eletrônica e solda: instruções de ligação **visuais**, passo
  a passo, com esquema em ASCII.
- **Lógica fica no servidor.** O firmware só desenha, lê o cartão, bipa e acende o LED.
  Flash e RAM do Nano: conferir o tamanho a cada mudança (`pio run -e painel`).
- O cartão RFID (MIFARE) não é segurança: dá para copiar. Ação perigosa por cartão
  (desligar o servidor) fica desligada por padrão. As ações do cartão ainda serão
  decididas com o usuário; por enquanto o cartão só é mostrado e registrado.
- Testes sem instalar outro sistema: o serviço roda no Windows; o Linux é coberto pelo
  CI (GitHub Actions) e pelo próprio servidor (Lubuntu).

## Comandos
- Firmware: `cd firmware && uvx --python 3.11 --from platformio pio run` (todos os
  ambientes: `-e painel -e painel_antigo -e t_tela -e t_rfid -e t_buzzer -e t_led`).
- Testes do protocolo no PC: `pio test -e nativo` (precisa de gcc; no Windows sem gcc,
  compile com `uvx --from ziglang python -m ziglang c++`).
- Servidor: `cd servidor && uv run pytest -q`, `uv run ruff check .`,
  `uv run ruff format .` (rode depois de editar).
