import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all modules can be imported."""
    try:
        # Test edge imports
        from edge.capture import MediaCapture
        from edge.object_detection import ObjectDetector
        from edge.violation_logic import ViolationLogicEngine

        # Test cloud imports
        from cloud.database import DatabaseManager
        from cloud.e_challan import EChallanGenerator

        # Test utils
        print("All imports successful!")
        assert True

    except ImportError as e:
        print(f"Import error: {e}")
        assert False, f"Import failed: {e}"

def test_config_files():
    """Test that config files exist and are valid JSON."""
    import json
    from pathlib import Path

    config_files = [
        'config/violation_rules.json',
        'config/incentive_config.json'
    ]

    for config_file in config_files:
        file_path = Path(config_file)
        assert file_path.exists(), f"Config file {config_file} does not exist"

        with open(file_path, 'r') as f:
            try:
                json.load(f)
                print(f"{config_file} is valid JSON")
            except json.JSONDecodeError as e:
                assert False, f"{config_file} is not valid JSON: {e}"

def test_directory_structure():
    """Test that required directories exist."""
    required_dirs = [
        'edge',
        'cloud',
        'dashboard',
        'models',
        'utils',
        'database',
        'tests',
        'config',
        'data',
        'templates',
        'dashboard/templates',
        'dashboard/static'
    ]

    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

if __name__ == "__main__":
    test_imports()
    test_config_files()
    test_directory_structure()
    print("All basic tests passed!")