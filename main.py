import sys
from gui import MainWindow
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import ollama

class DownloadWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name

    def run(self):
        try:
            ollama.pull(self.model_name)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

def main():
    print("Starting GUI Symbiote...")
    app = QApplication(sys.argv)

    # We remove the startup blocking check so the GUI always opens,
    # even if Ollama is temporarily returning 503 (e.g. busy loading a model).
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
