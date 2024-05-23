# Testing the MLP model live on the microphone input

import sounddevice as sd
import soundfile as sf
import numpy as np
import joblib
import librosa
import os



model = joblib.load('path/to/your/model.joblib')
scaler = joblib.load('path/to/your/scaler.joblib')

# Extract the features from the audio file
def extract_feature(file_name, mfcc, chroma, mel):
    X, sample_rate = librosa.load(os.path.join(file_name), res_type='kaiser_fast')
    if chroma:
        stft = np.abs(librosa.stft(X))
    result = np.array([])
    if mfcc:
        mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T, axis=0)
        result = np.hstack((result, mfccs))
    if chroma:
        chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
        result = np.hstack((result, chroma))
    if mel:
        mel = np.mean(librosa.feature.melspectrogram(y=X, sr=sample_rate).T, axis=0)
        result = np.hstack((result, mel))
    return result

def record_audio():
    fs = 44100
    seconds = 5
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()
    sf.write('audio.wav', myrecording, fs)
    return 'audio.wav'

def split_audio(file_name):
    X, sample_rate = librosa.load(os.path.join(file_name), res_type='kaiser_fast')
    duration = len(X) / sample_rate
    split_duration = duration / 5
    for i in range(5):
        start = int(i * split_duration * sample_rate)
        end = int((i + 1) * split_duration * sample_rate)
        split = X[start:end]
        sf.write(f'audio_{i}.wav', split, sample_rate)

def predict_parts():
    predictions = []
    for i in range(5):
        feature = extract_feature(f'audio_{i}.wav', mfcc=True, chroma=True, mel=True)
        feature = np.array(feature).reshape(1, -1)   
        feature = scaler.transform(feature)
        prediction = model.predict(feature)
        predictions.append(prediction[0])
    return predictions

def print_prediction(predictions):
    print(predictions)
    prediction = max(set(predictions), key=predictions.count)
    print(prediction)



def test():
    file_name = record_audio()
    split_audio(file_name)
    predictions = predict_parts()
    print_prediction(predictions=predictions)
test()