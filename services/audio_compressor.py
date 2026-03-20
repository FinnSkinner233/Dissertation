import subprocess
import numpy as np

#Incorperate a halftone based compression
#This is to allow the audio data to be sotred inside itself to then later be extracted for recovery

def compress_audio(audio_file):
    subprocess.run([
        "ffmpeg",
        "-i","audio_file", ##input file
        "-c:a", "libopus" ##libopus s used as it supports low bitrates
        "-b:a", "10K", ##bitrate of audio
        "compressed_audio.opus" ##output file
    ])

    with open("compressed_audio.opus", "rb") as comp_audio:
        compressed_audio_bytes = comp_audio.read()

        return compressed_audio_bytes
    
def embed_compressed_audio(compressed_audio_bytes, audio_file):
    with open (audio_file, "rb") as f:
        audio_data = f.read()

    audio_bytes = bytearray(audio_data)

    compressed_length = len(compressed_audio_bytes) ##get the length of the data to be stored
    compressed_length = format(compressed_length, '032b') ##convert the length of the bits to the first 32 bits
    binary_audio_data = ''.join(format(byte,'08b') for byte in compressed_audio_bytes)
    audio_data_stored = compressed_length + binary_audio_data

    counter = 0
    total_bits = len(audio_data_stored)

    for i in range (len(audio_bytes)):
        if counter >= total_bits:
            break
        audio_bytes[i] = (audio_bytes[i] & 0b11111110) | int(audio_data_stored[counter])
        counter += 1


    with open("modified_audio.mp3", "wb") as f:
        f.write(bytes(audio_bytes))

    return bytes(audio_bytes), total_bits

def extract_compressed_audio(extracted_audio):

    with open(extracted_audio, "rb") as f:
        audio_data = f.read()

    audio_bytes = bytearray(audio_data)
    flat_audio = list(audio_bytes)

    #get the first 32 bits to get the length of the rest of the audio

    header_bits = []
    lsb_value = [y & 1 for y in flat_audio]
    header_bits = lsb_value[:32]

    #get the rest of the relevant bits stored in the audio
    bit_string = ''.join(str(y) for y in header_bits)
    audio_data_length = int(bit_string, 2)
    total_bits_needed = audio_data_length * 8

    #extract the rest of the bits for the main body of the audio
    payload_bits = lsb_value[32: 32 + total_bits_needed]

    #convert the bits back into bytes
    compressed_bytes = bytearray()
    current_byte = 0
    count = 0

    for bit in payload_bits:
        current_byte = (current_byte << 1) | bit
        count += 1

        if count == 8:
            compressed_bytes.append(current_byte)
            current_byte = 0
            count = 0

    with open("extracted_compressed_audio.opus", "wb") as f:
        f.write(bytes(compressed_bytes))

    return bytes(compressed_bytes)

        
    
