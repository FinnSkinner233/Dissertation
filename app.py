from flask import Flask, render_template
from routes import encode, decode

app = Flask(__name__)
app.register_blueprint(encode.bp)
app.register_blueprint(decode.bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video")
def video():
    return render_template("video.html")

if __name__ == '__main__':
    app.run(debug=True)