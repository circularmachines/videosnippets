document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded');

    // Parameters
    const audioDetectionIntervalTime = 50; // Interval time in milliseconds
    const audioThreshold = 5; // Audio detection threshold
    const scrollDelay = 200; // Delay before scrolling in milliseconds

    let mediaRecorder;
    let recordedChunks = [];
    let audioContext;
    let analyser;
    let audioDetectionInterval;

    const localVideo = document.getElementById('localVideo');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const audioIndicator = document.getElementById('audioIndicator');

    console.log('localVideo element:', localVideo);
    console.log('startButton element:', startButton);
    console.log('stopButton element:', stopButton);
    console.log('audioIndicator element:', audioIndicator);

    const resultsContainer = document.getElementById('resultsContainer');

    function scrollToBottom() {
        setTimeout(() => {
            resultsContainer.scrollTop = resultsContainer.scrollHeight;
        }, scrollDelay);
    }

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
                audioDetected = true; // Set audio detected state
                
                //if (wasRed) {startRecording();}
                wasRed = false;

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
                        wasRed = true;
                    }
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
                    const data = await response.json();
                    console.log('Video uploaded successfully');
                    console.log('Transcription:', data.transcription);
                    
                    // Create a new result element
                    const resultElement = document.createElement('div');
                    resultElement.className = 'result-item';
                    
                    // Create a container for the image and transcription
                    const contentContainer = document.createElement('div');
                    contentContainer.className = 'content-container';
                    resultElement.appendChild(contentContainer);

                    // Add image
                    const frameImageElement = document.createElement('img');
                    frameImageElement.src = `data:image/jpeg;base64,${data.image}`;
                    frameImageElement.alt = 'Frame Image';
                    frameImageElement.className = 'result-image';
                    contentContainer.appendChild(frameImageElement);

                    // Add transcription
                    const transcriptionElement = document.createElement('p');
                    transcriptionElement.textContent = `${data.transcription}`;
                    transcriptionElement.className = 'result-transcription';
                    contentContainer.appendChild(transcriptionElement);

                    // Add the new result to the container
                    resultsContainer.appendChild(resultElement);

                    // Scroll to the bottom of the results container after a delay
                    scrollToBottom();
                } else {
                    const errorData = await response.json();
                    console.error('Failed to upload video:', errorData.error);
                }
            } catch (error) {
                console.error('Error uploading video:', error);
            }

            // Start a new recording immediately
            //startRecording();
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

    // Scroll to bottom on page load
    scrollToBottom();
});