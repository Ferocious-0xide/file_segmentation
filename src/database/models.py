from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid

Base = declarative_base()

class FileProcess(Base):
    """Represents a file processing job."""
    __tablename__ = 'file_processes'
    
    id = Column(Integer, primary_key=True)
    process_uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    total_segments = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    total_records = Column(Integer, default=0)
    segments = relationship("Segment", back_populates="file_process", cascade="all, delete-orphan")

class Segment(Base):
    """Represents a segment of records."""
    __tablename__ = 'segments'
    
    id = Column(Integer, primary_key=True)
    segment_uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    segment_number = Column(Integer, nullable=False)
    record_count = Column(Integer, default=0)
    file_process_id = Column(Integer, ForeignKey('file_processes.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    file_process = relationship("FileProcess", back_populates="segments")
    records = relationship("Record", back_populates="segment", cascade="all, delete-orphan")

class Record(Base):
    """Represents an individual record in a segment."""
    __tablename__ = 'records'
    
    id = Column(Integer, primary_key=True)
    record_uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    segment_id = Column(Integer, ForeignKey('segments.id'))
    record_data = Column(JSON, nullable=False)  # Store record data as JSON
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    segment = relationship("Segment", back_populates="records")

def init_db(engine):
    """Initialize the database schema."""
    Base.metadata.create_all(engine)