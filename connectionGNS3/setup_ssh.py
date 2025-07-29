"""
SSH Setup Script for GNS3 Routers
This script connects to routers via console (telnet) and configures SSH access
"""

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
        logging.FileHandler('logs/ssh_setup.log'),
        logging.StreamHandler()
    ]
)

# Set up GNS3 connection
gns3_server = Gns3Connector("http://127.0.0.1:3080")

def setup_ssh_on_device(device_info, username="admin", password="cisco123", enable_secret="cisco"):
    """
    Configure SSH on a single device using console connection
    """
    console_config = {
        'device_type': 'cisco_ios_telnet',
        'host': device_info['ip'],
        'port': device_info['port'],
        'username': '',
        'password': '',
        'secret': '',
        'timeout': 30,
        'global_delay_factor': 2,
        'fast_cli': False
    }
    
    try:
        logging.info(f"Connecting to {device_info['name']} via console ({device_info['ip']}:{device_info['port']})...")
        
        # Connect via console
        connection = ConnectHandler(**console_config)
        connection.enable()
        
        logging.info(f"Successfully connected to {device_info['name']} console")
        
        # Get current hostname for SSH key generation
        hostname_output = connection.send_command("show running-config | include hostname")
        if "hostname" in hostname_output:
            hostname = hostname_output.split()[1]
        else:
            hostname = device_info['name']
        
        # Configure SSH step by step
        ssh_commands = [
            'configure terminal',
            f'hostname {hostname}',
            'ip domain-name solange.local',
            f'username {username} privilege 15 password {password}',
            f'enable secret {enable_secret}',
            'crypto key generate rsa general-keys modulus 1024',
            'ip ssh version 2',
            'ip ssh time-out 120',
            'ip ssh authentication-retries 3',
            'line vty 0 4',
            'transport input ssh',
            'login local',
            'exit',
            'interface gigabitethernet0/0',
            'ip address 192.168.1.10 255.255.255.0',
            'no shutdown',
            'exit',
            'end',
            'write memory'
        ]
        
        # Apply SSH configuration
        for command in ssh_commands:
            if command == 'crypto key generate rsa general-keys modulus 1024':
                # RSA key generation requires special handling
                logging.info("Generating RSA keys...")
                connection.send_command_timing(command, delay_factor=5)
                time.sleep(8)  # Wait for key generation
            else:
                result = connection.send_command_timing(command, delay_factor=2)
                logging.info(f"Applied: {command}")
                time.sleep(1)
        
        # Verify SSH configuration
        ssh_status = connection.send_command_timing("show ip ssh", delay_factor=2)
        logging.info(f"SSH Status for {device_info['name']}:")
        logging.info(ssh_status)
        
        # Get interface status
        interface_status = connection.send_command_timing("show ip interface brief", delay_factor=2)
        logging.info(f"Interface Status for {device_info['name']}:")
        logging.info(interface_status)
        
        connection.disconnect()
        logging.info(f"SSH configuration completed for {device_info['name']}")
        
        return {
            'name': device_info['name'],
            'host': '192.168.1.10' if device_info['name'] == 'R1' else '192.168.1.11',
            'device_type': 'cisco_ios',
            'username': username,
            'password': password,
            'secret': enable_secret,
            'port': 22,
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': False
        }
        
    except Exception as e:
        logging.error(f"Failed to configure SSH on {device_info['name']}: {str(e)}")
        return None

def discover_and_setup_ssh():
    """
    Discover GNS3 devices and configure SSH on each router
    """
    try:
        logging.info("Connecting to GNS3 server...")
        
        # Get all projects
        projects_url = "http://127.0.0.1:3080/v2/projects"
        projects_response = requests.get(projects_url)
        projects = projects_response.json()
        
        # Find the Solange project
        solange_project = None
        for project in projects:
            if project['name'] == 'Solange':
                solange_project = project
                break
        
        if not solange_project:
            logging.error("Solange project not found")
            return False
        
        logging.info(f"Found project: {solange_project['name']}")
        
        # Get nodes in the project
        nodes_url = f"http://127.0.0.1:3080/v2/projects/{solange_project['project_id']}/nodes"
        nodes_response = requests.get(nodes_url)
        nodes = nodes_response.json()
        
        logging.info(f"Found {len(nodes)} nodes in project")
        
        # Find router nodes with console access
        router_devices = []
        for node in nodes:
            if node['node_type'] == 'dynamips' and node['status'] == 'started':
                console_host = node.get('console_host', '127.0.0.1')
                console_port = node.get('console')
                
                if console_port:
                    device_info = {
                        'name': node['name'],
                        'ip': console_host,
                        'port': console_port,
                        'node_id': node['node_id']
                    }
                    router_devices.append(device_info)
                    logging.info(f"Found router: {node['name']} accessible via {console_host}:{console_port} (console)")
                else:
                    logging.warning(f"Router {node['name']} has no console port configured")
            else:
                logging.info(f"Skipping {node['name']} - {node.get('node_type', 'unknown')} ({node.get('status', 'unknown')})")
        
        if not router_devices:
            logging.error("No active router devices found")
            return False
        
        logging.info(f"Found {len(router_devices)} active router devices in Solange project:")
        for device in router_devices:
            logging.info(f"  - {device['name']}: {device['ip']}:{device['port']} (console)")
        
        # Configure SSH on each device
        ssh_devices = []
        for i, device in enumerate(router_devices):
            logging.info(f"\n=== Configuring SSH on {device['name']} ===")
            
            # Assign IP addresses (R1: 192.168.1.10, R2: 192.168.1.11, etc.)
            ssh_device = setup_ssh_on_device(device, username="admin", password="cisco123")
            if ssh_device:
                if device['name'] == 'R1':
                    ssh_device['host'] = '192.168.1.10'
                elif device['name'] == 'R2':
                    ssh_device['host'] = '192.168.1.11'
                else:
                    ssh_device['host'] = f'192.168.1.{20 + i}'
                
                ssh_devices.append(ssh_device)
                logging.info(f"SSH configured successfully on {device['name']} - IP: {ssh_device['host']}")
            else:
                logging.error(f"Failed to configure SSH on {device['name']}")
        
        if not ssh_devices:
            logging.error("Failed to configure SSH on any devices")
            return False
        
        # Create SSH configuration file
        config_data = {
            'devices': ssh_devices
        }
        
        # Save SSH configuration to YAML file
        with open('config/devices_config.yaml', 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        # Also create JSON cache for web GUI
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
        
        # Save JSON cache for web GUI
        with open('config/devices_cache.json', 'w') as f:
            json.dump(json_devices, f, indent=2)
        
        logging.info(f"\n=== SSH Setup Summary ===")
        logging.info(f"SSH configured on {len(ssh_devices)} devices:")
        for device in ssh_devices:
            logging.info(f"  - {device['name']}: {device['host']}:22 (SSH)")
        
        logging.info(f"\nDevice configuration saved to config/devices_config.yaml")
        logging.info(f"Device cache saved to config/devices_cache.json")
        logging.info("SSH setup completed! You can now use SSH for automation tasks.")
        
        return True
        
    except Exception as e:
        logging.error(f"Error during SSH setup: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  SOLANGE SSH SETUP TOOL")
    print("=" * 60)
    print("  This tool will configure SSH access on your GNS3 routers")
    print("  Current connection: Console via telnet")
    print("  Target connection: SSH via network interface")
    print("=" * 60)
    
    success = discover_and_setup_ssh()
    
    if success:
        print("\nSSH setup completed successfully!")
        print("Your automation scripts will now use SSH instead of console telnet.")
        print("Make sure your routers have network connectivity for SSH access.")
    else:
        print("\nSSH setup failed. Check the logs for details.")
        print("Your scripts will continue to use console telnet access.")
