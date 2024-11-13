from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from ..config import DatabaseConfig
from .models import Base, init_db

class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(DatabaseConfig.SQLALCHEMY_DATABASE_URI)
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
        init_db(self.engine)
    
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