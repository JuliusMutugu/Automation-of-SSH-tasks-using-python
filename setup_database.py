#!/usr/bin/env python3
"""
Database initialization script for SSH Automation Project
Run this script to set up the database and run migrations
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.connection import DatabaseManager, initialize_database

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/database_setup.log', encoding='utf-8')
        ]
    )

def load_environment():
    """Load environment variables"""
    # Try to load from .env file
    env_file = os.path.join(project_root, 'database', '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print(f"📝 Copy database/.env.example to database/.env and update with your settings")
        
        # Create .env from example if it doesn't exist
        example_file = os.path.join(project_root, 'database', '.env.example')
        if os.path.exists(example_file):
            import shutil
            shutil.copy(example_file, env_file)
            print(f"📋 Created {env_file} from example file")
            print("🔧 Please update the database credentials in the .env file")

def test_mysql_connection():
    """Test MySQL server connection"""
    try:
        import mysql.connector
        from mysql.connector import Error
        
        # Test basic connection (without database)
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', '2587')
        }
        
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            print("✅ MySQL server connection successful")
            connection.close()
            return True
             
    except Error as e:
        print(f"❌ MySQL connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check your credentials in the .env file")
        print("3. Verify the MySQL server is accessible")
        return False
    except ImportError:
        print("❌ mysql-connector-python is not installed")
        print("Run: pip install -r requirements.txt")
        return False

def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = os.path.join(project_root, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"📁 Created logs directory: {logs_dir}")

def main():
    """Main initialization function"""
    print("🚀 SSH Automation Database Setup")
    print("=" * 50)
    
    # Create logs directory
    create_logs_directory()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load environment
    load_environment()
    
    # Test MySQL connection
    if not test_mysql_connection():
        print("\n❌ Database setup failed - MySQL connection issue")
        return False
    
    try:
        # Initialize database
        print("\n📡 Initializing database...")
        if initialize_database():
            print("✅ Database initialization completed successfully!")
            
            # Show connection info
            print(f"\n📊 Database Information:")
            print(f"   Host: {os.getenv('DB_HOST', 'localhost')}")
            print(f"   Port: {os.getenv('DB_PORT', 3306)}")
            print(f"   Database: {os.getenv('DB_NAME', 'ssh_automation')}")
            print(f"   User: {os.getenv('DB_USER', 'root')}")
            
            # Test database manager
            db_manager = DatabaseManager()
            if db_manager.connection.test_connection():
                print("✅ Database manager test successful")
                
                # Show tables
                tables = db_manager.execute_query("SHOW TABLES", fetch=True)
                if tables:
                    print(f"\n📋 Created tables:")
                    for table in tables:
                        table_name = list(table.values())[0]
                        print(f"   - {table_name}")
                
                return True
            else:
                print("❌ Database manager test failed")
                return False
        else:
            print("❌ Database initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        print(f"❌ Database setup error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Run the device discovery: python connectionGNS3/enable_hybrid.py")
        print("2. Start the web interface: python web_gui/app.py")
        print("3. Access the web UI at: http://localhost:5001")
    else:
        print("\n❌ Database setup failed!")
        print("Please check the error messages above and try again.")
    
    input("\nPress Enter to exit...")
