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

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
EDGE_SWITCH_TEMPLATE = "Ethernet switch"
KALI_TEMPLATE = "Kali Linux"

SENSOR_TEMPLATE = "generic-sensor"
PLC_TEMPLATE = "generic-plc"
HMI_TEMPLATE = "generic-hmi"

MANUFACTURING_SCADA_TEMPLATE = "generic-scada-manufacturing"
MANUFACTURING_SCADA_IMAGE = (
    "evankunkel/generic-scada-manafacturing:latest"
)

SCADA_IP = "10.10.40.200"
KALI_IP = "10.10.40.250"
HMI_IP = "10.10.40.20"
HISTORIAN_IP = "10.10.40.30"


# ---------------------------------------------------------------------------
# Required GNS3 templates
# ---------------------------------------------------------------------------

REQUIRED_TEMPLATES = [
    {
        "name": SENSOR_TEMPLATE,
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
        "name": PLC_TEMPLATE,
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
        "name": HMI_TEMPLATE,
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-hmi:latest",
        "adapters": 5,
        "console_type": "telnet",
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

MANUFACTURING_AREAS = [
    {
        "name": "conveyor",
        "label": "Conveyor Line",
        "field_vlan": "Vlan-01",
        "field_subnet": "192.168.10.0/24",
        "plc": "plc-conveyor",
        "plc_field_ip": "192.168.10.5",
        "plc_ops_ip": "10.10.40.11",
        "field_switch_core_port": "Ethernet0",
        "x": -540,
        "sensors": [
            ("SPEED-101", "192.168.10.1", "rpm"),
            ("PROX-101", "192.168.10.2", "state"),
            ("TEMP-101", "192.168.10.3", "C"),
            ("JAM-101", "192.168.10.4", "flag"),
        ],
        "age": "8",
        "role": "conveyor",
    },
    {
        "name": "robot_cell",
        "label": "Robot Cell",
        "field_vlan": "Vlan-02",
        "field_subnet": "192.168.20.0/24",
        "plc": "plc-robot-cell",
        "plc_field_ip": "192.168.20.5",
        "plc_ops_ip": "10.10.40.12",
        "field_switch_core_port": "Ethernet1",
        "x": -180,
        "sensors": [
            ("POS-201", "192.168.20.1", "mm"),
            ("PROX-201", "192.168.20.2", "state"),
            ("TEMP-201", "192.168.20.3", "C"),
            ("TORQUE-201", "192.168.20.4", "Nm"),
        ],
        "age": "10",
        "role": "robot_cell",
    },
    {
        "name": "packaging",
        "label": "Packaging",
        "field_vlan": "Vlan-03",
        "field_subnet": "192.168.30.0/24",
        "plc": "plc-packaging",
        "plc_field_ip": "192.168.30.5",
        "plc_ops_ip": "10.10.40.13",
        "field_switch_core_port": "Ethernet2",
        "x": 180,
        "sensors": [
            ("COUNT-301", "192.168.30.1", "units/min"),
            ("WEIGHT-301", "192.168.30.2", "kg"),
            ("TEMP-301", "192.168.30.3", "C"),
            ("SEAL-301", "192.168.30.4", "state"),
        ],
        "age": "17",
        "role": "packaging",
    },
    {
        "name": "quality",
        "label": "Quality Control",
        "field_vlan": "Vlan-04",
        "field_subnet": "192.168.40.0/24",
        "plc": "plc-quality",
        "plc_field_ip": "192.168.40.5",
        "plc_ops_ip": "10.10.40.14",
        "field_switch_core_port": "Ethernet3",
        "x": 540,
        "sensors": [
            ("CAM-401", "192.168.40.1", "score"),
            ("REJECT-401", "192.168.40.2", "count"),
            ("VIB-401", "192.168.40.3", "mm/s"),
            ("TEMP-401", "192.168.40.4", "C"),
        ],
        "age": "12",
        "role": "quality",
    },
]


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
    if response.status_code not in (200, 201):
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


def build_plc_config(field_ip, operations_ip):
    return f"""
auto eth0
iface eth0 inet static
    address {field_ip}
    netmask 255.255.255.0

auto eth1
iface eth1 inet static
    address {operations_ip}
    netmask {OPERATIONS_NETMASK}
"""


def sensor_simulation(sensor_name):
    if sensor_name.startswith("SPEED-"):
        return "random_walk:start=1200,step=50,min=500,max=1800"

    if sensor_name.startswith("POS-"):
        return "random_walk:start=50,step=4,min=0,max=100"

    if sensor_name.startswith("COUNT-"):
        return "random_walk:start=35,step=3,min=0,max=70"

    if sensor_name.startswith("WEIGHT-"):
        return "random_walk:start=2.5,step=0.15,min=1.0,max=5.0"

    if sensor_name.startswith("CAM-"):
        return "random_walk:start=95,step=1,min=70,max=100"

    if sensor_name.startswith("REJECT-"):
        return "random_walk:start=1,step=1,min=0,max=10"

    if sensor_name.startswith("TEMP-"):
        return "random_walk:start=55,step=1.5,min=35,max=80"

    if sensor_name.startswith("TORQUE-"):
        return "random_walk:start=25,step=2,min=5,max=50"

    if sensor_name.startswith("VIB-"):
        return "random_walk:start=2.5,step=0.2,min=0.5,max=6"

    if sensor_name.startswith("PROX-"):
        return "random_walk:start=1,step=1,min=0,max=1"

    if sensor_name.startswith("JAM-"):
        return "random_walk:start=0,step=1,min=0,max=1"

    if sensor_name.startswith("SEAL-"):
        return "random_walk:start=1,step=1,min=0,max=1"

    return "random_walk:start=1,step=0.1,min=0,max=10"


# ---------------------------------------------------------------------------
# Template setup
# ---------------------------------------------------------------------------

def ensure_10_port_switch(server_url):
    template_name = CORE_SWITCH_TEMPLATE

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


def update_template(
    server_url,
    template,
    expected_definition,
):
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

    shared_templates = {
        SENSOR_TEMPLATE,
        PLC_TEMPLATE,
        HMI_TEMPLATE,
    }

    for template in REQUIRED_TEMPLATES:
        template_name = template["name"]
        existing = templates_by_name.get(template_name)

        if existing:
            if template_name in shared_templates:
                logging.info(
                    "Leaving shared template '%s' unchanged.",
                    template_name,
                )
                continue

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
# Project
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
    for area in MANUFACTURING_AREAS:
        x = area["x"]

        for index, (
            sensor_name,
            _sensor_ip,
            _units,
        ) in enumerate(area["sensors"]):

            create_node(
                lab,
                sensor_name,
                SENSOR_TEMPLATE,
                x + index * 85,
                -610,
                errors,
            )

        create_node(
            lab,
            area["field_vlan"],
            EDGE_SWITCH_TEMPLATE,
            x + 120,
            -460,
            errors,
        )

        create_node(
            lab,
            area["plc"],
            PLC_TEMPLATE,
            x + 120,
            -300,
            errors,
        )

    create_node(
        lab,
        "ops-switch",
        CORE_SWITCH_TEMPLATE,
        0,
        80,
        errors,
    )

    create_node(
        lab,
        "line-hmi",
        HMI_TEMPLATE,
        -160,
        250,
        errors,
    )

    create_node(
        lab,
        "line-historian",
        HMI_TEMPLATE,
        170,
        250,
        errors,
    )

    create_node(
        lab,
        "scada-server",
        MANUFACTURING_SCADA_TEMPLATE,
        360,
        80,
        errors,
    )

    create_node(
        lab,
        "KaliLinux-1",
        KALI_TEMPLATE,
        600,
        80,
        errors,
    )


# ---------------------------------------------------------------------------
# Environment definitions
# ---------------------------------------------------------------------------

def sensor_environment(
    area,
    sensor_name,
    sensor_ip,
    units,
):
    return build_environment(
        SCENARIO=SCENARIO,
        TAG=sensor_name,
        SIMULATION=sensor_simulation(sensor_name),
        UNITS=units,
        DATA_TYPE="float",
        IP_ADDRESS=sensor_ip,
        NETMASK=OPERATIONS_NETMASK,
        FIELD_SUBNET=area["field_subnet"],
    )


def plc_environment(area):
    return build_environment(
        SCENARIO=SCENARIO,
        PLC_SCAN_SUBNETS=area["field_subnet"],
        PLC_FIELD_INTERFACE="eth0",
        PLC_FIELD_IP=area["plc_field_ip"],
        PLC_FIELD_SUBNET=area["field_subnet"],
        PLC_CONTROL_INTERFACE="eth1",
        PLC_CONTROL_IP=area["plc_ops_ip"],
        PLC_CONTROL_SUBNET=OPERATIONS_SUBNET,
        PLC_MODBUS_PORT=502,
        PLC_ROLE=area["role"],
        DEVICE_AGE_YEARS=area["age"],
        AGE_FAILURE_THRESHOLD_YEARS="12",
        AGE_FAILURE_WINDOW_SECONDS="10",
        AGE_FAILURE_MAX_REQUESTS="30",
        AGE_FAILURE_DURATION_SECONDS="20",
        AGE_FAILURE_MODE="zero",
    )


def hmi_environment():
    targets = " ".join(
        f"--plc {area['name']}={area['plc_ops_ip']}:502"
        for area in MANUFACTURING_AREAS
    )

    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="hmi",
        IP_ADDRESS=HMI_IP,
        NETMASK=OPERATIONS_NETMASK,
        PLC_TARGETS=targets,
    )


def historian_environment():
    targets = " ".join(
        f"--plc {area['name']}={area['plc_ops_ip']}:502"
        for area in MANUFACTURING_AREAS
    )

    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="historian",
        IP_ADDRESS=HISTORIAN_IP,
        NETMASK=OPERATIONS_NETMASK,
        PLC_TARGETS=targets,
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

        actual = properties.get(
            "environment"
        )

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
    for area in MANUFACTURING_AREAS:
        set_docker_node_environment(
            server_url,
            lab,
            area["plc"],
            plc_environment(area),
            errors,
        )

        for sensor_name, sensor_ip, units in area["sensors"]:
            set_docker_node_environment(
                server_url,
                lab,
                sensor_name,
                sensor_environment(
                    area,
                    sensor_name,
                    sensor_ip,
                    units,
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
    for area in MANUFACTURING_AREAS:
        configure_interfaces(
            lab,
            area["plc"],
            build_plc_config(
                area["plc_field_ip"],
                area["plc_ops_ip"],
            ),
            errors,
        )

        for sensor_name, sensor_ip, _units in area["sensors"]:
            configure_interfaces(
                lab,
                sensor_name,
                build_interface_config(sensor_ip),
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
    for area in MANUFACTURING_AREAS:
        create_link(
            lab,
            area["plc"],
            "eth0",
            area["field_vlan"],
            "Ethernet0",
            errors,
        )

        for index, (
            sensor_name,
            _sensor_ip,
            _units,
        ) in enumerate(
            area["sensors"],
            start=1,
        ):
            create_link(
                lab,
                sensor_name,
                "eth0",
                area["field_vlan"],
                f"Ethernet{index}",
                errors,
            )

        create_link(
            lab,
            area["plc"],
            "eth1",
            "ops-switch",
            area["field_switch_core_port"],
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

def start_node(
    lab,
    node_name,
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


def configure_kali(
    lab,
    node_name,
    errors,
):
    logging.info(
        "Skipping automated Kali configuration for '%s'.",
        node_name,
    )


def start_scenario_nodes(
    lab,
    errors,
):
    for area in MANUFACTURING_AREAS:
        start_node(
            lab,
            area["plc"],
            errors,
        )

        for sensor_name, _sensor_ip, _units in area["sensors"]:
            start_node(
                lab,
                sensor_name,
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
