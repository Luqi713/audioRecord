import os
import threading
import wave
import tkinter as tk
from tkinter import messagebox
import pyaudio
import sounddevice as sd
import numpy as np

# Define audio parameters
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 1              # 1 channel for microphone
RATE = 44100              # 44.1kHz sampling rate
CHUNK = 1024              # 2^10 samples for buffer
WAVE_OUTPUT_FILENAME = "output.wav"  # Name of the audio file

# Create Audios folder if it doesn't exist
if not os.path.exists("Audios"):
    os.makedirs("Audios")

class AudioRecorder:
    def __init__(self, root):
        self.root = root
        self.is_recording = False
        self.frames = []
        self.mic_frames = []
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Audio Recorder")
        
        self.start_button = tk.Button(self.root, text="Start", command=self.start_recording)
        self.start_button.pack(pady=10)
        
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_recording)
        self.stop_button.pack(pady=10)
        
    def start_recording(self):
        if self.is_recording:
            messagebox.showinfo("Info", "Recording already in progress.")
            return
        self.is_recording = True
        self.frames = []
        self.mic_frames = []

        self.audio = pyaudio.PyAudio()

        try:
            self.stream = self.audio.open(format=FORMAT,
                                          channels=CHANNELS,
                                          rate=RATE,
                                          input=True,
                                          frames_per_buffer=CHUNK)
        except OSError as e:
            self.is_recording = False
            messagebox.showerror("Error", f"Could not open stream: {e}")
            return
        
        threading.Thread(target=self.record_microphone).start()
        threading.Thread(target=self.record_system_audio).start()
        
    def record_microphone(self):
        while self.is_recording:
            try:
                data = self.stream.read(CHUNK)
                self.mic_frames.append(data)
            except Exception as e:
                print(f"Error recording microphone: {e}")
                break
            
    def record_system_audio(self):
        def callback(outdata, frames, time, status):
            if self.is_recording:
                self.frames.append(outdata.copy())
        
        try:
            with sd.OutputStream(samplerate=RATE, channels=2, callback=callback):
                while self.is_recording:
                    sd.sleep(1000)
        except Exception as e:
            print(f"Error recording system audio: {e}")
        
    def stop_recording(self):
        if not self.is_recording:
            messagebox.showinfo("Info", "No recording in progress.")
            return
        self.is_recording = False

        try:
            self.stream.stop_stream()
            self.stream.close()
        except AttributeError:
            pass  # Stream was never opened

        self.audio.terminate()

        mic_wave_file = wave.open(os.path.join("Audios", "mic_" + WAVE_OUTPUT_FILENAME), 'wb')
        mic_wave_file.setnchannels(CHANNELS)
        mic_wave_file.setsampwidth(self.audio.get_sample_size(FORMAT))
        mic_wave_file.setframerate(RATE)
        mic_wave_file.writeframes(b''.join(self.mic_frames))
        mic_wave_file.close()

        system_audio = np.concatenate(self.frames, axis=0)
        system_wave_file = wave.open(os.path.join("Audios", "system_" + WAVE_OUTPUT_FILENAME), 'wb')
        system_wave_file.setnchannels(2)
        system_wave_file.setsampwidth(2)  # 2 bytes for int16
        system_wave_file.setframerate(RATE)
        system_wave_file.writeframes(system_audio.tobytes())
        system_wave_file.close()

        messagebox.showinfo("Info", f"Recording saved as {WAVE_OUTPUT_FILENAME} in Audios folder.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorder(root)
    root.mainloop()
