import speech_recognition as sr
import pyttsx3
import threading

class VoiceManager:
    def __init__(self):
        # Initialize Text-to-Speech engine
        self.tts_engine = pyttsx3.init()
        # Ensure we use a decent voice if available
        voices = self.tts_engine.getProperty('voices')
        # On Linux, espeak is usually default. Set Russian voice if available, otherwise fallback.
        for voice in voices:
            if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        # Initialize Speech-to-Text recognizer
        self.recognizer = sr.Recognizer()

    def speak(self, text):
        """Speaks the given text asynchronously."""
        def run_tts():
            # In some setups, pyttsx3 needs to be re-initialized per thread.
            # But here we try to use the main instance carefully or just do it blocking in a thread.
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.say(text)
            engine.runAndWait()

        # Run TTS in a background thread to prevent UI freezing
        threading.Thread(target=run_tts, daemon=True).start()

    def listen(self, timeout=5, phrase_time_limit=10):
        """Listens to the microphone and returns recognized text."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                # We listen for a short time
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            print("Recognizing...")
            # We default to Russian recognition, falling back to english if necessary
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
