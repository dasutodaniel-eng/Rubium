import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QInputDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QThread, Qt

from memory import MemoryManager
from brain import Brain
from voice import VoiceManager

class LLMWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, brain, user_text):
        super().__init__()
        self.brain = brain
        self.user_text = user_text

    def run(self):
        # We use stream=False for simpler integration with TTS and GUI currently
        response = self.brain.process_message(self.user_text, stream=False)
        self.finished.emit(response)

class VoiceWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, voice_manager):
        super().__init__()
        self.voice_manager = voice_manager

    def run(self):
        recognized_text = self.voice_manager.listen()
        self.finished.emit(recognized_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.memory_manager = MemoryManager()
        self.brain = Brain(self.memory_manager, model="gemma2:2b")
        self.voice_manager = VoiceManager()

        # Determine the name
        self.assistant_name = self.prompt_for_name()
        if not self.assistant_name:
            self.assistant_name = "Jarvis" # Fallback

        system_prompt = (
            f"You are a highly advanced AI Symbiote and personal assistant named {self.assistant_name}. "
            "You are intelligent, resourceful, and capable of learning from interactions. "
            "Keep your responses concise and helpful. You speak Russian by default."
        )
        self.brain.set_system_prompt(system_prompt)

        self.setWindowTitle(f"{self.assistant_name} - AI Symbiote")
        self.resize(600, 500)

        # Main Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Chat Display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display)

        # Input Area (Text input, Send, Voice)
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message or click 'Voice'...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        self.voice_button = QPushButton("🎤 Voice")
        self.voice_button.clicked.connect(self.start_voice_input)
        input_layout.addWidget(self.voice_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_memory)
        input_layout.addWidget(self.clear_button)

        main_layout.addLayout(input_layout)

        self.load_history_to_display()

    def prompt_for_name(self):
        name, ok = QInputDialog.getText(self, "Assistant Name", "What would you like to call your assistant?")
        if ok and name.strip():
            return name.strip()
        return None

    def load_history_to_display(self):
        history = self.memory_manager.load_history()
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                self.chat_display.append(f"<b>You:</b> {content}")
            elif role == "assistant":
                self.chat_display.append(f"<b>{self.assistant_name}:</b> {content}")

    def append_chat(self, speaker, text):
        self.chat_display.append(f"<b>{speaker}:</b> {text}")

    def send_message(self, user_text=None):
        if not user_text:
            user_text = self.input_field.text().strip()

        if not user_text:
            return

        self.input_field.clear()
        self.append_chat("You", user_text)

        # Disable inputs while processing
        self.set_inputs_enabled(False)

        # Start background worker for LLM processing
        self.llm_worker = LLMWorker(self.brain, user_text)
        self.llm_worker.finished.connect(self.on_llm_finished)
        self.llm_worker.start()

    def on_llm_finished(self, response_text):
        self.append_chat(self.assistant_name, response_text)
        self.voice_manager.speak(response_text)
        self.set_inputs_enabled(True)
        self.input_field.setFocus()

    def start_voice_input(self):
        self.set_inputs_enabled(False)
        self.voice_button.setText("Listening...")
        self.input_field.setPlaceholderText("Listening to your voice...")

        self.voice_worker = VoiceWorker(self.voice_manager)
        self.voice_worker.finished.connect(self.on_voice_finished)
        self.voice_worker.start()

    def on_voice_finished(self, recognized_text):
        self.voice_button.setText("🎤 Voice")
        self.input_field.setPlaceholderText("Type a message or click 'Voice'...")
        self.set_inputs_enabled(True)

        if recognized_text:
            self.send_message(recognized_text)
        else:
            # Re-enable inputs if nothing was heard
            pass

    def clear_memory(self):
        self.memory_manager.clear_history()
        self.chat_display.clear()
        # Reset system prompt with name
        system_prompt = (
            f"You are a highly advanced AI Symbiote and personal assistant named {self.assistant_name}. "
            "You are intelligent, resourceful, and capable of learning from interactions. "
            "Keep your responses concise and helpful. You speak Russian by default."
        )
        self.brain.set_system_prompt(system_prompt)
        QMessageBox.information(self, "Memory Cleared", "The assistant's memory has been reset.")

    def set_inputs_enabled(self, enabled):
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.voice_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)

def run_app():
    # Needed for environments that might not have a display (e.g., CI/CD tests)
    import os
    if not os.environ.get("DISPLAY"):
        print("No DISPLAY found, GUI cannot start.")
        return

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
