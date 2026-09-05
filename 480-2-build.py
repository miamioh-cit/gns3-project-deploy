#!/usr/bin/env python3
"""
Build the CIT 480-2 freshwater treatment GNS3 project.

Freshwater stages:
    intake -> filtration -> dosing -> storage

Each stage has:
    - 4 field sensors
    - 1 field switch
    - 1 dual-homed PLC

Central operations network:
    - Core-Switch
    - HMI polling node
    - Historian
    - SCADA
    - Kali Linux

PLC nodes use:
    wtaylor8/generic-plc:latest

The shared generic-scada image is not modified. The 480-2-specific
freshwater SCADA diagram files are created inside the SCADA container
at container startup.

Important PLC discovery behavior:
    Sensors are started before their PLC so the PLC's initial field scan
    can discover the sensors immediately. PLC_SCAN_SUBNETS is restricted
    to each PLC's own field LAN so PLCs do not import other PLCs from the
    operations LAN into their aggregate child tables.
"""

from __future__ import annotations

import base64
import logging
import sys
from pathlib import Path

import requests
from gns3fy import Gns3Connector, Project


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


LAB_NAME = "Module 2 - Freshwater Treatment - Baseline"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "freshwater_treatment"

OPERATIONS_SUBNET = "10.10.20.0/24"
OPERATIONS_NETMASK = "255.255.255.0"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
FIELD_SWITCH_TEMPLATE = "GNS3 Ethernet switch"

SCADA_IP = "10.10.20.200"
HMI_IP = "10.10.20.20"
HISTORIAN_IP = "10.10.20.30"
KALI_IP = "10.10.20.250"


# ---------------------------------------------------------------------------
# Repository files used by the 480-2 deployment
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent

FRESHWATER_DIAGRAM_CONFIG = (
    REPO_ROOT
    / "scada"
    / "freshwater_treatment"
    / "diagrams.yaml"
)

FRESHWATER_DIAGRAM_TEMPLATE = (
    REPO_ROOT
    / "scada"
    / "templates"
    / "diagrams"
    / "freshwater_overview.html"
)


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


# ---------------------------------------------------------------------------
# Freshwater treatment stages
# ---------------------------------------------------------------------------

STAGES = [
    {
        "name": "intake",
        "label": "Raw Water Intake",
        "field_switch": "field-switch-intake",
        "field_subnet": "192.168.10.0/24",
        "field_ip": "192.168.10.5",
        "plc": "plc-intake",
        "plc_ops_ip": "10.10.20.11",
        "core_port": "Ethernet0",
        "x": -600,
        "sensors": [
            (
                "sensor-intake-flow",
                "192.168.10.1",
                "FT-INTAKE",
                "gpm",
                "float",
            ),
            (
                "sensor-intake-level",
                "192.168.10.2",
                "LT-INTAKE",
                "%",
                "float",
            ),
            (
                "sensor-intake-pressure",
                "192.168.10.3",
                "DP-INTAKE",
                "psi",
                "float",
            ),
            (
                "sensor-intake-turbidity",
                "192.168.10.4",
                "TU-INTAKE",
                "NTU",
                "float",
            ),
        ],
    },
    {
        "name": "filtration",
        "label": "Filtration",
        "field_switch": "field-switch-filtration",
        "field_subnet": "192.168.20.0/24",
        "field_ip": "192.168.20.5",
        "plc": "plc-filtration",
        "plc_ops_ip": "10.10.20.12",
        "core_port": "Ethernet1",
        "x": -200,
        "sensors": [
            (
                "sensor-filtration-turbidity",
                "192.168.20.1",
                "TU-FILTRATION",
                "NTU",
                "float",
            ),
            (
                "sensor-filtration-pressure",
                "192.168.20.2",
                "DP-FILTRATION",
                "psi",
                "float",
            ),
            (
                "sensor-filtration-flow",
                "192.168.20.3",
                "FT-FILTRATION",
                "gpm",
                "float",
            ),
            (
                "sensor-filtration-level",
                "192.168.20.4",
                "LT-FILTRATION",
                "%",
                "float",
            ),
        ],
    },
    {
        "name": "dosing",
        "label": "Chemical Dosing",
        "field_switch": "field-switch-dosing",
        "field_subnet": "192.168.30.0/24",
        "field_ip": "192.168.30.5",
        "plc": "plc-dosing",
        "plc_ops_ip": "10.10.20.13",
        "core_port": "Ethernet2",
        "x": 200,
        "sensors": [
            (
                "sensor-dosing-chlorine",
                "192.168.30.1",
                "CL-DOSING",
                "mg/L",
                "float",
            ),
            (
                "sensor-dosing-ph",
                "192.168.30.2",
                "PH-DOSING",
                "pH",
                "float",
            ),
            (
                "sensor-dosing-flow",
                "192.168.30.3",
                "FT-DOSING",
                "gpm",
                "float",
            ),
            (
                "sensor-dosing-rate",
                "192.168.30.4",
                "FT-DOSE",
                "L/h",
                "float",
            ),
        ],
    },
    {
        "name": "storage",
        "label": "Finished Water Storage",
        "field_switch": "field-switch-storage",
        "field_subnet": "192.168.40.0/24",
        "field_ip": "192.168.40.5",
        "plc": "plc-storage",
        "plc_ops_ip": "10.10.20.14",
        "core_port": "Ethernet3",
        "x": 600,
        "sensors": [
            (
                "sensor-storage-level",
                "192.168.40.1",
                "LT-STORAGE",
                "%",
                "float",
            ),
            (
                "sensor-storage-turbidity",
                "192.168.40.2",
                "TU-STORAGE",
                "NTU",
                "float",
            ),
            (
                "sensor-storage-chlorine",
                "192.168.40.3",
                "CL-STORAGE",
                "mg/L",
                "float",
            ),
            (
                "sensor-storage-temperature",
                "192.168.40.4",
                "TT-STORAGE",
                "C",
                "float",
            ),
        ],
    },
]


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
            f"HTTP {response.status_code}: {response.text}"
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
            f"Create template '{CORE_SWITCH_TEMPLATE}' "
            f"on {server_url}",
        )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error creating "
            f"'{CORE_SWITCH_TEMPLATE}' on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Created template '%s' with %d ports on %s.",
        CORE_SWITCH_TEMPLATE,
        len(ports),
        server_url,
    )


def update_template_environment(
    server_url: str,
    template: dict,
    expected_environment: str,
) -> None:

    template_name = template["name"]
    template_id = template.get("template_id")
    actual_environment = template.get("environment")

    if actual_environment == expected_environment:
        return

    if not template_id:
        raise RuntimeError(
            f"Template '{template_name}' on {server_url} "
            "has no template_id."
        )

    updated = dict(template)
    updated["environment"] = expected_environment

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
            f"environment on {server_url}",
        )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error updating template "
            f"'{template_name}' on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Updated template '%s' environment "
        "from %r to %r.",
        template_name,
        actual_environment,
        expected_environment,
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
            update_template_environment(
                server_url,
                existing,
                template["environment"],
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
                f"'{template['name']}' on {server_url}",
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
        node = lab.get_node(node_name)
        node.get()

        response = requests.get(
            f"{server_url}/v2/projects/"
            f"{lab.project_id}/nodes/{node.node_id}",
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

        actual_environment = properties.get(
            "environment"
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
            f"{lab.project_id}/nodes/{node.node_id}",
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
            f"Update node '{node_name}' environment",
        )

        logging.info(
            "Updated node '%s' environment to:\n%s",
            node_name,
            environment,
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
        node = lab.get_node(node_name)
        node.get()

        status = getattr(
            node.status,
            "value",
            str(node.status),
        ).lower()

        was_running = status == "started"

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
    stage: dict,
) -> str:

    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="plc",
        PLC_ROLE=stage["name"],
        FIELD_IP_ADDRESS=stage["field_ip"],
        FIELD_SUBNET=stage["field_subnet"],
        IP_ADDRESS=stage["plc_ops_ip"],
        NETMASK=OPERATIONS_NETMASK,
        DEVICE_AGE_YEARS={
            "intake": 7,
            "filtration": 16,
            "dosing": 13,
            "storage": 5,
        }[stage["name"]],
        AGE_FAILURE_THRESHOLD_YEARS=12,
        AGE_FAILURE_WINDOW_SECONDS=10,
        AGE_FAILURE_MAX_REQUESTS=30,
        AGE_FAILURE_DURATION_SECONDS=20,
        AGE_FAILURE_MODE="zero",
        PLC_SCAN_SUBNETS=stage["field_subnet"],
        PLC_FIELD_INTERFACE="eth0",
        PLC_FIELD_IP=stage["field_ip"],
        PLC_FIELD_SUBNET=stage["field_subnet"],
        PLC_CONTROL_INTERFACE="eth1",
        PLC_CONTROL_IP=stage["plc_ops_ip"],
        PLC_CONTROL_SUBNET=OPERATIONS_SUBNET,
        PLC_MODBUS_PORT=502,
    )


def hmi_environment() -> str:

    plc_targets = " ".join(
        f"--plc {stage['name']}="
        f"{stage['plc_ops_ip']}:502"
        for stage in STAGES
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
        f"--plc {stage['name']}="
        f"{stage['plc_ops_ip']}:502"
        for stage in STAGES
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
        SCADA_DIAGRAM_CONFIG=(
            "freshwater_treatment/diagrams.yaml"
        ),
        IP_ADDRESS=SCADA_IP,
        NETMASK=OPERATIONS_NETMASK,
    )


def sensor_environment(
    stage: dict,
    sensor_ip: str,
    tag: str,
    units: str,
    data_type: str,
) -> str:

    return build_environment(
        SCENARIO=SCENARIO,
        TAG=tag,
        SIMULATION="true",
        UNITS=units,
        DATA_TYPE=data_type,
        IP_ADDRESS=sensor_ip,
        NETMASK=OPERATIONS_NETMASK,
        FIELD_SUBNET=stage["field_subnet"],
    )


# ---------------------------------------------------------------------------
# Node creation
# ---------------------------------------------------------------------------

def create_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:

    for stage in STAGES:
        x = stage["x"]

        for index, (
            sensor_name,
            _ip,
            _tag,
            _units,
            _type,
        ) in enumerate(
            stage["sensors"]
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
            stage["field_switch"],
            FIELD_SWITCH_TEMPLATE,
            x + 120,
            -360,
            errors,
        )

        create_node(
            lab,
            stage["plc"],
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
        "hmi-poller",
        "generic-hmi",
        -260,
        40,
        errors,
    )

    create_node(
        lab,
        "historian",
        "generic-hmi",
        0,
        220,
        errors,
    )

    create_node(
        lab,
        "scada-server",
        "generic-scada",
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

    expected_nodes = []

    for stage in STAGES:

        expected_nodes.append(
            (
                stage["plc"],
                plc_environment(stage),
            )
        )

        for (
            sensor_name,
            sensor_ip,
            tag,
            units,
            data_type,
        ) in stage["sensors"]:

            expected_nodes.append(
                (
                    sensor_name,
                    sensor_environment(
                        stage,
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
                "hmi-poller",
                hmi_environment(),
            ),
            (
                "historian",
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
            node = lab.get_node(node_name)
            node.get()

            response = requests.get(
                f"{server_url}/v2/projects/"
                f"{lab.project_id}/nodes/{node.node_id}",
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

    for stage in STAGES:

        configure_interfaces(
            lab,
            stage["plc"],
            build_plc_interface_config(
                stage["field_ip"],
                stage["plc_ops_ip"],
            ),
            errors,
        )

        for (
            sensor_name,
            sensor_ip,
            _tag,
            _units,
            _data_type,
        ) in stage["sensors"]:

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
        "hmi-poller",
        build_single_interface_config(
            HMI_IP
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "historian",
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

    for stage in STAGES:

        set_docker_node_environment(
            server_url,
            lab,
            stage["plc"],
            plc_environment(stage),
            errors,
        )

        for (
            sensor_name,
            sensor_ip,
            tag,
            units,
            data_type,
        ) in stage["sensors"]:

            set_docker_node_environment(
                server_url,
                lab,
                sensor_name,
                sensor_environment(
                    stage,
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
        "hmi-poller",
        hmi_environment(),
        errors,
    )

    set_docker_node_environment(
        server_url,
        lab,
        "historian",
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
        node = lab.get_node(node_name)
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

    for stage in STAGES:

        stop_node(
            lab,
            stage["plc"],
            errors,
        )

        for (
            sensor_name,
            _ip,
            _tag,
            _units,
            _data_type,
        ) in stage["sensors"]:

            stop_node(
                lab,
                sensor_name,
                errors,
            )

    for node_name in (
        "hmi-poller",
        "historian",
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
        node = lab.get_node(node_name)
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

    # Start sensors before their PLCs so the PLC initial discovery
    # scan can see all field devices.
    for stage in STAGES:

        for (
            sensor_name,
            _ip,
            _tag,
            _units,
            _data_type,
        ) in stage["sensors"]:

            start_node(
                lab,
                sensor_name,
                errors,
            )

        start_node(
            lab,
            stage["plc"],
            errors,
        )

    start_node(
        lab,
        "hmi-poller",
        errors,
    )

    start_node(
        lab,
        "historian",
        errors,
    )

    start_node(
        lab,
        "scada-server",
        errors,
    )

    start_node(
        lab,
        "KaliLinux-1",
        errors,
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

    for stage in STAGES:

        create_link(
            lab,
            stage["plc"],
            "eth0",
            stage["field_switch"],
            "Ethernet0",
            errors,
        )

        for index, (
            sensor_name,
            _ip,
            _tag,
            _units,
            _data_type,
        ) in enumerate(
            stage["sensors"],
            start=1,
        ):

            create_link(
                lab,
                sensor_name,
                "eth0",
                stage["field_switch"],
                f"Ethernet{index}",
                errors,
            )

        create_link(
            lab,
            stage["plc"],
            "eth1",
            "ops-switch",
            stage["core_port"],
            errors,
        )

    create_link(
        lab,
        "hmi-poller",
        "eth0",
        "ops-switch",
        "Ethernet5",
        errors,
    )

    create_link(
        lab,
        "historian",
        "eth0",
        "ops-switch",
        "Ethernet6",
        errors,
    )

    create_link(
        lab,
        "scada-server",
        "eth0",
        "ops-switch",
        "Ethernet7",
        errors,
    )

    create_link(
        lab,
        "KaliLinux-1",
        "Ethernet0",
        "ops-switch",
        "Ethernet8",
        errors,
    )


# ---------------------------------------------------------------------------
# Freshwater SCADA configuration
# ---------------------------------------------------------------------------

def install_freshwater_scada_files(
    server_url: str,
    lab: Project,
    errors: list[str],
) -> None:
    """
    Configure the Docker SCADA node's startup command so the two
    480-2-specific diagram files are created inside the running
    SCADA container before python3 -m scada starts.

    The files are base64 encoded to safely pass HTML/YAML through
    Docker environment variables.
    """

    try:
        if not FRESHWATER_DIAGRAM_CONFIG.is_file():
            raise RuntimeError(
                "Freshwater diagram config not found: "
                f"{FRESHWATER_DIAGRAM_CONFIG}"
            )

        if not FRESHWATER_DIAGRAM_TEMPLATE.is_file():
            raise RuntimeError(
                "Freshwater diagram template not found: "
                f"{FRESHWATER_DIAGRAM_TEMPLATE}"
            )

        diagram_config = (
            FRESHWATER_DIAGRAM_CONFIG.read_text(
                encoding="utf-8"
            )
        )

        diagram_template = (
            FRESHWATER_DIAGRAM_TEMPLATE.read_text(
                encoding="utf-8"
            )
        )

        config_b64 = base64.b64encode(
            diagram_config.encode("utf-8")
        ).decode("ascii")

        template_b64 = base64.b64encode(
            diagram_template.encode("utf-8")
        ).decode("ascii")

        node = lab.get_node(
            "scada-server"
        )
        node.get()

        # GNS3 Docker-specific node endpoint.
        docker_node_url = (
            f"{server_url}/v2/compute/projects/"
            f"{lab.project_id}/docker/nodes/"
            f"{node.node_id}"
        )

        response = requests.get(
            docker_node_url,
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        response.raise_for_status()

        docker_node = response.json()

        existing_environment = (
            docker_node.get("environment") or ""
        )

        environment_lines = [
            line
            for line in existing_environment.splitlines()
            if line.strip()
        ]

        # Remove previous copies if Jenkins is rerun.
        filtered_environment = []

        for line in environment_lines:

            if line.startswith(
                "FRESHWATER_DIAGRAM_CONFIG_B64="
            ):
                continue

            if line.startswith(
                "FRESHWATER_DIAGRAM_TEMPLATE_B64="
            ):
                continue

            filtered_environment.append(
                line
            )

        filtered_environment.extend(
            [
                (
                    "FRESHWATER_DIAGRAM_CONFIG_B64="
                    f"{config_b64}"
                ),
                (
                    "FRESHWATER_DIAGRAM_TEMPLATE_B64="
                    f"{template_b64}"
                ),
            ]
        )

        # This runs inside the SCADA Docker container.
        start_command = (
            "mkdir -p "
            "/app/scenarios/freshwater_treatment "
            "&& printf '%s' "
            "\"$FRESHWATER_DIAGRAM_CONFIG_B64\" "
            "| base64 -d > "
            "/app/scenarios/freshwater_treatment/"
            "diagrams.yaml "
            "&& printf '%s' "
            "\"$FRESHWATER_DIAGRAM_TEMPLATE_B64\" "
            "| base64 -d > "
            "/app/scada/templates/diagrams/"
            "freshwater_overview.html "
            "&& exec python3 -m scada"
        )

        update_payload = {
            "environment": (
                "\n".join(
                    filtered_environment
                )
            ),
            "start_command": start_command,
        }

        response = requests.put(
            docker_node_url,
            json=update_payload,
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        require_http_success(
            response,
            "Configure freshwater SCADA Docker node",
        )

        # Verify GNS3 retained the Docker properties.
        response = requests.get(
            docker_node_url,
            auth=(
                GNS3_USER,
                GNS3_PW,
            ),
            timeout=30,
        )

        response.raise_for_status()

        verified_node = response.json()

        verified_environment = (
            verified_node.get("environment") or ""
        )

        verified_start_command = (
            verified_node.get("start_command")
        )

        if (
            "FRESHWATER_DIAGRAM_CONFIG_B64="
            not in verified_environment
        ):
            raise RuntimeError(
                "GNS3 did not retain "
                "FRESHWATER_DIAGRAM_CONFIG_B64."
            )

        if (
            "FRESHWATER_DIAGRAM_TEMPLATE_B64="
            not in verified_environment
        ):
            raise RuntimeError(
                "GNS3 did not retain "
                "FRESHWATER_DIAGRAM_TEMPLATE_B64."
            )

        if verified_start_command != start_command:
            raise RuntimeError(
                "GNS3 did not retain the "
                "freshwater SCADA start_command."
            )

        logging.info(
            "Configured and verified freshwater "
            "SCADA Docker startup."
        )

    except Exception as exc:
        errors.append(
            "Configure freshwater SCADA startup failed: "
            f"{exc}"
        )


# ---------------------------------------------------------------------------
# Build project on one GNS3 server
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

    logging.info(
        "Creating freshwater nodes for '%s' on %s.",
        LAB_NAME,
        server_url,
    )

    create_scenario_nodes(
        lab,
        errors,
    )

    try:
        lab.get()

    except Exception as exc:
        errors.append(
            "Refresh project inventory after "
            f"node creation failed: {exc}"
        )

    logging.info(
        "Stopping Docker nodes before applying "
        "environment changes."
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

    logging.info(
        "Creating freshwater links."
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

    logging.info(
        "Configuring freshwater SCADA startup."
    )

    install_freshwater_scada_files(
        server_url,
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
        "Starting freshwater nodes."
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
        "All freshwater treatment builds "
        "completed successfully."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
