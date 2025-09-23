document.getElementById('downloadBtn').addEventListener('click', () => {
    const url = document.getElementById('urlInput').value;
    const status = document.getElementById('status');

    if (!url) {
        status.innerText = 'Please enter a URL!';
        return;
    }

    status.innerText = 'Downloading...';

    // Use relative path
    fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    })
    .then(response => response.json())  // your backend returns JSON
    .then(data => {
        status.innerText = 'Download started for: ' + data.title;
        // You can implement download progress / file fetching separately
    })
    .catch(err => {
        status.innerText = err.message;
    });
});
