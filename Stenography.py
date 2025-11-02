from flask import Flask, request, redirect, render_template
from cryptography.fernet import Fernet

app = Flask(__name__)

@app.route("/")


def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])

def encode():
    #storing both the audio and video files
    video_file = request.files.get('video')
    audio_file = request.files.get('audio')

    #makes sure both are stores or errors out
    if not video_file or not audio_file:
        return "Both video and audio files are required", 400
    
    #get the data stream of the audio file
    audio_data = audio_file.read()

    #generate a key and encrypt the data
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_audio = fernet.encrypt(audio_data)


    #convert the audio data into binary
    binary_audio = ''.join(format(byte,'08b') for byte in encrypted_audio)
    print (binary_audio)

    #confirms the audio and video files have been stored
    return "Files have been uploaded sucsesfully"



if __name__ == '__main__':
    app.run(debug=True)
