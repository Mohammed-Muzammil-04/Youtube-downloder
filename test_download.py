import requests

backend_url = "http://127.0.0.1:5000/download"
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Standard public video

response = requests.post(backend_url, json={"url": video_url}, stream=True)

if response.status_code == 200:
    with open("video.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Downloaded video.mp4 successfully!")
else:
    try:
        # If backend returned JSON error
        error = response.json()
    except Exception:
        error = response.text
    print("Error:", response.status_code, error)
