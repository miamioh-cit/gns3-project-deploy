MODULE 3 — AUTHORIZED MODBUS WRITE

This GNS3 config disk contains the only client used for the Module 3 activity.

1. Start Wireshark (or tcpdump) first if packet evidence is required.
2. Open a terminal in this folder.
3. Run:

   sudo bash module3_launch.sh

4. Enter the Kali account password when asked.

The launcher configures this Kali VM as 172.16.0.250/24 for the current
lab session, then sends exactly one approved request:

  PLC-US35 (172.16.0.3:502), Unit 2
  Function code 06 (Write Single Register)
  Register 3 = 1

It does not accept alternate targets, registers, or values.
