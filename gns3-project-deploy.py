import logging
from gns3fy import Gns3Connector, Project
import sys

# Config
LAB_NAME = "281-test12"
BASE_IP = "http://10.48.229."
SERVER_LAST_OCTETS = [44]
GNS3_USER = "gns3"
GNS3_PW = "gns3"

# Setup server connection
SERVER_URLS = [f"{BASE_IP}{octet}:80" for octet in SERVER_LAST_OCTETS]
server = None
for SERVER_URL in SERVER_URLS:
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, password=GNS3_PW)
    print("🔗 Connecting to GNS3 server:", SERVER_URL, "Version:", server.get_version())
    break

# Check if project already exists
existing_projects = server.get_projects()
if any(p["name"] == LAB_NAME for p in existing_projects):
    print(f"⚠️ Project '{LAB_NAME}' already exists. Aborting to avoid conflict.")
    sys.exit(1)

# Create project
try:
    lab = server.create_project(name=LAB_NAME)
except Exception as e:
    print(f"❌ Failed to create project: {e}")
    sys.exit(1)

print("✅ Project created. Starting node deployment...")

# Load project
lab = Project(name=LAB_NAME, connector=server)
lab.get()
lab.open()

# Validate template availability
required_templates = {
    "Cloud", "Cisco IOSvL2 15.2.1", "Windows 10 w/ Edge", "Cisco IOSv 15.5(3)M", "Windows Server 2022"
}
available_templates = {t["name"] for t in server.get_templates()}
missing_templates = required_templates - available_templates
if missing_templates:
    print(f"❌ Missing required templates: {missing_templates}")
    sys.exit(1)

# Node creation definitions
nodes = [
    ("internet", "Cloud", 76, -76),
    ("offsite-switch", "Cisco IOSvL2 15.2.1", -33, -175),
    ("ohio-switch", "Cisco IOSvL2 15.2.1", -19, 280),
    ("ky-switch-1", "Cisco IOSvL2 15.2.1", 163, 275),
    ("ky-switch-2", "Cisco IOSvL2 15.2.1", 334, 275),
    ("offsite-win10", "Windows 10 w/ Edge", 50, -300),
    ("in-win10-01", "Windows 10 w/ Edge", -188, -68),
    ("ohio-win10-01", "Windows 10 w/ Edge", -200, 400),
    ("ohio-win10-02", "Windows 10 w/ Edge", -116, 400),
    ("ohio-win10-03", "Windows 10 w/ Edge", -28, 400),
    ("ky-win10-01", "Windows 10 w/ Edge", 129, 400),
    ("ky-win10-02", "Windows 10 w/ Edge", 208, 400),
    ("ky-win10-03", "Windows 10 w/ Edge", 285, 400),
    ("ky-win10-04", "Windows 10 w/ Edge", 367, 400),
    ("in-edge", "Cisco IOSv 15.5(3)M", -113, 32),
    ("offsite-router", "Cisco IOSv 15.5(3)M", -37, -72),
    ("ky-edge", "Cisco IOSv 15.5(3)M", 46, 24),
    ("ky-int", "Cisco IOSv 15.5(3)M", 149, 96),
    ("oh-edge", "Cisco IOSv 15.5(3)M", -31, 91),
    ("oh-int", "Cisco IOSv 15.5(3)M", -31, 192),
    ("offsite-web", "Windows Server 2022", -75, -300),
    ("ohio-web", "Windows Server 2022", -172, 183)
]

# Create nodes
for name, template, x, y in nodes:
    lab.create_node(name=name, template=template, x=x, y=y)

# Start all nodes
for name, *_ in nodes:
    node = lab.get_node(name)
    node.start()

# Define links
links = [
    ("offsite-web", "Ethernet0", "offsite-switch", "Gi0/0"),
    ("offsite-win10", "NIC1", "offsite-switch", "Gi0/1"),
    ("offsite-switch", "Gi0/2", "offsite-router", "Gi0/0"),
    ("in-edge", "Gi0/0", "offsite-router", "Gi0/1"),
    ("ky-edge", "Gi0/0", "offsite-router", "Gi0/2"),
    ("ky-edge", "Gi0/1", "ky-int", "Gi0/1"),
    ("ky-edge", "Gi0/2", "oh-edge", "Gi0/0"),
    ("in-edge", "Gi0/1", "oh-edge", "Gi0/1"),
    ("oh-edge", "Gi0/2", "oh-int", "Gi0/0"),
    ("internet", "eth0", "ky-edge", "Gi0/3"),
    ("oh-int", "Gi0/1", "ohio-switch", "Gi0/0"),
    ("ohio-win10-01", "NIC1", "ohio-switch", "Gi0/1"),
    ("ohio-win10-02", "NIC1", "ohio-switch", "Gi0/2"),
    ("ohio-win10-03", "NIC1", "ohio-switch", "Gi0/3"),
    ("ohio-web", "Ethernet0", "oh-int", "Gi0/2"),
    ("in-win10-01", "NIC1", "in-edge", "Gi0/2"),
    ("ky-int", "Gi0/0", "ky-switch-1", "Gi0/0"),
    ("ky-switch-1", "Gi0/1", "ky-switch-2", "Gi0/0"),
    ("ky-win10-01", "NIC1", "ky-switch-1", "Gi0/2"),
    ("ky-win10-02", "NIC1", "ky-switch-1", "Gi0/3"),
    ("ky-win10-03", "NIC1", "ky-switch-2", "Gi1/0"),
    ("ky-win10-04", "NIC1", "ky-switch-2", "Gi1/1")
]

# Create links
for src_node, src_port, dst_node, dst_port in links:
    lab.create_link(src_node, src_port, dst_node, dst_port)

# Done
print("✅ Nodes created, started, and linked.")
print("🔗 Link Summary:")
print("-----------------------------------------------------------------------")
lab.links_summary()
print("-----------------------------------------------------------------------")
print(f"✅ {LAB_NAME} build complete. You can now safely open the project in GNS3.")
print("-----------------------------------------------------------------------")
