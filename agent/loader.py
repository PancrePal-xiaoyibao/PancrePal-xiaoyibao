import os
import importlib
import pkgutil
from pathlib import Path

def load_agents():
    """
    Dynamically load all agent modules in the agent directory.
    Each agent module should register itself with the registry.
    """
    # Get the current package directory
    package_dir = Path(__file__).parent
    
    # Iterate through all .py files in the agent directory
    for (_, module_name, _) in pkgutil.iter_modules([str(package_dir)]):
        # Skip special modules
        if module_name in ['__init__', 'base', 'registry', 'loader']:
            continue
        
        # Import the module
        try:
            importlib.import_module(f"agent.{module_name}")
            print(f"Loaded agent module: {module_name}")
        except Exception as e:
            print(f"Error loading agent module {module_name}: {e}")