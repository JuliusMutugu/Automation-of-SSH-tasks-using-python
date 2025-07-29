#!/usr/bin/env python3
"""
Check router interface status and fix SSH configuration
"""

import socket
import time

def check_and_fix_router_config(console_port=5000):
    """Connect to router and check/fix interface configuration"""
    
    print(f"Connecting to router console on localhost:{console_port}")
    
    try:
        # Connect to console port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('localhost', console_port))
        
        print("Connected to router console!")
        
        # Send initial commands to check status
        time.sleep(2)
        sock.send('\n'.encode())
        time.sleep(1)
        
        # Check interface status and fix configuration
        commands = [
            '',  # Enter
            'enable',  # Enter enable mode
            'show ip interface brief',  # Check interfaces
            'show ip ssh',  # Check SSH status
            'configure terminal',  # Enter configuration mode
            'interface FastEthernet0/0',  # Try FastEthernet instead
            'ip address 192.168.100.10 255.255.255.0',  # Set IP address
            'no shutdown',  # Enable interface
            'exit',  # Exit interface config
            'interface FastEthernet0/1',  # Configure second interface too
            'ip address 192.168.1.1 255.255.255.0',  # Set IP address
            'no shutdown',  # Enable interface
            'exit',  # Exit interface config
            'ip route 0.0.0.0 0.0.0.0 192.168.100.1',  # Default route
            'exit',  # Exit configuration mode
            'write memory',  # Save configuration
            'show ip interface brief',  # Verify interfaces
        ]
        
        print("\nChecking and fixing router configuration...")
        
        for i, cmd in enumerate(commands):
            print(f"\nStep {i+1}: {cmd if cmd else 'Press Enter'}")
            
            sock.send((cmd + '\n').encode())
            time.sleep(3)  # More time for each command
            
            # Read response
            try:
                sock.settimeout(5)
                response = sock.recv(8192).decode('utf-8', errors='ignore')
                if response.strip():
                    print(f"Response: {response.strip()}")
            except socket.timeout:
                print("(No response - continuing)")
            except:
                print("(Error reading response)")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_connectivity():
    """Test SSH connectivity to the router"""
    
    print("\nTesting connectivity...")
    
    # Test both potential IP addresses
    test_ips = ['192.168.100.10', '192.168.1.1']
    
    for ip in test_ips:
        print(f"\nTesting {ip}...")
        
        try:
            # Test SSH port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, 22))
            sock.close()
            
            if result == 0:
                print(f"✓ SSH port 22 is open on {ip}")
                
                # Try SSH with netmiko
                try:
                    from netmiko import ConnectHandler
                    device = {
                        'device_type': 'cisco_ios',
                        'host': ip,
                        'username': 'admin',
                        'password': 'password123',
                        'secret': 'password123',
                        'timeout': 10
                    }
                    
                    print(f"Testing SSH authentication to {ip}...")
                    connection = ConnectHandler(**device)
                    hostname = connection.send_command('show version | include uptime')
                    interfaces = connection.send_command('show ip interface brief')
                    connection.disconnect()
                    
                    print(f"✓ SSH successful to {ip}!")
                    print(f"Router hostname: {hostname.strip()}")
                    print("Interface status:")
                    print(interfaces)
                    return ip
                    
                except Exception as e:
                    print(f"SSH authentication failed to {ip}: {e}")
            else:
                print(f"✗ SSH port 22 not accessible on {ip}")
                
        except Exception as e:
            print(f"Error testing {ip}: {e}")
    
    return None

if __name__ == "__main__":
    print("Router Configuration Verification Tool")
    print("="*40)
    
    # Step 1: Check and fix configuration
    if check_and_fix_router_config(5000):
        print("\nWaiting 15 seconds for interfaces to come up...")
        time.sleep(15)
        
        # Step 2: Test connectivity
        working_ip = test_connectivity()
        
        if working_ip:
            print(f"\n🎉 Router is accessible via SSH at {working_ip}")
            print("You can now run the automation scripts!")
        else:
            print("\n⚠️ Router configuration updated but SSH still not accessible.")
            print("Please check the router manually through GNS3 console.")
    else:
        print("\n❌ Could not access router console.")
