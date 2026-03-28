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

class AppLauncher:
    def __init__(self, app):
        self.app = app
        self.model_name = "gemma2:2b"
        self.window = None
        self.progress = None

    def check_and_start(self):
        try:
            # Check if model exists
            models_response = ollama.list()
            models = []
            if hasattr(models_response, 'models'):
                models = [m.model for m in models_response.models]
            elif isinstance(models_response, dict) and 'models' in models_response:
                models = [m.get('name', '') for m in models_response.get('models', [])]

            model_exists = any(self.model_name in m for m in models)

            if not model_exists:
                print(f"Model {self.model_name} not found locally. Downloading...")
                self.progress = QProgressDialog(f"Downloading {self.model_name}...\nThis may take several minutes.", None, 0, 0) # 0,0 makes it an indeterminate spinner
                self.progress.setWindowTitle("First Time Setup")
                self.progress.setWindowModality(Qt.WindowModality.WindowModal)
                self.progress.setCancelButton(None)
                self.progress.show()

                self.worker = DownloadWorker(self.model_name)
                self.worker.finished.connect(self.on_download_finished)
                self.worker.error.connect(self.on_download_error)
                self.worker.start()
            else:
                self.launch_main_window()

        except Exception as e:
            QMessageBox.critical(None, "Ollama Error",
                                 f"Could not connect to Ollama. Is the Ollama app running?\n\nError: {e}\n\nPlease install and start Ollama from https://ollama.com")
            sys.exit(1)

    def on_download_finished(self):
        if self.progress:
            self.progress.close()
        print("Download complete.")
        self.launch_main_window()

    def on_download_error(self, err_msg):
        if self.progress:
            self.progress.close()
        QMessageBox.critical(None, "Download Error", f"Failed to download the model: {err_msg}")
        sys.exit(1)

    def launch_main_window(self):
        self.window = MainWindow()
        self.window.show()

def main():
    print("Starting GUI Symbiote...")
    app = QApplication(sys.argv)

    launcher = AppLauncher(app)
    launcher.check_and_start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
