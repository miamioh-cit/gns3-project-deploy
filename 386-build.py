import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "386-test"

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
    lab.create_node(name='switzerland-pc1', template='VPCS', x='-257', y='-704')
    VPC1 = lab.get_node("switzerland-pc1")
    VPC1.start()
   
    lab.create_node(name='switzerland-pc2', template='VPCS', x='-257', y='-629')
    VPC2 = lab.get_node("switzerland-pc2")
    VPC2.start()
   
    lab.create_node(name='switzerland-pc5', template='VPCS', x='-257', y='-554')
    VPC3 = lab.get_node("switzerland-pc5")
    VPC3.start()
   
    lab.create_node(name='switzerland-pc6', template='VPCS', x='-257', y='-479')
    VPC4 = lab.get_node("switzerland-pc6")
    VPC4.start()

    lab.create_node(name='switzerland-pc3', template='VPCS', x='42', y='-704')
    VPC5 = lab.get_node("switzerland-pc3")
    VPC5.start()

    lab.create_node(name='switzerland-pc4', template='VPCS', x='42', y='-629')
    VPC6 = lab.get_node("switzerland-pc4")
    VPC6.start()

    lab.create_node(name='switzerland-pc7', template='VPCS', x='42', y='-554')
    VPC7 = lab.get_node("switzerland-pc7")
    VPC7.start()

    lab.create_node(name='switzerland-pc8', template='VPCS', x='42', y='-479')
    VPC8 = lab.get_node("switzerland-pc8")
    VPC8.start()

    lab.create_node(name='switzerland-web', template='VPCS', x='35', y='-225')
    VPC9 = lab.get_node("switzerland-web")
    VPC9.start()

    lab.create_node(name='india-pc1', template='VPCS', x='-932', y='-329')
    VPC10 = lab.get_node("india-pc1")
    VPC10.start()

    lab.create_node(name='india-pc2', template='VPCS', x='-857', y='-329')
    VPC11 = lab.get_node("india-pc2")
    VPC11.start()

    lab.create_node(name='india-pc5', template='VPCS', x='-707', y='-329')
    VPC12 = lab.get_node("india-pc5")
    VPC12.start()

    lab.create_node(name='india-pc6', template='VPCS', x='-632', y='-331')
    VPC13 = lab.get_node("india-pc6")
    VPC13.start()

    lab.create_node(name='india-web', template='VPCS', x='-561', y='-331')
    VPC14 = lab.get_node("india-web")
    VPC14.start()

    lab.create_node(name='india-pc3', template='VPCS', x='-932', y='-104')
    VPC15 = lab.get_node("india-pc3")
    VPC15.start()

    lab.create_node(name='india-pc4', template='VPCS', x='-857', y='-104')
    VPC16 = lab.get_node("india-pc4")
    VPC16.start()

    lab.create_node(name='india-pc7', template='VPCS', x='-707', y='-104')
    VPC17 = lab.get_node("india-pc7")
    VPC17.start()

    lab.create_node(name='india-pc8', template='VPCS', x='-632', y='-104')
    VPC18 = lab.get_node("india-pc8")
    VPC18.start()
 

    lab.create_node(name='europe-web', template='VPCS', x='-407', y='45')
    VPC19 = lab.get_node("europe-web")
    VPC19.start()

    lab.create_node(name='europe-pc1', template='VPCS', x='-932', y='45')
    VPC20 = lab.get_node("europe-pc1")
    VPC20.start()

    lab.create_node(name='europe-pc2', template='VPCS', x='-857', y='45')
    VPC21 = lab.get_node("europe-pc2")
    VPC21.start()
   
    lab.create_node(name='europe-pc5', template='VPCS', x='-707', y='45')
    VPC22 = lab.get_node("europe-pc5")
    VPC22.start()

    lab.create_node(name='europe-pc6', template='VPCS', x='-632', y='45')
    VPC23 = lab.get_node("europe-pc6")
    VPC23.start()

    lab.create_node(name='europe-pc3', template='VPCS', x='-932', y='270')
    VPC24 = lab.get_node("europe-pc3")
    VPC24.start()

    lab.create_node(name='europe-pc4', template='VPCS', x='-857', y='270')
    VPC25 = lab.get_node("europe-pc4")
    VPC25.start()

    lab.create_node(name='europe-pc7', template='VPCS', x='-707', y='270')
    VPC26 = lab.get_node("europe-pc7")
    VPC26.start()

    lab.create_node(name='europe-pc8', template='VPCS', x='-632', y='270')
    VPC27 = lab.get_node("europe-pc8")
    VPC27.start()

    lab.create_node(name='america-pc1', template='VPCS', x='-932', y='420')
    VPC28 = lab.get_node("america-pc1")
    VPC28.start()

    lab.create_node(name='america-pc2', template='VPCS', x='-857', y='420')
    VPC29 = lab.get_node("america-pc2")
    VPC29.start()

    lab.create_node(name='america-pc5', template='VPCS', x='-707', y='420')
    VPC30 = lab.get_node("america-pc5")
    VPC30.start()

    lab.create_node(name='america-pc6', template='VPCS', x='-632', y='420')
    VPC31 = lab.get_node("america-pc6")
    VPC31.start()

    lab.create_node(name='america-pc3', template='VPCS', x='-932', y='645')
    VPC32 = lab.get_node("america-pc3")
    VPC32.start()

    lab.create_node(name='america-pc4', template='VPCS', x='-857', y='645')
    VPC33 = lab.get_node("america-pc4")
    VPC33.start()

    lab.create_node(name='america-pc7', template='VPCS', x='-707', y='645')
    VPC34 = lab.get_node("america-pc7")
    VPC34.start()

    lab.create_node(name='america-pc8', template='VPCS', x='-632', y='645')
    VPC35 = lab.get_node("america-pc8")
    VPC35.start()

    lab.create_node(name='america-web', template='VPCS', x='-407', y='645')
    VPC36 = lab.get_node("america-web")
    VPC36.start()

    lab.create_node(name='japan-web', template='VPCS', x='339', y='-328')
    VPC37 = lab.get_node("japan-web")
    VPC37.start()

    lab.create_node(name='japan-pc1', template='VPCS', x='417', y='-329')
    VPC38 = lab.get_node("japan-pc1")
    VPC38.start()

    lab.create_node(name='japan-pc2', template='VPCS', x='492', y='-329')
    VPC39 = lab.get_node("japan-pc2")
    VPC39.start()

    lab.create_node(name='japan-pc5', template='VPCS', x='642', y='-329')
    VPC40 = lab.get_node("japan-pc5")
    VPC40.start()

    lab.create_node(name='japan-pc6', template='VPCS', x='717', y='-329')
    VPC41 = lab.get_node("japan-pc6")
    VPC41.start()

    lab.create_node(name='japan-pc3', template='VPCS', x='417', y='-104')
    VPC42 = lab.get_node("japan-pc3")
    VPC42.start()

    lab.create_node(name='japan-pc4', template='VPCS', x='492', y='-104')
    VPC43 = lab.get_node("japan-pc4")
    VPC43.start()

    lab.create_node(name='japan-pc7', template='VPCS', x='642', y='-104')
    VPC44 = lab.get_node("japan-pc7")
    VPC44.start()

    lab.create_node(name='japan-pc8', template='VPCS', x='717', y='-104')
    VPC45 = lab.get_node("japan-pc8")
    VPC45.start()
    
    lab.create_node(name='china-pc1', template='VPCS', x='417', y='45')
    VPC46 = lab.get_node("china-pc1")
    VPC46.start()

    lab.create_node(name='china-pc2', template='VPCS', x='492', y='45')
    VPC47 = lab.get_node("china-pc2")
    VPC47.start()

    lab.create_node(name='china-pc5', template='VPCS', x='642', y='45')
    VPC48 = lab.get_node("china-pc5")
    VPC48.start()

    lab.create_node(name='china-pc6', template='VPCS', x='717', y='45')
    VPC49 = lab.get_node("china-pc6")
    VPC49.start()

    lab.create_node(name='china-pc3', template='VPCS', x='417', y='270')
    VPC50 = lab.get_node("china-pc3")
    VPC50.start()

    lab.create_node(name='china-pc4', template='VPCS', x='492', y='270')
    VPC51 = lab.get_node("china-pc4")
    VPC51.start()

    lab.create_node(name='china-pc7', template='VPCS', x='642', y='270')
    VPC52 = lab.get_node("china-pc7")
    VPC52.start()

    lab.create_node(name='china-pc8', template='VPCS', x='717', y='270')
    VPC53 = lab.get_node("china-pc8")
    VPC53.start()

    lab.create_node(name='china-web', template='VPCS', x='192', y='45')
    VPC54 = lab.get_node("china-web")
    VPC54.start()

    lab.create_node(name='germany-pc1', template='VPCS', x='422', y='420')
    VPC55 = lab.get_node("germany-pc1")
    VPC55.start()

    lab.create_node(name='germany-pc2', template='VPCS', x='492', y='420')
    VPC56 = lab.get_node("germany-pc2")
    VPC56.start()

    lab.create_node(name='germany-pc5', template='VPCS', x='642', y='420')
    VPC57 = lab.get_node("germany-pc5")
    VPC57.start()

    lab.create_node(name='germany-pc6', template='VPCS', x='717', y='420')
    VPC58 = lab.get_node("germany-pc6")
    VPC58.start()

    lab.create_node(name='germany-pc3', template='VPCS', x='417', y='645')
    VPC59 = lab.get_node("germany-pc3")
    VPC59.start()

    lab.create_node(name='germany-pc4', template='VPCS', x='492', y='645')
    VPC60 = lab.get_node("germany-pc4")
    VPC60.start()
     
    lab.create_node(name='germany-pc7', template='VPCS', x='639', y='645')
    VPC61 = lab.get_node("germany-pc7")
    VPC61.start()

    lab.create_node(name='germany-pc8', template='VPCS', x='716', y='645')
    VPC62 = lab.get_node("germany-pc8")
    VPC62.start()

    lab.create_node(name='germany-web', template='VPCS', x='192', y='645')
    VPC63 = lab.get_node("germany-web")
    VPC63.start()

    lab.create_node(name='switzerland-int', template='Cisco IOSv 15.5(3)M', x='-108', y='-322')
    router0 = lab.get_node("switzerland-int")
    router0.start()

    lab.create_node(name='switzerland-edge', template='Cisco IOSv 15.5(3)M', x='-107', y='-100')
    router1 = lab.get_node("switzerland-edge")
    router1.start()

    lab.create_node(name='india-int', template='Cisco IOSv 15.5(3)M', x='-555', y='-203')
    router2 = lab.get_node("india-int")
    router2.start()

    lab.create_node(name='india-edge', template='Cisco IOSv 15.5(3)M', x='-255', y='-20')
    router3 = lab.get_node("india-edge")
    router3.start()

    lab.create_node(name='japan-int', template='Cisco IOSv 15.5(3)M', x='340', y='-203')
    router4 = lab.get_node("japan-int")
    router4.start()

    lab.create_node(name='japan-edge', template='Cisco IOSv 15.5(3)M', x='39', y='-21')
    router5 = lab.get_node("japan-edge")
    router5.start()

    lab.create_node(name='china-int', template='Cisco IOSv 15.5(3)M', x='342', y='203')
    router6 = lab.get_node("china-int")
    router6.start() 

    lab.create_node(name='china-edge', template='Cisco IOSv 15.5(3)M', x='42', y='203')
    router7 = lab.get_node("china-edge")
    router7.start()

    lab.create_node(name='germany-int', template='Cisco IOSv 15.5(3)M', x='343', y='540')
    router8 = lab.get_node("germany-int")
    router8.start()

    lab.create_node(name='germany-edge', template='Cisco IOSv 15.5(3)M', x='42', y='428')
    router9 = lab.get_node("germany-edge")
    router9.start()

    lab.create_node(name='europe-int', template='Cisco IOSv 15.5(3)M', x='-558', y='203')
    router10 = lab.get_node("europe-int")
    router10.start()

    lab.create_node(name='europe-edge', template='Cisco IOSv 15.5(3)M', x='-258', y='201')
    router11 = lab.get_node("europe-edge")
    router11.start()

    lab.create_node(name='america-int', template='Cisco IOSv 15.5(3)M', x='-558', y='540')
    router12 = lab.get_node("america-int")
    router12.start()

    lab.create_node(name='america-edge', template='Cisco IOSv 15.5(3)M', x='-258', y='428')
    router13 = lab.get_node("america-edge")
    router13.start()

    
    lab.create_node(name='switzerland-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-100', y='-473')
    sw0 = lab.get_node("switzerland-sw1")
    sw0.start()

    lab.create_node(name='switzerland-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-100', y='-623')
    sw1 = lab.get_node("switzerland-sw2")
    sw1.start()

    lab.create_node(name='india-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-701', y='-203')
    sw2 = lab.get_node("india-sw1")
    sw2.start()

    lab.create_node(name='india-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-850', y='-203')
    sw3 = lab.get_node("india-sw2")
    sw3.start()

    lab.create_node(name='japan-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='502', y='-203')
    sw4 = lab.get_node("japan-sw1")
    sw4.start()

    lab.create_node(name='japan-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='656', y='-203')
    sw5 = lab.get_node("japan-sw2")
    sw5.start()

    lab.create_node(name='china-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='500', y='164')
    sw6 = lab.get_node("china-sw1")
    sw6.start()

    lab.create_node(name='china-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='653', y='164')
    sw7 = lab.get_node("china-sw2")
    sw7.start()

    lab.create_node(name='germany-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='498', y='536')
    sw8 = lab.get_node("germany-sw1")
    sw8.start()

    lab.create_node(name='germany-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='651', y='536')
    sw9 = lab.get_node("germany-sw2")
    sw9.start()

    lab.create_node(name='europe-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-700', y='167')
    sw10 = lab.get_node("europe-sw1")
    sw10.start()

    lab.create_node(name='europe-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-853', y='167')
    sw11 = lab.get_node("europe-sw2")
    sw11.start()

    lab.create_node(name='america-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-700', y='534')
    sw12 = lab.get_node("america-sw1")
    sw12.start()

    lab.create_node(name='america-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-850', y='534')
    sw13 = lab.get_node("america-sw2")
    sw13.start()

    lab.create_node(name='CiscoASAv9.16.2-3', template='Cisco ASAv 9.9.2', x='-101', y='-225')
    ASA0 = lab.get_node("CiscoASAv9.16.2-3")
    ASA0.start()

    lab.create_node(name='india-ASA', template='Cisco ASAv 9.9.2', x='-403', y='-112')
    ASA1 = lab.get_node("india-ASA")
    ASA1.start()

    lab.create_node(name='japan-ASA', template='Cisco ASAv 9.9.2', x='193', y='-118')
    ASA2 = lab.get_node("japan-ASA")
    ASA2.start()

    lab.create_node(name='china-ASA', template='Cisco ASAv 9.9.2', x='199', y='194')
    ASA3 = lab.get_node("china-ASA")
    ASA3.start()

    lab.create_node(name='germany-ASA', template='Cisco ASAv 9.9.2', x='198', y='463')
    ASA4 = lab.get_node("germany-ASA")
    ASA4.start()

    lab.create_node(name='europe-ASA', template='Cisco ASAv 9.9.2', x='-398', y='198')
    ASA5 = lab.get_node("europe-ASA")
    ASA5.start()

    lab.create_node(name='america-ASA', template='Cisco ASAv 9.9.2', x='-400', y='493')
    ASA6 = lab.get_node("america-ASA")
    ASA6.start()

    #Swiss links 
    lab.create_link("switzerland-sw2", "Gi0/1", "switzerland-pc1", "Ethernet0")
    lab.create_link("switzerland-sw2", "Gi1/2", "switzerland-pc2", "Ethernet0")
    lab.create_link("switzerland-sw2", "Gi1/0", "switzerland-pc3", "Ethernet0")
    lab.create_link("switzerland-sw2", "Gi1/1", "switzerland-pc4", "Ethernet0")
    lab.create_link("switzerland-sw1", "Gi0/3", "switzerland-sw2", "Gi0/3")
    lab.create_link("switzerland-sw1", "Gi1/2", "switzerland-pc5", "Ethernet0")
    lab.create_link("switzerland-sw1", "Gi0/0", "switzerland-pc6", "Ethernet0")
    lab.create_link("switzerland-sw1", "Gi1/1", "switzerland-pc7", "Ethernet0")
    lab.create_link("switzerland-sw1", "Gi1/0", "switzerland-pc8", "Ethernet0")
    lab.create_link("switzerland-sw1", "Gi0/2", "switzerland-int", "Gi0/2")
    lab.create_link("switzerland-int", "Gi0/1", "CiscoASAv9.16.2-3", "Gi0/1")
    lab.create_link("switzerland-web", "Ethernet0", "CiscoASAv9.16.2-3", "Gi0/2")
    lab.create_link("switzerland-edge", "Gi0/0", "CiscoASAv9.16.2-3", "Gi0/0")
    
    #India Links
    lab.create_link("india-sw2", "Gi0/3", "india-pc1", "Ethernet0")
    lab.create_link("india-sw2", "Gi0/1", "india-pc2", "Ethernet0")
    lab.create_link("india-sw2", "Gi1/0", "india-pc3", "Ethernet0")
    lab.create_link("india-sw2", "Gi0/0", "india-pc4", "Ethernet0")
    lab.create_link("india-sw1", "Gi0/2", "india-sw2", "Gi0/2")
    lab.create_link("india-sw1", "Gi0/0", "india-pc5", "Ethernet0")
    lab.create_link("india-sw1", "Gi1/0", "india-pc6", "Ethernet0")
    lab.create_link("india-sw1", "Gi1/1", "india-pc7", "Ethernet0")
    lab.create_link("india-sw1", "Gi0/3", "india-pc8", "Ethernet0")
    lab.create_link("india-sw1", "Gi0/1", "india-int", "Gi0/2")
    lab.create_link("india-int", "Gi0/1", "india-ASA", "Gi0/1")
    lab.create_link("india-web", "Ethernet0", "india-ASA", "Gi0/2")
    lab.create_link("india-edge", "Gi0/0", "india-ASA", "Gi0/0")

    #Japan Links
    lab.create_link("japan-sw2", "Gi1/0", "japan-pc8", "Ethernet0")
    lab.create_link("japan-sw2", "Gi0/0", "japan-pc7", "Ethernet0")
    lab.create_link("japan-sw2", "Gi1/1", "japan-pc6", "Ethernet0")
    lab.create_link("japan-sw2", "Gi1/2", "japan-pc5", "Ethernet0")
    lab.create_link("japan-sw2", "Gi0/3", "japan-sw1", "Gi0/3")
    lab.create_link("japan-sw1", "Gi0/1", "japan-pc4", "Ethernet0")
    lab.create_link("japan-sw1", "Gi0/0", "japan-pc3", "Ethernet0")
    lab.create_link("japan-sw1", "Gi1/0", "japan-pc2", "Ethernet0")
    lab.create_link("japan-sw1", "Gi1/1", "japan-pc1", "Ethernet0")
    lab.create_link("japan-sw1", "Gi0/2", "japan-int", "Gi0/2")
    lab.create_link("japan-int", "Gi0/1", "japan-ASA", "Gi0/1")
    lab.create_link("japan-web", "Ethernet0", "japan-ASA", "Gi0/2")
    lab.create_link("japan-edge", "Gi0/0", "japan-ASA", "Gi0/0")

    #China Links 
    lab.create_link("china-sw2", "Gi1/1", "china-pc8", "Ethernet0")
    lab.create_link("china-sw2", "Gi1/0", "china-pc7", "Ethernet0")
    lab.create_link("china-sw2", "Gi1/2", "china-pc6", "Ethernet0")
    lab.create_link("china-sw2", "Gi0/1", "china-pc5", "Ethernet0")
    lab.create_link("china-sw2", "Gi0/3", "china-sw1", "Gi0/3")
    lab.create_link("china-sw1", "Gi1/1", "china-pc4", "Ethernet0")
    lab.create_link("china-sw1", "Gi1/0", "china-pc3", "Ethernet0")
    lab.create_link("china-sw1", "Gi1/2", "china-pc2", "Ethernet0")
    lab.create_link("china-sw1", "Gi0/1", "china-pc1", "Ethernet0")
    lab.create_link("china-sw1", "Gi0/2", "china-int", "Gi0/2")
    lab.create_link("china-int", "Gi0/1", "china-ASA", "Gi0/1")
    lab.create_link("china-web", "Ethernet0", "china-ASA", "Gi0/2")
    lab.create_link("china-edge", "Gi0/0", "china-ASA", "Gi0/0")

    #Germany Links 
    lab.create_link("germany-sw2", "Gi1/1", "germany-pc8", "Ethernet0")
    lab.create_link("germany-sw2", "Gi1/0", "germany-pc7", "Ethernet0")
    lab.create_link("germany-sw2", "Gi1/2", "germany-pc6", "Ethernet0")
    lab.create_link("germany-sw2", "Gi0/1", "germany-pc5", "Ethernet0")
    lab.create_link("germany-sw2", "Gi0/3", "germany-sw1", "Gi0/3")
    lab.create_link("germany-sw1", "Gi1/2", "germany-pc4", "Ethernet0")
    lab.create_link("germany-sw1", "Gi1/0", "germany-pc3", "Ethernet0")
    lab.create_link("germany-sw1", "Gi0/1", "germany-pc2", "Ethernet0")
    lab.create_link("germany-sw1", "Gi0/0", "germany-pc1", "Ethernet0")
    lab.create_link("germany-sw1", "Gi0/2", "germany-int", "Gi0/2")
    lab.create_link("germany-int", "Gi0/1", "germany-ASA", "Gi0/1")
    lab.create_link("germany-web", "Ethernet0", "germany-ASA", "Gi0/2")
    lab.create_link("germany-edge", "Gi0/0", "germany-ASA", "Gi0/0")

    #Europe Links 
    lab.create_link("europe-sw2", "Gi0/0", "europe-pc1", "Ethernet0")
    lab.create_link("europe-sw2", "Gi1/0", "europe-pc2", "Ethernet0")
    lab.create_link("europe-sw2", "Gi0/1", "europe-pc3", "Ethernet0")
    lab.create_link("europe-sw2", "Gi1/1", "europe-pc4", "Ethernet0")
    lab.create_link("europe-sw2", "Gi0/3", "europe-sw1", "Gi0/3")
    lab.create_link("europe-sw1", "Gi0/0", "europe-pc5", "Ethernet0")
    lab.create_link("europe-sw1", "Gi1/0", "europe-pc6", "Ethernet0")
    lab.create_link("europe-sw1", "Gi0/1", "europe-pc7", "Ethernet0")
    lab.create_link("europe-sw1", "Gi1/1", "europe-pc8", "Ethernet0")
    lab.create_link("europe-sw1", "Gi0/2", "europe-int", "Gi0/2")
    lab.create_link("europe-int", "Gi0/1", "europe-ASA", "Gi0/1")
    lab.create_link("europe-web", "Ethernet0", "europe-ASA", "Gi0/2")   
    lab.create_link("europe-edge", "Gi0/0", "europe-ASA", "Gi0/0")

    #America Links
    lab.create_link("america-sw2", "Gi1/2", "america-pc1", "Ethernet0")
    lab.create_link("america-sw2", "Gi1/0", "america-pc2", "Ethernet0")
    lab.create_link("america-sw2", "Gi0/2", "america-pc3", "Ethernet0")
    lab.create_link("america-sw2", "Gi1/1", "america-pc4", "Ethernet0")
    lab.create_link("america-sw2", "Gi0/3", "america-sw1", "Gi0/3")
    lab.create_link("america-sw1", "Gi0/0", "america-pc5", "Ethernet0")
    lab.create_link("america-sw1", "Gi1/0", "america-pc6", "Ethernet0")
    lab.create_link("america-sw1", "Gi0/1", "america-pc7", "Ethernet0")
    lab.create_link("america-sw1", "Gi1/1", "america-pc8", "Ethernet0")
    lab.create_link("america-sw1", "Gi0/2", "america-int", "Gi0/2")
    lab.create_link("america-int", "Gi0/1", "america-ASA", "Gi0/1")
    lab.create_link("america-web", "Ethernet0", "america-ASA", "Gi0/2")
    lab.create_link("america-edge", "Gi0/0", "america-ASA", "Gi0/0")

    #Edge Router Connections
    lab.create_link("switzerland-edge", "Gi0/1", "india-edge", "Gi0/1")
    lab.create_link("switzerland-edge", "Gi0/2", "japan-edge", "Gi0/2")
    lab.create_link("switzerland-edge", "Gi0/4", "china-edge", "Gi0/5")
    lab.create_link("switzerland-edge", "Gi0/6", "germany-edge", "Gi0/6")
    lab.create_link("switzerland-edge", "Gi0/3", "europe-edge", "Gi0/4")
    lab.create_link("switzerland-edge", "Gi0/5", "america-edge", "Gi0/5")
    lab.create_link("india-edge", "Gi0/2", "europe-edge", "Gi0/2")
    lab.create_link("europe-edge", "Gi0/3", "america-edge", "Gi0/3")
    lab.create_link("japan-edge", "Gi0/3", "china-edge", "Gi0/3")
    lab.create_link("china-edge", "Gi0/4", "germany-edge", "Gi0/4")
    lab.create_link("germany-edge", "Gi0/5", "america-edge", "Gi0/4")
    



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
