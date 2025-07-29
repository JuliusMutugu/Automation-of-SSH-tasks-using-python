"""
Database Migration Manager for SSH Automation Project
"""
import os
import logging
from datetime import datetime
import json

class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.logger = logging.getLogger(__name__)
        self.migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
    def create_migration_table(self):
        """Create migrations tracking table"""
        try:
            connection = self.db_connection.get_connection()
            cursor = connection.cursor()
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                migration_name VARCHAR(255) NOT NULL UNIQUE,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_migration_name (migration_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_sql)
            cursor.close()
            connection.close()
            
            self.logger.info("Migration tracking table created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating migration table: {e}")
            return False
    
    def get_executed_migrations(self):
        """Get list of executed migrations"""
        try:
            connection = self.db_connection.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT migration_name FROM migrations ORDER BY executed_at")
            executed = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return executed
            
        except Exception as e:
            self.logger.error(f"Error getting executed migrations: {e}")
            return []
    
    def mark_migration_executed(self, migration_name):
        """Mark migration as executed"""
        try:
            connection = self.db_connection.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "INSERT INTO migrations (migration_name) VALUES (%s)",
                (migration_name,)
            )
            
            cursor.close()
            connection.close()
            
            self.logger.info(f"Migration {migration_name} marked as executed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking migration as executed: {e}")
            return False
    
    def get_migration_files(self):
        """Get all migration files in order"""
        try:
            if not os.path.exists(self.migrations_dir):
                self.logger.warning(f"Migrations directory not found: {self.migrations_dir}")
                return []
            
            migration_files = []
            for filename in os.listdir(self.migrations_dir):
                if filename.endswith('.sql') and filename.startswith('0'):
                    migration_files.append(filename)
            
            # Sort by filename (which should include timestamp/order)
            migration_files.sort()
            return migration_files
            
        except Exception as e:
            self.logger.error(f"Error getting migration files: {e}")
            return []
    
    def execute_migration_file(self, migration_file):
        """Execute a single migration file"""
        try:
            file_path = os.path.join(self.migrations_dir, migration_file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            connection = self.db_connection.get_connection()
            cursor = connection.cursor()
            
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            cursor.close()
            connection.close()
            
            self.logger.info(f"Migration {migration_file} executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing migration {migration_file}: {e}")
            return False
    
    def run_migrations(self):
        """Run all pending migrations"""
        try:
            self.logger.info("Starting database migrations...")
            
            # Create migration tracking table
            if not self.create_migration_table():
                return False
            
            # Get executed migrations
            executed_migrations = self.get_executed_migrations()
            
            # Get all migration files
            migration_files = self.get_migration_files()
            
            if not migration_files:
                self.logger.info("No migration files found")
                return True
            
            # Execute pending migrations
            pending_count = 0
            for migration_file in migration_files:
                if migration_file not in executed_migrations:
                    self.logger.info(f"Executing migration: {migration_file}")
                    
                    if self.execute_migration_file(migration_file):
                        if self.mark_migration_executed(migration_file):
                            pending_count += 1
                        else:
                            return False
                    else:
                        return False
            
            if pending_count > 0:
                self.logger.info(f"Successfully executed {pending_count} migrations")
            else:
                self.logger.info("All migrations are up to date")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Migration process failed: {e}")
            return False
    
    def create_migration_file(self, name, content):
        """Create a new migration file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{name}.sql"
            file_path = os.path.join(self.migrations_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Migration file created: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error creating migration file: {e}")
            return None
