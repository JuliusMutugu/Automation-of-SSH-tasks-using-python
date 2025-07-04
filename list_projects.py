"""
GNS3 Project Lister - Check what projects are available
"""

from gns3fy import Gns3Connector
import json

try:
    # Connect to GNS3
    gns3 = Gns3Connector(url="http://localhost:3080")
    print("✓ Connected to GNS3 server")
    
    # Get all projects
    projects = gns3.projects_summary()
    print(f"\nFound {len(projects)} projects:")
    
    for i, project in enumerate(projects, 1):
        print(f"{i}. {project}")
        
    print("\nDetailed project information:")
    for project in projects:
        print(f"Project: {project}")
        print(f"Type: {type(project)}")
        if hasattr(project, 'name'):
            print(f"Name: {project.name}")
        if hasattr(project, 'project_id'):
            print(f"ID: {project.project_id}")
        print("-" * 40)
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure GNS3 is running on localhost:3080")
