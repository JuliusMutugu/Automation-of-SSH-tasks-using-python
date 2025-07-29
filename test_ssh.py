#!/usr/bin/env python3
"""
Quick SSH connectivity test
"""

import yaml
from netmiko import ConnectHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ssh_devices():
    """Test SSH connectivity to all configured devices"""
    try:
        with open('config/devices_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        devices = config.get('devices', [])
        
        for device in devices:
            print(f"\n--- Testing SSH to {device['name']} ({device['host']}) ---")
            
            # Create connection dict without 'name' field
            conn_params = {k: v for k, v in device.items() if k != 'name'}
            
            try:
                connection = ConnectHandler(**conn_params)
                connection.enable()
                
                # Get basic device info
                hostname_output = connection.send_command('show version | include hostname|uptime')
                version_output = connection.send_command('show version | include Software')
                
                print(f"✅ SSH connection successful!")
                print(f"📋 Device info: {hostname_output}")
                print(f"🔧 Software: {version_output}")
                
                connection.disconnect()
                
            except Exception as e:
                print(f"❌ SSH connection failed: {str(e)}")
    
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")

if __name__ == "__main__":
    print("=== SSH Connectivity Test ===")
    test_ssh_devices()
