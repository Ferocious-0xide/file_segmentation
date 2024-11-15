from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class FileProcess(Base):
    __tablename__ = 'file_processes'

    id = Column(Integer, primary_key=True)
    process_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255))
    total_segments = Column(Integer)
    total_records = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    segments = relationship("Segment", back_populates="file_process")

class Segment(Base):
    __tablename__ = 'segments'

    id = Column(Integer, primary_key=True)
    segment_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    segment_number = Column(Integer)
    record_count = Column(Integer, default=0)
    file_process_id = Column(Integer, ForeignKey('file_processes.id'))
    
    file_process = relationship("FileProcess", back_populates="segments")
    records = relationship("Record", back_populates="segment")

class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True)
    record_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    segment_id = Column(Integer, ForeignKey('segments.id'))
    sequence_number = Column(Integer)
    record_data = Column(JSON)
    
    segment = relationship("Segment", back_populates="records")
    # Add this new relationship
    donor = relationship("Donor", back_populates="record", uselist=False)

class Donor(Base):
    __tablename__ = 'donors'

    id = Column(Integer, primary_key=True)
    donor_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String(255), unique=True, nullable=True)  # If donors have an external ID
    record_id = Column(Integer, ForeignKey('records.id'))
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Reference to the latest record data
    record = relationship("Record", back_populates="donor")
    
    email = Column(String(255), unique=True, nullable=True)
    first_name = Column(String(255))
    last_name = Column(String(255))

def init_db(engine):
    """Initialize database tables safely"""
    try:
        # Create all tables if they don't exist
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise