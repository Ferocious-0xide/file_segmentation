import pandas as pd
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..database.models import FileProcess, Segment, Record
from ..database.database import DatabaseHandler

class SegmentationProcessor:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def process_file(self, filepath: str, num_segments: int) -> Dict[str, Any]:
        """
        Process a file and segment it into the specified number of segments.
        
        Args:
            filepath: Path to the input file
            num_segments: Number of segments to create
            
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
            
            # Process file in chunks to handle large files
            total_records = self._process_file_chunks(session, filepath, segments)
            
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

    def _process_file_chunks(self, session: Session, filepath: str, segments: List[Segment]) -> int:
        """Process file in chunks and store records in segments."""
        chunk_size = 1000  # Adjust based on memory constraints
        total_records = 0
        
        # Read CSV in chunks
        for chunk in pd.read_csv(filepath, chunksize=chunk_size):
            records = []
            
            for _, row in chunk.iterrows():
                segment = segments[total_records % len(segments)]
                
                # Create record with JSON data
                record = Record(
                    segment_id=segment.id,
                    record_data=row.to_dict(),
                    sequence_number=total_records
                )
                records.append(record)
                
                # Update segment record count
                segment.record_count += 1
                total_records += 1
            
            # Bulk insert records
            session.bulk_save_objects(records)
            session.flush()
            
            # Emit progress (if needed)
            # self.progress.emit(int((total_records / total_size) * 100))
            
        return total_records

    def get_segment_stats(self, process_uuid: str) -> Dict[str, Any]:
        """Get statistics for all segments in a file process."""
        with self.db_handler.session_scope() as session:
            file_process = session.query(FileProcess).filter_by(process_uuid=process_uuid).first()
            if not file_process:
                raise ValueError(f"No file process found with UUID {process_uuid}")
            
            return {
                "filename": file_process.filename,
                "total_segments": file_process.total_segments,
                "total_records": file_process.total_records,
                "segments": [{
                    "segment_uuid": seg.segment_uuid,
                    "segment_number": seg.segment_number,
                    "record_count": seg.record_count
                } for seg in file_process.segments]
            }

    def get_segment_records(self, segment_uuid: str, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """Get records for a specific segment with pagination."""
        with self.db_handler.session_scope() as session:
            segment = session.query(Segment).filter_by(segment_uuid=segment_uuid).first()
            if not segment:
                raise ValueError(f"No segment found with UUID {segment_uuid}")
            
            # Get paginated records
            records = (session.query(Record)
                      .filter_by(segment_id=segment.id)
                      .order_by(Record.sequence_number)
                      .offset((page - 1) * per_page)
                      .limit(per_page)
                      .all())
            
            return {
                "segment_uuid": segment.segment_uuid,
                "segment_number": segment.segment_number,
                "record_count": segment.record_count,
                "page": page,
                "per_page": per_page,
                "records": [{
                    "record_uuid": record.record_uuid,
                    "sequence_number": record.sequence_number,
                    "data": record.record_data
                } for record in records]
            }