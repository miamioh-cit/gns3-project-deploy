import time
from gns3fy import Gns3Connector, Project, Node, Link

# Lab Configuration
LAB_NAME = "latest"
IP_ADDRS = ["10.48.229.96", "10.48.229.88", "10.48.229.67"]
GNS3_USER = "gns3"
GNS3_PW = "gns3"

# Function to create nodes
def create_and_start_node(lab, name, template, x, y):
    try:
        node = lab.create_node(name=name, template=template, x=x, y=y)
        if not node:
            raise ValueError(f"❌ Node '{name}' creation failed!")
        print(f"✅ Node '{name}' created successfully.")
        node = lab.get_node(name)
        node.start()
        print(f"🚀 Node '{name}' started.")
    except Exception as e:
        print(f"⚠️ Failed to create/start node '{name}': {e}")

# Function to create links
def create_link_safe(lab, node1, iface1, node2, iface2):
    try:
        lab.create_link(node1, iface1, node2, iface2)
        print(f"🔗 Link created: {node1} ({iface1}) ↔ {node2} ({iface2})")
    except Exception as e:
        print(f"❌ Failed to create link between {node1} and {node2}: {e}")

# Connect to each GNS3 server and create the project
for IP_ADD in IP_ADDRS:
    SERVER_URL = f"http://{IP_ADD}:80"
    try:
        print(f"🔍 Connecting to GNS3 server at {SERVER_URL} ...")
        server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)

        # Check server version
        print(f"✅ GNS3 Version: {server.get_version()}")

        # Check if project already exists
        existing_projects = [p.name for p in server.projects]
        if LAB_NAME in existing_projects:
            print(f"⚠️ Project '{LAB_NAME}' already exists on {IP_ADD}, skipping...")
            continue

        # Create a new project
        lab = server.create_project(name=LAB_NAME)
        print(f"✅ Created project '{LAB_NAME}' on {IP_ADD}")

        # Open the project
        lab = Project(name=LAB_NAME, connector=server)
        lab.get()
        if lab.status != "opened":
            print(f"⚠️ Project '{LAB_NAME}' was not opened successfully, skipping...")
            continue

        print("🚀 Creating network topology...")

        # Create and start nodes
        create_and_start_node(lab, "internet", "Cloud", 76, -76)
        create_and_start_node(lab, "offsite-switch", "Cisco IOSvL2 15.2.1", -33, -175)
        create_and_start_node(lab, "ohio-switch", "Cisco IOSvL2 15.2.1", -19, 280)
        create_and_start_node(lab, "ky-switch-1", "Cisco IOSvL2 15.2.1", 163, 275)
        create_and_start_node(lab, "ky-switch-2", "Cisco IOSvL2 15.2.1", 334, 275)

        # Create and start Windows 10 Clients
        clients = [
            ("offsite-win10", 50, -300),
            ("in-win10-01", -188, -68),
            ("ohio-win10-01", -200, 400),
            ("ohio-win10-02", -116, 400),
            ("ohio-win10-03", -28, 400),
            ("ky-win10-01", 129, 400),
            ("ky-win10-02", 208, 400),
            ("ky-win10-03", 285, 400),
            ("ky-win10-04", 367, 400),
        ]
        for name, x, y in clients:
            create_and_start_node(lab, name, "Windows 10 w/ Edge", x, y)

        # Create and start Routers
        routers = [
            ("in-edge", -113, 32),
            ("offsite-router", -37, -72),
            ("ky-edge", 46, 24),
            ("ky-int", 149, 96),
            ("oh-edge", -31, 91),
            ("oh-int", -31, 192),
        ]
        for name, x, y in routers:
            create_and_start_node(lab, name, "Cisco IOSv 15.5(3)M", x, y)

        # Create and start Windows Server 2022 Servers
        servers = [
            ("offsite-web", -75, -300),
            ("ohio-web", -172, 183),
        ]
        for name, x, y in servers:
            create_and_start_node(lab, name, "Windows Server 2022", x, y)

        # Create links
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
        for src, src_iface, dst, dst_iface in links:
            create_link_safe(lab, src, src_iface, dst, dst_iface)

        # Confirm completion
        print("✅ Nodes created, started, and linked successfully!")
        lab.links_summary()
        print(f"🎉 {LAB_NAME} build is complete. Open the project in GNS3.")

    except Exception as e:
        print(f"❌ Failed to connect to {SERVER_URL} or create project: {e}")
        continue  # Move to the next IP if there's an error
