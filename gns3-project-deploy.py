from gns3fy import Gns3Connector, Project, Node, Link
import sys

# 🔧 Configuration
LAB_NAME = "281-test12"
SERVER_URL = "http://10.48.229.44:80"

# 🔗 Connect to GNS3
server = Gns3Connector(url=SERVER_URL)
print(f"🔗 Connected to GNS3 server at {SERVER_URL} (version: {server.get_version()})")

# 🚫 Check for existing project
existing = server.get_projects()
if any(p["name"] == LAB_NAME for p in existing):
    print(f"❌ Project '{LAB_NAME}' already exists. Aborting.")
    sys.exit(1)

# 🆕 Create project
server.create_project(name=LAB_NAME)
print("✅ Project created.")

# 🧠 Attach & open
lab = Project(name=LAB_NAME, connector=server)
lab.get()
lab.open()

# 📦 Required templates
required_templates = {
    "Cloud", "Cisco IOSvL2 15.2.1", "Windows 10 w/ Edge", "Cisco IOSv 15.5(3)M", "Windows Server 2022"
}
available = {t["name"] for t in server.get_templates()}
missing = required_templates - available
if missing:
    print(f"❌ Missing required templates: {missing}")
    sys.exit(1)

# 🧱 Define nodes
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

for name, template, x, y in nodes:
    lab.create_node(name=name, template=template, x=x, y=y)

# ▶️ Start nodes
for name, *_ in nodes:
    lab.get_node(name).start()

# 🔌 Define links
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

for src, sport, dst, dport in links:
    lab.create_link(src, sport, dst, dport)

# ✅ All done
print("✅ All nodes created, started, and linked.")
lab.links_summary()
print(f"🎉 {LAB_NAME} is ready in GNS3.")
