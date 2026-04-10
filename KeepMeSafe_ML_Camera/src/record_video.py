import serial
import struct
import cv2
import numpy as np
import time

PORT     = "/dev/cu.usbmodem1101"
BAUD     = 921600
DURATION = 10       # วินาที
OUTPUT   = "recording.avi"
FPS      = 10

ser = serial.Serial(PORT, BAUD, timeout=5)
time.sleep(2)
ser.reset_input_buffer()
print("Connected!")

# รอ READY
print("Waiting for READY...")
ser.write(b'p\n')
while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if line: print(f">> {line}")
    if "READY" in line:
        print("✅ READY")
        break
    ser.write(b'p\n')

input("กด Enter เพื่อเริ่มอัดวิดีโอ...")

# เริ่ม stream
ser.write(b's\n')
print(f"🎥 Recording {DURATION} sec...")

# เตรียม video writer
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out    = None
frames = 0

start_time = time.time()

while time.time() - start_time < DURATION:
    # อ่าน 4 bytes = frame size
    size_bytes = ser.read(4)
    if len(size_bytes) < 4:
        continue

    frame_size = struct.unpack('<I', size_bytes)[0]

    # ตรวจสอบขนาด reasonable
    if frame_size < 100 or frame_size > 100000:
        ser.reset_input_buffer()
        continue

    # อ่าน JPEG bytes
    jpeg_data = b""
    while len(jpeg_data) < frame_size:
        chunk = ser.read(frame_size - len(jpeg_data))
        jpeg_data += chunk

    # decode JPEG
    arr = np.frombuffer(jpeg_data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        continue

    # flip ถ้าภาพกลับหัว
    img = cv2.flip(img, -1)

    # สร้าง VideoWriter ครั้งแรก
    if out is None:
        h, w = img.shape[:2]
        out = cv2.VideoWriter(OUTPUT, fourcc, FPS, (w, h))
        print(f"Video: {w}x{h}")

    out.write(img)
    frames += 1

    elapsed = time.time() - start_time
    print(f"\r{elapsed:.1f}s  {frames} frames", 
          end="", flush=True)

# หยุด stream
ser.write(b'x\n')

if out:
    out.release()

print(f"\n✅ Saved → {OUTPUT}")
print(f"   {frames} frames  |  {frames/DURATION:.1f} fps")
ser.close()