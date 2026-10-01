#!/usr/bin/env python3
"""Module 3's single authorized Modbus/TCP write.

This client is intentionally locked to the updated traffic-lab topology:
PLC-US35 at 172.16.0.3:502, unit ID 2, FC 06, register 3, value 1.
It does not provide discovery, arbitrary targets, or arbitrary writes.
"""

import socket
import struct
import sys

PLC_HOST = "172.16.0.3"
PLC_PORT = 502
UNIT_ID = 2
REGISTER = 3
VALUE = 1
TRANSACTION_ID = 0x0015


def receive_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("PLC closed the connection early")
        data += chunk
    return data


def main():
    pdu = struct.pack(">BHH", 0x06, REGISTER, VALUE)
    request = struct.pack(">HHHB", TRANSACTION_ID, 0, len(pdu) + 1, UNIT_ID) + pdu

    print(
        f"Sending authorized write: {PLC_HOST}:{PLC_PORT}, unit {UNIT_ID}, "
        f"FC 06, register {REGISTER}, value {VALUE}"
    )
    with socket.create_connection((PLC_HOST, PLC_PORT), timeout=5) as sock:
        sock.sendall(request)
        header = receive_exact(sock, 7)
        response_tid, protocol_id, length, response_unit = struct.unpack(">HHHB", header)
        response_pdu = receive_exact(sock, length - 1)

    if protocol_id != 0 or response_tid != TRANSACTION_ID or response_unit != UNIT_ID:
        raise RuntimeError("Response did not match the authorized request")
    if response_pdu[0] & 0x80:
        raise RuntimeError(f"PLC returned Modbus exception 0x{response_pdu[1]:02X}")
    if response_pdu != pdu:
        raise RuntimeError("PLC did not echo the FC 06 write")
    print("Success: PLC echoed the authorized FC 06 write.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ConnectionError) as error:
        print(f"Write not confirmed: {error}", file=sys.stderr)
        sys.exit(1)
