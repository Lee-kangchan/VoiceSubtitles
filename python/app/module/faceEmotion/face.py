import cv2
import base64

import numpy as np
from keras.preprocessing.image import img_to_array
from keras.models import load_model
from uuid import uuid4
import os


def faceEmotion():
    # 얼굴 감지 XML로드 및 훈련 된 모델로드
    emotion_classifier = load_model(os.getcwd() + '/module/faceEmotion/files/emotion_model.hdf5', compile=False)
    face_detection = cv2.CascadeClassifier(os.getcwd() + '/module/faceEmotion/files/haarcascade_frontalface_default.xml')

    EMOTIONS = ["Angry", "Disgusting", "Fearful", "Happy", "Sad", "Surpring", "Neutral"]
    camera = cv2.VideoCapture(0)
    while True:
        # 카메라에서 이미지 캡처
        #gray = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE);
        ret, frame = camera.read()

        # 색상을 그레이 스케일로 변환

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 프레임 내 얼굴 인식
        faces = face_detection.detectMultiScale(gray,
                                                scaleFactor=1.1,
                                                minNeighbors=5,
                                                minSize=(30, 30))

        # 얼굴이 감지 될 때만 감정 인식을 수행합니다.
        if len(faces) > 0:
            # 가장 큰 이미지
            face = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
            (fX, fY, fW, fH) = face
            # 신경망을 위해 이미지 크기를 48x48로 조정합니다.
            roi = gray[fY:fY + fH, fX:fX + fW]
            roi = cv2.resize(roi, (48, 48))
            roi = roi.astype("float") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)
            # 감정 예측
            preds = emotion_classifier.predict(roi)[0]
            emotion_probability = np.max(preds)
            label = EMOTIONS[preds.argmax()]

            Angry = preds[0]
            Disgusting = preds[1]
            Fearful = float(preds[2])
            Happy = preds[3]
            Sad = preds[4]
            Surprise = preds[5]
            Neutral = preds[6]

            return float(Fearful), float(Angry), float(Disgusting), float(Happy), float(Sad), float(Surprise), float(Neutral)

        else:
            return 0, 0, 0, 0, 0, 0, 0
