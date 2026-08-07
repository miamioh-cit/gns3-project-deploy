import logging
from gns3fy import Gns3Connector, Project, Node, Link

LAB_NAME = "480-Test"

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

    lab.create_node(name='H-101', template='generic-sensor', x=-575, y=-625)
    sw1 = lab.get_node("H-101")
    sw1.start()

    lab.create_node(name='LT-101', template='generic-sensor', x=-483, y=-628)
    sw2 = lab.get_node("LT-101")
    sw2.start()

    lab.create_node(name='DP-101', template='generic-sensor', x=-380, y=-619)
    sw3 = lab.get_node("DP-101")
    sw3.start()

    lab.create_node(name='P-101', template='generic-sensor', x=-299, y=-623)
    sw4 = lab.get_node("P-101")
    sw4.start()

    lab.create_node(name='FT-201', template='generic-sensor', x=-194, y=-627)
    sw5 = lab.get_node("FT-201")
    sw5.start()

    lab.create_node(name='LT-201', template='generic-sensor', x=-109, y=-632)
    sw6 = lab.get_node("LT-201")
    sw6.start()

    lab.create_node(name='DP-201', template='generic-sensor', x=-25, y=-618)
    sw7 = lab.get_node("DP-201")
    sw7.start()

    lab.create_node(name='MV-201', template='generic-sensor', x=58, y=-620)
    sw8 = lab.get_node("MV-201")
    sw8.start()

    lab.create_node(name='DO-301', template='generic-sensor', x=177, y=-606)
    sw9 = lab.get_node("DO-301")
    sw9.start()

    lab.create_node(name='FT-301', template='generic-sensor', x=254, y=-606)
    sw10 = lab.get_node("FT-301")
    sw10.start()

    lab.create_node(name='MLSS-301', template='generic-sensor', x=330, y=-599)
    sw11 = lab.get_node("MLSS-301")
    sw11.start()

    lab.create_node(name='SV-301', template='generic-sensor', x=406, y=-604)
    sw12 = lab.get_node("SV-301")
    sw12.start()

    lab.create_node(name='FT-401', template='generic-sensor', x=596, y=-578)
    sw13 = lab.get_node("FT-401")
    sw13.start()

    lab.create_node(name='LT-401', template='generic-sensor', x=687, y=-575)
    sw14 = lab.get_node("LT-401")
    sw14.start()

    lab.create_node(name='TU-401', template='generic-sensor', x=786, y=-577)
    sw15 = lab.get_node("TU-401")
    sw15.start()

    lab.create_node(name='DL-401', template='generic-sensor', x=892, y=-575)
    sw16 = lab.get_node("DL-401")
    sw16.start()

    lab.create_node(name='Vlan-01', template='Ethernet switch', x=-424, y=-476)
    vlan1 = lab.get_node("Vlan-01")
    vlan1.start()

    lab.create_node(name='Vlan-02', template='Ethernet switch', x=-81, y=-504)
    vlan2 = lab.get_node("Vlan-02")
    vlan2.start()

    lab.create_node(name='Vlan-03', template='Ethernet switch', x=307, y=-467)
    vlan3 = lab.get_node("Vlan-03")
    vlan3.start()

    lab.create_node(name='Vlan-04', template='Ethernet switch', x=741, y=-474)
    vlan4 = lab.get_node("Vlan-04")
    vlan4.start()

    lab.create_node(name='HMI-Influent', template='generic-hmi', x=-549, y=-316)
    HMI1 = lab.get_node("HMI-Influent")
    HMI1.start()

    lab.create_node(name='PLC-Influent', template='generic-plc', x=-419, y=-367)
    PLC1 = lab.get_node("PLC-Influent")
    PLC1.start()

    lab.create_node(name='HMI-Primary', template='generic-hmi', x=-234, y=-362)
    HMI2 = lab.get_node("HMI-Primary")
    HMI2.start()

    lab.create_node(name='PLC-Primary', template='generic-plc', x=-76, y=-364)
    PLC2 = lab.get_node("PLC-Primary")
    PLC2.start()

    lab.create_node(name='HMI-Aeration', template='generic-hmi', x=184, y=-365)
    HMI3 = lab.get_node("HMI-Aeration")
    HMI3.start()

    lab.create_node(name='PLC-Aeration', template='generic-plc', x=312, y=-356)
    PLC3 = lab.get_node("PLC-Aeration")
    PLC3.start()

    lab.create_node(name='HMI-Clarification', template='generic-hmi', x=598, y=-325)
    HMI4 = lab.get_node("HMI-Clarification")
    HMI4.start()

    lab.create_node(name='PLC-Clarification', template='generic-plc', x=746, y=-340)
    PLC4 = lab.get_node("PLC-Clarification")
    PLC4.start()

    lab.create_node(name='Vlan-10', template='Ethernet switch', x=-511, y=-199)
    Vlan10 = lab.get_node("Vlan-10")
    Vlan10.start()

    lab.create_node(name='Vlan-20', template='Ethernet switch', x=-146, y=-243)
    Vlan20 = lab.get_node("Vlan-20")
    Vlan20.start()

    lab.create_node(name='Vlan-30', template='Ethernet switch', x=236, y=-225)
    Vlan30 = lab.get_node("Vlan-30")
    Vlan30.start()

    lab.create_node(name='Vlan-40', template='Ethernet switch', x=562, y=-196)
    Vlan40 = lab.get_node("Vlan-40")
    Vlan40.start()

    lab.create_node(name='Ignition-Switch', template='Ethernet switch', x=-414, y=-41)
    sw17 = lab.get_node("Ignition-Switch")
    sw17.start()

    lab.create_node(name='scada-server', template='generic-scada', x=135, y=-54)
    scada = lab.get_node("scada-server")
    scada.start()

    lab.create_node(name='KaliLinux-1', template='Kali Linux', x=662, y=-48)
    KL = lab.get_node("KaliLinux-1")
    KL.start()

    lab.create_node(name='ignition-1', template='ignition', x=-632, y=61)
    sw18 = lab.get_node("ignition-1")
    sw18.start()

    lab.create_node(name='Vlan-50', template='Ethernet switch', x=-412, y=99)
    Vlan50 = lab.get_node("Vlan-50")
    Vlan50.start()

    lab.create_node(name='Vlan-60', template='Ethernet switch', x=-4, y=98)
    Vlan60 = lab.get_node("Vlan-60")
    Vlan60.start()

    lab.create_node(name='Vlan-70', template='Ethernet switch', x=460, y=92)
    Vlan70 = lab.get_node("Vlan-70")
    Vlan70.start()

    lab.create_node(name='HMI-Disenfection', template='generic-hmi', x=-566, y=-180)
    HMI5 = lab.get_node("HMI-Disenfection")
    HMI5.start()

    lab.create_node(name='PLC-Disenfection', template='generic-plc', x=-408, y=194)
    PLC5 = lab.get_node("PLC-Disenfection")
    PLC5.start()

    lab.create_node(name='HMI-Thickening', template='generic-hmi', x=-154, y=218)
    HMI6 = lab.get_node("HMI-Thickening")
    HMI6.start()

    lab.create_node(name='PLC-Thickening', template='generic-plc', x=-5, y=203)
    PLC6 = lab.get_node("PLC-Thickening")
    PLC6.start()

    lab.create_node(name='HMI-Digestion', template='generic-hmi', x=280, y=166)
    HMI7 = lab.get_node("HMI-Digestion")
    HMI7.start()

    lab.create_node(name='PLC-Digestion', template='generic-plc', x=467, y=189)
    PLC7 = lab.get_node("PLC-Digestion")
    PLC7.start()

    lab.create_node(name='Vlan-05', template='Ethernet switch', x=-410, y=317)
    Vlan05 = lab.get_node("Vlan-05")
    Vlan05.start()

    lab.create_node(name='Vlan-06', template='Ethernet switch', x=-8, y=306)
    Vlan06 = lab.get_node("Vlan-06")
    Vlan06.start()

    lab.create_node(name='Vlan-07', template='Ethernet switch', x=482, y=325)
    Vlan07 = lab.get_node("Vlan-07")
    Vlan07.start()

    lab.create_node(name='CL-501', template='generic-sensor', x=-564, y=402)
    sw19 = lab.get_node("CL-501")
    sw19.start()

    lab.create_node(name='FT-501', template='generic-sensor', x=-474, y=403)
    sw20 = lab.get_node("FT-501")
    sw20.start()

    lab.create_node(name='LT-501', template='generic-sensor', x=-325, y=402)
    sw21 = lab.get_node("LT-501")
    sw21.start()

    lab.create_node(name='AV-501', template='generic-sensor', x=-231, y=402)
    sw22 = lab.get_node("AV-501")
    sw22.start()

    lab.create_node(name='LT-601', template='generic-sensor', x=-107, y=398)
    sw23 = lab.get_node("LT-601")
    sw23.start()

    lab.create_node(name='FT-601', template='generic-sensor', x=-24, y=397)
    sw24 = lab.get_node("FT-601")
    sw24.start()

    lab.create_node(name='SS-601', template='generic-sensor', x=63, y=396)
    sw25 = lab.get_node("SS-601")
    sw25.start()

    lab.create_node(name='P-601', template='generic-sensor', x=154, y=394)
    sw26 = lab.get_node("P-601")
    sw26.start()

    lab.create_node(name='T-701', template='generic-sensor', x=344, y=410)
    sw27 = lab.get_node("T-701")
    sw27.start()

    lab.create_node(name='PT-701', template='generic-sensor', x=442, y=412)
    sw28 = lab.get_node("PT-701")
    sw28.start()

    lab.create_node(name='FT-701', template='generic-sensor', x=548, y=410)
    sw29 = lab.get_node("FT-701")
    sw29.start()

    lab.create_node(name='GAS-701', template='generic-sensor', x=647, y=412)
    sw30 = lab.get_node("GAS-701")
    sw30.start()


# --- Top Vlan-01 Segment ---
    lab.create_link("PLC-Influent", "eth0", "Vlan-01", "e0")
    lab.create_link("FT-101", "eth0", "Vlan-01", "Ethernet1")
    lab.create_link("LT-101", "eth0", "Vlan-01", "Ethernet2")
    lab.create_link("DP-101", "eth0", "Vlan-01", "Ethernet3")
    lab.create_link("P-101", "eth0", "Vlan-01", "Ethernet4")

    # --- Top Vlan-02 Segment ---
    lab.create_link("PLC-Primary", "eth0", "Vlan-02", "Ethernet0")
    lab.create_link("FT-201", "eth0", "Vlan-02", "Ethernet1")
    lab.create_link("LT-201", "eth0", "Vlan-02", "Ethernet2")
    lab.create_link("DP-201", "eth0", "Vlan-02", "Ethernet3")
    lab.create_link("MV-201", "eth0", "Vlan-02", "Ethernet4")

    # --- Top Vlan-03 Segment ---
    lab.create_link("PLC-Aeration", "eth0", "Vlan-03", "Ethernet0")
    lab.create_link("DO-301", "eth0", "Vlan-03", "Ethernet1")
    lab.create_link("FT-301", "eth0", "Vlan-03", "Ethernet2")
    lab.create_link("MLSS-301", "eth0", "Vlan-03", "Ethernet3")
    lab.create_link("SV-301", "eth0", "Vlan-03", "Ethernet")

    # --- Top Vlan-04 Segment ---
    lab.create_link("PLC-Clarification", "eth0", "Vlan-04", "Ethernet0")
    lab.create_link("FT-401", "eth0", "Vlan-04", "Ethernet1")
    lab.create_link("LT-401", "eth0", "Vlan-04", "Ethernet2")
    lab.create_link("TU-401", "eth0", "Vlan-04", "Ethernet3")
    lab.create_link("DL-401", "eth0", "Vlan-04", "Ethernet4")

    # --- Distribution Vlan-10 Segment ---
    lab.create_link("PLC-Influent", "eth1", "Vlan-10", "Ethernet0")
    lab.create_link("HMI-Influent", "eth0", "Vlan-10", "Ethernet1")
    lab.create_link("Vlan-10", "e2", "Ignition-Switch", "Ethernet0")
    lab.create_link("Vlan-10", "e3", "scada-server", "eth0")

    # --- Distribution Vlan-20 Segment ---
    lab.create_link("PLC-Primary", "eth1", "Vlan-20", "Ethernet0")
    lab.create_link("HMI-Primary", "eth0", "Vlan-20", "Ethernet1")
    lab.create_link("Vlan-20", "e2", "Ignition-Switch", "Ethernet1")
    lab.create_link("Vlan-20", "e3", "scada-server", "eth1")

    # --- Distribution Vlan-30 Segment ---
    lab.create_link("PLC-Aeration", "eth1", "Vlan-30", "Ethernet0")
    lab.create_link("HMI-Aeration", "eth0", "Vlan-30", "Ethernet1")
    lab.create_link("Vlan-30", "e2", "Ignition-Switch", "Ethernet2")
    lab.create_link("Vlan-30", "e3", "scada-server", "eth2")

    # --- Distribution Vlan-40 Segment ---
    lab.create_link("PLC-Clarification", "eth1", "Vlan-40", "Ethernet0")
    lab.create_link("HMI-Clarification", "eth0", "Vlan-40", "Ethernet1")
    lab.create_link("Vlan-40", "e2", "Ignition-Switch", "Ethernet3")
    lab.create_link("Vlan-40", "e3", "scada-server", "eth3")

    # --- Distribution Vlan-50 Segment ---
    lab.create_link("PLC-Disenfection", "eth1", "Vlan-50", "Ethernet0")
    lab.create_link("HMI-Disenfection", "eth0", "Vlan-50", "Ethernet1")
    lab.create_link("Vlan-50", "e2", "Ignition-Switch", "Ethernet4")
    lab.create_link("Vlan-50", "e3", "scada-server", "eth4")

    # --- Distribution Vlan-60 Segment ---
    lab.create_link("PLC-Thickening", "eth1", "Vlan-60", "Ethernet0")
    lab.create_link("HMI-Thickening", "eth0", "Vlan-60", "Ethernet1")
    lab.create_link("Vlan-60", "e2", "Ignition-Switch", "Ethernet5")
    lab.create_link("Vlan-60", "e3", "scada-server", "eth5")

    # --- Distribution Vlan-70 Segment ---
    lab.create_link("PLC-Digestion", "eth1", "Vlan-70", "Ethernet0")
    lab.create_link("HMI-Digestion", "eth0", "Vlan-70", "Ethernet1")
    lab.create_link("Vlan-70", "e2", "Ignition-Switch", "Ethernet6")
    lab.create_link("Vlan-70", "e3", "scada-server", "eth6")

    # --- Bottom Vlan-05 Segment ---
    lab.create_link("PLC-Disenfection", "eth0", "Vlan-05", "Ethernet0")
    lab.create_link("CL-501", "eth0", "Vlan-05", "Ethernet1")
    lab.create_link("FT-501", "eth0", "Vlan-05", "Ethernet2")
    lab.create_link("LT-501", "eth0", "Vlan-05", "Ethernet3")
    lab.create_link("AV-501", "eth0", "Vlan-05", "Ethernet4")

    # --- Bottom Vlan-06 Segment ---
    lab.create_link("PLC-Thickening", "eth0", "Vlan-06", "Ethernet0")
    lab.create_link("LT-601", "eth0", "Vlan-06", "Ethernet1")
    lab.create_link("FT-601", "eth0", "Vlan-06", "Ethernet2")
    lab.create_link("SS-601", "eth0", "Vlan-06", "Ethernet3")
    lab.create_link("P-601", "eth0", "Vlan-06", "Ethernet4")

    # --- Bottom Vlan-07 Segment ---
    lab.create_link("PLC-Digestion", "eth0", "Vlan-07", "Ethernet0")
    lab.create_link("T-701", "eth0", "Vlan-07", "Ethernet1")
    lab.create_link("PT-701", "eth0", "Vlan-07", "Ethernet2")
    lab.create_link("FT-701", "eth0", "Vlan-07", "Ethernet3")
    lab.create_link("GAS-701", "eth0", "Vlan-07", "Ethernet4")

    # --- Core / Outer Edge Devices ---
    lab.create_link("Ignition-Switch", "e7", "ignition-1", "eth0")
    lab.create_link("scada-server", "eth7", "KaliLinux-1", "eth0")




    


    


    

    print("-----------------------------------------------------------------------")
    print("Nodes created, started and linked. Here are the links:")
    print("-----------------------------------------------------------------------")
    lab.links_summary()
    print("-----------------------------------------------------------------------")
    print(LAB_NAME + f" build is Complete on {SERVER_URL}. It is now safe to open the project in GNS3")
