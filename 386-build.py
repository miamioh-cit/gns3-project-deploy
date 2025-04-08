import time
from gns3fy import Gns3Connector, Project, Node, Link
from getpass import getpass

LAB_NAME = input("Input a unique Lab Name: ")
SERVER_URL = "http://10.48.229.11:80"
GNS3_USER = "cit358-m"
GNS3_PW = "cit358-m"
server = Gns3Connector(url=SERVER_URL, user=GNS3_USER, cred=GNS3_PW)

# Verify connectivity by checking the server version
print("Connecting to GNS3 server to verify uniqueness of Project name", server.get_version(), "at", SERVER_URL)

#Verify that lab name is unique, then create a new project on the server.
try:
    lab = server.create_project(name=LAB_NAME)
except:
    print("=========================================================")
    print("Error: May not be a unique Lab Name!")
    print("=========================================================")
    from sys import exit
    exit()

#If lab name is unique, confirm with user.
print("-----------------------------------------------------------------------")
print("Project name is unique, nodes are being created.")
print("-----------------------------------------------------------------------")
print("Please wait until script rungs before entering the project in GNS3!")
print("-----------------------------------------------------------------------")

# Now open the project from the server
lab = Project(name=LAB_NAME, connector=server)
lab.get()
lab.open()

#Create and start Switzerland-PC1-VPC
lab.create_node(name='switzerland-pc1', template='VPC', x='-257', y='-704')
switzerland-pc1=lab.get_node("switzerland-pc1")
switzerland-pc1.start()

#Create and start Switzerland-PC2-VPC
lab.create_node(name='switzerland-pc2', template='VPC', x='-257', y='-629')
switzerland-pc2=lab.get_node("switzerland-pc2")
switzerland-pc2.start()

#Create and start Router
lab.create_node(name='router1', template='Cisco IOSv 15.5(3)M', x='298', y='300')
router1=lab.get_node("router1")
router1.start()

#Create and Start Windows Server 2016 Servers

lab.create_node(name='svr16', template='Windows Server 2016', x='299', y='300')
svr16=lab.get_node("svr16")
svr16.start()


#Create Kali
lab.create_node(name='kali', template='Kali Linux 2021.1', x='250', y='200')
kl1=lab.get_node("kali")
kl1.start()

#Create Switch
lab.create_node(name='switch1', template='Cisco IOSvL2 15.2(20170321:233949)', x='200', y='200')
sw1=lab.get_node("switch1")
sw1.start()

#Create and Start Ohio Windows 10 Client No. 1
lab.create_node(name='ohio-01', template='Windows 10 w/ Edge', x='301', y='200')
oh1=lab.get_node("ohio-01")
oh1.start()

#Create and Start Ohio Windows 10 Client No. 2
lab.create_node(name='ohio-02', template='Windows 10 w/ Edge', x='302', y='200')
win10_oh2=lab.get_node("ohio-02")
win10_oh2.start()

#Create and Start Ohio Windows 10 Client No. 3
lab.create_node(name='ohio-win10-03', template='Windows 10 w/ Edge', x='303', y='200')
win10_oh3=lab.get_node("ohio-win10-03")
win10_oh3.start()

#Create and Start Ohio Windows 10 Client No. 4
lab.create_node(name='ohio-win10-04', template='Windows 10 w/ Edge', x='304', y='200')
win10_oh3=lab.get_node("ohio-win10-04")
win10_oh3.start()

#Create and Start Kentucky Windows 10 Client No. 1
lab.create_node(name='ky-win10-01', template='Windows 10 w/ Edge', x='304', y='200')
win10_ky1=lab.get_node("ky-win10-01")
win10_ky1.start()

#Create and Start Kentucky Windows 10 Client No. 2
lab.create_node(name='ky-win10-02', template='Windows 10 w/ Edge', x='306', y='200')
win10_ky2=lab.get_node("ky-win10-02")
win10_ky2.start()

#Create and Start Kentucky Windows 10 Client No. 3
lab.create_node(name='ky-win10-03', template='Windows 10 w/ Edge', x='307', y='200')
win10_ky3=lab.get_node("ky-win10-03")
win10_ky3.start()

#Create and Start Kentucky Windows 10 Client No. 4
lab.create_node(name='ky-win10-04', template='Windows 10 w/ Edge', x='308', y='200')
win10_ky4=lab.get_node("ky-win10-04")
win10_ky4.start()





#Link the nodes
lab.create_link("svr16", "NIC1", "switch1", "Gi0/0")
#lab.create_link("sir16", "NIC1", "switch1", "Gi0/1")
#lab.create_link("offsite-switch", "Gi0/2", "offsite-router", "Gi0/0")
#lab.create_link("in-edge", "Gi0/0", "offsite-router", "Gi0/1")
#lab.create_link("ky-edge", "Gi0/0", "offsite-router", "Gi0/2")
#lab.create_link("ky-edge", "Gi0/1", "ky-int", "Gi0/1")
#lab.create_link("ky-edge", "Gi0/2", "oh-edge", "Gi0/0")
#lab.create_link("in-edge", "Gi0/1", "oh-edge", "Gi0/1")
#lab.create_link("oh-edge", "Gi0/2", "oh-int", "Gi0/0")
#lab.create_link("internet", "eth0", "ky-edge", "Gi0/3")
#lab.create_link("oh-int", "Gi0/1", "ohio-switch", "Gi0/0")
#lab.create_link("ohio-win10-01", "NIC1", "ohio-switch", "Gi0/1")
#lab.create_link("ohio-win10-02", "NIC1", "ohio-switch", "Gi0/2")
#lab.create_link("ohio-win10-03", "NIC1", "ohio-switch", "Gi0/3")
#lab.create_link("ohio-web", "NIC1", "oh-int", "Gi0/2")
#lab.create_link("in-win10-01", "NIC1", "in-edge", "Gi0/2")
#lab.create_link("ky-int", "Gi0/0", "ky-switch-1", "Gi0/0")
#lab.create_link("ky-switch-1", "Gi0/1", "ky-switch-2", "Gi0/0")
#lab.create_link("ky-win10-01", "NIC1", "ky-switch-1", "Gi0/2")
#lab.create_link("ky-win10-02", "NIC1", "ky-switch-1", "Gi0/3")
#lab.create_link("ky-win10-03", "NIC1", "ky-switch-2", "Gi1/0")
#lab.create_link("ky-win10-04", "NIC1", "ky-switch-2", "Gi1/1")

#Confirm completion of the script with the user.
print("-----------------------------------------------------------------------")
print("Nodes created, started and linked.  Here are the links:")
print("-----------------------------------------------------------------------")
lab.links_summary()
print("-----------------------------------------------------------------------")
print(LAB_NAME + " build is Complete. It is now safe to open the project in GNS3")
print("-----------------------------------------------------------------------")


