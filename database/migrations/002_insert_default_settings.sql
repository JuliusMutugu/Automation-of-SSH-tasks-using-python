-- Insert default system settings
-- Migration: 002_insert_default_settings.sql

-- Default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('backup_retention_days', '30', 'integer', 'Number of days to retain device backups'),
('max_concurrent_connections', '5', 'integer', 'Maximum concurrent device connections'),
('connection_timeout', '30', 'integer', 'Connection timeout in seconds'),
('log_retention_days', '90', 'integer', 'Number of days to retain operation logs'),
('auto_backup_enabled', 'true', 'boolean', 'Enable automatic daily backups'),
('backup_schedule', '{"hour": 2, "minute": 0}', 'json', 'Daily backup schedule'),
('notification_settings', '{"email_enabled": false, "smtp_server": "", "recipients": []}', 'json', 'Notification configuration'),
('default_device_credentials', '{"username": "admin", "timeout": 30, "global_delay_factor": 2}', 'json', 'Default device connection settings'),
('gns3_server_url', 'http://localhost:3080', 'string', 'GNS3 server URL for device discovery'),
('web_ui_theme', 'default', 'string', 'Web interface theme'),
('session_timeout', '3600', 'integer', 'Web session timeout in seconds')
ON DUPLICATE KEY UPDATE
    setting_value = VALUES(setting_value),
    updated_at = CURRENT_TIMESTAMP;

-- Insert default configuration templates
INSERT INTO config_templates (name, description, template_content, device_types, variables) VALUES
(
    'Basic Security Hardening',
    'Basic security configuration for Cisco devices',
    'service password-encryption\nno service pad\nno ip http server\nno ip http secure-server\nip ssh version 2\nip ssh time-out 60\nip ssh authentication-retries 3\nline vty 0 4\n transport input ssh\n exec-timeout 5 0\n logging synchronous\nexit',
    '["cisco_ios", "cisco_asa"]',
    '{}'
),
(
    'NTP Configuration', 
    'Configure NTP servers',
    'ntp server {{ntp_server1}}\nntp server {{ntp_server2}}\nclock timezone {{timezone}} {{offset}}',
    '["cisco_ios"]',
    '{"ntp_server1": "pool.ntp.org", "ntp_server2": "time.google.com", "timezone": "UTC", "offset": "0"}'
),
(
    'SNMP v3 Setup',
    'Configure SNMP v3 for monitoring',
    'snmp-server group {{group_name}} v3 auth\nsnmp-server user {{username}} {{group_name}} v3 auth sha {{auth_password}} priv aes 128 {{priv_password}}\nsnmp-server host {{management_server}} version 3 auth {{username}}',
    '["cisco_ios"]',
    '{"group_name": "MONITORING", "username": "snmpuser", "auth_password": "authpassword", "priv_password": "privpassword", "management_server": "192.168.1.100"}'
),
(
    'Interface Description Update',
    'Update interface descriptions',
    'interface {{interface_name}}\n description {{description}}\n no shutdown\nexit',
    '["cisco_ios"]',
    '{"interface_name": "FastEthernet0/0", "description": "Management Interface"}'
)
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    template_content = VALUES(template_content),
    device_types = VALUES(device_types),
    variables = VALUES(variables),
    updated_at = CURRENT_TIMESTAMP;
