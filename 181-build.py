import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "181-test"

BASE_IP = "http://10.48.229."

# Read last octets from datastore file
try:
    with open("datastore", "r") as f:
        content = f.read().strip()
        SERVER_LAST_OCTETS = [int(octet.strip()) for octet in content.split(",") if octet.strip().isdigit()]
except Exception as e:
    print("Error reading datastore file:", e)
    SERVER_LAST_OCTETS = []

if not SERVER_LAST_OCTETS:
    raise ValueError("No valid server last octets found in 'datastore'.")

SERVER_URLS = [f"{BASE_IP}{octet}:80" for octet in SERVER_LAST_OCTETS]

GNS3_USER = "gns3"
GNS3_PW = "gns3"

for SERVER_URL in SERVER_URLS:
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)
    print("Connecting to GNS3 server to verify uniqueness of Project name", server.get_version(), "at", SERVER_URL)

    lab = server.create_project(name=LAB_NAME)

    print("-----------------------------------------------------------------------")
    print(f"Project '{LAB_NAME}' created on {SERVER_URL}. Nodes are being created.")
    print("-----------------------------------------------------------------------")
    print("Please wait until script runs before entering the project in GNS3!")
    print("-----------------------------------------------------------------------")

    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    available_templates = [template["name"] for template in server.get_templates()]
    logging.debug(f"Available Templates: {available_templates}")

    lab.create_node(name='internet', template='Cloud', x=-120, y=-292)

    lab.create_node(name='router-1', template='Cisco IOSv 15.5(3)M', x=-454, y=-9)
    router1 = lab.get_node("router-1")
    router1.start()

    lab.create_node(name='router-2', template='Cisco IOSv 15.5(3)M', x=-218, y=-9)
    router2 = lab.get_node("router-2")
    router2.start()

    lab.create_node(name='router-3', template='Cisco IOSv 15.5(3)M', x=66, y=-9)
    router3 = lab.get_node("router-3")
    router3.start()

    lab.create_node(name='router-4', template='Cisco IOSv 15.5(3)M', x=334, y=-9)
    router4 = lab.get_node("router-4")
    router4.start()

    lab.create_node(name='router-5', template='Cisco IOSv 15.5(3)M', x=-78, y=-147, properties={"adapters": 16})
    router5 = lab.get_node("router-5")
    router5.start()

    lab.create_node(name='server-1', template='Windows Server 2022', x=-325, y=76)
    server1 = lab.get_node("server-1")
    server1.start()

    lab.create_node(name='server-2', template='Windows Server 2022', x=-89, y=76)
    server2 = lab.get_node("server-2")
    server2.start()

    lab.create_node(name='server-3', template='Windows Server 2022', x=189, y=76)
    server3 = lab.get_node("server-3")
    server3.start()

    lab.create_node(name='server-4', template='Windows Server 2022', x=449, y=76)
    server4 = lab.get_node("server-4")
    server4.start()

    lab.create_node(name='switch-1', template='Cisco IOSvL2 15.2.1', x=-452, y=214)
    sw1 = lab.get_node("switch-1")
    sw1.start()

    lab.create_node(name='switch-2', template='Cisco IOSvL2 15.2.1', x=-218, y=214)
    sw2 = lab.get_node("switch-2")
    sw2.start()

    lab.create_node(name='switch-3', template='Cisco IOSvL2 15.2.1', x=66, y=214)
    sw3 = lab.get_node("switch-3")
    sw3.start()

    lab.create_node(name='switch-4', template='Cisco IOSvL2 15.2.1', x=334, y=214)
    sw4 = lab.get_node("switch-4")
    sw4.start()

    lab.create_node(name='Linux-1', template='Kali Linux 2021.1', x=-452, y=325)
    linux1 = lab.get_node("Linux-1")
    linux1.start()

    lab.create_node(name='Linux-2', template='Kali Linux 2021.1', x=-218, y=325)
    linux2 = lab.get_node("Linux-2")
    linux2.start()

    lab.create_node(name='Linux-3', template='Kali Linux 2021.1', x=66, y=325)
    linux3 = lab.get_node("Linux-3")
    linux3.start()

    lab.create_node(name='Linux-4', template='Kali Linux 2021.1', x=334, y=325)
    linux4 = lab.get_node("Linux-4")
    linux4.start()



    lab.create_link("router-1", "Gi0/2", "router-5", "Gi0/0")
    lab.create_link("router-2", "Gi0/2", "router-5", "Gi0/1")
    lab.create_link("router-3", "Gi0/2", "router-5", "Gi0/2")
    lab.create_link("router-4", "Gi0/2", "router-5", "Gi0/3")
    lab.create_link("router-5", "Gi0/4", "internet", "eth0")

    lab.create_link("router-1", "Gi0/0", "switch-1", "Gi0/0")
    lab.create_link("router-2", "Gi0/0", "switch-2", "Gi0/0")
    lab.create_link("router-3", "Gi0/0", "switch-3", "Gi0/0")
    lab.create_link("router-4", "Gi0/0", "switch-4", "Gi0/0")

    lab.create_link("router-1", "Gi0/1", "server-1", "Ethernet0")
    lab.create_link("router-2", "Gi0/1", "server-2", "Ethernet0")
    lab.create_link("router-3", "Gi0/1", "server-3", "Ethernet0")
    lab.create_link("router-4", "Gi0/1", "server-4", "Ethernet0")

    lab.create_link("switch-1", "Gi0/1", "Linux-1", "eth0")
    lab.create_link("switch-2", "Gi0/1", "Linux-2", "eth0")
    lab.create_link("switch-3", "Gi0/1", "Linux-3", "eth0")
    lab.create_link("switch-4", "Gi0/1", "Linux-4", "eth0")

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
