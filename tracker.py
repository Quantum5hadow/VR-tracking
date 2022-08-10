# ============================================
# VR-tracking | by Quantum5hadow
# github.com/Quantum5hadow/VR-tracking
# star the repo if u like it
# pull requests welcome | follow for more
# ============================================
import cv2
import time
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarker, HandLandmarkerOptions, HandLandmarksConnections
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python import BaseOptions
from mediapipe import Image, ImageFormat

CONNECTIONS = [(c.start, c.end) for c in HandLandmarksConnections.HAND_CONNECTIONS]
_Q5 = "\x51\x75\x61\x6e\x74\x75\x6d\x35\x68\x61\x64\x6f\x77"
_GH = "\x67\x69\x74\x68\x75\x62\x2e\x63\x6f\x6d\x2f" + _Q5


class HandTracker:
    def __init__(self, modelPath="hand_landmarker.task", maxHands=1, detectionCon=0.7, trackCon=0.7):
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=modelPath),
            running_mode=VisionTaskRunningMode.VIDEO,
            num_hands=maxHands,
            min_hand_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.landmarks = []
        self.startTime = time.time()

    def process(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mpImg = Image(image_format=ImageFormat.SRGB, data=rgb)
        ts = int((time.time() - self.startTime) * 1000)
        result = self.landmarker.detect_for_video(mpImg, ts)
        self.landmarks = result.hand_landmarks
        return result

    def drawHand(self, img):
        if not self.landmarks:
            return
        h, w, _ = img.shape
        for hand in self.landmarks:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand]
            for s, e in CONNECTIONS:
                cv2.line(img, pts[s], pts[e], (200, 200, 0), 1, cv2.LINE_AA)
            for p in pts:
                cv2.circle(img, p, 2, (0, 255, 255), cv2.FILLED)

    def getLandmarks(self, img, handNo=0):
        if not self.landmarks or handNo >= len(self.landmarks):
            return []
        h, w, _ = img.shape
        return [[i, int(lm.x * w), int(lm.y * h)] for i, lm in enumerate(self.landmarks[handNo])]

    def fingersUp(self, lmList):
        if len(lmList) < 21:
            return []
        fingers = []
        fingers.append(1 if lmList[4][1] < lmList[3][1] else 0)
        for tip in [8, 12, 16, 20]:
            fingers.append(1 if lmList[tip][2] < lmList[tip - 2][2] else 0)
        return fingers

    def pinchDist(self, lmList):
        if len(lmList) < 21:
            return 999
        return int(((lmList[4][1] - lmList[8][1])**2 + (lmList[4][2] - lmList[8][2])**2)**0.5)

    def close(self):
        self.landmarker.close()
