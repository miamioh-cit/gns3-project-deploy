#!/usr/bin/env python3

from __future__ import annotations

import logging
import sys

import requests
from gns3fy import Gns3Connector, Project


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


LAB_NAME = "Module 4 - Manufacturing - Risk"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "manufacturing"
OPERATIONS_SUBNET = "10.10.40.0/24"
OPERATIONS_NETMASK = "255.255.255.0"

OPS_SWITCH_TEMPLATE = "GNS3 Ethernet switch"
ICS_TEMPLATE = "ics-node"
KALI_TEMPLATE = "Kali Linux"
MANUFACTURING_SCADA_TEMPLATE = "generic-scada-manufacturing"
MANUFACTURING_SCADA_IMAGE = "evankunkel/generic-scada-manafacturing:latest"

SCADA_IP = "10.10.40.200"
KALI_IP = "10.10.40.250"
HISTORIAN_IP = "10.10.40.30"
HMI_IP = "10.10.40.20"


# ---------------------------------------------------------------------------
# Required GNS3 templates
# ---------------------------------------------------------------------------

REQUIRED_TEMPLATES = [
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
# Manufacturing PLCs
# ---------------------------------------------------------------------------

MANUFACTURING_PLCS = [
    {
        "name": "plc-conveyor",
        "ip": "10.10.40.11",
        "role": "conveyor",
        "age": "8",
        "switch_port": "Ethernet0",
    },
    {
        "name": "plc-robot-cell",
        "ip": "10.10.40.12",
        "role": "robot_cell",
        "age": "10",
        "switch_port": "Ethernet1",
    },
    {
        "name": "plc-packaging",
        "ip": "10.10.40.13",
        "role": "packaging",
        "age": "17",
        "switch_port": "Ethernet2",
    },
    {
        "name": "plc-quality",
        "ip": "10.10.40.14",
        "role": "quality",
        "age": "12",
        "switch_port": "Ethernet3",
    },
]


PLC_TARGETS = (
    "--plc conveyor=10.10.40.11:502 "
    "--plc robot=10.10.40.12:502 "
    "--plc packaging=10.10.40.13:502 "
    "--plc quality=10.10.40.14:502"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_server_urls():
    with open(DATASTORE_FILE, "r", encoding="utf-8") as file_obj:
        content = file_obj.read().strip()

    last_octets = []

    for item in content.split(","):
        item = item.strip()

        if not item:
            continue

        if not item.isdigit():
            raise RuntimeError(
                f"Invalid datastore entry '{item}'."
            )

        last_octets.append(int(item))

    if not last_octets:
        raise RuntimeError(
            f"No valid GNS3 servers found in '{DATASTORE_FILE}'."
        )

    return [
        f"{BASE_IP}{octet}:80"
        for octet in last_octets
    ]


def require_http_success(response, action):
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"{action} failed: "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )


def build_environment(**values):
    return "\n".join(
        f"{key}={value}"
        for key, value in values.items()
    )


def build_interface_config(ip_address):
    return f"""
auto eth0
iface eth0 inet static
    address {ip_address}
    netmask {OPERATIONS_NETMASK}
"""


# ---------------------------------------------------------------------------
# GNS3 template setup
# ---------------------------------------------------------------------------

def ensure_10_port_switch(server_url):
    template_name = OPS_SWITCH_TEMPLATE

    response = requests.get(
        f"{server_url}/v2/templates",
        auth=(GNS3_USER, GNS3_PW),
        timeout=30,
    )
    response.raise_for_status()

    existing = next(
        (
            template
            for template in response.json()
            if template.get("name") == template_name
        ),
        None,
    )

    if existing:
        logging.info(
            "Template '%s' already exists on %s.",
            template_name,
            server_url,
        )
        return

    ports = [
        {
            "name": f"Ethernet{i}",
            "port_number": i,
            "type": "access",
            "vlan": 1,
        }
        for i in range(10)
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

    response = requests.post(
        f"{server_url}/v2/templates",
        json=switch_template,
        auth=(GNS3_USER, GNS3_PW),
        timeout=30,
    )

    require_http_success(
        response,
        f"Create template '{template_name}'",
    )


def update_template(server_url, template, expected_definition):
    template_name = template["name"]
    template_id = template.get("template_id")

    if not template_id:
        raise RuntimeError(
            f"Template '{template_name}' has no template_id."
        )

    changes = {}

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
    updated.update(changes)

    response = requests.put(
        f"{server_url}/v2/templates/{template_id}",
        json=updated,
        auth=(GNS3_USER, GNS3_PW),
        timeout=30,
    )

    require_http_success(
        response,
        f"Update template '{template_name}'",
    )

    logging.info(
        "Updated template '%s': %s",
        template_name,
        ", ".join(
            f"{key}={value!r}"
            for key, value in changes.items()
        ),
    )


def ensure_required_templates(server, server_url):
    available = server.get_templates()

    templates_by_name = {
        template["name"]: template
        for template in available
    }

    for template in REQUIRED_TEMPLATES:
        template_name = template["name"]
        existing = templates_by_name.get(template_name)

        if existing:
            update_template(
                server_url,
                existing,
                template,
            )
            continue

        response = requests.post(
            f"{server_url}/v2/templates",
            json=template,
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )

        require_http_success(
            response,
            f"Register template '{template_name}'",
        )

        logging.info(
            "Registered missing template '%s'.",
            template_name,
        )


# ---------------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------------

def open_or_create_project(server, server_url):
    projects = server.get_projects()

    existing = next(
        (
            project
            for project in projects
            if project["name"] == LAB_NAME
        ),
        None,
    )

    if existing:
        lab = Project(
            project_id=existing["project_id"],
            connector=server,
        )
        lab.get()
        lab.open()

        logging.info(
            "Opened existing project '%s'.",
            LAB_NAME,
        )

        return lab

    lab = Project(
        name=LAB_NAME,
        connector=server,
    )

    lab.create()
    lab.open()

    logging.info(
        "Created project '%s'.",
        LAB_NAME,
    )

    return lab


# ---------------------------------------------------------------------------
# Node creation
# ---------------------------------------------------------------------------

def create_node(
    lab,
    name,
    template,
    x,
    y,
    errors,
):
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
            f"Create node '{name}' failed: {exc}"
        )


def create_scenario_nodes(
    lab,
    errors,
):
    create_node(
        lab,
        "ops-switch",
        OPS_SWITCH_TEMPLATE,
        0,
        80,
        errors,
    )

    plc_positions = [
        (-500, -250),
        (-170, -250),
        (170, -250),
        (500, -250),
    ]

    for plc, (x, y) in zip(
        MANUFACTURING_PLCS,
        plc_positions,
    ):
        create_node(
            lab,
            plc["name"],
            ICS_TEMPLATE,
            x,
            y,
            errors,
        )

    create_node(
        lab,
        "line-hmi",
        ICS_TEMPLATE,
        -160,
        250,
        errors,
    )

    create_node(
        lab,
        "line-historian",
        ICS_TEMPLATE,
        180,
        250,
        errors,
    )

    create_node(
        lab,
        "scada-server",
        MANUFACTURING_SCADA_TEMPLATE,
        500,
        250,
        errors,
    )

    create_node(
        lab,
        "KaliLinux-1",
        KALI_TEMPLATE,
        500,
        80,
        errors,
    )


# ---------------------------------------------------------------------------
# Environment definitions
# ---------------------------------------------------------------------------

def plc_environment(plc):
    return build_environment(
        NODE_MODE="plc",
        PLC_ROLE=plc["role"],
        DEVICE_AGE_YEARS=plc["age"],
        AGE_FAILURE_THRESHOLD_YEARS="12",
        AGE_FAILURE_WINDOW_SECONDS="10",
        AGE_FAILURE_MAX_REQUESTS="30",
        AGE_FAILURE_DURATION_SECONDS="20",
        AGE_FAILURE_MODE="zero",
    )


def hmi_environment():
    return build_environment(
        NODE_MODE="hmi",
        IP_ADDRESS=HMI_IP,
        NETMASK=OPERATIONS_NETMASK,
        PLC_TARGETS=PLC_TARGETS,
    )


def historian_environment():
    return build_environment(
        NODE_MODE="historian",
        IP_ADDRESS=HISTORIAN_IP,
        NETMASK=OPERATIONS_NETMASK,
        PLC_TARGETS=PLC_TARGETS,
    )


def scada_environment():
    return build_environment(
        SCENARIO=SCENARIO,
        SCADA_SUBNETS=OPERATIONS_SUBNET,
        IP_ADDRESS=SCADA_IP,
        NETMASK=OPERATIONS_NETMASK,
    )


# ---------------------------------------------------------------------------
# Environment application
# ---------------------------------------------------------------------------

def set_docker_node_environment(
    server_url,
    lab,
    node_name,
    environment,
    errors,
):
    try:
        node = lab.get_node(node_name)
        node.get()

        response = requests.get(
            f"{server_url}/v2/projects/"
            f"{lab.project_id}/nodes/{node.node_id}",
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )

        response.raise_for_status()

        node_data = response.json()
        properties = dict(
            node_data.get("properties") or {}
        )

        actual = properties.get("environment")

        if actual == environment:
            return

        properties["environment"] = environment

        response = requests.put(
            f"{server_url}/v2/projects/"
            f"{lab.project_id}/nodes/{node.node_id}",
            json={"properties": properties},
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )

        require_http_success(
            response,
            f"Update node '{node_name}' environment",
        )

        logging.info(
            "Updated node '%s' environment.",
            node_name,
        )

    except Exception as exc:
        errors.append(
            f"Set environment '{node_name}' failed: {exc}"
        )


def set_scenario_environment(
    server_url,
    lab,
    errors,
):
    for plc in MANUFACTURING_PLCS:
        set_docker_node_environment(
            server_url,
            lab,
            plc["name"],
            plc_environment(plc),
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
# Network configuration
# ---------------------------------------------------------------------------

def configure_interfaces(
    lab,
    node_name,
    config,
    errors,
):
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
            f"Configure network '{node_name}' failed: {exc}"
        )


def configure_scenario_nodes(
    lab,
    errors,
):
    for plc in MANUFACTURING_PLCS:
        configure_interfaces(
            lab,
            plc["name"],
            build_interface_config(plc["ip"]),
            errors,
        )

    configure_interfaces(
        lab,
        "line-hmi",
        build_interface_config(HMI_IP),
        errors,
    )

    configure_interfaces(
        lab,
        "line-historian",
        build_interface_config(HISTORIAN_IP),
        errors,
    )

    configure_interfaces(
        lab,
        "scada-server",
        build_interface_config(SCADA_IP),
        errors,
    )


# ---------------------------------------------------------------------------
# Kali
# ---------------------------------------------------------------------------

def configure_kali(lab, node_name, errors):
    # Kali is intentionally left unconfigured for the student.
    # No automatic network configuration is performed.
    logging.info(
        "Skipping automated Kali configuration for '%s'.",
        node_name,
    )


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def create_link(
    lab,
    node_a,
    port_a,
    node_b,
    port_b,
    errors,
):
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
            f"Link {node_a}:{port_a} -> "
            f"{node_b}:{port_b} failed: {exc}"
        )


def create_scenario_links(
    lab,
    errors,
):
    for plc in MANUFACTURING_PLCS:
        create_link(
            lab,
            "ops-switch",
            plc["switch_port"],
            plc["name"],
            "eth0",
            errors,
        )

    create_link(
        lab,
        "ops-switch",
        "Ethernet4",
        "line-hmi",
        "eth0",
        errors,
    )

    create_link(
        lab,
        "ops-switch",
        "Ethernet5",
        "line-historian",
        "eth0",
        errors,
    )

    create_link(
        lab,
        "ops-switch",
        "Ethernet6",
        "scada-server",
        "eth0",
        errors,
    )

    create_link(
        lab,
        "ops-switch",
        "Ethernet7",
        "KaliLinux-1",
        "Ethernet0",
        errors,
    )


# ---------------------------------------------------------------------------
# Start nodes
# ---------------------------------------------------------------------------

def start_node(lab, node_name, errors):
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
    lab,
    errors,
):
    for plc in MANUFACTURING_PLCS:
        start_node(
            lab,
            plc["name"],
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

    # Kali is started, but intentionally not configured.
    start_node(
        lab,
        "KaliLinux-1",
        errors,
    )


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_project_on_server(
    server_url,
):
    errors = []

    logging.info(
        "Connecting to GNS3 server at %s.",
        server_url,
    )

    server = Gns3Connector(
        url=server_url,
        user=GNS3_USER,
        cred=GNS3_PW,
    )

    logging.info(
        "GNS3 server version: %s",
        server.get_version(),
    )

    ensure_required_templates(
        server,
        server_url,
    )

    lab = open_or_create_project(
        server,
        server_url,
    )

    create_scenario_nodes(
        lab,
        errors,
    )

    set_scenario_environment(
        server_url,
        lab,
        errors,
    )

    configure_scenario_nodes(
        lab,
        errors,
    )

    create_scenario_links(
        lab,
        errors,
    )

    start_scenario_nodes(
        lab,
        errors,
    )

    configure_kali(
        lab,
        "KaliLinux-1",
        errors,
    )

    if errors:
        raise RuntimeError(
            "\n".join(errors)
        )

    logging.info(
        "%s build completed successfully.",
        LAB_NAME,
    )

    lab.links_summary()


def main():
    try:
        server_urls = read_server_urls()
    except Exception as exc:
        logging.error(
            "Could not read servers: %s",
            exc,
        )
        return 1

    failed = []

    for server_url in server_urls:
        try:
            build_project_on_server(
                server_url
            )
        except Exception as exc:
            logging.error(
                "Build failed for %s: %s",
                server_url,
                exc,
            )
            failed.append(
                server_url
            )

    if failed:
        return 1

    logging.info(
        "All manufacturing builds completed successfully."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
