#!python3.12
# ============================================
# VR-tracking | by Quantum5hadow
# github.com/Quantum5hadow/VR-tracking
# star the repo if u like it
# pull requests welcome | follow for more
# ============================================
import cv2
import numpy as np
import time
from tracker import HandTracker
from hud import HUD, COLORS, BRUSHES, LABELS


def findCamera():
    _c = "Quantum5hadow|github.com/Quantum5hadow/VR-tracking"
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                if np.mean(frame) > 5:
                    return cap
        cap.release()
    return None


cap = findCamera()
if not cap:
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

frame = None
for _ in range(30):
    ret, frame = cap.read()
    if ret and frame is not None:
        break
    time.sleep(0.1)

if frame is None:
    cap.release()
    exit()

h, w, _ = frame.shape
cv2.namedWindow("HUD", cv2.WINDOW_NORMAL)
cv2.resizeWindow("HUD", w, h)

tracker = HandTracker(maxHands=2, detectionCon=0.7, trackCon=0.7)
hud = HUD(w, h)
canvas = np.zeros((h, w, 3), dtype=np.uint8)
undoStack = []

mode = "DRAW"
colorIdx = 0
brushIdx = 0
prevX, prevY = 0, 0
pTime = 0
cooldown = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)

    tracker.process(frame)
    lmList = tracker.getLandmarks(frame)
    tracker.drawHand(frame)
    fingers = tracker.fingersUp(lmList)
    pinch = tracker.pinchDist(lmList)

    if cooldown > 0:
        cooldown -= 1

    fx = lmList[8][1] if len(lmList) > 8 else -1
    fy = lmList[8][2] if len(lmList) > 8 else -1
    isPinch = pinch < 40 and cooldown == 0

    if isPinch and fx > 0:
        for btn in hud.modeBtns:
            if btn.isOver(fx, fy):
                mode = btn.label
                cooldown = 15
                hud.showNotify(mode, 18)
                break
        for i, btn in enumerate(hud.colorBtns):
            if btn.isOver(fx, fy):
                colorIdx = i
                cooldown = 12
                hud.showNotify(LABELS[i], 15)
                break
        for i, btn in enumerate(hud.brushBtns):
            if btn.isOver(fx, fy):
                brushIdx = i
                cooldown = 12
                hud.showNotify(f"{BRUSHES[i]}px", 15)
                break
        if hud.saveBtn.isOver(fx, fy):
            cv2.imwrite("drawing.png", canvas)
            cooldown = 20
            hud.showNotify("SAVED", 25)
        elif hud.clearBtn.isOver(fx, fy):
            undoStack.append(canvas.copy())
            if len(undoStack) > 15:
                undoStack.pop(0)
            canvas = np.zeros((h, w, 3), dtype=np.uint8)
            cooldown = 18
            hud.showNotify("CLEARED", 20)
        elif hud.undoBtn.isOver(fx, fy):
            if undoStack:
                canvas = undoStack.pop()
                hud.showNotify("UNDO", 15)
            cooldown = 15
        if mode == "TYPE":
            for btn in hud.keyBtns:
                if btn.isOver(fx, fy):
                    if btn.label == "SPACE":
                        hud.typedText += " "
                    elif btn.label == "DEL":
                        hud.typedText = hud.typedText[:-1]
                    elif btn.label == "CLR":
                        hud.typedText = ""
                    else:
                        hud.typedText += btn.label
                    cooldown = 10
                    break

    if fingers and lmList:
        if mode == "DRAW" and fingers == [0, 1, 0, 0, 0]:
            x, y = lmList[8][1], lmList[8][2]
            if prevX == 0 and prevY == 0:
                prevX, prevY = x, y
            cv2.line(canvas, (prevX, prevY), (x, y), COLORS[colorIdx], BRUSHES[brushIdx])
            prevX, prevY = x, y
        elif mode == "ERASE" and fingers[1] == 1 and sum(fingers) <= 2:
            x, y = lmList[8][1], lmList[8][2]
            cv2.circle(canvas, (x, y), 28, (0, 0, 0), cv2.FILLED)
            prevX, prevY = 0, 0
        else:
            prevX, prevY = 0, 0
    else:
        prevX, prevY = 0, 0

    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    maskInv = cv2.bitwise_not(mask)
    frame = cv2.bitwise_and(frame, frame, mask=maskInv)
    frame = cv2.add(frame, canvas)

    cTime = time.time()
    fps = int(1 / (cTime - pTime)) if cTime != pTime else 0
    pTime = cTime

    hud.render(frame, fps, mode, colorIdx, brushIdx, fx, fy)
    hud.handFX(frame, lmList, mode)

    cv2.imshow("HUD", frame)
    key = cv2.waitKey(1)
    if key == ord('q') or cv2.getWindowProperty("HUD", cv2.WND_PROP_VISIBLE) < 1:
        break

tracker.close()
cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)
