-- Insert default users and update settings
-- Migration: 003_insert_default_users.sql

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role, is_active) VALUES
('admin', 'admin@solange.local', '$2b$12$LQv3c1yQd0J3lzgbAUoaUeL/E7KD8B7mBYz4D5E6F7G8H9I0J1K2L', 'System Administrator', 'admin', TRUE),
('operator', 'operator@solange.local', '$2b$12$MRw4d2zRe1K4mzgbBVpbVfM/F8LE9C8nCZz5E6F7G8H9I0J1K2L3M', 'Network Operator', 'operator', TRUE),
('viewer', 'viewer@solange.local', '$2b$12$NSx5e3aSf2L5nzgbCWqcWgN/G9MF0D9oDaz6F7G8H9I0J1K2L3M4N', 'Network Viewer', 'viewer', TRUE)
ON DUPLICATE KEY UPDATE
    email = VALUES(email),
    full_name = VALUES(full_name),
    role = VALUES(role),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

-- Add user management settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('user_registration_enabled', 'false', 'boolean', 'Allow new user registration'),
('password_min_length', '8', 'integer', 'Minimum password length requirement'),
('password_require_special', 'true', 'boolean', 'Require special characters in passwords'),
('max_login_attempts', '5', 'integer', 'Maximum failed login attempts before lockout'),
('account_lockout_minutes', '30', 'integer', 'Account lockout duration in minutes'),
('session_timeout_hours', '8', 'integer', 'User session timeout in hours'),
('password_reset_token_expires_minutes', '60', 'integer', 'Password reset token expiration in minutes'),
('require_email_verification', 'false', 'boolean', 'Require email verification for new accounts')
ON DUPLICATE KEY UPDATE
    setting_value = VALUES(setting_value),
    updated_at = CURRENT_TIMESTAMP;
