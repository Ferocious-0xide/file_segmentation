from PyQt6.QtWidgets import (
    QMainWindow, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,
    QPushButton, 
    QLabel, 
    QFileDialog, 
    QSpinBox,
    QTableWidget, 
    QTableWidgetItem, 
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from ..segmentation.core import SegmentationProcessor
from ..database.database import DatabaseHandler


class ProcessingThread(QThread):
    """Thread for handling file processing operations."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, processor, filepath, num_segments):
        super().__init__()
        self.processor = processor
        self.filepath = filepath
        self.num_segments = num_segments

    def run(self):
        try:
            result = self.processor.process_file(self.filepath, self.num_segments)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window for file segmentation processor."""
    def __init__(self):
        super().__init__()
        self.db_handler = DatabaseHandler()
        self.processor = SegmentationProcessor(self.db_handler)
        self.processing_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('File Segmentation Processor')
        self.setMinimumSize(800, 600)
        
        self._setup_central_widget()
        self._setup_file_selection()
        self._setup_segment_configuration()
        self._setup_progress_bar()
        self._setup_results_table()
        self._setup_process_button()

    def _setup_central_widget(self):
        """Set up the central widget and main layout."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

    def _setup_file_selection(self):
        """Set up the file selection section."""
        file_layout = QHBoxLayout()
        self.file_label = QLabel('No file selected')
        self.file_button = QPushButton('Select File')
        self.file_button.clicked.connect(self.select_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_button)
        self.main_layout.addLayout(file_layout)

    def _setup_segment_configuration(self):
        """Set up the segment configuration section."""
        segment_layout = QHBoxLayout()
        segment_layout.addWidget(QLabel('Number of Segments:'))
        
        self.segment_spinbox = QSpinBox()
        self.segment_spinbox.setRange(1, 100)
        self.segment_spinbox.setValue(5)
        
        segment_layout.addWidget(self.segment_spinbox)
        self.main_layout.addLayout(segment_layout)

    def _setup_progress_bar(self):
        """Set up the progress bar."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

    def _setup_results_table(self):
        """Set up the results table."""
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(['Segment', 'Records', 'Status'])
        self.main_layout.addWidget(self.results_table)

    def _setup_process_button(self):
        """Set up the process button."""
        self.process_button = QPushButton('Process File')
        self.process_button.clicked.connect(self.process_file)
        self.process_button.setEnabled(False)
        self.main_layout.addWidget(self.process_button)

    def select_file(self):
        """Handle file selection."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, 'Select File', '', 'All Files (*.*)'
        )
        if filepath:
            self.file_label.setText(filepath)
            self.process_button.setEnabled(True)

    def process_file(self):
        """Handle file processing."""
        if not self.file_label.text() or self.file_label.text() == 'No file selected':
            return

        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.processing_thread = ProcessingThread(
            self.processor,
            self.file_label.text(),
            self.segment_spinbox.value()
        )
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.processing_complete)
        self.processing_thread.error.connect(self.processing_error)
        self.processing_thread.start()

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def processing_complete(self, result):
        """Handle completion of file processing."""
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        self.update_results_table(result)

    def processing_error(self, error_message):
        """Handle processing errors."""
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        self.file_label.setText(f"Error: {error_message}")

    def update_results_table(self, result):
        """Update the results table with processing results."""
        self.results_table.setRowCount(len(result['segments']))
        for i, segment in enumerate(result['segments']):
            self.results_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.results_table.setItem(i, 1, QTableWidgetItem(str(segment['record_count'])))
            self.results_table.setItem(i, 2, QTableWidgetItem('Complete'))

    def closeEvent(self, event):
        """Handle application closure."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
        
        if self.db_handler:
            self.db_handler.dispose()
        
        event.accept()