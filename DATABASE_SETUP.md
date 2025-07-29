# MySQL Database Integration for SSH Automation Project

This document explains how to set up and use MySQL database integration with the SSH Automation project.

## Overview

The database integration provides:
- **Device Management**: Store device information, status, and configuration
- **Operation Logging**: Track all automation operations and their results
- **Backup Management**: Store backup metadata and file references
- **Configuration Templates**: Reusable configuration templates
- **Audit Trail**: Complete history of changes and operations
- **Multi-Device Support**: Run on different devices with consistent data

## Prerequisites

1. **MySQL Server** (5.7 or higher)
2. **Python packages**: `mysql-connector-python`, `python-dotenv`, `cryptography`

## Quick Setup

### 1. Install MySQL Server

**Windows:**
```bash
# Download from: https://dev.mysql.com/downloads/mysql/
# Or use Chocolatey:
choco install mysql

# Or use XAMPP/WAMP for development
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

### 2. Run Database Setup

```bash
# Windows
setup_database.bat

# Or manually:
pip install mysql-connector-python python-dotenv cryptography
python setup_database.py
```

### 3. Configure Database Connection

Edit `database/.env` with your MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ssh_automation
DB_USER=root
DB_PASSWORD=your_mysql_password
```

## Database Schema

### Core Tables

#### `devices`
Stores network device information:
- `name`: Device name (unique)
- `hostname`: Real hostname from device
- `ip_address`: Management IP address
- `device_type`: Device type (cisco_ios, etc.)
- `status`: online/offline/unknown
- `connection_type`: ssh/telnet/console_telnet
- `console_host`, `console_port`: Console connection details
- `uptime`, `memory_info`: Real-time device information

#### `operation_logs`
Tracks all automation operations:
- `operation_type`: backup, config_change, discovery, etc.
- `device_name`: Target device
- `status`: success/failure/pending/running
- `details`: Operation details and results
- `duration_seconds`: Operation duration

#### `backups`
Stores backup file metadata:
- `device_name`: Source device
- `backup_type`: running-config/startup-config/full-backup
- `file_path`: Local file path
- `file_size`: File size in bytes
- `checksum`: File integrity verification

#### `config_templates`
Reusable configuration templates:
- `name`: Template name
- `template_content`: Configuration commands with variables
- `device_types`: Supported device types (JSON array)
- `variables`: Template variables (JSON object)

#### `config_changes`
Tracks configuration changes:
- `device_name`: Target device
- `change_type`: manual/template/bulk/restore
- `commands_applied`: Commands that were executed
- `config_before`, `config_after`: Configuration snapshots
- `success`: Whether change was successful

## Usage Examples

### Device Management

```python
from database.connection import get_db_manager

db = get_db_manager()

# Add/update a device
device_data = {
    'name': 'R1',
    'hostname': 'Baraton',
    'ip_address': '192.168.1.1',
    'device_type': 'cisco_ios',
    'status': 'online',
    'connection_type': 'console_telnet',
    'console_host': '127.0.0.1',
    'console_port': 5000,
    'uptime': '1 hour, 30 minutes',
    'last_seen': datetime.now().isoformat()
}
db.insert_device(device_data)

# Get all devices
devices = db.get_devices()

# Get specific device
device = db.get_device_by_name('R1')
```

### Operation Logging

```python
# Log a successful backup operation
db.log_operation(
    operation_type='backup',
    device_name='R1',
    status='success',
    details='Running configuration backed up successfully'
)

# Log a failed configuration change
db.log_operation(
    operation_type='config_change',
    device_name='R2',
    status='failure',
    details='Connection timeout during configuration'
)

# Get recent operation logs
logs = db.get_operation_logs(limit=50)
```

### Backup Management

```python
# Save backup information
db.save_backup(
    device_name='R1',
    backup_type='running-config',
    file_path='/backups/R1_2025-07-29_backup.txt',
    file_size=15430
)

# Get backup history
backups = db.get_backups('R1')  # For specific device
all_backups = db.get_backups()  # All devices
```

## Migration System

The project includes a migration system for database schema updates:

### Migration Files

Located in `database/migrations/`:
- `001_create_initial_tables.sql`: Initial schema
- `002_insert_default_settings.sql`: Default settings and templates

### Running Migrations

Migrations run automatically during setup:

```python
from database.migration_manager import MigrationManager
from database.connection import DatabaseConnection, DatabaseConfig

config = DatabaseConfig()
connection = DatabaseConnection(config)
migration_manager = MigrationManager(connection)

# Run all pending migrations
migration_manager.run_migrations()
```

### Creating New Migrations

```python
# Create a new migration file
content = """
ALTER TABLE devices ADD COLUMN location VARCHAR(100) NULL;
CREATE INDEX idx_devices_location ON devices(location);
"""

migration_manager.create_migration_file('add_device_location', content)
```

## Integration with Web Interface

The web interface automatically uses the database when available:

1. **Device Discovery**: Syncs discovered devices to database
2. **Operation Tracking**: All operations logged automatically
3. **Backup History**: Backup operations recorded with metadata
4. **Fallback Mode**: Falls back to file-based storage if database unavailable

### Hybrid Mode

The system operates in hybrid mode:
- **Primary**: Database storage for persistence and consistency
- **Fallback**: File-based cache for compatibility
- **Sync**: Automatic synchronization between database and files

## Configuration Options

### Environment Variables

```env
# Database Connection
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ssh_automation
DB_USER=root
DB_PASSWORD=

# Connection Pool
DB_POOL_SIZE=5
DB_CONNECTION_TIMEOUT=30

# Application Settings
BACKUP_RETENTION_DAYS=30
MAX_CONCURRENT_CONNECTIONS=5
LOG_RETENTION_DAYS=90

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key-here
```

### System Settings Table

Database-stored settings that can be modified:

```sql
SELECT * FROM system_settings;
```

Common settings:
- `backup_retention_days`: How long to keep backups
- `auto_backup_enabled`: Enable automatic backups
- `connection_timeout`: Default connection timeout
- `default_device_credentials`: Default login settings

## Security Considerations

1. **Credential Encryption**: Device passwords stored encrypted
2. **Database Access**: Use dedicated MySQL user with minimal privileges
3. **Network Security**: Restrict MySQL access to localhost/specific IPs
4. **Backup Security**: Secure backup file storage location

### Recommended MySQL User Setup

```sql
-- Create dedicated user for the application
CREATE USER 'ssh_automation'@'localhost' IDENTIFIED BY 'secure_password_here';

-- Grant necessary privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ssh_automation.* TO 'ssh_automation'@'localhost';
GRANT CREATE, DROP, ALTER ON ssh_automation.* TO 'ssh_automation'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check MySQL server is running
   - Verify credentials in `.env` file
   - Check firewall/network connectivity

2. **Migration Errors**
   - Check MySQL user has CREATE/ALTER privileges
   - Verify database exists
   - Check migration file syntax

3. **Import Errors**
   - Install required packages: `pip install -r requirements.txt`
   - Check Python path configuration

### Testing Database Connection

```python
python -c "
from database.connection import DatabaseManager
db = DatabaseManager()
if db.connection.test_connection():
    print('✅ Database connection successful')
else:
    print('❌ Database connection failed')
"
```

### Logs

Check logs for detailed error information:
- Application logs: `logs/`
- Database setup log: `logs/database_setup.log`

## Benefits of Database Integration

1. **Persistence**: Data survives system restarts and moves
2. **Consistency**: Single source of truth for device information
3. **Scalability**: Handle larger networks with better performance
4. **Reporting**: Rich querying capabilities for analysis
5. **Audit Trail**: Complete history of all operations
6. **Multi-User**: Support multiple users with proper access control
7. **Backup**: Reliable data backup and recovery options

## Deployment on Different Devices

The database integration makes it easy to deploy on different devices:

1. **Export Data**: Use MySQL dump to export data
2. **Setup New Device**: Run setup on new device
3. **Import Data**: Import the dumped data
4. **Configuration**: Update connection strings if needed

```bash
# Export data
mysqldump -u root -p ssh_automation > ssh_automation_backup.sql

# Import on new device
mysql -u root -p ssh_automation < ssh_automation_backup.sql
```

This ensures consistent device information, operation history, and configuration across different deployments.
