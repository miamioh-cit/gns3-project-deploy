#!/usr/bin/env python3

from __future__ import annotations

import logging
import sys
import time

import requests
from gns3fy import Gns3Connector, Project


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

LAB_NAME = "Module 3 - Miami Valley Traffic Operations"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "traffic"

OPERATIONS_SUBNET = "172.16.0.0/24"
OPERATIONS_NETMASK = "255.255.255.0"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
EDGE_SWITCH_TEMPLATE = "Ethernet switch"
KALI_TEMPLATE = "Kali Linux"

TRAFFIC_SCADA_TEMPLATE = "generic-scada-traffic"
TRAFFIC_SCADA_IMAGE = (
    "evankunkel/generic-scada-traffic:latest"
)

SCADA_IP = "172.16.0.200"
KALI_IP = "172.16.0.250"
HISTORIAN_IP = "172.16.0.220"


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
        "name": TRAFFIC_SCADA_TEMPLATE,
        "template_type": "docker",
        "category": "guest",
        "image": TRAFFIC_SCADA_IMAGE,
        "adapters": 11,
        "console_type": "http",
        "environment": f"SCENARIO={SCENARIO}",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
]


# ---------------------------------------------------------------------------
# Traffic zones
# ---------------------------------------------------------------------------

TRAFFIC_ZONES = [
    {
        "name": "I75",
        "label": "I-75 Mainline",
        "field_vlan": "Vlan-01",
        "operations_vlan": "Vlan-10",
        "subnet": "192.168.1.0/24",
        "plc": "PLC-I75",
        "hmi": "HMI-I75",
        "plc_field_ip": "192.168.1.5",
        "plc_ops_ip": "172.16.0.1",
        "hmi_ip": "172.16.0.2",
        "core_port": "Ethernet0",
        "x": -540,
        "sensors": [
            ("CAM-101", "192.168.1.1"),
            ("LOOP-101", "192.168.1.2"),
            ("SIGNAL-101", "192.168.1.3"),
            ("VMS-101", "192.168.1.4"),
        ],
    },
    {
        "name": "US35",
        "label": "US-35 Corridor",
        "field_vlan": "Vlan-02",
        "operations_vlan": "Vlan-20",
        "subnet": "192.168.2.0/24",
        "plc": "PLC-US35",
        "hmi": "HMI-US35",
        "plc_field_ip": "192.168.2.5",
        "plc_ops_ip": "172.16.0.3",
        "hmi_ip": "172.16.0.4",
        "core_port": "Ethernet1",
        "x": -180,
        "sensors": [
            ("CAM-201", "192.168.2.1"),
            ("LOOP-201", "192.168.2.2"),
            ("SIGNAL-201", "192.168.2.3"),
            ("VMS-201", "192.168.2.4"),
        ],
    },
    {
        "name": "SR48",
        "label": "SR-48 Far Hills",
        "field_vlan": "Vlan-03",
        "operations_vlan": "Vlan-30",
        "subnet": "192.168.3.0/24",
        "plc": "PLC-SR48",
        "hmi": "HMI-SR48",
        "plc_field_ip": "192.168.3.5",
        "plc_ops_ip": "172.16.0.5",
        "hmi_ip": "172.16.0.6",
        "core_port": "Ethernet2",
        "x": 180,
        "sensors": [
            ("CAM-301", "192.168.3.1"),
            ("LOOP-301", "192.168.3.2"),
            ("SIGNAL-301", "192.168.3.3"),
            ("VMS-301", "192.168.3.4"),
        ],
    },
    {
        "name": "DOWNTOWN",
        "label": "Downtown Grid",
        "field_vlan": "Vlan-04",
        "operations_vlan": "Vlan-40",
        "subnet": "192.168.4.0/24",
        "plc": "PLC-Downtown",
        "hmi": "HMI-Downtown",
        "plc_field_ip": "192.168.4.5",
        "plc_ops_ip": "172.16.0.7",
        "hmi_ip": "172.16.0.8",
        "core_port": "Ethernet3",
        "x": 540,
        "sensors": [
            ("CAM-401", "192.168.4.1"),
            ("LOOP-401", "192.168.4.2"),
            ("SIGNAL-401", "192.168.4.3"),
            ("VMS-401", "192.168.4.4"),
        ],
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

        response = requests.post(
            f"{server_url}/v2/templates",
            json=template,
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )

        require_http_success(
            response,
            f"Register template '{template['name']}'",
        )

        logging.info(
            "Registered template '%s'.",
            template["name"],
        )


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
        project_id = existing["project_id"]

        logging.info(
            "Existing project '%s' found. Deleting it before rebuild.",
            LAB_NAME,
        )

        # Close the project if it is open.
        if existing.get("status") == "opened":
            response = requests.post(
                f"{server_url}/v2/projects/{project_id}/close",
                auth=(GNS3_USER, GNS3_PW),
                timeout=30,
            )

            if response.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"Close project '{LAB_NAME}' failed: "
                    f"HTTP {response.status_code}: {response.text}"
                )

            logging.info(
                "Closed existing project '%s'.",
                LAB_NAME,
            )

        # Delete the old project.
        response = requests.delete(
            f"{server_url}/v2/projects/{project_id}",
            auth=(GNS3_USER, GNS3_PW),
            timeout=30,
        )

        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"Delete project '{LAB_NAME}' failed: "
                f"HTTP {response.status_code}: {response.text}"
            )

        logging.info(
            "Deleted existing project '%s'.",
            LAB_NAME,
        )

        time.sleep(2)

    # Create a completely fresh project.
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
    netmask 255.255.255.0
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
    netmask 255.255.255.0
"""


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


# ---------------------------------------------------------------------------
# Environment definitions
# ---------------------------------------------------------------------------

def sensor_units(sensor_name):

    if sensor_name.startswith("CAM-"):
        return "mph"

    if sensor_name.startswith("LOOP-"):
        return "veh/min"

    if sensor_name.startswith("SIGNAL-"):
        return "state"

    return "flag"


def sensor_simulation(sensor_name):

    if sensor_name.startswith("CAM-"):
        return "random_walk:start=45,step=3,min=0,max=85"

    if sensor_name.startswith("LOOP-"):
        return "random_walk:start=20,step=2,min=0,max=70"

    if sensor_name.startswith("SIGNAL-"):
        return "random_walk:start=1,step=1,min=0,max=2"

    return "random_walk:start=1,step=0.1,min=0,max=1"


def sensor_environment(
    zone,
    sensor_name,
    sensor_ip,
):
    return build_environment(
        SCENARIO=SCENARIO,
        TAG=sensor_name,
        SIMULATION=sensor_simulation(
            sensor_name
        ),
        UNITS=sensor_units(
            sensor_name
        ),
        DATA_TYPE="float",
        IP_ADDRESS=sensor_ip,
        NETMASK=OPERATIONS_NETMASK,
        FIELD_SUBNET=zone["subnet"],
    )


def plc_environment(zone):
    return build_environment(
        SCENARIO=SCENARIO,
        PLC_SCAN_SUBNETS=zone["subnet"],
        PLC_FIELD_INTERFACE="eth0",
        PLC_FIELD_IP=zone["plc_field_ip"],
        PLC_FIELD_SUBNET=zone["subnet"],
        PLC_CONTROL_INTERFACE="eth1",
        PLC_CONTROL_IP=zone["plc_ops_ip"],
        PLC_CONTROL_SUBNET=OPERATIONS_SUBNET,
        PLC_MODBUS_PORT=502,
    )


def hmi_environment(zone):
    return build_environment(
        SCENARIO=SCENARIO,
        NODE_MODE="hmi",
        IP_ADDRESS=zone["hmi_ip"],
        NETMASK=OPERATIONS_NETMASK,
        PLC_TARGETS=(
            f"--plc {zone['name'].lower()}="
            f"{zone['plc_ops_ip']}:502"
        ),
    )


def historian_environment():
    targets = " ".join(
        f"--plc {zone['name'].lower()}="
        f"{zone['plc_ops_ip']}:502"
        for zone in TRAFFIC_ZONES
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
        SCADA_DIAGRAM_CONFIG="module3/diagrams.yaml",
        IP_ADDRESS=SCADA_IP,
        NETMASK=OPERATIONS_NETMASK,
    )


# ---------------------------------------------------------------------------
# Node creation
# ---------------------------------------------------------------------------

def create_scenario_nodes(
    lab,
    errors,
):
    for zone in TRAFFIC_ZONES:

        x = zone["x"]

        for index, (
            sensor_name,
            _sensor_ip,
        ) in enumerate(zone["sensors"]):

            create_node(
                lab,
                sensor_name,
                "generic-sensor",
                x + index * 85,
                -610,
                errors,
            )

        create_node(
            lab,
            zone["field_vlan"],
            EDGE_SWITCH_TEMPLATE,
            x + 120,
            -460,
            errors,
        )

        create_node(
            lab,
            zone["plc"],
            "generic-plc",
            x + 120,
            -300,
            errors,
        )

        create_node(
            lab,
            zone["hmi"],
            "generic-hmi",
            x,
            -250,
            errors,
        )

        create_node(
            lab,
            zone["operations_vlan"],
            EDGE_SWITCH_TEMPLATE,
            x + 65,
            -125,
            errors,
        )

    create_node(
        lab,
        "Core-Switch",
        CORE_SWITCH_TEMPLATE,
        0,
        80,
        errors,
    )

    create_node(
        lab,
        "hmi-poller",
        "generic-hmi",
        -280,
        80,
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
        TRAFFIC_SCADA_TEMPLATE,
        280,
        80,
        errors,
    )

    create_node(
        lab,
        "KaliLinux-1",
        KALI_TEMPLATE,
        540,
        80,
        errors,
    )


# ---------------------------------------------------------------------------
# Environment application
# ---------------------------------------------------------------------------

def set_scenario_environment(
    server_url,
    lab,
    errors,
):
    for zone in TRAFFIC_ZONES:

        set_docker_node_environment(
            server_url,
            lab,
            zone["plc"],
            plc_environment(zone),
            errors,
        )

        set_docker_node_environment(
            server_url,
            lab,
            zone["hmi"],
            hmi_environment(zone),
            errors,
        )

        for sensor_name, sensor_ip in zone["sensors"]:

            set_docker_node_environment(
                server_url,
                lab,
                sensor_name,
                sensor_environment(
                    zone,
                    sensor_name,
                    sensor_ip,
                ),
                errors,
            )

    set_docker_node_environment(
        server_url,
        lab,
        "hmi-poller",
        build_environment(
            SCENARIO=SCENARIO,
            NODE_MODE="hmi",
            IP_ADDRESS="172.16.0.20",
            NETMASK=OPERATIONS_NETMASK,
        ),
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
# Network configuration
# ---------------------------------------------------------------------------

def configure_scenario_nodes(
    lab,
    errors,
):
    for zone in TRAFFIC_ZONES:

        configure_interfaces(
            lab,
            zone["plc"],
            build_plc_config(
                zone["plc_field_ip"],
                zone["plc_ops_ip"],
            ),
            errors,
        )

        configure_interfaces(
            lab,
            zone["hmi"],
            build_interface_config(
                zone["hmi_ip"]
            ),
            errors,
        )

        for sensor_name, sensor_ip in zone["sensors"]:

            configure_interfaces(
                lab,
                sensor_name,
                build_interface_config(
                    sensor_ip
                ),
                errors,
            )

    configure_interfaces(
        lab,
        "hmi-poller",
        build_interface_config(
            "172.16.0.20"
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "historian",
        build_interface_config(
            HISTORIAN_IP
        ),
        errors,
    )

    configure_interfaces(
        lab,
        "scada-server",
        build_interface_config(
            SCADA_IP
        ),
        errors,
    )


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def create_scenario_links(
    lab,
    errors,
):
    for zone in TRAFFIC_ZONES:

        create_link(
            lab,
            zone["plc"],
            "eth0",
            zone["field_vlan"],
            "Ethernet0",
            errors,
        )

        for index, (
            sensor_name,
            _sensor_ip,
        ) in enumerate(
            zone["sensors"],
            start=1,
        ):

            create_link(
                lab,
                sensor_name,
                "eth0",
                zone["field_vlan"],
                f"Ethernet{index}",
                errors,
            )

        create_link(
            lab,
            zone["plc"],
            "eth1",
            zone["operations_vlan"],
            "Ethernet0",
            errors,
        )

        create_link(
            lab,
            zone["hmi"],
            "eth0",
            zone["operations_vlan"],
            "Ethernet1",
            errors,
        )

        create_link(
            lab,
            zone["operations_vlan"],
            "Ethernet7",
            "Core-Switch",
            zone["core_port"],
            errors,
        )

    create_link(
        lab,
        "Core-Switch",
        "Ethernet4",
        "hmi-poller",
        "eth0",
        errors,
    )

    create_link(
        lab,
        "Core-Switch",
        "Ethernet5",
        "historian",
        "eth0",
        errors,
    )

    create_link(
        lab,
        "Core-Switch",
        "Ethernet7",
        "scada-server",
        "eth0",
        errors,
    )

    create_link(
        lab,
        "Core-Switch",
        "Ethernet8",
        "KaliLinux-1",
        "Ethernet0",
        errors,
    )


# ---------------------------------------------------------------------------
# Start nodes
# ---------------------------------------------------------------------------

def start_scenario_nodes(
    lab,
    errors,
):
    for zone in TRAFFIC_ZONES:

        start_node(
            lab,
            zone["plc"],
            errors,
        )

        start_node(
            lab,
            zone["hmi"],
            errors,
        )

        for sensor_name, _sensor_ip in zone["sensors"]:

            start_node(
                lab,
                sensor_name,
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
        "All traffic builds completed successfully."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
