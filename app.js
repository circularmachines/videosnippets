document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');

    let mediaRecorder;
    let recordedChunks = [];
    let audioContext;
    let analyser;
    let audioDetectionInterval;

    const localVideo = document.getElementById('localVideo');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');

    // Add a new element for audio indicator
    const audioIndicator = document.createElement('div');
    audioIndicator.id = 'audioIndicator';
    audioIndicator.style.padding = '10px';
    audioIndicator.style.marginTop = '10px';
    audioIndicator.style.border = '1px solid black';
    document.body.insertBefore(audioIndicator, startButton.parentNode);

    console.log('localVideo element:', localVideo);
    console.log('startButton element:', startButton);
    console.log('stopButton element:', stopButton);

    async function startWebcam() {
        try {
            console.log('Starting webcam...');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            console.log('Got media stream:', stream);
            localVideo.srcObject = stream;
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
        let wasYellow = false; // Track if the last state was yellow

        audioDetectionInterval = setInterval(() => {
            analyser.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;

            if (average > 5) { // Adjust this threshold as needed
                audioIndicator.textContent = 'Audio Detected';
                audioIndicator.style.backgroundColor = 'green'; // Green for audio on
                audioDetected = true; // Set audio detected state
                wasYellow = false; // Reset yellow state
            } else {
                if (audioDetected) {
                    audioIndicator.textContent = 'Audio Detected (Delayed)';
                    audioIndicator.style.backgroundColor = 'yellow'; // Yellow for audio within the last second
                    wasYellow = true; // Set yellow state
                    audioDetected = false; // Reset audio detected state
                } else {
                    if (wasYellow) {
                        audioIndicator.textContent = 'No Audio';
                        audioIndicator.style.backgroundColor = 'red'; // Red for no audio
                        wasYellow = false; // Reset yellow state

                        // Stop recording when audio goes from yellow to red
                        stopRecording(); // Stop recording to save the video
                        startRecording(); // Start new recording immediately after stopping
                    } else {
                        audioIndicator.textContent = 'No Audio';
                        audioIndicator.style.backgroundColor = 'red'; // Red for no audio
                    }
                }
            }
        }, 100);
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
            
            // Create a timestamped filename
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-'); // Format timestamp
            const filename = `recording-${timestamp}.webm`;
            
            // Log the filename to the console
            console.log('Saving video as:', filename);

            // Create a FormData object and append the blob
            const formData = new FormData();
            formData.append('video', blob, filename); // Ensure filename is included
            formData.append('filename', filename); // Add filename to FormData

            try {
                // Send the video to the server
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    console.log('Video uploaded successfully');
                } else {
                    console.error('Failed to upload video');
                }
            } catch (error) {
                console.error('Error uploading video:', error);
            }

            // Start a new recording immediately
            startRecording(); // Start new recording
        };

        mediaRecorder.start();
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
});