#!/usr/bin/env python3
"""
SSH Verification Script - Run this after manual configuration
"""

import socket
from netmiko import ConnectHandler

def verify_ssh_configuration():
    router_ip = "192.168.100.10"
    username = "admin"
    password = "password123"
    
    print(f"Testing SSH connection to {router_ip}...")
    
    # Test port 22 connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((router_ip, 22))
        sock.close()
        
        if result == 0:
            print("SUCCESS: SSH port 22 is accessible")
            
            # Test SSH authentication
            try:
                device = {
                    'device_type': 'cisco_ios',
                    'host': router_ip,
                    'username': username,
                    'password': password,
                    'secret': password,
                    'timeout': 15
                }
                
                connection = ConnectHandler(**device)
                connection.enable()
                
                # Get device information
                version = connection.send_command('show version | include uptime')
                interfaces = connection.send_command('show ip interface brief')
                ssh_status = connection.send_command('show ip ssh')
                
                connection.disconnect()
                
                print("SUCCESS: SSH authentication successful!")
                print(f"Router info: {version.strip()}")
                print(f"SSH status: {ssh_status.strip()}")
                print("\nInterface status:")
                print(interfaces)
                
                print("\nSUCCESS: SSH configuration is working correctly!")
                print("You can now run the automation scripts.")
                return True
                
            except Exception as e:
                print(f"ERROR: SSH authentication failed: {e}")
                print("Please check username/password and try manual SSH test")
                return False
        else:
            print("ERROR: SSH port 22 is not accessible")
            print("Please verify router configuration and network connectivity")
            return False
            
    except Exception as e:
        print(f"Error testing connectivity: {e}")
        return False

if __name__ == "__main__":
    print("SSH Configuration Verification")
    print("="*40)
    verify_ssh_configuration()
