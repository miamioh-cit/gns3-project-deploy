#!/usr/bin/env python3
"""
Build the CIT 480-5 electrical-grid Purdue-style VLAN segmentation project.

The topology is intentionally segmented and enforced, not merely labeled:

    VLAN 10  Enterprise
    VLAN 20  DMZ
    VLAN 30  Operations (HMI / collector / SCADA)
    VLAN 40  Control (electrical-grid PLCs)
    VLAN 50  Monitoring (Zeek and Suricata management)

The only routed Modbus/TCP paths are explicit operations-to-control flows:

    hmi-collector (10.50.30.10) -> PLCs (10.50.40.11-13), TCP/502
    scada-server  (10.50.30.200) -> PLCs (10.50.40.11-13), TCP/502

The firewall defaults to DROP for forwarded traffic and permits only those
TCP/502 flows plus established replies. Enterprise, DMZ, and monitoring
hosts therefore cannot initiate Modbus/TCP traffic to the control VLAN.

The firewall has one physical 802.1Q trunk to the core switch. Its eth0.10,
eth0.20, eth0.30, eth0.40, and eth0.50 subinterfaces provide the five zone
gateways while every endpoint remains on a separate access port.

The Lab 5 SCADA image is built and pushed by the existing Jenkins SCADA-image
stage before this deployment script runs.

Zeek and Suricata each use two interfaces:
    * eth0: monitoring VLAN 50 management attachment
    * eth1: no IP address; passive attachment to control-modbus-tap

The tap is an Ethernet hub between the firewall's control-side VLAN and the
PLC control switch. It copies the approved Modbus traffic to the sensor
interfaces, while neither sensor is inline or forwards control traffic.

The script is safe to rerun. It removes only nodes it owns, recreates them,
and re-applies the template, network, firewall, and sensor configuration.
"""

from __future__ import annotations

import logging
import shlex
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

LAB_NAME = "Module 5 - Electrical Grid - Purdue VLAN Segmentation"

BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "electrical-grid"
NETMASK = "255.255.255.0"

ENTERPRISE_VLAN = 10
DMZ_VLAN = 20
OPERATIONS_VLAN = 30
CONTROL_VLAN = 40
MONITORING_VLAN = 50

ENTERPRISE_SUBNET = "10.50.10.0/24"
DMZ_SUBNET = "10.50.20.0/24"
OPERATIONS_SUBNET = "10.50.30.0/24"
CONTROL_SUBNET = "10.50.40.0/24"
MONITORING_SUBNET = "10.50.50.0/24"

FIREWALL_ENTERPRISE_IP = "10.50.10.1"
FIREWALL_DMZ_IP = "10.50.20.1"
FIREWALL_OPERATIONS_IP = "10.50.30.1"
FIREWALL_CONTROL_IP = "10.50.40.1"
FIREWALL_MONITORING_IP = "10.50.50.1"

ENTERPRISE_HOST_IP = "10.50.10.10"
DMZ_HOST_IP = "10.50.20.10"
HMI_IP = "10.50.30.10"
SCADA_IP = "10.50.30.200"
ZEEK_MANAGEMENT_IP = "10.50.50.10"
SURICATA_MANAGEMENT_IP = "10.50.50.11"

CORE_SWITCH_TEMPLATE = "Purdue-VLAN-Core"
CONTROL_SWITCH_TEMPLATE = "Purdue-Control-VLAN40-Switch"
FIELD_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
CONTROL_TAP_TEMPLATE = "Ethernet hub"

# The core switch is the layout anchor. All Lab 5 node positions are
# expressed as offsets from this coordinate so the whole topology remains
# readable at the normal GNS3 zoom level.
CORE_SWITCH_X = 11
CORE_SWITCH_Y = -373

FIREWALL_TEMPLATE = "Purdue-OT-Firewall"
SCADA_TEMPLATE = "generic-scada-electrical-grid"
ZEEK_TEMPLATE = "Zeek"
SURICATA_TEMPLATE = "Suricata"

FIREWALL_IMAGE = "nicolaka/netshoot:latest"
SCADA_IMAGE = "evankunkel/generic-scada-electrical-grid:latest"
ZEEK_IMAGE = "zeek/zeek:latest"
SURICATA_IMAGE = "jasonish/suricata:latest"


# ---------------------------------------------------------------------------
# Electrical-grid process definition
# ---------------------------------------------------------------------------

GRID_AREAS = [
    {
        "name": "substation-a",
        "label": "Substation A",
        "plc": "plc-substation-a",
        "field_switch": "field-switch-substation-a",
        "field_subnet": "192.168.110.0/24",
        "field_ip": "192.168.110.5",
        "control_ip": "10.50.40.11",
        "x": -560,
        "sensors": [
            ("voltage-101", "192.168.110.10", "VOLT-101", "kV", "float"),
            ("frequency-101", "192.168.110.11", "FREQ-101", "Hz", "float"),
        ],
    },
    {
        "name": "feeder-b",
        "label": "Feeder B",
        "plc": "plc-feeder-b",
        "field_switch": "field-switch-feeder-b",
        "field_subnet": "192.168.120.0/24",
        "field_ip": "192.168.120.5",
        "control_ip": "10.50.40.12",
        "x": 0,
        "sensors": [
            ("current-201", "192.168.120.10", "CURR-201", "A", "float"),
            ("breaker-201", "192.168.120.11", "BRKR-201", "state", "float"),
        ],
    },
    {
        "name": "tie-line-c",
        "label": "Tie Line C",
        "plc": "plc-tie-line-c",
        "field_switch": "field-switch-tie-line-c",
        "field_subnet": "192.168.130.0/24",
        "field_ip": "192.168.130.5",
        "control_ip": "10.50.40.13",
        "x": 560,
        "sensors": [
            ("power-301", "192.168.130.10", "POWER-301", "MW", "float"),
            ("temperature-301", "192.168.130.11", "TEMP-301", "C", "float"),
        ],
    },
]

SENSOR_SIMULATION = {
    "VOLT-101": "random_walk:start=13.8,step=0.08,min=13.2,max=14.4",
    "FREQ-101": "random_walk:start=60,step=0.03,min=59.7,max=60.3",
    "CURR-201": "random_walk:start=320,step=8,min=220,max=430",
    "BRKR-201": "random_walk:start=1,step=0,min=0,max=1",
    "POWER-301": "random_walk:start=42,step=2,min=25,max=65",
    "TEMP-301": "random_walk:start=54,step=0.5,min=35,max=80",
}


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

SHARED_DOCKER_TEMPLATES = [
    {
        "name": "generic-sensor",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-sensor:latest",
        "adapters": 5,
        "console_type": "telnet",
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
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
]

FIREWALL_TEMPLATE_DEFINITION = {
    "name": FIREWALL_TEMPLATE,
    "template_type": "docker",
    "category": "guest",
    "image": FIREWALL_IMAGE,
    # One physical NIC carries the tagged 802.1Q core trunk.
    "adapters": 1,
    "console_type": "telnet",
    "start_command": "",
    "default_name_format": "{name}-{0}",
    "compute_id": "local",
    "symbol": ":/symbols/docker_guest.svg",
}

SCADA_TEMPLATE_DEFINITION = {
    "name": SCADA_TEMPLATE,
    "template_type": "docker",
    "category": "guest",
    "image": SCADA_IMAGE,
    "adapters": 11,
    "console_type": "http",
    "start_command": "",
    "default_name_format": "{name}-{0}",
    "compute_id": "local",
    "symbol": ":/symbols/docker_guest.svg",
}

ZEEK_TEMPLATE_DEFINITION = {
    "name": ZEEK_TEMPLATE,
    "template_type": "docker",
    "category": "guest",
    "image": ZEEK_IMAGE,
    "adapters": 2,
    "console_type": "telnet",
    "start_command": "",
    "extra_volumes": ["/var/log/zeek"],
    "default_name_format": "{name}-{0}",
    "compute_id": "local",
    "symbol": ":/symbols/docker_guest.svg",
}

SURICATA_TEMPLATE_DEFINITION = {
    "name": SURICATA_TEMPLATE,
    "template_type": "docker",
    "category": "guest",
    "image": SURICATA_IMAGE,
    "adapters": 2,
    "console_type": "telnet",
    "start_command": "",
    "extra_volumes": ["/var/log/suricata"],
    "default_name_format": "{name}-{0}",
    "compute_id": "local",
    "symbol": ":/symbols/docker_guest.svg",
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

    content = path.read_text(encoding="utf-8").strip()

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

        urls.append(f"{BASE_IP}{int(item)}:80")

    if not urls:
        raise RuntimeError(
            f"No valid GNS3 server last octets found in '{DATASTORE_FILE}'."
        )

    return urls


def require_http_success(
    response: requests.Response,
    action: str,
) -> None:
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"{action} failed: HTTP {response.status_code}: "
            f"{response.text}"
        )


def get_templates_by_name(server_url: str) -> dict[str, dict]:
    try:
        response = requests.get(
            f"{server_url}/v2/templates",
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not list templates on {server_url}: {exc}"
        ) from exc

    return {
        template["name"]: template
        for template in response.json()
        if template.get("name")
    }


def create_template(
    server_url: str,
    definition: dict,
) -> None:
    try:
        response = requests.post(
            f"{server_url}/v2/templates",
            json=definition,
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )
        require_http_success(
            response,
            f"Create template '{definition['name']}'",
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error creating template "
            f"'{definition['name']}' on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Created template '%s'.",
        definition["name"],
    )


def update_template_fields(
    server_url: str,
    template: dict,
    expected_definition: dict,
    fields: tuple[str, ...],
) -> None:
    template_id = template.get("template_id")

    if not template_id:
        raise RuntimeError(
            f"Template '{template.get('name')}' has no template_id."
        )

    changes = {
        field: expected_definition[field]
        for field in fields
        if field in expected_definition
        and template.get(field) != expected_definition[field]
    }

    if not changes:
        return

    updated = dict(template)
    updated.update(changes)

    try:
        response = requests.put(
            f"{server_url}/v2/templates/{template_id}",
            json=updated,
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )
        require_http_success(
            response,
            f"Update template '{template['name']}'",
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error updating template "
            f"'{template['name']}' on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Updated template '%s': %s.",
        template["name"],
        ", ".join(changes),
    )


# ---------------------------------------------------------------------------
# GNS3 template setup
# ---------------------------------------------------------------------------

def switch_template_definition(
    name: str,
    vlan_by_port: list[int],
    trunk_ports: dict[int, int] | None = None,
) -> dict:
    """Create a built-in Ethernet-switch template with access and trunk ports.

    A GNS3 dot1q port is an 802.1Q trunk. Its VLAN value is the native VLAN,
    so VLAN 1 is reserved as unused native traffic and every lab-zone VLAN is
    transmitted tagged on the firewall uplink.
    """
    trunk_ports = trunk_ports or {}

    return {
        "name": name,
        "template_type": "ethernet_switch",
        "category": "switch",
        "compute_id": "local",
        "default_name_format": "{name}-{0}",
        "symbol": ":/symbols/ethernet_switch.svg",
        "builtin": False,
        "ports_mapping": [
            {
                "name": f"Ethernet{port_number}",
                "port_number": port_number,
                "type": (
                    "dot1q"
                    if port_number in trunk_ports
                    else "access"
                ),
                "vlan": trunk_ports.get(port_number, vlan),
            }
            for port_number, vlan in enumerate(vlan_by_port)
        ],
    }


def ensure_field_switch_template(server_url: str) -> None:
    templates = get_templates_by_name(server_url)

    if FIELD_SWITCH_TEMPLATE in templates:
        return

    create_template(
        server_url,
        switch_template_definition(
            FIELD_SWITCH_TEMPLATE,
            [1] * 10,
        ),
    )


def ensure_purdue_switch_templates(server_url: str) -> None:
    definitions = [
        switch_template_definition(
            CORE_SWITCH_TEMPLATE,
            [
                1,                 # Ethernet0: firewall trunk native VLAN
                ENTERPRISE_VLAN,   # Ethernet1: enterprise workstation
                DMZ_VLAN,          # Ethernet2: DMZ jump host
                OPERATIONS_VLAN,   # Ethernet3: HMI / collector
                OPERATIONS_VLAN,   # Ethernet4: SCADA server
                CONTROL_VLAN,      # Ethernet5: passive control TAP
                MONITORING_VLAN,   # Ethernet6: Zeek management
                MONITORING_VLAN,   # Ethernet7: Suricata management
                MONITORING_VLAN,
                MONITORING_VLAN,
                MONITORING_VLAN,
                MONITORING_VLAN,
            ],
            trunk_ports={0: 1},
        ),
        switch_template_definition(
            CONTROL_SWITCH_TEMPLATE,
            [CONTROL_VLAN] * 8,
        ),
    ]

    for definition in definitions:
        templates = get_templates_by_name(server_url)
        existing = templates.get(definition["name"])

        if not existing:
            create_template(server_url, definition)
            continue

        update_template_fields(
            server_url,
            existing,
            definition,
            (
                "template_type",
                "category",
                "compute_id",
                "default_name_format",
                "symbol",
                "ports_mapping",
            ),
        )


def ensure_shared_docker_templates(server_url: str) -> None:
    templates = get_templates_by_name(server_url)

    for definition in SHARED_DOCKER_TEMPLATES:
        if definition["name"] in templates:
            logging.info(
                "Leaving shared template '%s' unchanged.",
                definition["name"],
            )
            continue

        create_template(server_url, definition)


def ensure_owned_docker_template(
    server_url: str,
    definition: dict,
) -> None:
    templates = get_templates_by_name(server_url)
    existing = templates.get(definition["name"])

    if not existing:
        create_template(server_url, definition)
        return

    update_template_fields(
        server_url,
        existing,
        definition,
        (
            "template_type",
            "category",
            "image",
            "adapters",
            "console_type",
            "start_command",
            "extra_volumes",
            "default_name_format",
            "compute_id",
            "symbol",
        ),
    )


def ensure_sensor_template(
    server_url: str,
    definition: dict,
) -> None:
    """Preserve an instructor-provided sensor image but require two NICs."""
    templates = get_templates_by_name(server_url)
    existing = templates.get(definition["name"])

    if not existing:
        create_template(server_url, definition)
        return

    expected = dict(existing)
    expected["adapters"] = max(
        int(existing.get("adapters") or 0),
        2,
    )

    update_template_fields(
        server_url,
        existing,
        expected,
        ("adapters",),
    )

    logging.info(
        "Using existing %s template.",
        definition["name"],
    )


def ensure_required_templates(server_url: str) -> None:
    ensure_field_switch_template(server_url)
    ensure_purdue_switch_templates(server_url)
    ensure_shared_docker_templates(server_url)

    ensure_owned_docker_template(
        server_url,
        FIREWALL_TEMPLATE_DEFINITION,
    )
    ensure_owned_docker_template(
        server_url,
        SCADA_TEMPLATE_DEFINITION,
    )

    # The lab calls for Zeek and Suricata Docker templates. If the
    # instructor already supplied either template, preserve its image and
    # only ensure the two interfaces required for management plus passive tap.
    ensure_sensor_template(
        server_url,
        ZEEK_TEMPLATE_DEFINITION,
    )
    ensure_sensor_template(
        server_url,
        SURICATA_TEMPLATE_DEFINITION,
    )


# ---------------------------------------------------------------------------
# Project and node helpers
# ---------------------------------------------------------------------------

def open_or_create_project(
    server: Gns3Connector,
    server_url: str,
) -> Project:
    try:
        projects = server.get_projects()
    except Exception as exc:
        raise RuntimeError(
            f"Could not list projects on {server_url}: {exc}"
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
            return lab

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
        return lab

    except Exception as exc:
        raise RuntimeError(
            f"Could not open/create '{LAB_NAME}' on "
            f"{server_url}: {exc}"
        ) from exc


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
            "Created node '%s' from template '%s'.",
            name,
            template,
        )

    except Exception as exc:
        errors.append(
            f"Create node '{name}' failed: {exc}"
        )


def managed_node_names() -> set[str]:
    names: set[str] = {
        "vlan-core-switch",
        "control-vlan40-switch",
        "control-modbus-tap",
        "ot-firewall",
        "enterprise-workstation",
        "dmz-jump-host",
        "hmi-collector",
        "scada-server",
        "zeek-sensor",
        "suricata-sensor",
    }

    for area in GRID_AREAS:
        names.add(area["plc"])
        names.add(area["field_switch"])

        for sensor_name, *_ in area["sensors"]:
            names.add(sensor_name)

    return names


def is_managed_node_name(
    node_name: str,
    base_names: set[str],
) -> bool:
    for base_name in base_names:
        if node_name == base_name:
            return True

        if not node_name.startswith(base_name):
            continue

        suffix = node_name[len(base_name):]

        if suffix.isdigit():
            return True

        if (
            suffix.startswith("-")
            and suffix[1:].isdigit()
        ):
            return True

    return False


def remove_existing_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:
    try:
        lab.get()
        base_names = managed_node_names()

        for node in list(lab.nodes):
            if not is_managed_node_name(
                node.name,
                base_names,
            ):
                continue

            try:
                node.get()

                status = getattr(
                    node.status,
                    "value",
                    str(node.status),
                ).lower()

                if status == "started":
                    node.stop()

                node.delete()

                logging.info(
                    "Deleted existing 480-5 node '%s'.",
                    node.name,
                )

            except Exception as exc:
                errors.append(
                    f"Delete existing node '{node.name}' failed: {exc}"
                )

        lab.get()

    except Exception as exc:
        errors.append(
            f"Refresh/remove existing 480-5 nodes failed: {exc}"
        )


def update_node_properties(
    server_url: str,
    lab: Project,
    node_name: str,
    updates: dict[str, object],
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

        response = requests.get(
            f"{server_url}/v2/projects/{lab.project_id}/"
            f"nodes/{node.node_id}",
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )
        response.raise_for_status()

        node_data = response.json()
        properties = dict(
            node_data.get("properties") or {}
        )

        if all(
            properties.get(key) == value
            for key, value in updates.items()
        ):
            if was_running:
                node.start()
            return

        properties.update(updates)

        response = requests.put(
            f"{server_url}/v2/projects/{lab.project_id}/"
            f"nodes/{node.node_id}",
            json={"properties": properties},
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )
        require_http_success(
            response,
            f"Update node '{node_name}' properties",
        )

        logging.info(
            "Updated node '%s' properties: %s.",
            node_name,
            ", ".join(updates),
        )

        if was_running:
            node.start()

    except Exception as exc:
        errors.append(
            f"Update properties for '{node_name}' failed: {exc}"
        )


def set_docker_node_environment(
    server_url: str,
    lab: Project,
    node_name: str,
    environment: str,
    errors: list[str],
) -> None:
    update_node_properties(
        server_url,
        lab,
        node_name,
        {"environment": environment},
        errors,
    )


def set_node_start_command(
    server_url: str,
    lab: Project,
    node_name: str,
    start_command: str,
    errors: list[str],
) -> None:
    update_node_properties(
        server_url,
        lab,
        node_name,
        {"start_command": start_command},
        errors,
    )


# ---------------------------------------------------------------------------
# Docker environments and static interface configurations
# ---------------------------------------------------------------------------

def plc_environment(area: dict) -> str:
    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="plc",
        PLC_ROLE=area["name"],
        FIELD_IP_ADDRESS=area["field_ip"],
        FIELD_SUBNET=area["field_subnet"],
        IP_ADDRESS=area["control_ip"],
        NETMASK=NETMASK,
        DEVICE_AGE_YEARS=5,
        AGE_FAILURE_THRESHOLD_YEARS=99,
        PLC_SCAN_SUBNETS=area["field_subnet"],
        PLC_FIELD_INTERFACE="eth0",
        PLC_FIELD_IP=area["field_ip"],
        PLC_FIELD_SUBNET=area["field_subnet"],
        PLC_CONTROL_INTERFACE="eth1",
        PLC_CONTROL_IP=area["control_ip"],
        PLC_CONTROL_SUBNET=CONTROL_SUBNET,
        PLC_MODBUS_PORT=502,
    )


def hmi_environment() -> str:
    plc_targets = " ".join(
        f"--plc {area['name']}={area['control_ip']}:502"
        for area in GRID_AREAS
    )

    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="hmi",
        HMI_ROLE="operations-collector",
        IP_ADDRESS=HMI_IP,
        NETMASK=NETMASK,
        PLC_TARGETS=plc_targets,
    )


def scada_environment() -> str:
    """Return the SCADA server's operations-side configuration.

    The application discovers the PLC service addresses in the control VLAN;
    the firewall permits this one dashboard source over TCP/502 only.
    """
    return build_environment(
        SCENARIO=SCENARIO,
        SCADA_SUBNETS=CONTROL_SUBNET,
        SCADA_DIAGRAM_CONFIG="electrical_grid/diagrams.yaml",
        IP_ADDRESS=SCADA_IP,
        NETMASK=NETMASK,
    )


def passive_endpoint_environment(
    role: str,
    ip_address: str,
) -> str:
    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="hmi",
        HMI_ROLE=role,
        IP_ADDRESS=ip_address,
        NETMASK=NETMASK,
        PLC_TARGETS="",
    )


def field_sensor_environment(
    area: dict,
    sensor_ip: str,
    tag: str,
    units: str,
    data_type: str,
) -> str:
    return build_environment(
        SCENARIO=SCENARIO,
        TAG=tag,
        SIMULATION=SENSOR_SIMULATION.get(
            tag,
            "random_walk:start=50,step=1,min=0,max=100",
        ),
        UNITS=units,
        DATA_TYPE=data_type,
        IP_ADDRESS=sensor_ip,
        NETMASK=NETMASK,
        FIELD_SUBNET=area["field_subnet"],
    )


def interface_block(
    interface: str,
    ip_address: str,
    gateway: str | None = None,
) -> str:
    lines = [
        f"auto {interface}",
        f"iface {interface} inet static",
        f"    address {ip_address}",
        f"    netmask {NETMASK}",
    ]

    if gateway:
        lines.append(f"    gateway {gateway}")

    return "\n".join(lines)


def single_interface_config(
    ip_address: str,
    gateway: str | None = None,
) -> str:
    return interface_block(
        "eth0",
        ip_address,
        gateway,
    )


def plc_interface_config(area: dict) -> str:
    return "\n\n".join(
        [
            interface_block(
                "eth0",
                area["field_ip"],
            ),
            interface_block(
                "eth1",
                area["control_ip"],
                FIREWALL_CONTROL_IP,
            ),
        ]
    )


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

        logging.info(
            "Applied network configuration to '%s'.",
            node_name,
        )

        if was_running:
            node.start()

    except Exception as exc:
        errors.append(
            f"Configure interfaces for '{node_name}' failed: {exc}"
        )


def firewall_start_command() -> str:
    """Configure the single physical 802.1Q firewall trunk and policy."""
    interface_ips = [
        (ENTERPRISE_VLAN, FIREWALL_ENTERPRISE_IP),
        (DMZ_VLAN, FIREWALL_DMZ_IP),
        (OPERATIONS_VLAN, FIREWALL_OPERATIONS_IP),
        (CONTROL_VLAN, FIREWALL_CONTROL_IP),
        (MONITORING_VLAN, FIREWALL_MONITORING_IP),
    ]

    commands = [
        "ip link set eth0 up",
        "ip addr flush dev eth0",
    ]

    for vlan, ip_address in interface_ips:
        subinterface = f"eth0.{vlan}"
        commands.extend(
            [
                f"ip link delete {subinterface} 2>/dev/null || true",
                (
                    f"ip link add link eth0 name {subinterface} "
                    f"type vlan id {vlan}"
                ),
                f"ip link set {subinterface} up",
                f"ip addr add {ip_address}/24 dev {subinterface}",
            ]
        )

    commands.extend(
        [
            "sysctl -w net.ipv4.ip_forward=1",
            "iptables -F",
            "iptables -P FORWARD DROP",
            (
                "iptables -A FORWARD "
                "-m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
            ),
            (
                "iptables -A FORWARD -i eth0.30 -o eth0.40 "
                f"-p tcp -s {HMI_IP} -d {CONTROL_SUBNET} "
                "--dport 502 -m conntrack --ctstate NEW -j ACCEPT"
            ),
            (
                "iptables -A FORWARD -i eth0.30 -o eth0.40 "
                f"-p tcp -s {SCADA_IP} -d {CONTROL_SUBNET} "
                "--dport 502 -m conntrack --ctstate NEW -j ACCEPT"
            ),
            "exec tail -f /dev/null",
        ]
    )

    return "sh -c " + shlex.quote(
        "; ".join(commands)
    )


def sensor_start_command(
    sensor: str,
    management_ip: str,
) -> str:
    commands = [
        "ip link set eth0 up || true",
        (
            f"ip addr replace {management_ip}/24 "
            "dev eth0 || true"
        ),
        "ip link set eth1 up || true",
        "ip link set eth1 promisc on || true",
    ]

    if sensor == "zeek":
        commands.extend(
            [
                "mkdir -p /var/log/zeek",
                "cd /var/log/zeek",
                "exec zeek -C -i eth1",
            ]
        )
    else:
        commands.extend(
            [
                "mkdir -p /var/log/suricata",
                "exec suricata -i eth1 "
                "-l /var/log/suricata",
            ]
        )

    return "sh -c " + shlex.quote(
        "; ".join(commands)
    )


# ---------------------------------------------------------------------------
# Node creation, configuration, and links
# ---------------------------------------------------------------------------

def core_relative_position(
    x_offset: int,
    y_offset: int,
) -> tuple[int, int]:
    """Return a node position relative to the fixed core-switch anchor."""
    return (
        CORE_SWITCH_X + x_offset,
        CORE_SWITCH_Y + y_offset,
    )


def create_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:
    for area in GRID_AREAS:
        area_x = area["x"]

        for index, (
            sensor_name,
            _sensor_ip,
            _tag,
            _units,
            _data_type,
        ) in enumerate(area["sensors"]):
            x, y = core_relative_position(
                area_x - 90 + index * 120,
                375,
            )
            create_node(
                lab,
                sensor_name,
                "generic-sensor",
                x,
                y,
                errors,
            )

        x, y = core_relative_position(area_x + 45, 500)
        create_node(
            lab,
            area["field_switch"],
            FIELD_SWITCH_TEMPLATE,
            x,
            y,
            errors,
        )

        x, y = core_relative_position(area_x + 45, 630)
        create_node(
            lab,
            area["plc"],
            "generic-plc",
            x,
            y,
            errors,
        )

    create_node(
        lab,
        "vlan-core-switch",
        CORE_SWITCH_TEMPLATE,
        CORE_SWITCH_X,
        CORE_SWITCH_Y,
        errors,
    )

    x, y = core_relative_position(-700, 200)
    create_node(
        lab,
        "enterprise-workstation",
        "generic-hmi",
        x,
        y,
        errors,
    )

    x, y = core_relative_position(-700, 360)
    create_node(
        lab,
        "dmz-jump-host",
        "generic-hmi",
        x,
        y,
        errors,
    )

    x, y = core_relative_position(-300, 345)
    create_node(
        lab,
        "hmi-collector",
        "generic-hmi",
        x,
        y,
        errors,
    )

    x, y = core_relative_position(-300, 485)
    create_node(
        lab,
        "scada-server",
        SCADA_TEMPLATE,
        x,
        y,
        errors,
    )

    x, y = core_relative_position(300, 205)
    create_node(
        lab,
        "ot-firewall",
        FIREWALL_TEMPLATE,
        x,
        y,
        errors,
    )

    x, y = core_relative_position(265, 420)
    create_node(
        lab,
        "control-modbus-tap",
        CONTROL_TAP_TEMPLATE,
        x,
        y,
        errors,
    )

    x, y = core_relative_position(265, 535)
    create_node(
        lab,
        "control-vlan40-switch",
        CONTROL_SWITCH_TEMPLATE,
        x,
        y,
        errors,
    )

    x, y = core_relative_position(650, 345)
    create_node(
        lab,
        "zeek-sensor",
        ZEEK_TEMPLATE,
        x,
        y,
        errors,
    )

    x, y = core_relative_position(650, 490)
    create_node(
        lab,
        "suricata-sensor",
        SURICATA_TEMPLATE,
        x,
        y,
        errors,
    )


def set_scenario_environments(
    server_url: str,
    lab: Project,
    errors: list[str],
) -> None:
    for area in GRID_AREAS:
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
                field_sensor_environment(
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
        "hmi-collector",
        hmi_environment(),
        errors,
    )

    set_docker_node_environment(
        server_url,
        lab,
        "scada-server",
        scada_environment(),
        errors,
    )
    set_docker_node_environment(
        server_url,
        lab,
        "enterprise-workstation",
        passive_endpoint_environment(
            "enterprise-workstation",
            ENTERPRISE_HOST_IP,
        ),
        errors,
    )

    set_docker_node_environment(
        server_url,
        lab,
        "dmz-jump-host",
        passive_endpoint_environment(
            "dmz-jump-host",
            DMZ_HOST_IP,
        ),
        errors,
    )

    set_node_start_command(
        server_url,
        lab,
        "ot-firewall",
        firewall_start_command(),
        errors,
    )

    set_node_start_command(
        server_url,
        lab,
        "zeek-sensor",
        sensor_start_command(
            "zeek",
            ZEEK_MANAGEMENT_IP,
        ),
        errors,
    )

    set_node_start_command(
        server_url,
        lab,
        "suricata-sensor",
        sensor_start_command(
            "suricata",
            SURICATA_MANAGEMENT_IP,
        ),
        errors,
    )


def configure_scenario_nodes(
    lab: Project,
    errors: list[str],
) -> None:
    for area in GRID_AREAS:
        configure_interfaces(
            lab,
            area["plc"],
            plc_interface_config(area),
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
                single_interface_config(sensor_ip),
                errors,
            )

    configure_interfaces(
        lab,
        "hmi-collector",
        single_interface_config(
            HMI_IP,
            FIREWALL_OPERATIONS_IP,
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "scada-server",
        single_interface_config(
            SCADA_IP,
            FIREWALL_OPERATIONS_IP,
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "enterprise-workstation",
        single_interface_config(
            ENTERPRISE_HOST_IP,
            FIREWALL_ENTERPRISE_IP,
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "dmz-jump-host",
        single_interface_config(
            DMZ_HOST_IP,
            FIREWALL_DMZ_IP,
        ),
        errors,
    )


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
    for area in GRID_AREAS:
        create_link(
            lab,
            area["plc"],
            "eth0",
            area["field_switch"],
            "Ethernet0",
            errors,
        )

        for index, (
            sensor_name,
            _sensor_ip,
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

    # One real 802.1Q trunk carries all Purdue VLANs to the firewall. The
    # core's Ethernet0 port is dot1q/native VLAN 1; lab traffic is tagged.
    create_link(
        lab,
        "ot-firewall",
        "eth0",
        "vlan-core-switch",
        "Ethernet0",
        errors,
    )

    # Access ports remain untagged at the endpoints.
    create_link(
        lab,
        "enterprise-workstation",
        "eth0",
        "vlan-core-switch",
        "Ethernet1",
        errors,
    )
    create_link(
        lab,
        "dmz-jump-host",
        "eth0",
        "vlan-core-switch",
        "Ethernet2",
        errors,
    )
    create_link(
        lab,
        "hmi-collector",
        "eth0",
        "vlan-core-switch",
        "Ethernet3",
        errors,
    )
    create_link(
        lab,
        "scada-server",
        "eth0",
        "vlan-core-switch",
        "Ethernet4",
        errors,
    )

    # VLAN 40 is an access port between the core and passive TAP. The TAP
    # copies approved Modbus traffic but is not an inline control device.
    create_link(
        lab,
        "control-modbus-tap",
        "Ethernet0",
        "vlan-core-switch",
        "Ethernet5",
        errors,
    )
    create_link(
        lab,
        "control-modbus-tap",
        "Ethernet1",
        "control-vlan40-switch",
        "Ethernet0",
        errors,
    )

    for index, area in enumerate(
        GRID_AREAS,
        start=1,
    ):
        create_link(
            lab,
            area["plc"],
            "eth1",
            "control-vlan40-switch",
            f"Ethernet{index}",
            errors,
        )

    # Monitoring-management access ports. Their routing to Control is denied.
    create_link(
        lab,
        "zeek-sensor",
        "eth0",
        "vlan-core-switch",
        "Ethernet6",
        errors,
    )
    create_link(
        lab,
        "suricata-sensor",
        "eth0",
        "vlan-core-switch",
        "Ethernet7",
        errors,
    )

    # Passive-only NICs receive copied VLAN-40 traffic at the hub.
    create_link(
        lab,
        "zeek-sensor",
        "eth1",
        "control-modbus-tap",
        "Ethernet2",
        errors,
    )
    create_link(
        lab,
        "suricata-sensor",
        "eth1",
        "control-modbus-tap",
        "Ethernet3",
        errors,
    )


# ---------------------------------------------------------------------------
# Start and verification helpers
# ---------------------------------------------------------------------------

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
    # The hub is a passive TAP, not a control endpoint.
    start_node(
        lab,
        "control-modbus-tap",
        errors,
    )

    start_node(
        lab,
        "ot-firewall",
        errors,
    )

    # Field devices must be ready before PLC discovery begins.
    for area in GRID_AREAS:
        for (
            sensor_name,
            _sensor_ip,
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

    # Start passive visibility before the HMI begins Modbus polling.
    start_node(
        lab,
        "zeek-sensor",
        errors,
    )
    start_node(
        lab,
        "suricata-sensor",
        errors,
    )

    start_node(
        lab,
        "enterprise-workstation",
        errors,
    )
    start_node(
        lab,
        "dmz-jump-host",
        errors,
    )
    start_node(
        lab,
        "hmi-collector",
        errors,
    )
    start_node(
        lab,
        "scada-server",
        errors,
    )


def verify_topology(
    server_url: str,
    lab: Project,
    errors: list[str],
) -> None:
    try:
        lab.get()

        actual_names = {
            node.name
            for node in lab.nodes
        }
        missing = managed_node_names() - actual_names

        if missing:
            errors.append(
                "Topology is missing required node(s): "
                + ", ".join(sorted(missing))
            )

        response = requests.get(
            f"{server_url}/v2/projects/{lab.project_id}/links",
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )
        response.raise_for_status()

        # This project creates 23 links: 9 field links plus 14 Purdue,
        # SCADA, and passive-monitoring links. Check for at least that many
        # without deleting user-added links.
        if len(response.json()) < 23:
            errors.append(
                "Topology link verification failed: expected at least "
                f"23 links, found {len(response.json())}."
            )

    except Exception as exc:
        errors.append(
            f"Final topology verification failed: {exc}"
        )


def raise_if_errors(
    server_url: str,
    errors: list[str],
) -> None:
    if errors:
        raise RuntimeError(
            "\n".join(
                f"{server_url}: {error}"
                for error in errors
            )
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

        ensure_required_templates(server_url)

        lab = open_or_create_project(
            server,
            server_url,
        )

    except Exception as exc:
        raise RuntimeError(
            f"Project setup failed on {server_url}: {exc}"
        ) from exc

    logging.info(
        "Removing existing 480-5-managed nodes."
    )
    remove_existing_scenario_nodes(
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    logging.info(
        "Creating the segmented Purdue topology."
    )
    create_scenario_nodes(
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    try:
        lab.get()
    except Exception as exc:
        errors.append(
            f"Refresh after node creation failed: {exc}"
        )
    raise_if_errors(server_url, errors)

    logging.info(
        "Applying Docker environments and sensor/firewall commands."
    )
    set_scenario_environments(
        server_url,
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    logging.info(
        "Applying static host and PLC interface configuration."
    )
    configure_scenario_nodes(
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    logging.info(
        "Creating VLAN, control, and passive monitoring links."
    )
    create_scenario_links(
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    logging.info(
        "Starting firewall, field devices, passive sensors, and HMI."
    )
    start_scenario_nodes(
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    verify_topology(
        server_url,
        lab,
        errors,
    )
    raise_if_errors(server_url, errors)

    logging.info(
        "Allowed Modbus paths: hmi-collector (%s) and scada-server (%s) "
        "-> %s over TCP/502 only.",
        HMI_IP,
        SCADA_IP,
        ", ".join(
            area["control_ip"]
            for area in GRID_AREAS
        ),
    )
    logging.info(
        "Enterprise, DMZ, and monitoring VLANs have no permitted "
        "forwarded Modbus/TCP path to the control VLAN."
    )

    lab.links_summary()

    logging.info(
        "%s build completed successfully on %s.",
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
            build_project_on_server(server_url)
        except Exception as exc:
            logging.error(
                "Build failed for %s:\n%s",
                server_url,
                exc,
            )
            failed_servers.append(server_url)

    if failed_servers:
        logging.error(
            "Deployment finished with errors on: %s",
            ", ".join(failed_servers),
        )
        return 1

    logging.info(
        "All electrical-grid Purdue segmentation builds completed "
        "successfully."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
