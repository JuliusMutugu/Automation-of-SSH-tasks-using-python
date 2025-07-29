#!/usr/bin/env python3
import requests
import json

def get_console_ports():
    try:
        # Get GNS3 projects
        response = requests.get('http://localhost:3080/v2/projects')
        projects = response.json()
        
        solange_project = None
        for project in projects:
            if project['name'] == 'Solange':
                solange_project = project
                break
        
        if not solange_project:
            print("Solange project not found")
            return
        
        project_id = solange_project['project_id']
        print(f"Project ID: {project_id}")
        
        # Get nodes in the project
        nodes_response = requests.get(f'http://localhost:3080/v2/projects/{project_id}/nodes')
        nodes = nodes_response.json()
        
        print(f"\nFound {len(nodes)} nodes:")
        router_console = None
        
        for node in nodes:
            name = node.get('name', 'Unknown')
            console_port = node.get('console', 'N/A')
            status = node.get('status', 'unknown')
            node_type = node.get('node_type', 'unknown')
            
            print(f"- {name}: Console port {console_port}, Status: {status}, Type: {node_type}")
            
            # Look for router devices
            if any(keyword in name.lower() for keyword in ['r1', 'router', 'baraton']):
                router_console = console_port
                print(f"  ** ROUTER FOUND: {name} on console port {console_port}")
        
        if router_console:
            print(f"\nTo configure SSH on the router, connect to console port {router_console}")
            print(f"Use: telnet localhost {router_console}")
            print("Or use GNS3 console by right-clicking the router in GNS3")
        
        return router_console
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    get_console_ports()
