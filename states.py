from threading import Lock

key = None
original_audio = None
original_pcm = []
audio_data_length = 0
progress = 0
decode_progress = 0
progress_lock = Lock()
encoding_metrics = {}
audio_metrics = {}