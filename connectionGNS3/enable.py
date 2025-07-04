from gns3fy import Gns3Connector
from netmiko import ConnectHandler
import time
import logging
import json
import yaml
import os
import requests
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = '../logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/gns3_automation.log'),
        logging.StreamHandler()
    ]
)

# Set up GNS3 connection
try:
    gns3 = Gns3Connector(url="http://localhost:3080")
    print("✓ Connected to GNS3 server")
except Exception as e:
    print(f"✗ Failed to connect to GNS3 server: {e}")
    print("Make sure GNS3 is running on localhost:3080")
    exit(1)

# Get the project and nodes
try:
    # Get project information as dictionary
    project_info = gns3.get_project(name="Solange")
    if not project_info:
        print("✗ Project 'Solange' not found")
        exit(1)
    
    print(f"✓ Found project: {project_info.get('name', 'Unknown')}")
    project_id = project_info.get('project_id')
    
    if not project_id:
        print("✗ Could not get project ID")
        exit(1)
    
    # Get nodes using HTTP API directly
    import requests
    nodes_url = f"http://localhost:3080/v2/projects/{project_id}/nodes"
    response = requests.get(nodes_url)
    
    if response.status_code == 200:
        nodes_data = response.json()
        print(f"✓ Found {len(nodes_data)} nodes in project")
    else:
        print(f"✗ Failed to get nodes: HTTP {response.status_code}")
        exit(1)
        
except Exception as e:
    print(f"✗ Failed to get project 'Solange': {e}")
    print("Make sure the 'Solange' project is open in GNS3")
    exit(1)

# Collect device information
devices_info = []
for node_data in nodes_data:
    if node_data.get('status') == "started":  # Only include running devices
        # Try to get IP address from node properties
        node_name = node_data.get('name', 'Unknown')
        node_id = node_data.get('node_id')
        
        # For now, we'll need to manually determine IP addresses
        # or use console port for further configuration
        console_port = node_data.get('console')
        
        # You may need to configure static IPs or use DHCP
        # For this example, let's assume your devices have known IPs
        device_ip = None
        
        # Map device names to IPs (you'll need to update this based on your setup)
        device_ip_map = {
            'Baraton': '192.168.1.1',  # Your router's IP
            'R1': '192.168.1.1',       # Assuming R1 is your Baraton router
            'Switch1': '192.168.1.2',  # Switch IP (if managed)
            'PC1': '192.168.1.10',     # PC1 IP
            'PC2': '192.168.1.11',     # PC2 IP
            # Add other devices here as needed
        }
        
        if node_name in device_ip_map:
            device_ip = device_ip_map[node_name]
        
        if device_ip:
            devices_info.append({
                'name': node_name,
                'ip': device_ip,
                'node_id': node_id,
                'console_port': console_port
            })
            logging.info(f"Found device: {node_name} at {device_ip}")
        else:
            print(f"⚠ Device {node_name} found but no IP configured - add to device_ip_map")

# Function to create device connection configuration for SSH
def create_device_config(device_info):
    return {
        'device_type': 'cisco_ios',
        'host': device_info['ip'],
        'username': 'admin',        # Username configured on devices
        'password': 'password123',  # Password configured on devices
        'secret': 'password123',    # Enable secret (using same password)
        'timeout': 30,
        'global_delay_factor': 2,
        'fast_cli': False
    }

# Function to test SSH connectivity to a device
def test_ssh_connection(device_info):
    device_config = create_device_config(device_info)
    try:
        connection = ConnectHandler(**device_config)
        connection.enable()  # Enter enable mode
        hostname = connection.send_command('show version | include uptime')
        connection.disconnect()
        logging.info(f"SSH connection successful to {device_info['name']} ({device_info['ip']})")
        return True
    except Exception as e:
        logging.error(f"SSH connection failed to {device_info['name']} ({device_info['ip']}): {e}")
        return False

# Function to get device information
def get_device_info(device_info):
    device_config = create_device_config(device_info)
    try:
        connection = ConnectHandler(**device_config)
        connection.enable()
        
        # Get device information
        version_info = connection.send_command('show version')
        interfaces = connection.send_command('show ip interface brief')
        running_config = connection.send_command('show running-config')
        
        connection.disconnect()
        
        return {
            'device_name': device_info['name'],
            'ip_address': device_info['ip'],
            'version_info': version_info,
            'interfaces': interfaces,
            'config_length': len(running_config.split('\n'))
        }
    except Exception as e:
        logging.error(f"Failed to get device info for {device_info['name']}: {e}")
        return None

# Main execution
if __name__ == "__main__":
    print(f"Found {len(devices_info)} active devices in Solange project:")
    for device in devices_info:
        print(f"  - {device['name']}: {device['ip']}")
    
    print("\n=== Testing SSH Connectivity ===")
    active_devices = []
    for device in devices_info:
        if test_ssh_connection(device):
            active_devices.append(device)
    
    print(f"\n{len(active_devices)} devices are accessible via SSH")
    
    # Get device information for accessible devices
    print("\n=== Device Information ===")
    for device in active_devices:
        info = get_device_info(device)
        if info:
            print(f"\nDevice: {info['device_name']} ({info['ip_address']})")
            print(f"Config lines: {info['config_length']}")
    
    # Save device configuration to file for other scripts
    config_data = {
        'devices': []
    }
    
    for device in active_devices:
        config_data['devices'].append({
            'device_type': 'cisco_ios',
            'host': device['ip'],
            'username': 'admin',
            'password': 'password123',
            'secret': 'password123',
            'name': device['name'],
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': False
        })
    
    # Save to YAML file for other scripts to use
    config_dir = '../config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    with open('../config/devices_config.yaml', 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    print(f"\nDevice configuration saved to config/devices_config.yaml")
    print("You can now run the automation scripts!")
