#!/usr/bin/env python3
"""
Build the CIT 480-2 Little Miami Water Authority (LMWA) GNS3 project.

Based on the LMWA-DOC-002 v1.0 architecture:
Four distinct PLC zones (Intake, Filtration, Dosing, Storage) communicate
with field sensors over simulated Modbus TCP. The PLCs uplink to a central
OT/SCADA network (10.10.200.0/24) where the central HMI, Historian, and
Engineering Workstation reside.
"""

import logging
import sys
import time

import requests
from gns3fy import Gns3Connector, Project

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

LAB_NAME = "CIT480 Little Miami Water Authority"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "water"
CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
EDGE_SWITCH_TEMPLATE = "Ethernet switch"
OPERATIONS_SUBNET = "10.10.200.0/24"

REQUIRED_TEMPLATES = [
    {
        "name": "generic-sensor",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-sensor:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
    {
        "name": "generic-plc",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-plc:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
    {
        "name": "generic-hmi",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-hmi:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
    {
        "name": "generic-scada",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-scada:latest",
        "adapters": 11,
        "console_type": "http",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
]

# Field IPs are simulated local networks behind the PLCs
WATER_ZONES = [
    {
        "name": "INTAKE",
        "label": "Raw Water Intake",
        "field_vlan": "Vlan-01",
        "subnet": "192.168.1.0/24",
        "plc": "PLC-1",
        "plc_field_ip": "192.168.1.5",
        "plc_ops_ip": "10.10.200.11",
        "core_port": "Ethernet0",
        "x": -540,
        "sensors": [
            ("FLOW-40001", "192.168.1.1"),
            ("PUMP-40002", "192.168.1.2"),
        ],
    },
    {
        "name": "FILTRATION",
        "label": "Filtration",
        "field_vlan": "Vlan-02",
        "subnet": "192.168.2.0/24",
        "plc": "PLC-2",
        "plc_field_ip": "192.168.2.5",
        "plc_ops_ip": "10.10.200.12",
        "core_port": "Ethernet1",
        "x": -180,
        "sensors": [
            ("DP-40003", "192.168.2.1"),
            ("TURBIDITY-40004", "192.168.2.2"),
        ],
    },
    {
        "name": "DOSING",
        "label": "Chemical Dosing",
        "field_vlan": "Vlan-03",
        "subnet": "192.168.3.0/24",
        "plc": "PLC-3",
        "plc_field_ip": "192.168.3.5",
        "plc_ops_ip": "10.10.200.13",
        "core_port": "Ethernet2",
        "x": 180,
        "sensors": [
            ("RATE-40005", "192.168.3.1"),
            ("CHLORINE-40006", "192.168.3.2"),
        ],
    },
    {
        "name": "STORAGE",
        "label": "Storage and Distribution",
        "field_vlan": "Vlan-04",
        "subnet": "192.168.4.0/24",
        "plc": "PLC-4",
        "plc_field_ip": "192.168.4.5",
        "plc_ops_ip": "10.10.200.14",
        "core_port": "Ethernet3",
        "x": 540,
        "sensors": [
            ("LEVEL-40007", "192.168.4.1"),
            ("DPUMP-40008", "192.168.4.2"),
            ("PRESS-40009", "192.168.4.3"),
            ("ALARM-40010", "192.168.4.4"),
        ],
    },
]

def read_server_urls():
    """Read GNS3 server last octets from the datastore file."""
    try:
        with open(DATASTORE_FILE, "r", encoding="utf-8") as file_obj:
            content = file_obj.read().strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required file '{DATASTORE_FILE}' was not found.") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not read '{DATASTORE_FILE}': {exc}") from exc

    last_octets = []
    for item in content.split(","):
        item = item.strip()
        if not item:
            continue
        if not item.isdigit():
            raise RuntimeError(
                f"Invalid datastore entry '{item}'. Expected comma-separated last octets."
            )
        last_octets.append(int(item))

    if not last_octets:
        raise RuntimeError(f"No valid GNS3 server last octets found in '{DATASTORE_FILE}'.")

    return [f"{BASE_IP}{octet}:80" for octet in last_octets]

def require_http_success(response, action):
    """Raise an error that includes the exact HTTP failure."""
    if response.status_code not in (200, 201):
        raise RuntimeError(f"{action} failed: HTTP {response.status_code}: {response.text}")

def ensure_10_port_switch(server_url):
    """Ensure the GNS3 server has a reusable local Ethernet switch with 10 ports."""
    template_name = CORE_SWITCH_TEMPLATE

    try:
        response = requests.get(f"{server_url}/v2/templates", auth=(GNS3_USER, GNS3_PW))
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not list templates on {server_url}: {exc}") from exc

    existing = next((t for t in response.json() if t.get("name") == template_name), None)
    if existing:
        return

    ports = [
        {"name": f"Ethernet{p}", "port_number": p, "type": "access", "vlan": 1}
        for p in range(10)
    ]
    switch_template = {
        "name": template_name,
        "template_type": "ethernet_switch",
        "category": "switch",
        "compute_id": "local",
        "default_name_format": "{name}-{0}",
        "symbol": ":/symbols/ethernet_switch.svg",
        "builtin": False,
        "ports_mapping": ports,
    }

    try:
        response = requests.post(f"{server_url}/v2/templates", json=switch_template, auth=(GNS3_USER, GNS3_PW))
        require_http_success(response, f"Create template '{template_name}' on {server_url}")
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error creating '{template_name}' on {server_url}: {exc}") from exc

def ensure_required_templates(server, server_url):
    """Register or update the Docker templates required by this scenario."""
    try:
        available_templates = server.get_templates()
    except Exception as exc:
        raise RuntimeError(f"Could not list GNS3 templates on {server_url}: {exc}") from exc

    templates_by_name = {template["name"]: template for template in available_templates}
    
