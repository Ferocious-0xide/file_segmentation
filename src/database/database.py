from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/file_segmentation')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_session(self):
        """Get a new session."""
        return self.Session()
    
    def dispose(self):
        """Dispose of the engine."""
        self.engine.dispose()