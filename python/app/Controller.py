import pyaudio
from flask import Flask, render_template, jsonify, request
import numpy as np
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World'

@app.route('/test')
def test():
    return render_template("main.html")

@app.route('/test2')
def test2():
    return render_template("main2.html")



@app.route('/test3', methods=['GET'])
def ajax():
    RATE = 16000
    CHUNK = int(RATE / 10)  # 100ms

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=2)

    data = np.fromstring(stream.read(CHUNK), dtype=np.int16)

    stream.stop_stream()
    stream.close()
    p.terminate()

    return jsonify(result = np.average(np.abs(data)))

if __name__ == '__main__':
    app.run(debug=True)