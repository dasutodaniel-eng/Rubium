import sys
from gui import MainWindow
from PyQt6.QtWidgets import QApplication

def main():
    print("Starting GUI Symbiote...")
    # Initialize the QApplication
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
