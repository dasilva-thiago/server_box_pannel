#!/usr/bin/env bash
# Instala o serviço do painel no servidor (Lubuntu/Ubuntu). Rodar como root, da raiz
# do repositório:   sudo bash servidor/deploy/instalar.sh
#
# Pode rodar de novo para atualizar: a configuração existente não é sobrescrita.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Rode com sudo: sudo bash servidor/deploy/instalar.sh" >&2
    exit 1
fi

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVIDOR="$(dirname "$AQUI")"
DESTINO=/opt/eduserver-painel
CONFIG=/etc/eduserver-painel
USUARIO=eduserver-painel

echo "== 1. Python"
if ! python3 -c 'import venv, ensurepip' 2>/dev/null; then
    echo "Falta o pacote python3-venv. Instale com:  sudo apt install python3-venv" >&2
    exit 1
fi

echo "== 2. brltty (programa de leitor braille que toma a porta do CH340 no Ubuntu)"
if dpkg -s brltty >/dev/null 2>&1; then
    echo "AVISO: o brltty está instalado e costuma sequestrar o CH340 do Nano"
    echo "       (a porta /dev/ttyUSB0 aparece e some). Se você não usa leitor braille:"
    echo "       sudo apt remove brltty"
fi

echo "== 3. Usuário do serviço ($USUARIO, sem login, no grupo dialout)"
if ! id "$USUARIO" >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin --groups dialout "$USUARIO"
fi

echo "== 4. Programa em $DESTINO"
mkdir -p "$DESTINO"
python3 -m venv "$DESTINO/venv"
"$DESTINO/venv/bin/pip" install --quiet --upgrade pip
"$DESTINO/venv/bin/pip" install --quiet "$SERVIDOR"

echo "== 5. Configuração em $CONFIG"
mkdir -p "$CONFIG"
if [[ ! -f "$CONFIG/config.toml" ]]; then
    install -m 0644 "$AQUI/config.exemplo.toml" "$CONFIG/config.toml"
else
    echo "   (já existe, mantida)"
fi

echo "== 6. Regra udev e serviço"
install -m 0644 "$AQUI/99-eduserver-painel.rules" /etc/udev/rules.d/
udevadm control --reload-rules
udevadm trigger --subsystem-match=tty
install -m 0644 "$AQUI/eduserver-painel.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now eduserver-painel
systemctl restart eduserver-painel

echo
echo "Pronto. Acompanhe com:  journalctl -u eduserver-painel -f"
