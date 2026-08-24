import logging
import requests
import time
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "480-Test3"
BASE_IP = "http://10.48.229."
GNS3_USER = "gns3"
GNS3_PW = "gns3"

# Read last octets from datastore file
try:
    with open("datastore", "r") as f:
        content = f.read().strip()
        SERVER_LAST_OCTETS = [
            int(octet.strip())
            for octet in content.split(",")
            if octet.strip().isdigit()
        ]
except Exception as e:
    print("Error reading datastore file:", e)
    SERVER_LAST_OCTETS = []

if not SERVER_LAST_OCTETS:
    raise ValueError("No valid server last octets found in 'datastore'.")

SERVER_URLS = [f"{BASE_IP}{octet}:80" for octet in SERVER_LAST_OCTETS]

# Required Docker Templates Payload
REQUIRED_TEMPLATES = [
    {
        "name": "generic-sensor",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-sensor:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": "SCENARIO=wastewater",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg"
    },
    {
        "name": "generic-plc",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-plc:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": "SCENARIO=wastewater",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg"
    },
    {
        "name": "generic-hmi",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-hmi:latest",
        "adapters": 5,
        "console_type": "telnet",
        "environment": "SCENARIO=wastewater",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg"
    },
    {
        "name": "generic-scada",
        "template_type": "docker",
        "category": "guest",
        "image": "wtaylor8/generic-scada:latest",
        "adapters": 11,
        "console_type": "http",
        "environment": "SCENARIO=wastewater",
        "default_name_format": "{name}-{0}",
        "compute_id": "local",
        "symbol": ":/symbols/docker_guest.svg"
    }
]

# Network Configurations
PLC_CONFIGS = {
    "PLC-Influent": "\nauto eth0\niface eth0 inet static\n    address 192.168.1.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.1\n    netmask 255.255.255.0\n",
    "PLC-Primary": "\nauto eth0\niface eth0 inet static\n    address 192.168.2.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.3\n    netmask 255.255.255.0\n",
    "PLC-Aeration": "\nauto eth0\niface eth0 inet static\n    address 192.168.3.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.5\n    netmask 255.255.255.0\n",
    "PLC-Clarification": "\nauto eth0\niface eth0 inet static\n    address 192.168.4.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.7\n    netmask 255.255.255.0\n",
    "PLC-Disenfection": "\nauto eth0\niface eth0 inet static\n    address 192.168.5.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.9\n    netmask 255.255.255.0\n",
    "PLC-Thickening": "\nauto eth0\niface eth0 inet static\n    address 192.168.6.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.11\n    netmask 255.255.255.0\n",
    "PLC-Digestion": "\nauto eth0\niface eth0 inet static\n    address 192.168.7.5\n    netmask 255.255.255.0\n\nauto eth1\niface eth1 inet static\n    address 172.16.0.13\n    netmask 255.255.255.0\n"
}

HMI_CONFIGS = {
    "HMI-Influent": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.2\n    netmask 255.255.255.0\n",
    "HMI-Primary": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.4\n    netmask 255.255.255.0\n",
    "HMI-Aeration": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.6\n    netmask 255.255.255.0\n",
    "HMI-Clarification": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.8\n    netmask 255.255.255.0\n",
    "HMI-Disenfection": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.10\n    netmask 255.255.255.0\n",
    "HMI-Thickening": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.12\n    netmask 255.255.255.0\n",
    "HMI-Digestion": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.14\n    netmask 255.255.255.0\n"
}

SPECIAL_CONFIGS = {
    "scada-server": "\nauto eth0\niface eth0 inet static\n    address 172.16.0.200\n    netmask 255.255.255.0\n"
}

SENSOR_IPS = {
    "FT-101": "192.168.1.1", "LT-101": "192.168.1.2", "DP-101": "192.168.1.3", "P-101": "192.168.1.4",
    "FT-201": "192.168.2.1", "LT-201": "192.168.2.2", "DP-201": "192.168.2.3", "MV-201": "192.168.2.4",
    "DO-301": "192.168.3.1", "FT-301": "192.168.3.2", "MLSS-301": "192.168.3.3", "SV-301": "192.168.3.4",
    "FT-401": "192.168.4.1", "LT-401": "192.168.4.2", "TU-401": "192.168.4.3", "DL-401": "192.168.4.4",
    "CL-501": "192.168.5.1", "FT-501": "192.168.5.2", "LT-501": "192.168.5.3", "AV-501": "192.168.5.4",
    "LT-601": "192.168.6.1", "FT-601": "192.168.6.2", "SS-601": "192.168.6.3", "P-601": "192.168.6.4",
    "T-701": "192.168.7.1",  "PT-701": "192.168.7.2", "FT-701": "192.168.7.3", "GAS-701": "192.168.7.4",
}

SENSOR_CONFIGS = {
    tag: f"\nauto eth0\niface eth0 inet static\n    address {ip}\n    netmask 255.255.255.0\n"
    for tag, ip in SENSOR_IPS.items()
}

# Helpers
def configure_interfaces(node, config):
    try:
        node.get()
        status = getattr(node.status, "value", str(node.status)).lower()
        was_running = status == "started"
        if was_running:
            node.stop()
        node.write_file(path="/etc/network/interfaces", data=config.strip() + "\n")
        if was_running:
            node.start()
        print(f"[OK] Configured network for {node.name}")
    except Exception as e:
        print(f"[FAIL] Network configuration for {node.name}: {e}")

def configure_kali(node):
    try:
        node.get()
        status = getattr(node.status, "value", str(node.status)).lower()
        if status != "started":
            node.start()
        time.sleep(8)
        for attempt in range(30):
            try:
                result = node.execute("nmcli device status")
                if "eth0" in str(result):
                    print(f"[OK] Kali eth0 detected after {attempt + 1} attempts")
                    break
            except Exception:
                pass
            time.sleep(2)
        else:
            raise RuntimeError("Kali eth0 did not become available after 60 seconds")

        node.execute("nmcli connection delete kali-eth0 || true")
        node.execute("nmcli connection add type ethernet ifname eth0 con-name kali-eth0 ipv4.method manual ipv4.addresses 172.16.0.250/24")
        time.sleep(2)
        node.execute("nmcli connection up kali-eth0")
        print("[OK] Kali eth0 configured as 172.16.0.250/24")
    except Exception as e:
        print(f"[FAIL] Kali network configuration: {e}")

def safe_link(lab, n1, p1, n2, p2):
    try:
        lab.create_link(n1, p1, n2, p2)
    except Exception as e:
        print(f"[ERROR] Linking {n1} ({p1}) <-> {n2} ({p2}): {e}")

# Main Deployment
for SERVER_URL in SERVER_URLS:
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)
    print(f"Connecting to GNS3 server at {SERVER_URL}...")

    # Register Missing Templates
    try:
        available_templates = [t["name"] for t in server.get_templates()]
        for tmpl in REQUIRED_TEMPLATES:
            if tmpl["name"] not in available_templates:
                print(f"Registering missing template '{tmpl['name']}'...")
                res = requests.post(f"{SERVER_URL}/v2/templates", json=tmpl)
                if res.status_code in [200, 201]:
                    print(f"[OK] Registered '{tmpl['name']}'")
                else:
                    print(f"[FAIL] HTTP {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[ERROR] Connecting to server {SERVER_URL}: {e}")
        continue

    # Project Setup
    server.create_project(name=LAB_NAME)
    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    print(f"Project '{LAB_NAME}' created. Spawning nodes...")

    # Create Field Devices Top
    sensors_top = [
        ("FT-101", -575, -625), ("LT-101", -483, -628), ("DP-101", -380, -619), ("P-101", -299, -623),
        ("FT-201", -194, -627), ("LT-201", -109, -632), ("DP-201", -25, -618),  ("MV-201", 58, -620),
        ("DO-301", 177, -606),  ("FT-301", 254, -606),  ("MLSS-301", 330, -599),("SV-301", 406, -604),
        ("FT-401", 596, -578),  ("LT-401", 687, -575),  ("TU-401", 786, -577),  ("DL-401", 892, -575)
    ]
    for name, x, y in sensors_top:
        lab.create_node(name=name, template="generic-sensor", x=x, y=y)

    # Top Switches & PLCs/HMIs
    top_vlans = [("Vlan-01", -424, -476), ("Vlan-02", -81, -504), ("Vlan-03", 307, -467), ("Vlan-04", 741, -474)]
    for name, x, y in top_vlans:
        lab.create_node(name=name, template="Ethernet switch", x=x, y=y)

    top_hmis_plcs = [
        ("HMI-Influent", "generic-hmi", -549, -316), ("PLC-Influent", "generic-plc", -419, -367),
        ("HMI-Primary", "generic-hmi", -234, -362),  ("PLC-Primary", "generic-plc", -76, -364),
        ("HMI-Aeration", "generic-hmi", 184, -365),  ("PLC-Aeration", "generic-plc", 312, -356),
        ("HMI-Clarification", "generic-hmi", 598, -325), ("PLC-Clarification", "generic-plc", 746, -340)
    ]
    for name, tmpl, x, y in top_hmis_plcs:
        lab.create_node(name=name, template=tmpl, x=x, y=y)

    # Distribution Switches & Core Devices
    dist_switches = [
        ("Vlan-10", -511, -199), ("Vlan-20", -146, -243), ("Vlan-30", 236, -225), ("Vlan-40", 562, -196),
        ("Vlan-50", -412, 99),   ("Vlan-60", -4, 98),     ("Vlan-70", 460, 92)
    ]
    for name, x, y in dist_switches:
        lab.create_node(name=name, template="Ethernet switch", x=x, y=y)

    lab.create_node(name="Core-Switch", template="Ethernet-Switch-10P", x=38, y=-66)
    lab.create_node(name="scada-server", template="generic-scada", x=375, y=-82)
    lab.create_node(name="KaliLinux-1", template="Kali Linux", x=-662, y=-48)

    # Bottom PLCs/HMIs, VLANs, & Field Devices
    bottom_hmis_plcs = [
        ("HMI-Disenfection", "generic-hmi", -547, 139), ("PLC-Disenfection", "generic-plc", -408, 194),
        ("HMI-Thickening", "generic-hmi", -154, 218),   ("PLC-Thickening", "generic-plc", -5, 203),
        ("HMI-Digestion", "generic-hmi", 280, 166),     ("PLC-Digestion", "generic-plc", 467, 189)
    ]
    for name, tmpl, x, y in bottom_hmis_plcs:
        lab.create_node(name=name, template=tmpl, x=x, y=y)

    bottom_vlans = [("Vlan-05", -410, 317), ("Vlan-06", -8, 306), ("Vlan-07", 482, 325)]
    for name, x, y in bottom_vlans:
        lab.create_node(name=name, template="Ethernet switch", x=x, y=y)

    sensors_bottom = [
        ("CL-501", -564, 402), ("FT-501", -474, 403), ("LT-501", -325, 402), ("AV-501", -231, 402),
        ("LT-601", -107, 398), ("FT-601", -24, 397),  ("SS-601", 63, 396),   ("P-601", 154, 394),
        ("T-701", 344, 410),   ("PT-701", 442, 412),  ("FT-701", 548, 410),  ("GAS-701", 647, 412)
    ]
    for name, x, y in sensors_bottom:
        lab.create_node(name=name, template="generic-sensor", x=x, y=y)

    lab.get()

    # Apply Network Configs
    print("Applying network configurations...")
    for name, config in PLC_CONFIGS.items():
        configure_interfaces(lab.get_node(name), config)
    for name, config in HMI_CONFIGS.items():
        configure_interfaces(lab.get_node(name), config)
    for name, config in SPECIAL_CONFIGS.items():
        configure_interfaces(lab.get_node(name), config)
    for name, config in SENSOR_CONFIGS.items():
        configure_interfaces(lab.get_node(name), config)

    configure_kali(lab.get_node("KaliLinux-1"))
    lab.get()

    # Link Top Segments (VLANs 01 - 04)
    safe_link(lab, "PLC-Influent", "eth0", "Vlan-01", "Ethernet7")
    for idx, sensor in enumerate(["FT-101", "LT-101", "DP-101", "P-101"], start=1):
        safe_link(lab, sensor, "eth0", "Vlan-01", f"Ethernet{idx}")

    safe_link(lab, "Vlan-02", "Ethernet0", "PLC-Primary", "eth0")
    for idx, sensor in enumerate(["FT-201", "LT-201", "DP-201", "MV-201"], start=1):
        safe_link(lab, "Vlan-02", f"Ethernet{idx}", sensor, "eth0")

    safe_link(lab, "PLC-Aeration", "eth0", "Vlan-03", "Ethernet0")
    for idx, sensor in enumerate(["DO-301", "FT-301", "MLSS-301", "SV-301"], start=1):
        safe_link(lab, "Vlan-03", f"Ethernet{idx}", sensor, "eth0")

    safe_link(lab, "PLC-Clarification", "eth0", "Vlan-04", "Ethernet0")
    for idx, sensor in enumerate(["FT-401", "LT-401", "TU-401", "DL-401"], start=1):
        safe_link(lab, "Vlan-04", f"Ethernet{idx}", sensor, "eth0")

    # Link Distribution Networks & Core Switch
    dist_mappings = [
        ("PLC-Influent", "HMI-Influent", "Vlan-10", "Ethernet0"),
        ("PLC-Primary", "HMI-Primary", "Vlan-20", "Ethernet1"),
        ("PLC-Aeration", "HMI-Aeration", "Vlan-30", "Ethernet2"),
        ("PLC-Clarification", "HMI-Clarification", "Vlan-40", "Ethernet3"),
        ("PLC-Disenfection", "HMI-Disenfection", "Vlan-50", "Ethernet4"),
        ("PLC-Thickening", "HMI-Thickening", "Vlan-60", "Ethernet5"),
        ("PLC-Digestion", "HMI-Digestion", "Vlan-70", "Ethernet6")
    ]
    for plc, hmi, vlan, core_port in dist_mappings:
        safe_link(lab, plc, "eth1", vlan, "Ethernet0")
        safe_link(lab, vlan, "Ethernet2", hmi, "eth0")
        safe_link(lab, vlan, "Ethernet7", "Core-Switch", core_port)

    # Link Core to SCADA and Kali
    safe_link(lab, "scada-server", "eth0", "Core-Switch", "Ethernet7")
    safe_link(lab, "KaliLinux-1", "eth0", "Core-Switch", "Ethernet8")

    # Link Bottom Process Segments (VLANs 05 - 07)
    bottom_mappings = [
        ("PLC-Disenfection", "Vlan-05", ["CL-501", "FT-501", "LT-501", "AV-501"]),
        ("PLC-Thickening", "Vlan-06", ["LT-601", "FT-601", "SS-601", "P-601"]),
        ("PLC-Digestion", "Vlan-07", ["T-701", "PT-701", "FT-701", "GAS-701"])
    ]
    for plc, vlan, sensors in bottom_mappings:
        safe_link(lab, plc, "eth0", vlan, "Ethernet0")
        for idx, sensor in enumerate(sensors, start=1):
            safe_link(lab, vlan, f"Ethernet{idx}", sensor, "eth0")

    print(f"Deployment complete for {LAB_NAME} on {SERVER_URL}!")
