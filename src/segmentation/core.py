import pandas as pd
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..database.models import FileProcess, Segment, Record
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
        
        Args:
            filepath: Path to the input file
            num_segments: Number of segments to create
            selected_columns: List of columns to include in processing
            
        Returns:
            Dict containing processing results
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
        
        Args:
            filepath: Path to the input file
            segment_column: Column to use for segmentation
            selected_columns: List of columns to include in processing
            
        Returns:
            Dict containing processing results
        """
        with self.db_handler.session_scope() as session:
            # Read unique values from segment column
            df = pd.read_csv(filepath, usecols=[segment_column])
            unique_values = df[segment_column].unique()
            num_segments = len(unique_values)
            
            # Create file process record
            file_process = FileProcess(
                filename=filepath,
                total_segments=num_segments
            )
            session.add(file_process)
            session.flush()

            # Create segments
            segments = self._create_segments(session, file_process.id, num_segments)
            
            # Create mapping of unique values to segment IDs
            value_to_segment = dict(zip(unique_values, segments))
            
            # Process file in chunks with column-based segmentation
            total_records = self._process_file_chunks_by_column(
                session,
                filepath,
                value_to_segment,
                segment_column,
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
        
        # Prepare column list for reading CSV
        usecols = selected_columns if selected_columns else None
        
        for chunk in pd.read_csv(filepath, chunksize=chunk_size, usecols=usecols):
            records = []
            
            for _, row in chunk.iterrows():
                segment = segments[total_records % len(segments)]
                
                record = Record(
                    segment_id=segment.id,
                    record_data=row.to_dict(),
                    sequence_number=total_records
                )
                records.append(record)
                
                segment.record_count += 1
                total_records += 1
            
            session.bulk_save_objects(records)
            session.flush()
            
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
        
        # Prepare column list for reading CSV
        usecols = selected_columns if selected_columns else None
        if usecols and segment_column not in usecols:
            usecols.append(segment_column)
        
        for chunk in pd.read_csv(filepath, chunksize=chunk_size, usecols=usecols):
            records = []
            
            for _, row in chunk.iterrows():
                segment_value = row[segment_column]
                segment = value_to_segment[segment_value]
                
                # Remove segment column from record data if not in selected columns
                record_data = row.to_dict()
                if selected_columns and segment_column not in selected_columns:
                    del record_data[segment_column]
                
                record = Record(
                    segment_id=segment.id,
                    record_data=record_data,
                    sequence_number=total_records
                )
                records.append(record)
                
                segment.record_count += 1
                total_records += 1
            
            session.bulk_save_objects(records)
            session.flush()
            
        return total_records

    # Existing get_segment_stats and get_segment_records methods remain the same...