#!/usr/bin/env python3
"""
Router Status Checker and Manual SSH Guide
"""

import socket
import time
import requests

def check_router_console_status():
    """Check what's actually happening on the router console"""
    
    console_ports = [5000, 5008]  # R1 and R2
    
    for port in console_ports:
        print(f"\n📡 Checking router on console port {port}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('localhost', port))
            
            print(f"   ✅ Console port {port} is accessible")
            
            # Send show commands to check status
            commands = [
                '',
                'show ip interface brief',
                'show ip ssh',
                'show running-config | include username'
            ]
            
            for cmd in commands:
                sock.send((cmd + '\n').encode())
                time.sleep(2)
                
                try:
                    response = sock.recv(2048).decode('utf-8', errors='ignore')
                    if cmd and response.strip():
                        print(f"   Command '{cmd}':")
                        print(f"   Response: {response.strip()[:200]}...")
                except:
                    pass
            
            sock.close()
            
        except Exception as e:
            print(f"   ❌ Cannot connect to console port {port}: {e}")

def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n🌐 Testing network connectivity...")
    
    test_ips = ['192.168.100.10', '192.168.100.11', '127.0.0.1']
    
    for ip in test_ips:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, 80))  # Test any port
            sock.close()
            
            if result == 0 or ip == '127.0.0.1':
                print(f"   ✅ Network route to {ip} exists")
            else:
                print(f"   ❌ No network route to {ip}")
                
        except Exception as e:
            print(f"   ❌ Network test failed for {ip}: {e}")

def create_manual_configuration_file():
    """Create a file with manual configuration steps"""
    
    config_content = """
MANUAL SSH CONFIGURATION FOR ROUTERS
====================================

If automatic configuration didn't work, follow these steps manually:

STEP 1: Open GNS3 Console
-------------------------
1. Open GNS3
2. Right-click on R1 router
3. Select "Console"
4. Press ENTER to get prompt

STEP 2: Configure R1 Router
---------------------------
Copy and paste these commands one by one:

enable
configure terminal
hostname R1
ip domain-name cisco.local
username admin privilege 15 secret password123
crypto key generate rsa modulus 1024
(Press 'yes' when prompted)
ip ssh version 2
line vty 0 4
transport input ssh
login local
exit
interface FastEthernet0/0
ip address 192.168.100.10 255.255.255.0
no shutdown
exit
exit
write memory

STEP 3: Verify Configuration
----------------------------
show ip interface brief
show ip ssh
ping 192.168.100.10

STEP 4: Test SSH
----------------
From Windows Command Prompt:
ssh admin@192.168.100.10
(Password: password123)

STEP 5: Configure R2 (Optional)
-------------------------------
Repeat steps 1-4 for R2 router with:
- Console: Right-click R2 → Console  
- IP Address: 192.168.100.11

TROUBLESHOOTING
--------------
1. If interface shows "down/down":
   - Check GNS3 topology connections
   - Verify interface is connected to a switch/cloud

2. If SSH port not accessible:
   - Wait 2-3 minutes after configuration
   - Check firewall settings
   - Verify IP address with 'show ip interface brief'

3. If authentication fails:
   - Verify username: admin
   - Verify password: password123
   - Check with 'show running-config | include username'
"""
    
    with open('manual_ssh_config.txt', 'w') as f:
        f.write(config_content)
    
    print("📝 Created manual_ssh_config.txt with detailed instructions")

def quick_ssh_retest():
    """Quick test to see if SSH is working now"""
    print("\n🔄 Quick SSH retest...")
    
    test_configs = [
        {'ip': '192.168.100.10', 'user': 'admin', 'pass': 'password123'},
        {'ip': '192.168.100.11', 'user': 'admin', 'pass': 'password123'},
        {'ip': '192.168.1.1', 'user': 'admin', 'pass': 'password123'},
    ]
    
    working_devices = []
    
    for config in test_configs:
        try:
            # Test port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((config['ip'], 22))
            sock.close()
            
            if result == 0:
                print(f"   ✅ SSH port open on {config['ip']}")
                
                # Test auth
                try:
                    from netmiko import ConnectHandler
                    device = {
                        'device_type': 'cisco_ios',
                        'host': config['ip'],
                        'username': config['user'],
                        'password': config['pass'],
                        'secret': config['pass'],
                        'timeout': 10
                    }
                    
                    connection = ConnectHandler(**device)
                    hostname = connection.send_command('show version | include uptime')
                    connection.disconnect()
                    
                    print(f"   🎉 SSH SUCCESS: {config['ip']} with {config['user']}:{config['pass']}")
                    working_devices.append(config)
                    
                except Exception as e:
                    print(f"   ❌ SSH auth failed: {e}")
            else:
                print(f"   ❌ SSH port closed on {config['ip']}")
                
        except Exception as e:
            print(f"   ❌ Error testing {config['ip']}: {e}")
    
    return working_devices

def main():
    print("=" * 60)
    print("ROUTER STATUS CHECK AND SSH TROUBLESHOOTING")
    print("=" * 60)
    
    # Check current router status
    check_router_console_status()
    
    # Test network connectivity
    test_network_connectivity()
    
    # Quick SSH test
    working_devices = quick_ssh_retest()
    
    if working_devices:
        print(f"\n🎉 Found {len(working_devices)} working SSH devices!")
        for device in working_devices:
            print(f"   {device['ip']} - {device['user']}:{device['pass']}")
        print("\n✅ SSH is working! You can now run: python enable_new.py")
    else:
        print("\n❌ SSH still not working")
        create_manual_configuration_file()
        print("\n📖 Next steps:")
        print("1. Check manual_ssh_config.txt for detailed instructions")
        print("2. Configure SSH manually through GNS3 console")
        print("3. Run this script again to test")

if __name__ == "__main__":
    main()
