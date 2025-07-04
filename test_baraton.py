"""
Test script specifically for Baraton router in Solange project
This script will test the SSH connection with the credentials you configured
"""

from netmiko import ConnectHandler
import time

# Baraton router configuration (update IP as needed)
baraton_config = {
    'device_type': 'cisco_ios',
    'host': '192.168.1.1',  # Update this to your Baraton router's IP
    'username': 'admin',
    'password': 'password123',
    'secret': 'password123',  # Using the same password for enable
    'timeout': 30,
    'global_delay_factor': 2,
    'fast_cli': False
}

def test_baraton_connection():
    """Test SSH connection to Baraton router"""
    try:
        print("Connecting to Baraton router...")
        connection = ConnectHandler(**baraton_config)
        connection.enable()
        
        print("✓ SSH connection successful!")
        
        # Get hostname
        hostname = connection.send_command('show running-config | include hostname')
        print(f"Hostname: {hostname}")
        
        # Get version info
        version = connection.send_command('show version | include uptime')
        print(f"Uptime: {version}")
        
        # Get interface status
        interfaces = connection.send_command('show ip interface brief')
        print("\nInterface Status:")
        print(interfaces)
        
        # Check DHCP pool configuration
        dhcp_pool = connection.send_command('show ip dhcp pool')
        print("\nDHCP Pool Configuration:")
        print(dhcp_pool)
        
        # Check SSH configuration
        ssh_status = connection.send_command('show ip ssh')
        print("\nSSH Status:")
        print(ssh_status)
        
        connection.disconnect()
        print("\n✓ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if the IP address is correct")
        print("2. Verify the router is running and SSH is enabled")
        print("3. Confirm the username/password are correct")
        print("4. Check network connectivity")
        return False

def configure_additional_settings():
    """Apply additional configuration to Baraton router"""
    try:
        print("\nApplying additional configuration to Baraton...")
        connection = ConnectHandler(**baraton_config)
        connection.enable()
        
        # Enter configuration mode
        connection.send_command('configure terminal')
        
        # Additional configurations
        commands = [
            'ip ssh time-out 60',
            'ip ssh authentication-retries 3',
            'logging buffered 16384',
            'logging console warnings',
            'banner motd ^Welcome to Baraton Router - Solange Project^',
            'ntp server 8.8.8.8',
            'clock timezone UTC 0'
        ]
        
        for command in commands:
            print(f"Applying: {command}")
            connection.send_command(command)
            time.sleep(0.5)
        
        # Save configuration
        connection.send_command('end')
        connection.send_command('write memory')
        
        print("✓ Additional configuration applied successfully!")
        connection.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False

def backup_baraton_config():
    """Backup Baraton router configuration"""
    try:
        print("\nBacking up Baraton configuration...")
        connection = ConnectHandler(**baraton_config)
        connection.enable()
        
        # Get running config
        running_config = connection.send_command('show running-config')
        
        # Save to file
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f'../backups/Baraton_backup_{timestamp}.txt'
        
        with open(backup_filename, 'w') as f:
            f.write(running_config)
        
        print(f"✓ Configuration backed up to: {backup_filename}")
        connection.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False

def main():
    print("=" * 60)
    print("  BARATON ROUTER TEST - SOLANGE PROJECT")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Test SSH connection")
        print("2. Apply additional configuration")
        print("3. Backup configuration")
        print("4. Show current IP (update script if needed)")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            test_baraton_connection()
        elif choice == "2":
            configure_additional_settings()
        elif choice == "3":
            backup_baraton_config()
        elif choice == "4":
            print(f"\nCurrent configured IP: {baraton_config['host']}")
            print("If this is incorrect, please update the 'host' value in this script")
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
