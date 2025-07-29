-- Initial database schema for SSH Automation Project
-- Migration: 001_create_initial_tables.sql

-- Devices table - stores network device information
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    hostname VARCHAR(100) NULL,
    ip_address VARCHAR(45) NULL,
    device_type VARCHAR(50) NOT NULL DEFAULT 'cisco_ios',
    status ENUM('online', 'offline', 'unknown') DEFAULT 'unknown',
    connection_type ENUM('ssh', 'telnet', 'console_telnet') DEFAULT 'ssh',
    console_host VARCHAR(45) NULL,
    console_port INT NULL,
    uptime VARCHAR(255) NULL,
    memory_info TEXT NULL,
    management_ip VARCHAR(45) NULL,
    last_seen TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_ip_address (ip_address),
    INDEX idx_status (status),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Operation logs table - stores automation operation history
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_type VARCHAR(100) NOT NULL,
    device_name VARCHAR(100) NULL,
    status ENUM('success', 'failure', 'pending', 'running') NOT NULL,
    details TEXT NULL,
    error_message TEXT NULL,
    duration_seconds INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_operation_type (operation_type),
    INDEX idx_device_name (device_name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (device_name) REFERENCES devices(name) 
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Backups table - stores device backup information
CREATE TABLE IF NOT EXISTS backups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    backup_type ENUM('running-config', 'startup-config', 'full-backup') NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NULL,
    checksum VARCHAR(64) NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_device_name (device_name),
    INDEX idx_backup_type (backup_type),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (device_name) REFERENCES devices(name) 
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Configuration templates table - stores reusable configuration templates
CREATE TABLE IF NOT EXISTS config_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    template_content TEXT NOT NULL,
    device_types JSON NULL,
    variables JSON NULL,
    created_by VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Configuration changes table - tracks configuration changes
CREATE TABLE IF NOT EXISTS config_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    change_type ENUM('manual', 'template', 'bulk', 'restore') NOT NULL,
    template_id INT NULL,
    commands_applied TEXT NOT NULL,
    config_before LONGTEXT NULL,
    config_after LONGTEXT NULL,
    applied_by VARCHAR(100) NULL,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_device_name (device_name),
    INDEX idx_change_type (change_type),
    INDEX idx_created_at (created_at),
    INDEX idx_success (success),
    
    FOREIGN KEY (device_name) REFERENCES devices(name) 
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES config_templates(id) 
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Device credentials table (encrypted) - stores device access credentials
CREATE TABLE IF NOT EXISTS device_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    enable_secret_encrypted TEXT NULL,
    ssh_key_path VARCHAR(500) NULL,
    encryption_method VARCHAR(50) DEFAULT 'AES',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_device_name (device_name),
    
    FOREIGN KEY (device_name) REFERENCES devices(name) 
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System settings table - stores application configuration
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NULL,
    setting_type ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
