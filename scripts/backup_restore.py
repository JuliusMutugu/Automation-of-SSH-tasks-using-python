import os
import time
from netmiko import ConnectHandler
from datetime import datetime
import yaml
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/backup_restore.log'),
        logging.StreamHandler()
    ]
)

# Function to load device configurations from the YAML file
def load_device_config(config_file='config/devices_config.yaml'):
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found. Please run the main connection script first.")
        return None

# Function to backup a device's configuration
def backup_device(device):
    try:
        # Clean device config for netmiko - remove metadata fields
        clean_config = {
            'device_type': device['device_type'],
            'host': device['host'],
            'port': device['port'],
            'username': device.get('username', ''),
            'password': device.get('password', ''),
            'secret': device.get('secret', ''),
            'timeout': device.get('timeout', 30),
            'fast_cli': device.get('fast_cli', False),
            'global_delay_factor': device.get('global_delay_factor', 2)
        }
        
        # Establish console telnet connection to the device
        connection = ConnectHandler(**clean_config)
        connection.enable()  # Enter enable mode
        logging.info(f"Connected to {device.get('name', device['host'])} via console")

        # Get the current device configuration
        config = connection.send_command('show running-config')
        startup_config = connection.send_command('show startup-config')

        # Create backup directory if it doesn't exist
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Save the configuration to a file
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        device_name = device.get('name', device['host']).replace(' ', '_')
        
        # Save running config
        running_backup_filename = f"{backup_dir}/{device_name}_running_config_{timestamp}.txt"
        with open(running_backup_filename, 'w') as backup_file:
            backup_file.write(config)
        
        # Save startup config
        startup_backup_filename = f"{backup_dir}/{device_name}_startup_config_{timestamp}.txt"
        with open(startup_backup_filename, 'w') as backup_file:
            backup_file.write(startup_config)
        
        logging.info(f"Backup of {device.get('name', device['host'])} saved to {running_backup_filename}")

        # Close the SSH connection
        connection.disconnect()
        return True
    except Exception as e:
        logging.error(f"Failed to backup {device.get('name', device['host'])}: {e}")
        return False

# Function to restore configuration to a device
def restore_device(device, config_file):
    try:
        # Read the configuration file
        with open(config_file, 'r') as file:
            config_lines = file.readlines()
        
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        connection.enable()
        logging.info(f"Connected to {device.get('name', device['host'])} for restore")

        # Enter configuration mode
        connection.send_command('configure terminal')
        
        # Apply configuration line by line
        for line in config_lines:
            line = line.strip()
            if line and not line.startswith('!'):  # Skip empty lines and comments
                connection.send_command(line)
                time.sleep(0.1)  # Small delay between commands

        # Save configuration
        connection.send_command('end')
        connection.send_command('write memory')
        
        logging.info(f"Configuration restored to {device.get('name', device['host'])}")
        connection.disconnect()
        return True
    except Exception as e:
        logging.error(f"Failed to restore configuration to {device.get('name', device['host'])}: {e}")
        return False

# Main function to backup all devices
def backup_all_devices():
    device_config = load_device_config()
    if not device_config:
        return
    
    successful_backups = 0
    total_devices = len(device_config['devices'])
    
    logging.info(f"Starting backup of {total_devices} devices...")
    
    for device in device_config['devices']:
        if backup_device(device):
            successful_backups += 1
        time.sleep(1)  # Delay between devices
    
    logging.info(f"Backup completed: {successful_backups}/{total_devices} devices successful")

# Function to list available backup files
def list_backup_files():
    backup_dir = "../backups"
    if not os.path.exists(backup_dir):
        logging.warning("No backup directory found")
        return []
    
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.txt')]
    return backup_files

if __name__ == "__main__":
    backup_all_devices()
