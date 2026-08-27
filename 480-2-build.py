#!/usr/bin/env python3
"""480-2 GNS3 deployment entry point.

Combines the generic JSON-driven GNS3 project scaffold with the proven
wastewater treatment deployment path used by the earlier laboratory build.

Configuration is supplied through environment variables where possible so
private GNS3 infrastructure and credentials are not stored in source control.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import requests
from gns3fy import Gns3Connector, Project


def api(session: requests.Session, method: str, base_url: str, path: str, **kwargs):
    """Make a GNS3 API request and return decoded JSON when present."""
    response = session.request(
        method,
        f"{base_url.rstrip('/')}{path}",
        timeout=30,
        **kwargs,
    )
    response.raise_for_status()
    if response.text:
        return response.json()
    return None


def find_template(session: requests.Session, base_url: str, name: str) -> str:
    """Find a GNS3 template ID by template name."""
    templates = api(session, "GET", base_url, "/v2/templates")
    for template in templates:
        if template.get("name") == name:
            return template["template_id"]
    raise SystemExit(f"GNS3 template not found: {name}")


def symbol_filename_for_node(node: dict) -> str:
    """Choose a diagram symbol based on the node definition."""
    name = node.get("name", "").lower()
    template = node.get("template", "").lower()
    env = node.get("env") or {}
    mode = env.get("NODE_MODE", "").lower()

    if "switch" in name or "switch" in template:
        return "switch.svg"
    if name.startswith("plc") or mode == "plc":
        return "plc.svg"
    if "hmi" in name or mode == "hmi":
        return "hmi.svg"
    if "historian" in name or "collector" in name or mode == "historian":
        return "historian.svg"
    if "router" in name or "fw" in name or "firewall" in name:
        return "firewall.svg"
    if "zeek" in name or "suricata" in name or "monitoring" in template:
        return "monitoring.svg"
    return "ot_node.svg"


def symbol_path(prefix: str | None, node: dict) -> str | None:
    if not prefix:
        return None
    return f"{prefix.rstrip('/')}/{symbol_filename_for_node(node)}"


def build_generic_topology(topology_path: Path, gns3_url: str, symbol_prefix: str | None = None) -> None:
    """Build a JSON-defined topology using the generic GNS3 API scaffold."""
    topology = json.loads(topology_path.read_text(encoding="utf-8"))
    session = requests.Session()

    if GNS3_USER and GNS3_PW:
        session.auth = (GNS3_USER, GNS3_PW)

    project = api(
        session,
        "POST",
        gns3_url,
        "/v2/projects",
        json={"name": topology["project_name"]},
    )
    project_id = project["project_id"]
    print(f"created project {project['name']} {project_id}")

    node_ids: dict[str, str] = {}

    for node in topology.get("nodes", []):
        template_name = node.get("template", "ics-node")
        template_id = find_template(session, gns3_url, template_name)

        payload = {
            "name": node["name"],
            "template_id": template_id,
            "x": 100 + 180 * (len(node_ids) % 4),
            "y": 100 + 120 * (len(node_ids) // 4),
        }

        node_symbol = symbol_path(symbol_prefix, node)
        if node_symbol:
            payload["symbol"] = node_symbol

        created = api(
            session,
            "POST",
            gns3_url,
            f"/v2/projects/{project_id}/templates/{template_id}",
            json=payload,
        )

        node_ids[node["name"]] = created["node_id"]
        print(f"created node {node['name']}")

    next_port: dict[str, int] = {name: 0 for name in node_ids}

    for left, right in topology.get("links", []):
        if left not in node_ids or right not in node_ids:
            print(f"skipping link {left}--{right}: missing node")
            continue

        left_port = next_port[left]
        right_port = next_port[right]
        next_port[left] += 1
        next_port[right] += 1

        payload = {
            "nodes": [
                {
                    "node_id": node_ids[left],
                    "adapter_number": 0,
                    "port_number": left_port,
                },
                {
                    "node_id": node_ids[right],
                    "adapter_number": 0,
                    "port_number": right_port,
                },
            ]
        }

        api(
            session,
            "POST",
            gns3_url,
            f"/v2/projects/{project_id}/links",
            json=payload,
        )
        print(f"linked {left}:{left_port} -- {right}:{right_port}")

    print("Project scaffold created.")


# ============================================================
# PUBLIC CONFIGURATION
# ============================================================

LAB_NAME = os.getenv("ICS_LAB_NAME", "SCADA-Wastewater")
GNS3_URL = os.getenv("GNS3_URL", "http://127.0.0.1:3080")
GNS3_USER = os.getenv("GNS3_USER", "")
GNS3_PW = os.getenv("GNS3_PASSWORD", "")

SERVER_URLS = [
    url.strip()
    for url in os.getenv("GNS3_SERVER_URLS", "").split(",")
    if url.strip()
]

if not SERVER_URLS:
    SERVER_URLS = [GNS3_URL]


# ============================================================
# WASTEWATER DEPLOYMENT
# ============================================================

def build_wastewater() -> None:
    """Run the proven wastewater deployment path."""

    # Add missing template payloads for Docker nodes
    # ==========================================
    # REQUIRED TEMPLATES
    # ==========================================



    REQUIRED_TEMPLATES = [
        # Required Docker templates
        {
            "name": "generic-sensor",
            "template_type": "docker",
            "category": "guest",
            "image": "wtaylor8/generic-sensor:latest",
            "adapters": 5,
            "console_type": "telnet",
            "environment": "SCENARIO=wastewater",
            "default_name_format": "{name}-{0}",
            "compute_id": "local",
            "symbol": ":/symbols/docker_guest.svg"
        },
        {
            "name": "generic-plc",
            "template_type": "docker",
            "category": "guest",
            "image": "wtaylor8/generic-plc:latest",
            "adapters": 5,
            "console_type": "telnet",
            "environment": "SCENARIO=wastewater",
            "default_name_format": "{name}-{0}",
            "compute_id": "local",
            "symbol": ":/symbols/docker_guest.svg"
        },
        {
            "name": "generic-hmi",
            "template_type": "docker",
            "category": "guest",
            "image": "wtaylor8/generic-hmi:latest",
            "adapters": 5,
            "console_type": "telnet",
            "environment": "SCENARIO=wastewater",
            "default_name_format": "{name}-{0}",
            "compute_id": "local",
            "symbol": ":/symbols/docker_guest.svg"
        },
        {
            "name": "generic-scada",
            "template_type": "docker",
            "category": "guest",
            "image": "wtaylor8/generic-scada:latest",
            "adapters": 11,
            "console_type": "http",
            "environment": "SCENARIO=wastewater",
            "default_name_format": "{name}-{0}",
            "compute_id": "local",
            "symbol": ":/symbols/docker_guest.svg"
        }
    ]

    # =========================================================
    # CREATE 10-PORT LOCAL ETHERNET SWITCH TEMPLATE
    # =========================================================
    def ensure_10_port_switch(server_url):
        """
        Ensure that the GNS3 server has a local Ethernet switch
        template with 10 ports.
        """

        template_name = "Ethernet-Switch-10P"

        try:
            response = requests.get(
                f"{server_url}/v2/templates",
                auth=(GNS3_USER, GNS3_PW)
            )

            response.raise_for_status()

            templates = response.json()

            existing = next(
                (
                    t for t in templates
                    if t.get("name") == template_name
                ),
                None
            )

            if existing:
                print(
                    f"[OK] Template '{template_name}' already exists "
                    f"on {server_url}"
                )
                return

            print(
                f"[INFO] Creating '{template_name}' on {server_url}..."
            )

            ports = []

            for port_number in range(10):
                ports.append({
                    "name": f"Ethernet{port_number}",
                    "port_number": port_number,
                    "type": "access",
                    "vlan": 1
                })

            switch_template = {
                "name": template_name,
                "template_type": "ethernet_switch",
                "category": "switch",
                "compute_id": "local",
                "default_name_format": "{name}-{0}",
                "symbol": ":/symbols/ethernet_switch.svg",
                "builtin": False,
                "ports_mapping": ports
            }

            response = requests.post(
                f"{server_url}/v2/templates",
                json=switch_template,
                auth=(GNS3_USER, GNS3_PW)
            )

            if response.status_code not in (200, 201):
                raise RuntimeError(
                    f"Failed to create {template_name}: "
                    f"HTTP {response.status_code}: "
                    f"{response.text}"
                )

            print(
                f"[OK] Created '{template_name}' "
                f"with {len(ports)} ports"
            )

        except Exception as e:
            raise RuntimeError(
                f"Could not ensure 10-port switch template "
                f"on {server_url}: {e}"
            )

    # ==========================================
    # REGISTER TEMPLATES
    # ==========================================
    for SERVER_URL in SERVER_URLS:
        # Pass credentials to Gns3Connector
        server = Gns3Connector(
            url=SERVER_URL,
            user=GNS3_USER,
            cred=GNS3_PW
        )

        ensure_10_port_switch(SERVER_URL)
        
        try:
            available_templates = [t["name"] for t in server.get_templates()]
        except Exception as e:
            print(f"[ERROR] Could not connect to GNS3 server at {SERVER_URL}: {e}")
            continue

        # REGISTER MISSING TEMPLATES ON TARGET SERVER FIRST
        for tmpl in REQUIRED_TEMPLATES:
            if tmpl["name"] not in available_templates:
                print(f"Registering missing template '{tmpl['name']}' on {SERVER_URL}...")
                try:
                    # Register the template using the configured GNS3 credentials
                    res = requests.post(
                        f"{SERVER_URL}/v2/templates", 
                        json=tmpl, 
                        auth=(GNS3_USER, GNS3_PW)
                    )
                    if res.status_code in [200, 201]:
                        print(f"[OK] Successfully registered '{tmpl['name']}'")
                    else:
                        print(f"[FAIL] Server rejected '{tmpl['name']}': HTTP {res.status_code} - {res.text}")
                except Exception as req_err:
                    print(f"[FAIL] Network error registering '{tmpl['name']}': {req_err}")

        # Open the existing project when available.
        projects = server.get_projects()
        existing_lab = next((p for p in projects if p["name"] == LAB_NAME), None)

        if existing_lab:
            lab = Project(project_id=existing_lab["project_id"], connector=server)
            lab.get()
            lab.open()
        else:
            lab = Project(name=LAB_NAME, connector=server)
            lab.create()
            lab.open()
        
        # ... Node creation code follows (FT-101, LT-101, etc.) ...
    # =========================================================
    # NETWORK CONFIGURATION HELPERS
    # =========================================================

    def configure_interfaces(node, config):
        """
        Write /etc/network/interfaces to a Docker node and restart it
        so the configuration is applied.
        """
        try:
            node.get()

            status = getattr(node.status, "value", str(node.status)).lower()
            was_running = status == "started"

            if was_running:
                node.stop()

            node.write_file(
                path="/etc/network/interfaces",
                data=config.strip() + "\n"
            )

            if was_running:
                node.start()

            print(f"[OK] Configured network for {node.name}")

        except Exception as e:
            print(f"[FAIL] Network configuration for {node.name}: {e}")

    def configure_kali(node):
        """
        Configure a fresh Kali VM with a persistent static IPv4 address
        using NetworkManager.
        """
        try:
            node.get()

            status = getattr(node.status, "value", str(node.status)).lower()

            if status != "started":
                node.start()

            import time
            time.sleep(8)

            print("[KALI TEST] Running nmcli device status...")
            result = node.execute("nmcli device status")
            print(f"[KALI TEST] nmcli result: {result}")

            for attempt in range(30):
                try:
                    result = node.execute("nmcli device status")

                    if "eth0" in str(result):
                        print(f"[OK] Kali eth0 detected after {attempt + 1} attempts")
                        break

                except Exception:
                    pass

                time.sleep(2)

            else:
                raise RuntimeError("Kali eth0 did not become available after 60 seconds")

            # Remove our profile if a previous deployment somehow left one behind.
            node.execute(
                "nmcli connection delete kali-eth0 || true"
            )

            # Create the working NetworkManager profile.
            node.execute(
                "nmcli connection add "
                "type ethernet "
                "ifname eth0 "
                "con-name kali-eth0 "
                "ipv4.method manual "
                "ipv4.addresses 172.16.0.250/24"
            )

            time.sleep(2)

            # Activate it.
            node.execute(
                "nmcli connection up kali-eth0"
            )

            print("[OK] Kali eth0 configured as 172.16.0.250/24")

        except Exception as e:
            print(f"[FAIL] Kali network configuration: {e}")
    # =========================================================
    # CONTAINER ENVIRONMENT CONFIGURATION
    # =========================================================

    PLC_ENV = {

        "PLC-Influent": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-influent-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.1.0/24",
        },

        "PLC-Primary": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-primary-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.2.0/24",
        },

        "PLC-Aeration": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-aeration-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.3.0/24",
        },

        "PLC-Clarification": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-clarification-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.4.0/24",
        },

        "PLC-Disinfection": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-disinfection-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.5.0/24",
        },

        "PLC-Thickening": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-thickening-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.6.0/24",
        },

        "PLC-Digestion": {
            "SCENARIO": "wastewater",
            "PLC_LOGIC_FILE": "wastewater/plc-digestion-logic.yaml",
            "PLC_SCAN_SUBNETS": "192.168.7.0/24",
        },
    }


    SCADA_ENV = {
        "SCADA_SUBNETS": "172.16.0.0/24",
    }


    # =========================================================
    # WORKING PLC NETWORK CONFIGS
    # =========================================================

    PLC_CONFIGS = {

        "PLC-Influent": """
    auto eth0
    iface eth0 inet static
        address 192.168.1.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.1
        netmask 255.255.255.0
    """,

        "PLC-Primary": """
    auto eth0
    iface eth0 inet static
        address 192.168.2.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.3
        netmask 255.255.255.0
    """,

        "PLC-Aeration": """
    auto eth0
    iface eth0 inet static
        address 192.168.3.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.5
        netmask 255.255.255.0
    """,

        "PLC-Clarification": """
    auto eth0
    iface eth0 inet static
        address 192.168.4.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.7
        netmask 255.255.255.0
    """,

        "PLC-Disinfection": """
    auto eth0
    iface eth0 inet static
        address 192.168.5.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.9
        netmask 255.255.255.0
    """,

        "PLC-Thickening": """
    auto eth0
    iface eth0 inet static
        address 192.168.6.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.11
        netmask 255.255.255.0
    """,

        "PLC-Digestion": """
    auto eth0
    iface eth0 inet static
        address 192.168.7.5
        netmask 255.255.255.0

    auto eth1
    iface eth1 inet static
        address 172.16.0.13
        netmask 255.255.255.0
    """
    }


    # =========================================================
    # WORKING HMI NETWORK CONFIGS
    # =========================================================

    HMI_CONFIGS = {

        "HMI-Influent": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.2
        netmask 255.255.255.0
    """,

        "HMI-Primary": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.4
        netmask 255.255.255.0
    """,

        "HMI-Aeration": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.6
        netmask 255.255.255.0
    """,

        "HMI-Clarification": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.8
        netmask 255.255.255.0
    """,

        "HMI-Disinfection": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.10
        netmask 255.255.255.0
    """,

        "HMI-Thickening": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.12
        netmask 255.255.255.0
    """,

        "HMI-Digestion": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.14
        netmask 255.255.255.0
    """
    }


    # =========================================================
    # SCADA + CORE CONFIGS
    # =========================================================

    SPECIAL_CONFIGS = {

        "scada-server": """
    auto eth0
    iface eth0 inet static
        address 172.16.0.200
        netmask 255.255.255.0
    """
    }


    # =========================================================
    # KALI NETWORK CONFIG
    # =========================================================

    KALI_CONFIG = """
    auto eth0
    iface eth0 inet static
        address 172.16.0.250
        netmask 255.255.255.0
    """

    # =========================================================
    # WORKING FIELD SENSOR CONFIGS
    # =========================================================

    SENSOR_IPS = {

        # -------------------------
        # VLAN 01 / 192.168.1.0/24
        # -------------------------
        "FT-101": "192.168.1.1",
        "LT-101": "192.168.1.2",
        "DP-101": "192.168.1.3",
        "P-101": "192.168.1.4",

        # -------------------------
        # VLAN 02 / 192.168.2.0/24
        # -------------------------
        "FT-201": "192.168.2.1",
        "LT-201": "192.168.2.2",
        "DP-201": "192.168.2.3",
        "MV-201": "192.168.2.4",

        # -------------------------
        # VLAN 03 / 192.168.3.0/24
        # -------------------------
        "DO-301": "192.168.3.1",
        "FT-301": "192.168.3.2",
        "MLSS-301": "192.168.3.3",
        "SV-301": "192.168.3.4",

        # -------------------------
        # VLAN 04 / 192.168.4.0/24
        # -------------------------
        "FT-401": "192.168.4.1",
        "LT-401": "192.168.4.2",
        "TU-401": "192.168.4.3",
        "DL-401": "192.168.4.4",

        # -------------------------
        # VLAN 05 / 192.168.5.0/24
        # -------------------------
        "CL-501": "192.168.5.1",
        "FT-501": "192.168.5.2",
        "LT-501": "192.168.5.3",
        "AV-501": "192.168.5.4",

        # -------------------------
        # VLAN 06 / 192.168.6.0/24
        # -------------------------
        "LT-601": "192.168.6.1",
        "FT-601": "192.168.6.2",
        "SS-601": "192.168.6.3",
        "P-601": "192.168.6.4",

        # -------------------------
        # VLAN 07 / 192.168.7.0/24
        # -------------------------
        "T-701": "192.168.7.1",
        "PT-701": "192.168.7.2",
        "FT-701": "192.168.7.3",
        "GAS-701": "192.168.7.4",
    }


    SENSOR_CONFIGS = {}

    for tag, ip in SENSOR_IPS.items():
        SENSOR_CONFIGS[tag] = f"""
    auto eth0
    iface eth0 inet static
        address {ip}
        netmask 255.255.255.0
    """


    # =========================================================
    # BUILD PROJECT
    # =========================================================

    for SERVER_URL in SERVER_URLS:

        server = Gns3Connector(
            url=SERVER_URL,
            user=GNS3_USER,
            cred=GNS3_PW
        )

        print(
            "Connecting to GNS3 server to verify uniqueness of Project name",
            server.get_version(),
            "at",
            SERVER_URL
        )


        print("-----------------------------------------------------------------------")
        print(
            f"Project '{LAB_NAME}' created on {SERVER_URL}. "
            "Nodes are being created."
        )
        print("-----------------------------------------------------------------------")
        print("Please wait until script runs before entering the project in GNS3!")
        print("-----------------------------------------------------------------------")

        lab = Project(name=LAB_NAME, connector=server)
        lab.get()
        lab.open()

        available_templates = [
            template["name"]
            for template in server.get_templates()
        ]

        logging.debug(
            f"Available Templates: {available_templates}"
        )

        available_templates = [
            template["name"]
            for template in server.get_templates()
        ]

        logging.debug(
            f"Available Templates: {available_templates}"
        )

        # =====================================================
        # TOP FIELD DEVICES
        # =====================================================

        try:
            lab.create_node(
                name="FT-101",
                template="generic-sensor",
                x=-575,
                y=-625
            )
            sw1 = lab.get_node("FT-101")
        except Exception as e:
            print(f"Error creating FT-101: {e}")

        try:
            lab.create_node(
                name="LT-101",
                template="generic-sensor",
                x=-483,
                y=-628
            )
            sw2 = lab.get_node("LT-101")
        except Exception as e:
            print(f"Error creating LT-101: {e}")

        lab.create_node(
            name="DP-101",
            template="generic-sensor",
            x=-380,
            y=-619
        )
        sw3 = lab.get_node("DP-101")

        lab.create_node(
            name="P-101",
            template="generic-sensor",
            x=-299,
            y=-623
        )
        sw4 = lab.get_node("P-101")

        lab.create_node(
            name="FT-201",
            template="generic-sensor",
            x=-194,
            y=-627
        )
        sw5 = lab.get_node("FT-201")

        lab.create_node(
            name="LT-201",
            template="generic-sensor",
            x=-109,
            y=-632
        )
        sw6 = lab.get_node("LT-201")

        lab.create_node(
            name="DP-201",
            template="generic-sensor",
            x=-25,
            y=-618
        )
        sw7 = lab.get_node("DP-201")

        lab.create_node(
            name="MV-201",
            template="generic-sensor",
            x=58,
            y=-620
        )
        sw8 = lab.get_node("MV-201")

        lab.create_node(
            name="DO-301",
            template="generic-sensor",
            x=177,
            y=-606
        )
        sw9 = lab.get_node("DO-301")

        lab.create_node(
            name="FT-301",
            template="generic-sensor",
            x=254,
            y=-606
        )
        sw10 = lab.get_node("FT-301")

        lab.create_node(
            name="MLSS-301",
            template="generic-sensor",
            x=330,
            y=-599
        )
        sw11 = lab.get_node("MLSS-301")

        lab.create_node(
            name="SV-301",
            template="generic-sensor",
            x=406,
            y=-604
        )
        sw12 = lab.get_node("SV-301")

        lab.create_node(
            name="FT-401",
            template="generic-sensor",
            x=596,
            y=-578
        )
        sw13 = lab.get_node("FT-401")

        lab.create_node(
            name="LT-401",
            template="generic-sensor",
            x=687,
            y=-575
        )
        sw14 = lab.get_node("LT-401")

        lab.create_node(
            name="TU-401",
            template="generic-sensor",
            x=786,
            y=-577
        )
        sw15 = lab.get_node("TU-401")

        lab.create_node(
            name="DL-401",
            template="generic-sensor",
            x=892,
            y=-575
        )
        sw16 = lab.get_node("DL-401")


        # =====================================================
        # TOP VLANS
        # =====================================================

        lab.create_node(
            name="Vlan-01",
            template="Ethernet switch",
            x=-424,
            y=-476
        )
        vlan1 = lab.get_node("Vlan-01")

        lab.create_node(
            name="Vlan-02",
            template="Ethernet switch",
            x=-81,
            y=-504
        )
        vlan2 = lab.get_node("Vlan-02")

        lab.create_node(
            name="Vlan-03",
            template="Ethernet switch",
            x=307,
            y=-467
        )
        vlan3 = lab.get_node("Vlan-03")

        lab.create_node(
            name="Vlan-04",
            template="Ethernet switch",
            x=741,
            y=-474
        )
        vlan4 = lab.get_node("Vlan-04")


        # =====================================================
        # HMI / PLC TOP SECTION
        # =====================================================

        lab.create_node(
            name="HMI-Influent",
            template="generic-hmi",
            x=-549,
            y=-316
        )
        HMI1 = lab.get_node("HMI-Influent")

        lab.create_node(
            name="PLC-Influent",
            template="generic-plc",
            x=-419,
            y=-367
        )
        PLC1 = lab.get_node("PLC-Influent")

        lab.create_node(
            name="HMI-Primary",
            template="generic-hmi",
            x=-234,
            y=-362
        )
        HMI2 = lab.get_node("HMI-Primary")

        lab.create_node(
            name="PLC-Primary",
            template="generic-plc",
            x=-76,
            y=-364
        )
        PLC2 = lab.get_node("PLC-Primary")

        lab.create_node(
            name="HMI-Aeration",
            template="generic-hmi",
            x=184,
            y=-365
        )
        HMI3 = lab.get_node("HMI-Aeration")

        lab.create_node(
            name="PLC-Aeration",
            template="generic-plc",
            x=312,
            y=-356
        )
        PLC3 = lab.get_node("PLC-Aeration")

        lab.create_node(
            name="HMI-Clarification",
            template="generic-hmi",
            x=598,
            y=-325
        )
        HMI4 = lab.get_node("HMI-Clarification")

        lab.create_node(
            name="PLC-Clarification",
            template="generic-plc",
            x=746,
            y=-340
        )
        PLC4 = lab.get_node("PLC-Clarification")


        # =====================================================
        # DISTRIBUTION VLANS 10-40
        # =====================================================

        lab.create_node(
            name="Vlan-10",
            template="Ethernet switch",
            x=-511,
            y=-199
        )
        Vlan10 = lab.get_node("Vlan-10")

        lab.create_node(
            name="Vlan-20",
            template="Ethernet switch",
            x=-146,
            y=-243
        )
        Vlan20 = lab.get_node("Vlan-20")

        lab.create_node(
            name="Vlan-30",
            template="Ethernet switch",
            x=236,
            y=-225
        )
        Vlan30 = lab.get_node("Vlan-30")

        lab.create_node(
            name="Vlan-40",
            template="Ethernet switch",
            x=562,
            y=-196
        )
        Vlan40 = lab.get_node("Vlan-40")


        # =====================================================
        # CORE DEVICES
        # =====================================================

        lab.create_node(
            name="Core-Switch",
            template="Ethernet-Switch-10P",
            x=38,
            y=-66
        )

        lab.create_node(
            name="scada-server",
            template="generic-scada",
            x=375,
            y=-82
        )
        scada = lab.get_node("scada-server")

        lab.create_node(
            name="KaliLinux-1",
            template="Kali Linux",
            x=-662,
            y=-48
        )
        KL = lab.get_node("KaliLinux-1")


        # =====================================================
        # BOTTOM PLCS / HMIS
        # =====================================================

        lab.create_node(
            name="Vlan-50",
            template="Ethernet switch",
            x=-412,
            y=99
        )
        Vlan50 = lab.get_node("Vlan-50")

        lab.create_node(
            name="Vlan-60",
            template="Ethernet switch",
            x=-4,
            y=98
        )
        Vlan60 = lab.get_node("Vlan-60")

        lab.create_node(
            name="Vlan-70",
            template="Ethernet switch",
            x=460,
            y=92
        )
        Vlan70 = lab.get_node("Vlan-70")

        lab.create_node(
            name="HMI-Disinfection",
            template="generic-hmi",
            x=-547,
            y=139
        )
        HMI5 = lab.get_node("HMI-Disinfection")

        lab.create_node(
            name="PLC-Disinfection",
            template="generic-plc",
            x=-408,
            y=194
        )
        PLC5 = lab.get_node("PLC-Disinfection")

        lab.create_node(
            name="HMI-Thickening",
            template="generic-hmi",
            x=-154,
            y=218
        )
        HMI6 = lab.get_node("HMI-Thickening")

        lab.create_node(
            name="PLC-Thickening",
            template="generic-plc",
            x=-5,
            y=203
        )
        PLC6 = lab.get_node("PLC-Thickening")

        lab.create_node(
            name="HMI-Digestion",
            template="generic-hmi",
            x=280,
            y=166
        )
        HMI7 = lab.get_node("HMI-Digestion")

        lab.create_node(
            name="PLC-Digestion",
            template="generic-plc",
            x=467,
            y=189
        )
        PLC7 = lab.get_node("PLC-Digestion")


        # =====================================================
        # BOTTOM VLANS
        # =====================================================

        lab.create_node(
            name="Vlan-05",
            template="Ethernet switch",
            x=-410,
            y=317
        )
        Vlan05 = lab.get_node("Vlan-05")

        lab.create_node(
            name="Vlan-06",
            template="Ethernet switch",
            x=-8,
            y=306
        )
        Vlan06 = lab.get_node("Vlan-06")

        lab.create_node(
            name="Vlan-07",
            template="Ethernet switch",
            x=482,
            y=325
        )
        Vlan07 = lab.get_node("Vlan-07")


        # =====================================================
        # BOTTOM FIELD DEVICES
        # =====================================================

        lab.create_node(
            name="CL-501",
            template="generic-sensor",
            x=-564,
            y=402
        )
        sw19 = lab.get_node("CL-501")

        lab.create_node(
            name="FT-501",
            template="generic-sensor",
            x=-474,
            y=403
        )
        sw20 = lab.get_node("FT-501")

        lab.create_node(
            name="LT-501",
            template="generic-sensor",
            x=-325,
            y=402
        )
        sw21 = lab.get_node("LT-501")

        lab.create_node(
            name="AV-501",
            template="generic-sensor",
            x=-231,
            y=402
        )
        sw22 = lab.get_node("AV-501")

        lab.create_node(
            name="LT-601",
            template="generic-sensor",
            x=-107,
            y=398
        )
        sw23 = lab.get_node("LT-601")

        lab.create_node(
            name="FT-601",
            template="generic-sensor",
            x=-24,
            y=397
        )
        sw24 = lab.get_node("FT-601")

        lab.create_node(
            name="SS-601",
            template="generic-sensor",
            x=63,
            y=396
        )
        sw25 = lab.get_node("SS-601")

        lab.create_node(
            name="P-601",
            template="generic-sensor",
            x=154,
            y=394
        )
        sw26 = lab.get_node("P-601")

        lab.create_node(
            name="T-701",
            template="generic-sensor",
            x=344,
            y=410
        )
        sw27 = lab.get_node("T-701")

        lab.create_node(
            name="PT-701",
            template="generic-sensor",
            x=442,
            y=412
        )
        sw28 = lab.get_node("PT-701")

        lab.create_node(
            name="FT-701",
            template="generic-sensor",
            x=548,
            y=410
        )
        sw29 = lab.get_node("FT-701")

        lab.create_node(
            name="GAS-701",
            template="generic-sensor",
            x=647,
            y=412
        )
        sw30 = lab.get_node("GAS-701")


        # =====================================================
        # REFRESH PROJECT INVENTORY
        # =====================================================

        lab.get()


        # =====================================================
        # APPLY WORKING NETWORK CONFIGURATIONS
        # =====================================================

        print("-----------------------------------------------------------------------")
        print("Applying working network configurations...")
        print("-----------------------------------------------------------------------")

        for name, config in PLC_CONFIGS.items():
            node = lab.get_node(name)
            configure_interfaces(node, config)

        for name, config in HMI_CONFIGS.items():
            node = lab.get_node(name)
            configure_interfaces(node, config)

        for name, config in SPECIAL_CONFIGS.items():
            node = lab.get_node(name)
            configure_interfaces(node, config)

        for name, config in SENSOR_CONFIGS.items():
            node = lab.get_node(name)
            configure_interfaces(node, config)

        print("-----------------------------------------------------------------------")
        print("Network configuration complete.")
        print("-----------------------------------------------------------------------")


        # =====================================================
        # REFRESH AGAIN AFTER NODE RESTARTS
        # =====================================================

        lab.get()


        # =====================================================
        # TOP VLAN-01 SEGMENT
        # =====================================================

        try:
            lab.create_link(
                "PLC-Influent",
                "eth0",
                "Vlan-01",
                "Ethernet7"
            )
        except Exception as e:
            print(f"Error linking PLC-Influent to Vlan-01: {e}")

        try:
            lab.create_link(
                "FT-101",
                "eth0",
                "Vlan-01",
                "Ethernet1"
            )
        except Exception as e:
            print(f"Error linking FT-101 to Vlan-01: {e}")

        try:
            lab.create_link(
                "LT-101",
                "eth0",
                "Vlan-01",
                "Ethernet2"
            )
        except Exception as e:
            print(f"Error linking LT-101 to Vlan-01: {e}")

        try:
            lab.create_link(
                "DP-101",
                "eth0",
                "Vlan-01",
                "Ethernet3"
            )
        except Exception as e:
            print(f"Error linking DP-101 to Vlan-01: {e}")

        try:
            lab.create_link(
                "P-101",
                "eth0",
                "Vlan-01",
                "Ethernet4"
            )
        except Exception as e:
            print(f"Error linking P-101 to Vlan-01: {e}")


        # =====================================================
        # TOP VLAN-02 SEGMENT
        # =====================================================

        try:
            lab.create_link(
                "Vlan-02",
                "Ethernet0",
                "PLC-Primary",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-02 to PLC-Primary: {e}")

        try:
            lab.create_link(
                "Vlan-02",
                "Ethernet1",
                "FT-201",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-02 to FT-201: {e}")

        try:
            lab.create_link(
                "Vlan-02",
                "Ethernet2",
                "LT-201",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-02 to LT-201: {e}")

        try:
            lab.create_link(
                "Vlan-02",
                "Ethernet3",
                "DP-201",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-02 to DP-201: {e}")

        try:
            lab.create_link(
                "Vlan-02",
                "Ethernet4",
                "MV-201",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-02 to MV-201: {e}")


        # =====================================================
        # TOP VLAN-03 SEGMENT
        # =====================================================

        try:
            lab.create_link(
                "PLC-Aeration",
                "eth0",
                "Vlan-03",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Aeration to Vlan-03: {e}")

        try:
            lab.create_link(
                "Vlan-03",
                "Ethernet1",
                "DO-301",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-03 to DO-301: {e}")

        try:
            lab.create_link(
                "Vlan-03",
                "Ethernet2",
                "FT-301",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-03 to FT-301: {e}")

        try:
            lab.create_link(
                "Vlan-03",
                "Ethernet3",
                "MLSS-301",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-03 to MLSS-301: {e}")

        try:
            lab.create_link(
                "Vlan-03",
                "Ethernet4",
                "SV-301",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-03 to SV-301: {e}")


        # =====================================================
        # TOP VLAN-04 SEGMENT
        # =====================================================

        try:
            lab.create_link(
                "PLC-Clarification",
                "eth0",
                "Vlan-04",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Clarification to Vlan-04: {e}")

        try:
            lab.create_link(
                "Vlan-04",
                "Ethernet1",
                "FT-401",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-04 to FT-401: {e}")

        try:
            lab.create_link(
                "Vlan-04",
                "Ethernet2",
                "LT-401",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-04 to LT-401: {e}")

        try:
            lab.create_link(
                "Vlan-04",
                "Ethernet3",
                "TU-401",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-04 to TU-401: {e}")

        try:
            lab.create_link(
                "Vlan-04",
                "Ethernet4",
                "DL-401",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-04 to DL-401: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-10
        # =====================================================

        try:
            lab.create_link(
                "PLC-Influent",
                "eth1",
                "Vlan-10",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Influent to Vlan-10: {e}")

        try:
            lab.create_link(
                "Vlan-10",
                "Ethernet2",
                "HMI-Influent",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-10 to HMI-Influent: {e}")

        try:
            lab.create_link(
                "Vlan-10",
                "Ethernet7",
                "Core-Switch",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking Vlan-10 to Core-Switch: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-20
        # =====================================================

        try:
            lab.create_link(
                "PLC-Primary",
                "eth1",
                "Vlan-20",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Primary to Vlan-20: {e}")

        try:
            lab.create_link(
                "Vlan-20",
                "Ethernet1",
                "HMI-Primary",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking HMI-Primary to Vlan-20: {e}")

        try:
            lab.create_link(
                "Vlan-20",
                "Ethernet7",
                "Core-Switch",
                "Ethernet1"
            )
        except Exception as e:
            print(f"Error linking Vlan-20 to Core-Switch: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-30
        # =====================================================

        try:
            lab.create_link(
                "PLC-Aeration",
                "eth1",
                "Vlan-30",
                "Ethernet2"
            )
        except Exception as e:
            print(f"Error linking PLC-Aeration to Vlan-30: {e}")

        try:
            lab.create_link(
                "Vlan-30",
                "Ethernet3",
                "HMI-Aeration",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking HMI-Aeration to Vlan-30: {e}")

        try:
            lab.create_link(
                "Vlan-30",
                "Ethernet0",
                "Core-Switch",
                "Ethernet2"
            )
        except Exception as e:
            print(f"Error linking Vlan-30 to Core-Switch: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-40
        # =====================================================

        try:
            lab.create_link(
                "PLC-Clarification",
                "eth1",
                "Vlan-40",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Clarification to Vlan-40: {e}")

        try:
            lab.create_link(
                "Vlan-40",
                "Ethernet3",
                "HMI-Clarification",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking HMI-Clarification to Vlan-40: {e}")

        try:
            lab.create_link(
                "Core-Switch",
                "Ethernet3",
                "Vlan-40",
                "Ethernet1"
            )
        except Exception as e:
            print(f"Error linking Core-Switch to Vlan-40: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-50
        # =====================================================

        try:
            lab.create_link(
                "PLC-Disinfection",
                "eth1",
                "Vlan-50",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Disinfection to Vlan-50: {e}")

        try:
            lab.create_link(
                "HMI-Disinfection",
                "eth0",
                "Vlan-50",
                "Ethernet1"
            )
        except Exception as e:
            print(f"Error linking HMI-Disinfection to Vlan-50: {e}")

        try:
            lab.create_link(
                "Vlan-50",
                "Ethernet6",
                "Core-Switch",
                "Ethernet6"
            )
        except Exception as e:
            print(f"Error linking Vlan-50 to Core-Switch: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-60
        # =====================================================

        try:
            lab.create_link(
                "PLC-Thickening",
                "eth1",
                "Vlan-60",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Thickening to Vlan-60: {e}")

        try:
            lab.create_link(
                "HMI-Thickening",
                "eth0",
                "Vlan-60",
                "Ethernet2"
            )
        except Exception as e:
            print(f"Error linking HMI-Thickening to Vlan-60: {e}")

        try:
            lab.create_link(
                "Vlan-60",
                "Ethernet7",
                "Core-Switch",
                "Ethernet4"
            )
        except Exception as e:
            print(f"Error linking Vlan-60 to Core-Switch: {e}")


        # =====================================================
        # DISTRIBUTION VLAN-70
        # =====================================================

        try:
            lab.create_link(
                "PLC-Digestion",
                "eth1",
                "Vlan-70",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Digestion to Vlan-70: {e}")

        try:
            lab.create_link(
                "HMI-Digestion",
                "eth0",
                "Vlan-70",
                "Ethernet5"
            )
        except Exception as e:
            print(f"Error linking HMI-Digestion to Vlan-70: {e}")

        try:
            lab.create_link(
                "Core-Switch",
                "Ethernet5",
                "Vlan-70",
                "Ethernet7"
            )
        except Exception as e:
            print(f"Error linking Core-Switch to Vlan-70: {e}")


        # =====================================================
        # BOTTOM VLAN-05
        # =====================================================

        try:
            lab.create_link(
                "PLC-Disinfection",
                "eth0",
                "Vlan-05",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Disinfection to Vlan-05: {e}")

        try:
            lab.create_link(
                "Vlan-05",
                "Ethernet1",
                "CL-501",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-05 to CL-501: {e}")

        try:
            lab.create_link(
                "Vlan-05",
                "Ethernet2",
                "FT-501",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-05 to FT-501: {e}")

        try:
            lab.create_link(
                "Vlan-05",
                "Ethernet3",
                "LT-501",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-05 to LT-501: {e}")

        try:
            lab.create_link(
                "Vlan-05",
                "Ethernet4",
                "AV-501",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-05 to AV-501: {e}")


        # =====================================================
        # BOTTOM VLAN-06
        # =====================================================

        try:
            lab.create_link(
                "PLC-Thickening",
                "eth0",
                "Vlan-06",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Thickening to Vlan-06: {e}")

        try:
            lab.create_link(
                "Vlan-06",
                "Ethernet1",
                "LT-601",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-06 to LT-601: {e}")

        try:
            lab.create_link(
                "Vlan-06",
                "Ethernet2",
                "FT-601",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-06 to FT-601: {e}")

        try:
            lab.create_link(
                "Vlan-06",
                "Ethernet3",
                "SS-601",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-06 to SS-601: {e}")

        try:
            lab.create_link(
                "Vlan-06",
                "Ethernet4",
                "P-601",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-06 to P-601: {e}")


        # =====================================================
        # BOTTOM VLAN-07
        # =====================================================

        try:
            lab.create_link(
                "PLC-Digestion",
                "eth0",
                "Vlan-07",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking PLC-Digestion to Vlan-07: {e}")

        try:
            lab.create_link(
                "Vlan-07",
                "Ethernet1",
                "T-701",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-07 to T-701: {e}")

        try:
            lab.create_link(
                "Vlan-07",
                "Ethernet2",
                "PT-701",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-07 to PT-701: {e}")

        try:
            lab.create_link(
                "Vlan-07",
                "Ethernet3",
                "FT-701",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-07 to FT-701: {e}")

        try:
            lab.create_link(
                "Vlan-07",
                "Ethernet4",
                "GAS-701",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Vlan-07 to GAS-701: {e}")


        # =====================================================
        # CORE / OUTER EDGE
        #
        # SCADA NOW HAS ONLY ONE CONNECTION:
        # Core-Switch -> scada-server
        #
        # KALI NOW CONNECTS TO CORE-SWITCH.
        # =====================================================

        try:
            lab.create_link(
                "Core-Switch",
                "Ethernet7",
                "scada-server",
                "eth0"
            )
        except Exception as e:
            print(f"Error linking Core-Switch to scada-server: {e}")

        try:
            lab.create_link(
                "Core-Switch",
                "Ethernet8",
                "KaliLinux-1",
                "Ethernet0"
            )
        except Exception as e:
            print(f"Error linking Core-Switch to KaliLinux-1: {e}")

        
        # =====================================================
        # CONFIGURE KALI NETWORK
        # =====================================================

        configure_kali(KL)

        # =====================================================
        # FINAL OUTPUT
        # =====================================================

        print("-----------------------------------------------------------------------")
        print("Nodes created, started and linked. Here are the links:")
        print("-----------------------------------------------------------------------")

        lab.links_summary()

        print("-----------------------------------------------------------------------")
        print(
            LAB_NAME
            + f" build is Complete on {SERVER_URL}. "
              "It is now safe to open the project in GNS3"
        )



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy an IT/OT GNS3 scenario."
    )
    parser.add_argument(
        "--scenario",
        default=os.getenv("SCENARIO", "wastewater"),
        help="Scenario to deploy. Use 'wastewater' for the full treatment deployment or 'generic' for a JSON topology.",
    )
    parser.add_argument(
        "--gns3-url",
        default=os.getenv("GNS3_URL", GNS3_URL),
        help="GNS3 server URL for generic JSON scenarios.",
    )
    parser.add_argument(
        "--topology",
        default=os.getenv(
            "TOPOLOGY_FILE",
            "configs/module_1_wastewater_flat.json",
        ),
        help="Topology JSON file used by the generic deployment path.",
    )
    parser.add_argument(
        "--symbol-prefix",
        default=os.getenv("SYMBOL_PREFIX"),
        help="Optional custom GNS3 symbol prefix.",
    )
    args = parser.parse_args()

    scenario = args.scenario.strip().lower()

    if scenario in {"wastewater", "water", "ww"}:
        build_wastewater()
        return

    if scenario in {"generic", "json", "scaffold"}:
        build_generic_topology(
            Path(args.topology),
            args.gns3_url,
            args.symbol_prefix,
        )
        return

    raise SystemExit(
        f"Unknown scenario '{args.scenario}'. "
        "Use 'wastewater' or 'generic'."
    )


if __name__ == "__main__":
    main()
