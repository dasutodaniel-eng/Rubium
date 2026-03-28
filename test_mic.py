import time
import speech_recognition as sr
from voice import SoundDeviceMicrophone

print("Testing SoundDeviceMicrophone...")
try:
    with SoundDeviceMicrophone() as source:
        print("Microphone context opened successfully.")

        # Try to read a chunk
        print("Reading chunk...")
        data = source.stream.read(1024)
        print(f"Read {len(data)} bytes of audio data.")

        if len(data) > 0:
            print("Microphone adapter seems to be working.")
        else:
            print("Microphone adapter returned no data.")
except Exception as e:
    print(f"Test failed with error: {e}")
