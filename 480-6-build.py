#!/usr/bin/env python3
"""Build the Module 6 railroad-control monitoring topology in GNS3.

The topology keeps railroad HMI/historian-to-PLC Modbus/TCP traffic on one
monitored segment and places ``zeek-sensor`` and ``suricata-sensor`` as
passive visibility nodes.  It is an educational lab topology only: no node
connects to a production railroad network.

For evidence, start the HMI and historian first, then use the instructor's
designated SPAN/mirror configuration or GNS3 link capture on the monitored
HMI/historian-to-PLC path.  Sensors are never an inline control hop.
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import shlex
import sys
from pathlib import Path

try:
    import requests
except ImportError:  # Lets --validate run without deployment dependencies.
    requests = None

try:
    from gns3fy import Gns3Connector, Project
except ImportError:  # Lets --validate run without deployment dependencies.
    Gns3Connector = None
    Project = None


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

LAB_NAME = "Module 6 - Railroad Control - Monitoring"
SCENARIO = "railroad-control"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"
GNS3_USER = "gns3"
GNS3_PASSWORD = "gns3"

OPERATIONS_SUBNET = "10.60.30.0/24"
MONITORING_SUBNET = "10.60.50.0/24"
NETMASK = "255.255.255.0"
HMI_IP = "10.60.30.10"
HISTORIAN_IP = "10.60.30.20"
ZEEK_IP = "10.60.50.10"
SURICATA_IP = "10.60.50.11"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
PASSIVE_TAP_TEMPLATE = "Ethernet hub"
RAIL_SENSOR_TEMPLATE = "generic-sensor"
RAIL_PLC_TEMPLATE = "generic-plc"
RAIL_HMI_TEMPLATE = "generic-hmi"
ZEEK_TEMPLATE = "Zeek"
SURICATA_TEMPLATE = "Suricata"
SCADA_TEMPLATE = "generic-scada"
SCADA_IP = "10.60.30.200"
KALI_IP = "10.60.30.250"

# All three application nodes can legitimately poll PLCs. The baseline is
# read-only: writes from any source require operational review.
APPROVED_MODBUS_CLIENTS = (HMI_IP, HISTORIAN_IP, SCADA_IP)
SURICATA_CONFIG = "/etc/suricata/suricata.yaml"
SURICATA_RULE_PATH = "/var/log/suricata/railroad-modbus.rules"

RAIL_AREAS = [
    {
        "name": "interlocking",
        "field_switch": "field-switch-interlocking",
        "field_subnet": "192.168.61.0/24",
        "field_ip": "192.168.61.5",
        "plc": "plc-interlocking",
        "plc_ops_ip": "10.60.30.31",
        "x": -550,
        "sensors": [
            ("TRACK-101", "192.168.61.1", "TRACK-101", "occupied", "float"),
            ("SIGNAL-101", "192.168.61.2", "SIGNAL-101", "aspect", "float"),
        ],
    },
    {
        "name": "crossing",
        "field_switch": "field-switch-crossing",
        "field_subnet": "192.168.62.0/24",
        "field_ip": "192.168.62.5",
        "plc": "plc-crossing",
        "plc_ops_ip": "10.60.30.32",
        "x": -180,
        "sensors": [
            ("GATE-201", "192.168.62.1", "GATE-201", "state", "float"),
            ("APPROACH-201", "192.168.62.2", "APPROACH-201", "occupied", "float"),
        ],
    },
    {
        "name": "yard",
        "field_switch": "field-switch-yard",
        "field_subnet": "192.168.63.0/24",
        "field_ip": "192.168.63.5",
        "plc": "plc-yard",
        "plc_ops_ip": "10.60.30.33",
        "x": 180,
        "sensors": [
            ("SWITCH-301", "192.168.63.1", "SWITCH-301", "position", "float"),
            ("YARD-301", "192.168.63.2", "YARD-301", "occupied", "float"),
        ],
    },
    {
        "name": "dispatch",
        "field_switch": "field-switch-dispatch",
        "field_subnet": "192.168.64.0/24",
        "field_ip": "192.168.64.5",
        "plc": "plc-dispatch",
        "plc_ops_ip": "10.60.30.34",
        "x": 550,
        "sensors": [
            ("ROUTE-401", "192.168.64.1", "ROUTE-401", "state", "float"),
            ("OCCUPANCY-401", "192.168.64.2", "OCCUPANCY-401", "occupied", "float"),
        ],
    },
]

SENSOR_SIMULATION = {
    "TRACK-101": "random_walk:start=0,step=0,min=0,max=1",
    "SIGNAL-101": "random_walk:start=1,step=0,min=0,max=2",
    "GATE-201": "random_walk:start=0,step=0,min=0,max=1",
    "APPROACH-201": "random_walk:start=0,step=0,min=0,max=1",
    "SWITCH-301": "random_walk:start=1,step=0,min=0,max=2",
    "YARD-301": "random_walk:start=0,step=0,min=0,max=1",
    "ROUTE-401": "random_walk:start=1,step=0,min=0,max=2",
    "OCCUPANCY-401": "random_walk:start=0,step=0,min=0,max=1",
}


def environment(**values: object) -> str:
    return "\n".join(f"{key}={value}" for key, value in values.items())


def plc_targets() -> str:
    return " ".join(
        f"--plc {area['name']}={area['plc_ops_ip']}:502" for area in RAIL_AREAS
    )


def detection_rules() -> str:
    clients = "[" + ",".join(APPROVED_MODBUS_CLIENTS) + "]"
    plcs = "[" + ",".join(area["plc_ops_ip"] for area in RAIL_AREAS) + "]"
    return "\n".join((
        '# Baseline: HMI, historian and SCADA read; all writes require review.',
        f'alert modbus any any -> {plcs} 502 (msg:"Railroad lab unexpected Modbus write"; flow:to_server,established; modbus: access write; classtype:policy-violation; sid:4806001; rev:1;)',
        f'alert tcp !{clients} any -> {plcs} 502 (msg:"Railroad lab unapproved Modbus client connection attempt"; flags:S; flow:stateless; classtype:policy-violation; sid:4806010; rev:1;)',
    )) + "\n"


def validate_configuration() -> list[str]:
    """Check the lab's measurable topology requirements without GNS3 access."""
    failures: list[str] = []
    if len(RAIL_AREAS) < 2:
        failures.append("At least two railroad PLCs are required for the monitored path.")
    if any(not area["plc_ops_ip"].startswith("10.60.30.") for area in RAIL_AREAS):
        failures.append("Every railroad PLC must use the monitored operations subnet.")
    if len({HMI_IP, HISTORIAN_IP, SCADA_IP, KALI_IP, ZEEK_IP, SURICATA_IP, *(area["plc_ops_ip"] for area in RAIL_AREAS)}) != 10:
        failures.append("Operations, PLC, and monitoring sensor addresses must be unique.")
    if not plc_targets():
        failures.append("HMI and historian must have named Modbus targets.")
    ops = ipaddress.ip_network(OPERATIONS_SUBNET)
    if len(set(APPROVED_MODBUS_CLIENTS)) != len(APPROVED_MODBUS_CLIENTS):
        failures.append("Approved Modbus clients must be unique.")
    for address in (*APPROVED_MODBUS_CLIENTS, KALI_IP, *(area['plc_ops_ip'] for area in RAIL_AREAS)):
        if ipaddress.ip_address(address) not in ops:
            failures.append(f"{address} must be in the monitored operations subnet.")
    if KALI_IP in APPROVED_MODBUS_CLIENTS:
        failures.append("The optional test workstation must not be an approved polling client.")
    return failures


REQUIRED_TEMPLATES = [
    {
        "name": RAIL_SENSOR_TEMPLATE,
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
        "name": RAIL_PLC_TEMPLATE,
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
        "name": RAIL_HMI_TEMPLATE,
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
    {
        "name": ZEEK_TEMPLATE,
        "template_type": "docker",
        "category": "guest",
        "image": "zeek/zeek:latest",
        "extra_volumes": ["/var/log/zeek"],
        "adapters": 5,
        "console_type": "telnet",
        "environment": "SENSOR_MODE=passive\nSENSOR_TOOL=zeek",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
    {
        "name": SURICATA_TEMPLATE,
        "template_type": "docker",
        "category": "guest",
        "image": "jasonish/suricata:latest",
        "extra_volumes": ["/var/log/suricata"],
        "adapters": 5,
        "console_type": "telnet",
        "environment": "SENSOR_MODE=passive\nSENSOR_TOOL=suricata",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
]


def require_success(response: requests.Response, action: str) -> None:
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(f"{action} failed: HTTP {response.status_code}: {response.text}")


def read_server_urls() -> list[str]:
    path = Path(DATASTORE_FILE)
    if not path.exists():
        raise RuntimeError(f"Required file '{DATASTORE_FILE}' was not found.")
    urls: list[str] = []
    for value in path.read_text(encoding="utf-8").split(","):
        value = value.strip()
        if not value:
            continue
        if not value.isdigit():
            raise RuntimeError("datastore must contain comma-separated GNS3 server last octets.")
        urls.append(f"{BASE_IP}{int(value)}:80")
    if not urls:
        raise RuntimeError("datastore contains no usable GNS3 server addresses.")
    return urls


def ensure_switch_template(server_url: str) -> None:
    response = requests.get(f"{server_url}/v2/templates", auth=(GNS3_USER, GNS3_PASSWORD), timeout=30)
    response.raise_for_status()
    if any(item.get("name") == CORE_SWITCH_TEMPLATE for item in response.json()):
        return
    ports = [
        {"name": f"Ethernet{number}", "port_number": number, "type": "access", "vlan": 1}
        for number in range(10)
    ]
    require_success(
        requests.post(
            f"{server_url}/v2/templates",
            json={
                "name": CORE_SWITCH_TEMPLATE,
                "template_type": "ethernet_switch",
                "category": "switch",
                "compute_id": "local",
                "default_name_format": "{name}-{0}",
                "symbol": ":/symbols/ethernet_switch.svg",
                "builtin": False,
                "ports_mapping": ports,
            },
            auth=(GNS3_USER, GNS3_PASSWORD),
            timeout=30,
        ),
        f"create switch template '{CORE_SWITCH_TEMPLATE}'",
    )


def update_template(server_url: str, current: dict, expected: dict) -> None:
    changed = {
        key: value
        for key, value in expected.items()
        if key in {"template_type", "category", "image", "adapters", "console_type", "environment", "default_name_format", "compute_id", "symbol"}
        and current.get(key) != value
    }
    if not changed:
        return
    template_id = current.get("template_id")
    if not template_id:
        raise RuntimeError(f"Template '{expected['name']}' has no template_id.")
    payload = dict(current)
    payload.update(changed)
    require_success(
        requests.put(
            f"{server_url}/v2/templates/{template_id}", json=payload,
            auth=(GNS3_USER, GNS3_PASSWORD), timeout=30,
        ),
        f"update template '{expected['name']}'",
    )


def ensure_required_templates(server: Gns3Connector, server_url: str) -> None:
    existing = {item["name"]: item for item in server.get_templates()}
    # Inspect before project cleanup. Never silently rewrite a shared image.
    for expected in REQUIRED_TEMPLATES:
        current = existing.get(expected["name"])
        if not current:
            continue
        minimum = 2 if expected["name"] in {RAIL_PLC_TEMPLATE, ZEEK_TEMPLATE, SURICATA_TEMPLATE} else 1
        if current.get("template_type") != "docker" or int(current.get("adapters") or 0) < minimum:
            raise RuntimeError(
                f"Template '{expected['name']}' must be Docker with at least {minimum} adapters; "
                "correct the shared template before rebuilding. Existing project nodes have not been removed."
            )
    if "Kali Linux" not in existing:
        raise RuntimeError("Required optional-test workstation template 'Kali Linux' is missing; existing project nodes have not been removed.")
    for expected in REQUIRED_TEMPLATES:
        current = existing.get(expected["name"])
        if current:
            if expected["name"] in {
                ZEEK_TEMPLATE,
                SURICATA_TEMPLATE,
                SCADA_TEMPLATE,
                RAIL_SENSOR_TEMPLATE,
                RAIL_PLC_TEMPLATE,
                RAIL_HMI_TEMPLATE,
            }:
                logging.info("Using existing shared template '%s'.", expected["name"])
            else:
                update_template(server_url, current, expected)
            continue
        require_success(
            requests.post(f"{server_url}/v2/templates", json=expected, auth=(GNS3_USER, GNS3_PASSWORD), timeout=30),
            f"register template '{expected['name']}'",
        )


def open_or_create_project(server: Gns3Connector) -> Project:
    record = next((item for item in server.get_projects() if item["name"] == LAB_NAME), None)
    if record:
        project = Project(project_id=record["project_id"], connector=server)
        project.get()
        project.open()
        return project
    project = Project(name=LAB_NAME, connector=server)
    project.create()
    project.open()
    return project


def node_names() -> set[str]:
    names = {
        "railroad-monitored-switch", "railroad-modbus-tap",
        "railroad-hmi", "railroad-historian", "railroad-scada",
        "KaliLinux-1", "zeek-sensor", "suricata-sensor",
    }
    for area in RAIL_AREAS:
        names.update({area["field_switch"], area["plc"]})
        names.update(item[0] for item in area["sensors"])
    return names


def is_managed_name(name: str, bases: set[str]) -> bool:
    return any(name == base or (name.startswith(base) and name[len(base):].isdigit()) for base in bases)


def remove_existing_nodes(project: Project) -> None:
    project.get()
    for node in list(project.nodes):
        if not is_managed_name(node.name, node_names()):
            continue
        if str(getattr(node.status, "value", node.status)).lower() == "started":
            node.stop()
        node.delete()
    project.get()


def create_node(project: Project, name: str, template: str, x: int, y: int) -> None:
    try:
        project.create_node(name=name, template=template, x=x, y=y)
    except Exception as exc:
        raise RuntimeError(f"Create node '{name}' from '{template}' failed: {exc}") from exc


def create_nodes(project: Project) -> None:
    for area in RAIL_AREAS:
        for index, (sensor, *_rest) in enumerate(area["sensors"]):
            create_node(project, sensor, RAIL_SENSOR_TEMPLATE, area["x"] - 60 + index * 120, -430)
        create_node(project, area["field_switch"], CORE_SWITCH_TEMPLATE, area["x"] + 60, -290)
        create_node(project, area["plc"], RAIL_PLC_TEMPLATE, area["x"] + 60, -135)
    create_node(project, "railroad-monitored-switch", CORE_SWITCH_TEMPLATE, 0, 95)
    create_node(project, "railroad-hmi", RAIL_HMI_TEMPLATE, -290, 250)
    create_node(project, "railroad-historian", RAIL_HMI_TEMPLATE, -90, 250)
    create_node(project, "railroad-scada", SCADA_TEMPLATE, -300, 430)
    create_node(project, "railroad-modbus-tap", PASSIVE_TAP_TEMPLATE, 0, 180)
    create_node(project, "zeek-sensor", ZEEK_TEMPLATE, 180, 250)
    create_node(project, "suricata-sensor", SURICATA_TEMPLATE, 400, 250)
    create_node(project, "KaliLinux-1", "Kali Linux", 570, 430)


def set_node_property(
    server_url: str,
    project: Project,
    name: str,
    property_name: str,
    value: str,
) -> None:
    node = project.get_node(name)
    node.get()
    endpoint = f"{server_url}/v2/projects/{project.project_id}/nodes/{node.node_id}"
    response = requests.get(endpoint, auth=(GNS3_USER, GNS3_PASSWORD), timeout=30)
    response.raise_for_status()
    properties = dict(response.json().get("properties") or {})
    properties[property_name] = value
    require_success(
        requests.put(
            endpoint,
            json={"properties": properties},
            auth=(GNS3_USER, GNS3_PASSWORD),
            timeout=30,
        ),
        f"set {property_name} for '{name}'",
    )


def set_environment(server_url: str, project: Project, name: str, value: str) -> None:
    set_node_property(server_url, project, name, "environment", value)


def set_start_command(server_url: str, project: Project, name: str, value: str) -> None:
    set_node_property(server_url, project, name, "start_command", value)


def interfaces(entries: list[tuple[str, str]]) -> str:
    return "\n\n".join(
        "\n".join((f"auto eth{index}", f"iface eth{index} inet static", f"    address {address}", f"    netmask {mask}"))
        for index, (address, mask) in enumerate(entries)
    )


def configure_interfaces(project: Project, name: str, config: str) -> None:
    node = project.get_node(name)
    node.get()
    if str(getattr(node.status, "value", node.status)).lower() == "started":
        node.stop()
    node.write_file(path="/etc/network/interfaces", data=config.strip() + "\n")


def plc_environment(area: dict) -> str:
    return environment(
        SCENARIO=SCENARIO, NODE_MODE="plc", PLC_ROLE=area["name"],
        FIELD_IP_ADDRESS=area["field_ip"], FIELD_SUBNET=area["field_subnet"],
        IP_ADDRESS=area["plc_ops_ip"], NETMASK=NETMASK, PLC_MODBUS_PORT=502,
        PLC_SCAN_SUBNETS=area["field_subnet"], PLC_FIELD_INTERFACE="eth0",
        PLC_FIELD_IP=area["field_ip"], PLC_FIELD_SUBNET=area["field_subnet"],
        PLC_CONTROL_INTERFACE="eth1", PLC_CONTROL_IP=area["plc_ops_ip"],
        PLC_CONTROL_SUBNET=OPERATIONS_SUBNET,
    )

def sensor_start_command(tool: str, management_ip: str) -> str:
    """Configure management on eth0 and capture passively on eth1."""
    if tool not in {"zeek", "suricata"}:
        raise ValueError(f"Unknown monitoring tool: {tool}")
    commands = [
        "set -eu",
        "command -v ip >/dev/null",
        "ip link set eth0 up",
        f"ip addr replace {management_ip}/24 dev eth0",
        "ip link set eth1 up",
        "ip addr flush dev eth1",
        "ip link set eth1 promisc on",
    ]
    if tool == "zeek":
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
                f"printf '%s' {shlex.quote(detection_rules())} > {SURICATA_RULE_PATH}",
                f"suricata -T -c {SURICATA_CONFIG} -S {SURICATA_RULE_PATH} --set app-layer.protocols.modbus.enabled=yes -l /var/log/suricata",
                f"exec suricata -c {SURICATA_CONFIG} -S {SURICATA_RULE_PATH} --set app-layer.protocols.modbus.enabled=yes -k none -i eth1 -l /var/log/suricata",
            ]
        )
    return "sh -c " + shlex.quote("; ".join(commands))


def apply_environments(server_url: str, project: Project) -> None:
    for area in RAIL_AREAS:
        set_environment(server_url, project, area["plc"], plc_environment(area))
        for name, address, tag, units, data_type in area["sensors"]:
            set_environment(
                server_url, project, name,
                environment(SCENARIO=SCENARIO, TAG=tag, SIMULATION=SENSOR_SIMULATION[tag], UNITS=units, DATA_TYPE=data_type, IP_ADDRESS=address, NETMASK=NETMASK, FIELD_SUBNET=area["field_subnet"]),
            )
    set_environment(server_url, project, "railroad-hmi", environment(SCENARIO=SCENARIO, NODE_MODE="hmi", IP_ADDRESS=HMI_IP, NETMASK=NETMASK, PLC_TARGETS=plc_targets()))
    set_environment(server_url, project, "railroad-historian", environment(SCENARIO=SCENARIO, NODE_MODE="historian", IP_ADDRESS=HISTORIAN_IP, NETMASK=NETMASK, PLC_TARGETS=plc_targets()))
    set_environment(
        server_url,
        project,
        "railroad-scada",
        environment(
            SCENARIO=SCENARIO,
            NODE_MODE="scada",
            IP_ADDRESS=SCADA_IP,
            NETMASK=NETMASK,
            SCADA_SUBNETS=OPERATIONS_SUBNET,
        ),
    )
    set_start_command(
        server_url,
        project,
        "zeek-sensor",
        sensor_start_command("zeek", ZEEK_IP),
    )
    set_start_command(
        server_url,
        project,
        "suricata-sensor",
        sensor_start_command("suricata", SURICATA_IP),
    )


def configure_nodes(project: Project) -> None:
    for area in RAIL_AREAS:
        configure_interfaces(project, area["plc"], interfaces([(area["field_ip"], NETMASK), (area["plc_ops_ip"], NETMASK)]))
        for name, address, *_rest in area["sensors"]:
            configure_interfaces(project, name, interfaces([(address, NETMASK)]))
    for name, address in (
        ("railroad-hmi", HMI_IP),
        ("railroad-historian", HISTORIAN_IP),
        ("railroad-scada", SCADA_IP),
    ):
        configure_interfaces(project, name, interfaces([(address, NETMASK)]))


def create_link(project: Project, left: str, left_port: str, right: str, right_port: str) -> None:
    try:
        project.create_link(left, left_port, right, right_port)
    except Exception as exc:
        raise RuntimeError(f"Link {left}:{left_port} -> {right}:{right_port} failed: {exc}") from exc


def create_links(project: Project) -> None:
    for area in RAIL_AREAS:
        create_link(project, area["plc"], "eth0", area["field_switch"], "Ethernet0")
        for port, (sensor, *_rest) in enumerate(area["sensors"], start=1):
            create_link(project, sensor, "eth0", area["field_switch"], f"Ethernet{port}")

    # The Ethernet hub is a passive TAP. HMI/historian Modbus requests must
    # cross it before reaching a PLC, so both sensor NICs receive copies.
    create_link(project, "railroad-hmi", "eth0", "railroad-monitored-switch", "Ethernet0")
    create_link(project, "railroad-historian", "eth0", "railroad-monitored-switch", "Ethernet1")
    create_link(project, "railroad-modbus-tap", "Ethernet0", "railroad-monitored-switch", "Ethernet2")
    for port, area in enumerate(RAIL_AREAS, start=1):
        create_link(project, area["plc"], "eth1", "railroad-modbus-tap", f"Ethernet{port}")
    # eth0 is the Monitoring-zone management interface.  eth1 has no IP
    # address and receives the copied Modbus frames from the passive TAP.
    create_link(project, "zeek-sensor", "eth0", "railroad-monitored-switch", "Ethernet3")
    create_link(project, "suricata-sensor", "eth0", "railroad-monitored-switch", "Ethernet4")
    create_link(project, "railroad-scada", "eth0", "railroad-monitored-switch", "Ethernet5")
    create_link(project, "KaliLinux-1", "Ethernet0", "railroad-monitored-switch", "Ethernet6")
    create_link(project, "zeek-sensor", "eth1", "railroad-modbus-tap", "Ethernet5")
    create_link(project, "suricata-sensor", "eth1", "railroad-modbus-tap", "Ethernet6")


def start_node(project: Project, name: str) -> None:
    node = project.get_node(name)
    node.get()
    if str(getattr(node.status, "value", node.status)).lower() != "started":
        node.start()


def start_nodes(project: Project) -> None:
    for area in RAIL_AREAS:
        for sensor, *_rest in area["sensors"]:
            start_node(project, sensor)
        start_node(project, area["plc"])
    # Start passive visibility before HMI/historian polling begins.
    for name in (
        "railroad-modbus-tap",
        "zeek-sensor",
        "suricata-sensor",
        "railroad-hmi",
        "railroad-historian",
        "railroad-scada",
        "KaliLinux-1",
    ):
        start_node(project, name)


def build_project(server_url: str) -> None:
    if requests is None or Gns3Connector is None:
        raise RuntimeError("requests and gns3fy are required for deployment; install requirements.txt first.")
    server = Gns3Connector(url=server_url, user=GNS3_USER, cred=GNS3_PASSWORD)
    logging.info("Connected to GNS3 %s at %s.", server.get_version(), server_url)
    ensure_switch_template(server_url)
    ensure_required_templates(server, server_url)
    project = open_or_create_project(server)
    remove_existing_nodes(project)
    create_nodes(project)
    project.get()
    apply_environments(server_url, project)
    configure_nodes(project)
    project.get()
    create_links(project)
    start_nodes(project)
    project.links_summary()
    logging.info("%s topology created. The passive TAP is connected to the HMI/historian-to-PLC Modbus path and both sensors.", LAB_NAME)
    logging.info("Topology start requests completed; verify live polling and sensor output before collecting lab evidence.")
    logging.info("Configure Kali's actual guest NIC manually as %s/24; the builder cannot configure a QEMU guest via Docker interfaces files.", KALI_IP)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="validate the topology definition without contacting GNS3")
    parser.add_argument("--print-rules", action="store_true", help="print the railroad detection rules without contacting GNS3")
    args = parser.parse_args(argv)
    failures = validate_configuration()
    if failures:
        for failure in failures:
            logging.error("Configuration validation failed: %s", failure)
        return 1
    if args.print_rules:
        print(detection_rules(), end="")
        return 0
    if args.validate:
        logging.info("480-6 railroad monitoring topology validation passed.")
        return 0
    try:
        servers = read_server_urls()
    except RuntimeError as exc:
        logging.error("Startup failed: %s", exc)
        return 1
    failed: list[str] = []
    for server_url in servers:
        try:
            build_project(server_url)
        except Exception as exc:
            logging.exception("Build failed for %s: %s", server_url, exc)
            failed.append(server_url)
    if failed:
        logging.error("Deployment failed on: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
