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
import logging
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
SCENARIO = "railroad_control"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"
GNS3_USER = "gns3"
GNS3_PASSWORD = "gns3"

OPERATIONS_SUBNET = "10.60.1.0/24"
NETMASK = "255.255.255.0"
HMI_IP = "10.60.1.10"
HISTORIAN_IP = "10.60.1.20"
KALI_IP = "10.60.1.250"
ZEEK_IP = "10.60.1.50"
SURICATA_IP = "10.60.1.51"

CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
RAIL_SENSOR_TEMPLATE = "railroad-sensor"
RAIL_PLC_TEMPLATE = "railroad-plc"
RAIL_HMI_TEMPLATE = "railroad-hmi"

RAIL_AREAS = [
    {
        "name": "interlocking",
        "field_switch": "field-switch-interlocking",
        "field_subnet": "192.168.61.0/24",
        "field_ip": "192.168.61.5",
        "plc": "plc-interlocking",
        "plc_ops_ip": "10.60.1.31",
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
        "plc_ops_ip": "10.60.1.32",
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
        "plc_ops_ip": "10.60.1.33",
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
        "plc_ops_ip": "10.60.1.34",
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


def validate_configuration() -> list[str]:
    """Check the lab's measurable topology requirements without GNS3 access."""
    failures: list[str] = []
    if len(RAIL_AREAS) < 2:
        failures.append("At least two railroad PLCs are required for the monitored path.")
    if any(not area["plc_ops_ip"].startswith("10.60.1.") for area in RAIL_AREAS):
        failures.append("Every railroad PLC must use the monitored operations subnet.")
    if HMI_IP == ZEEK_IP or HMI_IP == SURICATA_IP or ZEEK_IP == SURICATA_IP:
        failures.append("HMI and monitoring sensor addresses must be unique.")
    if not plc_targets():
        failures.append("HMI and historian must have named Modbus targets.")
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
        "name": "zeek-sensor",
        "template_type": "docker",
        "category": "guest",
        "image": "zeek/zeek:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": "SENSOR_MODE=passive\nSENSOR_TOOL=zeek",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg",
    },
    {
        "name": "suricata-sensor",
        "template_type": "docker",
        "category": "guest",
        "image": "jasonish/suricata:latest",
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
    for expected in REQUIRED_TEMPLATES:
        current = existing.get(expected["name"])
        if current:
            if expected["name"] in {"zeek-sensor", "suricata-sensor"}:
                logging.info("Using existing instructor monitoring template '%s'.", expected["name"])
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
        "railroad-monitored-switch", "railroad-hmi", "railroad-historian",
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
    create_node(project, "zeek-sensor", "zeek-sensor", 145, 250)
    create_node(project, "suricata-sensor", "suricata-sensor", 340, 250)
    create_node(project, "KaliLinux-1", "Kali Linux", 550, 250)


def set_environment(server_url: str, project: Project, name: str, value: str) -> None:
    node = project.get_node(name)
    node.get()
    endpoint = f"{server_url}/v2/projects/{project.project_id}/nodes/{node.node_id}"
    response = requests.get(endpoint, auth=(GNS3_USER, GNS3_PASSWORD), timeout=30)
    response.raise_for_status()
    properties = dict(response.json().get("properties") or {})
    properties["environment"] = value
    require_success(
        requests.put(endpoint, json={"properties": properties}, auth=(GNS3_USER, GNS3_PASSWORD), timeout=30),
        f"set environment for '{name}'",
    )


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
    set_environment(server_url, project, "zeek-sensor", environment(SCENARIO=SCENARIO, SENSOR_MODE="passive", SENSOR_TOOL="zeek", CAPTURE_INTERFACE="eth0", MONITORED_SUBNET=OPERATIONS_SUBNET, MONITORED_PORT=502, IP_ADDRESS=ZEEK_IP, NETMASK=NETMASK))
    set_environment(server_url, project, "suricata-sensor", environment(SCENARIO=SCENARIO, SENSOR_MODE="passive", SENSOR_TOOL="suricata", CAPTURE_INTERFACE="eth0", MONITORED_SUBNET=OPERATIONS_SUBNET, MONITORED_PORT=502, IP_ADDRESS=SURICATA_IP, NETMASK=NETMASK))


def configure_nodes(project: Project) -> None:
    for area in RAIL_AREAS:
        configure_interfaces(project, area["plc"], interfaces([(area["field_ip"], NETMASK), (area["plc_ops_ip"], NETMASK)]))
        for name, address, *_rest in area["sensors"]:
            configure_interfaces(project, name, interfaces([(address, NETMASK)]))
    for name, address in (("railroad-hmi", HMI_IP), ("railroad-historian", HISTORIAN_IP), ("zeek-sensor", ZEEK_IP), ("suricata-sensor", SURICATA_IP), ("KaliLinux-1", KALI_IP)):
        configure_interfaces(project, name, interfaces([(address, NETMASK)]))


def create_link(project: Project, left: str, left_port: str, right: str, right_port: str) -> None:
    try:
        project.create_link(left, left_port, right, right_port)
    except Exception as exc:
        raise RuntimeError(f"Link {left}:{left_port} -> {right}:{right_port} failed: {exc}") from exc


def create_links(project: Project) -> None:
    for index, area in enumerate(RAIL_AREAS):
        create_link(project, area["plc"], "eth0", area["field_switch"], "Ethernet0")
        for port, (sensor, *_rest) in enumerate(area["sensors"], start=1):
            create_link(project, sensor, "eth0", area["field_switch"], f"Ethernet{port}")
        create_link(project, area["plc"], "eth1", "railroad-monitored-switch", f"Ethernet{index}")
    create_link(project, "railroad-hmi", "eth0", "railroad-monitored-switch", "Ethernet4")
    create_link(project, "railroad-historian", "eth0", "railroad-monitored-switch", "Ethernet5")
    # These passive interfaces are intentionally on the monitored segment and
    # are not placed between the HMI/historian and any PLC.
    create_link(project, "zeek-sensor", "eth0", "railroad-monitored-switch", "Ethernet6")
    create_link(project, "suricata-sensor", "eth0", "railroad-monitored-switch", "Ethernet7")
    create_link(project, "KaliLinux-1", "Ethernet0", "railroad-monitored-switch", "Ethernet8")


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
    # HMI and historian start before monitoring evidence is collected.
    for name in ("railroad-hmi", "railroad-historian", "zeek-sensor", "suricata-sensor", "KaliLinux-1"):
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
    logging.info("%s is ready. Capture the HMI/historian-to-PLC link or configure the instructor's mirror feed for evidence.", LAB_NAME)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="validate the topology definition without contacting GNS3")
    args = parser.parse_args(argv)
    failures = validate_configuration()
    if failures:
        for failure in failures:
            logging.error("Configuration validation failed: %s", failure)
        return 1
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

