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

# Function to scan for SSH services on common IP ranges
def scan_for_ssh_devices(base_network="192.168.1", timeout=2):
    """Scan network range for devices with SSH enabled"""
    import socket
    import threading
    
    ssh_devices = []
    
    def check_ssh_port(ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, 22))
            sock.close()
            
            if result == 0:  # Port 22 is open
                print(f"✓ Found SSH service at {ip}")
                ssh_devices.append(ip)
        except Exception:
            pass
    
    print(f"🔍 Scanning {base_network}.1-254 for SSH services...")
    
    # Create threads to scan IPs in parallel for faster discovery
    threads = []
    for i in range(1, 255):
        ip = f"{base_network}.{i}"
        thread = threading.Thread(target=check_ssh_port, args=(ip,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    return ssh_devices

# Function to test SSH authentication
def test_ssh_auth(ip, credentials_list):
    """Test SSH authentication with different credential combinations"""
    for creds in credentials_list:
        try:
            device_config = {
                'device_type': 'cisco_ios',
                'host': ip,
                'username': creds['username'],
                'password': creds['password'],
                'secret': creds.get('secret', creds['password']),
                'timeout': 10,
                'global_delay_factor': 1,
                'fast_cli': False
            }
            
            connection = ConnectHandler(**device_config)
            # Try to get hostname to verify connection
            hostname = connection.send_command('show version | include uptime')
            connection.disconnect()
            
            print(f"✅ SSH authentication successful to {ip} with user '{creds['username']}'")
            return creds
            
        except Exception as e:
            continue
    
    print(f"❌ SSH authentication failed for {ip}")
    return None

# Collect device information with automatic discovery
devices_info = []
discovered_ips = []

# First, scan for SSH-enabled devices on multiple networks
potential_networks = ["192.168.1", "192.168.100", "10.0.0", "172.16.0"]
ssh_ips = []

for network in potential_networks:
    print(f"🔍 Scanning {network}.1-254 for SSH services...")
    network_ssh_ips = scan_for_ssh_devices(network)
    ssh_ips.extend(network_ssh_ips)
    if network_ssh_ips:
        print(f"✅ Found SSH devices in {network}.x network: {network_ssh_ips}")

if ssh_ips:
    print(f"\n📡 Found {len(ssh_ips)} devices with SSH enabled: {ssh_ips}")
    
    # Common credential combinations to try
    credential_combinations = [
        {'username': 'admin', 'password': 'password123', 'secret': 'password123'},
        {'username': 'admin', 'password': 'admin', 'secret': 'admin'},
        {'username': 'cisco', 'password': 'cisco', 'secret': 'cisco'},
        {'username': 'admin', 'password': 'password', 'secret': 'password'},
        {'username': 'admin', 'password': '', 'secret': ''},  # No password
    ]
    
    print("\n🔐 Testing SSH authentication...")
    
    for ip in ssh_ips:
        working_creds = test_ssh_auth(ip, credential_combinations)
        if working_creds:
            discovered_ips.append({'ip': ip, 'credentials': working_creds})

# Now map discovered IPs to GNS3 nodes
for node_data in nodes_data:
    if node_data.get('status') == "started":
        node_name = node_data.get('name', 'Unknown')
        node_id = node_data.get('node_id')
        console_port = node_data.get('console')
        
        print(f"\n📋 Processing node: {node_name}")
        
        # Try to match this node with discovered SSH devices
        device_ip = None
        device_creds = None
        
        # First check if we have a hardcoded mapping for this device
        device_ip_map = {
            'Baraton': ['192.168.1.1', '192.168.100.10'],  # Try multiple potential IPs
            'R1': ['192.168.1.1', '192.168.100.10'],
            'R2': ['192.168.1.2', '192.168.100.11'],
            'Router1': ['192.168.1.1', '192.168.100.10'],
            'Switch1': None,  # Layer 2 switch typically has no IP
            'PC1': ['192.168.1.10', '192.168.100.20'],
            'PC2': ['192.168.1.11', '192.168.100.21'],
        }
        
        expected_ips = device_ip_map.get(node_name, [])
        if isinstance(expected_ips, str):
            expected_ips = [expected_ips]
        
        # Check if any of the expected IPs is in our discovered SSH devices
        if expected_ips:
            for expected_ip in expected_ips:
                for discovered in discovered_ips:
                    if discovered['ip'] == expected_ip:
                        device_ip = expected_ip
                        device_creds = discovered['credentials']
                        print(f"✅ Matched {node_name} with SSH device at {device_ip}")
                        break
                if device_ip:  # Break outer loop if found
                    break
        
        # If no match found with expected IP, try to match by device type
        if not device_ip and node_name.lower() not in ['switch1', 'pc1', 'pc2', 'pc3']:
            # For routers/manageable devices, try to assign any available SSH IP
            for discovered in discovered_ips:
                # Check if this IP is not already assigned
                already_assigned = any(d.get('ip') == discovered['ip'] for d in devices_info)
                if not already_assigned:
                    device_ip = discovered['ip']
                    device_creds = discovered['credentials']
                    print(f"🔄 Auto-assigned {node_name} to SSH device at {device_ip}")
                    break
        
        if device_ip and device_creds:
            devices_info.append({
                'name': node_name,
                'ip': device_ip,
                'node_id': node_id,
                'console_port': console_port,
                'credentials': device_creds,
                'ssh_enabled': True
            })
            logging.info(f"Added SSH-enabled device: {node_name} at {device_ip}")
        else:
            # Add device without SSH capability
            devices_info.append({
                'name': node_name,
                'ip': expected_ips[0] if expected_ips else None,
                'node_id': node_id,
                'console_port': console_port,
                'credentials': None,
                'ssh_enabled': False
            })
            if expected_ips:
                print(f"⚠️ Device {node_name} expected at {expected_ips} but SSH not accessible")
            else:
                print(f"ℹ️ Device {node_name} (console-only) - no SSH expected")

# Function to create device connection configuration for SSH
def create_device_config(device_info):
    if not device_info.get('ssh_enabled') or not device_info.get('credentials'):
        # Use default credentials if none discovered
        credentials = {
            'username': 'admin',
            'password': 'password123',
            'secret': 'password123'
        }
    else:
        credentials = device_info['credentials']
    
    return {
        'device_type': 'cisco_ios',
        'host': device_info['ip'],
        'username': credentials['username'],
        'password': credentials['password'],
        'secret': credentials.get('secret', credentials['password']),
        'timeout': 30,
        'global_delay_factor': 2,
        'fast_cli': False
    }

# Function to test SSH connectivity to a device
def test_ssh_connection(device_info):
    if not device_info.get('ssh_enabled'):
        logging.info(f"Skipping SSH test for {device_info['name']} - SSH not enabled/configured")
        return False
        
    device_config = create_device_config(device_info)
    try:
        connection = ConnectHandler(**device_config)
        connection.enable()  # Enter enable mode
        hostname = connection.send_command('show version | include uptime')
        connection.disconnect()
        logging.info(f"✅ SSH connection successful to {device_info['name']} ({device_info['ip']})")
        return True
    except Exception as e:
        logging.error(f"❌ SSH connection failed to {device_info['name']} ({device_info['ip']}): {e}")
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
    print(f"\n📊 DISCOVERY SUMMARY")
    print("=" * 50)
    print(f"Total GNS3 nodes found: {len(devices_info)}")
    
    ssh_devices = [d for d in devices_info if d.get('ssh_enabled')]
    console_devices = [d for d in devices_info if not d.get('ssh_enabled')]
    
    print(f"SSH-enabled devices: {len(ssh_devices)}")
    print(f"Console-only devices: {len(console_devices)}")
    
    print(f"\n📋 Device Details:")
    for device in devices_info:
        ssh_status = "🔑 SSH" if device.get('ssh_enabled') else "🖥️ Console"
        ip_info = f" ({device['ip']})" if device.get('ip') else " (No IP)"
        print(f"  - {device['name']}: {ssh_status}{ip_info}")
    
    if ssh_devices:
        print("\n=== Testing SSH Connectivity ===")
        active_devices = []
        for device in ssh_devices:
            if test_ssh_connection(device):
                active_devices.append(device)
        
        print(f"\n✅ {len(active_devices)} devices are accessible via SSH")
        
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
            creds = device.get('credentials', {})
            config_data['devices'].append({
                'device_type': 'cisco_ios',
                'host': device['ip'],
                'username': creds.get('username', 'admin'),
                'password': creds.get('password', 'password123'),
                'secret': creds.get('secret', 'password123'),
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
        
        print(f"\n💾 Device configuration saved to config/devices_config.yaml")
        print("✅ You can now run the automation scripts!")
        
    else:
        print("\n❌ No SSH-enabled devices found!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify your router has SSH configured:")
        print("   - IP address assigned and interface up")
        print("   - 'ip domain-name' configured")
        print("   - RSA keys generated")
        print("   - Local user account created")
        print("   - VTY lines set for SSH")
        print("2. Test SSH manually: ssh admin@192.168.1.1")
        print("3. Check network connectivity between host and router")
        print("4. Verify credentials match what's configured on device")
