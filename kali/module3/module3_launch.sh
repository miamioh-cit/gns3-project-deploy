#!/usr/bin/env bash
# Module 3 launcher: prepares the isolated Kali lab interface and performs
# exactly one authorized Modbus/TCP write. Do not add target/value arguments.

set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
    echo "Administrator approval is required to configure the lab IP address."
    exec sudo -E bash "$0"
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

ip link set eth0 up
ip addr flush dev eth0
ip addr add 172.16.0.250/24 dev eth0

echo "Kali is ready on 172.16.0.250/24."
exec python3 "$SCRIPT_DIR/module3_kali_authorized_write.py"
