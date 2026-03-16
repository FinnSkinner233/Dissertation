import math
import numpy as np
from skimage.metrics import structural_similarity as ssim


def calculate_mse(original_frames, modified_frames, sample_set = 5):
    
    total_mse = 0
    sample_count = 0

    for index, (orig_frames, mod_frames) in enumerate(zip(original_frames, modified_frames)):
        if index % sample_set == 0:
            image_mse = np.square(np.subtract(orig_frames.astype(float), mod_frames.astype(float))).mean()
            total_mse += image_mse
            sample_count += 1
    return total_mse / sample_count


def claculate_psnr(mse):
    if mse > 0:
        return  10 * math.log10((255 ** 2) / mse)
    return float('inf')


def calculate_ssim(original_frames, modified_frames, sample_set = 5):
    total_ssim = 0
    sample_count = 0

    for index, (orig_frames, mod_frames) in enumerate(zip(original_frames, modified_frames)):
        if index % sample_set == 0:
            frame_ssim = ssim(orig_frames, mod_frames, channel_axis=2)
            total_ssim += frame_ssim
            sample_count += 1
    return total_ssim / sample_count

def claculate_correlation(original_audio, decrypted_audio):

    original_array = np.array(list(original_audio))
    decrypted_array = np.array(list(decrypted_audio))

    #make sure the arrays are both the same length for the comparison
    smaller_array = min(len(original_array), len(decrypted_array))
    original_array = original_array[:smaller_array]
    decrypted_array = decrypted_array[:smaller_array]

    #claculate the coefficent
    correlation_coefficent = np.corrcoef(original_array, decrypted_array)[0,1]
    #claculate the bit rate error
    correct_bits = np.sum(original_array == decrypted_array)
    correct_bit_percent = (correct_bits / len(original_array) * 100)

    return float(correlation_coefficent), float (correct_bit_percent)