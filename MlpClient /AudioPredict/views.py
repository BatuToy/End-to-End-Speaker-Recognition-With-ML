from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import librosa
import soundfile as sf
import joblib
import os
from io import BytesIO
import subprocess
from collections import Counter
import speech_recognition as sr

r = sr.Recognizer()

model = joblib.load('/Users/batu/Desktop/PROJECTS/MLP/Training/3Person.joblib')
scaler = joblib.load('/Users/batu/Desktop/PROJECTS/MLP/Training/scaler.joblib')

def Index(request):
    return render(request, 'index.html')

def extract_feature(y, sr, mfcc=True, chroma=True, mel=True):
    result = np.array([])
    if chroma:
        stft = np.abs(librosa.stft(y))
    if mfcc:
        mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
        result = np.hstack((result, mfccs))
    if chroma:
        chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sr).T, axis=0)
        result = np.hstack((result, chroma))
    if mel:
        mel = np.mean(librosa.feature.melspectrogram(y=y, sr=sr).T, axis=0)
        result = np.hstack((result, mel))
    return result

def convert_audio(input_path, output_path):
    command = ['ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1', output_path]
    subprocess.run(command, check=True)

def recognize_speech(filename):
    with sr.WavFile(filename) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data, language='tr-TR')
        split_text = text.split()
        counter = len(split_text)
        return counter
    
@csrf_exempt
def record_audio(request):
    if request.method == 'POST':
        try:
            audio_file = request.FILES['audio']
            temp_input_path = '/tmp/temp_input.webm'
            temp_output_path = '/tmp/temp_output.wav'

            with open(temp_input_path, 'wb') as f:
                f.write(audio_file.read())

            convert_audio(temp_input_path, temp_output_path)

            words = recognize_speech(temp_output_path)
            y, sr = librosa.load(temp_output_path, res_type='kaiser_fast')
            os.remove(temp_input_path)
            os.remove(temp_output_path)
            # Split the audio into 5 equal parts
            part_length = len(y) // 2
            predictions = []

            for i in range(2):
                start = i * part_length
                end = (i + 1) * part_length if i < 1 else len(y)
                y_part = y[start:end]

                feature = extract_feature(y_part, sr, mfcc=True, chroma=True, mel=True)
                feature = np.array(feature).reshape(1, -1)
                feature = scaler.transform(feature)
                prediction = model.predict(feature)[0]
                predictions.append(prediction)

            # Find the most frequent prediction
            most_common_prediction = Counter(predictions).most_common(1)[0][0]

            return JsonResponse({'prediction': str(most_common_prediction), 'counter': words})
        except KeyError:
            return JsonResponse({'error': 'Invalid audio data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)
