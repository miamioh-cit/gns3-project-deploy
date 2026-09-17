#!/usr/bin/env python3
"""
Build the CIT 480-4 manufacturing risk GNS3 project.

Manufacturing process:
    conveyor -> robot cell -> packaging -> quality

Each manufacturing area has:
    - 4 field sensors
    - 1 field switch
    - 1 dual-homed PLC

Central operations network:
    - ops-switch
    - HMI polling node
    - Historian
    - SCADA
    - Kali Linux

The manufacturing SCADA image is:
    evankunkel/generic-scada-manafacturing:latest

IMPORTANT:
    Jenkins is responsible for building and pushing the manufacturing
    SCADA Docker image before this deployment script runs.

    This script does NOT build the Docker image.

    This script only:
        - synchronizes the GNS3 SCADA template
        - creates the manufacturing topology
        - applies Docker environments
        - applies network configuration
        - creates links
        - starts the nodes

The SCADA startup remains the normal WTaylor SCADA startup.

The script is safe to rerun against the same project:
    - managed nodes are removed first
    - their links disappear with them
    - clean nodes are recreated
    - the manufacturing SCADA template is synchronized
    - environments and networks are reapplied
    - links are recreated
    - everything is restarted
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import requests
from gns3fy import Gns3Connector, Project


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


# ---------------------------------------------------------------------------
# Global configuration
# ---------------------------------------------------------------------------

LAB_NAME = "Module 4 - Manufacturing - Risk"

BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "manufacturing"

OPERATIONS_SUBNET = "10.10.40.0/24"
OPERATIONS_NETMASK = "255.255.255.0"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
FIELD_SWITCH_TEMPLATE = "Ethernet-Switch-10P"

MANUFACTURING_SCADA_TEMPLATE = "generic-scada-manufacturing"

# IMPORTANT:
# Keep the Docker Hub repository spelling exactly as this.
MANUFACTURING_SCADA_IMAGE = (
    "evankunkel/generic-scada-manafacturing:latest"
)

SCADA_IP = "10.10.40.200"
HMI_IP = "10.10.40.20"
HISTORIAN_IP = "10.10.40.30"
KALI_IP = "10.10.40.250"


# ---------------------------------------------------------------------------
# Required GNS3 templates
# ---------------------------------------------------------------------------

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
        "name": MANUFACTURING_SCADA_TEMPLATE,
        "template_type": "docker",
        "category": "guest",
        "image": MANUFACTURING_SCADA_IMAGE,
        "adapters": 11,
        "console_type": "http",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
]


# ---------------------------------------------------------------------------
# Manufacturing areas
# ---------------------------------------------------------------------------

AREAS = [
    {
        "name": "conveyor",
        "label": "Conveyor",
        "field_switch": "field-switch-conveyor",
        "field_subnet": "192.168.10.0/24",
        "field_ip": "192.168.10.5",
        "plc": "plc-conveyor",
        "plc_ops_ip": "10.10.40.11",
        "core_port": "Ethernet0",
        "x": -600,
        "device_age": 8,
        "sensors": [
            (
                "SPEED-101",
                "192.168.10.1",
                "SPEED-101",
                "rpm",
                "float",
            ),
            (
                "PROX-101",
                "192.168.10.2",
                "PROX-101",
                "state",
                "float",
            ),
            (
                "TEMP-101",
                "192.168.10.3",
                "TEMP-101",
                "C",
                "float",
            ),
            (
                "JAM-101",
                "192.168.10.4",
                "JAM-101",
                "flag",
                "float",
            ),
        ],
    },
    {
        "name": "robot_cell",
        "label": "Robot Cell",
        "field_switch": "field-switch-robot-cell",
        "field_subnet": "192.168.20.0/24",
        "field_ip": "192.168.20.5",
        "plc": "plc-robot-cell",
        "plc_ops_ip": "10.10.40.12",
        "core_port": "Ethernet1",
        "x": -200,
        "device_age": 10,
        "sensors": [
            (
                "POS-201",
                "192.168.20.1",
                "POS-201",
                "mm",
                "float",
            ),
            (
                "PROX-201",
                "192.168.20.2",
                "PROX-201",
                "state",
                "float",
            ),
            (
                "TEMP-201",
                "192.168.20.3",
                "TEMP-201",
                "C",
                "float",
            ),
            (
                "TORQUE-201",
                "192.168.20.4",
                "TORQUE-201",
                "Nm",
                "float",
            ),
        ],
    },
    {
        "name": "packaging",
        "label": "Packaging",
        "field_switch": "field-switch-packaging",
        "field_subnet": "192.168.30.0/24",
        "field_ip": "192.168.30.5",
        "plc": "plc-packaging",
        "plc_ops_ip": "10.10.40.13",
        "core_port": "Ethernet2",
        "x": 200,
        "device_age": 17,
        "sensors": [
            (
                "COUNT-301",
                "192.168.30.1",
                "COUNT-301",
                "units/min",
                "float",
            ),
            (
                "WEIGHT-301",
                "192.168.30.2",
                "WEIGHT-301",
                "kg",
                "float",
            ),
            (
                "TEMP-301",
                "192.168.30.3",
                "TEMP-301",
                "C",
                "float",
            ),
            (
                "SEAL-301",
                "192.168.30.4",
                "SEAL-301",
                "state",
                "float",
            ),
        ],
    },
    {
        "name": "quality",
        "label": "Quality",
        "field_switch": "field-switch-quality",
        "field_subnet": "192.168.40.0/24",
        "field_ip": "192.168.40.5",
        "plc": "plc-quality",
        "plc_ops_ip": "10.10.40.14",
        "core_port": "Ethernet3",
        "x": 600,
        "device_age": 12,
        "sensors": [
            (
                "CAM-401",
                "192.168.40.1",
                "CAM-401",
                "score",
                "float",
            ),
            (
                "REJECT-401",
                "192.168.40.2",
                "REJECT-401",
                "count",
                "float",
            ),
            (
                "VIB-401",
                "192.168.40.3",
                "VIB-401",
                "mm/s",
                "float",
            ),
            (
                "TEMP-401",
                "192.168.40.4",
                "TEMP-401",
                "C",
                "float",
            ),
        ],
    },
]


# ---------------------------------------------------------------------------
# Sensor simulation profiles
# ---------------------------------------------------------------------------

SENSOR_SIMULATION = {
    "SPEED-101":
        "random_walk:start=1200,step=25,min=900,max=1500",

    "PROX-101":
        "random_walk:start=1,step=0,min=0,max=1",

    "TEMP-101":
        "random_walk:start=36,step=0.5,min=25,max=50",

    "JAM-101":
        "random_walk:start=0,step=0,min=0,max=1",

    "POS-201":
        "random_walk:start=125,step=4,min=80,max=180",

    "PROX-201":
        "random_walk:start=1,step=0,min=0,max=1",

    "TEMP-201":
        "random_walk:start=42,step=0.6,min=30,max=60",

    "TORQUE-201":
        "random_walk:start=55,step=2,min=30,max=80",

    "COUNT-301":
        "random_walk:start=42,step=2,min=25,max=60",

    "WEIGHT-301":
        "random_walk:start=18,step=0.4,min=10,max=25",

    "TEMP-301":
        "random_walk:start=39,step=0.5,min=28,max=52",

    "SEAL-301":
        "random_walk:start=1,step=0,min=0,max=1",

    "CAM-401":
        "random_walk:start=95,step=1.0,min=80,max=100",

    "REJECT-401":
        "random_walk:start=2,step=1,min=0,max=10",

    "VIB-401":
        "random_walk:start=3.5,step=0.15,min=1,max=7",

    "TEMP-401":
        "random_walk:start=37,step=0.5,min=28,max=50",
}


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def build_environment(**values: object) -> str:
    return "\n".join(
        f"{key}={value}"
        for key, value in values.items()
    )


def read_server_urls() -> list[str]:
    path = Path(DATASTORE_FILE)

    if not path.exists():
        raise RuntimeError(
            f"Required file '{DATASTORE_FILE}' was not found."
        )

    content = path.read_text(
        encoding="utf-8"
    ).strip()

    if not content:
        raise RuntimeError(
            f"Required file '{DATASTORE_FILE}' is empty."
        )

    urls: list[str] = []

    for item in content.split(","):
        item = item.strip()

        if not item:
            continue

        if not item.isdigit():
            raise RuntimeError(
                f"Invalid datastore entry '{item}'. "
                "Expected comma-separated last octets."
            )

        urls.append(
            f"{BASE_IP}{int(item)}:80"
        )

    if not urls:
        raise RuntimeError(
            f"No valid GNS3 server last octets found "
            f"in '{DATASTORE_FILE}'."
        )

    return urls


def require_http_success(
    response: requests.Response,
    action: str,
) -> None:

    if response.status_code not in (
        200,
        201,
        204,
    ):
        raise RuntimeError(
            f"{action} failed: "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )


# ---------------------------------------------------------------------------
# GNS3 template setup
# ---------------------------------------------------------------------------

def ensure_10_port_switch(
    server_url: str,
) -> None:

    try:
        response = requests.get(
            f"{server_url}/v2/templates",
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not list templates on "
            f"{server_url}: {exc}"
        ) from exc

    existing = next(
        (
            template
            for template in response.json()
            if template.get("name")
            == CORE_SWITCH_TEMPLATE
        ),
        None,
    )

    if existing:
        logging.info(
            "Template '%s' already exists on %s.",
            CORE_SWITCH_TEMPLATE,
            server_url,
        )
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
        "name": CORE_SWITCH_TEMPLATE,
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
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        require_http_success(
            response,
            f"Create template "
            f"'{CORE_SWITCH_TEMPLATE}' on "
            f"{server_url}",
        )

    except requests.RequestException as exc:

        raise RuntimeError(
            f"Network error creating "
            f"'{CORE_SWITCH_TEMPLATE}' on "
            f"{server_url}: {exc}"
        ) from exc

    logging.info(
        "Created template '%s' with %d ports on %s.",
        CORE_SWITCH_TEMPLATE,
        len(ports),
        server_url,
    )


def update_template(
    server_url: str,
    template: dict,
    expected_definition: dict,
) -> None:

    template_name = template["name"]

    template_id = template.get(
        "template_id"
    )

    if not template_id:
        raise RuntimeError(
            f"Template '{template_name}' on {server_url} "
            "has no template_id."
        )

    logging.info(
        "Template '%s' current image=%r, "
        "expected image=%r",
        template_name,
        template.get("image"),
        expected_definition.get("image"),
    )

    changes: dict[str, object] = {}

    for key in (
        "template_type",
        "category",
        "image",
        "adapters",
        "console_type",
        "environment",
        "default_name_format",
        "compute_id",
        "symbol",
    ):

        if key not in expected_definition:
            continue

        expected_value = expected_definition[key]

        if template.get(key) != expected_value:
            changes[key] = expected_value

    if not changes:
        logging.info(
            "Template '%s' is already up to date.",
            template_name,
        )
        return

    updated = dict(template)

    updated.update(
        changes
    )

    try:

        response = requests.put(
            f"{server_url}/v2/templates/{template_id}",
            json=updated,
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        require_http_success(
            response,
            f"Update template '{template_name}' "
            f"on {server_url}",
        )

    except requests.RequestException as exc:

        raise RuntimeError(
            f"Network error updating "
            f"'{template_name}' on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Updated template '%s' on %s: %s",
        template_name,
        server_url,
        ", ".join(
            f"{key}={value!r}"
            for key, value in changes.items()
        ),
    )


def ensure_required_templates(
    server: Gns3Connector,
    server_url: str,
) -> None:

    try:

        available = server.get_templates()

    except Exception as exc:

        raise RuntimeError(
            f"Could not list GNS3 templates on "
            f"{server_url}: {exc}"
        ) from exc

    templates_by_name = {
        template["name"]: template
        for template in available
    }

    for template in REQUIRED_TEMPLATES:

        existing = templates_by_name.get(
            template["name"]
        )

        if existing:

            update_template(
                server_url,
                existing,
                template,
            )

            continue

        try:

            response = requests.post(
                f"{server_url}/v2/templates",
                json=template,
                auth=(
                    GNS3_USER,
                    GNS3_PW,
                ),
                timeout=30,
            )

            require_http_success(
                response,
                f"Register template "
                f"'{template['name']}' on "
                f"{server_url}",
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                f"Network error registering "
                f"template '{template['name']}' "
                f"on {server_url}: {exc}"
            ) from exc

        logging.info(
            "Registered template '%s' on %s.",
            template["name"],
            server_url,
        )


# ---------------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------------

def open_or_create_project(
    server: Gns3Connector,
    server_url: str,
) -> Project:

    try:

        projects = server.get_projects()

    except Exception as exc:

        raise RuntimeError(
            f"Could not list projects on "
            f"{server_url}: {exc}"
        ) from exc

    existing = next(
        (
            project
            for project in projects
            if project["name"] == LAB_NAME
        ),
        None,
    )

    try:

        if existing:

            lab = Project(
                project_id=existing["project_id"],
                connector=server,
            )

            lab.get()
            lab.open()

            logging.info(
                "Opened existing project '%s' on %s.",
                LAB_NAME,
                server_url,
            )

        else:

            lab = Project(
                name=LAB_NAME,
                connector=server,
            )

            lab.create()
            lab.open()

            logging.info(
                "Created project '%s' on %s.",
                LAB_NAME,
                server_url,
            )

    except Exception as exc:

        raise RuntimeError(
            f"Could not open/create project "
            f"'{LAB_NAME}' on {server_url}: {exc}"
        ) from exc

    return lab


def create_node(
    lab: Project,
    name: str,
    template: str,
    x: int,
    y: int,
    errors: list[str],
) -> None:

    try:

        lab.create_node(
            name=name,
            template=template,
            x=x,
            y=y,
        )

        logging.info(
            "Created node '%s' with template '%s'.",
            name,
            template,
        )

    except Exception as exc:

        errors.append(
            f"Create node '{name}' using template "
            f"'{template}' failed: {exc}"
        )


# ---------------------------------------------------------------------------
# Managed node cleanup
# ---------------------------------------------------------------------------

def managed_node_names() -> set[str]:

    names: set[str] = set()

    for area in AREAS:

        names.add(
            area["field_switch"]
        )

        names.add(
            area["plc"]
        )

        for sensor_name, *_ in area["sensors"]:
            names.add(sensor_name)

    names.update(
        {
            "ops-switch",
            "line-hmi",
            "line-historian",
            "scada-server",
            "KaliLinux-1",

            # Older naming used by earlier versions.
            "hmi-poller",
            "historian",
        }
    )

    return names


def is_managed_node_name(
    node_name: str,
    base_names: set[str],
) -> bool:

    for base_name in base_names:

        if node_name == base_name:
            return True

        if not node_name.startswith(
            base_name
        ):
            continue

        suffix = node_name[
            len(base_name):
        ]

        if suffix.isdigit():
            return True

    return False


def remove_existing_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:

    try:

        lab.get()

        base_names = managed_node_names()

        existing_nodes = list(
            lab.nodes
        )

        for node in existing_nodes:

            node_name = node.name

            if not is_managed_node_name(
                node_name,
                base_names,
            ):
                continue

            try:

                logging.info(
                    "Removing existing 480-4 node '%s'.",
                    node_name,
                )

                try:

                    status = getattr(
                        node.status,
                        "value",
                        str(node.status),
                    ).lower()

                    if status == "started":

                        node.stop()

                        logging.info(
                            "Stopped existing node '%s'.",
                            node_name,
                        )

                except Exception as stop_exc:

                    logging.warning(
                        "Could not stop existing node '%s' "
                        "before deletion: %s",
                        node_name,
                        stop_exc,
                    )

                node.delete()

                logging.info(
                    "Deleted existing node '%s'.",
                    node_name,
                )

            except Exception as exc:

                errors.append(
                    f"Delete existing node "
                    f"'{node_name}' failed: {exc}"
                )

        lab.get()

    except Exception as exc:

        errors.append(
            "Refresh/remove existing 480-4 nodes failed: "
            f"{exc}"
        )


# ---------------------------------------------------------------------------
# Docker node environment
# ---------------------------------------------------------------------------

def set_docker_node_environment(
    server_url: str,
    lab: Project,
    node_name: str,
    environment: str,
    errors: list[str],
) -> None:

    try:

        node = lab.get_node(
            node_name
        )

        node.get()

        response = requests.get(
            f"{server_url}/v2/projects/"
            f"{lab.project_id}/nodes/"
            f"{node.node_id}",
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        response.raise_for_status()

        node_data = response.json()

        properties = dict(
            node_data.get("properties") or {}
        )

        actual_environment = (
            properties.get("environment")
        )

        if actual_environment == environment:

            logging.info(
                "Node '%s' already has "
                "the requested environment.",
                node_name,
            )

            return

        properties["environment"] = environment

        response = requests.put(
            f"{server_url}/v2/projects/"
            f"{lab.project_id}/nodes/"
            f"{node.node_id}",
            json={
                "properties": properties
            },
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        require_http_success(
            response,
            f"Update node '{node_name}' "
            f"environment",
        )

        logging.info(
            "Updated node '%s' environment.",
            node_name,
        )

    except Exception as exc:

        errors.append(
            f"Set environment for node "
            f"'{node_name}' failed: {exc}"
        )


# ---------------------------------------------------------------------------
# Network configuration
# ---------------------------------------------------------------------------

def configure_interfaces(
    lab: Project,
    node_name: str,
    config: str,
    errors: list[str],
) -> None:

    try:

        node = lab.get_node(
            node_name
        )

        node.get()

        status = getattr(
            node.status,
            "value",
            str(node.status),
        ).lower()

        was_running = (
            status == "started"
        )

        if was_running:
            node.stop()

        node.write_file(
            path="/etc/network/interfaces",
            data=config.strip() + "\n",
        )

        if was_running:
            node.start()

        logging.info(
            "Configured network for '%s'.",
            node_name,
        )

    except Exception as exc:

        errors.append(
            f"Configure network for node "
            f"'{node_name}' failed: {exc}"
        )


def build_single_interface_config(
    ip_address: str,
) -> str:

    return f"""
auto eth0
iface eth0 inet static
    address {ip_address}
    netmask {OPERATIONS_NETMASK}
""".strip()


def build_plc_interface_config(
    field_ip: str,
    operations_ip: str,
) -> str:

    return f"""
auto eth0
iface eth0 inet static
    address {field_ip}
    netmask {OPERATIONS_NETMASK}

auto eth1
iface eth1 inet static
    address {operations_ip}
    netmask {OPERATIONS_NETMASK}
""".strip()


# ---------------------------------------------------------------------------
# Environment builders
# ---------------------------------------------------------------------------

def plc_environment(
    area: dict,
) -> str:

    return build_environment(

        SCENARIO=SCENARIO,

        NODE_MODE="plc",

        PLC_ROLE=area["name"],

        FIELD_IP_ADDRESS=area["field_ip"],

        FIELD_SUBNET=area["field_subnet"],

        IP_ADDRESS=area["plc_ops_ip"],

        NETMASK=OPERATIONS_NETMASK,

        DEVICE_AGE_YEARS=area["device_age"],

        AGE_FAILURE_THRESHOLD_YEARS=12,

        AGE_FAILURE_WINDOW_SECONDS=10,

        AGE_FAILURE_MAX_REQUESTS=30,

        AGE_FAILURE_DURATION_SECONDS=20,

        AGE_FAILURE_MODE="zero",

        PLC_SCAN_SUBNETS=area["field_subnet"],

        PLC_FIELD_INTERFACE="eth0",

        PLC_FIELD_IP=area["field_ip"],

        PLC_FIELD_SUBNET=area["field_subnet"],

        PLC_CONTROL_INTERFACE="eth1",

        PLC_CONTROL_IP=area["plc_ops_ip"],

        PLC_CONTROL_SUBNET=OPERATIONS_SUBNET,

        PLC_MODBUS_PORT=502,
    )


def hmi_environment() -> str:

    plc_targets = " ".join(
        f"--plc {area['name']}="
        f"{area['plc_ops_ip']}:502"
        for area in AREAS
    )

    return build_environment(

        SCENARIO=SCENARIO,

        NODE_MODE="hmi",

        IP_ADDRESS=HMI_IP,

        NETMASK=OPERATIONS_NETMASK,

        PLC_TARGETS=plc_targets,
    )


def historian_environment() -> str:

    plc_targets = " ".join(
        f"--plc {area['name']}="
        f"{area['plc_ops_ip']}:502"
        for area in AREAS
    )

    return build_environment(

        SCENARIO=SCENARIO,

        NODE_MODE="historian",

        IP_ADDRESS=HISTORIAN_IP,

        NETMASK=OPERATIONS_NETMASK,

        PLC_TARGETS=plc_targets,
    )


def scada_environment() -> str:
    return build_environment(
        SCENARIO=SCENARIO,
        SCADA_SUBNETS=OPERATIONS_SUBNET,
        SCADA_DIAGRAM_CONFIG="manufacturing/diagrams.yaml",
        IP_ADDRESS=SCADA_IP,
        NETMASK=OPERATIONS_NETMASK,
    )


def sensor_environment(
    area: dict,
    sensor_ip: str,
    tag: str,
    units: str,
    data_type: str,
) -> str:

    simulation = SENSOR_SIMULATION.get(
        tag,
        "random_walk:start=50,step=1,min=0,max=100",
    )

    return build_environment(

        SCENARIO=SCENARIO,

        TAG=tag,

        SIMULATION=simulation,

        UNITS=units,

        DATA_TYPE=data_type,

        IP_ADDRESS=sensor_ip,

        NETMASK=OPERATIONS_NETMASK,

        FIELD_SUBNET=area["field_subnet"],
    )


# ---------------------------------------------------------------------------
# Node creation
# ---------------------------------------------------------------------------

def create_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:

    for area in AREAS:

        x = area["x"]

        for index, (
            sensor_name,
            _ip,
            _tag,
            _units,
            _type,
        ) in enumerate(
            area["sensors"]
        ):

            create_node(
                lab,
                sensor_name,
                "generic-sensor",
                x - 140 + index * 90,
                -520,
                errors,
            )

        create_node(
            lab,
            area["field_switch"],
            FIELD_SWITCH_TEMPLATE,
            x + 120,
            -360,
            errors,
        )

        create_node(
            lab,
            area["plc"],
            "generic-plc",
            x + 120,
            -210,
            errors,
        )

    create_node(
        lab,
        "ops-switch",
        CORE_SWITCH_TEMPLATE,
        0,
        40,
        errors,
    )

    create_node(
        lab,
        "line-hmi",
        "generic-hmi",
        -260,
        40,
        errors,
    )

    create_node(
        lab,
        "line-historian",
        "generic-hmi",
        0,
        220,
        errors,
    )

    create_node(
        lab,
        "scada-server",
        MANUFACTURING_SCADA_TEMPLATE,
        260,
        40,
        errors,
    )

    create_node(
        lab,
        "KaliLinux-1",
        "Kali Linux",
        520,
        40,
        errors,
    )


# ---------------------------------------------------------------------------
# Environment verification
# ---------------------------------------------------------------------------

def verify_scenario_environments(
    server_url: str,
    lab: Project,
    errors: list[str],
) -> None:

    expected_nodes: list[tuple[str, str]] = []

    for area in AREAS:

        expected_nodes.append(
            (
                area["plc"],
                plc_environment(area),
            )
        )

        for (
            sensor_name,
            sensor_ip,
            tag,
            units,
            data_type,
        ) in area["sensors"]:

            expected_nodes.append(
                (
                    sensor_name,
                    sensor_environment(
                        area,
                        sensor_ip,
                        tag,
                        units,
                        data_type,
                    ),
                )
            )

    expected_nodes.extend(
        [
            (
                "line-hmi",
                hmi_environment(),
            ),
            (
                "line-historian",
                historian_environment(),
            ),
            (
                "scada-server",
                scada_environment(),
            ),
        ]
    )

    for node_name, expected in expected_nodes:

        try:

            node = lab.get_node(
                node_name
            )

            node.get()

            response = requests.get(
                f"{server_url}/v2/projects/"
                f"{lab.project_id}/nodes/"
                f"{node.node_id}",
                auth=(
                    GNS3_USER,
                    GNS3_PW,
                ),
                timeout=30,
            )

            response.raise_for_status()

            actual = (
                response.json()
                .get("properties", {})
                .get("environment", "")
            )

            if actual != expected:

                errors.append(
                    f"Environment verification failed "
                    f"for '{node_name}'. "
                    f"Expected {expected!r}, "
                    f"got {actual!r}"
                )

        except Exception as exc:

            errors.append(
                f"Environment verification for "
                f"'{node_name}' failed: {exc}"
            )


# ---------------------------------------------------------------------------
# Apply network configuration
# ---------------------------------------------------------------------------

def configure_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:

    for area in AREAS:

        configure_interfaces(
            lab,
            area["plc"],
            build_plc_interface_config(
                area["field_ip"],
                area["plc_ops_ip"],
            ),
            errors,
        )

        for (
            sensor_name,
            sensor_ip,
            _tag,
            _units,
            _data_type,
        ) in area["sensors"]:

            configure_interfaces(
                lab,
                sensor_name,
                build_single_interface_config(
                    sensor_ip
                ),
                errors,
            )

    configure_interfaces(
        lab,
        "line-hmi",
        build_single_interface_config(
            HMI_IP
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "line-historian",
        build_single_interface_config(
            HISTORIAN_IP
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "scada-server",
        build_single_interface_config(
            SCADA_IP
        ),
        errors,
    )


# ---------------------------------------------------------------------------
# Apply Docker environments
# ---------------------------------------------------------------------------

def set_scenario_environments(
    server_url: str,
    lab: Project,
    errors: list[str],
) -> None:

    for area in AREAS:

        set_docker_node_environment(
            server_url,
            lab,
            area["plc"],
            plc_environment(area),
            errors,
        )

        for (
            sensor_name,
            sensor_ip,
            tag,
            units,
            data_type,
        ) in area["sensors"]:

            set_docker_node_environment(
                server_url,
                lab,
                sensor_name,
                sensor_environment(
                    area,
                    sensor_ip,
                    tag,
                    units,
                    data_type,
                ),
                errors,
            )

    set_docker_node_environment(
        server_url,
        lab,
        "line-hmi",
        hmi_environment(),
        errors,
    )

    set_docker_node_environment(
        server_url,
        lab,
        "line-historian",
        historian_environment(),
        errors,
    )

    set_docker_node_environment(
        server_url,
        lab,
        "scada-server",
        scada_environment(),
        errors,
    )


# ---------------------------------------------------------------------------
# Stop/start helpers
# ---------------------------------------------------------------------------

def stop_node(
    lab: Project,
    node_name: str,
    errors: list[str],
) -> None:

    try:

        node = lab.get_node(
            node_name
        )

        node.get()

        status = getattr(
            node.status,
            "value",
            str(node.status),
        ).lower()

        if status == "started":

            node.stop()

            logging.info(
                "Stopped node '%s' before applying configuration.",
                node_name,
            )

    except Exception as exc:

        errors.append(
            f"Stop node '{node_name}' failed: {exc}"
        )


def stop_configurable_nodes(
    lab: Project,
    errors: list[str],
) -> None:

    for area in AREAS:

        stop_node(
            lab,
            area["plc"],
            errors,
        )

        for (
            sensor_name,
            _ip,
            _tag,
            _units,
            _data_type,
        ) in area["sensors"]:

            stop_node(
                lab,
                sensor_name,
                errors,
            )

    for node_name in (
        "line-hmi",
        "line-historian",
        "scada-server",
    ):

        stop_node(
            lab,
            node_name,
            errors,
        )


def start_node(
    lab: Project,
    node_name: str,
    errors: list[str],
) -> None:

    try:

        node = lab.get_node(
            node_name
        )

        node.get()

        status = getattr(
            node.status,
            "value",
            str(node.status),
        ).lower()

        if status == "started":
            return

        node.start()

        logging.info(
            "Started node '%s'.",
            node_name,
        )

    except Exception as exc:

        errors.append(
            f"Start node '{node_name}' failed: {exc}"
        )


def start_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:

    # Start field sensors before their PLCs.
    # This allows the PLC discovery scan to see the sensors.
    for area in AREAS:

        for (
            sensor_name,
            _ip,
            _tag,
            _units,
            _data_type,
        ) in area["sensors"]:

            start_node(
                lab,
                sensor_name,
                errors,
            )

        start_node(
            lab,
            area["plc"],
            errors,
        )

    start_node(
        lab,
        "line-hmi",
        errors,
    )

    start_node(
        lab,
        "line-historian",
        errors,
    )

    start_node(
        lab,
        "scada-server",
        errors,
    )

    # Kali is intentionally started but NOT configured.
    start_node(
        lab,
        "KaliLinux-1",
        errors,
    )

    logging.info(
        "Skipping automated Kali configuration for "
        "'KaliLinux-1'."
    )


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def create_link(
    lab: Project,
    node_a: str,
    port_a: str,
    node_b: str,
    port_b: str,
    errors: list[str],
) -> None:

    try:

        lab.create_link(
            node_a,
            port_a,
            node_b,
            port_b,
        )

        logging.info(
            "Linked %s:%s -> %s:%s.",
            node_a,
            port_a,
            node_b,
            port_b,
        )

    except Exception as exc:

        errors.append(
            f"Create link {node_a}:{port_a} -> "
            f"{node_b}:{port_b} failed: {exc}"
        )


def create_scenario_links(
    lab: Project,
    errors: list[str],
) -> None:

    for area in AREAS:

        # PLC field side -> field switch
        create_link(
            lab,
            area["plc"],
            "eth0",
            area["field_switch"],
            "Ethernet0",
            errors,
        )

        # Four field sensors -> field switch
        for index, (
            sensor_name,
            _ip,
            _tag,
            _units,
            _data_type,
        ) in enumerate(
            area["sensors"],
            start=1,
        ):

            create_link(
                lab,
                sensor_name,
                "eth0",
                area["field_switch"],
                f"Ethernet{index}",
                errors,
            )

        # PLC control side -> central operations switch
        create_link(
            lab,
            area["plc"],
            "eth1",
            "ops-switch",
            area["core_port"],
            errors,
        )

    # Central operations network
    create_link(
        lab,
        "line-hmi",
        "eth0",
        "ops-switch",
        "Ethernet4",
        errors,
    )

    create_link(
        lab,
        "line-historian",
        "eth0",
        "ops-switch",
        "Ethernet5",
        errors,
    )

    create_link(
        lab,
        "scada-server",
        "eth0",
        "ops-switch",
        "Ethernet6",
        errors,
    )

    create_link(
        lab,
        "KaliLinux-1",
        "Ethernet0",
        "ops-switch",
        "Ethernet7",
        errors,
    )


# ---------------------------------------------------------------------------
# Build project
# ---------------------------------------------------------------------------

def build_project_on_server(
    server_url: str,
) -> None:

    errors: list[str] = []

    logging.info(
        "Connecting to GNS3 server at %s.",
        server_url,
    )

    server = Gns3Connector(
        url=server_url,
        user=GNS3_USER,
        cred=GNS3_PW,
    )

    try:

        logging.info(
            "GNS3 server version at %s: %s",
            server_url,
            server.get_version(),
        )

        ensure_10_port_switch(
            server_url
        )

        ensure_required_templates(
            server,
            server_url,
        )

        lab = open_or_create_project(
            server,
            server_url,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Project setup failed on "
            f"{server_url}: {exc}"
        ) from exc

    # -----------------------------------------------------------------------
    # Clean stale managed nodes.
    # -----------------------------------------------------------------------

    logging.info(
        "Cleaning up existing manufacturing nodes for '%s' on %s.",
        LAB_NAME,
        server_url,
    )

    remove_existing_scenario_nodes(
        lab,
        errors,
    )

    if errors:

        raise RuntimeError(
            "\n".join(
                f"{server_url}: {error}"
                for error in errors
            )
        )

    logging.info(
        "Existing 480-4 managed nodes removed successfully."
    )

    # -----------------------------------------------------------------------
    # Create topology.
    # -----------------------------------------------------------------------

    logging.info(
        "Creating manufacturing nodes for '%s' on %s.",
        LAB_NAME,
        server_url,
    )

    create_scenario_nodes(
        lab,
        errors,
    )

    if errors:

        raise RuntimeError(
            "\n".join(
                f"{server_url}: {error}"
                for error in errors
            )
        )

    try:

        lab.get()

    except Exception as exc:

        errors.append(
            "Refresh project inventory after "
            f"node creation failed: {exc}"
        )

    # -----------------------------------------------------------------------
    # Configure Docker nodes.
    # -----------------------------------------------------------------------

    logging.info(
        "Stopping Docker nodes before applying environment changes."
    )

    stop_configurable_nodes(
        lab,
        errors,
    )

    logging.info(
        "Applying Docker environments on %s.",
        server_url,
    )

    set_scenario_environments(
        server_url,
        lab,
        errors,
    )

    if not errors:

        logging.info(
            "Verifying Docker environments on %s.",
            server_url,
        )

        verify_scenario_environments(
            server_url,
            lab,
            errors,
        )

    # -----------------------------------------------------------------------
    # Configure interfaces.
    # -----------------------------------------------------------------------

    logging.info(
        "Applying network configurations."
    )

    configure_scenario_nodes(
        lab,
        errors,
    )

    try:

        lab.get()

    except Exception as exc:

        errors.append(
            "Refresh project inventory after "
            f"network configuration failed: {exc}"
        )

    # -----------------------------------------------------------------------
    # Create links.
    # -----------------------------------------------------------------------

    logging.info(
        "Creating manufacturing links."
    )

    create_scenario_links(
        lab,
        errors,
    )

    if errors:

        raise RuntimeError(
            "\n".join(
                f"{server_url}: {error}"
                for error in errors
            )
        )

    # -----------------------------------------------------------------------
    # Start everything.
    #
    # The SCADA Docker image should already have been built and pushed
    # by Jenkins before this script reaches this point.
    # -----------------------------------------------------------------------

    logging.info(
        "Using SCADA image: %s",
        MANUFACTURING_SCADA_IMAGE,
    )

    logging.info(
        "Starting manufacturing nodes."
    )

    start_scenario_nodes(
        lab,
        errors,
    )

    if errors:

        raise RuntimeError(
            "\n".join(
                f"{server_url}: {error}"
                for error in errors
            )
        )

    # -----------------------------------------------------------------------
    # Final verification.
    # -----------------------------------------------------------------------

    logging.info(
        "Final link summary:"
    )

    lab.links_summary()

    logging.info(
        "%s build is complete on %s.",
        LAB_NAME,
        server_url,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:

    try:

        server_urls = read_server_urls()

    except RuntimeError as exc:

        logging.error(
            "Startup failed: %s",
            exc,
        )

        return 1

    failed_servers: list[str] = []

    for server_url in server_urls:

        try:

            build_project_on_server(
                server_url
            )

        except Exception as exc:

            logging.error(
                "Build failed for %s:\n%s",
                server_url,
                exc,
            )

            failed_servers.append(
                server_url
            )

    if failed_servers:

        logging.error(
            "Deployment finished with errors on: %s",
            ", ".join(failed_servers),
        )

        return 1

    logging.info(
        "All manufacturing builds completed successfully."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
