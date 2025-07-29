"""
Flask Web Server for Solange Network Automation Suite
Provides a web-based GUI for network automation tasks with authentication
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash, make_response
from flask_session import Session
import subprocess
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
import yaml
import logging
from werkzeug.security import check_password_hash, generate_password_hash
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database integration
try:
    from database_integration import (
        db_integration, init_database_integration, 
        get_devices_hybrid, log_operation_hybrid
    )
    from database.user_manager import UserManager
    from database.connection import DatabaseManager
    DATABASE_ENABLED = True
    
    # Initialize user manager
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    
except ImportError as e:
    logger.warning(f"Database integration not available: {e}")
    DATABASE_ENABLED = False
    user_manager = None

app = Flask(__name__)
app.secret_key = 'solange-network-automation-2025-secure-key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'solange:'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Initialize session
Session(app)

# Default users (in production, store in database)
USERS = {
    'admin': generate_password_hash('admin123'),
    'operator': generate_password_hash('operator123'),
    'viewer': generate_password_hash('viewer123')
}

# User roles
USER_ROLES = {
    'admin': ['read', 'write', 'delete', 'configure'],
    'operator': ['read', 'write', 'configure'],
    'viewer': ['read']
}

# Authentication helpers
def is_logged_in():
    return 'user' in session and 'logged_in' in session and session['logged_in']

def get_current_user():
    return session.get('user', None)

def get_current_user_data():
    return session.get('user_data', None)

def has_permission(permission):
    if not is_logged_in():
        return False
    user_data = get_current_user_data()
    if not user_data:
        return False
    role = user_data.get('role', 'viewer')
    return permission in USER_ROLES.get(role, [])

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not is_logged_in():
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            if not has_permission(permission):
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('You do not have permission to perform this action.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        # Use database authentication if available
        if DATABASE_ENABLED and user_manager:
            try:
                auth_result = user_manager.authenticate_user(
                    username, 
                    password, 
                    request.remote_addr
                )
                
                if auth_result['success']:
                    user_data = auth_result['user']
                    session['user'] = user_data['username']
                    session['user_data'] = user_data
                    session['logged_in'] = True
                    session['login_time'] = datetime.now().isoformat()
                    session['session_token'] = auth_result['session_token']
                    session.permanent = True
                    
                    flash(f'Welcome, {user_data["username"]}!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('index'))
                else:
                    flash(auth_result['message'], 'error')
            except Exception as e:
                logger.error(f"Database authentication error: {e}")
                flash('Authentication service unavailable. Please try again.', 'error')
        else:
            # Fallback authentication (for development)
            flash('Database authentication not available. Please contact administrator.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    user = session.get('user', 'Unknown')
    session_token = session.get('session_token')
    
    # Invalidate database session if available
    if DATABASE_ENABLED and user_manager and session_token:
        try:
            user_manager.invalidate_session(session_token)
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    session.clear()
    flash(f'Goodbye, {user}!', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    # Check if registration is enabled
    registration_enabled = False
    password_min_length = 8
    password_require_special = True
    
    if DATABASE_ENABLED and user_manager:
        try:
            registration_enabled = user_manager.get_setting('user_registration_enabled', False)
            password_min_length = user_manager.get_setting('password_min_length', 8)
            password_require_special = user_manager.get_setting('password_require_special', True)
        except Exception as e:
            logger.error(f"Error getting registration settings: {e}")
    
    if request.method == 'POST' and registration_enabled:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Basic validation
        if not username or not email or not password:
            flash('Username, email, and password are required.', 'error')
            return render_template('register.html', 
                                 registration_enabled=registration_enabled,
                                 password_min_length=password_min_length,
                                 password_require_special=password_require_special)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html', 
                                 registration_enabled=registration_enabled,
                                 password_min_length=password_min_length,
                                 password_require_special=password_require_special)
        
        # Create user
        if DATABASE_ENABLED and user_manager:
            try:
                result = user_manager.create_user(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name or None,
                    role='viewer'  # Default role for new registrations
                )
                
                if result['success']:
                    flash('Account created successfully! You can now log in.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash(result['message'], 'error')
            except Exception as e:
                logger.error(f"Registration error: {e}")
                flash('Registration failed. Please try again.', 'error')
        else:
            flash('Registration service unavailable.', 'error')
    
    return render_template('register.html', 
                         registration_enabled=registration_enabled,
                         password_min_length=password_min_length,
                         password_require_special=password_require_special)

@app.route('/')
@require_auth
def index():
    """Serve the main web interface"""
    user = get_current_user()
    user_data = get_current_user_data()
    user_role = user_data.get('role', 'viewer') if user_data else 'viewer'
    user_permissions = USER_ROLES.get(user_role, [])
    return render_template('index.html', user=user, permissions=user_permissions, user_data=user_data)

@app.route('/api/devices/discover', methods=['POST'])
@require_permission('write')
def discover_devices():
    """Discover devices using the GNS3 connection script"""
    try:
        operation_manager.start_operation('Device Discovery')
        
        # Run the device discovery script in a separate thread
        def run_discovery():
            try:
                operation_manager.add_log('Starting device discovery...')
                
                # Change to the correct directory and run the script
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'connectionGNS3', 'enable_hybrid.py')
                
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(__file__))
                )
                
                if result.returncode == 0:
                    operation_manager.add_log('Device discovery completed successfully')
                    # The hybrid script already saves devices_cache.json, so just reload it
                    operation_manager.add_log('Device cache updated with latest discovery results')
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
@require_permission('write')
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
    operation_complete = operation_manager.current_operation is None
    return jsonify({
        'success': True,
        'current_operation': operation_manager.current_operation,
        'operation_complete': operation_complete,
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
@require_auth
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

def generate_backup_pdf(backup_data):
    """Generate PDF report for backup history"""
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    # Add title
    title = Paragraph("Solange Network Automation - Backup History Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Add generation info
    info_style = styles['Normal']
    info = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style)
    elements.append(info)
    elements.append(Paragraph(f"Generated by: {get_current_user()}", info_style))
    elements.append(Spacer(1, 20))
    
    # Create table data
    table_data = [['Device Name', 'File Name', 'Size', 'Date Created']]
    
    for backup in backup_data:
        table_data.append([
            backup.get('device', 'Unknown'),
            backup.get('filename', 'Unknown'),
            backup.get('size', 'Unknown'),
            backup.get('date', 'Unknown')
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Add footer
    footer = Paragraph(
        "This report contains backup file information from Solange Network Automation Suite.",
        styles['Normal']
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/api/backups/pdf', methods=['GET'])
@require_auth
def download_backup_pdf():
    """Download backup history as PDF"""
    try:
        # Get backup data (same as get_backup_history)
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        backups = []
        
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.endswith('.cfg') or file.endswith('.txt'):
                    file_path = os.path.join(backup_dir, file)
                    stat = os.path.stat(file_path)
                    
                    # Extract device name from filename
                    device_name = file.split('_')[0] if '_' in file else file.split('.')[0]
                    
                    backups.append({
                        'device': device_name,
                        'filename': file,
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        # Sort by date (newest first)
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        # Generate PDF
        pdf_buffer = generate_backup_pdf(backups)
        
        # Create response
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=backup_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return jsonify({'error': str(e)}), 500

def load_devices_cache():
    """Load devices from database or cache file"""
    if DATABASE_ENABLED:
        try:
            return get_devices_hybrid()
        except Exception as e:
            logger.error(f"Error loading devices from database: {e}")
    
    # Fallback to file cache
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
    print("  Open your browser to: http://localhost:5001")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
