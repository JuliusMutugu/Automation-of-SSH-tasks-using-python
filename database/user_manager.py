"""
User Management Module for SSH Automation Project
Handles user registration, authentication, and session management
"""

import bcrypt
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from database.connection import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class UserManager:
    """Manages user accounts, authentication, and sessions"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            'valid': True,
            'errors': []
        }
        
        # Get password requirements from settings
        min_length = self.get_setting('password_min_length', 8)
        require_special = self.get_setting('password_require_special', True)
        
        if len(password) < min_length:
            result['valid'] = False
            result['errors'].append(f'Password must be at least {min_length} characters long')
        
        if not re.search(r'[A-Z]', password):
            result['valid'] = False
            result['errors'].append('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', password):
            result['valid'] = False
            result['errors'].append('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', password):
            result['valid'] = False
            result['errors'].append('Password must contain at least one digit')
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['valid'] = False
            result['errors'].append('Password must contain at least one special character')
        
        return result
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get system setting value"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT setting_value, setting_type FROM system_settings WHERE setting_key = %s",
                (key,)
            )
            result = cursor.fetchone()
            
            if result:
                value = result['setting_value']
                setting_type = result['setting_type']
                
                # Convert based on type
                if setting_type == 'boolean':
                    return value.lower() in ('true', '1', 'yes')
                elif setting_type == 'integer':
                    return int(value)
                elif setting_type == 'json':
                    import json
                    return json.loads(value)
                else:
                    return value
            
            return default
            
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def create_user(self, username: str, email: str, password: str, full_name: str = None, role: str = 'viewer') -> Dict[str, Any]:
        """Create a new user account"""
        result = {
            'success': False,
            'message': '',
            'user_id': None
        }
        
        try:
            # Check if registration is enabled
            if not self.get_setting('user_registration_enabled', False):
                result['message'] = 'User registration is currently disabled'
                return result
            
            # Validate inputs
            if not username or not email or not password:
                result['message'] = 'Username, email, and password are required'
                return result
            
            # Validate password
            password_validation = self.validate_password(password)
            if not password_validation['valid']:
                result['message'] = '; '.join(password_validation['errors'])
                return result
            
            # Validate email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                result['message'] = 'Invalid email format'
                return result
            
            # Check if user already exists
            if self.get_user_by_username(username):
                result['message'] = 'Username already exists'
                return result
            
            if self.get_user_by_email(email):
                result['message'] = 'Email already registered'
                return result
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, email, password_hash, full_name, role, True))
            
            connection.commit()
            result['user_id'] = cursor.lastrowid
            result['success'] = True
            result['message'] = 'User created successfully'
            
            logger.info(f"New user created: {username} ({email})")
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            result['message'] = 'Failed to create user account'
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
        
        return result
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Authenticate user login"""
        result = {
            'success': False,
            'message': '',
            'user': None,
            'session_token': None
        }
        
        try:
            user = self.get_user_by_username(username)
            if not user:
                result['message'] = 'Invalid username or password'
                return result
            
            # Check if account is locked
            if user.get('locked_until') and user['locked_until'] > datetime.now():
                result['message'] = 'Account is temporarily locked. Please try again later.'
                return result
            
            # Check if account is active
            if not user.get('is_active', False):
                result['message'] = 'Account is disabled'
                return result
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                self.record_failed_login(user['id'])
                result['message'] = 'Invalid username or password'
                return result
            
            # Reset login attempts on successful login
            self.reset_login_attempts(user['id'])
            
            # Update last login
            self.update_last_login(user['id'])
            
            # Create session
            session_token = self.create_session(user['id'], ip_address)
            
            # Remove sensitive data
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
            
            result['success'] = True
            result['message'] = 'Login successful'
            result['user'] = user_data
            result['session_token'] = session_token
            
            logger.info(f"User logged in: {username}")
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            result['message'] = 'Authentication failed'
        
        return result
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, username, email, password_hash, full_name, role, is_active,
                       last_login, login_attempts, locked_until, created_at, updated_at
                FROM users WHERE username = %s
            """, (username,))
            
            return cursor.fetchone()
            
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, username, email, password_hash, full_name, role, is_active,
                       last_login, login_attempts, locked_until, created_at, updated_at
                FROM users WHERE email = %s
            """, (email,))
            
            return cursor.fetchone()
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def record_failed_login(self, user_id: int):
        """Record failed login attempt and lock account if necessary"""
        try:
            max_attempts = self.get_setting('max_login_attempts', 5)
            lockout_minutes = self.get_setting('account_lockout_minutes', 30)
            
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # Increment login attempts
            cursor.execute("""
                UPDATE users 
                SET login_attempts = login_attempts + 1
                WHERE id = %s
            """, (user_id,))
            
            # Check if we need to lock the account
            cursor.execute("SELECT login_attempts FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            
            if result and result[0] >= max_attempts:
                locked_until = datetime.now() + timedelta(minutes=lockout_minutes)
                cursor.execute("""
                    UPDATE users 
                    SET locked_until = %s
                    WHERE id = %s
                """, (locked_until, user_id))
                
                logger.warning(f"User account locked due to failed login attempts: {user_id}")
            
            connection.commit()
            
        except Exception as e:
            logger.error(f"Error recording failed login: {e}")
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def reset_login_attempts(self, user_id: int):
        """Reset login attempts and unlock account"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET login_attempts = 0, locked_until = NULL
                WHERE id = %s
            """, (user_id,))
            
            connection.commit()
            
        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))
            
            connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Create user session"""
        try:
            session_token = secrets.token_urlsafe(32)
            session_timeout_hours = self.get_setting('session_timeout_hours', 8)
            expires_at = datetime.now() + timedelta(hours=session_timeout_hours)
            
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, session_token, ip_address, user_agent, expires_at))
            
            connection.commit()
            return session_token
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user data"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT s.user_id, s.expires_at, u.username, u.email, u.full_name, u.role, u.is_active
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = %s AND s.is_active = TRUE AND s.expires_at > NOW()
            """, (session_token,))
            
            session = cursor.fetchone()
            
            if session and session['is_active']:
                return {
                    'user_id': session['user_id'],
                    'username': session['username'],
                    'email': session['email'],
                    'full_name': session['full_name'],
                    'role': session['role']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def invalidate_session(self, session_token: str):
        """Invalidate session token"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = FALSE
                WHERE session_token = %s
            """, (session_token,))
            
            connection.commit()
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = FALSE
                WHERE expires_at <= NOW() AND is_active = TRUE
            """)
            
            connection.commit()
            logger.info("Expired sessions cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (excluding password hashes)"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active, last_login, 
                       login_attempts, locked_until, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
            """)
            
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user role"""
        try:
            if new_role not in ['admin', 'operator', 'viewer']:
                return False
            
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET role = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_role, user_id))
            
            connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))
            
            # Also invalidate all sessions
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = FALSE
                WHERE user_id = %s
            """, (user_id,))
            
            connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
        finally:
            if 'connection' in locals():
                self.db.return_connection(connection)
