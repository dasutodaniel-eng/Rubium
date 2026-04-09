import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QInputDialog, QMessageBox,
                             QDialog, QLabel, QComboBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal, QThread, Qt

from memory import MemoryManager
from brain import Brain
from voice import VoiceManager, QtVoiceWorker

class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Symbiote Setup")
        self.setFixedSize(400, 250)

        layout = QFormLayout()

        # Assistant Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Jarvis, Friday, Cortana")
        layout.addRow("Assistant Name:", self.name_input)

        # Provider Dropdown
        self.provider_dropdown = QComboBox()
        self.provider_dropdown.addItems(["OpenAI", "DeepSeek", "Anthropic", "Google"])
        layout.addRow("AI Provider:", self.provider_dropdown)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("API Key:", self.api_key_input)

        # Submit Button
        self.submit_btn = QPushButton("Start Symbiote")
        self.submit_btn.clicked.connect(self.accept)
        layout.addRow("", self.submit_btn)

        self.setLayout(layout)

    def get_data(self):
        return {
            "assistant_name": self.name_input.text().strip() or "Jarvis",
            "provider": self.provider_dropdown.currentText().lower(),
            "api_key": self.api_key_input.text().strip()
        }

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

class MainWindow(QMainWindow):
    def __init__(self, config_data):
        super().__init__()

        self.assistant_name = config_data.get("assistant_name", "Jarvis")

        # Re-initialize Brain with the new config that was saved earlier
        self.memory_manager = MemoryManager()
        self.brain = Brain(self.memory_manager)
        self.voice_manager = VoiceManager()

        system_prompt = (
            f"You are a highly advanced AI Symbiote and personal assistant named {self.assistant_name}. "
            "You are intelligent, resourceful, and capable of learning from interactions. "
            "Keep your responses concise and helpful. You speak Russian by default."
        )
        self.brain.set_system_prompt(system_prompt)

        self.setWindowTitle(f"{self.assistant_name} - AI Symbiote")
        self.resize(700, 600)

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

    def load_history_to_display(self):
        history = self.memory_manager.load_history()
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                self.append_chat("You", content)
            elif role == "assistant":
                self.append_chat(self.assistant_name, content)

    def append_chat(self, speaker, text):
        # Apply custom HTML styling depending on whether the speaker is the user or assistant
        if speaker == "You":
            color = "#4DA6FF" # Light blue for user
        else:
            color = "#00E676" # Neon green for assistant

        styled_message = f'<span style="color: {color}; font-size: 14px;"><b>{speaker}:</b></span><br><span style="color: #FFFFFF; font-size: 14px;">{text}</span><br>'
        self.chat_display.append(styled_message)

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

        # Use our new native Qt Multimedia Voice Worker
        self.voice_worker = QtVoiceWorker()
        self.voice_worker.finished.connect(self.on_voice_finished)

        # Important: this operates entirely via Qt Signals rather than QThread blocks.
        self.voice_worker.start_listening()

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
