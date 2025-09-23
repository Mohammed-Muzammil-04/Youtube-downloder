from flask import Flask, request, send_file, after_this_request, jsonify, Response, stream_with_context, render_template
from flask_cors import CORS
import os, uuid, threading, time, yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

progress_dict = {}
cancel_flags = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    progress_dict[file_id] = {'percent':0,'speed':0,'eta':0,'downloaded':0,'total':0,'filename':None,'error':None,'title':'', 'thumbnail':''}
    cancel_flags[file_id] = False

    # Fetch title & thumbnail
    try:
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            info = ydl.extract_info(url, download=False)
            progress_dict[file_id]['title'] = info.get('title','Unknown')
            progress_dict[file_id]['thumbnail'] = info.get('thumbnail','')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if format_type == 'mp3':
        base_filename = os.path.join(DOWNLOAD_FOLDER, file_id)
        ydl_opts = {
            'format':'bestaudio/best',
            'outtmpl':base_filename,
            'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}],
            'progress_hooks':[lambda d: update_progress(d,file_id)]
        }
    else:
        filename = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp4")
        ydl_format = 'bestvideo[height<={quality}]+bestaudio/best' if quality != 'best' else 'bestvideo+bestaudio/best'
        ydl_opts = {
            'format': ydl_format,
            'outtmpl': filename,
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
            'progress_hooks':[lambda d: update_progress(d,file_id)]
        }

    def download_task():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                if cancel_flags[file_id]:
                    progress_dict[file_id]['error'] = 'Download cancelled'
                    return
                progress_dict[file_id]['filename'] = filename if format_type=='mp4' else base_filename+'.mp3'
                progress_dict[file_id]['percent'] = 100
        except Exception as e:
            progress_dict[file_id]['error'] = str(e)
            progress_dict[file_id]['percent'] = -1

    threading.Thread(target=download_task).start()
    return jsonify({"id":file_id,"title":progress_dict[file_id]['title'],"thumbnail":progress_dict[file_id]['thumbnail']})

@app.route('/progress/<file_id>')
def progress(file_id):
    def generate():
        while True:
            data = progress_dict.get(file_id,{})
            msg = f"{data.get('percent',0)}|{data.get('speed',0)}|{data.get('eta',0)}|{data.get('downloaded',0)}|{data.get('total',0)}"
            yield f"data:{msg}\n\n"
            if data.get('percent',0) >= 100 or data.get('percent',0) == -1:
                break
            time.sleep(0.2)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/file/<file_id>')
def get_file(file_id):
    timeout = 20
    waited = 0
    while not progress_dict.get(file_id,'').get('filename') and waited < timeout:
        time.sleep(0.2)
        waited += 0.2
    filename = progress_dict[file_id].get('filename')
    if not filename or not os.path.exists(filename):
        return jsonify({"error":"File not ready"}),404

    @after_this_request
    def remove_file(response):
        try: os.remove(filename)
        except Exception as e: print(f"Error deleting file: {e}")
        return response

    return send_file(filename, as_attachment=True)

@app.route('/cancel/<file_id>', methods=['POST'])
def cancel_download(file_id):
    cancel_flags[file_id] = True
    return jsonify({"status":"cancelled"})

def update_progress(d, file_id):
    if cancel_flags.get(file_id):
        raise yt_dlp.utils.DownloadError("Cancelled by user")
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes',0)
        speed = d.get('speed',0)
        eta = d.get('eta',0)
        percent = int(downloaded/total_bytes*100) if total_bytes else 0
        progress_dict[file_id].update({'percent':percent,'speed':speed,'eta':eta,'downloaded':downloaded,'total':total_bytes})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
