 --- Client-00 startup config ---
hostname Client-00
no ip domain-lookup
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
ip dhcp excluded-address 192.168.1.1 192.168.1.10
ip dhcp pool MY_LAN_POOL
 network 192.168.1.0 255.255.255.0
 default-router 192.168.1.1
end
copy run start

#You will also need to set the webgoat IP address to 192.168.1.100, and give students the URL of 192.168.1.100:8080/WebGoat to use in Kali.
