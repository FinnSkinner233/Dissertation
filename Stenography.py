from flask import Flask, request, redirect, render_template, url_for
from cryptography.fernet import Fernet
import cv2
import os
import numpy

app = Flask(__name__)

@app.route("/")


def index():
    return render_template('index.html')

@app.route('/decode', methods=['POST'])

def decode():
    pass

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

    counter = 0
    total_bits = len(binary_audio)


    #set the dimensions and framerate of the new video
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out_video = cv2.VideoWriter('static/output.avi',fourcc,fps,(width,height))

    #read the frames of the video
    #ret is a boolean determined if there is a frame to read
    #frame is the data of the frame
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        if counter < total_bits:
            flat_frame = frame.flatten()
            num_pixles = flat_frame.size

            indices = list(range(num_pixles))
            for i in range(len(flat_frame)):
                if counter < total_bits:
                    flat_frame[i] = (flat_frame[i] & numpy.uint8(254)) | int(binary_audio[counter])
                    counter += 1
            new_frame = flat_frame.reshape(frame.shape)
        else:
            new_frame = frame                

        out_video.write(new_frame)


        
    video_capture.release()
    out_video.release()
    os.remove(video_path)



    #confirms the audio and video files have been stored
    return redirect(url_for('download_video'))

@app.route("/video")
def download_video():
    return render_template("video.html", video_path = "/static/output.avi")

if __name__ == '__main__':
    app.run(debug=True)
