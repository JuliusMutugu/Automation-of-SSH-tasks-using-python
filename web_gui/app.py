"""
Flask Web Server for Solange Network Automation Suite
Provides a web-based GUI for network automation tasks
"""

from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import json
import os
import sys
import threading
import time
from datetime import datetime
import yaml
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.secret_key = 'solange-network-automation-2025'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for operation status
current_operation = None
operation_logs = []

class OperationManager:
    def __init__(self):
        self.current_operation = None
        self.logs = []
        self.progress = 0
        
    def start_operation(self, operation_name):
        self.current_operation = operation_name
        self.logs = []
        self.progress = 0
        
    def add_log(self, message, level='info'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def update_progress(self, progress):
        self.progress = progress
        
    def complete_operation(self):
        self.current_operation = None
        self.progress = 100

operation_manager = OperationManager()

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/devices/discover', methods=['POST'])
def discover_devices():
    """Discover devices using the GNS3 connection script"""
    try:
        operation_manager.start_operation('Device Discovery')
        
        # Run the device discovery script in a separate thread
        def run_discovery():
            try:
                operation_manager.add_log('Starting device discovery...')
                
                # Change to the correct directory and run the script
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'connectionGNS3', 'enable_new.py')
                
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(__file__))
                )
                
                if result.returncode == 0:
                    operation_manager.add_log('Device discovery completed successfully')
                    # Parse the output to extract device information
                    devices = parse_discovery_output(result.stdout)
                    save_devices_cache(devices)
                else:
                    operation_manager.add_log(f'Device discovery failed: {result.stderr}', 'error')
                    
            except Exception as e:
                operation_manager.add_log(f'Error during discovery: {str(e)}', 'error')
            finally:
                operation_manager.complete_operation()
        
        # Start discovery in background
        threading.Thread(target=run_discovery, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Device discovery started'})
        
    except Exception as e:
        logger.error(f"Device discovery error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of discovered devices"""
    try:
        devices = load_devices_cache()
        return jsonify({'success': True, 'devices': devices})
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup/all', methods=['POST'])
def backup_all_devices():
    """Backup all device configurations"""
    try:
        operation_manager.start_operation('Backup All Devices')
        
        def run_backup():
            try:
                operation_manager.add_log('Starting backup operation...')
                
                # Run the backup script
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'backup_restore.py')
                
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(__file__))
                )
                
                if result.returncode == 0:
                    operation_manager.add_log('Backup completed successfully')
                else:
                    operation_manager.add_log(f'Backup failed: {result.stderr}', 'error')
                    
            except Exception as e:
                operation_manager.add_log(f'Error during backup: {str(e)}', 'error')
            finally:
                operation_manager.complete_operation()
        
        threading.Thread(target=run_backup, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Backup started'})
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/apply', methods=['POST'])
def apply_configuration():
    """Apply bulk configuration to devices"""
    try:
        data = request.get_json()
        commands = data.get('commands', '')
        
        if not commands:
            return jsonify({'success': False, 'error': 'No commands provided'}), 400
        
        operation_manager.start_operation('Apply Configuration')
        
        def run_config():
            try:
                operation_manager.add_log('Applying configuration...')
                
                # Save commands to bulk config file
                config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bulk_config_commands.txt')
                with open(config_file, 'w') as f:
                    f.write(commands)
                
                # Run the bulk configuration script
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'bulk_configuration.py')
                
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(__file__))
                )
                
                if result.returncode == 0:
                    operation_manager.add_log('Configuration applied successfully')
                else:
                    operation_manager.add_log(f'Configuration failed: {result.stderr}', 'error')
                    
            except Exception as e:
                operation_manager.add_log(f'Error applying configuration: {str(e)}', 'error')
            finally:
                operation_manager.complete_operation()
        
        threading.Thread(target=run_config, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Configuration application started'})
        
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/security/password', methods=['POST'])
def manage_passwords():
    """Enable password authentication or rotate passwords"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'enable' or 'rotate'
        username = data.get('username', 'admin')
        password = data.get('password')
        enable_secret = data.get('enable_secret')
        
        if not password:
            return jsonify({'success': False, 'error': 'Password required'}), 400
        
        operation_manager.start_operation(f'Password {action.title()}')
        
        def run_password_operation():
            try:
                operation_manager.add_log(f'Starting password {action}...')
                
                # Run the password rotation script
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'password_rotation.py')
                
                # Create a temporary input file for the script
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    if action == 'enable':
                        f.write('1\n')  # Enable password auth
                    else:
                        f.write('2\n')  # Rotate passwords
                    f.write(f'{username}\n')
                    f.write(f'{password}\n')
                    if enable_secret:
                        f.write(f'{enable_secret}\n')
                    else:
                        f.write('\n')
                    temp_file = f.name
                
                try:
                    result = subprocess.run(
                        [sys.executable, script_path],
                        input=open(temp_file).read(),
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(os.path.dirname(__file__))
                    )
                    
                    if result.returncode == 0:
                        operation_manager.add_log(f'Password {action} completed successfully')
                    else:
                        operation_manager.add_log(f'Password {action} failed: {result.stderr}', 'error')
                finally:
                    os.unlink(temp_file)
                    
            except Exception as e:
                operation_manager.add_log(f'Error during password {action}: {str(e)}', 'error')
            finally:
                operation_manager.complete_operation()
        
        threading.Thread(target=run_password_operation, daemon=True).start()
        
        return jsonify({'success': True, 'message': f'Password {action} started'})
        
    except Exception as e:
        logger.error(f"Password management error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/operation/status', methods=['GET'])
def get_operation_status():
    """Get current operation status and logs"""
    return jsonify({
        'current_operation': operation_manager.current_operation,
        'logs': operation_manager.logs,
        'progress': operation_manager.progress
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get system logs"""
    try:
        log_files = [
            'logs/gns3_automation.log',
            'logs/backup_restore.log',
            'logs/bulk_configuration.log',
            'logs/password_rotation.log'
        ]
        
        all_logs = []
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        for log_file in log_files:
            log_path = os.path.join(base_dir, log_file)
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-50:]:  # Last 50 lines
                            if line.strip():
                                all_logs.append({
                                    'source': os.path.basename(log_file),
                                    'content': line.strip()
                                })
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
        
        return jsonify({'success': True, 'logs': all_logs})
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backups', methods=['GET'])
def get_backup_history():
    """Get backup file history"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        backups = []
        
        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.endswith('.txt'):
                    file_path = os.path.join(backup_dir, filename)
                    stat = os.stat(file_path)
                    backups.append({
                        'name': filename,
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'device': filename.split('_')[0] if '_' in filename else 'Unknown'
                    })
        
        backups.sort(key=lambda x: x['date'], reverse=True)
        return jsonify({'success': True, 'backups': backups})
        
    except Exception as e:
        logger.error(f"Error getting backup history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get configuration templates"""
    try:
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'templates')
        templates = []
        
        # Default templates
        default_templates = [
            {
                'name': 'Basic OSPF Configuration',
                'description': 'Configure OSPF routing protocol',
                'content': 'router ospf 1\nnetwork 192.168.1.0 0.0.0.255 area 0\nexit'
            },
            {
                'name': 'DHCP Server Setup',
                'description': 'Configure DHCP server settings',
                'content': 'ip dhcp pool LAN\nnetwork 192.168.1.0 255.255.255.0\ndefault-router 192.168.1.1\ndns-server 8.8.8.8\nexit'
            },
            {
                'name': 'Security Hardening',
                'description': 'Apply basic security settings',
                'content': 'line vty 0 4\nlogin local\ntransport input ssh\nexec-timeout 5 0\nexit\nip ssh time-out 60\nip ssh authentication-retries 3'
            }
        ]
        
        templates.extend(default_templates)
        
        # Load custom templates if they exist
        if os.path.exists(templates_dir):
            for filename in os.listdir(templates_dir):
                if filename.endswith('.txt'):
                    with open(os.path.join(templates_dir, filename), 'r') as f:
                        content = f.read()
                        templates.append({
                            'name': filename[:-4],  # Remove .txt extension
                            'description': 'Custom template',
                            'content': content
                        })
        
        return jsonify({'success': True, 'templates': templates})
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper functions
def parse_discovery_output(output):
    """Parse the output from device discovery script"""
    devices = []
    lines = output.split('\n')
    
    # This is a simplified parser - you might need to adjust based on actual output
    for line in lines:
        if 'Found device:' in line:
            parts = line.split()
            if len(parts) >= 4:
                name = parts[2]
                ip = parts[-1] if parts[-1] != parts[2] else '192.168.1.1'
                devices.append({
                    'name': name,
                    'ip': ip,
                    'type': 'router' if 'router' in name.lower() else 'switch' if 'switch' in name.lower() else 'device',
                    'status': 'online',
                    'lastSeen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
    
    # If no devices found in output, return default Baraton device
    if not devices:
        devices.append({
            'name': 'Baraton',
            'ip': '192.168.1.1',
            'type': 'router',
            'status': 'online',
            'lastSeen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return devices

def save_devices_cache(devices):
    """Save devices to cache file"""
    cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'devices_cache.json')
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(devices, f, indent=2)

def load_devices_cache():
    """Load devices from cache file"""
    cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'devices_cache.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return []

if __name__ == '__main__':
    print("=" * 60)
    print("  SOLANGE NETWORK AUTOMATION WEB INTERFACE")
    print("=" * 60)
    print("  Starting web server...")
    print("  Open your browser to: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
