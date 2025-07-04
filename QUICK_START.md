# Quick Start Guide - Solange Project Automation

## Your Current Setup
✅ GNS3 project "Solange" running  
✅ Baraton router configured with:
- SSH enabled (RSA 1034-bit keys)
- Username: admin
- Password: password123
- DHCP pool: 192.168.1.0/24
- Domain: solange.com

## Getting Started

### 1. First Time Setup
```powershell
# Install dependencies
python -m pip install -r requirements.txt

# Test your Baraton router specifically
python test_baraton.py
```

### 2. Run Main Automation Suite
```powershell
# Option 1: Use the batch file (easiest)
run_automation.bat

# Option 2: Run directly
python main.py
```

### 3. Discover All Devices
1. Run the main script
2. Choose option 1 (Initialize - Connect to GNS3 and discover devices)
3. This will find all your devices and create the configuration file

### 4. Common Operations

#### Backup All Configurations
```powershell
python scripts/backup_restore.py
```

#### Apply Bulk Configuration
1. Edit `config/bulk_config_commands.txt` with your commands
2. Run: `python scripts/bulk_configuration.py`

#### Password Management
```powershell
python scripts/password_rotation.py
```

## Your Network Configuration

Based on your Baraton setup, you have:
- DHCP pool serving 192.168.1.0/24
- Default gateway: 192.168.1.1
- DNS server: 8.8.8.8

## Quick Test Commands

### Test Baraton Router
```powershell
python test_baraton.py
```

### Test All Devices
```powershell
python connectionGNS3/enable.py
```

## Configuration Files Created

After running device discovery, you'll have:
- `config/devices_config.yaml` - Device connection details
- `config/bulk_config_commands.txt` - Commands for bulk operations
- `backups/` - Configuration backup files
- `logs/` - Operation logs

## Example Bulk Configuration Commands

Edit `config/bulk_config_commands.txt` to include commands like:
```
# Configure OSPF
router ospf 1
network 192.168.1.0 0.0.0.255 area 0
exit

# Configure SNMP
snmp-server community public ro
snmp-server location "Solange Project Lab"
```

## Troubleshooting

### Common Issues
1. **Connection refused**: Check if SSH is enabled on devices
2. **Authentication failed**: Verify username/password (admin/password123)
3. **Project not found**: Ensure GNS3 project "Solange" is open

### Check Logs
All operations are logged in the `logs/` directory:
- `gns3_automation.log` - Device discovery
- `backup_restore.log` - Backup operations
- `bulk_configuration.log` - Configuration changes
- `password_rotation.log` - Password changes

## Next Steps

1. **Add more devices**: Configure additional routers/switches with SSH
2. **Create templates**: Use the template system for different device types
3. **Schedule automation**: Set up regular backups and configuration checks
4. **Monitor**: Use the logging system to track all changes

## Security Best Practices

- Change default passwords regularly
- Use strong passwords in production
- Keep configuration backups secure
- Monitor access logs

---

**Ready to start!** Run `python test_baraton.py` first to verify connectivity to your configured router.
