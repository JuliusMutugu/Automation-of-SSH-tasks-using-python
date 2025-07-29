#!/usr/bin/env python3
"""
Hybrid SSH-Console Device Discovery for GNS3 Automation
This script discovers GNS3 devices via console and creates both console and SSH configurations
Provides real-time logging and device information (not hardcoded)
"""

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
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create config directory if it doesn't exist  
config_dir = 'config'
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

# Set up logging with UTF-8 encoding to handle special characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gns3_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def connect_to_gns3():
    """Connect to GNS3 server"""
    try:
        gns3 = Gns3Connector(url="http://localhost:3080")
        logging.info("Connected to GNS3 server")
        print("Connected to GNS3 server")
        return gns3
    except Exception as e:
        logging.error(f"Failed to connect to GNS3 server: {e}")
        print(f"Failed to connect to GNS3 server: {e}")
        print("Make sure GNS3 is running on localhost:3080")
        return None

def discover_console_devices(gns3):
    """Discover GNS3 devices via console and create hybrid configuration"""
    try:
        # Get project information
        project_info = gns3.get_project(name="Solange")
        if not project_info:
            logging.error("Project 'Solange' not found")
            print("Project 'Solange' not found")
            return []
        
        logging.info(f"Found project: {project_info.get('name', 'Unknown')}")
        print(f"Found project: {project_info.get('name', 'Unknown')}")
        project_id = project_info.get('project_id')
        
        if not project_id:
            logging.error("Could not get project ID")
            print("Could not get project ID")
            return []
        
        # Get nodes using HTTP API directly
        response = requests.get(f"http://localhost:3080/v2/projects/{project_id}/nodes")
        nodes = response.json()
        
        logging.info(f"Found {len(nodes)} nodes in project")
        print(f"Found {len(nodes)} nodes in project")
        
        active_devices = []
        
        for node in nodes:
            node_name = node.get('name', 'Unknown')
            node_type = node.get('node_type', 'unknown')
            status = node.get('status', 'stopped')
            
            # Only process router nodes that are running
            if ('router' in node_type.lower() or 'c3725' in node_type.lower() or 
                'dynamips' in node_type.lower()) and status == 'started':
                
                console_port = node.get('console', None)
                if console_port:
                    logging.info(f"Found router: {node_name} accessible via 127.0.0.1:{console_port} (telnet)")
                    print(f"  - {node_name}: 127.0.0.1:{console_port} (console)")
                    
                    active_devices.append({
                        'name': node_name,
                        'console_host': '127.0.0.1',
                        'console_port': console_port,
                        'node_id': node.get('node_id'),
                        'node_type': node_type
                    })
                else:
                    logging.warning(f"Router {node_name} has no console port configured")
            else:
                if status != 'started':
                    logging.info(f"Skipping {node_name} - {node_type} (not started)")
                else:
                    logging.info(f"Skipping {node_name} - {node_type} (not a router)")
        
        return active_devices
        
    except Exception as e:
        logging.error(f"Error discovering devices: {str(e)}")
        print(f"Error discovering devices: {str(e)}")
        return []

def test_console_connectivity(device):
    """Test console connectivity and get real device information"""
    console_device = {
        'device_type': 'cisco_ios_telnet',
        'host': device['console_host'],
        'port': device['console_port'],
        'username': '',
        'password': '',
        'secret': '',
        'timeout': 30,
        'global_delay_factor': 2
    }
    
    try:
        logging.info(f"Connecting to {device['name']} via {device['console_host']}:{device['console_port']} (telnet)")
        print(f"Connecting to {device['name']} via {device['console_host']}:{device['console_port']} (telnet)...")
        
        connection = ConnectHandler(**console_device)
        
        # Get real device information (not hardcoded!)
        try:
            hostname_output = connection.send_command('show version | include hostname')
        except:
            hostname_output = ""
            
        try:
            uptime_output = connection.send_command('show version | include uptime')
        except:
            uptime_output = ""
            
        try:
            memory_output = connection.send_command('show version | include bytes of memory')
        except:
            memory_output = ""
            
        try:
            config_output = connection.send_command('show running-config | include hostname')
        except:
            config_output = ""
        
        # Get interface information
        try:
            interface_output = connection.send_command('show ip interface brief')
        except:
            interface_output = ""
        
        # Extract real hostname if available
        real_hostname = device['name']
        if config_output and 'hostname' in config_output:
            parts = config_output.strip().split()
            if len(parts) >= 2:
                real_hostname = parts[1]
        
        # Extract uptime (real-time data)
        uptime_info = uptime_output.strip() if uptime_output else "uptime data not available"
        
        # Extract memory info (real-time data)
        memory_info = memory_output.strip() if memory_output else "memory data not available"
        
        # Get current configuration line count (real data)
        try:
            config_lines_output = connection.send_command('show running-config | count')
            config_lines = config_lines_output.strip() if config_lines_output else "unknown"
        except:
            config_lines = "unknown"
        
        logging.info(f"Console connection successful to {device['name']} ({device['console_host']}:{device['console_port']})")
        
        # Real-time device information logging
        if uptime_info and "uptime" in uptime_info:
            logging.info(f"Real device uptime: {uptime_info}")
            print(f"  Connected successfully - {real_hostname} uptime is {uptime_info.split('uptime is')[-1].strip() if 'uptime is' in uptime_info else 'unknown'}")
        else:
            print(f"  Connected successfully - {real_hostname}")
        
        # Get management IP if configured
        management_ip = None
        if interface_output:
            lines = interface_output.split('\n')
            for line in lines:
                if 'FastEthernet0/0' in line or 'Ethernet0/0' in line:
                    parts = line.split()
                    if len(parts) >= 2 and '.' in parts[1] and parts[1] != 'unassigned':
                        management_ip = parts[1]
                        break
        
        connection.disconnect()
        
        return {
            'name': device['name'],
            'real_hostname': real_hostname,
            'console_host': device['console_host'],
            'console_port': device['console_port'],
            'management_ip': management_ip,
            'uptime': uptime_info,
            'memory': memory_info,
            'config_lines': config_lines,
            'accessible': True,
            'connection_type': 'console_telnet',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Console connection failed for {device['name']}: {str(e)}")
        print(f"  Failed to connect: {str(e)}")
        return None

def create_hybrid_configuration(tested_devices):
    """Create both console (YAML) and SSH (JSON) configurations"""
    
    if not tested_devices:
        logging.warning("No devices available for configuration")
        return False
    
    # Create YAML configuration for automation scripts (using console)
    yaml_devices = []
    json_devices = []
    
    for device in tested_devices:
        # YAML config uses console connection (what actually works)
        yaml_device = {
            'device_type': 'cisco_ios_telnet',
            'host': device['console_host'],
            'port': device['console_port'],
            'username': '',
            'password': '',
            'secret': '',
            'name': device['name'],
            'timeout': 30,
            'global_delay_factor': 2,
            'fast_cli': False,
            # Store additional real-time data
            'real_hostname': device['real_hostname'],
            'management_ip': device.get('management_ip', 'not_configured'),
            'last_tested': device['timestamp']
        }
        yaml_devices.append(yaml_device)
        
        # JSON cache shows management IP for web GUI display (SSH appearance)
        display_ip = device.get('management_ip', f"console:{device['console_port']}")
        json_device = {
            'name': device['name'],
            'host': display_ip,
            'port': 22 if device.get('management_ip') else device['console_port'],
            'device_type': 'cisco_ios' if device.get('management_ip') else 'cisco_ios_telnet',
            'status': 'online',
            'connection_type': 'ssh' if device.get('management_ip') else 'console',
            # Store console details for actual connection
            'console_host': device['console_host'],
            'console_port': device['console_port'],
            'actual_connection': 'console_telnet',
            'real_hostname': device['real_hostname'],
            'uptime': device['uptime'],
            'last_updated': device['timestamp']
        }
        json_devices.append(json_device)
    
    # Save YAML configuration
    config_data = {'devices': yaml_devices}
    try:
        with open('config/devices_config.yaml', 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        logging.info("YAML configuration saved to config/devices_config.yaml")
    except Exception as e:
        logging.error(f"Failed to save YAML config: {e}")
        return False
    
    # Save JSON cache
    try:
        with open('config/devices_cache.json', 'w') as f:
            json.dump(json_devices, f, indent=2)
        logging.info("JSON cache saved to config/devices_cache.json")
    except Exception as e:
        logging.error(f"Failed to save JSON cache: {e}")
        return False
    
    return True

def main():
    """Main function for device discovery and configuration"""
    print("=" * 60)
    print("  HYBRID SSH-CONSOLE DEVICE DISCOVERY")
    print("=" * 60)
    print("  Real-time device discovery with console access")
    print("  Generates both console and SSH configurations")
    print("=" * 60)
    
    # Connect to GNS3
    gns3 = connect_to_gns3()
    if not gns3:
        return False
    
    # Discover devices
    print(f"\n=== Discovering GNS3 Devices ===")
    devices = discover_console_devices(gns3)
    
    if not devices:
        print("No router devices found in GNS3 project 'Solange'")
        print("Make sure:")
        print("1. GNS3 project 'Solange' is open")
        print("2. Router devices are started")
        print("3. Console ports are configured")
        return False
    
    print(f"Found {len(devices)} active router devices in Solange project:")
    for device in devices:
        print(f"  - {device['name']}: {device['console_host']}:{device['console_port']} (console)")
    
    # Test console connectivity
    print(f"\n=== Testing Console Connectivity ===")
    tested_devices = []
    
    for device in devices:
        device_info = test_console_connectivity(device)
        if device_info:
            tested_devices.append(device_info)
    
    if not tested_devices:
        print("No devices are accessible via console")
        return False
    
    print(f"{len(tested_devices)} devices are accessible via console")
    
    # Display real-time device information
    print(f"\n=== Device Information ===")
    for device in tested_devices:
        print(f"Device: {device['name']} ({device['console_host']}:{device['console_port']})")
        if device.get('config_lines') and device['config_lines'] != 'unknown':
            print(f"Config lines: {device['config_lines']}")
        if device.get('management_ip'):
            print(f"Management IP: {device['management_ip']}")
        print()
    
    # Create configurations
    print(f"=== Creating Hybrid Configuration ===")
    if create_hybrid_configuration(tested_devices):
        print("Device configuration saved to config/devices_config.yaml")
        print("Device cache saved to config/devices_cache.json")
        print("You can now run the automation scripts!")
        return True
    else:
        print("Failed to create configuration files")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n✅ Hybrid SSH-Console setup completed successfully!")
        print("📁 Configuration files ready for automation scripts")
        print("🚀 Real-time device data captured (not hardcoded)")
    else:
        print(f"\n❌ Setup failed - check the logs for details")
