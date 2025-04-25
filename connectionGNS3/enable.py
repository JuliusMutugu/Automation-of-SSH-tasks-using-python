from gns3fy import Gns3Connector
from netmiko import ConnectHandler
import time

# Set up GNS3 connection
gns3 = Gns3Connector(url="http://localhost:3080")
# gns3.auth(username="your_username", password="your_password")

# Get the project and nodes
project = gns3.get_project(name="MiniProjectNet")
nodes = project.nodes()

# Collect device IPs
device_ips = [node.get_ip() for node in nodes]

# Function to rotate the password
def rotate_password_on_device(device_ip, new_password):
    device = {
        'device_type': 'cisco_ios',
        'host': device_ip,
        'username': 'admin',
        'password': 'admin_password',
    }

    try:
        connection = ConnectHandler(**device)
        connection.send_command('enable')
        connection.send_command('configure terminal')
        connection.send_command(f'username admin password {new_password}')
        connection.send_command('end')
        connection.send_command('write memory')
        connection.disconnect()
        print(f"Password rotated on {device_ip}")
    except Exception as e:
        print(f"Error rotating password on {device_ip}: {e}")

# Run password rotation on all devices
new_password = "new_secure_password"
for device_ip in device_ips:
    rotate_password_on_device(device_ip, new_password)
    time.sleep(1)  # Delay to avoid overwhelming devices
