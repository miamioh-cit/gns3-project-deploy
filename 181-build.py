import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "cit181-sp26"

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

    lab.create_node(name='s1-router', template='Cisco IOSv 15.7(3)M3', x=-454, y=-9)
    router1 = lab.get_node("s1-router")
    router1.start()

    lab.create_node(name='s2-router', template='Cisco IOSv 15.7(3)M3', x=-218, y=-9)
    router2 = lab.get_node("s2-router")
    router2.start()

    lab.create_node(name='s3-router', template='Cisco IOSv 15.7(3)M3', x=66, y=-9)
    router3 = lab.get_node("s3-router")
    router3.start()

    lab.create_node(name='s4-router', template='Cisco IOSv 15.7(3)M3', x=334, y=-9)
    router4 = lab.get_node("s4-router")
    router4.start()

    lab.create_node(name='core', template='Cisco IOSv 15.7(3)M3', x=-78, y=-147, properties={"adapters": 16})
    router5 = lab.get_node("core")
    router5.start()

    lab.create_node(name='s1-web', template='Windows Server 2022', x=-325, y=76)
    server1 = lab.get_node("s1-web")
    server1.start()

    lab.create_node(name='s2-web', template='Windows Server 2022', x=-89, y=76)
    server2 = lab.get_node("s2-web")
    server2.start()

    lab.create_node(name='s3-web', template='Windows Server 2022', x=189, y=76)
    server3 = lab.get_node("s3-web")
    server3.start()

    lab.create_node(name='s4-web', template='Windows Server 2022', x=449, y=76)
    server4 = lab.get_node("s4-web")
    server4.start()

    lab.create_node(name='s1-client', template='Windows 11', x=-354, y=200)
    server3 = lab.get_node("s1-client")
    server3.start()

    lab.create_node(name='s2-client', template='Windows 11', x=-118, y=200)
    server4 = lab.get_node("s2-client")
    server4.start()
    
    lab.create_node(name='s3-client', template='Windows 11', x=150, y=200)
    server5 = lab.get_node("s3-client")
    server5.start()

    lab.create_node(name='s4-client', template='Windows 11', x=410, y=200)
    server6 = lab.get_node("s4-client")
    server6.start()

    lab.create_node(name='s1-switch', template='Cisco IOSvL2 15.2.1', x=-452, y=214)
    sw1 = lab.get_node("s1-switch")
    sw1.start()

    lab.create_node(name='s2-switch', template='Cisco IOSvL2 15.2.1', x=-218, y=214)
    sw2 = lab.get_node("s2-switch")
    sw2.start()

    lab.create_node(name='s3-switch', template='Cisco IOSvL2 15.2.1', x=66, y=214)
    sw3 = lab.get_node("s3-switch")
    sw3.start()

    lab.create_node(name='s4-switch', template='Cisco IOSvL2 15.2.1', x=334, y=214)
    sw4 = lab.get_node("s4-switch")
    sw4.start()

    lab.create_node(name='s1-ubuntu', template='ubuntu', x=-452, y=325)
    linux1 = lab.get_node("s1-ubuntu")
    linux1.start()

    lab.create_node(name='s2-ubuntu', template='ubuntu', x=-218, y=325)
    linux2 = lab.get_node("s2-ubuntu")
    linux2.start()

    lab.create_node(name='s3-ubuntu', template='ubuntu', x=66, y=325)
    linux3 = lab.get_node("s3-ubuntu")
    linux3.start()

    lab.create_node(name='s4-ubuntu', template='ubuntu', x=334, y=325)
    linux4 = lab.get_node("s4-ubuntu")
    linux4.start()


    lab.create_link("s1-router", "Gi0/2", "core", "Gi0/0")
    lab.create_link("s2-router", "Gi0/2", "core", "Gi0/1")
    lab.create_link("s3-router", "Gi0/2", "core", "Gi0/2")
    lab.create_link("s4-router", "Gi0/2", "core", "Gi0/3")
    lab.create_link("core", "Gi0/4", "internet", "eth0")

    lab.create_link("s1-router", "Gi0/0", "s1-switch", "Gi0/0")
    lab.create_link("s2-router", "Gi0/0", "s2-switch", "Gi0/0")
    lab.create_link("s3-router", "Gi0/0", "s3-switch", "Gi0/0")
    lab.create_link("s4-router", "Gi0/0", "s4-switch", "Gi0/0")

    lab.create_link("s1-router", "Gi0/1", "s1-web", "Ethernet0")
    lab.create_link("s2-router", "Gi0/1", "s2-web", "Ethernet0")
    lab.create_link("s3-router", "Gi0/1", "s3-web", "Ethernet0")
    lab.create_link("s4-router", "Gi0/1", "s4-web", "Ethernet0")

    lab.create_link("s1-switch", "Gi0/1", "s1-ubuntu", "eth0")
    lab.create_link("s2-switch", "Gi0/1", "s2-ubuntu", "eth0")
    lab.create_link("s3-switch", "Gi0/1", "s3-ubuntu", "eth0")
    lab.create_link("s4-switch", "Gi0/1", "s4-ubuntu", "eth0")

    lab.create_link("s1-switch", "Gi0/2", "s1-client", "Ethernet0")
    lab.create_link("s2-switch", "Gi0/2", "s2-client", "Ethernet0")
    lab.create_link("s3-switch", "Gi0/2", "s3-client", "Ethernet0")
    lab.create_link("s4-switch", "Gi0/2", "s4-client", "Ethernet0")

    
    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
