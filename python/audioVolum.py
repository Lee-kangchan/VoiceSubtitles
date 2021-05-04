import pyaudio
import numpy as np

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                frames_per_buffer=CHUNK, input_device_index=2)

while (True):
    data = np.fromstring(stream.read(CHUNK), dtype=np.int16)
    print(int(np.average(np.abs(data))))

stream.stop_stream()
stream.close()
p.terminate()