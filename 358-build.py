import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "358-lab"  # Or dynamically set if you want
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

    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    # ---- Everything below here stays as-is from your original 358 build logic ---- #

    lab.create_node(name='router1', template='Cisco IOSv 15.5(3)M', x='298', y='300')
    lab.get_node("router1").start()

    lab.create_node(name='svr16', template='Windows Server 2022', x='299', y='300')
    lab.get_node("svr16").start()

    lab.create_node(name='kali', template='Kali Linux 2021.1', x='250', y='200')
    lab.get_node("kali").start()

    lab.create_node(name='switch1', template='Cisco IOSvL2 15.2.1', x='200', y='200')
    lab.get_node("switch1").start()

    lab.create_node(name='ohio-01', template='Windows 10 w/ Edge', x='301', y='200').start()
    lab.create_node(name='ohio-02', template='Windows 10 w/ Edge', x='302', y='200').start()
    lab.create_node(name='ohio-win10-03', template='Windows 10 w/ Edge', x='303', y='200').start()
    lab.create_node(name='ohio-win10-04', template='Windows 10 w/ Edge', x='304', y='200').start()
    lab.create_node(name='ky-win10-01', template='Windows 10 w/ Edge', x='304', y='200').start()
    lab.create_node(name='ky-win10-02', template='Windows 10 w/ Edge', x='306', y='200').start()
    lab.create_node(name='ky-win10-03', template='Windows 10 w/ Edge', x='307', y='200').start()
    lab.create_node(name='ky-win10-04', template='Windows 10 w/ Edge', x='308', y='200').start()

    # Links
    lab.create_link("svr16", "NIC1", "switch1", "Gi0/0")

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
