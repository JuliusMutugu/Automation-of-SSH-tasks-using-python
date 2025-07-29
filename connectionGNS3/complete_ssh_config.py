#!/usr/bin/env python3
"""
Comprehensive Router SSH Configuration
Waits for router to fully boot, then configures SSH properly
"""

import socket
import time
import re

def wait_for_router_prompt(sock, timeout=120):
    """Wait for router to finish booting and show prompt"""
    print("Waiting for router to finish booting...")
    
    start_time = time.time()
    buffer = ""
    
    while time.time() - start_time < timeout:
        try:
            sock.settimeout(2)
            data = sock.recv(1024).decode('utf-8', errors='ignore')
            buffer += data
            print(data, end='', flush=True)
            
            # Look for router prompt patterns
            if re.search(r'(Router>|Baraton>|R1>|\w+>)\s*$', buffer) or \
               re.search(r'Press RETURN to get started', buffer):
                print("\n*** Router prompt detected! ***")
                return True
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error waiting for prompt: {e}")
            break
    
    print(f"\nTimeout waiting for router prompt after {timeout} seconds")
    return False

def send_command_wait_prompt(sock, command, expected_prompt="R1#", timeout=10):
    """Send command and wait for specific prompt"""
    print(f"Sending: {command}")
    sock.send((command + '\n').encode())
    
    start_time = time.time()
    buffer = ""
    
    while time.time() - start_time < timeout:
        try:
            sock.settimeout(2)
            data = sock.recv(1024).decode('utf-8', errors='ignore')
            buffer += data
            
            if expected_prompt in buffer or (command == '' and '>' in buffer):
                print(f"Command completed. Buffer: {buffer[-100:]}")
                return buffer
                
        except socket.timeout:
            continue
    
    print(f"Timeout waiting for prompt '{expected_prompt}' after command: {command}")
    return buffer

def configure_router_ssh_complete():
    """Complete SSH configuration with proper boot handling"""
    
    console_port = 5000
    print(f"Connecting to router console on localhost:{console_port}")
    
    try:
        # Connect to console port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect(('localhost', console_port))
        
        print("Connected to router console!")
        
        # Wait for router to fully boot
        if not wait_for_router_prompt(sock):
            print("Router failed to boot properly")
            return False
        
        # Press Enter to get prompt
        print("\nGetting initial prompt...")
        sock.send('\n'.encode())
        time.sleep(2)
        
        # Try to read current prompt
        try:
            sock.settimeout(5)
            initial_response = sock.recv(2048).decode('utf-8', errors='ignore')
            print(f"Initial response: {initial_response}")
        except:
            pass
        
        print("\n" + "="*50)
        print("Starting SSH Configuration")
        print("="*50)
        
        # Configuration sequence
        commands = [
            ('enable', 'R1#'),
            ('configure terminal', 'R1(config)#'),
            ('hostname R1', 'R1(config)#'),
            ('ip domain-name cisco.local', 'R1(config)#'),
            ('username admin privilege 15 secret password123', 'R1(config)#'),
            ('crypto key generate rsa modulus 1024', 'R1(config)#'),
            ('ip ssh version 2', 'R1(config)#'),
            ('line vty 0 4', 'R1(config-line)#'),
            ('transport input ssh', 'R1(config-line)#'),
            ('login local', 'R1(config-line)#'),
            ('exit', 'R1(config)#'),
            ('interface FastEthernet0/0', 'R1(config-if)#'),
            ('ip address 192.168.100.10 255.255.255.0', 'R1(config-if)#'),
            ('no shutdown', 'R1(config-if)#'),
            ('description LAN Interface', 'R1(config-if)#'),
            ('exit', 'R1(config)#'),
            ('interface FastEthernet0/1', 'R1(config-if)#'),
            ('ip address 192.168.1.1 255.255.255.0', 'R1(config-if)#'),
            ('no shutdown', 'R1(config-if)#'),
            ('description WAN Interface', 'R1(config-if)#'),
            ('exit', 'R1(config)#'),
            ('exit', 'R1#'),
            ('write memory', 'R1#'),
        ]
        
        for i, (cmd, expected_prompt) in enumerate(commands):
            print(f"\nStep {i+1}: {cmd}")
            
            if 'crypto key generate rsa' in cmd:
                print("Generating RSA keys - this may take 30+ seconds...")
                sock.send((cmd + '\n').encode())
                time.sleep(3)
                
                # Handle potential prompts during key generation
                try:
                    response = sock.recv(2048).decode('utf-8', errors='ignore')
                    print(f"RSA response: {response}")
                    
                    if 'yes/no' in response.lower():
                        print("Responding 'yes' to key generation prompt")
                        sock.send('yes\n'.encode())
                        time.sleep(20)  # Wait for key generation
                    
                except:
                    time.sleep(20)  # Default wait time
                
            else:
                response = send_command_wait_prompt(sock, cmd, expected_prompt, timeout=15)
                
                # Handle special prompts
                if 'yes/no' in response.lower():
                    print("Detected yes/no prompt, responding 'yes'")
                    sock.send('yes\n'.encode())
                    time.sleep(5)
        
        print("\n" + "="*50)
        print("Configuration completed!")
        print("="*50)
        
        # Verify configuration
        print("\nVerifying configuration...")
        verification_commands = [
            'show ip interface brief',
            'show ip ssh',
            'show running-config | include username',
            'show crypto key mypubkey rsa'
        ]
        
        for cmd in verification_commands:
            print(f"\nVerification: {cmd}")
            response = send_command_wait_prompt(sock, cmd, 'R1#', timeout=10)
            print(f"Result: {response[-200:]}")  # Show last 200 chars
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"Error during configuration: {e}")
        return False

def test_final_ssh_connection():
    """Test SSH connection after complete configuration"""
    print("\n" + "="*50)
    print("Testing SSH Connection")
    print("="*50)
    
    # Wait a bit for SSH service to start
    print("Waiting 20 seconds for SSH service to fully initialize...")
    time.sleep(20)
    
    test_ips = ['192.168.100.10', '192.168.1.1']
    
    for ip in test_ips:
        print(f"\nTesting SSH to {ip}...")
        
        # Test port 22 connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, 22))
            sock.close()
            
            if result == 0:
                print(f"✓ SSH port 22 is open on {ip}")
                
                # Test SSH authentication
                try:
                    from netmiko import ConnectHandler
                    device = {
                        'device_type': 'cisco_ios',
                        'host': ip,
                        'username': 'admin',
                        'password': 'password123',
                        'secret': 'password123',
                        'timeout': 15,
                        'global_delay_factor': 2
                    }
                    
                    print(f"Testing SSH authentication to {ip}...")
                    connection = ConnectHandler(**device)
                    connection.enable()
                    
                    hostname = connection.send_command('show version | include uptime')
                    interfaces = connection.send_command('show ip interface brief')
                    ssh_status = connection.send_command('show ip ssh')
                    
                    connection.disconnect()
                    
                    print(f"✅ SSH SUCCESS to {ip}!")
                    print(f"Hostname info: {hostname.strip()}")
                    print("SSH Status:", ssh_status.strip()[:100])
                    print("Interfaces:")
                    print(interfaces)
                    
                    return ip
                    
                except Exception as e:
                    print(f"❌ SSH authentication failed to {ip}: {e}")
            else:
                print(f"✗ SSH port 22 not accessible on {ip}")
                
        except Exception as e:
            print(f"Error testing {ip}: {e}")
    
    return None

if __name__ == "__main__":
    print("Complete Router SSH Configuration Tool")
    print("="*50)
    print("This will:")
    print("1. Wait for router to fully boot")
    print("2. Configure SSH with proper credentials")
    print("3. Set up interfaces with IP addresses")
    print("4. Test SSH connectivity")
    print("="*50)
    
    if configure_router_ssh_complete():
        working_ip = test_final_ssh_connection()
        
        if working_ip:
            print(f"\n🎉 SUCCESS! Router is accessible via SSH at {working_ip}")
            print("\nCredentials:")
            print("- Username: admin")
            print("- Password: password123")
            print(f"- SSH Command: ssh admin@{working_ip}")
            print("\n✅ You can now run the automation scripts!")
        else:
            print("\n⚠️ Configuration completed but SSH test failed.")
            print("The router may need more time or manual verification.")
    else:
        print("\n❌ Router configuration failed.")
        print("Please check GNS3 and try again.")
