#!/bin/sh
set -eu

interface="${INTERFACE:-eth0}"
ip link set "$interface" up

if [ -n "${IP_ADDRESS:-}" ]; then
    ip addr flush dev "$interface"
    ip addr add "${IP_ADDRESS}/${PREFIX_LENGTH:-24}" dev "$interface"
fi

exec "$@"
