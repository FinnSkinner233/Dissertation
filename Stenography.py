from flask import Flask, request, redirect, render_template
app = Flask(__name__)

@app.route("/")


def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])

def encode():
    video_file = request.files.get('video')
    audio_file = request.files.get('audio')

    if not video_file or not audio_file:
        return "Both video and audio files are required", 400
    

    return "Files have been uploaded sucsesfully"

if __name__ == '__main__':
    app.run(debug=True)
