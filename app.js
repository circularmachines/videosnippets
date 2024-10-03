function scrollToBottom() {
    setTimeout(() => {
        const resultsContainer = document.getElementById('resultsContainer');
        resultsContainer.scrollTop = resultsContainer.scrollHeight;
    }, 200);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');

    // Parameters
    const audioDetectionIntervalTime = 250; // Increased from 100ms to 500ms
    const audioThreshold = 20; // Audio detection threshold
    const scrollDelay = 200; // Delay before scrolling in milliseconds
    const recordingMinDuration = 2500; // Minimum recording duration in milliseconds

    let mediaRecorder;
    let recordedChunks = [];
    let audioContext;
    let analyser;
    let audioDetectionInterval;
    let lastRecordingStartTime = 0;

    const localVideo = document.getElementById('localVideo');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const audioIndicator = document.getElementById('audioIndicator');

    console.log('localVideo element:', localVideo);
    console.log('startButton element:', startButton);
    console.log('stopButton element:', stopButton);
    console.log('audioIndicator element:', audioIndicator);

    const resultsContainer = document.getElementById('resultsContainer');

    async function startWebcam() {
        try {
            console.log('Starting webcam...');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            console.log('Got media stream:', stream);
            localVideo.srcObject = stream;
            localVideo.play(); // Explicitly play the video
            console.log('Webcam started successfully');

            // Set up audio analysis
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 2048;

            startAudioDetection();
        } catch (error) {
            console.error('Error starting webcam:', error);
        }
    }

    function startAudioDetection() {
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        let audioDetected = false; // Track if audio was detected
        let wasRed = true; // Track if the last state was red
        let wasYellow = false; // Track if the last state was yellow

        audioDetectionInterval = setInterval(() => {
            analyser.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;

            if (average > audioThreshold) { // Use parameter for threshold
                audioIndicator.textContent = 'Audio Detected';
                audioIndicator.style.backgroundColor = 'green'; // Green for audio on
                if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                    startRecording();
                }
            } else {
                audioIndicator.textContent = 'No Audio';
                audioIndicator.style.backgroundColor = 'red'; // Red for no audio
                if (mediaRecorder && mediaRecorder.state === 'recording' && 
                    Date.now() - lastRecordingStartTime > recordingMinDuration) {
                    stopRecording();
                }
            }
        }, audioDetectionIntervalTime); // Use parameter for interval time
    }

    function startRecording() {
        console.log('Start recording function called');
        recordedChunks = [];
        const stream = localVideo.srcObject;
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `recording-${timestamp}.webm`;
            
            console.log('Saving video as:', filename);

            const formData = new FormData();
            formData.append('video', blob, filename);
            formData.append('filename', filename);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    console.log('Video uploaded successfully, processing started');
                    // Remove this line to prevent immediate update
                    // fetchAndDisplayEntries();
                } else {
                    const errorData = await response.json();
                    console.error('Failed to upload video:', errorData.error);
                }
            } catch (error) {
                console.error('Error uploading video:', error);
            }

            // Start a new recording immediately
            startRecording();
        };

        mediaRecorder.start();
        lastRecordingStartTime = Date.now();
        startButton.disabled = true;
        stopButton.disabled = false;
        console.log('Recording started');
    }

    function stopRecording() {
        console.log('Stop recording function called');
        mediaRecorder.stop();
        startButton.disabled = false;
        stopButton.disabled = true;
    }

    console.log('Adding event listeners to buttons');
    startButton.addEventListener('click', startRecording);
    stopButton.addEventListener('click', stopRecording);

    console.log('Starting webcam');
    startWebcam();

    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
        if (audioDetectionInterval) {
            clearInterval(audioDetectionInterval);
        }
        if (audioContext) {
            audioContext.close();
        }
    });

    // Scroll to bottom on page load
    scrollToBottom();

    // Add this function to set up SSE
    function setupSSE() {
        const eventSource = new EventSource('/stream');
        
        eventSource.onmessage = function(event) {
            const entries = JSON.parse(event.data);
            console.log("Received entries:", entries);
            updateResults(entries);
        };

        eventSource.onerror = function(error) {
            console.error("EventSource failed:", error);
            eventSource.close();
        };
    }

    // Update the updateResults function
    function updateResults(entries) {
        resultsContainer.innerHTML = ''; // Clear existing results
        entries.forEach(entry => {
            const resultElement = createResultElement(entry);
            resultsContainer.appendChild(resultElement);
        });
        scrollToBottom();
    }

    // Call setupSSE when the page loads
    setupSSE();

    // Remove the fetchAndDisplayEntries function and related code

    // Update the createResultElement function
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
            const img = document.createElement('img');
            img.alt = "Frame Image";
            img.className = "result-image";
            img.onerror = () => {
                console.error('Failed to load image');
                img.style.display = 'none';
            };
            contentContainer.prepend(img);

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