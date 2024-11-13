import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
# Use Heroku's DATABASE_URL if available, otherwise use local database
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    # Heroku requires 'postgresql://' instead of 'postgres://'
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    DATABASE_URL = 'postgresql://localhost/file_segmentation'

# File processing configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1048576'))  # 1MB default
MAX_SEGMENTS = int(os.getenv('MAX_SEGMENTS', '100'))
DEFAULT_SEGMENTS = int(os.getenv('DEFAULT_SEGMENTS', '5'))

# Application configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
PROCESSED_DATA_DIR = os.path.join('data', 'processed')
RAW_DATA_DIR = os.path.join('data', 'raw')

# Ensure required directories exist
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(RAW_DATA_DIR, exist_ok=True)

# Database models configuration
class DatabaseConfig:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False