from gns3fy import Gns3Connector, Project, Node, Link
from getpass import getpass

LAB_NAME = "281-start"
# LAB_NAME = input("Input a unique Lab Name: ")

# Base IP address (first three octets remain constant)
BASE_IP = "http://10.48.10."

# List of last octets for the servers
SERVER_LAST_OCTETS = [159]  # Add more as needed, seperated by commas

GNS3_USER = "gns3"
# GNS3_USER = input("Input your GNS3 Username: ")

GNS3_PW = "gns3"
# GNS3_PW = getpass ("Input your GNS3 Password (It won't show as you enter it!: ")

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

# If lab name is unique, confirm with user.
print("-----------------------------------------------------------------------")
print("Project name is unique, nodes are being created.")
print("-----------------------------------------------------------------------")
print("Please wait until script runs before entering the project in GNS3!")
print("-----------------------------------------------------------------------")

# Now open the project from the server
lab = Project(name=LAB_NAME, connector=server)
lab.get()
lab.open()

# Build Cloud
lab.create_node(name='internet', template='Cloud', x='76', y='-76')

# Create Switches
for switch_name, coords in [
    ('offsite-switch', (-33, -175)),
    ('ohio-switch', (-19, 280)),
    ('ky-switch-1', (163, 275)),
    ('ky-switch-2', (334, 275))
]:
    lab.create_node(name=switch_name, template='Cisco IOSvL2', x=coords[0], y=coords[1])
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
    lab.create_node(name=name, template='Windows 10 w/ Edge', x=x, y=y)
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
    lab.create_node(name=name, template='Cisco IOSv', x=x, y=y)
    router = lab.get_node(name)
    router.start()

# Create and Start Windows Server 2016 Servers
servers = [
    ('offsite-web', -75, -300),
    ('ohio-web', -172, 183)
]

for name, x, y in servers:
    lab.create_node(name=name, template='Windows Server 2022', x=x, y=y)
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
    lab.create_link(node1, int1, node2, int2)

# Confirm completion of the script with the user.
print("-----------------------------------------------------------------------")
print("Nodes created, started, and linked. Here are the links:")
print("-----------------------------------------------------------------------")
lab.links_summary()
print("-----------------------------------------------------------------------")
print(f"{LAB_NAME} build is Complete. It is now safe to open the project in GNS3")
print("Be sure that you document the links in your Visio Topology!!!!")
print("-----------------------------------------------------------------------")
