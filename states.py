from threading import Lock

key = None
progress = 0
decode_progress = 0
progress_lock = Lock()
encoding_metrics = {}
audio_metrics = {}