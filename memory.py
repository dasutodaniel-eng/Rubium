import os
import json

class MemoryManager:
    def __init__(self, memory_dir="./memory"):
        self.memory_dir = memory_dir
        self.history_file = os.path.join(self.memory_dir, "history.json")
        self.config_file = os.path.join(self.memory_dir, "config.json")
        self._ensure_memory_dir()

    def _ensure_memory_dir(self):
        """Creates the memory directory and files if they do not exist."""
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

        if not os.path.exists(self.history_file):
            self.save_history([])

        if not os.path.exists(self.config_file):
            self.save_config({})

    def load_config(self):
        """Loads user configuration (API keys, assistant name)."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_config(self, config_data):
        """Saves user configuration."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

    def load_history(self):
        """Loads conversation history from the local JSON file."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_history(self, history):
        """Saves conversation history to the local JSON file."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)

    def add_message(self, role, content):
        """Adds a new message to the history."""
        history = self.load_history()
        history.append({"role": role, "content": content})
        self.save_history(history)

    def clear_history(self):
        """Clears all conversation history."""
        self.save_history([])

    def sync_to_cloud(self):
        """Placeholder for future cloud sync functionality."""
        print("Cloud sync feature is not yet implemented.")
        pass

    def sync_from_cloud(self):
        """Placeholder for future cloud sync functionality."""
        print("Cloud sync feature is not yet implemented.")
        pass
