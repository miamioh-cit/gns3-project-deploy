import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "325-Rohaeb"

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

    lab.create_node(name='isp', template='Cloud', x='512', y='169')
    lab.create_node(name='NAT', template='NAT', x='496', y='-5')

    lab.create_node(name='mgmt', template='Cisco IOSv 15.5(3)M', x=-20, y=-337)
    router1 = lab.get_node("mgmt")
    router1.start()

    lab.create_node(name='mid-r', template='Cisco IOSv 15.5(3)M', x=-102, y=355)
    router2 = lab.get_node("mid-r")
    router2.start()

    lab.create_node(name='ham-r', template='Cisco IOSv 15.5(3)M', x=115, y=355)
    router3 = lab.get_node("ham-r")
    router3.start()

    lab.create_node(name='reg-traffic', template='Cisco IOSv 15.5(3)M', x=0, y=471)
    router4 = lab.get_node("reg-traffic")
    router4.start()

    lab.create_node(name='1', template='Cisco IOSvL2 15.2.1', x=-20, y=-205)
    switch1 = lab.get_node("1")
    switch1.start()

    lab.create_node(name='mid-sw', template='Cisco IOSvL2 15.2.1', x=-259, y=258)
    switch2 = lab.get_node("mid-sw")
    switch2.start()

    lab.create_node(name='ham-sw', template='Cisco IOSvL2 15.2.1', x=273, y=258)
    switch2 = lab.get_node("ham-sw")
    switch2.start()

    lab.create_node(name='oxford', template='ubuntu', x=-250, y=-85)
    oxford = lab.get_node("oxford")
    oxford.start()
   
    lab.create_node(name='mid-I', template='ubuntu', x=-250, y=0)
    mid_i = lab.get_node("mid-I")
    mid_i.start()

    lab.create_node(name='ham-I', template='ubuntu', x=250, y=0)
    ham1 = lab.get_node("ham-I")
    ham1.start()

    lab.create_node(name='mid-w', template='Windows 10', x=-141, y=63)
    midw = lab.get_node("mid-w")
    midw.start()

    lab.create_node(name='ham-w', template='Windows 10', x=136, y=57)
    hamw = lab.get_node("ham-w")
    hamw.start()



    lab.create_link("mgmt", "Gi0/0", "1", "Gi0/0")
    lab.create_link("reg-traffic", "Gi0/2", "isp", "eth0")
    lab.create_link("1", "Gi0/1", "oxford", "Ethernet0")
    lab.create_link("1", "Gi0/2", "mid-I", "Ethernet0")
    lab.create_link("1", "Gi0/3", "mid-w", "Ethernet0")
    lab.create_link("1", "Gi1/0", "mid-r", "Gi0/0")
    lab.create_link("1", "Gi1/1", "ham-r", "Gi0/0")
    lab.create_link("1", "Gi1/2", "ham-w", "Ethernet0")
    lab.create_link("1", "Gi1/3", "ham-I", "Ethernet0")
    
    lab.create_link("mid-sw", "Gi0/0", "mid-I", "Ethernet1")
    lab.create_link("mid-sw", "Gi0/1", "mid-w", "Ethernet1")
    lab.create_link("mid-sw", "Gi0/2", "mid-r", "Gi0/1")
    lab.create_link("reg-traffic", "Gi0/0", "ham-r", "Gi0/1")
    lab.create_link("reg-traffic", "Gi0/1", "mid-r", "Gi0/2")
    
    lab.create_link("ham-sw", "Gi0/0", "ham-I", "Ethernet1")
    lab.create_link("ham-sw", "Gi0/1", "ham-w", "Ethernet1")
    lab.create_link("ham-sw", "Gi0/2", "ham-r", "Gi0/2")
    lab.create_link("mgmt", "Gi0/1", "NAT", "nat0")

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
