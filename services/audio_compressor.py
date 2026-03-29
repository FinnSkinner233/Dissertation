import subprocess
import numpy as np
import os

#Incorperate a halftone based compression
#This is to allow the audio data to be sotred inside itself to then later be extracted for recovery

def convert_to_pcm(audio_bytes, temp_name ="temp_input"):
    with open(f"{temp_name}.mp3", "wb") as f:
        f.write(audio_bytes)
    
    subprocess.run([
        "ffmpeg", "-y",
        "-i", f"{temp_name}.mp3",
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        f"{temp_name}_pcm.raw"
    ])
    with open (f"{temp_name}_pcm.raw", "rb") as f:
        raw_bytes = f.read()

    sample = np.frombuffer(raw_bytes, dtype=np.int16)
    return sample

def apply_halftone_compression(audio_samples):
    #get a sample rate to show the overall representation of the audio data

    samples = audio_samples[::4]

    reduced_sample_size = (samples/256).astype(np.int8)

    return reduced_sample_size

def halftone_to_bytes(halftone_samples):
    #convert the halftone samples to bytes for embedding during LSB
    return halftone_samples.astype(np.int8).tobytes()

def bytes_to_halftone(halftone_bytes):
    #convert the extracted bytes back into the halftone sample
    return np.frombuffer(halftone_bytes, dtype=np.int8)
    


def compress_audio(audio_file):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", audio_file, ##input file
        "-c:a", "libopus", ##libopus s used as it supports low bitrates
        "-b:a", "8K", ##bitrate of audio
        "compressed_audio.opus" ##output file
    ])

    with open("compressed_audio.opus", "rb") as comp_audio:
        compressed_audio_bytes = comp_audio.read()

        return compressed_audio_bytes
    
def embed_compressed_audio(compressed_audio_bytes, audio_data_bytes):

    audio_bytes = bytearray(audio_data_bytes)

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

    return bytes(audio_bytes)

def extract_compressed_audio(audio_bytes_input):

    audio_bytes = bytearray(audio_bytes_input)
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

        
    
