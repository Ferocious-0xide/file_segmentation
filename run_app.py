import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Add src directory to Python path
src_path = project_root / 'src'
sys.path.append(str(src_path))

from src.utils.generate_test_data import generate_test_file

def setup_environment():
    """Setup the environment for the application."""
    # Create necessary directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Generate test data if it doesn't exist
    test_file_path = 'data/raw/test_data.csv'
    if not os.path.exists(test_file_path):
        generate_test_file(num_records=1000, output_path=test_file_path)
        print(f"Generated test file at: {test_file_path}")

def main():
    """Main entry point for the application."""
    # Setup environment
    setup_environment()
    
    # Import and run the main application
    from src.main import main
    main()

if __name__ == '__main__':
    main()