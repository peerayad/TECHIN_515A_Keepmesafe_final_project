import serial
import cv2
import numpy as np

PORT = "/dev/cu.usbmodem1101"
BAUD = 921600

ser = serial.Serial(PORT, BAUD, timeout=5)
print("Connected! Press Q to quit")

while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()

    if line.startswith("IMG:"):
        size = int(line.split(":")[1])
        data = ser.read(size)
        ser.readline()

        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img is not None:
            img = cv2.flip(img, -1)
            img = cv2.GaussianBlur(img, (3, 3), 0)
            kernel = np.array([[0, -1,  0],
                               [-1,  5, -1],
                               [0, -1,  0]])
            img = cv2.filter2D(img, -1, kernel)
            img = cv2.convertScaleAbs(img, alpha=1.2, beta=10)
            img = cv2.resize(img, (960, 720),
                             interpolation=cv2.INTER_CUBIC)
            cv2.imshow("GuardianPod Camera", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

ser.close()
cv2.destroyAllWindows()