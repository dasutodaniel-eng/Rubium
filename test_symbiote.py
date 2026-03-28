import pytest
import os
import json
from memory import MemoryManager
from brain import Brain

@pytest.fixture
def temp_memory_dir(tmpdir):
    return str(tmpdir.mkdir("test_memory"))

def test_memory_manager_creation(temp_memory_dir):
    manager = MemoryManager(memory_dir=temp_memory_dir)
    assert os.path.exists(temp_memory_dir)
    assert os.path.exists(manager.history_file)

    # Check default structure
    history = manager.load_history()
    assert history == []

def test_memory_manager_add_and_clear(temp_memory_dir):
    manager = MemoryManager(memory_dir=temp_memory_dir)
    manager.add_message("user", "Hello World")
    manager.add_message("assistant", "Hello Human")

    history = manager.load_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["content"] == "Hello Human"

    manager.clear_history()
    history = manager.load_history()
    assert history == []

def test_brain_set_system_prompt(temp_memory_dir):
    manager = MemoryManager(memory_dir=temp_memory_dir)
    brain = Brain(manager, model="test_model")

    brain.set_system_prompt("You are a test AI.")
    history = manager.load_history()
    assert len(history) == 1
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "You are a test AI."

    # Ensure it updates rather than adds another
    brain.set_system_prompt("You are an updated test AI.")
    history = manager.load_history()
    assert len(history) == 1
    assert history[0]["content"] == "You are an updated test AI."

# Mock Ollama response for testing Brain processing without actually hitting Ollama
class MockOllamaResponse:
    def __iter__(self):
        yield {'message': {'content': 'This '}}
        yield {'message': {'content': 'is '}}
        yield {'message': {'content': 'a test.'}}

def mock_chat(*args, **kwargs):
    return MockOllamaResponse()

def test_brain_process_message(temp_memory_dir, monkeypatch):
    import ollama
    monkeypatch.setattr(ollama, 'chat', mock_chat)

    manager = MemoryManager(memory_dir=temp_memory_dir)
    brain = Brain(manager, model="test_model")

    # Process a message
    reply = brain.process_message("Test message")
    assert reply == "This is a test."

    history = manager.load_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Test message"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "This is a test."
