"""
Direct GNS3 connection using project ID
"""

from gns3fy import Gns3Connector

try:
    # Connect to GNS3
    gns3 = Gns3Connector(url="http://localhost:3080")
    print("✓ Connected to GNS3 server")
    
    # Use the project ID we found for Solange
    project_id = "9b01516e-96e2-45e3-b1ee-b11cafb4912a"
    
    # Get project directly by ID
    project = gns3.get_project(project_id=project_id)
    print(f"✓ Found project: {project}")
    print(f"Project type: {type(project)}")
    
    if hasattr(project, 'name'):
        print(f"Project name: {project.name}")
    
    if hasattr(project, 'nodes'):
        nodes = project.nodes()
        print(f"✓ Found {len(nodes)} nodes")
    else:
        print("Project object doesn't have nodes method")
        print(f"Available methods: {[method for method in dir(project) if not method.startswith('_')]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
