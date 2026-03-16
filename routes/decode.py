from flask import Blueprint, request, jsonify, render_template, url_for
from threading import Thread
import states
from services.decoder import run_decoding_process

bp = Blueprint('decode',__name__)

@bp.route('/decode', methods = ['POST'])
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

@bp.route('/decode_progress')
def deocde_progress():
    with states.progress_lock:
        return jsonify(progress=states.decode_progress)
    
@bp.route('/decoded')
def decoded():
    return render_template("decoded.html", audio_file=url_for('static', filename="decrypted.mp3"))

@bp.route('/metrics')
def metrics():
    with states.progress_lock:
        return jsonify(audio_metrics = states.audio_metrics)