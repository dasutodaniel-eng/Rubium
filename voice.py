import speech_recognition as sr
import pyttsx3
import threading
import sounddevice as sd
import numpy as np

class SoundDeviceMicrophone(sr.AudioSource):
    """
    A custom Microphone class for SpeechRecognition that uses sounddevice instead of pyaudio.
    """
    def __init__(self, device_index=None, sample_rate=16000, chunk_size=1024):
        self.device_index = device_index
        self.format = np.int16  # 16-bit int
        self.SAMPLE_WIDTH = 2  # size in bytes of format
        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk_size
        self.audio = None
        self.stream = None

    def __enter__(self):
        self.audio = sd.InputStream(
            device=self.device_index,
            channels=1,
            samplerate=self.SAMPLE_RATE,
            dtype=self.format,
            blocksize=self.CHUNK
        )
        self.stream = self.audio.start()

        # Monkey patch the stream object to support a `read` method which SpeechRecognition expects
        class StreamAdapter:
            def __init__(self, sd_stream):
                self.sd_stream = sd_stream
            def read(self, chunk_size, exception_on_overflow=False):
                data, overflow = self.sd_stream.read(chunk_size)
                # Convert the NumPy array to bytes
                return data.tobytes()

        self.stream = StreamAdapter(self.audio)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.audio is not None:
            self.audio.stop()
            self.audio.close()
            self.stream = None
            self.audio = None

class VoiceManager:
    def __init__(self):
        # Initialize Text-to-Speech engine
        self.tts_engine = pyttsx3.init()
        # Ensure we use a decent voice if available
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        # Initialize Speech-to-Text recognizer
        self.recognizer = sr.Recognizer()

    def speak(self, text):
        """Speaks the given text asynchronously."""
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

    def listen(self, timeout=5, phrase_time_limit=10):
        """Listens to the microphone using sounddevice and returns recognized text."""
        try:
            # Use our custom SoundDeviceMicrophone instead of sr.Microphone()
            with SoundDeviceMicrophone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            print("Recognizing...")
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""
        except Exception as e:
            print(f"Microphone access error: {e}")
            return ""
