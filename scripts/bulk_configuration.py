import time
from netmiko import ConnectHandler
import yaml
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/bulk_configuration.log'),
        logging.StreamHandler()
    ]
)

# Load device configurations from YAML file
def load_device_config(config_file='../config/devices_config.yaml'):
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found. Please run the main connection script first.")
        return None

# Function to apply configuration to a device
def apply_bulk_configuration(device, config_commands):
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        connection.enable()
        logging.info(f"Connected to {device.get('name', device['host'])}")

        # Enter global configuration mode
        connection.send_command('configure terminal')

        # Apply each configuration command
        for command in config_commands:
            if command.strip() and not command.strip().startswith('#'):  # Skip empty lines and comments
                logging.info(f"Applying command: {command.strip()}")
                result = connection.send_command(command.strip())
                time.sleep(0.5)  # Delay between commands to avoid overwhelming the device

        # Commit changes
        connection.send_command('end')
        connection.send_command('write memory')  # Save the configuration

        logging.info(f"Configuration applied to {device.get('name', device['host'])} successfully.")

        # Close the SSH connection
        connection.disconnect()
        return True
    except Exception as e:
        logging.error(f"Failed to apply configuration for {device.get('name', device['host'])}: {e}")
        return False

# Function to load bulk configuration commands from a file
def load_configuration_commands(config_file='../config/bulk_config_commands.txt'):
    try:
        with open(config_file, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        logging.error(f"Configuration commands file {config_file} not found.")
        # Create a sample file
        sample_commands = [
            "# Sample bulk configuration commands",
            "# Add your commands below (one per line)",
            "# Example commands:",
            "# interface loopback 0",
            "# ip address 192.168.1.1 255.255.255.255",
            "# no shutdown",
            "# exit",
            "# ip route 0.0.0.0 0.0.0.0 192.168.1.254"
        ]
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as file:
            file.write('\n'.join(sample_commands))
        logging.info(f"Created sample configuration file: {config_file}")
        return []

# Function to apply configuration to all devices
def apply_bulk_configuration_to_all_devices():
    device_config = load_device_config()
    if not device_config:
        return
    
    config_commands = load_configuration_commands()
    if not config_commands:
        logging.warning("No configuration commands found. Please edit the bulk_config_commands.txt file.")
        return

    successful_configs = 0
    total_devices = len(device_config['devices'])
    
    logging.info(f"Starting bulk configuration of {total_devices} devices...")
    logging.info(f"Commands to apply: {len(config_commands)}")

    for device in device_config['devices']:
        if apply_bulk_configuration(device, config_commands):
            successful_configs += 1
        time.sleep(2)  # Delay between devices
    
    logging.info(f"Bulk configuration completed: {successful_configs}/{total_devices} devices successful")

# Function to create custom configuration templates
def create_config_template(template_name, commands):
    template_dir = "../config/templates"
    os.makedirs(template_dir, exist_ok=True)
    
    template_file = f"{template_dir}/{template_name}.txt"
    with open(template_file, 'w') as file:
        file.write('\n'.join(commands))
    
    logging.info(f"Configuration template saved: {template_file}")

# Function to apply specific template to devices
def apply_template_to_devices(template_name, device_names=None):
    template_file = f"../config/templates/{template_name}.txt"
    
    if not os.path.exists(template_file):
        logging.error(f"Template file {template_file} not found")
        return
    
    device_config = load_device_config()
    if not device_config:
        return
    
    config_commands = load_configuration_commands(template_file)
    
    devices_to_configure = device_config['devices']
    if device_names:
        devices_to_configure = [d for d in device_config['devices'] if d.get('name') in device_names]
    
    for device in devices_to_configure:
        apply_bulk_configuration(device, config_commands)

if __name__ == "__main__":
    apply_bulk_configuration_to_all_devices()
