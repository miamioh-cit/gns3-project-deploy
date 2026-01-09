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

#You will also need to give students the URL of 192.168.1.200:8080/WebGoat to use in Kali AFTER you have pasted in this Interface Configuration on Client-05...
##################################
auto eth0

iface eth0 inet static

	address 192.168.1.200
	
	netmask 255.255.255.0
	
	gateway 192.168.1.1
	
	up echo nameserver 192.168.1.1 > /etc/resolv.conf
