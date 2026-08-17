import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "480-Test1"

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

    try:
        lab.create_node(name='H-101', template='generic-sensor', x=-575, y=-625)
        sw1 = lab.get_node("H-101")
    except Exception as e:
        print(f"Error creating or starting node: {e}")
    
    try:
        lab.create_node(name='LT-101', template='generic-sensor', x=-483, y=-628)
        sw2 = lab.get_node("LT-101")
    except Exception as e:
        print(f"Error creating or starting node: {e}")

    lab.create_node(name='DP-101', template='generic-sensor', x=-380, y=-619)
    sw3 = lab.get_node("DP-101")


    lab.create_node(name='P-101', template='generic-sensor', x=-299, y=-623)
    sw4 = lab.get_node("P-101")


    lab.create_node(name='FT-201', template='generic-sensor', x=-194, y=-627)
    sw5 = lab.get_node("FT-201")


    lab.create_node(name='LT-201', template='generic-sensor', x=-109, y=-632)
    sw6 = lab.get_node("LT-201")

    lab.create_node(name='DP-201', template='generic-sensor', x=-25, y=-618)
    sw7 = lab.get_node("DP-201")


    lab.create_node(name='MV-201', template='generic-sensor', x=58, y=-620)
    sw8 = lab.get_node("MV-201")


    lab.create_node(name='DO-301', template='generic-sensor', x=177, y=-606)
    sw9 = lab.get_node("DO-301")


    lab.create_node(name='FT-301', template='generic-sensor', x=254, y=-606)
    sw10 = lab.get_node("FT-301")


    lab.create_node(name='MLSS-301', template='generic-sensor', x=330, y=-599)
    sw11 = lab.get_node("MLSS-301")


    lab.create_node(name='SV-301', template='generic-sensor', x=406, y=-604)
    sw12 = lab.get_node("SV-301")


    lab.create_node(name='FT-401', template='generic-sensor', x=596, y=-578)
    sw13 = lab.get_node("FT-401")


    lab.create_node(name='LT-401', template='generic-sensor', x=687, y=-575)
    sw14 = lab.get_node("LT-401")

    
    lab.create_node(name='TU-401', template='generic-sensor', x=786, y=-577)
    sw15 = lab.get_node("TU-401")
  

    lab.create_node(name='DL-401', template='generic-sensor', x=892, y=-575)
    sw16 = lab.get_node("DL-401")
 

    lab.create_node(name='Vlan-01', template='Ethernet switch', x=-424, y=-476)
    vlan1 = lab.get_node("Vlan-01")
 

    lab.create_node(name='Vlan-02', template='Ethernet switch', x=-81, y=-504)
    vlan2 = lab.get_node("Vlan-02")


    lab.create_node(name='Vlan-03', template='Ethernet switch', x=307, y=-467)
    vlan3 = lab.get_node("Vlan-03")
  
    lab.create_node(name='Vlan-04', template='Ethernet switch', x=741, y=-474)
    vlan4 = lab.get_node("Vlan-04")


    lab.create_node(name='HMI-Influent', template='generic-hmi', x=-549, y=-316)
    HMI1 = lab.get_node("HMI-Influent")

    lab.create_node(name='PLC-Influent', template='generic-plc', x=-419, y=-367)
    PLC1 = lab.get_node("PLC-Influent")
    

    lab.create_node(name='HMI-Primary', template='generic-hmi', x=-234, y=-362)
    HMI2 = lab.get_node("HMI-Primary")
    

    lab.create_node(name='PLC-Primary', template='generic-plc', x=-76, y=-364)
    PLC2 = lab.get_node("PLC-Primary")
    

    lab.create_node(name='HMI-Aeration', template='generic-hmi', x=184, y=-365)
    HMI3 = lab.get_node("HMI-Aeration")
    

    lab.create_node(name='PLC-Aeration', template='generic-plc', x=312, y=-356)
    PLC3 = lab.get_node("PLC-Aeration")
    

    lab.create_node(name='HMI-Clarification', template='generic-hmi', x=598, y=-325)
    HMI4 = lab.get_node("HMI-Clarification")
    

    lab.create_node(name='PLC-Clarification', template='generic-plc', x=746, y=-340)
    PLC4 = lab.get_node("PLC-Clarification")
    

    lab.create_node(name='Vlan-10', template='Ethernet switch', x=-511, y=-199)
    Vlan10 = lab.get_node("Vlan-10")
    

    lab.create_node(name='Vlan-20', template='Ethernet switch', x=-146, y=-243)
    Vlan20 = lab.get_node("Vlan-20")
    

    lab.create_node(name='Vlan-30', template='Ethernet switch', x=236, y=-225)
    Vlan30 = lab.get_node("Vlan-30")
    

    lab.create_node(name='Vlan-40', template='Ethernet switch', x=562, y=-196)
    Vlan40 = lab.get_node("Vlan-40")
    

    lab.create_node(name='Ignition-Switch', template='Ethernet switch', x=-414, y=-41)
    sw17 = lab.get_node("Ignition-Switch")
    

    lab.create_node(name='scada-server', template='generic-scada', x=135, y=-54)
    scada = lab.get_node("scada-server")
    

    lab.create_node(name='KaliLinux-1', template='Kali Linux', x=662, y=-48)
    KL = lab.get_node("KaliLinux-1")
    

    lab.create_node(name='ignition-1', template='ignition', x=-632, y=61)
    sw18 = lab.get_node("ignition-1")
    

    lab.create_node(name='Vlan-50', template='Ethernet switch', x=-412, y=99)
    Vlan50 = lab.get_node("Vlan-50")
    

    lab.create_node(name='Vlan-60', template='Ethernet switch', x=-4, y=98)
    Vlan60 = lab.get_node("Vlan-60")
    

    lab.create_node(name='Vlan-70', template='Ethernet switch', x=460, y=92)
    Vlan70 = lab.get_node("Vlan-70")
    

    lab.create_node(name='HMI-Disenfection', template='generic-hmi', x=-673, y=-180)
    HMI5 = lab.get_node("HMI-Disenfection")
    

    lab.create_node(name='PLC-Disenfection', template='generic-plc', x=-408, y=194)
    PLC5 = lab.get_node("PLC-Disenfection")
    

    lab.create_node(name='HMI-Thickening', template='generic-hmi', x=-154, y=218)
    HMI6 = lab.get_node("HMI-Thickening")
    

    lab.create_node(name='PLC-Thickening', template='generic-plc', x=-5, y=203)
    PLC6 = lab.get_node("PLC-Thickening")
    

    lab.create_node(name='HMI-Digestion', template='generic-hmi', x=280, y=166)
    HMI7 = lab.get_node("HMI-Digestion")
    

    lab.create_node(name='PLC-Digestion', template='generic-plc', x=467, y=189)
    PLC7 = lab.get_node("PLC-Digestion")
    

    lab.create_node(name='Vlan-05', template='Ethernet switch', x=-410, y=317)
    Vlan05 = lab.get_node("Vlan-05")
    

    lab.create_node(name='Vlan-06', template='Ethernet switch', x=-8, y=306)
    Vlan06 = lab.get_node("Vlan-06")
    

    lab.create_node(name='Vlan-07', template='Ethernet switch', x=482, y=325)
    Vlan07 = lab.get_node("Vlan-07")
    

    lab.create_node(name='CL-501', template='generic-sensor', x=-564, y=402)
    sw19 = lab.get_node("CL-501")
    
    lab.create_node(name='FT-501', template='generic-sensor', x=-474, y=403)
    sw20 = lab.get_node("FT-501")
    

    lab.create_node(name='LT-501', template='generic-sensor', x=-325, y=402)
    sw21 = lab.get_node("LT-501")
    

    lab.create_node(name='AV-501', template='generic-sensor', x=-231, y=402)
    sw22 = lab.get_node("AV-501")
    

    lab.create_node(name='LT-601', template='generic-sensor', x=-107, y=398)
    sw23 = lab.get_node("LT-601")
    

    lab.create_node(name='FT-601', template='generic-sensor', x=-24, y=397)
    sw24 = lab.get_node("FT-601")
    

    lab.create_node(name='SS-601', template='generic-sensor', x=63, y=396)
    sw25 = lab.get_node("SS-601")
    

    lab.create_node(name='P-601', template='generic-sensor', x=154, y=394)
    sw26 = lab.get_node("P-601")
    

    lab.create_node(name='T-701', template='generic-sensor', x=344, y=410)
    sw27 = lab.get_node("T-701")
    

    lab.create_node(name='PT-701', template='generic-sensor', x=442, y=412)
    sw28 = lab.get_node("PT-701")
    

    lab.create_node(name='FT-701', template='generic-sensor', x=548, y=410)
    sw29 = lab.get_node("FT-701")
    

    lab.create_node(name='GAS-701', template='generic-sensor', x=647, y=412)
    sw30 = lab.get_node("GAS-701")
    


    
 # Refresh project inventory so gns3fy knows all node ports
    lab.get()

    # --- Top Vlan-01 Segment ---
    try:
        lab.create_link("PLC-Influent", "eth0", "Vlan-01", "Ethernet7")
    except Exception as e:
        print(f"Error linking PLC-Influent to Vlan-01: {e}")
    try:
        lab.create_link("H-101", "eth0", "Vlan-01", "Ethernet1")  # Fixed node name
    except Exception as e:
        print(f"Error linking H-101 to Vlan-01: {e}")
    try:
        lab.create_link("LT-101", "eth0", "Vlan-01", "Ethernet2")
    except Exception as e:
        print(f"Error linking LT-101 to Vlan-01: {e}")
    try:
        lab.create_link("DP-101", "eth0", "Vlan-01", "Ethernet3")
    except Exception as e:
        print(f"Error linking DP-101 to Vlan-01: {e}")
    try:
        lab.create_link("P-101", "eth0", "Vlan-01", "Ethernet4")
    except Exception as e:
        print(f"Error linking P-101 to Vlan-01: {e}")

    # --- Top Vlan-02 Segment ---
    try:
        lab.create_link("Vlan-02", "Ethernet0", "PLC-Primary", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-02 to PLC-Primary: {e}")
    try:
        lab.create_link("Vlan-02", "Ethernet1", "FT-201", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-02 to FT-201: {e}")
    try:    
        lab.create_link("Vlan-02", "Ethernet2", "LT-201", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-02 to LT-201: {e}")
    try:
        lab.create_link("Vlan-02", "Ethernet3", "DP-201", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-02 to DP-201: {e}")
    try:
        lab.create_link("Vlan-02", "Ethernet4", "MV-201", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-02 to MV-201: {e}")
    # --- Top Vlan-03 Segment ---
    try:
        lab.create_link("PLC-Aeration", "eth0", "Vlan-03", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Aeration to Vlan-03: {e}")
    try:
        lab.create_link("Vlan-03", "Ethernet1", "DO-301", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-03 to DO-301: {e}")
    try:
        lab.create_link("Vlan-03", "Ethernet2", "FT-301", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-03 to FT-301: {e}")
    try:
        lab.create_link("Vlan-03", "Ethernet3", "MLSS-301", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-03 to MLSS-301: {e}")
    try:
        lab.create_link("Vlan-03", "Ethernet4", "SV-301", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-03 to SV-301: {e}")
        
    # --- Top Vlan-04 Segment ---
    try:
        lab.create_link("PLC-Clarification", "eth0", "Vlan-04", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Clarification to Vlan-04: {e}")
    try:
        lab.create_link("Vlan-04", "Ethernet1", "FT-401", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-04 to FT-401: {e}")
    try:
        lab.create_link("Vlan-04", "Ethernet2", "LT-401", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-04 to LT-401: {e}")
    try:
        lab.create_link("Vlan-04", "Ethernet3", "TU-401", "eth0")
    except Exception as e:  
        print(f"Error linking Vlan-04 to TU-401: {e}")
    try:
        lab.create_link("Vlan-04", "Ethernet4", "DL-401", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-04 to DL-401: {e}")

    # --- Distribution Vlan-10 Segment ---
    try:
        lab.create_link("PLC-Influent", "eth1", "Vlan-10", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Influent to Vlan-10: {e}")
    try:
        lab.create_link("Vlan-10", "Ethernet2", "HMI-Influent", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-10 to HMI-Influent: {e}")
    try:
        lab.create_link("Vlan-10", "Ethernet7", "Ignition-Switch", "Ethernet0")
    except Exception as e:
        print(f"Error linking Vlan-10 to Ignition-Switch: {e}")
    try:
        lab.create_link("Vlan-10", "Ethernet1", "scada-server", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-10 to scada-server: {e}")

    # --- Distribution Vlan-20 Segment ---
    try:
        lab.create_link("PLC-Primary", "eth1", "Vlan-20", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Primary to Vlan-20: {e}")
    try:
        lab.create_link("Vlan-20", "Ethernet1", "HMI-Primary", "Eth0")
    except Exception as e:
        print(f"Error linking HMI-Primary to Vlan-20: {e}")
    try:
        lab.create_link("Vlan-20", "Ethernet7", "Ignition-Switch", "Ethernet1")
    except Exception as e:
        print(f"Error linking Vlan-20 to Ignition-Switch: {e}")
    try:
        lab.create_link("Vlan-20", "Ethernet2", "scada-server", "eth1")
    except Exception as e:
        print(f"Error linking Vlan-20 to scada-server: {e}")

    # --- Distribution Vlan-30 Segment ---
    try:
        lab.create_link("PLC-Aeration", "eth1", "Vlan-30", "Ethernet2")
    except Exception as e:
        print(f"Error linking PLC-Aeration to Vlan-30: {e}")
    try:
        lab.create_link("Vlan-30", "Ethernet3", "HMI-Aeration", "Eth0")
    except Exception as e:
        print(f"Error linking HMI-Aeration to Vlan-30: {e}")
    try:
        lab.create_link("Vlan-30", "Ethernet0", "Ignition-Switch", "Ethernet2")
    except Exception as e:
        print(f"Error linking Vlan-30 to Ignition-Switch: {e}")
    try:
        lab.create_link("Vlan-30", "Ethernet1", "scada-server", "eth2")
    except Exception as e:
        print(f"Error linking Vlan-30 to scada-server: {e}")

    # --- Distribution Vlan-40 Segment ---
    try:
        lab.create_link("PLC-Clarification", "eth1", "Vlan-40", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Clarification to Vlan-40: {e}")
    try:
        lab.create_link("Vlan-40", "Ethernet3", "HMI-Clarification", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-40 to HMI-Clarification: {e}")
    try:
        lab.create_link("Ignition-Switch", "Ethernet3", "Vlan-40", "Ethernet1")
    except Exception as e:
        print(f"Error linking Ignition-Switch to Vlan-40: {e}")
    try:
        lab.create_link("Vlan-40", "Ethernet2", "scada-server", "eth3")
    except Exception as e:
        print(f"Error linking Vlan-40 to scada-server: {e}")

    # --- Distribution Vlan-50 Segment ---
    try:
        lab.create_link("PLC-Disenfection", "eth1", "Vlan-50", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Disenfection to Vlan-50: {e}")
    try:
        lab.create_link("HMI-Disenfection", "eth0", "Vlan-50", "Ethernet1")
    except Exception as e:
        print(f"Error linking HMI-Disenfection to Vlan-50: {e}")
    try:
        lab.create_link("Vlan-50", "Ethernet6", "Ignition-Switch", "Ethernet6")
    except Exception as e:
        print(f"Error linking Vlan-50 to Ignition-Switch: {e}")
    try:
        lab.create_link("Vlan-50", "Ethernet7", "scada-server", "eth4")
    except Exception as e:
        print(f"Error linking Vlan-50 to scada-server: {e}")

    # --- Distribution Vlan-60 Segment ---
    try:
        lab.create_link("PLC-Thickening", "eth1", "Vlan-60", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Thickening to Vlan-60: {e}")
    try:
        lab.create_link("HMI-Thickening", "eth0", "Vlan-60", "Ethernet2")
    except Exception as e:
        print(f"Error linking HMI-Thickening to Vlan-60: {e}")
    try:
        lab.create_link("Vlan-60", "Ethernet7", "Ignition-Switch", "Ethernet4")
    except Exception as e:
        print(f"Error linking Vlan-60 to Ignition-Switch: {e}")
    try:
        lab.create_link("Vlan-60", "Ethernet3", "scada-server", "eth5")
    except Exception as e:
        print(f"Error linking Vlan-60 to scada-server: {e}")

    # --- Distribution Vlan-70 Segment ---
    try:
        lab.create_link("PLC-Digestion", "eth1", "Vlan-70", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Digestion to Vlan-70: {e}")
    try:
        lab.create_link("HMI-Digestion", "eth0", "Vlan-70", "Ethernet5")
    except Exception as e:
        print(f"Error linking HMI-Digestion to Vlan-70: {e}")
    try:
        lab.create_link("Ignition-Switch", "Ethernet5", "Vlan-70", "Ethernet7")
    except Exception as e:
        print(f"Error linking Ignition-Switch to Vlan-70: {e}")
    try:
        lab.create_link("Vlan-70", "Ethernet6", "scada-server", "eth6")
    except Exception as e:
        print(f"Error linking Vlan-70 to scada-server: {e}")

    # --- Bottom Vlan-05 Segment ---
    try:
        lab.create_link("PLC-Disenfection", "eth0", "Vlan-05", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Disenfection to Vlan-05: {e}")
    try:
        lab.create_link("Vlan-05", "Ethernet1", "CL-501", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-05 to CL-501: {e}")
    try:
        lab.create_link("Vlan-05", "Ethernet2", "FT-501", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-05 to FT-501: {e}")
    try:
        lab.create_link("Vlan-05", "Ethernet3", "LT-501", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-05 to LT-501: {e}")
    try:
        lab.create_link("Vlan-05", "Ethernet4", "AV-501", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-05 to AV-501: {e}")

    # --- Bottom Vlan-06 Segment ---
    try:
        lab.create_link("PLC-Thickening", "eth0", "Vlan-06", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Thickening to Vlan-06: {e}")
    try:
        lab.create_link("Vlan-06", "Ethernet1", "LT-601", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-06 to LT-601: {e}")
    try:
        lab.create_link("Vlan-06", "Ethernet2", "FT-601", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-06 to FT-601: {e}")
    try:
        lab.create_link("Vlan-06", "Ethernet3", "SS-601", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-06 to SS-601: {e}")
    try:
        lab.create_link("Vlan-06", "Ethernet4", "P-601", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-06 to P-601: {e}")

    # --- Bottom Vlan-07 Segment ---
    try:
        lab.create_link("PLC-Digestion", "eth0", "Vlan-07", "Ethernet0")
    except Exception as e:
        print(f"Error linking PLC-Digestion to Vlan-07: {e}")
    try:
        lab.create_link("Vlan-07", "Ethernet1", "T-701", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-07 to T-701: {e}")
    try:
        lab.create_link("Vlan-07", "Ethernet2", "PT-701", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-07 to PT-701: {e}")
    try:
        lab.create_link("Vlan-07", "Ethernet3", "FT-701", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-07 to FT-701: {e}")
    try:
        lab.create_link("Vlan-07", "Ethernet4", "GAS-701", "eth0")
    except Exception as e:
        print(f"Error linking Vlan-07 to GAS-701: {e}")

    # --- Core / Outer Edge Devices ---
    try:
        lab.create_link("Ignition-Switch", "Ethernet7", "ignition-1", "eth0")
    except Exception as e:
        print(f"Error linking Ignition-Switch to ignition-1: {e}")
    try:
        lab.create_link("scada-server", "eth7", "KaliLinux-1", "Ethernet0")
    except Exception as e:
        print(f"Error linking scada-server to KaliLinux-1: {e}")


    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
