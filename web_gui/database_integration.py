"""
Database integration for Flask Web Server
"""
import os
import sys
import json
import logging
from datetime import datetime

# Add project root to path for database imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from database.connection import get_db_manager, initialize_database
    DATABASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Database module not available: {e}")
    DATABASE_AVAILABLE = False

class DatabaseIntegration:
    """Handles database operations for the web interface"""
    
    def __init__(self):
        self.db_manager = None
        self.logger = logging.getLogger(__name__)
        
        if DATABASE_AVAILABLE:
            try:
                self.db_manager = get_db_manager()
                self.logger.info("Database manager initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize database manager: {e}")
                self.db_manager = None
        else:
            self.logger.warning("Database not available - running in file-only mode")
    
    def is_available(self):
        """Check if database is available"""
        return self.db_manager is not None
    
    def sync_devices_to_database(self, devices_data):
        """Sync device data from JSON/YAML to database"""
        if not self.is_available():
            return False
        
        try:
            synced_count = 0
            for device in devices_data:
                # Prepare device data for database
                db_device_data = {
                    'name': device.get('name', 'unknown'),
                    'hostname': device.get('real_hostname', device.get('name')),
                    'ip_address': device.get('ip'),
                    'device_type': device.get('device_type', 'cisco_ios'),
                    'status': 'online' if device.get('accessible') else 'offline',
                    'connection_type': device.get('connection_type', 'ssh'),
                    'console_host': device.get('console_host'),
                    'console_port': device.get('console_port'),
                    'uptime': device.get('uptime'),
                    'memory_info': device.get('memory'),
                    'management_ip': device.get('management_ip'),
                    'last_seen': datetime.now().isoformat()
                }
                
                # Insert/update device in database
                if self.db_manager.insert_device(db_device_data):
                    synced_count += 1
            
            self.logger.info(f"Synced {synced_count} devices to database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error syncing devices to database: {e}")
            return False
    
    def get_devices_from_database(self):
        """Get devices from database"""
        if not self.is_available():
            return []
        
        try:
            devices = self.db_manager.get_devices()
            return devices if devices else []
        except Exception as e:
            self.logger.error(f"Error getting devices from database: {e}")
            return []
    
    def log_operation(self, operation_type, device_name=None, status='success', details=None):
        """Log operation to database"""
        if not self.is_available():
            return False
        
        try:
            return self.db_manager.log_operation(operation_type, device_name, status, details)
        except Exception as e:
            self.logger.error(f"Error logging operation: {e}")
            return False
    
    def get_operation_logs(self, limit=100):
        """Get operation logs from database"""
        if not self.is_available():
            return []
        
        try:
            logs = self.db_manager.get_operation_logs(limit)
            return logs if logs else []
        except Exception as e:
            self.logger.error(f"Error getting operation logs: {e}")
            return []
    
    def save_backup_info(self, device_name, backup_type, file_path, file_size=None):
        """Save backup information to database"""
        if not self.is_available():
            return False
        
        try:
            if file_size is None and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            
            return self.db_manager.save_backup(device_name, backup_type, file_path, file_size)
        except Exception as e:
            self.logger.error(f"Error saving backup info: {e}")
            return False
    
    def get_device_backups(self, device_name=None):
        """Get backup history from database"""
        if not self.is_available():
            return []
        
        try:
            backups = self.db_manager.get_backups(device_name)
            return backups if backups else []
        except Exception as e:
            self.logger.error(f"Error getting backups: {e}")
            return []

# Global database integration instance
db_integration = DatabaseIntegration()

def init_database_integration():
    """Initialize database integration"""
    global db_integration
    
    if not DATABASE_AVAILABLE:
        logging.warning("Database not available - running in file-only mode")
        return False
    
    try:
        # Try to initialize database
        if initialize_database():
            db_integration = DatabaseIntegration()
            logging.info("Database integration initialized successfully")
            return True
        else:
            logging.error("Database initialization failed")
            return False
    except Exception as e:
        logging.error(f"Database integration initialization error: {e}")
        return False

def get_devices_hybrid():
    """Get devices from both database and file cache"""
    devices = []
    
    # Try database first
    if db_integration.is_available():
        db_devices = db_integration.get_devices_from_database()
        if db_devices:
            # Convert database format to web format
            for db_device in db_devices:
                device = {
                    'name': db_device['name'],
                    'real_hostname': db_device['hostname'],
                    'ip': db_device['ip_address'],
                    'device_type': db_device['device_type'],
                    'status': db_device['status'],
                    'connection_type': db_device['connection_type'],
                    'console_host': db_device['console_host'],
                    'console_port': db_device['console_port'],
                    'uptime': db_device['uptime'],
                    'memory': db_device['memory_info'],
                    'management_ip': db_device['management_ip'],
                    'last_seen': db_device['last_seen'],
                    'accessible': db_device['status'] == 'online'
                }
                devices.append(device)
            
            logging.info(f"Loaded {len(devices)} devices from database")
            return devices
    
    # Fallback to file cache
    try:
        cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'devices_cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                devices = json.load(f)
            logging.info(f"Loaded {len(devices)} devices from file cache")
            
            # Sync to database if available
            if db_integration.is_available():
                db_integration.sync_devices_to_database(devices)
                
        return devices
    except Exception as e:
        logging.error(f"Error loading devices from file: {e}")
        return []

def log_operation_hybrid(operation_type, device_name=None, status='success', details=None):
    """Log operation to both database and file"""
    # Log to database
    db_integration.log_operation(operation_type, device_name, status, details)
    
    # Also log to application logs
    log_level = logging.INFO if status == 'success' else logging.ERROR
    message = f"Operation: {operation_type}"
    if device_name:
        message += f" on {device_name}"
    message += f" - Status: {status}"
    if details:
        message += f" - Details: {details}"
    
    logging.log(log_level, message)
