himport logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "cit358-sp26"  # Or dynamically set if you want
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
   

    lab.create_node(name='Client-07', template='Cloud', x=84, y=-242, symbol=":/symbols/classic/computer.svg")

    lab.create_node(name='KaliLinux1', template='Kali Linux', x='-351', y='-346')
    kali1 = lab.get_node("KaliLinux1")
    kali1.start()

    lab.create_node(name='KaliLinux2', template='Kali Linux', x='-139', y='-346')
    kali2 = lab.get_node("KaliLinux2")
    kali2.start()

    lab.create_node(name='KaliLinux3', template='Kali Linux', x='73', y='-346')
    kali3 = lab.get_node("KaliLinux3")
    kali3.start()

    lab.create_node(name="Hub1", template='Ethernet hub', x=-143, y=-174, properties={"ports": 12})
    hub1 = lab.get_node("Hub1")
    hub1.start()
    
    lab.create_node(name='Client-00', template='Cisco IOSv 15.7(3)M3', x='-417', y='-211', symbol=":/symbols/classic/computer.svg")
    win10_1 = lab.get_node("Client-00")
    win10_1.start()

    lab.create_node(name='Client-01', template='Windows 10 w/ Edge', x='-384', y='-103', symbol=":/symbols/classic/computer.svg")
    win10_2 = lab.get_node("Client-01")
    win10_2.start()

    lab.create_node(name='Client-02', template='Windows 10 w/ Edge', x='-288', y='-25', symbol=":/symbols/classic/computer.svg")
    win10_3 = lab.get_node("Client-02")
    win10_3.start()

    lab.create_node(name='Client-03', template='ubuntu', x='-175', y='-8', symbol=":/symbols/classic/computer.svg")
    win10_4 = lab.get_node("Client-03")
    win10_4.start()

    lab.create_node(name='Client-04', template='ubuntu', x='-58', y='-6', symbol=":/symbols/classic/computer.svg")
    win10_5 = lab.get_node("Client-04")
    win10_5.start()

    lab.create_node(name='Client-05', template='Windows Server 2016', x='45', y='-53', symbol=":/symbols/classic/computer.svg")
    win10_6 = lab.get_node("Client-05")
    win10_6.start()

    lab.create_node(name="Client-06", node_type="docker", template="webgoat", x=150, y=-140, symbol=":/symbols/classic/computer.svg")
    client06 = lab.get_node("Client-06")
    client06.start()


    
   

    # Links
    lab.create_link("Hub1", "Ethernet0", "KaliLinux1", "Ethernet0")
    lab.create_link("Hub1", "Ethernet1", "KaliLinux2", "Ethernet0")
    lab.create_link("Hub1", "Ethernet2", "KaliLinux3", "Ethernet0")
    lab.create_link("Hub1", "Ethernet3", "Client-00", "Gi0/0")
    lab.create_link("Hub1", "Ethernet4", "Client-01", "NIC1")
    lab.create_link("Hub1", "Ethernet5", "Client-02", "NIC1")
    lab.create_link("Hub1", "Ethernet6", "Client-03", "eth0")
    lab.create_link("Hub1", "Ethernet7", "Client-04", "eth0")
    lab.create_link("Hub1", "Ethernet8", "Client-05", "NIC1")
    lab.create_link("Hub1", "Ethernet9", "Client-06", "eth0")
    lab.create_link("Hub1", "Ethernet10", "Client-07", "eth0")

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
