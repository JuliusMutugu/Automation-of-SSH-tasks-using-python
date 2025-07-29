#!/usr/bin/env python3
"""
Check router interface status and fix SSH connectivity
"""

from netmiko import ConnectHandler
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_and_fix_interfaces():
    """Check router interfaces via console and fix if needed"""
    
    routers = [
        {'name': 'R1', 'host': '127.0.0.1', 'port': 5000, 'target_ip': '192.168.1.1'},
        {'name': 'R2', 'host': '127.0.0.1', 'port': 5008, 'target_ip': '192.168.1.2'}
    ]
    
    for router in routers:
        console_device = {
            'device_type': 'cisco_ios_telnet',
            'host': router['host'],
            'port': router['port'],
            'username': '',
            'password': '',
            'secret': '',
            'timeout': 30,
            'global_delay_factor': 2
        }
        
        try:
            print(f"\n--- Checking {router['name']} via console ---")
            connection = ConnectHandler(**console_device)
            
            # Check interface status
            print("📋 Current interface status:")
            ip_brief = connection.send_command('show ip interface brief')
            print(ip_brief)
            
            # Check if FastEthernet0/0 has the correct IP
            lines = ip_brief.split('\n')
            fe00_found = False
            fe00_up = False
            
            for line in lines:
                if 'FastEthernet0/0' in line:
                    fe00_found = True
                    parts = line.split()
                    if len(parts) >= 5:
                        ip = parts[1]
                        status = parts[4]
                        protocol = parts[5]
                        
                        print(f"FastEthernet0/0: IP={ip}, Status={status}, Protocol={protocol}")
                        
                        if ip == router['target_ip'] and status == 'up' and protocol == 'up':
                            fe00_up = True
                            print(f"✅ Interface is properly configured and up")
                        else:
                            print(f"⚠️  Interface needs configuration")
            
            if not fe00_found or not fe00_up:
                print(f"🔧 Fixing interface configuration...")
                
                # Configure interface
                config_commands = [
                    'configure terminal',
                    'interface fastethernet0/0',
                    f'ip address {router["target_ip"]} 255.255.255.0',
                    'no shutdown',
                    'exit',
                    'exit'
                ]
                
                for cmd in config_commands:
                    print(f"Executing: {cmd}")
                    output = connection.send_command_timing(cmd, delay_factor=2)
                    time.sleep(1)
                
                # Save configuration
                save_output = connection.send_command('write memory')
                print(f"Configuration saved: {save_output}")
                
                # Wait a moment for interface to come up
                time.sleep(3)
                
                # Check again
                ip_brief = connection.send_command('show ip interface brief')
                print("📋 Updated interface status:")
                print(ip_brief)
            
            # Test SSH connectivity from router to verify it's working
            print(f"🔍 Testing SSH server status...")
            ssh_status = connection.send_command('show ip ssh')
            print(f"SSH Status:\n{ssh_status}")
            
            connection.disconnect()
            
        except Exception as e:
            print(f"❌ Error checking {router['name']}: {str(e)}")

if __name__ == "__main__":
    print("=== Router Interface Check and Fix ===")
    check_and_fix_interfaces()
