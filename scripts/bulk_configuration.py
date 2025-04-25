import time
from netmiko import ConnectHandler
import yaml

# Load device configurations from YAML file
def load_device_config(config_file='config/devices_config.yaml'):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

# Function to apply configuration to a device
def apply_bulk_configuration(device, config_commands):
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        print(f"Connected to {device['host']}")

        # Enter enable mode if necessary (for privileged commands)
        connection.send_command('enable')

        # Enter global configuration mode
        connection.send_command('configure terminal')

        # Apply each configuration command
        for command in config_commands:
            print(f"Applying command: {command}")
            connection.send_command(command)
            time.sleep(1)  # Delay between commands to avoid overwhelming the device

        # Commit changes
        connection.send_command('end')
        connection.send_command('write memory')  # Save the configuration

        print(f"Configuration applied to {device['host']} successfully.")

        # Close the SSH connection
        connection.disconnect()
    except Exception as e:
        print(f"Failed to apply configuration for {device['host']}: {e}")

# Function to load bulk configuration commands from a file
def load_configuration_commands(config_file='config/bulk_config_commands.txt'):
    with open(config_file, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Function to apply configuration to all devices
def apply_bulk_configuration_to_all_devices():
    devices = load_device_config()
    config_commands = load_configuration_commands()

    for device in devices['devices']:
        apply_bulk_configuration(device, config_commands)

if __name__ == "__main__":
    apply_bulk_configuration_to_all_devices()
