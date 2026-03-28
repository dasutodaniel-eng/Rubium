import threading
import pyttsx3
import speech_recognition as sr
from PyQt6.QtCore import QObject, pyqtSignal, QByteArray, QIODevice, QBuffer
from PyQt6.QtMultimedia import QAudioSource, QMediaFormat, QAudioFormat, QAudioDevice
from PyQt6.QtMultimedia import QMediaDevices
import time

class QtVoiceWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.audio_source = None
        self.buffer = QBuffer()

        # Configure Audio Format for Speech Recognition (16kHz, 16-bit, Mono)
        self.format = QAudioFormat()
        self.format.setSampleRate(16000)
        self.format.setChannelCount(1)
        self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

    def start_listening(self):
        default_device = QMediaDevices.defaultAudioInput()
        if not default_device.isNull():
            if not default_device.isFormatSupported(self.format):
                print("Default format not natively supported by hardware. Qt will attempt software conversion.")

            self.audio_source = QAudioSource(default_device, self.format, self)

            # Use QBuffer to store audio data
            self.buffer = QBuffer()
            self.buffer.open(QIODevice.OpenModeFlag.ReadWrite)

            print("Listening (QtMultimedia)...")
            self.audio_source.start(self.buffer)

            # Listen for 5 seconds total (simple approach without silence detection for now)
            # You can tweak the delay below if you want it longer
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(4000, self.stop_listening)
        else:
            print("No audio input device found.")
            self.finished.emit("")

    def stop_listening(self):
        if self.audio_source:
            self.audio_source.stop()
            print("Recognizing...")

            # Get the raw PCM bytes
            self.buffer.seek(0)

            # readAll() returns a QByteArray. We must cast it to Python bytes
            # otherwise SpeechRecognition will throw an AssertionError.
            audio_bytes = bytes(self.buffer.readAll())

            if not audio_bytes:
                print("No audio data captured.")
                self.finished.emit("")
                return

            # Convert raw bytes to SpeechRecognition AudioData
            # sample_width = 2 (16-bit)
            audio_data = sr.AudioData(audio_bytes, self.format.sampleRate(), 2)

            def recognize_worker():
                try:
                    text = self.recognizer.recognize_google(audio_data, language="ru-RU")
                    self.finished.emit(text)
                except sr.UnknownValueError:
                    print("Could not understand audio.")
                    self.finished.emit("")
                except sr.RequestError as e:
                    print(f"Speech recognition service error: {e}")
                    self.finished.emit("")
                except Exception as e:
                    print(f"Unexpected recognition error: {e}")
                    self.finished.emit("")

            threading.Thread(target=recognize_worker, daemon=True).start()
        else:
            self.finished.emit("")


class VoiceManager:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

    def speak(self, text):
        def run_tts():
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.say(text)
            engine.runAndWait()

        threading.Thread(target=run_tts, daemon=True).start()

    def listen(self):
        # We no longer use this blocking `listen` method in GUI.
        # The GUI should use QtVoiceWorker asynchronously.
        pass
