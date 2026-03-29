from flask import Blueprint, request, jsonify, send_file
from threading import Thread
import states
from services.encoder import run_encoding_process

bp = Blueprint('encode',__name__)

@bp.route('/encode', methods = ['POST'])
def encode():

    ##states.key  = Fernet.generate_key()
    
    
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

@bp.route('/progress')
def encode_progress():
    with states.progress_lock:
        return jsonify(progress = states.progress)
    
@bp.route('/quality_metrics')
def quality_metrics():
    with states.progress_lock:
        return jsonify(states.encoding_metrics)
    
@bp.route('/download')
def download():
    try:
        return send_file(
            'static/output_with_audio.avi',
            as_attachment = True,
            download_name = 'encoded_video.avi'
        )
    except FileNotFoundError:
        return jsonify({"error": "video file not found"}), 404