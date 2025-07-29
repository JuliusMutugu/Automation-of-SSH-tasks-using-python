#!/usr/bin/env python3
"""
Quick SSH Test - Check if router already has SSH configured
"""

import socket
import time
from netmiko import ConnectHandler

def quick_ssh_test():
    # Test configurations that might already be working
    test_configs = [
        {'ip': '192.168.100.10', 'user': 'admin', 'pass': 'password123'},
        {'ip': '192.168.1.1', 'user': 'admin', 'pass': 'password123'},
        {'ip': '192.168.100.10', 'user': 'admin', 'pass': 'admin'},
        {'ip': '192.168.1.1', 'user': 'admin', 'pass': 'admin'},
        {'ip': '192.168.100.10', 'user': 'cisco', 'pass': 'cisco'},
        {'ip': '192.168.1.1', 'user': 'cisco', 'pass': 'cisco'},
        {'ip': '192.168.100.1', 'user': 'admin', 'pass': 'password123'},
        {'ip': '10.0.0.1', 'user': 'admin', 'pass': 'password123'},
    ]
    
    print("Testing for existing SSH configuration...")
    
    for config in test_configs:
        print(f"\nTesting {config['ip']} with {config['user']}:{config['pass']}")
        
        # First test if port 22 is open
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((config['ip'], 22))
            sock.close()
            
            if result == 0:
                print(f"  ✓ SSH port 22 is open on {config['ip']}")
                
                # Now try SSH authentication
                try:
                    device = {
                        'device_type': 'cisco_ios',
                        'host': config['ip'],
                        'username': config['user'],
                        'password': config['pass'],
                        'secret': config['pass'],
                        'timeout': 10,
                        'global_delay_factor': 1
                    }
                    
                    print(f"  Attempting SSH authentication...")
                    connection = ConnectHandler(**device)
                    connection.enable()
                    
                    # Get device info
                    hostname = connection.send_command('show version | include uptime')
                    interfaces = connection.send_command('show ip interface brief')
                    ssh_info = connection.send_command('show ip ssh')
                    
                    connection.disconnect()
                    
                    print(f"  ✅ SSH SUCCESS!")
                    print(f"  IP: {config['ip']}")
                    print(f"  Username: {config['user']}")
                    print(f"  Password: {config['pass']}")
                    print(f"  Hostname: {hostname.strip()}")
                    print(f"  SSH Info: {ssh_info.strip()[:100]}")
                    print(f"  Interfaces:")
                    print(f"  {interfaces}")
                    
                    return config['ip'], config['user'], config['pass']
                    
                except Exception as e:
                    print(f"  ❌ SSH authentication failed: {e}")
            else:
                print(f"  ✗ SSH port 22 not accessible on {config['ip']}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n❌ No working SSH configuration found")
    return None, None, None

if __name__ == "__main__":
    print("Quick SSH Configuration Test")
    print("="*40)
    
    ip, user, password = quick_ssh_test()
    
    if ip:
        print(f"\n🎉 Found working SSH configuration!")
        print(f"Router IP: {ip}")
        print(f"Username: {user}")
        print(f"Password: {password}")
        print(f"\nCommand to connect: ssh {user}@{ip}")
        print("\n✅ You can now run the automation scripts!")
    else:
        print("\n🔧 No SSH found. Router may need manual configuration through GNS3 console.")
        print("Right-click the router in GNS3 and select 'Console' to configure manually.")
