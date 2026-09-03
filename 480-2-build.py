#!/usr/bin/env python3
"""
Build the CIT 480-2 Freshwater Treatment GNS3 project.

The topology keeps the larger, process-oriented layout of the original
long deployment script, but all scenario content is freshwater treatment.

Freshwater process areas:
    intake -> filtration -> dosing -> storage

Core freshwater devices:
    plc-intake       10.10.20.11
    plc-filtration   10.10.20.12
    plc-dosing       10.10.20.13
    plc-storage      10.10.20.14
    hmi-poller       10.10.20.20
    historian        10.10.20.30
    scada-server     10.10.20.200
    KaliLinux-1      10.10.20.250

The four PLC environment blocks match the Freshwater Treatment baseline
configuration supplied for Module 2.
"""

import logging
import sys
import time

import requests
from gns3fy import Gns3Connector, Project


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

LAB_NAME = "Module 2 - Freshwater Treatment - Baseline"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "freshwater_treatment"
FRESHWATER_SUBNET = "10.10.20.0/24"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
EDGE_SWITCH_TEMPLATE = "GNS3 Ethernet switch"
KALI_TEMPLATE = "Kali Linux"
SCADA_TEMPLATE = "generic-scada"
ICS_TEMPLATE = "ics-node"

SCADA_IP = "10.10.20.200"
KALI_IP = "10.10.20.250"


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
        "name": ICS_TEMPLATE,
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/ics-node:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
    {
        "name": SCADA_TEMPLATE,
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


FRESHWATER_STAGES = [
    {
        "name": "intake",
        "label": "Raw Water Intake",
        "field_vlan": "vlan-intake",
        "field_subnet": "192.168.10.0/24",
        "plc": "plc-intake",
        "plc_field_ip": "192.168.10.5",
        "plc_ops_ip": "10.10.20.11",
        "field_switch": "field-switch-intake",
        "plc_env": {
            "SCENARIO": SCENARIO,
            "NODE_MODE": "plc",
            "PLC_ROLE": "intake",
            "DEVICE_AGE_YEARS": "7",
            "AGE_FAILURE_THRESHOLD_YEARS": "12",
            "AGE_FAILURE_WINDOW_SECONDS": "10",
            "AGE_FAILURE_MAX_REQUESTS": "30",
            "AGE_FAILURE_DURATION_SECONDS": "20",
            "AGE_FAILURE_MODE": "zero",
        },
        "sensors": [
            {"name": "sensor-intake-flow", "ip": "192.168.10.1", "tag": "intake_flow", "units": "gpm"},
            {"name": "sensor-intake-level", "ip": "192.168.10.2", "tag": "intake_level", "units": "ft"},
            {"name": "sensor-intake-pressure", "ip": "192.168.10.3", "tag": "intake_pressure", "units": "psi"},
            {"name": "sensor-intake-turbidity", "ip": "192.168.10.4", "tag": "intake_turbidity", "units": "ntu"},
        ],
        "x": -540,
    },
    {
        "name": "filtration",
        "label": "Filtration",
        "field_vlan": "vlan-filtration",
        "field_subnet": "192.168.20.0/24",
        "plc": "plc-filtration",
        "plc_field_ip": "192.168.20.5",
        "plc_ops_ip": "10.10.20.12",
        "field_switch": "field-switch-filtration",
        "plc_env": {
            "SCENARIO": SCENARIO,
            "NODE_MODE": "plc",
            "PLC_ROLE": "filtration",
            "DEVICE_AGE_YEARS": "16",
            "AGE_FAILURE_THRESHOLD_YEARS": "12",
            "AGE_FAILURE_WINDOW_SECONDS": "10",
            "AGE_FAILURE_MAX_REQUESTS": "30",
            "AGE_FAILURE_DURATION_SECONDS": "20",
            "AGE_FAILURE_MODE": "zero",
        },
        "sensors": [
            {"name": "sensor-filtration-turbidity", "ip": "192.168.20.1", "tag": "filtration_turbidity", "units": "ntu"},
            {"name": "sensor-filtration-pressure", "ip": "192.168.20.2", "tag": "filtration_pressure", "units": "psi"},
            {"name": "sensor-filtration-flow", "ip": "192.168.20.3", "tag": "filtration_flow", "units": "gpm"},
            {"name": "sensor-filtration-level", "ip": "192.168.20.4", "tag": "filtration_level", "units": "ft"},
        ],
        "x": -180,
    },
    {
        "name": "dosing",
        "label": "Chemical Dosing",
        "field_vlan": "vlan-dosing",
        "field_subnet": "192.168.30.0/24",
        "plc": "plc-dosing",
        "plc_field_ip": "192.168.30.5",
        "plc_ops_ip": "10.10.20.13",
        "field_switch": "field-switch-dosing",
        "plc_env": {
            "SCENARIO": SCENARIO,
            "NODE_MODE": "plc",
            "PLC_ROLE": "dosing",
            "DEVICE_AGE_YEARS": "13",
            "AGE_FAILURE_THRESHOLD_YEARS": "12",
            "AGE_FAILURE_WINDOW_SECONDS": "10",
            "AGE_FAILURE_MAX_REQUESTS": "30",
            "AGE_FAILURE_DURATION_SECONDS": "20",
            "AGE_FAILURE_MODE": "zero",
        },
        "sensors": [
            {"name": "sensor-dosing-chlorine", "ip": "192.168.30.1", "tag": "dosing_chlorine", "units": "mg_l"},
            {"name": "sensor-dosing-ph", "ip": "192.168.30.2", "tag": "dosing_ph", "units": "ph"},
            {"name": "sensor-dosing-flow", "ip": "192.168.30.3", "tag": "dosing_flow", "units": "gpm"},
            {"name": "sensor-dosing-rate", "ip": "192.168.30.4", "tag": "dosing_rate", "units": "lpm"},
        ],
        "x": 180,
    },
    {
        "name": "storage",
        "label": "Treated Water Storage",
        "field_vlan": "vlan-storage",
        "field_subnet": "192.168.40.0/24",
        "plc": "plc-storage",
        "plc_field_ip": "192.168.40.5",
        "plc_ops_ip": "10.10.20.14",
        "field_switch": "field-switch-storage",
        "plc_env": {
            "SCENARIO": SCENARIO,
            "NODE_MODE": "plc",
            "PLC_ROLE": "storage",
            "DEVICE_AGE_YEARS": "5",
            "AGE_FAILURE_THRESHOLD_YEARS": "12",
            "AGE_FAILURE_WINDOW_SECONDS": "10",
            "AGE_FAILURE_MAX_REQUESTS": "30",
            "AGE_FAILURE_DURATION_SECONDS": "20",
            "AGE_FAILURE_MODE": "zero",
        },
        "sensors": [
            {"name": "sensor-storage-level", "ip": "192.168.40.1", "tag": "storage_level", "units": "ft"},
            {"name": "sensor-storage-turbidity", "ip": "192.168.40.2", "tag": "storage_turbidity", "units": "ntu"},
            {"name": "sensor-storage-chlorine", "ip": "192.168.40.3", "tag": "storage_chlorine", "units": "mg_l"},
            {"name": "sensor-storage-temperature", "ip": "192.168.40.4", "tag": "storage_temperature", "units": "c"},
        ],
        "x": 540,
    },
]

HMI_ENV = {
    "NODE_MODE": "hmi",
    "PLC_TARGETS": (
        "--plc intake=10.10.20.11:502 "
        "--plc filtration=10.10.20.12:502 "
        "--plc dosing=10.10.20.13:502 "
        "--plc storage=10.10.20.14:502"
    ),
}

HISTORIAN_ENV = {
    "NODE_MODE": "historian",
    "PLC_TARGETS": (
        "--plc intake=10.10.20.11:502 "
        "--plc filtration=10.10.20.12:502 "
        "--plc dosing=10.10.20.13:502 "
        "--plc storage=10.10.20.14:502"
    ),
}

SCADA_ENV = {
    "SCENARIO": SCENARIO,
    "SCADA_SUBNETS": FRESHWATER_SUBNET,
}


NODE_IPS = {
    "hmi-poller": "10.10.20.20",
    "historian": "10.10.20.30",
    "scada-server": SCADA_IP,
}


# ---------- GNS3 server/project helpers ----------


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
    """Ensure the reusable ten-port operations switch template exists."""
    template_name = CORE_SWITCH_TEMPLATE

    try:
        response = requests.get(
            f"{server_url}/v2/templates",
            auth=(GNS3_USER, GNS3_PW),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not list templates on {server_url}: {exc}") from exc

    existing = next((t for t in response.json() if t.get("name") == template_name), None)
    if existing:
        logging.info("Template '%s' already exists on %s.", template_name, server_url)
        return

    ports = [
        {
            "name": f"Ethernet{port_number}",
            "port_number": port_number,
            "type": "access",
            "vlan": 1,
        }
        for port_number in range(10)
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
        response = requests.post(
            f"{server_url}/v2/templates",
            json=switch_template,
            auth=(GNS3_USER, GNS3_PW),
        )
        require_http_success(response, f"Create template '{template_name}' on {server_url}")
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error creating '{template_name}' on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Created template '%s' with %s ports on %s.",
        template_name,
        len(ports),
        server_url,
    )


def ensure_required_templates(server, server_url):
    """Register/update only the Docker templates used by freshwater treatment."""
    try:
        available_templates = server.get_templates()
    except Exception as exc:
        raise RuntimeError(f"Could not list GNS3 templates on {server_url}: {exc}") from exc

    templates_by_name = {template["name"]: template for template in available_templates}

    for template in REQUIRED_TEMPLATES:
        template_name = template["name"]
        existing_template = templates_by_name.get(template_name)

        if existing_template:
            update_existing_template_environment(
                server_url,
                existing_template,
                template["environment"],
            )
            continue

        logging.info("Registering missing template '%s' on %s.", template_name, server_url)
        try:
            response = requests.post(
                f"{server_url}/v2/templates",
                json=template,
                auth=(GNS3_USER, GNS3_PW),
            )
            require_http_success(
                response,
                f"Register template '{template_name}' on {server_url}",
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error registering '{template_name}' on {server_url}: {exc}"
            ) from exc


def update_existing_template_environment(server_url, template, expected_environment):
    """Update a reused Docker template if it points at a different scenario."""
    template_name = template["name"]
    template_id = template.get("template_id")
    actual_environment = template.get("environment")

    if actual_environment == expected_environment:
        logging.info(
            "Template '%s' already has %s on %s.",
            template_name,
            expected_environment,
            server_url,
        )
        return

    if not template_id:
        raise RuntimeError(
            f"Template '{template_name}' on {server_url} has no template_id; cannot update it."
        )

    updated_template = dict(template)
    updated_template["environment"] = expected_environment

    logging.info(
        "Updating template '%s' environment on %s from %r to %r.",
        template_name,
        server_url,
        actual_environment,
        expected_environment,
    )

    try:
        response = requests.put(
            f"{server_url}/v2/templates/{template_id}",
            json=updated_template,
            auth=(GNS3_USER, GNS3_PW),
        )
        require_http_success(
            response,
            f"Update template '{template_name}' environment on {server_url}",
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error updating '{template_name}' environment on {server_url}: {exc}"
        ) from exc


def open_or_create_project(server, server_url):
    """Open the freshwater project or create it if it does not exist."""
    try:
        projects = server.get_projects()
    except Exception as exc:
        raise RuntimeError(f"Could not list projects on {server_url}: {exc}") from exc

    existing_lab = next((p for p in projects if p["name"] == LAB_NAME), None)

    try:
        if existing_lab:
            lab = Project(project_id=existing_lab["project_id"], connector=server)
            lab.get()
            lab.open()
            logging.info("Opened existing project '%s' on %s.", LAB_NAME, server_url)
        else:
            lab = Project(name=LAB_NAME, connector=server)
            lab.create()
            lab.open()
            logging.info("Created project '%s' on %s.", LAB_NAME, server_url)
    except Exception as exc:
        raise RuntimeError(
            f"Could not open or create project '{LAB_NAME}' on {server_url}: {exc}"
        ) from exc

    return lab


# ---------- Node helpers ----------


def create_node(lab, name, template, x, y, errors):
    """Create one node and record a detailed error if it fails."""
    try:
        lab.create_node(name=name, template=template, x=x, y=y)
        logging.info("Created node '%s' with template '%s'.", name, template)
    except Exception as exc:
        errors.append(
            f"Create node '{name}' using template '{template}' failed: {exc}"
        )


def build_environment(values):
    """Return Docker environment variables in the GNS3 format."""
    return "\n".join(f"{key}={value}" for key, value in values.items())


def build_interface_config(ip_address):
    """Return a simple static IPv4 interface configuration."""
    return f"""
auto eth0
iface eth0 inet static
    address {ip_address}
    netmask 255.255.255.0
"""


def build_plc_config(field_ip, operations_ip):
    """Return a dual-interface PLC configuration: field VLAN plus operations LAN."""
    return f"""
auto eth0
iface eth0 inet static
    address {field_ip}
    netmask 255.255.255.0

auto eth1
iface eth1 inet static
    address {operations_ip}
    netmask 255.255.255.0
"""


def sensor_environment(sensor):
    """Return the freshwater field sensor environment."""
    return build_environment(
        {
            "SCENARIO": SCENARIO,
            "TAG": sensor["tag"],
            "SIMULATION": "true",
            "UNITS": sensor["units"],
            "DATA_TYPE": "float",
        }
    )


def configure_interfaces(lab, node_name, config, errors):
    """Write /etc/network/interfaces to a Docker node."""
    try:
        node = lab.get_node(node_name)
        node.get()

        status = getattr(node.status, "value", str(node.status)).lower()
        was_running = status == "started"

        if was_running:
            node.stop()

        node.write_file(path="/etc/network/interfaces", data=config.strip() + "\n")

        if was_running:
            node.start()

        logging.info("Configured network for '%s'.", node_name)
    except Exception as exc:
        errors.append(
            f"Configure network for node '{node_name}' failed: {exc}"
        )


def set_docker_node_environment(server_url, lab, node_name, environment, errors):
    """Set Docker environment variables on a project node."""
    try:
        node = lab.get_node(node_name)
        node.get()

        response = requests.get(
            f"{server_url}/v2/projects/{lab.project_id}/nodes/{node.node_id}",
            auth=(GNS3_USER, GNS3_PW),
        )
        response.raise_for_status()
        node_data = response.json()

        properties = dict(node_data.get("properties") or {})
        actual_environment = properties.get("environment")

        if actual_environment == environment:
            logging.info("Node '%s' already has the requested environment.", node_name)
            return

        properties["environment"] = environment

        response = requests.put(
            f"{server_url}/v2/projects/{lab.project_id}/nodes/{node.node_id}",
            json={"properties": properties},
            auth=(GNS3_USER, GNS3_PW),
        )
        require_http_success(response, f"Update node '{node_name}' environment")

        logging.info(
            "Updated node '%s' environment from %r to %r.",
            node_name,
            actual_environment,
            environment,
        )
    except Exception as exc:
        errors.append(
            f"Set environment for node '{node_name}' to '{environment}' failed: {exc}"
        )


def start_node(lab, node_name, errors):
    """Start a node if it is not already running."""
    try:
        node = lab.get_node(node_name)
        node.get()

        status = getattr(node.status, "value", str(node.status)).lower()
        if status == "started":
            logging.info("Node '%s' is already started.", node_name)
            return

        node.start()
        logging.info("Started node '%s'.", node_name)
    except Exception as exc:
        errors.append(f"Start node '{node_name}' failed: {exc}")


def create_link(lab, node_a, port_a, node_b, port_b, errors):
    """Create one link and record a detailed error if it fails."""
    try:
        lab.create_link(node_a, port_a, node_b, port_b)
        logging.info("Linked %s:%s to %s:%s.", node_a, port_a, node_b, port_b)
    except Exception as exc:
        errors.append(
            f"Create link {node_a}:{port_a} -> {node_b}:{port_b} failed: {exc}"
        )


# ---------- Freshwater topology ----------


def create_scenario_nodes(lab, errors):
    """Create four freshwater field VLANs with four sensors each, PLCs, and operations services."""
    create_node(lab, "ops-switch", CORE_SWITCH_TEMPLATE, 0, 120, errors)

    for stage in FRESHWATER_STAGES:
        x = stage["x"]

        for index, sensor in enumerate(stage["sensors"]):
            create_node(
                lab,
                sensor["name"],
                "generic-sensor",
                x - 120 + (index * 80),
                -600,
                errors,
            )

        create_node(
            lab,
            stage["field_vlan"],
            EDGE_SWITCH_TEMPLATE,
            x + 60,
            -430,
            errors,
        )
        create_node(
            lab,
            stage["plc"],
            ICS_TEMPLATE,
            x + 60,
            -250,
            errors,
        )

    create_node(lab, "hmi-poller", ICS_TEMPLATE, -170, -20, errors)
    create_node(lab, "historian", ICS_TEMPLATE, 170, -20, errors)
    create_node(lab, "scada-server", SCADA_TEMPLATE, 270, 120, errors)
    create_node(lab, "KaliLinux-1", KALI_TEMPLATE, -270, 120, errors)


def configure_scenario_nodes(lab, errors):
    """Apply field and operations addresses to all freshwater Docker nodes."""
    for stage in FRESHWATER_STAGES:
        configure_interfaces(
            lab,
            stage["plc"],
            build_plc_config(stage["plc_field_ip"], stage["plc_ops_ip"]),
            errors,
        )

        for sensor in stage["sensors"]:
            configure_interfaces(
                lab,
                sensor["name"],
                build_interface_config(sensor["ip"]),
                errors,
            )

    for node_name, ip_address in NODE_IPS.items():
        configure_interfaces(
            lab,
            node_name,
            build_interface_config(ip_address),
            errors,
        )


def set_scenario_environment(server_url, lab, errors):
    """Apply freshwater PLC, sensor, HMI, historian, and SCADA environments."""
    for stage in FRESHWATER_STAGES:
        set_docker_node_environment(
            server_url,
            lab,
            stage["plc"],
            build_environment(stage["plc_env"]),
            errors,
        )

        for sensor in stage["sensors"]:
            set_docker_node_environment(
                server_url,
                lab,
                sensor["name"],
                sensor_environment(sensor),
                errors,
            )

    set_docker_node_environment(
        server_url, lab, "hmi-poller", build_environment(HMI_ENV), errors
    )
    set_docker_node_environment(
        server_url, lab, "historian", build_environment(HISTORIAN_ENV), errors
    )
    set_docker_node_environment(
        server_url, lab, "scada-server", build_environment(SCADA_ENV), errors
    )


def start_scenario_nodes(lab, errors):
    """Start every freshwater field and operations node."""
    start_node(lab, "ops-switch", errors)

    for stage in FRESHWATER_STAGES:
        for sensor in stage["sensors"]:
            start_node(lab, sensor["name"], errors)
        start_node(lab, stage["field_vlan"], errors)
        start_node(lab, stage["plc"], errors)

    start_node(lab, "hmi-poller", errors)
    start_node(lab, "historian", errors)
    start_node(lab, "scada-server", errors)


def create_scenario_links(lab, errors):
    """Connect four isolated freshwater field VLANs to the operations network."""
    ops_ports = ["Ethernet0", "Ethernet1", "Ethernet2", "Ethernet3"]

    for stage_index, stage in enumerate(FRESHWATER_STAGES):
        field_switch = stage["field_vlan"]

        # Four sensors plus the PLC share this stage's field VLAN.
        for sensor_index, sensor in enumerate(stage["sensors"], start=1):
            create_link(
                lab,
                sensor["name"],
                "eth0",
                field_switch,
                f"Ethernet{sensor_index}",
                errors,
            )

        create_link(
            lab,
            stage["plc"],
            "eth0",
            field_switch,
            "Ethernet0",
            errors,
        )

        # PLC eth1 is the operations-network interface.
        create_link(
            lab,
            stage["plc"],
            "eth1",
            "ops-switch",
            ops_ports[stage_index],
            errors,
        )

    create_link(lab, "hmi-poller", "eth0", "ops-switch", "Ethernet4", errors)
    create_link(lab, "historian", "eth0", "ops-switch", "Ethernet5", errors)
    create_link(lab, "scada-server", "eth0", "ops-switch", "Ethernet6", errors)
    create_link(lab, "KaliLinux-1", "Ethernet0", "ops-switch", "Ethernet7", errors)

def configure_kali(lab, node_name, errors):
    """Configure Kali with a persistent static IPv4 address."""
    try:
        node = lab.get_node(node_name)
        node.get()

        status = getattr(node.status, "value", str(node.status)).lower()
        if status != "started":
            node.start()

        time.sleep(8)

        for attempt in range(30):
            try:
                result = node.execute("nmcli device status")
                if "eth0" in str(result):
                    logging.info(
                        "Kali eth0 detected after %s attempt(s).",
                        attempt + 1,
                    )
                    break
            except Exception:
                pass
            time.sleep(2)
        else:
            raise RuntimeError("Kali eth0 did not become available after 60 seconds.")

        node.execute("nmcli connection delete kali-eth0 || true")
        node.execute(
            "nmcli connection add "
            "type ethernet "
            "ifname eth0 "
            "con-name kali-eth0 "
            "ipv4.method manual "
            f"ipv4.addresses {KALI_IP}/24"
        )
        time.sleep(2)
        node.execute("nmcli connection up kali-eth0")
        logging.info("Configured Kali '%s' as %s/24.", node_name, KALI_IP)
    except Exception as exc:
        errors.append(f"Configure Kali node '{node_name}' failed: {exc}")


def verify_kali_to_scada(lab, errors):
    """Verify the final student-access path from Kali to the SCADA server."""
    try:
        node = lab.get_node("KaliLinux-1")
        node.get()
        time.sleep(2)
        result = node.execute(f"ping -c 3 -W 2 {SCADA_IP}")
        result_text = str(result)
        if "0% packet loss" not in result_text and ", 0.0% packet loss" not in result_text:
            raise RuntimeError(
                f"Kali could not successfully ping SCADA at {SCADA_IP}. Result: {result_text}"
            )
        logging.info("Kali successfully reached SCADA at %s.", SCADA_IP)
    except Exception as exc:
        errors.append(f"Kali-to-SCADA connectivity test failed: {exc}")


# ---------- Main deployment ----------


def build_project_on_server(server_url):
    """Build the complete freshwater treatment project with four sensors per field VLAN on one GNS3 server."""
    errors = []

    logging.info("Connecting to GNS3 server at %s.", server_url)
    server = Gns3Connector(url=server_url, user=GNS3_USER, cred=GNS3_PW)

    try:
        logging.info("GNS3 server version at %s: %s", server_url, server.get_version())
        ensure_10_port_switch(server_url)
        ensure_required_templates(server, server_url)
        lab = open_or_create_project(server, server_url)
    except Exception as exc:
        raise RuntimeError(f"Project setup failed on {server_url}: {exc}") from exc

    logging.info("Creating freshwater nodes for '%s' on %s.", LAB_NAME, server_url)
    create_scenario_nodes(lab, errors)

    try:
        lab.get()
    except Exception as exc:
        errors.append(f"Refresh project inventory after node creation failed: {exc}")

    logging.info(
        "Applying freshwater Docker environments (SCENARIO=%s) on %s.",
        SCENARIO,
        server_url,
    )
    set_scenario_environment(server_url, lab, errors)

    logging.info(
        "Applying freshwater network configuration on %s.",
        server_url,
    )
    configure_scenario_nodes(lab, errors)

    try:
        lab.get()
    except Exception as exc:
        errors.append(
            f"Refresh project inventory after network configuration failed: {exc}"
        )

    logging.info("Creating freshwater topology links on %s.", server_url)
    create_scenario_links(lab, errors)

    logging.info("Starting freshwater treatment nodes on %s.", server_url)
    start_scenario_nodes(lab, errors)

    configure_kali(lab, "KaliLinux-1", errors)

    # Do not hide this failure. A completed deployment must have a working
    # student-access path to the freshwater SCADA server.
    if not errors:
        verify_kali_to_scada(lab, errors)

    if errors:
        raise RuntimeError(
            "\n".join(f"{server_url}: {error}" for error in errors)
        )

    logging.info("Nodes created, configured, and linked. Link summary follows.")
    lab.links_summary()
    logging.info(
        "%s build is complete on %s. It is safe to open the project in GNS3.",
        LAB_NAME,
        server_url,
    )


def main():
    """Read target servers and build the freshwater project on each one."""
    try:
        server_urls = read_server_urls()
    except RuntimeError as exc:
        logging.error("Startup failed: %s", exc)
        return 1

    failed_servers = []

    for server_url in server_urls:
        try:
            build_project_on_server(server_url)
        except Exception as exc:
            logging.error("Build failed for %s:\n%s", server_url, exc)
            failed_servers.append(server_url)

    if failed_servers:
        logging.error(
            "Deployment finished with errors on: %s",
            ", ".join(failed_servers),
        )
        return 1

    logging.info("All freshwater treatment builds completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
