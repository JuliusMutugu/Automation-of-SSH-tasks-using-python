import time
from netmiko import ConnectHandler
import yaml
import logging
import getpass
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/password_rotation.log'),
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

# Function to enable password authentication on a device (since currently disabled)
def enable_password_auth(device, username, password, enable_secret=None):
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        connection.enable()
        logging.info(f"Connected to {device.get('name', device['host'])}")

        # Enter global configuration mode
        connection.send_command('configure terminal')

        # Set up username and password
        connection.send_command(f"username {username} privilege 15 password {password}")
        
        # Set enable secret if provided
        if enable_secret:
            connection.send_command(f"enable secret {enable_secret}")
        
        # Enable SSH authentication
        connection.send_command("line vty 0 4")
        connection.send_command("login local")
        connection.send_command("transport input ssh")
        connection.send_command("exit")
        
        # Ensure SSH is enabled
        connection.send_command("ip ssh version 2")
        connection.send_command("crypto key generate rsa general-keys modulus 2048")
        
        # Commit changes
        connection.send_command('end')
        connection.send_command('write memory')

        logging.info(f"Password authentication enabled on {device.get('name', device['host'])} for user {username}")

        # Close the SSH connection
        connection.disconnect()
        return True
    except Exception as e:
        logging.error(f"Failed to enable password auth for {device.get('name', device['host'])}: {e}")
        return False

# Function to change the password of a device
def rotate_password(device, username, new_password, enable_secret=None):
    try:
        # Establish SSH connection to the device
        connection = ConnectHandler(**device)
        connection.enable()
        logging.info(f"Connected to {device.get('name', device['host'])}")

        # Enter global configuration mode
        connection.send_command('configure terminal')

        # Change the password
        connection.send_command(f"username {username} password {new_password}")
        
        # Update enable secret if provided
        if enable_secret:
            connection.send_command(f"enable secret {enable_secret}")

        # Commit changes
        connection.send_command('end')
        connection.send_command('write memory')

        logging.info(f"Password for {device.get('name', device['host'])} changed successfully.")

        # Close the SSH connection
        connection.disconnect()
        return True
    except Exception as e:
        logging.error(f"Failed to rotate password for {device.get('name', device['host'])}: {e}")
        return False

# Function to rotate password for all devices
def rotate_password_for_all_devices(username, new_password, enable_secret=None):
    device_config = load_device_config()
    if not device_config:
        return
    
    successful_rotations = 0
    total_devices = len(device_config['devices'])
    
    logging.info(f"Starting password rotation for {total_devices} devices...")

    for device in device_config['devices']:
        if rotate_password(device, username, new_password, enable_secret):
            successful_rotations += 1
        time.sleep(1)  # Delay between devices
    
    logging.info(f"Password rotation completed: {successful_rotations}/{total_devices} devices successful")

# Function to enable password authentication for all devices
def enable_password_auth_for_all_devices(username, password, enable_secret=None):
    device_config = load_device_config()
    if not device_config:
        return
    
    successful_setups = 0
    total_devices = len(device_config['devices'])
    
    logging.info(f"Enabling password authentication for {total_devices} devices...")

    for device in device_config['devices']:
        if enable_password_auth(device, username, password, enable_secret):
            successful_setups += 1
        time.sleep(2)  # Longer delay for setup operations
    
    logging.info(f"Password authentication setup completed: {successful_setups}/{total_devices} devices successful")
    
    # Update the device configuration file to include the new credentials
    if successful_setups > 0:
        update_device_config_with_credentials(username, password, enable_secret)

# Function to update device configuration file with new credentials
def update_device_config_with_credentials(username, password, enable_secret=None):
    config_file = '../config/devices_config.yaml'
    device_config = load_device_config(config_file)
    
    if device_config:
        for device in device_config['devices']:
            device['username'] = username
            device['password'] = password
            if enable_secret:
                device['secret'] = enable_secret
        
        with open(config_file, 'w') as f:
            yaml.dump(device_config, f, default_flow_style=False)
        
        logging.info(f"Updated device configuration file with new credentials")

# Function to create password rotation schedule
def create_password_rotation_schedule():
    """Create a simple schedule file for password rotation reminders"""
    schedule_file = '../config/password_rotation_schedule.txt'
    
    current_date = datetime.now()
    next_rotation = current_date.replace(month=current_date.month + 3 if current_date.month <= 9 else current_date.month - 9, 
                                       year=current_date.year + (1 if current_date.month > 9 else 0))
    
    schedule_content = f"""
Password Rotation Schedule for Solange Project
Last Rotation: {current_date.strftime('%Y-%m-%d %H:%M:%S')}
Next Scheduled Rotation: {next_rotation.strftime('%Y-%m-%d')}
Rotation Frequency: Every 3 months

Notes:
- Remember to update all automation scripts with new passwords
- Test connectivity after password changes
- Keep backup of old passwords for 24 hours in case of issues
"""
    
    with open(schedule_file, 'w') as f:
        f.write(schedule_content)
    
    logging.info(f"Password rotation schedule created: {schedule_file}")

if __name__ == "__main__":
    print("Password Management for Solange Project")
    print("1. Enable password authentication (first time setup)")
    print("2. Rotate existing passwords")
    print("3. Create rotation schedule")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        username = input("Enter username to create: ")
        password = getpass.getpass("Enter password: ")
        enable_secret = getpass.getpass("Enter enable secret (optional, press Enter to skip): ")
        if not enable_secret.strip():
            enable_secret = None
        
        enable_password_auth_for_all_devices(username, password, enable_secret)
        
    elif choice == "2":
        username = input("Enter username: ")
        new_password = getpass.getpass("Enter new password: ")
        enable_secret = getpass.getpass("Enter new enable secret (optional, press Enter to skip): ")
        if not enable_secret.strip():
            enable_secret = None
        
        rotate_password_for_all_devices(username, new_password, enable_secret)
        
    elif choice == "3":
        create_password_rotation_schedule()
        
    else:
        print("Invalid choice")
