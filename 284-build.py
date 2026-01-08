import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "cit284-sp26"

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

    #create and start all nodes
    lab.create_node(name='ADDC-1', template='Windows Server 2022', x=-315, y=-48)
    ADDC1 = lab.get_node("ADDC-1")
    ADDC1.start()

    lab.create_node(name='Windows10w/Edge-1', template='Windows 10 w/ Edge', x=-401, y=58)
    win10Edge1 = lab.get_node("Windows10w/Edge-1")
    win10Edge1.start()

    lab.create_node(name='Windows10w/Edge-0', template='Windows 10 w/ Edge', x=-559, y=58)
    win10Edge2 = lab.get_node("Windows10w/Edge-0")
    win10Edge2.start()

    lab.create_node(name='Switch1', template='Ethernet switch', x=-472, y=-30)
    switch1 = lab.get_node("Switch1")
    switch1.start()

    lab.create_node(name='NAT1', template='NAT', x=-512, y=-310)
    nat1 = lab.get_node("NAT1")
    nat1.start()

    #Create links
    
    
    
    lab.create_link("Switch1", "Ethernet0", "ADDC-1", "Ethernet0")
    lab.create_link("Switch1", "Ethernet1", "Windows10w/Edge-0", "NIC1")
    lab.create_link("Switch1", "Ethernet2", "Windows10w/Edge-1", "NIC1")
    lab.create_link("Switch1", "Ethernet3", "NAT1", "nat0")

    note_payload = {
        "type": "note",
        "x": 200,
        "y": 250,
        "text": "Configure default gateway here",
        "font_size": 12,
        "color": "#000000",
        "background_color": "#E0E0E0",
        "locked": False}

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
