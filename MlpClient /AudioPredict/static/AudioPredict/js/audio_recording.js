const recordButton = document.getElementById('recordButton');
const predictionResult = document.getElementById('predictionResult');

let audioChunks = [];
let mediaRecorder;

recordButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        recordButton.textContent = "Record";
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const options = MediaRecorder.isTypeSupported('audio/wav') ? { mimeType: 'audio/wav' } : { mimeType: 'audio/webm' };
                mediaRecorder = new MediaRecorder(stream, options);
                mediaRecorder.start();
                recordButton.textContent = "Stop";

                audioChunks = [];
                mediaRecorder.addEventListener("dataavailable", event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener("stop", () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    sendAudioToServer(audioBlob);
                });
            }).catch(error => console.error("Error accessing media devices.", error));
    }
});

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav"); // Ensure this matches the backend expectations

    fetch('/predict/', {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        predictionResult.textContent = `Prediction: ${data.prediction}`;
    })
    .catch(error => {
        console.error('Error:', error);
        predictionResult.textContent = 'Error making prediction';
    });
}
