#!/usr/bin/env python3
"""
Solange Project - GNS3 Network Automation Suite
Main orchestration script for SSH-based network automation tasks
"""

import sys
import os
import time
import subprocess
from datetime import datetime
import logging

# Add the connectionGNS3 directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'connectionGNS3'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main_automation.log'),
        logging.StreamHandler()
    ]
)

def print_banner():
    print("=" * 60)
    print("  SOLANGE PROJECT - GNS3 NETWORK AUTOMATION SUITE")
    print("=" * 60)
    print("  SSH-based automation for network devices")
    print("  Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

def print_menu():
    print("\nAvailable Operations:")
    print("1. Initialize - Connect to GNS3 and discover devices")
    print("2. Backup - Backup all device configurations")
    print("3. Bulk Configuration - Apply configuration to all devices")
    print("4. Password Management - Enable/rotate passwords")
    print("5. Device Status - Check connectivity and device info")
    print("6. Restore Configuration - Restore from backup")
    print("7. Create Configuration Template")
    print("8. Install Dependencies")
    print("9. View Logs")
    print("0. Exit")

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    try:
        print(f"\n{'-' * 40}")
        print(f"Starting: {description}")
        print(f"{'-' * 40}")
        
        # Get the absolute path to the script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_script_path = os.path.join(base_dir, script_path)
        
        result = subprocess.run([sys.executable, full_script_path], 
                              capture_output=False, text=True, cwd=base_dir)
        
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return True
        else:
            print(f"✗ {description} failed with return code {result.returncode}")
            return False
    except Exception as e:
        print(f"✗ Error running {description}: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    try:
        print("Installing required packages...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ All dependencies installed successfully")
            return True
        else:
            print(f"✗ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error installing dependencies: {e}")
        return False

def view_logs():
    """Display recent log entries"""
    log_files = [
        'logs/main_automation.log',
        'logs/gns3_automation.log',
        'logs/backup_restore.log',
        'logs/bulk_configuration.log',
        'logs/password_rotation.log'
    ]
    
    print("\nRecent log entries:")
    print("-" * 40)
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n{log_file}:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Show last 5 lines
                    for line in lines[-5:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"  Error reading log: {e}")

def check_prerequisites():
    """Check if required files and directories exist"""
    required_dirs = ['logs', 'config', 'backups']
    required_files = ['requirements.txt']
    
    missing_items = []
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
    
    for file in required_files:
        if not os.path.exists(file):
            missing_items.append(file)
    
    if missing_items:
        print(f"Warning: Missing files: {missing_items}")
        return False
    
    return True

def main():
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print("Some required files are missing. Please ensure all files are in place.")
    
    while True:
        print_menu()
        
        try:
            choice = input("\nEnter your choice (0-9): ").strip()
            
            if choice == "0":
                print("Exiting Solange Network Automation Suite...")
                break
                
            elif choice == "1":
                # Initialize - Connect to GNS3 and discover devices
                success = run_script("connectionGNS3/enable.py", "GNS3 Device Discovery")
                if success:
                    print("\n✓ Device discovery completed. You can now run other operations.")
                
            elif choice == "2":
                # Backup configurations
                success = run_script("scripts/backup_restore.py", "Configuration Backup")
                
            elif choice == "3":
                # Bulk configuration
                success = run_script("scripts/bulk_configuration.py", "Bulk Configuration")
                
            elif choice == "4":
                # Password management
                success = run_script("scripts/password_rotation.py", "Password Management")
                
            elif choice == "5":
                # Device status (re-run discovery)
                success = run_script("connectionGNS3/enable.py", "Device Status Check")
                
            elif choice == "6":
                # Restore configuration
                print("\nRestore Configuration:")
                print("This will run the backup script which includes restore functionality")
                print("Make sure you have backup files in the 'backups' directory")
                input("Press Enter to continue...")
                success = run_script("scripts/backup_restore.py", "Configuration Restore")
                
            elif choice == "7":
                # Create configuration template
                template_name = input("Enter template name: ")
                print("Enter configuration commands (one per line, empty line to finish):")
                commands = []
                while True:
                    command = input("> ")
                    if not command.strip():
                        break
                    commands.append(command)
                
                if commands:
                    template_dir = "config/templates"
                    os.makedirs(template_dir, exist_ok=True)
                    template_file = f"{template_dir}/{template_name}.txt"
                    
                    with open(template_file, 'w') as f:
                        f.write('\n'.join(commands))
                    
                    print(f"✓ Template saved: {template_file}")
                else:
                    print("No commands entered.")
                
            elif choice == "8":
                # Install dependencies
                install_dependencies()
                
            elif choice == "9":
                # View logs
                view_logs()
                
            else:
                print("Invalid choice. Please enter a number between 0-9.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            logging.error(f"Main script error: {e}")

if __name__ == "__main__":
    main()
