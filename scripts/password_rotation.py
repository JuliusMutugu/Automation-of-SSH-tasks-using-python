import time
from netmiko import ConnectHandler
import yaml

# Load device configurations from YAML file
def load_device_config(config_file='config/devices_config.yaml'):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

# Function to change the password of a device
def rotate_password(device, new_password):
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        print(f"Connected to {device['host']}")

        # Enter enable mode if necessary (for privileged commands)
        connection.send_command('enable')

        # Enter global configuration mode
        connection.send_command('configure terminal')

        # Change the password (assuming we're changing the console password as an example)
        connection.send_command(f"username {device['username']} password {new_password}")

        # Commit changes
        connection.send_command('end')
        connection.send_command('write memory')  # Save the configuration

        print(f"Password for {device['host']} changed successfully.")

        # Close the SSH connection
        connection.disconnect()
    except Exception as e:
        print(f"Failed to rotate password for {device['host']}: {e}")

# Function to rotate password for all devices
def rotate_password_for_all_devices(new_password):
    devices = load_device_config()
    for device in devices['devices']:
        rotate_password(device, new_password)

if __name__ == "__main__":
    # New password to be set
    new_password = "new_secure_password123"
    
    # Call the function to rotate passwords for all devices
    rotate_password_for_all_devices(new_password)
