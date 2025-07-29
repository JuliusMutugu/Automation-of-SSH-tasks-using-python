#!/usr/bin/env python3
"""
Router SSH Configuration Script
This script will help configure SSH on your Cisco router through console access
"""

import socket
import time
import sys

def send_command(sock, command, wait_time=2):
    """Send a command to the router and wait for response"""
    print(f"Sending: {command}")
    sock.send((command + '\n').encode())
    time.sleep(wait_time)
    
    try:
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        print(f"Response: {response}")
        return response
    except:
        return ""

def configure_ssh_on_router(console_port=5000):
    """Configure SSH on the router through console connection"""
    
    print(f"Connecting to router console on localhost:{console_port}")
    
    try:
        # Connect to console port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('localhost', console_port))
        
        print("Connected to router console!")
        
        # Send initial commands
        time.sleep(2)
        sock.send('\n'.encode())
        time.sleep(1)
        
        # Configuration commands for SSH
        commands = [
            '',  # Enter
            'enable',  # Enter enable mode
            'configure terminal',  # Enter configuration mode
            'hostname R1',  # Set hostname
            'ip domain-name cisco.local',  # Set domain name (required for SSH)
            'username admin privilege 15 secret password123',  # Create user
            'crypto key generate rsa modulus 1024',  # Generate RSA keys
            'ip ssh version 2',  # Enable SSH version 2
            'line vty 0 4',  # Configure VTY lines
            'transport input ssh',  # Allow only SSH
            'login local',  # Use local authentication
            'exit',  # Exit line config
            'interface GigabitEthernet0/0',  # Configure interface
            'ip address 192.168.100.10 255.255.255.0',  # Set IP address
            'no shutdown',  # Enable interface
            'exit',  # Exit interface config
            'exit',  # Exit configuration mode
            'write memory',  # Save configuration
        ]
        
        print("\nConfiguring SSH on router...")
        
        for i, cmd in enumerate(commands):
            print(f"\nStep {i+1}: {cmd if cmd else 'Press Enter'}")
            
            if cmd == 'crypto key generate rsa modulus 1024':
                print("Generating RSA keys (this may take a moment)...")
                sock.send((cmd + '\n').encode())
                time.sleep(10)  # RSA key generation takes time
                
                # Send 'yes' if prompted
                sock.send('yes\n'.encode())
                time.sleep(5)
                
            else:
                sock.send((cmd + '\n').encode())
                time.sleep(2)
            
            # Read any response
            try:
                sock.settimeout(3)
                response = sock.recv(4096).decode('utf-8', errors='ignore')
                if response.strip():
                    print(f"Router response: {response.strip()}")
            except socket.timeout:
                pass
            except:
                print("No response received")
        
        print("\n" + "="*50)
        print("SSH Configuration Complete!")
        print("="*50)
        print("Router should now be accessible via:")
        print("- IP Address: 192.168.100.10")
        print("- Username: admin")
        print("- Password: password123")
        print("- SSH: ssh admin@192.168.100.10")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"Error configuring router: {e}")
        return False

def test_ssh_after_config():
    """Test SSH connection after configuration"""
    print("\nTesting SSH connection...")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('192.168.100.10', 22))
        sock.close()
        
        if result == 0:
            print("✓ SSH port 22 is open on 192.168.100.10")
            
            # Try SSH connection
            try:
                from netmiko import ConnectHandler
                device = {
                    'device_type': 'cisco_ios',
                    'host': '192.168.100.10',
                    'username': 'admin',
                    'password': 'password123',
                    'secret': 'password123',
                    'timeout': 10
                }
                
                connection = ConnectHandler(**device)
                hostname = connection.send_command('show version | include uptime')
                connection.disconnect()
                
                print("✓ SSH authentication successful!")
                print(f"Router info: {hostname.strip()}")
                return True
                
            except Exception as e:
                print(f"SSH connection failed: {e}")
                return False
        else:
            print("✗ SSH port 22 is not accessible")
            return False
            
    except Exception as e:
        print(f"Error testing SSH: {e}")
        return False

if __name__ == "__main__":
    print("Router SSH Configuration Tool")
    print("="*40)
    
    # Step 1: Configure SSH
    success = configure_ssh_on_router(5000)
    
    if success:
        print("\nWaiting 10 seconds for configuration to take effect...")
        time.sleep(10)
        
        # Step 2: Test SSH
        if test_ssh_after_config():
            print("\n🎉 SSH configuration successful!")
            print("You can now run the automation scripts.")
        else:
            print("\n⚠️ SSH configuration completed but connection test failed.")
            print("The router may need more time to initialize SSH services.")
    else:
        print("\n❌ SSH configuration failed.")
        print("Please try connecting manually through GNS3 console.")
