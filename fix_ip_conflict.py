#!/usr/bin/env python3
"""
Reconfigure router IP addresses to avoid conflicts
"""

from netmiko import ConnectHandler
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def reconfigure_router_ips():
    """Reconfigure router IPs to avoid network conflicts"""
    
    routers = [
        {'name': 'R1', 'host': '127.0.0.1', 'port': 5000, 'new_ip': '192.168.1.10'},
        {'name': 'R2', 'host': '127.0.0.1', 'port': 5008, 'new_ip': '192.168.1.20'}
    ]
    
    updated_devices = []
    
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
            print(f"\n--- Reconfiguring {router['name']} with IP {router['new_ip']} ---")
            connection = ConnectHandler(**console_device)
            
            # Configure new IP address
            config_commands = [
                'configure terminal',
                'interface fastethernet0/0',
                f'ip address {router["new_ip"]} 255.255.255.0',
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
            
            # Wait for interface to come up
            time.sleep(3)
            
            # Verify new configuration
            ip_brief = connection.send_command('show ip interface brief')
            print(f"📋 Updated interface status:\n{ip_brief}")
            
            connection.disconnect()
            
            updated_devices.append({
                'device_type': 'cisco_ios',
                'fast_cli': False,
                'global_delay_factor': 2,
                'host': router['new_ip'],
                'name': router['name'],
                'password': 'cisco123',
                'port': 22,
                'secret': 'enable123',
                'timeout': 30,
                'username': 'admin'
            })
            
            print(f"✅ {router['name']} reconfigured successfully with IP {router['new_ip']}")
            
        except Exception as e:
            print(f"❌ Error reconfiguring {router['name']}: {str(e)}")
    
    return updated_devices

if __name__ == "__main__":
    print("=== Router IP Reconfiguration ===")
    print("Changing router IPs to avoid conflicts with your network:")
    print("- R1: 192.168.1.1 → 192.168.1.10")
    print("- R2: 192.168.1.2 → 192.168.1.20")
    
    updated_devices = reconfigure_router_ips()
    
    if updated_devices:
        # Update configuration files
        import yaml
        import json
        
        config_data = {'devices': updated_devices}
        
        with open('config/devices_config.yaml', 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        # Update JSON cache
        json_devices = []
        for device in updated_devices:
            json_devices.append({
                'name': device['name'],
                'host': device['host'],
                'port': device['port'],
                'device_type': device['device_type'],
                'status': 'online',
                'connection_type': 'ssh'
            })
        
        with open('config/devices_cache.json', 'w') as f:
            json.dump(json_devices, f, indent=2)
        
        print(f"\n✅ Configuration files updated with new IP addresses")
        print("Updated devices:")
        for device in updated_devices:
            print(f"- {device['name']}: {device['host']}:22 (SSH)")
    else:
        print("\n❌ No devices were successfully reconfigured")
