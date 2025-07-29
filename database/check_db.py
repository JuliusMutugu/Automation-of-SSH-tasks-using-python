#!/usr/bin/env python3
"""
Quick database checker to see the current state
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseConnection, DatabaseConfig

def check_tables():
    """Check what tables exist in the database"""
    try:
        db_config = DatabaseConfig()
        db_connection = DatabaseConnection(db_config)
        connection = db_connection.get_connection()
        
        cursor = connection.cursor()
        
        # Check what tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("Tables in ssh_automation database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check migration tracking table
        if ('migrations',) in tables:
            print("\nMigration tracking table content:")
            cursor.execute("SELECT * FROM migrations ORDER BY executed_at")
            migrations = cursor.fetchall()
            for migration in migrations:
                print(f"  - {migration[1]} (executed at {migration[2]})")
        
        # Check if users table exists and has structure
        if ('users',) in tables:
            print("\nUsers table structure:")
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        else:
            print("\n❌ Users table does not exist!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_tables()
