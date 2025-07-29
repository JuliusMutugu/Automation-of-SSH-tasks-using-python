#!/usr/bin/env python3
"""
Manual Router SSH Configuration Guide
Follow these steps in the GNS3 console to configure SSH
"""

def print_configuration_guide():
    print("="*60)
    print("MANUAL SSH CONFIGURATION GUIDE FOR GNS3 ROUTER")
    print("="*60)
    print()
    print("STEP 1: Access Router Console")
    print("-" * 30)
    print("1. Open GNS3")
    print("2. Right-click on the R1 router")
    print("3. Select 'Console' from the context menu")
    print("4. A console window will open")
    print("5. Press ENTER to get the router prompt")
    print()
    
    print("STEP 2: Enter Configuration Mode")
    print("-" * 35)
    print("Type each command and press ENTER:")
    print()
    print("Router> enable")
    print("Router# configure terminal")
    print()
    
    print("STEP 3: Basic Router Setup")
    print("-" * 27)
    print("Router(config)# hostname R1")
    print("R1(config)# ip domain-name cisco.local")
    print()
    
    print("STEP 4: Create User Account")
    print("-" * 28)
    print("R1(config)# username admin privilege 15 secret password123")
    print()
    
    print("STEP 5: Generate RSA Keys for SSH")
    print("-" * 33)
    print("R1(config)# crypto key generate rsa modulus 1024")
    print("(When prompted, type 'yes' and press ENTER)")
    print("(Wait for key generation to complete - may take 30+ seconds)")
    print()
    
    print("STEP 6: Enable SSH")
    print("-" * 17)
    print("R1(config)# ip ssh version 2")
    print()
    
    print("STEP 7: Configure VTY Lines for SSH")
    print("-" * 37)
    print("R1(config)# line vty 0 4")
    print("R1(config-line)# transport input ssh")
    print("R1(config-line)# login local")
    print("R1(config-line)# exit")
    print()
    
    print("STEP 8: Configure Network Interface")
    print("-" * 36)
    print("R1(config)# interface FastEthernet0/0")
    print("R1(config-if)# ip address 192.168.100.10 255.255.255.0")
    print("R1(config-if)# no shutdown")
    print("R1(config-if)# description LAN Interface")
    print("R1(config-if)# exit")
    print()
    
    print("STEP 9: Save Configuration")
    print("-" * 27)
    print("R1(config)# exit")
    print("R1# write memory")
    print("(Or: R1# copy running-config startup-config)")
    print()
    
    print("STEP 10: Verify Configuration")
    print("-" * 31)
    print("R1# show ip interface brief")
    print("R1# show ip ssh")
    print("R1# show running-config | include username")
    print()
    
    print("="*60)
    print("EXPECTED RESULTS:")
    print("="*60)
    print("- FastEthernet0/0 should show 192.168.100.10 and status 'up up'")
    print("- SSH should show 'SSH Enabled - version 2.0'")
    print("- Username admin should be visible in config")
    print()
    
    print("AFTER CONFIGURATION:")
    print("="*60)
    print("Test SSH connection from your computer:")
    print("- From Windows Command Prompt: ssh admin@192.168.100.10")
    print("- Username: admin")
    print("- Password: password123")
    print()
    print("Then run the automation script:")
    print("- python enable.py")
    print()
    
    print("TROUBLESHOOTING:")
    print("="*60)
    print("If SSH still doesn't work:")
    print("1. Check interface status: show ip interface brief")
    print("2. Verify SSH is enabled: show ip ssh")
    print("3. Check if interface is connected in GNS3 topology")
    print("4. Verify your computer's network adapter is on 192.168.100.x network")
    print()

def create_verification_script():
    """Create a script to test SSH after manual configuration"""
    script_content = '''#!/usr/bin/env python3
"""
SSH Verification Script - Run this after manual configuration
"""

import socket
from netmiko import ConnectHandler

def verify_ssh_configuration():
    router_ip = "192.168.100.10"
    username = "admin"
    password = "password123"
    
    print(f"Testing SSH connection to {router_ip}...")
    
    # Test port 22 connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((router_ip, 22))
        sock.close()
        
        if result == 0:
            print("✓ SSH port 22 is accessible")
            
            # Test SSH authentication
            try:
                device = {
                    'device_type': 'cisco_ios',
                    'host': router_ip,
                    'username': username,
                    'password': password,
                    'secret': password,
                    'timeout': 15
                }
                
                connection = ConnectHandler(**device)
                connection.enable()
                
                # Get device information
                version = connection.send_command('show version | include uptime')
                interfaces = connection.send_command('show ip interface brief')
                ssh_status = connection.send_command('show ip ssh')
                
                connection.disconnect()
                
                print("✅ SSH authentication successful!")
                print(f"Router info: {version.strip()}")
                print(f"SSH status: {ssh_status.strip()}")
                print("\\nInterface status:")
                print(interfaces)
                
                print("\\n🎉 SSH configuration is working correctly!")
                print("You can now run the automation scripts.")
                return True
                
            except Exception as e:
                print(f"❌ SSH authentication failed: {e}")
                print("Please check username/password and try manual SSH test")
                return False
        else:
            print("✗ SSH port 22 is not accessible")
            print("Please verify router configuration and network connectivity")
            return False
            
    except Exception as e:
        print(f"Error testing connectivity: {e}")
        return False

if __name__ == "__main__":
    print("SSH Configuration Verification")
    print("="*40)
    verify_ssh_configuration()
'''
    
    with open('verify_ssh.py', 'w') as f:
        f.write(script_content)
    
    print("Created verify_ssh.py - run this after manual configuration")

if __name__ == "__main__":
    print_configuration_guide()
    print()
    create_verification_script()
    print()
    print("Next steps:")
    print("1. Follow the manual configuration guide above")
    print("2. Run: python verify_ssh.py")
    print("3. If successful, run: python enable.py")
