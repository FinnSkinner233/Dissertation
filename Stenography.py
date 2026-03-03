import math
import random
from flask import Flask, jsonify, request, redirect, render_template, url_for, send_file
from cryptography.fernet import Fernet
import cv2
import os
import subprocess
from threading import Thread, Lock
from skimage.metrics import structural_similarity as ssim
import numpy as np
import hashlib

app = Flask(__name__)

key = None
progress = 0
decode_progress = 0
progress_lock = Lock()
encoding_metrics = {}
audio_metrics = {}

@app.route("/")
def index():

    return render_template('index.html')

#######################################
######## Main Decoding Function #######

def run_decoding_process(video_path):
    global decode_progress, key, audio_metrics
    with progress_lock:
        decode_progress = 0
    video_capture = cv2.VideoCapture(video_path)

    if key is None:
        print("No encryption key avalibale")
        with progress_lock:
            decode_progress = 100
        return

    #make sure the video is captured
    if not video_capture.isOpened():
        with progress_lock:
            decode_progress = 100
        return
    

    header_bits = []
    #extrac the first 32 bits containing the audio length

    ret, frame = video_capture.read()
    if not ret:
        return "The Video dose not contain frames"
        
    flat_frame = frame.flatten(order="C")
    lsb_value = (flat_frame & 1)
    header_bits.extend(int(b) for b in lsb_value[:32])

    #get the rest of the relevant bits from the frame

    audio_data_length = 0
    bit_string = ''.join(str(b) for b in header_bits)
    audio_data_length = int(bit_string, 2)
    total_bits_needed = audio_data_length * 8

    #extract the order of the shuffled bit sections
    bit_order = [int(b) for b in lsb_value[32:56]]
    section_order = []
    for i in range(8):
        section_bits = ''.join(str(bit_order[i*3 + j])for j in range(3))
        section_order.append(int(section_bits, 2))

    

    # extract the rest of the bits for the main body of audio
    payload_bits = [int(b) for b in lsb_value[56:]]

    #extract the rest of the bits based on the total_bits_needed

    while len(payload_bits) < total_bits_needed:
        ret, frame = video_capture.read()
        if not ret:
            break
        flat_frame = frame.flatten(order="C")
        lsb_value = (flat_frame & 1)
        payload_bits.extend(int(b) for b in lsb_value)

    #trim to the amount of bits needed
    payload_bits = payload_bits[:total_bits_needed]

    #split the bits needed into there eight shuffled sections
    bit_section_length = math.floor(total_bits_needed / 8)

    shuffled_sections = []
    for i in range(8):
        start = i * bit_section_length
        if i != 7:
            shuffled_sections.append(payload_bits[start:start + bit_section_length])
        else:
            shuffled_sections.append(payload_bits[start:])
    
    #get the original order
    sections = [val for i, val in sorted(zip(section_order,shuffled_sections))]

    payload_bits = []
    for section in sections:
        payload_bits.extend(section)

    #convert the bits into bytes
    audio_bytes = bytearray()
    current_byte = 0
    count = 0
    for bit in payload_bits:
        current_byte = (current_byte << 1) | bit
        count += 1

        with progress_lock:
            decode_progress = min(int((len(payload_bits) / (total_bits_needed)) * 100),99)

        if count == 8:
            audio_bytes.append(current_byte)
            current_byte = 0
            count = 0

    video_capture.release()
    os.remove(video_path)

    encrypted_extracted = bytes(audio_bytes)
    decode_hash = hashlib.sha256(encrypted_extracted).hexdigest()
    audio_metrics.update({'decode_hash' : decode_hash})


    furnet = Fernet(key)
    print ("check")
    decrypted_audio_data = furnet.decrypt(bytes(audio_bytes))

    #calculate Pearsons corilation cofficent

    if 'original_audio' in audio_metrics:
        original_audio = audio_metrics['original_audio']

        original_array = np.array(list(original_audio))
        decrypted_array = np.array(list(decrypted_audio_data))

        #make sure the arrays are both the same length for the comparison
        smaller_array = min(len(original_array), len(decrypted_array))
        original_array = original_array[:smaller_array]
        decrypted_array = decrypted_array[:smaller_array]

        #claculate the coefficent
        correlation_coefficent = np.corrcoef(original_array, decrypted_array)[0,1]

        #claculate the bit rate error
        correct_bits = np.sum(original_array == decrypted_array)
        correct_bit_percent = (correct_bits / len(original_array) * 100)
        print(correct_bit_percent)
        print(correlation_coefficent)

        #add the values to the audio_metrics
        audio_metrics.update({
            'correlation_coefficent': float(correlation_coefficent),
            'bit_rate_error': float(correct_bit_percent)
        })

        audio_metrics.pop('original_audio', None)


    audio_output = "static/decrypted.mp3"

    with open (audio_output, 'wb') as f:
        f.write(decrypted_audio_data)

    with progress_lock:
        decode_progress = 100
    

@app.route('/decode', methods=['POST'])
def decode():
    #store the video file to be decrypted
    video_file = request.files.get('video')

    #check to make sure that the video is stored
    if not video_file:
        return "A video file is requiered"
    
    #save and capture the video
    video_path = "temp_video.avi"
    video_file.save(video_path)

    thread = Thread(target=run_decoding_process, args=(video_path,))
    thread.start()

    return jsonify({"status": "started"})


@app.route("/decoded")
def decoded():
    return render_template("decoded.html", audio_file = url_for('static', filename="decrypted.mp3"))

@app.route("/decode_progress")
def decode_endpoint():
    with progress_lock:
        return jsonify(progress = decode_progress)


#######################################
######## Main encoding Function #######

def run_encoding_process(video_path, audio_path):
    global progress, key, encoding_metrics, audio_metrics
    progress = 0

    video_capture = cv2.VideoCapture(video_path)

    #make sure the video is captured
    if not video_capture.isOpened():
        progress = 100
        return
    
    #get the original video size
    video_size = os.path.getsize(video_path)
    
    #store the original frames for use in mse
    original_frames = []
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        original_frames.append(frame.copy())


    #get the video again so it can be read again
    video_capture.release()
    video_capture = cv2.VideoCapture(video_path)

    #get the audio from the video using ffmpeg
    # -y overrides the file if it already exists. -i sepcifies the input file. -vn ignors the video.
    # -c:a selects audio codec and libmp3lame outputs a .mp3 extension
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn", "-c:a",
        "libmp3lame", "temp_audio.mp3",
    ],check=True)
    
    #get the data stream of the audio file
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    audio_metrics.update({'original_audio': audio_data})


    #encrypt the data
    fernet = Fernet(key)
    encrypted_audio = fernet.encrypt(audio_data)

    audio_data_hash = hashlib.sha256(encrypted_audio).hexdigest()
    audio_metrics.update({'encoded_hash' : audio_data_hash})


    #get the length of the audio later for decrypting and store it as the first 32 bits
    
    audio_length = len(encrypted_audio)
    audio_length_bits = format(audio_length, '032b')


    #convert the audio data into binary

    binary_audio_data = ''.join(format(byte,'08b') for byte in encrypted_audio)
    binary_audio = audio_length_bits + binary_audio_data
    counter = 0
    total_bits = len(binary_audio)

    #get only the data bits
    data_bits = binary_audio[32:]

    #find the length of 1/8 of the total bits
    bit_section_length = math.floor((total_bits - 32) / 8)

    #seperate the bits into 8 different sections
    sections = []
    for i in range (8):
        start = i * bit_section_length
        if i != 7:
            sections.append(data_bits[start:start + bit_section_length])
        else:
            sections.append(data_bits[start:])

    #create a list with the section numbers and shuffle the list
    bit_order = list(range(8))
    random.shuffle(bit_order)

    #create a 24 bits to denote the order of the sections
    order_bits = ''.join(format(order, '03b') for order in bit_order)

    #recombine the header, bit order and sections together.
    randomised_sections = ''.join(sections[order] for order in bit_order)
    binary_audio = audio_length_bits + order_bits + randomised_sections
    
    total_bits = len(binary_audio)


    #set the dimensions and framerate of the new video
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    out_video = cv2.VideoWriter('static/output.avi',fourcc,fps,(width,height))

    #calculate payload capacity (bits per pixle) for quality metrics
    pixle_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    pixle_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    pixles_per_frame = pixle_width * pixle_height
    total_frame_NO = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
    total_pixle_NO = pixles_per_frame * total_frame_NO
    BPP = total_bits / total_pixle_NO

    #make a copy of the modified frames to be used in mse
    modified_frames = []


    #read the frames of the video
    #ret is a boolean determined if there is a frame to read
    #frame is the data of the frame
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        if counter < total_bits:
            flat_frame = frame.flatten(order="C")
            for i in range(len(flat_frame)):
                if counter >= total_bits:
                    break
                flat_frame[i] = (flat_frame[i] & 0b11111110) | int(binary_audio[counter])
                counter += 1

                with progress_lock:
                    progress = min(int((counter / total_bits) * 25),25)

            new_frame = flat_frame.reshape(frame.shape)
        else:
            new_frame = frame                

        modified_frames.append(new_frame.copy())
        out_video.write(new_frame)

    
        
    video_capture.release()
    out_video.release()
    os.remove(video_path)

    with progress_lock:
        progress = 25

    #calculate the mean squared error by comparing the original and modded frames

    total_mse = 0
    total_ssim = 0
    check_frame = 5
    sample_count = 0


    for index, (orig_frames, mod_frames) in enumerate(zip(original_frames, modified_frames)):
        if index % check_frame == 0:
            image_mse = np.square(np.subtract(orig_frames.astype(float), mod_frames.astype(float))).mean()
            total_mse += image_mse
            frame_ssim = ssim(orig_frames, mod_frames, channel_axis=2)
            total_ssim += frame_ssim
            sample_count += 1

        with progress_lock:
            progress = 25 + min(int(index / len(original_frames) * 70), 70)
    
    average_mse = total_mse / sample_count if sample_count > 0 else 0
    average_ssim = total_ssim / sample_count if sample_count > 0 else 0

    #calculate peak signal to noise ratio
    if average_mse > 0:
        PSNR = 10*math.log10((255 ** 2) / average_mse)
    else:
        PSNR = float('inf')

    #calculate the structured simularity index measurement
    with progress_lock:
        progress = 95
    




    
    #copys the audio extracted and reapplies it to the output video
    #Done to preserve the original audio from the video
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "static/output.avi",
        "-i", "temp_audio.mp3",
        "-c:v", "copy",
        "-c:a", "copy",
        "static/output_with_audio.avi"
    ],check = True)


    #get the video size after encoding
    encoded_video_size = os.path.getsize("static/output_with_audio.avi")

    #find the difference between the video sizes

    video_size_difference = encoded_video_size - video_size
    video_size_difference_percent = ((encoded_video_size - video_size) / video_size) * 100


    #set the quality metrics to be returned
    with progress_lock:
        encoding_metrics = {
            "BPP" : (BPP),
            "MSE" : (average_mse),
            "PSNR" : (PSNR),
            "SSIM" : (average_ssim),
            "video_size" : (video_size),
            "encoded_video_size" : (encoded_video_size),
            "size_difference" : (video_size_difference),
            "percent_size_diff" : (video_size_difference_percent)
        }



    with progress_lock:
        progress = 99
    
    try:
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists("static/output.avi"):
            os.remove("static/output.avi")
    except Exception as e:
        print (f"Cleanup error: {e}")

    if os.path.exists('static/output_with_audio.avi'):
        print(f"File created: {os.path.getsize('static/output_with_audio.avi')} bytes")
    else:
        print("File NOT created!")
        

    with progress_lock:
        progress = 100
    

@app.route('/encode', methods=['POST'])

def encode():
    global key
    global progress
    with progress_lock:
        progress = 0
    key = Fernet.generate_key()
    #storing both the audio and video files
    
    video_file = request.files.get('video')
    audio_file = request.files.get('audio')

    #makes sure both are stored or errors out
    if not video_file or not audio_file:
        return jsonify({"error": "Both video and audio files are required"})
    


    #save and capture the video
    video_path = "temp_video.avi"
    video_file.save(video_path)
    audio_path = "temp_audio_input.mp3"
    audio_file.save(audio_path)
    
    thread = Thread(target=run_encoding_process, args=(video_path, audio_path))
    thread.start()

    return jsonify({"status": "started"})





@app.route("/download")
def download_encoded_video():
    try:
        return send_file(
            'static/output_with_audio.avi',
            as_attachment = True,
            download_name = 'encoded_video.avi'
        )
    except FileNotFoundError:
        return jsonify({"error": "video file not found"}), 404

@app.route("/metrics")
def get_audio_metrics():
    with progress_lock:
        return jsonify(audio_metrics = audio_metrics)

@app.route("/progress")
def encode_endpoint():
    with progress_lock:
        return jsonify(progress = progress)

@app.route("/quality_metrics")
def return_quality_metrics():
    with progress_lock:
        return jsonify(encoding_metrics)

@app.route("/video")
def download_video():
    return render_template("video.html")

if __name__ == '__main__':
    app.run(debug=True)

