#!/usr/bin/env python3
"""
Build the CIT 480-3 Miami Valley Traffic Operations GNS3 project.

This project uses the same generic Docker templates used by the earlier
ICS/OT scenarios:

* generic-sensor
* generic-plc
* generic-hmi
* generic-scada

The topology is intentionally simple. Four traffic operation zones each have
field sensors, one PLC, and one HMI. All zone networks uplink to a core switch
where the SCADA server and Kali workstation are attached.
"""

import logging
import sys
import time

import requests
from gns3fy import Gns3Connector, Project


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

LAB_NAME = "CIT480 Miami Valley Traffic Operations"
BASE_IP = "http://10.48.229."
DATASTORE_FILE = "datastore"

GNS3_USER = "gns3"
GNS3_PW = "gns3"

SCENARIO = "traffic"
CORE_SWITCH_TEMPLATE = "Ethernet-Switch-10P"
EDGE_SWITCH_TEMPLATE = "Ethernet switch"
OPERATIONS_SUBNET = "172.16.0.0/24"


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
    """Ensure the GNS3 server has a reusable local Ethernet switch with 10 ports."""
    template_name = CORE_SWITCH_TEMPLATE

    try:
        response = requests.get(f"{server_url}/v2/templates", auth=(GNS3_USER, GNS3_PW))
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
        raise RuntimeError(f"Network error creating '{template_name}' on {server_url}: {exc}") from exc

    logging.info("Created template '%s' with %s ports on %s.", template_name, len(ports), server_url)


def ensure_required_templates(server, server_url):
    """Register or update the Docker templates required by this scenario."""
    try:
        available_templates = server.get_templates()
    except Exception as exc:
        raise RuntimeError(f"Could not list GNS3 templates on {server_url}: {exc}") from exc

    templates_by_name = {
        template["name"]: template
        for template in available_templates
    }

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
            require_http_success(response, f"Register template '{template_name}' on {server_url}")
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error registering template '{template_name}' on {server_url}: {exc}"
            ) from exc


def update_existing_template_environment(server_url, template, expected_environment):
    """Update a reused Docker template if it still points at another scenario."""
    template_name = template["name"]
    template_id = template.get("template_id")
    actual_environment = template.get("environment")

    if actual_environment == expected_environment:
        logging.info("Template '%s' already has %s on %s.", template_name, expected_environment, server_url)
        return

    if not template_id:
        raise RuntimeError(f"Template '{template_name}' on {server_url} has no template_id; cannot update it.")

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
        require_http_success(response, f"Update template '{template_name}' environment on {server_url}")
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Network error updating template '{template_name}' environment on {server_url}: {exc}"
        ) from exc


def open_or_create_project(server, server_url):
    """Open the existing project or create it if it is not present."""
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
        raise RuntimeError(f"Could not open or create project '{LAB_NAME}' on {server_url}: {exc}") from exc

    return lab


def create_node(lab, name, template, x, y, errors):
    """Create one node and record a detailed error if it fails."""
    try:
        lab.create_node(name=name, template=template, x=x, y=y)
        logging.info("Created node '%s' with template '%s'.", name, template)
    except Exception as exc:
        errors.append(f"Create node '{name}' using template '{template}' failed: {exc}")


def build_environment(**values):
    """Return Docker environment variables in the format GNS3 expects."""
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
    """Return the two-interface PLC configuration."""
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
        errors.append(f"Configure network for node '{node_name}' failed: {exc}")


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
            logging.info("Node '%s' already has %s.", node_name, environment)
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
        errors.append(f"Set environment for node '{node_name}' to '{environment}' failed: {exc}")


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


def configure_kali(lab, node_name, errors):
    """Configure Kali with a persistent static IPv4 address through NetworkManager."""
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
                    logging.info("Kali eth0 detected after %s attempt(s).", attempt + 1)
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
            "ipv4.addresses 172.16.0.250/24"
        )
        time.sleep(2)
        node.execute("nmcli connection up kali-eth0")
        logging.info("Configured Kali '%s' as 172.16.0.250/24.", node_name)
    except Exception as exc:
        errors.append(f"Configure Kali node '{node_name}' failed: {exc}")


def create_link(lab, node_a, port_a, node_b, port_b, errors):
    """Create one link and record a detailed error if it fails."""
    try:
        lab.create_link(node_a, port_a, node_b, port_b)
        logging.info("Linked %s:%s to %s:%s.", node_a, port_a, node_b, port_b)
    except Exception as exc:
        errors.append(f"Create link {node_a}:{port_a} -> {node_b}:{port_b} failed: {exc}")


def create_scenario_nodes(lab, errors):
    """Create sensors, PLCs, HMIs, switches, SCADA, and Kali."""
    for zone in TRAFFIC_ZONES:
        x_base = zone["x"]

        for index, (sensor_name, _sensor_ip) in enumerate(zone["sensors"]):
            create_node(
                lab,
                sensor_name,
                "generic-sensor",
                x_base + (index * 85),
                -610,
                errors,
            )

        create_node(lab, zone["field_vlan"], EDGE_SWITCH_TEMPLATE, x_base + 120, -460, errors)
        create_node(lab, zone["hmi"], "generic-hmi", x_base, -250, errors)
        create_node(lab, zone["plc"], "generic-plc", x_base + 120, -300, errors)
        create_node(lab, zone["operations_vlan"], EDGE_SWITCH_TEMPLATE, x_base + 65, -125, errors)

    create_node(lab, "Core-Switch", CORE_SWITCH_TEMPLATE, 0, 80, errors)
    create_node(lab, "scada-server", "generic-scada", 250, 80, errors)
    create_node(lab, "KaliLinux-1", "Kali Linux", -250, 80, errors)


def configure_scenario_nodes(lab, errors):
    """Apply network settings to every Docker node in the scenario."""
    for zone in TRAFFIC_ZONES:
        configure_interfaces(
            lab,
            zone["plc"],
            build_plc_config(zone["plc_field_ip"], zone["plc_ops_ip"]),
            errors,
        )
        configure_interfaces(lab, zone["hmi"], build_interface_config(zone["hmi_ip"]), errors)

        for sensor_name, sensor_ip in zone["sensors"]:
            configure_interfaces(lab, sensor_name, build_interface_config(sensor_ip), errors)

    configure_interfaces(lab, "scada-server", build_interface_config("172.16.0.200"), errors)


def plc_environment(zone):
    """Return the traffic PLC environment for one operations zone."""
    return build_environment(
        SCENARIO=SCENARIO,
        PLC_LOGIC_FILE=f"traffic/plc-{zone['name'].lower()}-logic.yaml",
        PLC_SCAN_SUBNETS=zone["subnet"],
    )


def hmi_environment():
    """Return the traffic HMI environment."""
    return build_environment(
        SCENARIO=SCENARIO,
        HMI_SCAN_SUBNETS=OPERATIONS_SUBNET,
    )


def sensor_environment():
    """Return the traffic field sensor environment."""
    return build_environment(SCENARIO=SCENARIO)


def scada_environment():
    """Return the traffic SCADA environment used for PLC auto-discovery."""
    return build_environment(
        SCENARIO=SCENARIO,
        SCADA_SUBNETS=OPERATIONS_SUBNET,
    )


def set_scenario_environment(server_url, lab, errors):
    """Force all reusable Docker nodes to use traffic instead of wastewater."""

    for zone in TRAFFIC_ZONES:
        set_docker_node_environment(server_url, lab, zone["plc"], plc_environment(zone), errors)
        set_docker_node_environment(server_url, lab, zone["hmi"], hmi_environment(), errors)

        for sensor_name, _sensor_ip in zone["sensors"]:
            set_docker_node_environment(server_url, lab, sensor_name, sensor_environment(), errors)

    set_docker_node_environment(server_url, lab, "scada-server", scada_environment(), errors)


def start_scenario_nodes(lab, errors):
    """Start all traffic Docker nodes so discovery can run immediately."""
    for zone in TRAFFIC_ZONES:
        start_node(lab, zone["plc"], errors)
        start_node(lab, zone["hmi"], errors)

        for sensor_name, _sensor_ip in zone["sensors"]:
            start_node(lab, sensor_name, errors)

    start_node(lab, "scada-server", errors)


def create_scenario_links(lab, errors):
    """Connect the field and operations networks."""
    for zone in TRAFFIC_ZONES:
        create_link(lab, zone["plc"], "eth0", zone["field_vlan"], "Ethernet0", errors)

        for index, (sensor_name, _sensor_ip) in enumerate(zone["sensors"], start=1):
            create_link(lab, sensor_name, "eth0", zone["field_vlan"], f"Ethernet{index}", errors)

        create_link(lab, zone["plc"], "eth1", zone["operations_vlan"], "Ethernet0", errors)
        create_link(lab, zone["hmi"], "eth0", zone["operations_vlan"], "Ethernet1", errors)
        create_link(
            lab,
            zone["operations_vlan"],
            "Ethernet7",
            "Core-Switch",
            zone["core_port"],
            errors,
        )

    create_link(lab, "Core-Switch", "Ethernet7", "scada-server", "eth0", errors)
    create_link(lab, "Core-Switch", "Ethernet8", "KaliLinux-1", "Ethernet0", errors)


def build_project_on_server(server_url):
    """Build the full Miami Valley Traffic Operations project on one GNS3 server."""
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

    logging.info("Creating nodes for '%s' on %s.", LAB_NAME, server_url)
    create_scenario_nodes(lab, errors)

    try:
        lab.get()
    except Exception as exc:
        errors.append(f"Refresh project inventory after node creation failed: {exc}")

    logging.info("Setting Docker node environments to SCENARIO=%s on %s.", SCENARIO, server_url)
    set_scenario_environment(server_url, lab, errors)

    logging.info("Applying network configurations for '%s' on %s.", LAB_NAME, server_url)
    configure_scenario_nodes(lab, errors)

    try:
        lab.get()
    except Exception as exc:
        errors.append(f"Refresh project inventory after network configuration failed: {exc}")

    logging.info("Creating links for '%s' on %s.", LAB_NAME, server_url)
    create_scenario_links(lab, errors)

    logging.info("Starting traffic PLC, HMI, sensor, and SCADA nodes on %s.", server_url)
    start_scenario_nodes(lab, errors)

    configure_kali(lab, "KaliLinux-1", errors)

    if errors:
        raise RuntimeError("\n".join(f"{server_url}: {error}" for error in errors))

    logging.info("Nodes created, configured, and linked. Link summary follows.")
    lab.links_summary()
    logging.info("%s build is complete on %s. It is safe to open the project in GNS3.", LAB_NAME, server_url)


def main():
    """Read target servers and build the project on each one."""
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
        logging.error("Deployment finished with errors on: %s", ", ".join(failed_servers))
        return 1

    logging.info("All Miami Valley Traffic Operations builds completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
