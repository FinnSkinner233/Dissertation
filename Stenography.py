from flask import Flask, request, redirect, render_template, url_for
from cryptography.fernet import Fernet
import cv2
import os
import numpy

app = Flask(__name__)

@app.route("/")
def index():
    global key
    key = Fernet.generate_key()
    return render_template('index.html')

@app.route('/decode', methods=['POST'])

def decode():
    #store the video file to be decrypted
    video_file = request.files.get('video')

    #check to make sure that the video is stored
    if not video_file:
        return "A video file is requiered", 400
    
    #save and capture the video
    video_path = "temp_video.avi"
    video_file.save(video_path)
    video_capture = cv2.VideoCapture(video_path)

    #make sure the video is captured
    if not video_capture.isOpened():
        return "Video could not be opened"
    

    audio_list = []

    bits_needed = 32
    #extrac the first 32 bits containing the audio length
    while len(audio_list) < bits_needed:
        ret, frame = video_capture.read()
        if not ret:
            break
        
        lsb_value = (frame & 1).ravel()
        remaining_bits = bits_needed - len(audio_list)
        audio_list.extend(lsb_value[:remaining_bits])

    audio_data_length = int(''.join(map(str,audio_list)),2)
    total_bits_needed = 32 + audio_data_length * 8


    while len(audio_list) < total_bits_needed:
        ret, frame = video_capture.read()
        if not ret:
            break

        lsb_value = (frame & 1).ravel()
        remaining = total_bits_needed - len(audio_list)
        audio_list.extend(lsb_value[:remaining])

    video_capture.release()
    audio_bits = audio_list[32:total_bits_needed]

    joined_bits = ''.join(map(str, audio_bits))
    audio_bytes = int(joined_bits,2).to_bytes(audio_data_length, 'big')


    furnet = Fernet(key)
    decrypted_audio_data = furnet.decrypt(audio_bytes)

    audio_output = "static/decrypted.mp3"

    with open (audio_output, 'wb') as f:
        f.write(decrypted_audio_data)
    
    return render_template("decoded.html", audio_file=audio_output)



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

    #encrypt the data
    fernet = Fernet(key)
    encrypted_audio = fernet.encrypt(audio_data)

    #get the length of the audio later for decrypting and store it as the first 32 bits
    audio_length = len(encrypted_audio)
    audio_length_bits = format(audio_length, '032b')

    #convert the audio data into binary
    binary_audio = audio_length_bits + ''.join(format(byte,'08b') for byte in encrypted_audio)

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
    return render_template("video.html")

if __name__ == '__main__':
    app.run(debug=True)
