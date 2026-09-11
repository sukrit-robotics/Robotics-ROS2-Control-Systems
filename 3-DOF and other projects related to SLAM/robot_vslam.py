import cv2
import serial
import time
import numpy as np

# 1. ESP32 कनेक्शन सेटअप (COM3)
try:
    esp32 = serial.Serial(port='COM3', baudrate=115200, timeout=0.1)
    print("ESP32 Connected on COM3!")
    time.sleep(2)
except Exception as e:
    print(f"ESP32 Connection Error: {e}")
    esp32 = None

# 2. कैमरा और फीचर डिटेक्टर (ORB) चालू करें
cap = cv2.VideoCapture(0)
time.sleep(2)
orb = cv2.ORB_create(nfeatures=500)

# मैप के लिए एक खाली ब्लैक इमेज (800x800 पिक्सल) बनाएं
map_canvas = np.zeros((800, 800, 3), dtype=np.uint8)
robot_x, robot_y = 400, 400 # मैप के केंद्र (Center) से शुरुआत

print("\nControls: 'f' = Forward, 's' = Stop, 'q' = Quit")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    
    # कैमरे के लाइव व्यू पर हरे डॉट्स दिखाएं
    frame_features = cv2.drawKeypoints(frame, keypoints, None, color=(0, 255, 0), flags=0)
    
    # --- बेसिक 2D पॉइंट मैप जनरेशन लॉजिक ---
    if len(keypoints) > 0:
        for kp in keypoints[:50]: # पहले 50 मुख्य पॉइंट्स को मैप पर डालेंगे
            # कैमरे के x, y को मैप के स्केल में बदल रहे हैं
            pt_x = int(kp.pt[0] * 0.5) + (robot_x - 160)
            pt_y = int(kp.pt[1] * 0.5) + (robot_y - 120)
            if 0 <= pt_x < 800 and 0 <= pt_y < 800:
                cv2.circle(map_canvas, (pt_x, pt_y), 1, (0, 255, 255), -1) # पीले डॉट्स = मैप पॉइंट्स

    # मैप पर रोबोट की करंट पोजीशन (लाल डॉट)
    cv2.circle(map_canvas, (robot_x, robot_y), 5, (0, 0, 255), -1)
    
    # दोनों विंडोज़ को एक साथ स्क्रीन पर दिखाएं
    cv2.imshow('1. Camera Feature Tracking', frame_features)
    cv2.imshow('2. 2D Point Map (Visual SLAM)', map_canvas)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('f'):
        if esp32: esp32.write(b'F')
        robot_y -= 5 # रोबोट आगे बढ़ेगा तो मैप पर डॉट ऊपर जाएगा
    elif key == ord('s'):
        if esp32: esp32.write(b'S')
    elif key == ord('q'):
        if esp32: esp32.write(b'S')
        break

if esp32: esp32.close()
cap.release()
cv2.destroyAllWindows()
