# ============================================
# VR-tracking | by Quantum5hadow
# github.com/Quantum5hadow/VR-tracking
# star the repo if u like it
# pull requests welcome | follow for more
# ============================================
import cv2
import numpy as np
import math

COLORS = [(255, 255, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 255), (0, 165, 255), (0, 0, 255)]
LABELS = ["CYAN", "MAGENTA", "GREEN", "YELLOW", "WHITE", "ORANGE", "RED"]
BRUSHES = [3, 6, 10, 16]
_CREDIT = b'\x51\x75\x61\x6e\x74\x75\x6d\x35\x68\x61\x64\x6f\x77'.decode()
_REPO = "github.com/Quantum5hadow/VR-tracking"


def glow(img, center, radius, color, thick=1, layers=3):
    for i in range(layers, 0, -1):
        cv2.circle(img, center, radius + i * 2, (*[max(0, c // (i + 1)) for c in color],), thick, cv2.LINE_AA)
    cv2.circle(img, center, radius, color, thick, cv2.LINE_AA)


def glass(img, x, y, w, h, alpha=0.4, border=(0, 255, 200)):
    ih, iw = img.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(iw, x + w), min(ih, y + h)
    if x2 > x1 and y2 > y1:
        roi = img[y1:y2, x1:x2]
        dark = np.full_like(roi, 10)
        cv2.addWeighted(dark, alpha, roi, 1 - alpha, 0, roi)
    if border:
        cv2.rectangle(img, (x, y), (x + w, y + h), border, 1)


class Btn:
    def __init__(self, x, y, w, h, label):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label

    def isOver(self, px, py):
        return self.x < px < self.x + self.w and self.y < py < self.y + self.h

    def draw(self, img, active=False, hover=False):
        bc = (0, 255, 200) if active else (0, 180, 140) if hover else (40, 40, 40)
        al = 0.5 if active else 0.35 if hover else 0.2
        glass(img, self.x, self.y, self.w, self.h, al, bc)
        ts = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)[0]
        tx = self.x + (self.w - ts[0]) // 2
        ty = self.y + (self.h + ts[1]) // 2
        tc = (0, 255, 200) if active else (0, 200, 160) if hover else (90, 90, 90)
        cv2.putText(img, self.label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.35, tc, 1, cv2.LINE_AA)


class HUD:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.tick = 0
        self.trail = []
        self.notify = ""
        self.notifyTimer = 0
        self.typedText = ""
        self._buildUI()

    def _buildUI(self):
        self.modeBtns = [Btn(8, 46 + i * 40, 52, 34, m) for i, m in enumerate(["DRAW", "TYPE", "ERASE"])]
        self.saveBtn = Btn(8, 46 + 3 * 40 + 8, 52, 34, "SAVE")
        self.clearBtn = Btn(8, 46 + 4 * 40 + 8, 52, 34, "CLEAR")
        self.undoBtn = Btn(8, 46 + 5 * 40 + 8, 52, 34, "UNDO")
        self.actionBtns = [self.saveBtn, self.clearBtn, self.undoBtn]
        px = self.w - 42
        self.colorBtns = [Btn(px, 46 + i * 32, 34, 26, "") for i in range(len(COLORS))]
        bStart = 46 + len(COLORS) * 32 + 8
        self.brushBtns = [Btn(px, bStart + i * 28, 34, 22, "") for i in range(len(BRUSHES))]
        kw, kh, gap = 40, 34, 3
        r1w = 10 * (kw + gap) - gap
        kx = 68
        ky = self.h - 165
        self.keyBtns = []
        for i, k in enumerate("QWERTYUIOP"):
            self.keyBtns.append(Btn(kx + i * (kw + gap), ky, kw, kh, k))
        r2w = 9 * (kw + gap) - gap
        r2x = kx + (r1w - r2w) // 2
        for i, k in enumerate("ASDFGHJKL"):
            self.keyBtns.append(Btn(r2x + i * (kw + gap), ky + kh + gap, kw, kh, k))
        r3w = 7 * (kw + gap) - gap
        r3x = kx + (r1w - r3w) // 2
        for i, k in enumerate("ZXCVBNM"):
            self.keyBtns.append(Btn(r3x + i * (kw + gap), ky + 2 * (kh + gap), kw, kh, k))
        r4y = ky + 3 * (kh + gap)
        spW = r1w // 2
        delW = (r1w - spW - 2 * gap) // 2
        self.keyBtns.append(Btn(kx, r4y, spW, kh, "SPACE"))
        self.keyBtns.append(Btn(kx + spW + gap, r4y, delW, kh, "DEL"))
        self.keyBtns.append(Btn(kx + spW + delW + 2 * gap, r4y, delW, kh, "CLR"))
        self.kbX, self.kbW = kx, r1w

    def render(self, img, fps, mode, colorIdx, brushIdx, fx=-1, fy=-1):
        self.tick += 1
        self._frame(img)
        self._topBar(img, fps, mode)
        self._modes(img, mode, fx, fy)
        self._colors(img, colorIdx, fx, fy)
        if mode != "TYPE":
            self._brushes(img, brushIdx, colorIdx, fx, fy)
        if mode == "TYPE":
            self._keyboard(img, fx, fy)
            self._textBox(img)
        self._notification(img)
        self._watermark(img)

    def _frame(self, img):
        c = (0, 255, 200)
        for x, y, dx, dy in [(2,2,1,1),(self.w-2,2,-1,1),(2,self.h-2,1,-1),(self.w-2,self.h-2,-1,-1)]:
            cv2.line(img, (x, y), (x + 35*dx, y), c, 1, cv2.LINE_AA)
            cv2.line(img, (x, y), (x, y + 35*dy), c, 1, cv2.LINE_AA)

    def _topBar(self, img, fps, mode):
        glass(img, 0, 0, self.w, 34, 0.5, None)
        cv2.line(img, (0, 34), (self.w, 34), (0, 255, 200), 1)
        f = cv2.FONT_HERSHEY_SIMPLEX
        mc = {"DRAW": (0,255,0), "TYPE": (255,200,0), "ERASE": (0,100,255)}.get(mode, (100,100,100))
        cv2.circle(img, (15, 17), 5, mc, cv2.FILLED)
        glow(img, (15, 17), 5, mc, cv2.FILLED, 2)
        cv2.putText(img, mode, (28, 23), f, 0.42, mc, 1, cv2.LINE_AA)
        cv2.putText(img, f"{fps} FPS", (self.w - 70, 23), f, 0.38, (0, 255, 200), 1, cv2.LINE_AA)
        sx = int(self.w * 0.4 + 80 * math.sin(self.tick * 0.04))
        cv2.line(img, (sx - 12, 17), (sx + 12, 17), (0, 255, 200), 1, cv2.LINE_AA)
        cv2.circle(img, (sx, 17), 2, (0, 255, 200), cv2.FILLED)

    def _modes(self, img, mode, fx, fy):
        for btn in self.modeBtns:
            btn.draw(img, active=(btn.label == mode), hover=btn.isOver(fx, fy))
        for btn in self.actionBtns:
            btn.draw(img, hover=btn.isOver(fx, fy))

    def _colors(self, img, colorIdx, fx, fy):
        for i, btn in enumerate(self.colorBtns):
            cx, cy = btn.x + btn.w // 2, btn.y + btn.h // 2
            hover = btn.isOver(fx, fy)
            if i == colorIdx:
                glow(img, (cx, cy), 11, COLORS[i], 2, 3)
                cv2.circle(img, (cx, cy), 8, COLORS[i], cv2.FILLED)
            elif hover:
                cv2.circle(img, (cx, cy), 9, COLORS[i], 2)
                cv2.circle(img, (cx, cy), 6, COLORS[i], cv2.FILLED)
            else:
                cv2.circle(img, (cx, cy), 6, COLORS[i], cv2.FILLED)
                cv2.circle(img, (cx, cy), 7, (30, 30, 30), 1)

    def _brushes(self, img, brushIdx, colorIdx, fx, fy):
        for i, btn in enumerate(self.brushBtns):
            cx, cy = btn.x + btn.w // 2, btn.y + btn.h // 2
            hover = btn.isOver(fx, fy)
            sel = (i == brushIdx)
            bc = COLORS[colorIdx] if sel else (0, 180, 140) if hover else (60, 60, 60)
            glass(img, btn.x, btn.y, btn.w, btn.h, 0.4 if sel else 0.2, bc)
            cv2.circle(img, (cx, cy), BRUSHES[i], COLORS[colorIdx] if sel else (100, 100, 100), cv2.FILLED)

    def _keyboard(self, img, fx, fy):
        for btn in self.keyBtns:
            btn.draw(img, hover=btn.isOver(fx, fy))

    def _textBox(self, img):
        ty = self.h - 175
        glass(img, self.kbX, ty, self.kbW, 28, 0.4, (0, 255, 200))
        txt = self.typedText[-35:] if self.typedText else "pinch on keys to type..."
        clr = (0, 255, 200) if self.typedText else (50, 50, 50)
        cv2.putText(img, txt, (self.kbX + 8, ty + 19), cv2.FONT_HERSHEY_SIMPLEX, 0.4, clr, 1, cv2.LINE_AA)

    def _notification(self, img):
        if self.notifyTimer > 0:
            self.notifyTimer -= 1
            f = cv2.FONT_HERSHEY_SIMPLEX
            tw = cv2.getTextSize(self.notify, f, 0.5, 1)[0][0]
            cx = self.w // 2
            glass(img, cx - tw // 2 - 12, 40, tw + 24, 26, 0.6, (0, 255, 200))
            cv2.putText(img, self.notify, (cx - tw // 2, 59), f, 0.5, (0, 255, 200), 1, cv2.LINE_AA)

    def showNotify(self, text, frames=25):
        self.notify = text
        self.notifyTimer = frames

    def _watermark(self, img):
        f = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "Quantum5hadow", (self.w - 140, self.h - 42), f, 0.3, (0, 80, 65), 1, cv2.LINE_AA)
        cv2.putText(img, "github.com/Quantum5hadow", (self.w - 180, self.h - 30), f, 0.25, (0, 60, 50), 1, cv2.LINE_AA)

    def handFX(self, img, lmList, mode):
        if not lmList:
            self.trail = []
            return
        tipNames = ["THB", "IDX", "MID", "RNG", "PNK"]
        tips = [4, 8, 12, 16, 20]
        for j, tip in enumerate(tips):
            x, y = lmList[tip][1], lmList[tip][2]
            glow(img, (x, y), 5, (0, 255, 200), 1, 2)
            cv2.circle(img, (x, y), 2, (255, 255, 255), cv2.FILLED)
            cv2.putText(img, tipNames[j], (x - 8, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 200, 180), 1, cv2.LINE_AA)
        if len(lmList) > 12:
            cx, cy = lmList[9][1], lmList[9][2]
            r = 42
            a = (self.tick * 3) % 360
            cv2.ellipse(img, (cx, cy), (r, r), 0, a, a + 70, (0, 255, 200), 1, cv2.LINE_AA)
            cv2.ellipse(img, (cx, cy), (r, r), 0, a + 180, a + 250, (0, 255, 200), 1, cv2.LINE_AA)
            cv2.ellipse(img, (cx, cy), (r - 10, r - 10), 0, a + 90, a + 130, (0, 180, 160), 1, cv2.LINE_AA)
            for i in range(4):
                an = math.radians(a + i * 90)
                px, py = int(cx + r * math.cos(an)), int(cy + r * math.sin(an))
                cv2.circle(img, (px, py), 2, (0, 255, 200), cv2.FILLED)
            span = int(((lmList[0][1] - lmList[12][1])**2 + (lmList[0][2] - lmList[12][2])**2)**0.5)
            cv2.putText(img, f"SPAN {span}", (cx - 20, cy + r + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (0, 180, 160), 1, cv2.LINE_AA)
        if mode == "DRAW":
            x, y = lmList[8][1], lmList[8][2]
            self.trail.append((x, y))
            if len(self.trail) > 18:
                self.trail.pop(0)
            for i in range(1, len(self.trail)):
                a = i / len(self.trail)
                cv2.line(img, self.trail[i - 1], self.trail[i], (int(a * 180), 255, int(a * 180)), 2, cv2.LINE_AA)
            glow(img, (x, y), 10, (0, 255, 0), 1, 3)
            s = 16
            cv2.line(img, (x - s, y), (x - 5, y), (0, 255, 0), 1, cv2.LINE_AA)
            cv2.line(img, (x + 5, y), (x + s, y), (0, 255, 0), 1, cv2.LINE_AA)
            cv2.line(img, (x, y - s), (x, y - 5), (0, 255, 0), 1, cv2.LINE_AA)
            cv2.line(img, (x, y + 5), (x, y + s), (0, 255, 0), 1, cv2.LINE_AA)
        elif mode == "ERASE":
            x, y = lmList[8][1], lmList[8][2]
            glow(img, (x, y), 28, (0, 0, 255), 2, 3)
            self.trail = []
        else:
            self.trail = []
