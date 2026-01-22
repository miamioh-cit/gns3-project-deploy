import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "cit386-sp26"

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
    

    
    # Create and start all nodes
    lab.create_node(name='alpha-pc1', template='VPCS', x='-257', y='-704')
    VPC1 = lab.get_node("alpha-pc1")
    VPC1.start()
   
    lab.create_node(name='alpha-pc2', template='VPCS', x='-257', y='-629')
    VPC2 = lab.get_node("alpha-pc2")
    VPC2.start()

    lab.create_node(name='alpha-pc3', template='VPCS', x='42', y='-704')
    VPC5 = lab.get_node("alpha-pc3")
    VPC5.start()

    lab.create_node(name='alpha-pc4', template='VPCS', x='42', y='-629')
    VPC6 = lab.get_node("alpha-pc4")
    VPC6.start()
    
    lab.create_node(name='alpha-pc5', template='VPCS', x='-257', y='-554')
    VPC3 = lab.get_node("alpha-pc5")
    VPC3.start()
   
    lab.create_node(name='alpha-pc6', template='VPCS', x='-257', y='-479')
    VPC4 = lab.get_node("alpha-pc6")
    VPC4.start()

    lab.create_node(name='alpha-pc7', template='VPCS', x='42', y='-554')
    VPC7 = lab.get_node("alpha-pc7")
    VPC7.start()

    lab.create_node(name='alpha-pc8', template='VPCS', x='42', y='-479')
    VPC8 = lab.get_node("alpha-pc8")
    VPC8.start()

    lab.create_node(name='bravo-pc1', template='VPCS', x='417', y='-329')
    VPC38 = lab.get_node("bravo-pc1")
    VPC38.start()

    lab.create_node(name='bravo-pc2', template='VPCS', x='492', y='-329')
    VPC39 = lab.get_node("bravo-pc2")
    VPC39.start()
    
    lab.create_node(name='bravo-pc3', template='VPCS', x='417', y='-104')
    VPC42 = lab.get_node("bravo-pc3")
    VPC42.start()

    lab.create_node(name='bravo-pc4', template='VPCS', x='492', y='-104')
    VPC43 = lab.get_node("bravo-pc4")
    VPC43.start()

    lab.create_node(name='bravo-pc5', template='VPCS', x='642', y='-329')
    VPC40 = lab.get_node("bravo-pc5")
    VPC40.start()

    lab.create_node(name='bravo-pc6', template='VPCS', x='717', y='-329')
    VPC41 = lab.get_node("bravo-pc6")
    VPC41.start()

    lab.create_node(name='bravo-pc7', template='VPCS', x='642', y='-104')
    VPC44 = lab.get_node("bravo-pc7")
    VPC44.start()

    lab.create_node(name='bravo-pc8', template='VPCS', x='717', y='-104')
    VPC45 = lab.get_node("bravo-pc8")
    VPC45.start()
    
    lab.create_node(name='charlie-pc1', template='VPCS', x='417', y='45')
    VPC46 = lab.get_node("charlie-pc1")
    VPC46.start()

    lab.create_node(name='charlie-pc2', template='VPCS', x='492', y='45')
    VPC47 = lab.get_node("charlie-pc2")
    VPC47.start()

    lab.create_node(name='charlie-pc3', template='VPCS', x='417', y='270')
    VPC50 = lab.get_node("charlie-pc3")
    VPC50.start()

    lab.create_node(name='charlie-pc4', template='VPCS', x='492', y='270')
    VPC51 = lab.get_node("charlie-pc4")
    VPC51.start()
    
    lab.create_node(name='charlie-pc5', template='VPCS', x='642', y='45')
    VPC48 = lab.get_node("charlie-pc5")
    VPC48.start()

    lab.create_node(name='charlie-pc6', template='VPCS', x='717', y='45')
    VPC49 = lab.get_node("charlie-pc6")
    VPC49.start()

    lab.create_node(name='charlie-pc7', template='VPCS', x='642', y='270')
    VPC52 = lab.get_node("charlie-pc7")
    VPC52.start()

    lab.create_node(name='charlie-pc8', template='VPCS', x='717', y='270')
    VPC53 = lab.get_node("charlie-pc8")
    VPC53.start()

    lab.create_node(name='delta-pc1', template='VPCS', x='422', y='420')
    VPC55 = lab.get_node("delta-pc1")
    VPC55.start()

    lab.create_node(name='delta-pc2', template='VPCS', x='492', y='420')
    VPC56 = lab.get_node("delta-pc2")
    VPC56.start()

    lab.create_node(name='delta-pc3', template='VPCS', x='417', y='645')
    VPC59 = lab.get_node("delta-pc3")
    VPC59.start()

    lab.create_node(name='delta-pc4', template='VPCS', x='492', y='645')
    VPC60 = lab.get_node("delta-pc4")
    VPC60.start()
  
    lab.create_node(name='delta-pc5', template='VPCS', x='642', y='420')
    VPC57 = lab.get_node("delta-pc5")
    VPC57.start()

    lab.create_node(name='delta-pc6', template='VPCS', x='717', y='420')
    VPC58 = lab.get_node("delta-pc6")
    VPC58.start()
   
    lab.create_node(name='delta-pc7', template='VPCS', x='639', y='645')
    VPC61 = lab.get_node("delta-pc7")
    VPC61.start()

    lab.create_node(name='delta-pc8', template='VPCS', x='716', y='645')
    VPC62 = lab.get_node("delta-pc8")
    VPC62.start()
    
    lab.create_node(name='echo-pc1', template='VPCS', x='-932', y='420')
    VPC28 = lab.get_node("echo-pc1")
    VPC28.start()

    lab.create_node(name='echo-pc2', template='VPCS', x='-857', y='420')
    VPC29 = lab.get_node("echo-pc2")
    VPC29.start()
  
    lab.create_node(name='echo-pc3', template='VPCS', x='-932', y='645')
    VPC32 = lab.get_node("echo-pc3")
    VPC32.start()

    lab.create_node(name='echo-pc4', template='VPCS', x='-857', y='645')
    VPC33 = lab.get_node("echo-pc4")
    VPC33.start()

    lab.create_node(name='echo-pc5', template='VPCS', x='-707', y='420')
    VPC30 = lab.get_node("echo-pc5")
    VPC30.start()

    lab.create_node(name='echo-pc6', template='VPCS', x='-632', y='420')
    VPC31 = lab.get_node("echo-pc6")
    VPC31.start()

    lab.create_node(name='echo-pc7', template='VPCS', x='-707', y='645')
    VPC34 = lab.get_node("echo-pc7")
    VPC34.start()

    lab.create_node(name='echo-pc8', template='VPCS', x='-632', y='645')
    VPC35 = lab.get_node("echo-pc8")
    VPC35.start()

    lab.create_node(name='foxtrot-pc1', template='VPCS', x='-932', y='45')
    VPC20 = lab.get_node("foxtrot-pc1")
    VPC20.start()

    lab.create_node(name='foxtrot-pc2', template='VPCS', x='-857', y='45')
    VPC21 = lab.get_node("foxtrot-pc2")
    VPC21.start()
    
    lab.create_node(name='foxtrot-pc3', template='VPCS', x='-932', y='270')
    VPC24 = lab.get_node("foxtrot-pc3")
    VPC24.start()

    lab.create_node(name='foxtrot-pc4', template='VPCS', x='-857', y='270')
    VPC25 = lab.get_node("foxtrot-pc4")
    VPC25.start()
 
    lab.create_node(name='foxtrot-pc5', template='VPCS', x='-707', y='45')
    VPC22 = lab.get_node("foxtrot-pc5")
    VPC22.start()

    lab.create_node(name='foxtrot-pc6', template='VPCS', x='-632', y='45')
    VPC23 = lab.get_node("foxtrot-pc6")
    VPC23.start()

    lab.create_node(name='foxtrot-pc7', template='VPCS', x='-707', y='270')
    VPC26 = lab.get_node("foxtrot-pc7")
    VPC26.start()

    lab.create_node(name='foxtrot-pc8', template='VPCS', x='-632', y='270')
    VPC27 = lab.get_node("foxtrot-pc8")
    VPC27.start()

    lab.create_node(name='golf-pc1', template='VPCS', x='-932', y='-329')
    VPC10 = lab.get_node("golf-pc1")
    VPC10.start()

    lab.create_node(name='golf-pc2', template='VPCS', x='-857', y='-329')
    VPC11 = lab.get_node("golf-pc2")
    VPC11.start()

    lab.create_node(name='golf-pc3', template='VPCS', x='-932', y='-104')
    VPC15 = lab.get_node("golf-pc3")
    VPC15.start()

    lab.create_node(name='golf-pc4', template='VPCS', x='-857', y='-104')
    VPC16 = lab.get_node("golf-pc4")
    VPC16.start()

    lab.create_node(name='golf-pc5', template='VPCS', x='-707', y='-329')
    VPC12 = lab.get_node("golf-pc5")
    VPC12.start()

    lab.create_node(name='golf-pc6', template='VPCS', x='-632', y='-331')
    VPC13 = lab.get_node("golf-pc6")
    VPC13.start()

    lab.create_node(name='golf-pc7', template='VPCS', x='-707', y='-104')
    VPC17 = lab.get_node("golf-pc7")
    VPC17.start()

    lab.create_node(name='golf-pc8', template='VPCS', x='-632', y='-104')
    VPC18 = lab.get_node("golf-pc8")
    VPC18.start()

#Add routers
    lab.create_node(name='alpha-int', template='Cisco IOSv 15.7(3)M3', x='-108', y='-322')
    router0 = lab.get_node("alpha-int")
    router0.start()

    lab.create_node(name='alpha-edge', template='Cisco IOSv 15.7(3)M3', x='-107', y='-100', properties={"adapters": 16})
    router1 = lab.get_node("alpha-edge")
    router1.start()

    lab.create_node(name='bravo-int', template='Cisco IOSv 15.7(3)M3', x='340', y='-203')
    router4 = lab.get_node("bravo-int")
    router4.start()

    lab.create_node(name='bravo-edge', template='Cisco IOSv 15.7(3)M3', x='39', y='-21', properties={"adapters": 16})
    router5 = lab.get_node("bravo-edge")
    router5.start()

    lab.create_node(name='charlie-int', template='Cisco IOSv 15.7(3)M3', x='342', y='203')
    router6 = lab.get_node("charlie-int")
    router6.start() 

    lab.create_node(name='charlie-edge', template='Cisco IOSv 15.7(3)M3', x='42', y='203', properties={"adapters": 16})
    router7 = lab.get_node("charlie-edge")
    router7.start()

    lab.create_node(name='delta-int', template='Cisco IOSv 15.7(3)M3', x='343', y='540')
    router8 = lab.get_node("delta-int")
    router8.start()

    lab.create_node(name='delta-edge', template='Cisco IOSv 15.7(3)M3', x='42', y='428', properties={"adapters": 16})
    router9 = lab.get_node("delta-edge")
    router9.start()

    lab.create_node(name='echo-int', template='Cisco IOSv 15.7(3)M3', x='-558', y='540')
    router12 = lab.get_node("echo-int")
    router12.start()

    lab.create_node(name='echo-edge', template='Cisco IOSv 15.7(3)M3', x='-258', y='428', properties={"adapters": 16})
    router13 = lab.get_node("echo-edge")
    router13.start()
    
    lab.create_node(name='foxtrot-int', template='Cisco IOSv 15.7(3)M3', x='-558', y='203')
    router10 = lab.get_node("foxtrot-int")
    router10.start()

    lab.create_node(name='foxtrot-edge', template='Cisco IOSv 15.7(3)M3', x='-258', y='201', properties={"adapters": 16})
    router11 = lab.get_node("foxtrot-edge")
    router11.start()
    
    lab.create_node(name='golf-int', template='Cisco IOSv 15.7(3)M3', x='-555', y='-203')
    router2 = lab.get_node("golf-int")
    router2.start()

    lab.create_node(name='golf-edge', template='Cisco IOSv 15.7(3)M3', x='-255', y='-20', properties={"adapters": 16})
    router3 = lab.get_node("golf-edge")
    router3.start()


#Add Switches
    lab.create_node(name='alpha-sw1', template='Cisco IOSvL2 15.2.1', x='-100', y='-473')
    sw0 = lab.get_node("alpha-sw1")
    sw0.start()

    lab.create_node(name='alpha-sw2', template='Cisco IOSvL2 15.2.1', x='-100', y='-623')
    sw1 = lab.get_node("alpha-sw2")
    sw1.start()

    lab.create_node(name='bravo-sw1', template='Cisco IOSvL2 15.2.1', x='502', y='-203')
    sw4 = lab.get_node("bravo-sw1")
    sw4.start()

    lab.create_node(name='bravo-sw2', template='Cisco IOSvL2 15.2.1', x='656', y='-203')
    sw5 = lab.get_node("bravo-sw2")
    sw5.start()

    lab.create_node(name='charlie-sw1', template='Cisco IOSvL2 15.2.1', x='500', y='164')
    sw6 = lab.get_node("charlie-sw1")
    sw6.start()

    lab.create_node(name='charlie-sw2', template='Cisco IOSvL2 15.2.1', x='653', y='164')
    sw7 = lab.get_node("charlie-sw2")
    sw7.start()

    lab.create_node(name='delta-sw1', template='Cisco IOSvL2 15.2.1', x='498', y='536')
    sw8 = lab.get_node("delta-sw1")
    sw8.start()

    lab.create_node(name='delta-sw2', template='Cisco IOSvL2 15.2.1', x='651', y='536')
    sw9 = lab.get_node("delta-sw2")
    sw9.start()
    
    lab.create_node(name='echo-sw1', template='Cisco IOSvL2 15.2.1', x='-700', y='534')
    sw12 = lab.get_node("echo-sw1")
    sw12.start()

    lab.create_node(name='echo-sw2', template='Cisco IOSvL2 15.2.1', x='-850', y='534')
    sw13 = lab.get_node("echo-sw2")
    sw13.start()
    
    lab.create_node(name='foxtrot-sw1', template='Cisco IOSvL2 15.2.1', x='-700', y='167')
    sw10 = lab.get_node("foxtrot-sw1")
    sw10.start()

    lab.create_node(name='foxtrot-sw2', template='Cisco IOSvL2 15.2.1', x='-853', y='167')
    sw11 = lab.get_node("foxtrot-sw2")
    sw11.start()

    lab.create_node(name='golf-sw1', template='Cisco IOSvL2 15.2.1', x='-701', y='-203')
    sw2 = lab.get_node("golf-sw1")
    sw2.start()

    lab.create_node(name='golf-sw2', template='Cisco IOSvL2 15.2.1', x='-850', y='-203')
    sw3 = lab.get_node("golf-sw2")
    sw3.start()


#Add ASAs
    lab.create_node(name='alpha-asa', template='Cisco ASAv 9.9.2', x='-101', y='-225')
    ASA0 = lab.get_node("alpha-asa")
    ASA0.start()

    lab.create_node(name='bravo-asa', template='Cisco ASAv 9.9.2', x='193', y='-118')
    ASA2 = lab.get_node("bravo-asa")
    ASA2.start()

    lab.create_node(name='charlie-asa', template='Cisco ASAv 9.9.2', x='199', y='194')
    ASA3 = lab.get_node("charlie-asa")
    ASA3.start()

    lab.create_node(name='delta-asa', template='Cisco ASAv 9.9.2', x='198', y='463')
    ASA4 = lab.get_node("delta-asa")
    ASA4.start()

    lab.create_node(name='echo-asa', template='Cisco ASAv 9.9.2', x='-400', y='493')
    ASA6 = lab.get_node("echo-asa")
    ASA6.start()
    
    lab.create_node(name='foxtrot-asa', template='Cisco ASAv 9.9.2', x='-398', y='198')
    ASA5 = lab.get_node("foxtrot-asa")
    ASA5.start()

    lab.create_node(name='golf-asa', template='Cisco ASAv 9.9.2', x='-403', y='-112')
    ASA1 = lab.get_node("golf-asa")
    ASA1.start()

#Add WebServers    
    lab.create_node(name='alpha-web', template='ubuntu', x='35', y='-225')
    VPC9 = lab.get_node("alpha-web")
    VPC9.start()

    lab.create_node(name='bravo-web', template='ubuntu', x='305', y='-328')
    VPC37 = lab.get_node("bravo-web")
    VPC37.start()
    
    lab.create_node(name='charlie-web', template='ubuntu', x='192', y='45')
    VPC54 = lab.get_node("charlie-web")
    VPC54.start()

    lab.create_node(name='delta-web', template='ubuntu', x='192', y='645')
    VPC63 = lab.get_node("delta-web")
    VPC63.start()
    
    lab.create_node(name='echo-web', template='ubuntu', x='-407', y='645')
    VPC36 = lab.get_node("echo-web")
    VPC36.start()
    
    lab.create_node(name='foxtrot-web', template='ubuntu', x='-407', y='45')
    VPC19 = lab.get_node("foxtrot-web")
    VPC19.start()

    lab.create_node(name='golf-web', template='ubuntu', x='-515', y='-331')
    VPC14 = lab.get_node("golf-web")
    VPC14.start()

    
#Team Alpha links 
    lab.create_link("alpha-sw2", "Gi0/1", "alpha-pc1", "Ethernet0")
    lab.create_link("alpha-sw2", "Gi1/2", "alpha-pc2", "Ethernet0")
    lab.create_link("alpha-sw2", "Gi1/0", "alpha-pc3", "Ethernet0")
    lab.create_link("alpha-sw2", "Gi1/1", "alpha-pc4", "Ethernet0")
    lab.create_link("alpha-sw1", "Gi0/3", "alpha-sw2", "Gi0/3")
    lab.create_link("alpha-sw1", "Gi1/2", "alpha-pc5", "Ethernet0")
    lab.create_link("alpha-sw1", "Gi0/0", "alpha-pc6", "Ethernet0")
    lab.create_link("alpha-sw1", "Gi1/1", "alpha-pc7", "Ethernet0")
    lab.create_link("alpha-sw1", "Gi1/0", "alpha-pc8", "Ethernet0")
    lab.create_link("alpha-sw1", "Gi0/2", "alpha-int", "Gi0/2")
    lab.create_link("alpha-int", "Gi0/1", "alpha-asa", "Gi0/1")
    lab.create_link("alpha-web", "eth0", "alpha-asa", "Gi0/2")
    lab.create_link("alpha-edge", "Gi0/0", "alpha-asa", "Gi0/0")
    
#Team Bravo Links
    lab.create_link("bravo-sw2", "Gi1/0", "bravo-pc8", "Ethernet0")
    lab.create_link("bravo-sw2", "Gi0/0", "bravo-pc7", "Ethernet0")
    lab.create_link("bravo-sw2", "Gi1/1", "bravo-pc6", "Ethernet0")
    lab.create_link("bravo-sw2", "Gi1/2", "bravo-pc5", "Ethernet0")
    lab.create_link("bravo-sw2", "Gi0/3", "bravo-sw1", "Gi0/3")
    lab.create_link("bravo-sw1", "Gi0/1", "bravo-pc4", "Ethernet0")
    lab.create_link("bravo-sw1", "Gi0/0", "bravo-pc3", "Ethernet0")
    lab.create_link("bravo-sw1", "Gi1/0", "bravo-pc2", "Ethernet0")
    lab.create_link("bravo-sw1", "Gi1/1", "bravo-pc1", "Ethernet0")
    lab.create_link("bravo-sw1", "Gi0/2", "bravo-int", "Gi0/2")
    lab.create_link("bravo-int", "Gi0/1", "bravo-asa", "Gi0/1")
    lab.create_link("bravo-web", "eth0", "bravo-asa", "Gi0/2")
    lab.create_link("bravo-edge", "Gi0/0", "bravo-asa", "Gi0/0")

#Charlie Team Links 
    lab.create_link("charlie-sw2", "Gi1/1", "charlie-pc8", "Ethernet0")
    lab.create_link("charlie-sw2", "Gi1/0", "charlie-pc7", "Ethernet0")
    lab.create_link("charlie-sw2", "Gi1/2", "charlie-pc6", "Ethernet0")
    lab.create_link("charlie-sw2", "Gi0/1", "charlie-pc5", "Ethernet0")
    lab.create_link("charlie-sw2", "Gi0/3", "charlie-sw1", "Gi0/3")
    lab.create_link("charlie-sw1", "Gi1/1", "charlie-pc4", "Ethernet0")
    lab.create_link("charlie-sw1", "Gi1/0", "charlie-pc3", "Ethernet0")
    lab.create_link("charlie-sw1", "Gi1/2", "charlie-pc2", "Ethernet0")
    lab.create_link("charlie-sw1", "Gi0/1", "charlie-pc1", "Ethernet0")
    lab.create_link("charlie-sw1", "Gi0/2", "charlie-int", "Gi0/2")
    lab.create_link("charlie-int", "Gi0/1", "charlie-asa", "Gi0/1")
    lab.create_link("charlie-web", "eth0", "charlie-asa", "Gi0/2")
    lab.create_link("charlie-edge", "Gi0/0", "charlie-asa", "Gi0/0")

#Delta Force Links 
    lab.create_link("delta-sw2", "Gi1/1", "delta-pc8", "Ethernet0")
    lab.create_link("delta-sw2", "Gi1/0", "delta-pc7", "Ethernet0")
    lab.create_link("delta-sw2", "Gi1/2", "delta-pc6", "Ethernet0")
    lab.create_link("delta-sw2", "Gi0/1", "delta-pc5", "Ethernet0")
    lab.create_link("delta-sw2", "Gi0/3", "delta-sw1", "Gi0/3")
    lab.create_link("delta-sw1", "Gi1/2", "delta-pc4", "Ethernet0")
    lab.create_link("delta-sw1", "Gi1/0", "delta-pc3", "Ethernet0")
    lab.create_link("delta-sw1", "Gi0/1", "delta-pc2", "Ethernet0")
    lab.create_link("delta-sw1", "Gi0/0", "delta-pc1", "Ethernet0")
    lab.create_link("delta-sw1", "Gi0/2", "delta-int", "Gi0/2")
    lab.create_link("delta-int", "Gi0/1", "delta-asa", "Gi0/1")
    lab.create_link("delta-web", "eth0", "delta-asa", "Gi0/2")
    lab.create_link("delta-edge", "Gi0/0", "delta-asa", "Gi0/0")

#Echo Team Links
    lab.create_link("echo-sw2", "Gi1/2", "echo-pc1", "Ethernet0")
    lab.create_link("echo-sw2", "Gi1/0", "echo-pc2", "Ethernet0")
    lab.create_link("echo-sw2", "Gi0/2", "echo-pc3", "Ethernet0")
    lab.create_link("echo-sw2", "Gi1/1", "echo-pc4", "Ethernet0")
    lab.create_link("echo-sw2", "Gi0/3", "echo-sw1", "Gi0/3")
    lab.create_link("echo-sw1", "Gi0/0", "echo-pc5", "Ethernet0")
    lab.create_link("echo-sw1", "Gi1/0", "echo-pc6", "Ethernet0")
    lab.create_link("echo-sw1", "Gi0/1", "echo-pc7", "Ethernet0")
    lab.create_link("echo-sw1", "Gi1/1", "echo-pc8", "Ethernet0")
    lab.create_link("echo-sw1", "Gi0/2", "echo-int", "Gi0/2")
    lab.create_link("echo-int", "Gi0/1", "echo-asa", "Gi0/1")
    lab.create_link("echo-web", "eth0", "echo-asa", "Gi0/2")
    lab.create_link("echo-edge", "Gi0/0", "echo-asa", "Gi0/0")

#Team Foxtrot Links 
    lab.create_link("foxtrot-sw2", "Gi0/0", "foxtrot-pc1", "Ethernet0")
    lab.create_link("foxtrot-sw2", "Gi1/0", "foxtrot-pc2", "Ethernet0")
    lab.create_link("foxtrot-sw2", "Gi0/1", "foxtrot-pc3", "Ethernet0")
    lab.create_link("foxtrot-sw2", "Gi1/1", "foxtrot-pc4", "Ethernet0")
    lab.create_link("foxtrot-sw2", "Gi0/3", "foxtrot-sw1", "Gi0/3")
    lab.create_link("foxtrot-sw1", "Gi0/0", "foxtrot-pc5", "Ethernet0")
    lab.create_link("foxtrot-sw1", "Gi1/0", "foxtrot-pc6", "Ethernet0")
    lab.create_link("foxtrot-sw1", "Gi0/1", "foxtrot-pc7", "Ethernet0")
    lab.create_link("foxtrot-sw1", "Gi1/1", "foxtrot-pc8", "Ethernet0")
    lab.create_link("foxtrot-sw1", "Gi0/2", "foxtrot-int", "Gi0/2")
    lab.create_link("foxtrot-int", "Gi0/1", "foxtrot-asa", "Gi0/1")
    lab.create_link("foxtrot-web", "eth0", "foxtrot-asa", "Gi0/2")   
    lab.create_link("foxtrot-edge", "Gi0/0", "foxtrot-asa", "Gi0/0")
    
#Team Golf Links
    lab.create_link("golf-sw2", "Gi0/3", "golf-pc1", "Ethernet0")
    lab.create_link("golf-sw2", "Gi0/1", "golf-pc2", "Ethernet0")
    lab.create_link("golf-sw2", "Gi1/0", "golf-pc3", "Ethernet0")
    lab.create_link("golf-sw2", "Gi0/0", "golf-pc4", "Ethernet0")
    lab.create_link("golf-sw1", "Gi0/2", "golf-sw2", "Gi0/2")
    lab.create_link("golf-sw1", "Gi0/0", "golf-pc5", "Ethernet0")
    lab.create_link("golf-sw1", "Gi1/0", "golf-pc6", "Ethernet0")
    lab.create_link("golf-sw1", "Gi1/1", "golf-pc7", "Ethernet0")
    lab.create_link("golf-sw1", "Gi0/3", "golf-pc8", "Ethernet0")
    lab.create_link("golf-sw1", "Gi0/1", "golf-int", "Gi0/2")
    lab.create_link("golf-int", "Gi0/1", "golf-asa", "Gi0/1")
    lab.create_link("golf-web", "eth0", "golf-asa", "Gi0/2")
    lab.create_link("golf-edge", "Gi0/0", "golf-asa", "Gi0/0")


#Edge Router Links
    lab.create_link("alpha-edge", "Gi0/1", "golf-edge", "Gi0/1")
    lab.create_link("alpha-edge", "Gi0/2", "bravo-edge", "Gi0/2")
    lab.create_link("alpha-edge", "Gi0/3", "foxtrot-edge", "Gi0/4")
    lab.create_link("alpha-edge", "Gi0/4", "charlie-edge", "Gi0/5")
    lab.create_link("alpha-edge", "Gi0/5", "echo-edge", "Gi0/5")
    lab.create_link("alpha-edge", "Gi0/6", "delta-edge", "Gi0/6")
    lab.create_link("golf-edge", "Gi0/2", "foxtrot-edge", "Gi0/2")
    lab.create_link("foxtrot-edge", "Gi0/3", "echo-edge", "Gi0/3")
    lab.create_link("bravo-edge", "Gi0/3", "charlie-edge", "Gi0/3")
    lab.create_link("charlie-edge", "Gi0/4", "delta-edge", "Gi0/4")
    lab.create_link("delto-edge", "Gi0/5", "echo-edge", "Gi0/4")

    #alpha-switzerland
    #bravo-japan
    #charlie-china
    #delta-germany
    #echo-america/us
    #foxtrot-europe
    #golf-india
  
    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(f"{LAB_NAME} build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
