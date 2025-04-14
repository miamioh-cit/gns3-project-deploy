import logging
from gns3fy import Gns3Connector, Project

LAB_NAME = "386-test"
BASE_IP = "http://10.48.229."

# Read datastore IPs
try:
    with open("datastore", "r") as f:
        SERVER_LAST_OCTETS = [int(o.strip()) for o in f.read().strip().split(",") if o.strip().isdigit()]
except Exception as e:
    print("Error reading datastore file:", e)
    SERVER_LAST_OCTETS = []

if not SERVER_LAST_OCTETS:
    raise ValueError("No valid server last octets found in 'datastore'.")

SERVER_URLS = [f"{BASE_IP}{octet}:80" for octet in SERVER_LAST_OCTETS]
GNS3_USER = "cit358-m"
GNS3_PW = "cit358-m"

for SERVER_URL in SERVER_URLS:
    server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)
    print("Connecting to GNS3 server to verify uniqueness of Project name", server.get_version(), "at", SERVER_URL)

    try:
        lab = server.create_project(name=LAB_NAME)
    except:
        print("=========================================================")
        print("Error: May not be a unique Lab Name!")
        print("=========================================================")
        exit()

    print("-----------------------------------------------------------------------")
    print("Project name is unique, nodes are being created.")
    print("-----------------------------------------------------------------------")
    print("Please wait until script runs before entering the project in GNS3!")
    print("-----------------------------------------------------------------------")

    lab = Project(name=LAB_NAME, connector=server)
    lab.get()
    lab.open()

    # Create and start all nodes
    lab.create_node(name='switzerland-pc1', template='VPC', x='-257', y='-704').start()
    lab.create_node(name='switzerland-pc2', template='VPC', x='-257', y='-629').start()
    lab.create_node(name='router1', template='Cisco IOSv 15.5(3)M', x='298', y='300').start()
    lab.create_node(name='svr16', template='Windows Server 2016', x='299', y='300').start()
    lab.create_node(name='kali', template='Kali Linux 2021.1', x='250', y='200').start()
    lab.create_node(name='switch1', template='Cisco IOSvL2 15.2(20170321:233949)', x='200', y='200').start()

    # Ohio + Kentucky clients
    for i, name in enumerate([
        "ohio-01", "ohio-02", "ohio-win10-03", "ohio-win10-04",
        "ky-win10-01", "ky-win10-02", "ky-win10-03", "ky-win10-04"
    ]):
        lab.create_node(name=name, template='Windows 10 w/ Edge', x=300+i, y=200).start()

    # Links
    lab.create_link("svr16", "NIC1", "switch1", "Gi0/0")

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(f"{LAB_NAME} build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
