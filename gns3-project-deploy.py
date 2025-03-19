from gns3fy import Gns3Connector, Project, Node, Link
from getpass import getpass
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

LAB_NAME = "281-new"

# Base IP address (first three octets remain constant)
BASE_IP = "http://10.48.229."

# List of last octets for the servers
SERVER_LAST_OCTETS = [44]  # Add more as needed, separated by commas

GNS3_USER = "gns3"
GNS3_PW = "gns3"

# Generate full server URLs
SERVER_URLS = [f"{BASE_IP}{octet}:80" for octet in SERVER_LAST_OCTETS]

# Try to connect to each server until one succeeds
server = None
for SERVER_URL in SERVER_URLS:
    try:
        server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)
        print("Connecting to GNS3 server to verify uniqueness of Project name", server.get_version(), "at", SERVER_URL)
        break
    except Exception as e:
        print(f"Failed to connect to {SERVER_URL}: {e}")

if server is None:
    print("Could not connect to any GNS3 servers. Exiting.")
    exit()

# Verify that lab name is unique, then create a new project on the server.
try:
    lab = server.create_project(name=LAB_NAME)
except:
    print("=========================================================")
    print("Error: May not be a unique Lab Name!")
    print("=========================================================")
    from sys import exit
    exit()

print("-----------------------------------------------------------------------")
print("Project name is unique, nodes are being created.")
print("-----------------------------------------------------------------------")
print("Please wait until script runs before entering the project in GNS3!")
print("-----------------------------------------------------------------------")

# Open the project from the server
lab = Project(name=LAB_NAME, connector=server)
lab.get()
lab.open()

# Verify available templates
available_templates = [template["name"] for template in server.get_templates()]
logging.debug(f"Available Templates: {available_templates}")

# Function to create nodes while filtering out unwanted fields
def create_filtered_node(lab, name, template, x, y):
    data = {
        "name": name,
        "compute_id": "local",
        "x": x,
        "y": y
    }

    # Ensure '__pydantic_initialised__' is removed
    if "__pydantic_initialised__" in data:
        del data["__pydantic_initialised__"]

    logging.debug(f"Creating node: {data}")
    
    try:
        lab.create_node(**data)
    except Exception as e:
        logging.error(f"Failed to create node {name}: {e}")

# Build Cloud (check if the template exists)
if "Cloud" in available_templates:
    create_filtered_node(lab, name='internet', template='Cloud', x=76, y=-76)
else:
    print("Cloud template not found! Skipping 'internet' node.")

# Create Switches
switches = [
    ('offsite-switch', -33, -175),
    ('ohio-switch', -19, 280),
    ('ky-switch-1', 163, 275),
    ('ky-switch-2', 334, 275),
]

for switch_name, (x, y) in switches:
    create_filtered_node(lab, switch_name, 'Cisco IOSvL2 15.2.1', x, y)
    sw = lab.get_node(switch_name)
    sw.start()

# Create and Start Windows 10 Clients
win_clients = [
    ('offsite-win10', 50, -300),
    ('in-win10-01', -188, -68),
    ('ohio-win10-01', -200, 400),
    ('ohio-win10-02', -116, 400),
    ('ohio-win10-03', -28, 400),
    ('ky-win10-01', 129, 400),
    ('ky-win10-02', 208, 400),
    ('ky-win10-03', 285, 400),
    ('ky-win10-04', 367, 400),
]

for name, x, y in win_clients:
    create_filtered_node(lab, name, 'Windows 10 w/ Edge', x, y)
    win = lab.get_node(name)
    win.start()

# Create and Start Routers
routers = [
    ('in-edge', -113, 32),
    ('offsite-router', -37, -72),
    ('ky-edge', 46, 24),
    ('ky-int', 149, 96),
    ('oh-edge', -31, 91),
    ('oh-int', -31, 192),
]

for name, x, y in routers:
    create_filtered_node(lab, name, 'Cisco IOSv 15.5(3)M', x, y)
    router = lab.get_node(name)
    router.start()

# Create and Start Windows Server 2016 Servers
servers = [
    ('offsite-web', -75, -300),
    ('ohio-web', -172, 183)
]

for name, x, y in servers:
    create_filtered_node(lab, name, 'Windows Server 2022', x, y)
    server_node = lab.get_node(name)
    server_node.start()

# Link the nodes
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
    ("ky-win10-04", "NIC1", "ky-switch-2", "Gi1/1"),
]

for node1, int1, node2, int2 in links:
    try:
        lab.create_link(node1, int1, node2, int2)
    except Exception as e:
        logging.error(f"Failed to create link between {node1} and {node2}: {e}")

print("-----------------------------------------------------------------------")
print("Nodes created, started, and linked. Here are the links:")
print("-----------------------------------------------------------------------")
lab.links_summary()
print("-----------------------------------------------------------------------")
print(f"{LAB_NAME} build is Complete. It is now safe to open the project in GNS3")
print("Be sure that you document the links in your Visio Topology!!!!")
print("-----------------------------------------------------------------------")
