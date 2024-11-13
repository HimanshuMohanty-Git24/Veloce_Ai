// main.js

// Global variables
let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// Function to start recording audio
function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.start();
      isRecording = true;

      mediaRecorder.addEventListener('dataavailable', event => {
        audioChunks.push(event.data);
      });

      mediaRecorder.addEventListener('stop', () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = [];
        uploadAudio(audioBlob);
      });
    })
    .catch(error => {
      console.error('Error accessing microphone:', error);
    });
}

// Function to stop recording audio
function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
  }
}

// Function to upload recorded audio to the server
function uploadAudio(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recorded_audio.webm');

  fetch('/upload_audio', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    // Handle the server response, e.g., display the transcribed text
    displayTranscription(data.transcript);
  })
  .catch(error => {
    console.error('Error uploading audio:', error);
  });
}

// Function to display the transcribed text
function displayTranscription(transcript) {
  const chatContainer = document.getElementById('chatContainer');
  const userMessage = document.createElement('div');
  userMessage.classList.add('chat-message', 'user');
  userMessage.textContent = transcript;
  chatContainer.appendChild(userMessage);

  // Send the transcript to the server for further processing
  sendTranscriptToServer(transcript);
}

// Function to send the transcribed text to the server
function sendTranscriptToServer(transcript) {
  fetch('/process_transcript', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ transcript: transcript })
  })
  .then(response => response.json())
  .then(data => {
    // Handle the server response, e.g., display the assistant's response
    displayAssistantResponse(data.response);
  })
  .catch(error => {
    console.error('Error processing transcript:', error);
  });
}

// Function to display the assistant's response
function displayAssistantResponse(response) {
  const chatContainer = document.getElementById('chatContainer');
  const assistantMessage = document.createElement('div');
  assistantMessage.classList.add('chat-message', 'assistant');
  assistantMessage.textContent = response;
  chatContainer.appendChild(assistantMessage);
}

// Event listener for the voice input button
const voiceInputButton = document.getElementById('voiceInputButton');
voiceInputButton.addEventListener('click', () => {
  if (isRecording) {
    stopRecording();
    voiceInputButton.textContent = 'Start Recording';
  } else {
    startRecording();
    voiceInputButton.textContent = 'Stop Recording';
  }
});

// Event listener for the text input form
const textInputForm = document.getElementById('textInputForm');
textInputForm.addEventListener('submit', event => {
  event.preventDefault();
  const textInput = document.getElementById('textInput');
  const userInput = textInput.value.trim();
  if (userInput) {
    displayTranscription(userInput);
    sendTranscriptToServer(userInput);
    textInput.value = '';
  }
});