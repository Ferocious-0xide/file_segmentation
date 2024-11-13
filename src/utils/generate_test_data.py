import pandas as pd
import os
import numpy as np

def generate_test_file(num_records=1000, output_path='data/raw/test_data.csv'):
    """Generate a test CSV file with random data."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate random data
    data = {
        'id': range(num_records),
        'value': np.random.randint(1, 1000, num_records),
        'category': np.random.choice(['A', 'B', 'C'], num_records),
        'timestamp': pd.date_range(start='2023-01-01', periods=num_records, freq='H')
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    return output_path

if __name__ == '__main__':
    file_path = generate_test_file()
    print(f"Test file generated at: {file_path}")