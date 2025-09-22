from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import os
import threading
import uuid
import yt_dlp

# Create Flask app
app = Flask(__name__)  # Will automatically use templates/ and static/
CORS(app)

# Dictionary to track downloads (optional, for SSE/progress)
downloads = {}

@app.route("/")
def home():
    return render_template("index.html")  # Make sure index.html is inside templates/

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    fmt = data.get("format", "mp4")
    quality = data.get("quality", "best")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{fmt}"

    ydl_opts = {
        "format": "best" if fmt == "mp4" else "bestaudio/best",
        "outtmpl": f"downloads/{filename}",
        "noplaylist": True,
        "quiet": True
    }

    def run_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        downloads[file_id] = filename

    threading.Thread(target=run_download).start()

    return jsonify({"id": file_id, "title": url.split("v=")[-1]})

@app.route("/file/<file_id>")
def get_file(file_id):
    filename = downloads.get(file_id)
    if not filename:
        return "File not ready", 404
    filepath = os.path.join("downloads", filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True)


@app.route("/")
def index():
    return render_template("index.html")

# Add your download routes here...
# Example placeholder
@app.route("/download", methods=["POST"])
def download():
    return "Download logic goes here"

# Ensure download folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Run app on Render
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

