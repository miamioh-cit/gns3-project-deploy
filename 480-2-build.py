#!/usr/bin/env python3
"""
Build the CIT 480-2 Freshwater Treatment GNS3 project.

Freshwater topology:
    intake -> filtration -> dosing -> storage

Field networks:
    Intake      192.168.10.0/24
    Filtration  192.168.20.0/24
    Dosing      192.168.30.0/24
    Storage     192.168.40.0/24

Operations / SCADA network:
    10.10.20.0/24

Operations addresses:
    plc-intake       10.10.20.11
    plc-filtration   10.10.20.12
    plc-dosing       10.10.20.13
    plc-storage      10.10.20.14
    hmi-poller       10.10.20.20
    historian        10.10.20.30
    scada-server     10.10.20.200
    KaliLinux-1      10.10.20.250

The freshwater course provides its own PLC/HMI/historian Python runtime under
course/plc_sim. The GNS3 ics-node image used on the server is only a shell
container, so this deployment provisions the course runtime into a persistent
GNS3 Docker volume, installs Python + pymodbus, and sets the Docker start
command to run plc_sim.node_entrypoint. This makes NODE_MODE=plc actually
launch the Modbus/TCP server on port 502.
"""

import logging
import os
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
NETMASK = "255.255.255.0"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
EDGE_SWITCH_TEMPLATE = "GNS3 Ethernet switch"
KALI_TEMPLATE = "Kali Linux"
SCADA_TEMPLATE = "generic-scada"
ICS_TEMPLATE = "ics-node"
SENSOR_TEMPLATE = "generic-sensor"

# This deployment owns the entire lab project. When rerun, clear the existing
# project contents first so Jenkins retries can never append duplicate nodes.
RESET_EXISTING_PROJECT = True

SCADA_IP = "10.10.20.200"
KALI_IP = "10.10.20.250"

# The Jenkins deployment image copies the course's plc_sim directory here.
COURSE_PLC_SIM_DIR = os.getenv("COURSE_PLC_SIM_DIR", "/app/course/plc_sim")
RUNTIME_DIR = "/opt/freshwater_runtime"
RUNTIME_PACKAGE_DIR = f"{RUNTIME_DIR}/plc_sim"
RUNTIME_LAUNCHER = f"{RUNTIME_DIR}/start.sh"

# These are the Python files used by node_entrypoint.py and its imports.
COURSE_RUNTIME_FILES = (
    "__init__.py",
    "node_entrypoint.py",
    "plc_server.py",
    "plant_model.py",
    "hmi_poller.py",
    "historian.py",
    "modbus_write.py",
)

RUNTIME_START_COMMAND = f"/bin/bash {RUNTIME_LAUNCHER}"


REQUIRED_TEMPLATES = [
    {
        "name": SENSOR_TEMPLATE,
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
            "IP_ADDRESS": "10.10.20.11",
            "FIELD_IP_ADDRESS": "192.168.10.5",
            "FIELD_SUBNET": "192.168.10.0/24",
            "SUBNET": FRESHWATER_SUBNET,
            "NETMASK": NETMASK,
            "NODE_MODE": "plc",
            "PLC_ROLE": "intake",
            "PLC_PORT": "502",
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
            "IP_ADDRESS": "10.10.20.12",
            "FIELD_IP_ADDRESS": "192.168.20.5",
            "FIELD_SUBNET": "192.168.20.0/24",
            "SUBNET": FRESHWATER_SUBNET,
            "NETMASK": NETMASK,
            "NODE_MODE": "plc",
            "PLC_ROLE": "filtration",
            "PLC_PORT": "502",
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
            "IP_ADDRESS": "10.10.20.13",
            "FIELD_IP_ADDRESS": "192.168.30.5",
            "FIELD_SUBNET": "192.168.30.0/24",
            "SUBNET": FRESHWATER_SUBNET,
            "NETMASK": NETMASK,
            "NODE_MODE": "plc",
            "PLC_ROLE": "dosing",
            "PLC_PORT": "502",
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
            "IP_ADDRESS": "10.10.20.14",
            "FIELD_IP_ADDRESS": "192.168.40.5",
            "FIELD_SUBNET": "192.168.40.0/24",
            "SUBNET": FRESHWATER_SUBNET,
            "NETMASK": NETMASK,
            "NODE_MODE": "plc",
            "PLC_ROLE": "storage",
            "PLC_PORT": "502",
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
    "SCENARIO": SCENARIO,
    "IP_ADDRESS": "10.10.20.20",
    "SUBNET": FRESHWATER_SUBNET,
    "NETMASK": NETMASK,
    "NODE_MODE": "hmi",
    "PLC_TARGETS": (
        "--plc intake=10.10.20.11:502 "
        "--plc filtration=10.10.20.12:502 "
        "--plc dosing=10.10.20.13:502 "
        "--plc storage=10.10.20.14:502"
    ),
}

HISTORIAN_ENV = {
    "SCENARIO": SCENARIO,
    "IP_ADDRESS": "10.10.20.30",
    "SUBNET": FRESHWATER_SUBNET,
    "NETMASK": NETMASK,
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
    "IP_ADDRESS": SCADA_IP,
    "SUBNET": FRESHWATER_SUBNET,
    "NETMASK": NETMASK,
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
            update_existing_template_properties(
                server_url,
                existing_template,
                {"environment": template["environment"]},
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


def update_existing_template_properties(server_url, template, updates):
    """Update selected properties of a reused Docker template."""
    template_id = template.get("template_id")
    if not template_id:
        raise RuntimeError(
            f"Template '{template.get('name')}' on {server_url} has no template_id; cannot update it."
        )

    changed = False
    updated_template = dict(template)
    for key, value in updates.items():
        if updated_template.get(key) != value:
            updated_template[key] = value
            changed = True

    if not changed:
        return

    try:
        response = requests.put(
            f"{server_url}/v2/templates/{template_id}",
            json=updated_template,
            auth=(GNS3_USER, GNS3_PW),
        )
        require_http_success(
            response,
            f"Update template '{template.get('name')}' on {server_url}",
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error updating template '{template.get('name')}' on {server_url}: {exc}"
        ) from exc


def reset_project_contents(server_url, lab):
    """Delete all existing links and nodes from this deployment-owned project."""
    try:
        lab.get()
    except Exception as exc:
        raise RuntimeError(f"Could not refresh project before reset: {exc}") from exc

    project_id = lab.project_id
    links = list(getattr(lab, "links", []) or [])
    nodes = list(getattr(lab, "nodes", []) or [])

    # Delete links first so node deletion cannot leave dangling links.
    for link in links:
        link_id = getattr(link, "link_id", None) or getattr(link, "id", None)
        if not link_id and isinstance(link, dict):
            link_id = link.get("link_id") or link.get("id")
        if not link_id:
            logging.warning("Skipping existing link with no link_id while resetting project.")
            continue
        response = requests.delete(
            f"{server_url}/v2/projects/{project_id}/links/{link_id}",
            auth=(GNS3_USER, GNS3_PW),
        )
        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"Delete existing link '{link_id}' failed: HTTP {response.status_code}: {response.text}"
            )

    for node in nodes:
        node_id = getattr(node, "node_id", None) or getattr(node, "id", None)
        if not node_id and isinstance(node, dict):
            node_id = node.get("node_id") or node.get("id")
        if not node_id:
            logging.warning("Skipping existing node with no node_id while resetting project.")
            continue
        response = requests.delete(
            f"{server_url}/v2/projects/{project_id}/nodes/{node_id}",
            auth=(GNS3_USER, GNS3_PW),
        )
        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"Delete existing node '{node_id}' failed: HTTP {response.status_code}: {response.text}"
            )

    try:
        lab.get()
    except Exception as exc:
        raise RuntimeError(f"Could not refresh project after reset: {exc}") from exc

    logging.info(
        "Cleared existing project '%s' before rebuild: %d link(s), %d node(s).",
        LAB_NAME,
        len(links),
        len(nodes),
    )


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
            if RESET_EXISTING_PROJECT:
                reset_project_contents(server_url, lab)
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
    netmask {NETMASK}
"""


def build_plc_config(field_ip, operations_ip):
    """Return a dual-interface PLC configuration."""
    return f"""
auto eth0
iface eth0 inet static
    address {field_ip}
    netmask {NETMASK}

auto eth1
iface eth1 inet static
    address {operations_ip}
    netmask {NETMASK}
"""


def sensor_environment(sensor, stage_subnet):
    """Return the freshwater field sensor environment."""
    return build_environment(
        {
            "SCENARIO": SCENARIO,
            "IP_ADDRESS": sensor["ip"],
            "SUBNET": stage_subnet,
            "NETMASK": NETMASK,
            "TAG": sensor["tag"],
            "SIMULATION": "true",
            "UNITS": sensor["units"],
            "DATA_TYPE": "float",
        }
    )


def get_node_data(server_url, lab, node_name):
    """Return the current GNS3 node JSON for a project node."""
    node = lab.get_node(node_name)
    node.get()
    response = requests.get(
        f"{server_url}/v2/projects/{lab.project_id}/nodes/{node.node_id}",
        auth=(GNS3_USER, GNS3_PW),
    )
    response.raise_for_status()
    return node, response.json()


def update_docker_node_properties(server_url, lab, node_name, updates, errors):
    """Update Docker node properties while preserving the other properties."""
    try:
        node, node_data = get_node_data(server_url, lab, node_name)
        properties = dict(node_data.get("properties") or {})
        changed = False

        for key, value in updates.items():
            if properties.get(key) != value:
                properties[key] = value
                changed = True

        if not changed:
            return

        response = requests.put(
            f"{server_url}/v2/projects/{lab.project_id}/nodes/{node.node_id}",
            json={"properties": properties},
            auth=(GNS3_USER, GNS3_PW),
        )
        require_http_success(
            response,
            f"Update node '{node_name}' properties",
        )
        logging.info("Updated Docker properties for '%s'.", node_name)
    except Exception as exc:
        errors.append(
            f"Update Docker properties for node '{node_name}' failed: {exc}"
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
        node, node_data = get_node_data(server_url, lab, node_name)
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


# ---------- Freshwater runtime provisioning ----------


def verify_course_runtime_source():
    """Verify the Jenkins image contains the freshwater PLC simulator source."""
    if not os.path.isdir(COURSE_PLC_SIM_DIR):
        raise RuntimeError(
            f"Freshwater course runtime directory '{COURSE_PLC_SIM_DIR}' was not found. "
            "The Jenkins Docker build must copy course_it_ot_convergence/gns3_water_treatment/plc_sim there."
        )

    missing = [
        name
        for name in COURSE_RUNTIME_FILES
        if not os.path.isfile(os.path.join(COURSE_PLC_SIM_DIR, name))
    ]
    if missing:
        raise RuntimeError(
            "Freshwater PLC runtime is incomplete; missing files: " + ", ".join(missing)
        )


def provision_ics_node_runtime(server_url, lab, node_name, errors):
    """Install Python/pymodbus, copy the course runtime, and configure its launcher."""
    try:
        verify_course_runtime_source()
        node, _node_data = get_node_data(server_url, lab, node_name)

        # The extra volume makes the course runtime survive normal Docker
        # stop/start cycles and GNS3 topology shutdown/restart.
        update_docker_node_properties(
            server_url,
            lab,
            node_name,
            {
                "extra_volumes": [RUNTIME_DIR],
            },
            errors,
        )

        # This image currently starts as /bin/bash. Start it first so the
        # deployment can install the missing Python runtime and copy in the
        # course code.
        start_node(lab, node_name, errors)
        time.sleep(2)

        install_cmd = (
            "command -v python3 >/dev/null 2>&1 || "
            "(apt-get update && apt-get install -y --no-install-recommends python3 python3-pip)"
        )
        node.execute(install_cmd)

        install_pymodbus = (
            "python3 -m pip install --no-cache-dir pymodbus==3.5.4 "
            "|| python3 -m pip install --break-system-packages --no-cache-dir pymodbus==3.5.4"
        )
        node.execute(install_pymodbus)

        # Create the persistent package directory.
        node.execute(f"mkdir -p {RUNTIME_PACKAGE_DIR}")

        for filename in COURSE_RUNTIME_FILES:
            source_path = os.path.join(COURSE_PLC_SIM_DIR, filename)
            with open(source_path, "r", encoding="utf-8") as source_file:
                data = source_file.read()
            node.write_file(
                path=f"{RUNTIME_PACKAGE_DIR}/{filename}",
                data=data,
            )

        launcher = f"""#!/bin/bash
set -e
export PYTHONPATH={RUNTIME_DIR}
exec python3 -m plc_sim.node_entrypoint
"""
        node.write_file(path=RUNTIME_LAUNCHER, data=launcher)
        node.execute(f"chmod +x {RUNTIME_LAUNCHER}")

        update_docker_node_properties(
            server_url,
            lab,
            node_name,
            {
                "extra_volumes": [RUNTIME_DIR],
                "start_command": RUNTIME_START_COMMAND,
            },
            errors,
        )

        # Restart so the new Docker start command becomes PID 1.
        node.get()
        status = getattr(node.status, "value", str(node.status)).lower()
        if status == "started":
            node.stop()
            time.sleep(1)
        node.start()

        logging.info(
            "Provisioned freshwater PLC/HMI runtime on '%s' using %s.",
            node_name,
            RUNTIME_START_COMMAND,
        )
    except Exception as exc:
        errors.append(
            f"Provision freshwater runtime on node '{node_name}' failed: {exc}"
        )


def provision_all_ics_nodes(server_url, lab, errors):
    """Provision the actual freshwater Python runtime on all six ics-node containers."""
    runtime_nodes = [
        stage["plc"] for stage in FRESHWATER_STAGES
    ] + ["hmi-poller", "historian"]

    for node_name in runtime_nodes:
        provision_ics_node_runtime(server_url, lab, node_name, errors)


# ---------- Freshwater topology ----------


def create_scenario_nodes(lab, errors):
    """Create four freshwater field networks with four sensors each and operations services."""
    create_node(lab, "ops-switch", CORE_SWITCH_TEMPLATE, 0, 120, errors)

    for stage in FRESHWATER_STAGES:
        x = stage["x"]

        for index, sensor in enumerate(stage["sensors"]):
            create_node(
                lab,
                sensor["name"],
                SENSOR_TEMPLATE,
                x - 120 + (index * 80),
                -600,
                errors,
            )

        create_node(
            lab,
            stage["field_switch"],
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

    configure_interfaces(lab, "hmi-poller", build_interface_config("10.10.20.20"), errors)
    configure_interfaces(lab, "historian", build_interface_config("10.10.20.30"), errors)
    configure_interfaces(lab, "scada-server", build_interface_config(SCADA_IP), errors)


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
                sensor_environment(sensor, stage["field_subnet"]),
                errors,
            )

    set_docker_node_environment(
        server_url,
        lab,
        "hmi-poller",
        build_environment(HMI_ENV),
        errors,
    )
    set_docker_node_environment(
        server_url,
        lab,
        "historian",
        build_environment(HISTORIAN_ENV),
        errors,
    )
    set_docker_node_environment(
        server_url,
        lab,
        "scada-server",
        build_environment(SCADA_ENV),
        errors,
    )


def start_scenario_nodes(lab, errors):
    """Start all freshwater field sensors/switches and the non-ics operation nodes."""
    start_node(lab, "ops-switch", errors)

    for stage in FRESHWATER_STAGES:
        for sensor in stage["sensors"]:
            start_node(lab, sensor["name"], errors)
        start_node(lab, stage["field_switch"], errors)
        # PLC/HMI/historian nodes are started by runtime provisioning below.

    start_node(lab, "scada-server", errors)


def create_scenario_links(lab, errors):
    """Connect the freshwater field networks to their PLCs and the operations LAN."""
    ops_ports = ["Ethernet0", "Ethernet1", "Ethernet2", "Ethernet3"]

    for stage_index, stage in enumerate(FRESHWATER_STAGES):
        field_switch = stage["field_switch"]

        # Four sensors plus the PLC share this field network.
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

        # PLC eth1 is the SCADA/operations interface.
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


# ---------- Main deployment ----------


def build_project_on_server(server_url):
    """Build the complete freshwater treatment project on one GNS3 server."""
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

    verify_course_runtime_source()

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

    logging.info("Applying freshwater network configuration on %s.", server_url)
    configure_scenario_nodes(lab, errors)

    try:
        lab.get()
    except Exception as exc:
        errors.append(
            f"Refresh project inventory after network configuration failed: {exc}"
        )

    logging.info("Creating freshwater topology links on %s.", server_url)
    create_scenario_links(lab, errors)

    logging.info("Starting freshwater field and operations nodes on %s.", server_url)
    start_scenario_nodes(lab, errors)

    # This is the critical step missing from the earlier deployment: the
    # server's ics-node image is only a shell, so provision the actual course
    # plc_sim runtime and restart the six ics-node containers with it.
    logging.info("Provisioning freshwater Python runtime on PLC/HMI/historian nodes.")
    provision_all_ics_nodes(server_url, lab, errors)

    # Do not fail the build over the QEMU guest-console issue we saw earlier.
    # Kali remains connected to the operations switch at 10.10.20.250 but is
    # not configured automatically here.
    if errors:
        raise RuntimeError("\n".join(f"{server_url}: {error}" for error in errors))

    logging.info("Nodes created, configured, provisioned, and linked. Link summary follows.")
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
