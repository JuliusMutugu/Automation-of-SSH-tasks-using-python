#!/usr/bin/env python3
"""
Complete SSH Configuration and Testing Script
This script will:
1. Check if SSH is already working
2. If not, configure SSH on the routers
3. Test SSH connectivity
4. Save working configuration
"""

import socket
import time
import threading
from netmiko import ConnectHandler
import requests
import json

def test_ssh_port(ip, timeout=3):
    """Test if SSH port 22 is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, 22))
        sock.close()
        return result == 0
    except:
        return False

def test_ssh_auth(ip, username, password):
    """Test SSH authentication"""
    try:
        device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': username,
            'password': password,
            'secret': password,
            'timeout': 10,
            'global_delay_factor': 1
        }
        
        connection = ConnectHandler(**device)
        connection.enable()
        hostname = connection.send_command('show version | include uptime')
        connection.disconnect()
        
        print(f"✅ SSH SUCCESS: {ip} with {username}:{password}")
        print(f"   Device info: {hostname.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ SSH auth failed for {ip}: {e}")
        return False

def scan_for_existing_ssh():
    """Scan for existing SSH services"""
    print("🔍 Scanning for existing SSH services...")
    
    # Test common IP ranges
    test_ips = [
        '192.168.100.10', '192.168.100.11', '192.168.100.1',
        '192.168.1.1', '192.168.1.2', '192.168.1.10',
        '10.0.0.1', '10.0.0.10', '172.16.0.1'
    ]
    
    ssh_devices = []
    for ip in test_ips:
        if test_ssh_port(ip):
            print(f"   SSH port open on {ip}")
            # Test common credentials
            credentials = [
                ('admin', 'password123'),
                ('admin', 'admin'),
                ('cisco', 'cisco'),
                ('admin', 'password')
            ]
            
            for user, pwd in credentials:
                if test_ssh_auth(ip, user, pwd):
                    ssh_devices.append({'ip': ip, 'username': user, 'password': pwd})
                    break
    
    return ssh_devices

def configure_router_ssh_via_console(console_port, target_ip):
    """Configure SSH on router through console"""
    print(f"🔧 Configuring SSH on router (console port {console_port}) for IP {target_ip}")
    
    try:
        # Connect to console
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        sock.connect(('localhost', console_port))
        
        print(f"   Connected to console port {console_port}")
        
        # Wait for router to be ready
        time.sleep(3)
        sock.send('\n'.encode())
        time.sleep(2)
        
        # Send configuration commands
        commands = [
            '',
            'enable',
            'configure terminal',
            'hostname R1',
            'ip domain-name cisco.local',
            'username admin privilege 15 secret password123',
            'crypto key generate rsa modulus 1024',
            'yes',  # Confirm key generation
            'ip ssh version 2',
            'line vty 0 4',
            'transport input ssh',
            'login local',
            'exit',
            f'interface FastEthernet0/0',
            f'ip address {target_ip} 255.255.255.0',
            'no shutdown',
            'exit',
            'exit',
            'write memory'
        ]
        
        for i, cmd in enumerate(commands):
            if i == 6:  # RSA key generation
                print("   Generating RSA keys (30+ seconds)...")
                sock.send((cmd + '\n').encode())
                time.sleep(25)  # Wait for key generation
            else:
                sock.send((cmd + '\n').encode())
                time.sleep(2)
        
        sock.close()
        print(f"   Configuration sent to router on port {console_port}")
        return True
        
    except Exception as e:
        print(f"   Error configuring router: {e}")
        return False

def get_gns3_router_consoles():
    """Get router console ports from GNS3"""
    try:
        # Get project info
        response = requests.get('http://localhost:3080/v2/projects')
        projects = response.json()
        
        solange_project = None
        for project in projects:
            if project['name'] == 'Solange':
                solange_project = project
                break
        
        if not solange_project:
            print("❌ Solange project not found")
            return []
        
        # Get nodes
        project_id = solange_project['project_id']
        nodes_response = requests.get(f'http://localhost:3080/v2/projects/{project_id}/nodes')
        nodes = nodes_response.json()
        
        routers = []
        for node in nodes:
            if node.get('status') == 'started':
                name = node.get('name', '')
                console_port = node.get('console')
                
                # Identify routers
                if any(keyword in name.lower() for keyword in ['r1', 'router', 'baraton']):
                    routers.append({
                        'name': name,
                        'console_port': console_port,
                        'target_ip': '192.168.100.10'
                    })
                elif 'r2' in name.lower():
                    routers.append({
                        'name': name,
                        'console_port': console_port,
                        'target_ip': '192.168.100.11'
                    })
        
        return routers
        
    except Exception as e:
        print(f"Error getting GNS3 info: {e}")
        return []

def main():
    print("=" * 60)
    print("SSH CONFIGURATION AND TESTING TOOL")
    print("=" * 60)
    
    # Step 1: Check for existing SSH
    existing_ssh = scan_for_existing_ssh()
    
    if existing_ssh:
        print(f"\n✅ Found {len(existing_ssh)} working SSH devices:")
        for device in existing_ssh:
            print(f"   {device['ip']} - {device['username']}:{device['password']}")
        
        print("\n🎉 SSH is already configured and working!")
        return existing_ssh
    
    print("\n❌ No working SSH found. Configuring routers...")
    
    # Step 2: Get router console information
    routers = get_gns3_router_consoles()
    
    if not routers:
        print("❌ No routers found in GNS3")
        return []
    
    print(f"\n📡 Found {len(routers)} routers to configure:")
    for router in routers:
        print(f"   {router['name']} - Console: {router['console_port']} - Target IP: {router['target_ip']}")
    
    # Step 3: Configure SSH on each router
    for router in routers:
        print(f"\n🔧 Configuring {router['name']}...")
        configure_router_ssh_via_console(router['console_port'], router['target_ip'])
    
    # Step 4: Wait for configuration to take effect
    print("\n⏳ Waiting 30 seconds for SSH services to start...")
    time.sleep(30)
    
    # Step 5: Test SSH again
    print("\n🧪 Testing SSH after configuration...")
    working_devices = []
    
    for router in routers:
        ip = router['target_ip']
        print(f"\nTesting {router['name']} at {ip}...")
        
        if test_ssh_port(ip, timeout=5):
            print(f"   SSH port open on {ip}")
            if test_ssh_auth(ip, 'admin', 'password123'):
                working_devices.append({
                    'name': router['name'],
                    'ip': ip,
                    'username': 'admin',
                    'password': 'password123'
                })
        else:
            print(f"   SSH port not accessible on {ip}")
    
    # Step 6: Summary
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    
    if working_devices:
        print(f"✅ Successfully configured {len(working_devices)} devices:")
        for device in working_devices:
            print(f"   {device['name']}: {device['ip']} ({device['username']}:{device['password']})")
        
        print(f"\n🎉 SSH configuration complete!")
        print("You can now run: python enable_new.py")
        
    else:
        print("❌ SSH configuration failed")
        print("Manual configuration may be required through GNS3 console")
    
    return working_devices

if __name__ == "__main__":
    main()
