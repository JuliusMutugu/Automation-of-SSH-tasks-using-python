#!/usr/bin/env python3
"""
Database setup script for SSH Automation system
This script initializes the database and runs all migrations
"""

import sys
import os
import logging

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseConnection, DatabaseConfig
from database.migration_manager import MigrationManager

def setup_logging():
    """Configure logging for the setup process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('database_setup.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        db_config = DatabaseConfig()
        db_connection = DatabaseConnection(db_config)
        connection = db_connection.get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return True
        return False
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def main():
    """Main setup process"""
    logger = setup_logging()
    
    print("=" * 60)
    print("SSH Automation System - Database Setup")
    print("=" * 60)
    
    # Test database connection
    print("\n1. Testing database connection...")
    if not test_database_connection():
        print("❌ Database connection failed!")
        print("Please check your database configuration in database/.env")
        return False
    print("✅ Database connection successful!")
    
    # Initialize database connection
    print("\n2. Initializing database connection...")
    try:
        db_config = DatabaseConfig()
        db_connection = DatabaseConnection(db_config)
        logger.info("Database connection initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database connection: {e}")
        return False
    print("✅ Database connection initialized!")
    
    # Run migrations
    print("\n3. Running database migrations...")
    try:
        migration_manager = MigrationManager(db_connection)
        
        # Get migration files to show what will be executed
        migration_files = migration_manager.get_migration_files()
        executed_migrations = migration_manager.get_executed_migrations()
        
        if migration_files:
            print(f"Found {len(migration_files)} migration files:")
            for i, file in enumerate(migration_files, 1):
                status = "✅ executed" if file in executed_migrations else "⏳ pending"
                print(f"   {i}. {file} ({status})")
        
        print(f"Already executed: {executed_migrations}")
        print(f"Migration files order: {migration_files}")
        
        # Run the migrations
        if migration_manager.run_migrations():
            print("✅ All migrations executed successfully!")
        else:
            print("❌ Migration process failed!")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        logger.error(f"Migration process failed: {e}")
        return False
    
    print("\n4. Database setup completed successfully!")
    print("=" * 60)
    print("Your SSH Automation system is ready to use!")
    print("You can now start the web interface with:")
    print("  python web_gui/app.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
