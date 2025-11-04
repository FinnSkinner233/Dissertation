from flask import Flask, request, redirect, render_template
from cryptography.fernet import Fernet
import cv2
import os

app = Flask(__name__)

@app.route("/")


def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])

def encode():
    #storing both the audio and video files
    video_file = request.files.get('video')
    audio_file = request.files.get('audio')


    #makes sure both are stored or errors out
    if not video_file or not audio_file:
        return "Both video and audio files are required", 400

    #save and capture the video
    video_path = "temp_video.avi"
    video_file.save(video_path)
    video_capture = cv2.VideoCapture(video_path)

    #make sure the video is captured
    if not video_capture.isOpened():
        return "Video could not be opened"
    
    #get the data stream of the audio file
    audio_data = audio_file.read()

    #generate a key and encrypt the data
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_audio = fernet.encrypt(audio_data)

    #convert the audio data into binary
    binary_audio = ''.join(format(byte,'08b') for byte in encrypted_audio)


    #create and array to store the frames of the video
    video_frames = []
    #read the frames of the video
    #ret is a boolean determined if there is a frame to read
    #frame is the data of the frame
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        video_frames.append(frame)

    video_capture.release()
    os.remove(video_path)

    #confirms the audio and video files have been stored
    return "Files have been uploaded sucsesfully"



if __name__ == '__main__':
    app.run(debug=True)
