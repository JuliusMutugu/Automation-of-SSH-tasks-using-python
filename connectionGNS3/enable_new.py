from gns3fy import Gns3Connector
from netmiko import ConnectHandler
import time
import logging
import json
import yaml
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gns3_automation.log'),
        logging.StreamHandler()
    ]
)

# Set up GNS3 connection
gns3 = Gns3Connector(url="http://localhost:3080")
# gns3.auth(username="your_username", password="your_password")

# Get the project and nodes
project = gns3.get_project(name="Solange")
nodes = project.nodes()

# Collect device information
devices_info = []
for node in nodes:
    if node.status == "started":  # Only include running devices
        device_ip = node.get_ip()
        if device_ip:
            devices_info.append({
                'name': node.name,
                'ip': device_ip,
                'node_id': node.node_id,
                'console_port': getattr(node, 'console', None)
            })
            logging.info(f"Found device: {node.name} at {device_ip}")

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
    with open('config/devices_config.yaml', 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    print(f"\nDevice configuration saved to config/devices_config.yaml")
    print("You can now run the automation scripts!")
