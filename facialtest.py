from flask import Flask, request, render_template
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import sys
import cv2


# 재귀 깊이 제한 증가 (일시적인 해결책)
sys.setrecursionlimit(10000)

app = Flask(__name__)

# 모델 로드
model = load_model('emotion_model.h5')

# 감정 레이블
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

def detect_face(img_path):
    # 이미지 읽기
    img = cv2.imread(img_path)
    # Haar Cascade 분류기 로드
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # 이미지를 흑백으로 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 얼굴 감지
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        raise ValueError("No face detected in the image.")
    
    # 가장 큰 얼굴 영역 선택
    (x, y, w, h) = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)[0]
    
    # 얼굴 이미지 추출
    face_img = img[y:y+h, x:x+w]
    
    # 이미지 저장 (optional)
    cv2.imwrite('uploads/face_' + os.path.basename(img_path), face_img)
    
    return 'uploads/face_' + os.path.basename(img_path)

# 이미지 전처리 함수
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(48, 48), color_mode='grayscale')
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0  # 정규화
    return img_array

# 감정 예측 함수
def predict_emotion(img_path):
    preprocessed_img = preprocess_image(img_path)
    predictions = model.predict(preprocessed_img)
    predictions_percentage = {emotion_labels[i]: round(pred * 100, 2) for i, pred in enumerate(predictions[0])}
    max_index = np.argmax(predictions[0])
    emotion = emotion_labels[max_index]
    return emotion, predictions_percentage

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', message='No file part')
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', message='No selected file')
        if file:
            try:
                # 파일을 업로드 디렉토리에 저장
                filename = os.path.join('uploads', file.filename)
                file.save(filename)
                # 얼굴 감지 및 추출
                face_path = detect_face(filename)
                # 감정 예측
                emotion, predictions_percentage = predict_emotion(face_path)
                return render_template('result.html', original_image=filename, face_image=face_path, prediction=emotion, percentages=predictions_percentage)
            except Exception as e:
                return render_template('index.html', message=str(e))
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
