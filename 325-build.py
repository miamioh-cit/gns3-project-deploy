import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "325-test7-22"

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

    lab.create_node(name='NAT-1', template='NAT', x='200', y='474')
    lab.create_node(name='NAT-0', template='NAT', x='220', y='-320')

    lab.create_node(name='mgmt-rtr', template='Cisco IOSv 15.5(3)M', x=-20, y=-337)
    router1 = lab.get_node("mgmt-rtr")
    router1.start()

    lab.create_node(name='mid-rtr', template='Cisco IOSv 15.5(3)M', x=-102, y=355)
    router2 = lab.get_node("mid-rtr")
    router2.start()

    lab.create_node(name='ham-rtr', template='Cisco IOSv 15.5(3)M', x=115, y=355)
    router3 = lab.get_node("ham-rtr")
    router3.start()

    lab.create_node(name='reg-rtr', template='Cisco IOSv 15.5(3)M', x=0, y=471)
    router4 = lab.get_node("reg-rtr")
    router4.start()

    lab.create_node(name='mgmt-sw', template='Cisco IOSvL2 15.2.1', x=-20, y=-205)
    switch1 = lab.get_node("mgmt-sw")
    switch1.start()

    lab.create_node(name='mid-sw', template='Cisco IOSvL2 15.2.1', x=-259, y=258)
    switch2 = lab.get_node("mid-sw")
    switch2.start()

    lab.create_node(name='ham-sw', template='Cisco IOSvL2 15.2.1', x=273, y=258)
    switch2 = lab.get_node("ham-sw")
    switch2.start()

    lab.create_node(name='jenkins-server', template='ubuntu', x=-6, y=132)
    jenkinsServer = lab.get_node("jenkins-server")
    jenkinsServer.start()
    
    lab.create_node(name='oxf-l', template='ubuntu', x=-250, y=-85)
    oxford = lab.get_node("oxf-l")
    oxford.start()
   
    lab.create_node(name='mid-l', template='ubuntu', x=-250, y=0)
    mid_i = lab.get_node("mid-l")
    mid_i.start()

    lab.create_node(name='ham-l', template='ubuntu', x=250, y=0)
    ham1 = lab.get_node("ham-l")
    ham1.start()

    lab.create_node(name='mid-w', template='Windows 10', x=-141, y=63)
    midw = lab.get_node("mid-w")
    midw.start()

    lab.create_node(name='ham-w', template='Windows 10', x=136, y=57)
    hamw = lab.get_node("ham-w")
    hamw.start()



    lab.create_link("mgmt-rtr", "Gi0/0", "mgmt-sw", "Gi0/0")
    lab.create_link("reg-rtr", "Gi0/2", "NAT-1", "nat0")
    lab.create_link("mgmt-sw", "Gi0/1", "oxf-l", "Ethernet0")
    lab.create_link("mgmt-sw", "Gi0/2", "mid-l", "Ethernet0")
    lab.create_link("mgmt-sw", "Gi0/3", "mid-w", "Ethernet0")
    lab.create_link("mgmt-sw", "Gi1/0", "mid-rtr", "Gi0/0")
    lab.create_link("mgmt-sw", "Gi1/1", "ham-rtr", "Gi0/0")
    lab.create_link("mgmt-sw", "Gi1/2", "ham-w", "Ethernet0")
    lab.create_link("mgmt-sw", "Gi1/3", "ham-l", "Ethernet0")
    lab.create_link("mgmt-sw", "Gi2/0", "jenkins-server", "Ethernet0")
    
    lab.create_link("mid-sw", "Gi0/0", "mid-l", "Ethernet1")
    lab.create_link("mid-sw", "Gi0/1", "mid-w", "Ethernet1")
    lab.create_link("mid-sw", "Gi0/2", "mid-rtr", "Gi0/1")
    lab.create_link("reg-rtr", "Gi0/0", "ham-rtr", "Gi0/1")
    lab.create_link("reg-rtr", "Gi0/1", "mid-rtr", "Gi0/2")
    lab.create_link("reg-rtr", "Gi0/3", "jenkins-server", "Ethernet1")
    
    
    lab.create_link("ham-sw", "Gi0/0", "ham-l", "Ethernet1")
    lab.create_link("ham-sw", "Gi0/1", "ham-w", "Ethernet1")
    lab.create_link("ham-sw", "Gi0/2", "ham-rtr", "Gi0/2")
    lab.create_link("mgmt-rtr", "Gi0/1", "NAT-0", "nat0")

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
