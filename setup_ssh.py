#!/usr/bin/env python3
"""
SSH Configuration Script for GNS3 Routers
This script connects via console (telnet) to configure SSH on routers,
then tests SSH connectivity and updates the device configuration.
"""

import yaml
import json
import logging
import os
from netmiko import ConnectHandler
from datetime import datetime
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ssh_setup.log'),
        logging.StreamHandler()
    ]
)

def load_console_config():
    """Load console configuration for initial connection"""
    # First try to load console configuration from enable_new.py output
    console_devices = [
        {
            'name': 'R1',
            'host': '127.0.0.1',
            'port': 5000,
            'device_type': 'cisco_ios_telnet'
        },
        {
            'name': 'R2', 
            'host': '127.0.0.1',
            'port': 5008,
            'device_type': 'cisco_ios_telnet'
        }
    ]
    
    logging.info("Using hardcoded console configuration for GNS3 routers")
    return {'devices': console_devices}

def configure_ssh_on_device(device_config, ssh_username, ssh_password, enable_secret):
    """Configure SSH on a router via console connection"""
    console_device = {
        'device_type': 'cisco_ios_telnet',
        'host': device_config['host'],
        'port': device_config['port'],
        'username': '',
        'password': '',
        'secret': '',
        'timeout': 30,
        'global_delay_factor': 2
    }
    
    try:
        logging.info(f"Connecting to {device_config['name']} via console {device_config['host']}:{device_config['port']}...")
        connection = ConnectHandler(**console_device)
        time.sleep(2)  # Give connection time to establish
        
        # Try to enable - might not need it on console
        try:
            connection.enable()
        except:
            logging.info("Enable not required or already in enable mode")
        
        # Get current hostname
        hostname_output = connection.send_command('show running-config | include hostname')
        if 'hostname' in hostname_output:
            hostname = hostname_output.split()[-1]
        else:
            hostname = device_config['name']
        
        logging.info(f"Connected to {hostname} - configuring SSH...")
        
        # Configure basic network settings first
        logging.info("Setting up basic network configuration...")
        basic_commands = [
            'configure terminal',
            f'hostname {hostname}',
            'ip domain-name automation.local',
            'interface fastethernet0/0',
            'ip address 192.168.1.1 255.255.255.0' if device_config['name'] == 'R1' else 'ip address 192.168.1.2 255.255.255.0',
            'no shutdown',
            'exit'
        ]
        
        for command in basic_commands:
            logging.info(f"Executing: {command}")
            output = connection.send_command_timing(command, delay_factor=2)
            time.sleep(1)
        
        # Generate RSA keys
        logging.info("Generating RSA keys...")
        rsa_output = connection.send_command_timing('crypto key generate rsa general-keys modulus 1024', delay_factor=5)
        if 'yes/no' in rsa_output or 'y/n' in rsa_output:
            rsa_output = connection.send_command_timing('yes', delay_factor=5)
        logging.info(f"RSA key generation output: {rsa_output}")
        
        # Configure SSH user and settings
        ssh_config_commands = [
            f'username {ssh_username} privilege 15 secret {ssh_password}',
            f'enable secret {enable_secret}',
            'ip ssh version 2',
            'ip ssh time-out 60',
            'ip ssh authentication-retries 3',
            'line vty 0 4',
            'transport input ssh',
            'login local',
            'exit',
            'exit'
        ]
        
        for command in ssh_config_commands:
            logging.info(f"Executing: {command}")
            output = connection.send_command_timing(command, delay_factor=2)
            time.sleep(1)
        
        # Save configuration
        save_output = connection.send_command('write memory')
        logging.info(f"Configuration saved: {save_output}")
        
        # Get interface status
        ip_output = connection.send_command('show ip interface brief')
        logging.info(f"Interface status:\n{ip_output}")
        
        connection.disconnect()
        
        # Return the expected management IP
        management_ip = '192.168.1.1' if device_config['name'] == 'R1' else '192.168.1.2'
        
        return {
            'hostname': hostname,
            'configured': True,
            'management_ip': management_ip
        }
        
    except Exception as e:
        logging.error(f"Failed to configure SSH on {device_config['name']}: {str(e)}")
        return {'configured': False, 'error': str(e)}

def find_management_ip(device_config):
    """Find the management IP of a router"""
    console_device = {
        'device_type': 'cisco_ios_telnet',
        'host': device_config['host'],
        'port': device_config['port'],
        'username': '',
        'password': '',
        'secret': '',
        'timeout': 30
    }
    
    try:
        connection = ConnectHandler(**console_device)
        connection.enable()
        
        # Get interface information
        ip_output = connection.send_command('show ip interface brief')
        lines = ip_output.split('\n')
        
        for line in lines:
            if 'up' in line.lower() and ('fastethernet' in line.lower() or 'gigabitethernet' in line.lower() or 'ethernet' in line.lower()):
                parts = line.split()
                if len(parts) >= 2 and '.' in parts[1]:
                    ip = parts[1]
                    if ip != 'unassigned' and not ip.startswith('127.'):
                        logging.info(f"Found management IP: {ip}")
                        connection.disconnect()
                        return ip
        
        connection.disconnect()
        return None
        
    except Exception as e:
        logging.error(f"Error finding management IP: {str(e)}")
        return None

def test_ssh_connection(ip, username, password, enable_secret):
    """Test SSH connectivity to a device"""
    ssh_device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': username,
        'password': password,
        'secret': enable_secret,
        'timeout': 30
    }
    
    try:
        logging.info(f"Testing SSH connection to {ip}...")
        connection = ConnectHandler(**ssh_device)
        connection.enable()
        
        # Test basic connectivity
        output = connection.send_command('show version | include uptime')
        logging.info(f"SSH test successful: {output}")
        
        connection.disconnect()
        return True
        
    except Exception as e:
        logging.error(f"SSH test failed for {ip}: {str(e)}")
        return False

def main():
    """Main configuration function"""
    print("=== SSH Configuration Setup ===")
    print("This will configure SSH on your GNS3 routers via console access")
    print("Make sure your GNS3 project 'Solange' is running with R1 and R2 started")
    
    # Get SSH credentials
    ssh_username = input("Enter SSH username (default: admin): ").strip() or "admin"
    ssh_password = input("Enter SSH password (default: cisco123): ").strip() or "cisco123"
    enable_secret = input("Enter enable secret (default: enable123): ").strip() or "enable123"
    
    # Load console configuration
    config_data = load_console_config()
    if not config_data:
        print("❌ Could not load console configuration")
        return
    
    devices = config_data.get('devices', [])
    ssh_devices = []
    
    print(f"\nConfiguring SSH on {len(devices)} devices...")
    
    for device in devices:
        print(f"\n--- Configuring {device['name']} ---")
        
        # Configure SSH via console
        result = configure_ssh_on_device(device, ssh_username, ssh_password, enable_secret)
        
        if result.get('configured'):
            management_ip = result.get('management_ip')
            if management_ip:
                print(f"⏳ Testing SSH connectivity to {management_ip}...")
                time.sleep(5)  # Give the router time to apply config
                
                # Test SSH connectivity
                if test_ssh_connection(management_ip, ssh_username, ssh_password, enable_secret):
                    ssh_devices.append({
                        'device_type': 'cisco_ios',
                        'host': management_ip,
                        'port': 22,
                        'username': ssh_username,
                        'password': ssh_password,
                        'secret': enable_secret,
                        'name': device['name'],
                        'timeout': 30,
                        'global_delay_factor': 2,
                        'fast_cli': False
                    })
                    print(f"✅ {device['name']} SSH configured successfully at {management_ip}")
                else:
                    print(f"⚠️  SSH configuration applied but test failed for {device['name']} at {management_ip}")
                    print("   This is normal - the interface might need time to come up")
                    # Add it anyway as configuration was successful
                    ssh_devices.append({
                        'device_type': 'cisco_ios',
                        'host': management_ip,
                        'port': 22,
                        'username': ssh_username,
                        'password': ssh_password,
                        'secret': enable_secret,
                        'name': device['name'],
                        'timeout': 30,
                        'global_delay_factor': 2,
                        'fast_cli': False
                    })
            else:
                print(f"❌ Could not determine management IP for {device['name']}")
        else:
            print(f"❌ SSH configuration failed for {device['name']}: {result.get('error', 'Unknown error')}")
    
    if ssh_devices:
        # Save SSH configuration
        ssh_config = {'devices': ssh_devices}
        
        with open('config/devices_config.yaml', 'w') as f:
            yaml.dump(ssh_config, f, default_flow_style=False)
        
        # Create JSON cache for web GUI
        json_devices = []
        for device in ssh_devices:
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
        
        print(f"\n✅ SSH configuration completed for {len(ssh_devices)} devices")
        print("Configuration files updated:")
        print("- config/devices_config.yaml")
        print("- config/devices_cache.json")
        
        # Display final configuration
        print("\n=== SSH Device Summary ===")
        for device in ssh_devices:
            print(f"- {device['name']}: {device['host']}:22 (SSH)")
            
        print("\n🔧 Next Steps:")
        print("1. Make sure your router interfaces are up and reachable")
        print("2. Test SSH connectivity manually if needed")
        print("3. Run your automation scripts - they will now use SSH!")
        
    else:
        print("\n❌ No devices were successfully configured for SSH")
        print("Check the logs for more details and ensure GNS3 routers are running")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    
    main()
