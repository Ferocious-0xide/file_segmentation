import pandas as pd
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..database.models import FileProcess, Segment, Record, Donor  # Added Donor
from ..database.database import DatabaseHandler

class SegmentationProcessor:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def process_file(
        self,
        filepath: str,
        num_segments: int,
        selected_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a file and segment it into equal-sized segments.
        """
        with self.db_handler.session_scope() as session:
            # Create file process record
            file_process = FileProcess(
                filename=filepath,
                total_segments=num_segments
            )
            session.add(file_process)
            session.flush()

            # Create segments
            segments = self._create_segments(session, file_process.id, num_segments)
            
            # Process file in chunks
            total_records = self._process_file_chunks(
                session,
                filepath,
                segments,
                selected_columns
            )
            
            # Update total records count
            file_process.total_records = total_records
            
            return {
                "process_uuid": file_process.process_uuid,
                "total_records": total_records,
                "segments": [{
                    "segment_uuid": seg.segment_uuid,
                    "segment_number": seg.segment_number,
                    "record_count": seg.record_count
                } for seg in segments]
            }

    def process_file_by_column(
        self,
        filepath: str,
        segment_column: str,
        selected_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a file and segment it based on unique values in a column.
        """
        with self.db_handler.session_scope() as session:
            df = pd.read_csv(filepath, usecols=[segment_column])
            unique_values = df[segment_column].unique()
            num_segments = len(unique_values)
            
            file_process = FileProcess(
                filename=filepath,
                total_segments=num_segments
            )
            session.add(file_process)
            session.flush()

            segments = self._create_segments(session, file_process.id, num_segments)
            value_to_segment = dict(zip(unique_values, segments))
            
            total_records = self._process_file_chunks_by_column(
                session,
                filepath,
                value_to_segment,
                segment_column,
                selected_columns
            )
            
            file_process.total_records = total_records
            
            return {
                "process_uuid": file_process.process_uuid,
                "total_records": total_records,
                "segments": [{
                    "segment_uuid": seg.segment_uuid,
                    "segment_number": seg.segment_number,
                    "record_count": seg.record_count,
                    "segment_value": val
                } for val, seg in value_to_segment.items()]
            }

    def _create_segments(self, session: Session, file_process_id: int, num_segments: int) -> List[Segment]:
        """Create the specified number of segments."""
        segments = [
            Segment(
                segment_number=i,
                file_process_id=file_process_id
            )
            for i in range(num_segments)
        ]
        session.add_all(segments)
        session.flush()
        return segments

    def _process_file_chunks(
        self,
        session: Session,
        filepath: str,
        segments: List[Segment],
        selected_columns: Optional[List[str]] = None
    ) -> int:
        """Process file in chunks for equal distribution."""
        chunk_size = 1000
        total_records = 0
        
        usecols = selected_columns if selected_columns else None
        
        for chunk in pd.read_csv(filepath, chunksize=chunk_size, usecols=usecols):
            for _, row in chunk.iterrows():
                segment = segments[total_records % len(segments)]
                record_data = row.to_dict()
                
                record = Record(
                    segment_id=segment.id,
                    record_data=record_data,
                    sequence_number=total_records
                )
                session.add(record)
                session.flush()  # Need to flush to get record.id
                
                # Look for existing donor by email or other unique identifier
                email = record_data.get('email')
                if email:
                    donor = session.query(Donor).filter(Donor.email == email).first()
                    if donor:
                        # Update existing donor
                        donor.record_id = record.id
                        donor.last_seen_at = datetime.utcnow()
                    else:
                        # Create new donor
                        donor = Donor(
                            record_id=record.id,
                            email=email,
                            first_name=record_data.get('first_name'),
                            last_name=record_data.get('last_name')
                        )
                        session.add(donor)
                
                segment.record_count += 1
                total_records += 1
                
                if total_records % 100 == 0:
                    session.flush()
            
            session.commit()
        
        return total_records

    def _process_file_chunks_by_column(
        self,
        session: Session,
        filepath: str,
        value_to_segment: Dict[Any, Segment],
        segment_column: str,
        selected_columns: Optional[List[str]] = None
    ) -> int:
        """Process file in chunks for column-based segmentation."""
        chunk_size = 1000
        total_records = 0
        
        usecols = selected_columns if selected_columns else None
        if usecols and segment_column not in usecols:
            usecols.append(segment_column)
        
        for chunk in pd.read_csv(filepath, chunksize=chunk_size, usecols=usecols):
            for _, row in chunk.iterrows():
                segment_value = row[segment_column]
                segment = value_to_segment[segment_value]
                
                record_data = row.to_dict()
                if selected_columns and segment_column not in selected_columns:
                    del record_data[segment_column]
                
                record = Record(
                    segment_id=segment.id,
                    record_data=record_data,
                    sequence_number=total_records
                )
                session.add(record)
                session.flush()

                # Added donor handling similar to _process_file_chunks
                email = record_data.get('email')
                if email:
                    donor = session.query(Donor).filter(Donor.email == email).first()
                    if donor:
                        donor.record_id = record.id
                        donor.last_seen_at = datetime.utcnow()
                    else:
                        donor = Donor(
                            record_id=record.id,
                            email=email,
                            first_name=record_data.get('first_name'),
                            last_name=record_data.get('last_name')
                        )
                        session.add(donor)
                
                segment.record_count += 1
                total_records += 1
                
                if total_records % 100 == 0:
                    session.flush()
            
            session.commit()
        
        return total_records