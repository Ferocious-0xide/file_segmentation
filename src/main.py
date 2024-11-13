import sys
from PyQt6.QtWidgets import QApplication
from src.gui.interface import MainWindow
from src.database.database import DatabaseHandler

def main():
    # Initialize the database
    db_handler = DatabaseHandler()
    
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()