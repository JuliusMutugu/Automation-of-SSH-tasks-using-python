import os
import time
from netmiko import ConnectHandler
from datetime import datetime
import yaml

# Function to load device configurations from the YAML file
def load_device_config(config_file='config/devices_config.yaml'):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

# Function to backup a device's configuration
def backup_device(device):
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        print(f"Connected to {device['host']}")

        # Get the current device configuration
        config = connection.send_command('show running-config')

        # Save the configuration to a file
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f"backups/{device['host']}_backup_{timestamp}.txt"
        with open(backup_filename, 'w') as backup_file:
            backup_file.write(config)
        
        print(f"Backup of {device['host']} saved to {backup_filename}")

        # Close the SSH connection
        connection.disconnect()
    except Exception as e:
        print(f"Failed to backup {device['host']}: {e}")

# Main function to backup all devices
def backup_all_devices():
    devices = load_device_config()
    for device in devices['devices']:
        backup_device(device)

if __name__ == "__main__":
    backup_all_devices()
