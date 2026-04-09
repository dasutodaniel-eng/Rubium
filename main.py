import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from gui import MainWindow, SetupDialog
from memory import MemoryManager

def apply_dark_theme(app):
    """Applies a sleek, dark mode style to the application."""
    dark_stylesheet = """
    QMainWindow {
        background-color: #121212;
    }
    QWidget {
        background-color: #121212;
        color: #E0E0E0;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }
    QTextEdit {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 10px;
    }
    QLineEdit {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 8px;
    }
    QPushButton {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3D3D3D;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #3D3D3D;
        border: 1px solid #555555;
    }
    QPushButton:pressed {
        background-color: #1A1A1A;
    }
    QComboBox {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 4px;
    }
    QComboBox::drop-down {
        border-left: 1px solid #333333;
    }
    QLabel {
        color: #B0B0B0;
        font-weight: bold;
    }
    """
    app.setStyleSheet(dark_stylesheet)

def main():
    print("Starting GUI Symbiote...")
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    memory_manager = MemoryManager()
    config = memory_manager.load_config()

    # Check if this is the first launch (missing API Key)
    if not config.get("api_key"):
        setup_dialog = SetupDialog()
        if setup_dialog.exec() == SetupDialog.DialogCode.Accepted:
            config = setup_dialog.get_data()
            memory_manager.save_config(config)
        else:
            print("Setup cancelled. Exiting.")
            sys.exit(0)

    # Launch main window with config
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
