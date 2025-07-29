"""
Database configuration and connection management for SSH Automation Project
"""
import os
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import json

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        # Default configuration - can be overridden by environment variables
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.database = os.getenv('DB_NAME', 'ssh_automation')
        self.username = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        
        # Connection pool settings
        self.pool_name = 'ssh_automation_pool'
        self.pool_size = 5
        
        # Logging setup
        self.logger = logging.getLogger(__name__)
        
    def get_connection_config(self):
        """Get database connection configuration"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password,
            'autocommit': True,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
    
    def create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        try:
            # Connect without specifying database
            temp_config = self.get_connection_config()
            temp_config.pop('database')
            
            connection = mysql.connector.connect(**temp_config)
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.logger.info(f"Database '{self.database}' created or already exists")
            
            cursor.close()
            connection.close()
            return True
            
        except Error as e:
            self.logger.error(f"Error creating database: {e}")
            return False

class DatabaseConnection:
    """Database connection management with connection pooling"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = None
        self.logger = logging.getLogger(__name__)
        
    def create_connection_pool(self):
        """Create connection pool"""
        try:
            # Ensure database exists
            self.config.create_database_if_not_exists()
            
            # Create connection pool
            pool_config = self.config.get_connection_config()
            pool_config.update({
                'pool_name': self.config.pool_name,
                'pool_size': self.config.pool_size,
                'pool_reset_session': True
            })
            
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
            self.logger.info(f"Connection pool created successfully with {self.config.pool_size} connections")
            return True
            
        except Error as e:
            self.logger.error(f"Error creating connection pool: {e}")
            return False
    
    def get_connection(self):
        """Get connection from pool"""
        try:
            if not self.connection_pool:
                if not self.create_connection_pool():
                    return None
            
            connection = self.connection_pool.get_connection()
            return connection
            
        except Error as e:
            self.logger.error(f"Error getting connection from pool: {e}")
            return None
    
    def test_connection(self):
        """Test database connection"""
        try:
            connection = self.get_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                
                if result and result[0] == 1:
                    self.logger.info("Database connection test successful")
                    return True
                    
        except Error as e:
            self.logger.error(f"Database connection test failed: {e}")
            
        return False

class DatabaseManager:
    """Main database manager class"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.connection = DatabaseConnection(self.config)
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def initialize(self):
        """Initialize database and run migrations"""
        try:
            self.logger.info("Initializing database...")
            
            # Test connection
            if not self.connection.test_connection():
                self.logger.error("Failed to connect to database")
                return False
            
            # Run migrations
            from .migration_manager import MigrationManager
            migration_manager = MigrationManager(self.connection)
            
            if migration_manager.run_migrations():
                self.logger.info("Database initialization completed successfully")
                return True
            else:
                self.logger.error("Migration failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False
    
    def get_connection(self):
        """Get database connection"""
        return self.connection.get_connection()
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute database query"""
        try:
            connection = self.get_connection()
            if not connection:
                return None
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                if 'SELECT' in query.upper():
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
            else:
                result = cursor.rowcount
            
            cursor.close()
            connection.close()
            return result
            
        except Error as e:
            self.logger.error(f"Database query error: {e}")
            return None
    
    def insert_device(self, device_data):
        """Insert device information"""
        query = """
        INSERT INTO devices (name, hostname, ip_address, device_type, status, 
                           connection_type, console_host, console_port, uptime, 
                           memory_info, last_seen, created_at)
        VALUES (%(name)s, %(hostname)s, %(ip_address)s, %(device_type)s, %(status)s,
                %(connection_type)s, %(console_host)s, %(console_port)s, %(uptime)s,
                %(memory_info)s, %(last_seen)s, NOW())
        ON DUPLICATE KEY UPDATE
            hostname = VALUES(hostname),
            status = VALUES(status),
            uptime = VALUES(uptime),
            memory_info = VALUES(memory_info),
            last_seen = VALUES(last_seen),
            updated_at = NOW()
        """
        return self.execute_query(query, device_data)
    
    def get_devices(self):
        """Get all devices"""
        query = "SELECT * FROM devices ORDER BY name"
        return self.execute_query(query, fetch=True)
    
    def get_device_by_name(self, name):
        """Get device by name"""
        query = "SELECT * FROM devices WHERE name = %s"
        result = self.execute_query(query, (name,), fetch=True)
        return result[0] if result else None
    
    def log_operation(self, operation_type, device_name, status, details=None):
        """Log automation operation"""
        query = """
        INSERT INTO operation_logs (operation_type, device_name, status, details, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        return self.execute_query(query, (operation_type, device_name, status, details))
    
    def get_operation_logs(self, limit=100):
        """Get operation logs"""
        query = """
        SELECT * FROM operation_logs 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True)
    
    def save_backup(self, device_name, backup_type, file_path, file_size):
        """Save backup information"""
        query = """
        INSERT INTO backups (device_name, backup_type, file_path, file_size, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        return self.execute_query(query, (device_name, backup_type, file_path, file_size))
    
    def get_backups(self, device_name=None):
        """Get backup history"""
        if device_name:
            query = """
            SELECT * FROM backups 
            WHERE device_name = %s 
            ORDER BY created_at DESC
            """
            return self.execute_query(query, (device_name,), fetch=True)
        else:
            query = "SELECT * FROM backups ORDER BY created_at DESC"
            return self.execute_query(query, fetch=True)

# Global database manager instance
db_manager = None

def get_db_manager():
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def initialize_database():
    """Initialize database for the application"""
    manager = get_db_manager()
    return manager.initialize()
