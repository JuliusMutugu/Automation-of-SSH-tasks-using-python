"""
Quick Device Discovery Script for Solange Project
Run this to discover and test connectivity to your GNS3 devices
"""

import sys
import os

# Add the parent directory to the path so we can import the enable module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now run the enable script
if __name__ == "__main__":
    print("=" * 60)
    print("  SOLANGE PROJECT - DEVICE DISCOVERY")
    print("=" * 60)
    
    try:
        # Import and run the enable script
        import connectionGNS3.enable
        print("\n" + "=" * 60)
        print("  DEVICE DISCOVERY COMPLETED")
        print("=" * 60)
    except Exception as e:
        print(f"Error during device discovery: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure GNS3 is running on localhost:3080")
        print("2. Ensure your 'Solange' project is open")
        print("3. Check that devices are started in GNS3")
        print("4. Verify network connectivity")
