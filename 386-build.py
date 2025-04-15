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
    lab.create_node(name='switzerland-pc5', template='VPC', x='-257', y='-554').start()
    lab.create_node(name='switzerland-pc6', template='VPC', x='-257', y='-479').start()
    lab.create_node(name='switzerland-pc3', template='VPC', x='42', y='-704').start()
    lab.create_node(name='switzerland-pc4', template='VPC', x='42', y='-629').start()
    lab.create_node(name='switzerland-pc7', template='VPC', x='42', y='-554').start()
    lab.create_node(name='switzerland-pc8', template='VPC', x='42', y='-479').start()
    lab.create_node(name='switzerland-web', template='VPC', x='35', y='-225').start()

    lab.create_node(name='india-pc1', template='VPC', x='-932', y='-329').start()
    lab.create_node(name='india-pc2', template='VPC', x='-857', y='-329').start()
    lab.create_node(name='india-pc5', template='VPC', x='-707', y='-329').start()
    lab.create_node(name='india-pc6', template='VPC', x='-632', y='-331').start()
    lab.create_node(name='india-web', template='VPC', x='-561', y='-331').start()
    lab.create_node(name='india-pc3', template='VPC', x='-932', y='-104').start()
    lab.create_node(name='india-pc4', template='VPC', x='-857', y='-104').start()
    lab.create_node(name='india-pc7', template='VPC', x='-707', y='-104').start()
    lab.create_node(name='india-pc8', template='VPC', x='-632', y='-104').start()

    lab.create_node(name='europe-web', template='VPC', x='-407', y='45').start()
    lab.create_node(name='europe-pc1', template='VPC', x='-932', y='45').start()
    lab.create_node(name='europe-pc2', template='VPC', x='-857', y='45').start()    
    lab.create_node(name='europe-pc5', template='VPC', x='-707', y='45').start()
    lab.create_node(name='europe-pc6', template='VPC', x='-632', y='45').start()
    lab.create_node(name='europe-pc3', template='VPC', x='-932', y='270').start()
    lab.create_node(name='europe-pc4', template='VPC', x='-857', y='270').start()
    lab.create_node(name='europe-pc7', template='VPC', x='-707', y='270').start()
    lab.create_node(name='europe-pc8', template='VPC', x='-632', y='270').start()

    lab.create_node(name='america-pc1', template='VPC', x='-932', y='420').start()
    lab.create_node(name='america-pc2', template='VPC', x='-857', y='420').start()
    lab.create_node(name='america-pc5', template='VPC', x='-707', y='420').start()
    lab.create_node(name='america-pc6', template='VPC', x='-632', y='420').start()
    lab.create_node(name='america-pc3', template='VPC', x='-932', y='645').start()
    lab.create_node(name='america-pc4', template='VPC', x='-857', y='645').start()
    lab.create_node(name='america-pc7', template='VPC', x='-707', y='645').start()
    lab.create_node(name='america-pc8', template='VPC', x='-632', y='645').start()
    lab.create_node(name='america-web', template='VPC', x='-407', y='645').start()

    lab.create_node(name='japan-web', template='VPC', x='339', y='-328').start()
    lab.create_node(name='japan-pc1', template='VPC', x='417', y='-329').start()
    lab.create_node(name='japan-pc2', template='VPC', x='492', y='-329').start()
    lab.create_node(name='japan-pc5', template='VPC', x='642', y='-329').start()
    lab.create_node(name='japan-pc6', template='VPC', x='717', y='-329').start()
    lab.create_node(name='japan-pc3', template='VPC', x='417', y='-104').start()
    lab.create_node(name='japan-pc4', template='VPC', x='492', y='-104').start()
    lab.create_node(name='japan-pc7', template='VPC', x='642', y='-104').start()
    lab.create_node(name='japan-pc8', template='VPC', x='717', y='-104').start()

    lab.create_node(name='china-pc1', template='VPC', x='417', y='45').start()
    lab.create_node(name='china-pc2', template='VPC', x='492', y='45').start()
    lab.create_node(name='china-pc5', template='VPC', x='642', y='45').start()
    lab.create_node(name='china-pc6', template='VPC', x='717', y='45').start()
    lab.create_node(name='china-pc3', template='VPC', x='417', y='270').start()
    lab.create_node(name='china-pc4', template='VPC', x='492', y='270').start()
    lab.create_node(name='china-pc7', template='VPC', x='642', y='270').start()
    lab.create_node(name='china-pc8', template='VPC', x='717', y='270').start()
    lab.create_node(name='china-web', template='VPC', x='192', y='45').start()

    lab.create_node(name='germany-pc1', template='VPC', x='422', y='420').start()
    lab.create_node(name='germany-pc2', template='VPC', x='492', y='420').start()
    lab.create_node(name='germany-pc5', template='VPC', x='642', y='420').start()
    lab.create_node(name='germany-pc6', template='VPC', x='717', y='420').start()   
    lab.create_node(name='germany-pc3', template='VPC', x='417', y='645').start()
    lab.create_node(name='germany-pc4', template='VPC', x='492', y='645').start()       
    lab.create_node(name='germany-pc7', template='VPC', x='639', y='645').start()
    lab.create_node(name='germany-pc8', template='VPC', x='716', y='645').start()
    lab.create_node(name='germany-web', template='VPC', x='192', y='645').start()

    lab.create_node(name='switzerland-int', template='Cisco IOSv 15.5(3)M', x='-108', y='-322').start()
    lab.create_node(name='switzerland-edge', template='Cisco IOSv 15.5(3)M', x='-107', y='-100').start()
    lab.create_node(name='india-int', template='Cisco IOSv 15.5(3)M', x='-555', y='-203').start()
    lab.create_node(name='india-edge', template='Cisco IOSv 15.5(3)M', x='-255', y='-20').start()
    lab.create_node(name='japan-int', template='Cisco IOSv 15.5(3)M', x='340', y='-203').start()
    lab.create_node(name='japan-edge', template='Cisco IOSv 15.5(3)M', x='39', y='-21').start()
    lab.create_node(name='china-int', template='Cisco IOSv 15.5(3)M', x='342', y='203').start()
    lab.create_node(name='china-edge', template='Cisco IOSv 15.5(3)M', x='42', y='203').start()
    lab.create_node(name='germany-int', template='Cisco IOSv 15.5(3)M', x='343', y='540').start()
    lab.create_node(name='germany-edge', template='Cisco IOSv 15.5(3)M', x='42', y='428').start()
    lab.create_node(name='europe-int', template='Cisco IOSv 15.5(3)M', x='-558', y='203').start()
    lab.create_node(name='europe-edge', template='Cisco IOSv 15.5(3)M', x='-258', y='201').start()
    lab.create_node(name='america-int', template='Cisco IOSv 15.5(3)M', x='-558', y='540').start()
    lab.create_node(name='america-edge', template='Cisco IOSv 15.5(3)M', x='-258', y='428').start()
    
    lab.create_node(name='switzerland-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-100', y='-473').start()
    lab.create_node(name='switzerland-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-100', y='-623').start()
    lab.create_node(name='india-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-701', y='-203').start()
    lab.create_node(name='india-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-850', y='-203').start()
    lab.create_node(name='japan-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='502', y='-203').start()
    lab.create_node(name='japan-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='656', y='-203').start()
    lab.create_node(name='china-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='500', y='164').start()
    lab.create_node(name='china-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='653', y='164').start()
    lab.create_node(name='germany-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='498', y='536').start()
    lab.create_node(name='germany-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='651', y='536').start()
    lab.create_node(name='europe-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-700', y='167').start()
    lab.create_node(name='europe-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-853', y='167').start()
    lab.create_node(name='america-sw1', template='Cisco IOSvL2 15.2(20170321:233949)', x='-700', y='534').start()
    lab.create_node(name='america-sw2', template='Cisco IOSvL2 15.2(20170321:233949)', x='-850', y='534').start()

    lab.create_node(name='CiscoASAv9.16.2-3', template='Cisco ASAv 9.9.2', x='-101', y='-225').start()
    lab.create_node(name='india-ASA', template='Cisco ASAv 9.9.2', x='-403', y='-112').start()
    lab.create_node(name='japan-ASA', template='Cisco ASAv 9.9.2', x='193', y='-118').start()
    lab.create_node(name='china-ASA', template='Cisco ASAv 9.9.2', x='199', y='194').start()
    lab.create_node(name='germany-ASA', template='Cisco ASAv 9.9.2', x='198', y='463').start()
    lab.create_node(name='europe-ASA', template='Cisco ASAv 9.9.2', x='-398', y='198').start()
    lab.create_node(name='america-ASA', template='Cisco ASAv 9.9.2', x='-400', y='493').start()

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
