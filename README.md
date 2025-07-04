# Solange Project - GNS3 Network Automation Suite

This project provides SSH-based automation tools for managing network devices in your GNS3 "Solange" project.

## Features

- **Device Discovery**: Automatically connect to GNS3 and discover active devices
- **Configuration Backup**: Backup running and startup configurations
- **Bulk Configuration**: Apply configuration commands to multiple devices
- **Password Management**: Enable password authentication and rotate passwords
- **Configuration Restore**: Restore configurations from backup files
- **Template Management**: Create and apply configuration templates
- **Comprehensive Logging**: Track all operations with detailed logs

## Prerequisites

1. **GNS3 Running**: Ensure GNS3 is running on localhost:3080
2. **Device Configuration**: Your devices should have SSH enabled
3. **Python 3.7+**: Python with pip installed

## Quick Start

### 1. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 2. Start GNS3 Project
- Ensure your "Solange" project is open in GNS3
- Start all the devices you want to manage
- Verify SSH is configured on devices

### 3. Run the Main Script
```powershell
python main.py
```

### 4. Initialize Device Discovery
- Choose option 1 from the menu to discover devices
- This will create the device configuration file

## Project Structure

```
├── main.py                     # Main orchestration script
├── requirements.txt            # Python dependencies
├── connectionGNS3/
│   └── enable.py              # GNS3 connection and device discovery
├── scripts/
│   ├── backup_restore.py      # Configuration backup and restore
│   ├── bulk_configuration.py  # Bulk configuration management
│   └── password_rotation.py   # Password management
├── config/
│   ├── devices_config.yaml    # Auto-generated device configuration
│   ├── bulk_config_commands.txt # Commands for bulk configuration
│   └── templates/             # Configuration templates
├── backups/                   # Configuration backup files
└── logs/                      # Operation logs
```

## Usage Guide

### Device Discovery
Run the initialization to discover devices in your GNS3 project:
```powershell
python connectionGNS3/enable.py
```

### Backup Configurations
```powershell
python scripts/backup_restore.py
```

### Apply Bulk Configuration
1. Edit `config/bulk_config_commands.txt` with your commands
2. Run: `python scripts/bulk_configuration.py`

### Password Management
```powershell
python scripts/password_rotation.py
```

## Configuration Files

### Device Configuration (devices_config.yaml)
Auto-generated file containing device connection details:
```yaml
devices:
  - device_type: cisco_ios
    host: 192.168.1.1
    username: ''
    password: ''
    name: Router1
    timeout: 30
```

### Bulk Configuration Commands
Edit `config/bulk_config_commands.txt` to add commands:
```
# Configure OSPF
router ospf 1
network 192.168.1.0 0.0.0.255 area 0
exit
```

## Current Device Setup

Your devices currently have:
- ✅ SSH enabled
- ❌ Passwords disabled (no authentication required)
- 🔧 Ready for automation

## Enabling Password Authentication

If you want to enable password authentication:

1. Run the password management script
2. Choose option 1 (Enable password authentication)
3. Set username and password
4. The script will update all devices and configuration files

## Troubleshooting

### Common Issues

1. **"Project 'Solange' not found"**
   - Verify the project name in GNS3
   - Ensure the project is open

2. **"No devices found"**
   - Check that devices are started in GNS3
   - Verify devices have IP addresses

3. **SSH connection fails**
   - Verify SSH is enabled on devices
   - Check IP connectivity

### Logs
Check logs in the `logs/` directory for detailed error information.

## Security Notes

- Currently configured for no-password SSH (lab environment)
- Use password authentication for production networks
- Regularly rotate passwords using the password management script
- Keep configuration backups in a secure location

## Customization

### Adding New Scripts
1. Create script in `scripts/` directory
2. Follow the logging pattern from existing scripts
3. Add option to `main.py` menu

### Custom Templates
1. Create templates in `config/templates/`
2. Use the bulk configuration script to apply them

## Support

For issues or questions about this automation suite, check the logs directory for detailed error information.

---

**Solange Project Network Automation Suite**
*SSH-based automation for GNS3 network devices*
