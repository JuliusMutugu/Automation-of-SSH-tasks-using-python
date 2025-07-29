import socket
import threading
import time

def scan_ip_for_ssh(ip):
    """Check if SSH port 22 is open on an IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, 22))
        sock.close()
        
        if result == 0:
            print(f"SSH FOUND: {ip}:22 is open!")
            return ip
    except:
        pass
    return None

def scan_network_for_ssh():
    """Scan multiple network ranges for SSH services"""
    networks = [
        "192.168.1",
        "192.168.100", 
        "10.0.0",
        "172.16.0"
    ]
    
    ssh_hosts = []
    threads = []
    
    print("Scanning for SSH services...")
    
    for network in networks:
        print(f"Scanning {network}.1-20...")
        for i in range(1, 21):  # Scan first 20 IPs in each network
            ip = f"{network}.{i}"
            thread = threading.Thread(target=lambda ip=ip: scan_ip_for_ssh(ip) and ssh_hosts.append(ip))
            threads.append(thread)
            thread.start()
    
    # Wait for all scans to complete
    for thread in threads:
        thread.join()
    
    return ssh_hosts

if __name__ == "__main__":
    print("Quick Network SSH Scan")
    print("="*30)
    
    ssh_hosts = scan_network_for_ssh()
    
    if ssh_hosts:
        print(f"\nFound SSH services on: {ssh_hosts}")
        
        # Test SSH authentication on found hosts
        for host in ssh_hosts:
            print(f"\nTesting SSH auth to {host}...")
            credentials = [
                ('admin', 'password123'),
                ('admin', 'admin'),
                ('cisco', 'cisco'),
                ('root', 'root')
            ]
            
            for user, password in credentials:
                try:
                    from netmiko import ConnectHandler
                    device = {
                        'device_type': 'cisco_ios',
                        'host': host,
                        'username': user,
                        'password': password,
                        'secret': password,
                        'timeout': 5
                    }
                    
                    connection = ConnectHandler(**device)
                    info = connection.send_command('show version | include uptime')
                    connection.disconnect()
                    
                    print(f"SUCCESS: {host} - {user}:{password}")
                    print(f"Info: {info.strip()}")
                    break
                    
                except Exception as e:
                    continue
    else:
        print("\nNo SSH services found on any scanned networks")
        print("Router may need manual SSH configuration through GNS3 console")
