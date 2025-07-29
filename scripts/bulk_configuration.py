#!/usr/bin/env python3
"""
Bulk Configuration Script for Network Devices
Applies bulk configuration commands to all devices via console.
Uses hybrid SSH-console setup with real device data.
"""

import os
import time
import yaml
import logging
from netmiko import ConnectHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '../logs/bulk_configuration.log')),
        logging.StreamHandler()
    ]
)

def load_device_config():
    """Load device configurations from YAML file"""
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/devices_config.yaml'))
    logging.info(f"Loading device config from: {config_file}")
    
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            logging.info(f"Loaded config: {config}")
            return config
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        return None
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return None

def load_configuration_commands():
    """Load bulk configuration commands from file"""
    config_file = os.path.join(os.path.dirname(__file__), '../config/bulk_config_commands.txt')
    
    try:
        with open(config_file, 'r') as file:
            commands = [line.strip() for line in file.readlines() 
                       if line.strip() and not line.strip().startswith('#')]
            logging.info(f"Loaded {len(commands)} configuration commands")
            return commands
    except FileNotFoundError:
        logging.error(f"Configuration commands file {config_file} not found.")
        return []

def apply_bulk_configuration(device, config_commands):
    """Apply configuration to a single device"""
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
        
        logging.info(f"Connecting to {device['name']} ({device['host']}:{device['port']}) via console")
        
        # Establish console telnet connection to the device
        connection = ConnectHandler(**clean_config)
        connection.enable()
        logging.info(f"Connected to {device['name']} - {device.get('real_hostname', 'Unknown')} via console")

        # Apply configuration commands using send_config_set (handles prompts automatically)
        logging.info(f"Applying {len(config_commands)} commands to {device['name']}")
        
        # Filter out comments and empty lines
        clean_commands = [cmd.strip() for cmd in config_commands 
                         if cmd.strip() and not cmd.strip().startswith('#')]
        
        # Apply all commands at once
        result = connection.send_config_set(clean_commands)
        logging.info(f"Configuration output for {device['name']}: {result[:200]}...")
        
        # Save configuration
        save_result = connection.send_command('write memory')
        logging.info(f"Save result for {device['name']}: {save_result}")

        logging.info(f"Configuration applied to {device['name']} ({device.get('real_hostname')}) successfully.")
        connection.disconnect()
        return True
        
    except Exception as e:
        logging.error(f"Failed to apply configuration to {device['name']}: {e}")
        return False

def main():
    """Main function to apply bulk configuration to all devices"""
    logging.info("Starting bulk configuration process...")
    
    # Load device configuration
    device_config = load_device_config()
    if not device_config:
        logging.error("Could not load device configuration. Exiting.")
        return
    
    devices = device_config.get('devices', [])
    if not devices:
        logging.error("No devices found in configuration. Exiting.")
        return
    
    # Load configuration commands
    config_commands = load_configuration_commands()
    if not config_commands:
        logging.warning("No configuration commands found. Nothing to apply.")
        return
    
    successful_configs = 0
    total_devices = len(devices)
    
    logging.info(f"Starting bulk configuration of {total_devices} devices...")
    logging.info(f"Commands to apply: {len(config_commands)}")
    
    # Apply configuration to each device
    for device in devices:
        if apply_bulk_configuration(device, config_commands):
            successful_configs += 1
        time.sleep(2)  # Delay between devices
    
    logging.info(f"Bulk configuration completed: {successful_configs}/{total_devices} devices successful")

if __name__ == "__main__":
    main()
