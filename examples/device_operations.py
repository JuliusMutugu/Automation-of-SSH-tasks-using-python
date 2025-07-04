"""
Example script demonstrating individual device operations
for the Solange project
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'connectionGNS3'))

from netmiko import ConnectHandler
import yaml
import time

def load_device_config():
    """Load device configuration from YAML file"""
    try:
        with open('../config/devices_config.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("Device configuration not found. Please run device discovery first.")
        return None

def connect_to_device(device):
    """Establish SSH connection to a device"""
    try:
        connection = ConnectHandler(**device)
        connection.enable()
        return connection
    except Exception as e:
        print(f"Failed to connect to {device.get('name', device['host'])}: {e}")
        return None

def show_device_info(device):
    """Display basic device information"""
    connection = connect_to_device(device)
    if not connection:
        return
    
    try:
        print(f"\n=== Device: {device.get('name', device['host'])} ===")
        
        # Show version
        version = connection.send_command("show version")
        print("Version Info:")
        for line in version.split('\n')[:3]:  # First 3 lines
            print(f"  {line}")
        
        # Show interfaces
        interfaces = connection.send_command("show ip interface brief")
        print("\nInterfaces:")
        for line in interfaces.split('\n')[:5]:  # First 5 lines
            print(f"  {line}")
        
        # Show running config (just hostname)
        hostname = connection.send_command("show running-config | include hostname")
        print(f"\nHostname: {hostname}")
        
    except Exception as e:
        print(f"Error getting device info: {e}")
    finally:
        connection.disconnect()

def configure_single_device(device, commands):
    """Apply configuration to a single device"""
    connection = connect_to_device(device)
    if not connection:
        return False
    
    try:
        print(f"\nConfiguring {device.get('name', device['host'])}...")
        
        # Enter configuration mode
        connection.send_command('configure terminal')
        
        # Apply commands
        for command in commands:
            if command.strip() and not command.startswith('#'):
                print(f"  Applying: {command}")
                result = connection.send_command(command)
                time.sleep(0.5)
        
        # Save configuration
        connection.send_command('end')
        connection.send_command('write memory')
        
        print(f"✓ Configuration applied successfully")
        return True
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False
    finally:
        connection.disconnect()

def interactive_device_selection():
    """Allow user to select a specific device"""
    config = load_device_config()
    if not config:
        return None
    
    devices = config['devices']
    if not devices:
        print("No devices found in configuration.")
        return None
    
    print("\nAvailable devices:")
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.get('name', device['host'])} ({device['host']})")
    
    while True:
        try:
            choice = int(input(f"\nSelect device (1-{len(devices)}): "))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def main():
    print("Solange Project - Individual Device Operations")
    print("=" * 50)
    
    while True:
        print("\nOperations:")
        print("1. Show device information")
        print("2. Configure single device")
        print("3. Test connectivity to all devices")
        print("4. Show all device IPs")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "0":
            break
            
        elif choice == "1":
            device = interactive_device_selection()
            if device:
                show_device_info(device)
                
        elif choice == "2":
            device = interactive_device_selection()
            if device:
                print("\nEnter configuration commands (empty line to finish):")
                commands = []
                while True:
                    command = input("> ")
                    if not command.strip():
                        break
                    commands.append(command)
                
                if commands:
                    configure_single_device(device, commands)
                else:
                    print("No commands entered.")
                    
        elif choice == "3":
            config = load_device_config()
            if config:
                print("\nTesting connectivity...")
                for device in config['devices']:
                    connection = connect_to_device(device)
                    if connection:
                        print(f"✓ {device.get('name', device['host'])} - Connected")
                        connection.disconnect()
                    else:
                        print(f"✗ {device.get('name', device['host'])} - Failed")
                        
        elif choice == "4":
            config = load_device_config()
            if config:
                print("\nDevice List:")
                for device in config['devices']:
                    print(f"  {device.get('name', device['host'])}: {device['host']}")
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
