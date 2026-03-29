import math
import cv2
import os
import hashlib
import states
from services.steg_metrics import claculate_correlation
from services.audio_compressor import extract_compressed_audio, convert_to_pcm
from services.restore_audio import run_random_forest

def run_decoding_process(video_path):
    with states.progress_lock:
        states.decode_progress = 0
    video_capture = cv2.VideoCapture(video_path)

    # if states.key is None:
    #     print("No encryption key avalibale")
    #     with states.progress_lock:
    #         states.decode_progress = 100
    #     return

    #make sure the video is captured
    if not video_capture.isOpened():
        with states.progress_lock:
            states.decode_progress = 100
        return
    

    header_bits = []
    #extrac the first 32 bits containing the audio length

    ret, frame = video_capture.read()
    if not ret:
        return "The Video dose not contain frames"
        
    flat_frame = frame.flatten(order="C")
    lsb_value = (flat_frame & 1)
    header_bits.extend(int(y) for y in lsb_value[:32])

    #get the rest of the relevant bits from the frame

    bit_string = ''.join(str(y) for y in header_bits)
    audio_data_length = states.audio_data_length
    total_bits_needed = audio_data_length * 8

    #extract the order of the shuffled bit sections
    bit_order = [int(y) for y in lsb_value[32:56]]
    section_order = []
    for i in range(8):
        section_bits = ''.join(str(bit_order[i*3 + j])for j in range(3))
        section_order.append(int(section_bits, 2))

    

    # extract the rest of the bits for the main body of audio
    payload_bits = [int(y) for y in lsb_value[56:]]

    #extract the rest of the bits based on the total_bits_needed

    while len(payload_bits) < total_bits_needed:
        ret, frame = video_capture.read()
        if not ret:
            break
        flat_frame = frame.flatten(order="C")
        lsb_value = (flat_frame & 1)
        payload_bits.extend(int(y) for y in lsb_value)

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

        with states.progress_lock:
            states.decode_progress = min(int((len(payload_bits) / (total_bits_needed)) * 100),99)

        if count == 8:
            audio_bytes.append(current_byte)
            current_byte = 0
            count = 0

    video_capture.release()
    os.remove(video_path)

    extracted_audio = bytes(audio_bytes)
    extracted_compressed_audio = extract_compressed_audio(extracted_audio)

    restored_audio = run_random_forest(
        corrupted_audio=extracted_audio,
        reference_audio=extracted_compressed_audio,
        original_audio=states.original_audio
        )

    decode_hash = hashlib.sha256(extracted_audio).hexdigest()
    states.audio_metrics.update({'decode_hash' : decode_hash})


    #furnet = Fernet(states.key)
    #decrypted_audio_data = furnet.decrypt(bytes(audio_bytes))

    #get pearsons correlation coefficient

    correlation_coefficent, bit_accuracy = claculate_correlation(states.original_audio, extracted_audio)

    original_pcm = convert_to_pcm(states.original_audio)

    restored_correclation_coefficeny, restored_bit_accuracy = claculate_correlation(list(original_pcm), restored_audio)
    

    #add the values to the audio_metrics
    states.audio_metrics.update({
        'correlation_coefficent': float(correlation_coefficent),
        'bit_rate_error': float(bit_accuracy),
        'restored_correclation_coefficeny': float(restored_correclation_coefficeny),
        'restored_bit_accuracy': float(restored_bit_accuracy)
    })

    states.audio_metrics.pop('original_audio', None)


    audio_output = "static/decrypted.mp3"



    with open (audio_output, 'wb') as f:
        f.write(extracted_audio)


    if os.path.exists("compressed_audio.opus"):
        os.remove("compressed_audio.opus")
    if os.path.exists("extracted_compressed_audio.opus"):
        os.remove("extracted_compressed_audio.opus")
    if os.path.exists("modified_audio.mp3"):
        os.remove("modified_audio.mp3")

    with states.progress_lock:
        states.decode_progress = 100
    