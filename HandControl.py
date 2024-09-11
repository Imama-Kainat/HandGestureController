import cv2
import time
import numpy as np
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc  # For controlling brightness
import pyautogui  # For mouse control
import tkinter as tk  # For graphical user interface

# Set up the screen resolution and camera settings
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

# Initialize the hand detector with a higher detection confidence
detector = htm.HandDetector(detectionCon=0.7)

# Audio control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol = volRange[0]  # Minimum volume
maxVol = volRange[1]  # Maximum volume
volBar = 400
volPer = 0
vol = 0
pTime = 0

# Initialize brightness control
minBrightness, maxBrightness = 0, 100  # Brightness range from 0% to 100%
brightnessPer = sbc.get_brightness()

# Initialize GUI
root = tk.Tk()
root.geometry("300x300")
root.title("Hand Gesture Controller")

volume_label = tk.Label(root, text="Volume Control", font=("Helvetica", 12))
volume_label.pack()

brightness_label = tk.Label(root, text="Brightness Control", font=("Helvetica", 12))
brightness_label.pack()

mouse_label = tk.Label(root, text="Mouse Control", font=("Helvetica", 12))
mouse_label.pack()

media_label = tk.Label(root, text="Media Control", font=("Helvetica", 12))
media_label.pack()

def update_gui(vol_per, brightness_per):
    volume_label.config(text=f"Volume: {vol_per}%")
    brightness_label.config(text=f"Brightness: {brightness_per}%")
    root.update_idletasks()

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    if len(lmList) != 0:
        # Get the x, y coordinates of the thumb and index finger
        x1, y1 = lmList[4][1], lmList[4][2]  # Thumb tip
        x2, y2 = lmList[8][1], lmList[8][2]  # Index finger tip
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        # Calculate the distance between thumb and index finger
        length, img, _ = detector.findDistance(4, 8, img)

        # Volume Control: Adjust volume based on the distance between thumb and index finger
        volBar = np.interp(length, [30, 250], [400, 150])
        volPer = np.interp(length, [30, 250], [0, 100])
        volume.SetMasterVolumeLevelScalar(volPer / 100, None)

        # Brightness Control: Adjust brightness using the distance between thumb and pinky finger
        brightnessLength, img, _ = detector.findDistance(4, 20, img)  # Distance between thumb and pinky
        brightnessPer = np.interp(brightnessLength, [30, 250], [0, 100])
        sbc.set_brightness(int(brightnessPer))  # Set brightness

        # Mouse Control: Move cursor using the hand gesture (based on thumb and index finger midpoint)
        if length < 40:  # Small distance indicates a 'pinch' gesture for mouse control
            screenWidth, screenHeight = pyautogui.size()
            fingerX = np.interp(x1, [0, wCam], [0, screenWidth])
            fingerY = np.interp(y1, [0, hCam], [0, screenHeight])
            pyautogui.moveTo(fingerX, fingerY)

        # Mouse Click: If thumb and middle finger are close, perform a mouse click
        clickLength, img, _ = detector.findDistance(4, 12, img)
        if clickLength < 40:
            pyautogui.click()

        # Media Control: Use gesture for play/pause and next track
        if length < 30:  # If fingers are close together, it can be a play/pause gesture
            pyautogui.press('playpause')  # Simulate play/pause key
        elif length > 100:  # If fingers are far apart, it can be a next track gesture
            pyautogui.press('nexttrack')  # Simulate next track key

        # Keyboard Shortcuts: Detecting gestures for copy/paste
        if lmList[8][1] < lmList[12][1]:  # Index finger is on the left of middle finger for copy
            pyautogui.hotkey('ctrl', 'c')  # Simulate Ctrl+C
        if lmList[8][1] > lmList[12][1]:  # Index finger is on the right of middle finger for paste
            pyautogui.hotkey('ctrl', 'v')  # Simulate Ctrl+V

        # Zoom Control: Zoom in/out using distance between index and middle fingers
        zoomLength, img, _ = detector.findDistance(8, 12, img)  # Distance between index and middle fingers
        if zoomLength < 30:  # If fingers are close together, zoom in
            pyautogui.hotkey('ctrl', '+')  # Simulate Ctrl++
        elif zoomLength > 100:  # If fingers are far apart, zoom out
            pyautogui.hotkey('ctrl', '-')  # Simulate Ctrl+-

        # Draw Volume Bar
        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'Vol: {int(volPer)}%', (40, 450), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

        # Update GUI
        update_gui(int(volPer), int(brightnessPer))

    # Frame rate display
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f"FPS: {int(fps)}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

    cv2.imshow("Image", img)
    root.update()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
root.quit()
