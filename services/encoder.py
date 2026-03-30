import math
import random
import cv2
import os
import subprocess
from skimage.metrics import structural_similarity as ssim
import hashlib
import states
from services.audio_compressor import compress_audio, embed_compressed_audio
from services.steg_metrics import calculate_mse, claculate_psnr, calculate_ssim



def run_encoding_process(video_path, audio_path):
    states.progress = 0

    video_capture = cv2.VideoCapture(video_path)

    #make sure the video is captured
    if not video_capture.isOpened():
        states.progress = 100
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

    
    
    compressed_audio_data = compress_audio("temp_audio.mp3")
    audio_data = embed_compressed_audio(compressed_audio_data, audio_data)

    states.original_audio = audio_data

    

    #encrypt the data
    #fernet = Fernet(states.key)
    #encrypted_audio = fernet.encrypt(audio_data)

    audio_data_hash = hashlib.sha256(audio_data).hexdigest()
    states.audio_metrics.update({'encoded_hash' : audio_data_hash})


    #get the length of the audio later for decrypting and store it as the first 32 bits
    audio_length = len(audio_data)
    audio_length_bits = format(audio_length, '032b')

    states.audio_data_length = audio_length

    #convert the audio data into binary

    binary_audio_data = ''.join(format(byte,'08b') for byte in audio_data)
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
    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
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

                with states.progress_lock:
                    states.progress = min(int((counter / total_bits) * 40),40)

            new_frame = flat_frame.reshape(frame.shape)
        else:
            new_frame = frame                

        modified_frames.append(new_frame.copy())
        out_video.write(new_frame)

    
        
    video_capture.release()
    out_video.release()
    os.remove(video_path)

    with states.progress_lock:
        states.progress = 50

    average_mse = calculate_mse(original_frames, modified_frames)
    PSNR = claculate_psnr(average_mse)
    average_ssim = calculate_ssim(original_frames, modified_frames)

    with states.progress_lock:
        states.progress = 95
    




    
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
    with states.progress_lock:
        states.encoding_metrics = {
            "BPP" : (BPP),
            "MSE" : (average_mse),
            "PSNR" : (PSNR),
            "SSIM" : (average_ssim),
            "video_size" : (video_size),
            "encoded_video_size" : (encoded_video_size),
            "size_difference" : (video_size_difference),
            "percent_size_diff" : (video_size_difference_percent)
        }



    with states.progress_lock:
        states.progress = 99
    
    if os.path.exists("temp_audio.mp3"):
        os.remove("temp_audio.mp3")
    if os.path.exists(audio_path):
        os.remove(audio_path)
    if os.path.exists("static/output.avi"):
        os.remove("static/output.avi")
        

    with states.progress_lock:
        states.progress = 100

