#!/usr/bin/env python3
"""
Reset database migrations - clears migration tracking and recreates tables
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseConnection, DatabaseConfig

def reset_migrations():
    """Reset migration state and clean database"""
    try:
        db_config = DatabaseConfig()
        db_connection = DatabaseConnection(db_config)
        connection = db_connection.get_connection()
        
        cursor = connection.cursor()
        
        print("Resetting database migrations...")
        
        # Drop all tables (in reverse dependency order)
        tables_to_drop = [
            'user_sessions',
            'users', 
            'device_credentials',
            'config_changes',
            'backups',
            'operation_logs',
            'config_templates',
            'devices',
            'system_settings',
            'migrations'
        ]
        
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"⚠️  Warning dropping {table}: {e}")
        
        cursor.close()
        connection.close()
        
        print("✅ Database reset completed!")
        print("You can now run setup_database.py to recreate everything.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    reset_migrations()
