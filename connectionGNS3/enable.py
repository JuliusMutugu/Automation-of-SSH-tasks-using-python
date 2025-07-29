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

# Set up logging with UTF-8 encoding to handle special characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gns3_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set up GNS3 connection
try:
    gns3 = Gns3Connector(url="http://localhost:3080")
    logging.info("Connected to GNS3 server")
    print("Connected to GNS3 server")
except Exception as e:
    logging.error(f"Failed to connect to GNS3 server: {e}")
    print(f"Failed to connect to GNS3 server: {e}")
    print("Make sure GNS3 is running on localhost:3080")
    exit(1)

def discover_console_devices():
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
                    logging.info(f"Found router: {node_name} accessible via 127.0.0.1:{console_port} (console)")
                    print(f"Found router: {node_name} accessible via 127.0.0.1:{console_port} (console)")
                    
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
        logging.info(f"Connecting to {device['name']} via {device['console_host']}:{device['console_port']} (console)")
        print(f"Connecting to {device['name']} via {device['console_host']}:{device['console_port']} (console)...")
        
        connection = ConnectHandler(**console_device)
        
        # Get real device information
        hostname_output = connection.send_command('show version | include hostname')
        uptime_output = connection.send_command('show version | include uptime')
        memory_output = connection.send_command('show version | include bytes of memory')
        
        # Get interface information
        interface_output = connection.send_command('show ip interface brief')
        
        # Extract real hostname if available
        real_hostname = device['name']
        if 'hostname' in hostname_output:
            real_hostname = hostname_output.split()[-1] if hostname_output.split() else device['name']
        
        # Extract uptime
        uptime_info = uptime_output.strip() if uptime_output else "uptime unknown"
        
        # Extract memory info
        memory_info = memory_output.strip() if memory_output else "memory unknown"
        
        logging.info(f"Console connection successful to {device['name']} ({device['console_host']}:{device['console_port']})")
        logging.info(f"Device hostname: {real_hostname}")
        logging.info(f"Device uptime: {uptime_info}")
        logging.info(f"Device memory: {memory_info}")
        
        print(f"  Connected successfully - {real_hostname}")
        print(f"  Uptime: {uptime_info}")
        
        # Get management IP if configured
        management_ip = None
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
            'accessible': True,
            'connection_type': 'console_telnet'
        }
        
    except Exception as e:
        logging.error(f"Console connection failed for {device['name']}: {str(e)}")
        print(f"  Failed to connect: {str(e)}")
        return None

# Main execution
if __name__ == "__main__":
    print(f"\n📊 SSH AUTOMATION DISCOVERY")
    print("=" * 50)
    
    # Use the hybrid script for real automation
    print("🔄 Redirecting to hybrid console-SSH script...")
    print("� For real SSH automation, use: python connectionGNS3/enable_hybrid.py")
    
    # Quick discovery using console
    devices = discover_console_devices()
    
    if devices:
        print(f"✅ Found {len(devices)} devices via console")
        
        active_count = 0
        for device in devices:
            result = test_console_connectivity(device)
            if result:
                active_count += 1
                print(f"  ✅ {result['name']} - {result.get('real_hostname', 'Unknown')}")
        
        print(f"\n� Summary: {active_count}/{len(devices)} devices accessible")
        print("\n🎯 For full automation features:")
        print("   python connectionGNS3/enable_hybrid.py")
        
    else:
        print("❌ No devices found!")
        print("Make sure GNS3 'Solange' project is running")
