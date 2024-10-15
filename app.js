function scrollToBottom() {
    setTimeout(() => {
        const resultsContainer = document.getElementById('resultsContainer');
        resultsContainer.scrollTop = resultsContainer.scrollHeight;
    }, 200);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');

    const localVideo = document.getElementById('localVideo');
    const resultsContainer = document.getElementById('resultsContainer');
    const recordButton = document.getElementById('recordButton');

    let captureInterval;
    let isRecording = false;
    let canvas;

    const promptInput = document.getElementById('promptInput');
    const submitPromptButton = document.getElementById('submitPrompt');

    submitPromptButton.addEventListener('click', submitPrompt);

    async function submitPrompt() {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        try {
            submitPromptButton.disabled = true;
            recordButton.disabled = true;
            
            const response = await fetch('/submit-prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Prompt submitted successfully:', result);
                promptInput.value = '';
            } else {
                console.error('Failed to submit prompt:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('Error submitting prompt:', error);
        } finally {
            submitPromptButton.disabled = false;
            recordButton.disabled = false;
        }
    }

    async function startWebcam() {
        try {
            console.log('Starting webcam...');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            console.log('Got media stream:', stream);

            // Create a video element to get the original video dimensions
            const videoElement = document.createElement('video');
            videoElement.srcObject = stream;
            await new Promise(resolve => videoElement.onloadedmetadata = resolve);

            // Calculate the crop dimensions
            const originalWidth = videoElement.videoWidth;
            const originalHeight = videoElement.videoHeight;
            const aspectRatio = originalWidth / originalHeight;
            let cropWidth, cropHeight;

            if (aspectRatio > 1) {
                cropHeight = originalHeight;
                cropWidth = cropHeight;
            } else {
                cropWidth = originalWidth;
                cropHeight = cropWidth;
            }

            // Create a canvas to crop and scale the video
            canvas = document.createElement('canvas');
            canvas.width = 480;
            canvas.height = 480;
            const ctx = canvas.getContext('2d');

            // Update the video feed
            function updateCanvas() {
                ctx.drawImage(
                    videoElement,
                    (originalWidth - cropWidth) / 2,
                    (originalHeight - cropHeight) / 2,
                    cropWidth,
                    cropHeight,
                    0,
                    0,
                    480,
                    480
                );
                requestAnimationFrame(updateCanvas);
            }

            // Start playing the video element
            await videoElement.play();

            // Start updating the canvas
            updateCanvas();

            // Create a new stream from the canvas
            const croppedStream = canvas.captureStream();

            localVideo.srcObject = croppedStream;
            await localVideo.play();
            console.log('Webcam started successfully');
            recordButton.disabled = false;  // Enable the record button
            updateRecordButtonState();  // Update the button state
        } catch (error) {
            console.error('Error starting webcam:', error);
        }
    }

    function toggleRecording() {
        if (isRecording) {
            stopCapturing();
        } else {
            startCapturing();
        }
    }

    function startCapturing() {
        if (isRecording) return;
        isRecording = true;
        console.log('Starting capture...');
        captureInterval = setInterval(() => {
            console.log('Capturing image...');
            if (canvas) {
                const imageDataUrl = canvas.toDataURL('image/jpeg');
                console.log('Image captured, sending to server...');
                sendImageToServer(imageDataUrl);
            } else {
                console.error('Canvas is not available');
            }
        }, 1000); // Capture every second
        updateRecordButtonState();
    }

    function stopCapturing() {
        if (!isRecording) return;
        isRecording = false;
        clearInterval(captureInterval);
        updateRecordButtonState();
    }

    function updateRecordButtonState() {
        recordButton.textContent = isRecording ? 'Stop Recording' : 'Start Recording';
        recordButton.style.backgroundColor = isRecording ? 'red' : 'grey';
    }

    async function sendImageToServer(imageDataUrl) {
        console.log('Preparing to send image to server...');
        const blob = await (await fetch(imageDataUrl)).blob();
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');

        try {
            console.log('Sending image to server...');
            const response = await fetch('/upload-image', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const responseText = await response.text();
                console.log('Image uploaded successfully. Server response:', responseText);
            } else {
                console.error('Failed to upload image:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Server error response:', errorText);
            }
        } catch (error) {
            console.error('Error uploading image:', error);
        }
    }

    console.log('Starting webcam');
    startWebcam();  // No need for .then() here

    // Set up button event listener
    recordButton.addEventListener('click', toggleRecording);

    // Scroll to bottom on page load
    scrollToBottom();

    function setupSSE() {
        const eventSource = new EventSource('/stream');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'entries') {
                updateResults(data.entries);
            } else if (data.type === 'prompt_processed') {
                console.log('Prompt processed:', data.message);
                recordButton.disabled = false;
            }
        };

        eventSource.onerror = function(error) {
            console.error("EventSource failed:", error);
            eventSource.close();
        };
    }

    function updateResults(entries) {
        resultsContainer.innerHTML = ''; // Clear existing results
        entries.forEach(entry => {
            const resultElement = createResultElement(entry);
            resultsContainer.appendChild(resultElement);
        });
        scrollToBottom();
    }

    setupSSE();

    function createResultElement(entry) {
        console.log("Creating result element for entry:", entry);
        const resultElement = document.createElement('div');
        resultElement.className = 'result-item';
        const contentContainer = document.createElement('div');
        contentContainer.className = 'content-container';

        if (entry.transcription) {
            const transcriptionElement = document.createElement('div');
            transcriptionElement.className = 'result-transcription';
            transcriptionElement.innerHTML = entry.transcription;
            contentContainer.appendChild(transcriptionElement);
        } else {
            contentContainer.innerHTML = '<p>No transcription available</p>';
        }

        if (entry.images && entry.images.length > 0) {
            const imageContainer = document.createElement('div');
            imageContainer.className = 'image-container';

            const img = document.createElement('img');
            img.alt = "Frame Image";
            img.className = "result-image";
            img.onerror = () => {
                console.error('Failed to load image');
                img.style.display = 'none';
            };

            imageContainer.appendChild(img);
            contentContainer.prepend(imageContainer);

            // Set up animation
            let currentImageIndex = 0;
            function updateImage() {
                img.src = `data:image/jpeg;base64,${entry.images[currentImageIndex]}`;
                currentImageIndex = (currentImageIndex + 1) % entry.images.length;
            }
            updateImage(); // Show the first image immediately
            setInterval(updateImage, 1000); // Change image every 1 second
        }

        resultElement.appendChild(contentContainer);
        return resultElement;
    }
});
