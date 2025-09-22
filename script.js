document.getElementById('downloadBtn').addEventListener('click', () => {
    const url = document.getElementById('urlInput').value;
    const status = document.getElementById('status');

    if (!url) {
        status.innerText = 'Please enter a URL!';
        return;
    }

    status.innerText = 'Downloading...';

    fetch('http://127.0.0.1:5000/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    })
    .then(response => {
        if (!response.ok) throw new Error('Download failed!');
        return response.blob();
    })
    .then(blob => {
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = 'video.mp4';
        link.click();
        status.innerText = 'Download complete!';
    })
    .catch(err => {
        status.innerText = err.message;
    });
});
