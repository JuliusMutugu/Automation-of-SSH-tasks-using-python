from gns3fy import Gns3Connector
from netmiko import ConnectHandler
import time
import logging
import json
import yaml
import requests
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
try:
    gns3 = Gns3Connector(url="http://localhost:3080")
    print("Connected to GNS3 server")
except Exception as e:
    print(f"Failed to connect to GNS3 server: {e}")
    print("Make sure GNS3 is running on localhost:3080")
    exit(1)

# Get the project and nodes
try:
    # Get project information as dictionary
    project_info = gns3.get_project(name="Solange")
    if not project_info:
        print("Project 'Solange' not found")
        exit(1)
    
    print(f"Found project: {project_info.get('name', 'Unknown')}")
    project_id = project_info.get('project_id')
    
    if not project_id:
        print("Could not get project ID")
        exit(1)
    
    # Get nodes using HTTP API directly
    import requests
    nodes_url = f"http://localhost:3080/v2/projects/{project_id}/nodes"
    response = requests.get(nodes_url)
    
    if response.status_code == 200:
        nodes_data = response.json()
        print(f"Found {len(nodes_data)} nodes in project")
    else:
        print(f"Failed to get nodes: HTTP {response.status_code}")
        exit(1)
        
except Exception as e:
    print(f"Failed to get project 'Solange': {e}")
    print("Make sure the 'Solange' project is open in GNS3")
    exit(1)

# Collect device information
devices_info = []
for node_data in nodes_data:
    if node_data.get('status') == "started":  # Only include running devices
        node_name = node_data.get('name', 'Unknown')
        node_id = node_data.get('node_id')
        console_port = node_data.get('console')
        node_type = node_data.get('node_type', '')
        
        # Use localhost with console port for telnet access to routers
        # Skip PCs and switches as they don't support SSH/telnet management
        if node_type == 'dynamips':  # Cisco routers
            devices_info.append({
                'name': node_name,
                'ip': '127.0.0.1',  # Use localhost
                'port': console_port,  # Console port for telnet access
                'node_id': node_id,
                'console_port': console_port,
                'access_method': 'telnet'  # Access via telnet to console
            })
            logging.info(f"Found router: {node_name} accessible via 127.0.0.1:{console_port} (telnet)")
        elif node_type == 'ethernet_switch':
            print(f"Skipping {node_name} - ethernet switch (no management)")
        elif node_type == 'vpcs':
            print(f"Skipping {node_name} - PC node (no management)")
        else:
            print(f"Skipping {node_name} - unknown type: {node_type}")

# Function to create device connection configuration for console access
def create_device_config(device_info):
    if device_info.get('access_method') == 'telnet':
        return {
            'device_type': 'cisco_ios_telnet',  # Use telnet for console access
            'host': device_info['ip'],  # 127.0.0.1
            'port': device_info['port'],  # Console port
            'username': '',  # No username needed for console
            'password': '',  # No password needed for console
            'secret': '',   # No enable secret initially
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': False
        }
    else:
        # Fallback to SSH if somehow needed
        return {
            'device_type': 'cisco_ios',
            'host': device_info['ip'],
            'username': 'admin',
            'password': 'password123',
            'secret': 'password123',
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': False
        }

# Function to test console connectivity to a device
def test_console_connection(device_info):
    device_config = create_device_config(device_info)
    try:
        print(f"Connecting to {device_info['name']} via {device_info['ip']}:{device_info['port']} (telnet)...")
        connection = ConnectHandler(**device_config)
        
        # Try to get to enable mode (might not need credentials on console)
        try:
            connection.enable()
        except:
            pass  # Enable might not work without password, that's OK
        
        # Get basic device info with real-time status
        try:
            # Get version information
            version_output = connection.send_command('show version', expect_string=r'#|>')
            
            # Extract uptime from version output
            uptime_match = None
            for line in version_output.split('\n'):
                if 'uptime is' in line.lower():
                    uptime_match = line.strip()
                    break
            
            # Get current time and basic system info
            clock_output = connection.send_command('show clock', expect_string=r'#|>')
            hostname_output = connection.send_command('show running-config | include hostname', expect_string=r'#|>')
            
            # Extract hostname
            hostname = "Unknown"
            if "hostname" in hostname_output:
                try:
                    hostname = hostname_output.split()[1]
                except:
                    hostname = device_info['name']
            
            # Create detailed status message
            if uptime_match:
                status_msg = f"{hostname} - {uptime_match}"
            else:
                status_msg = f"{hostname} - System time: {clock_output.strip()}"
            
        except Exception as e:
            # Fallback to simpler command
            try:
                simple_output = connection.send_command('show clock', expect_string=r'#|>')
                status_msg = f"{device_info['name']} - Connected at {simple_output.strip()}"
            except:
                status_msg = f"{device_info['name']} - Console connection active"
        connection.disconnect()
        
        logging.info(f"Console connection successful to {device_info['name']} ({device_info['ip']}:{device_info['port']})")
        print(f"  Connected successfully - {status_msg}")
        return True
    except Exception as e:
        logging.error(f"Console connection failed to {device_info['name']} (127.0.0.1:{device_info['port']}): {e}")
        print(f"  ❌ Connection failed: {e}")
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
    print(f"Found {len(devices_info)} active router devices in Solange project:")
    for device in devices_info:
        print(f"  - {device['name']}: 127.0.0.1:{device['port']} (console)")
    
    print("\n=== Testing Console Connectivity ===")
    active_devices = []
    for device in devices_info:
        if test_console_connection(device):
            active_devices.append(device)
    
    print(f"\n{len(active_devices)} devices are accessible via console")
    
    # Get device information for accessible devices
    print("\n=== Device Information ===")
    for device in active_devices:
        info = get_device_info(device)
        if info:
            print(f"\nDevice: {info['device_name']} (127.0.0.1:{device['port']})")
            print(f"Config lines: {info['config_length']}")
    
    # Save device configuration to file for other scripts
    config_data = {
        'devices': []
    }
    
    for device in active_devices:
        config_data['devices'].append({
            'device_type': 'cisco_ios_telnet',
            'host': device['ip'],  # 127.0.0.1
            'port': device['port'],  # Console port
            'username': '',
            'password': '',
            'secret': '',
            'name': device['name'],
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': False
        })
    
    # Save to YAML file for other scripts to use
    with open('config/devices_config.yaml', 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    # Also create JSON cache for web GUI
    json_devices = []
    for device in active_devices:
        json_devices.append({
            'name': device['name'],
            'host': device['ip'],
            'port': device['port'],
            'device_type': 'cisco_ios_telnet',
            'status': 'online',
            'connection_type': 'console'
        })
    
    # Save JSON cache for web GUI
    with open('config/devices_cache.json', 'w') as f:
        json.dump(json_devices, f, indent=2)
    
    print(f"\nDevice configuration saved to config/devices_config.yaml")
    print(f"Device cache saved to config/devices_cache.json")
    print("You can now run the automation scripts!")
