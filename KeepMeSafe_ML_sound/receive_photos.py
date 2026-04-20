import serial
import os
import time
import base64

PORT     = "/dev/cu.usbmodem1101"
BAUD     = 921600
SAVE_DIR = "/Users/supreme/Documents/PlatformIO/Projects/KeepMeSafe_ML_sound/photos"

os.makedirs(SAVE_DIR, exist_ok=True)

def connect():
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print(f"✅ Connected to {PORT}")
            return ser
        except Exception as e:
            print(f"⏳ Waiting... {e}")
            time.sleep(2)

print("KeepMeSafe Photo Receiver")
print("=" * 40)

ser        = connect()
b64_buffer = ""
capturing  = False
photo_num  = 0

while True:
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue

        if "##IMG_START:" in line:
            photo_num  = int(line.split("##IMG_START:")[1].split("##")[0])
            b64_buffer = ""
            capturing  = True
            print(f"📥 Receiving photo #{photo_num}...")

        elif "##IMG_END:" in line and capturing:
            # decode Base64 → JPEG
            try:
                jpeg_data = base64.b64decode(b64_buffer)
                filename  = f"{SAVE_DIR}/photo_{photo_num:03d}.jpg"
                with open(filename, "wb") as f:
                    f.write(jpeg_data)
                print(f"✅ Saved: {filename} ({len(jpeg_data)} bytes)")
            except Exception as e:
                print(f"❌ Decode error: {e}")
            capturing  = False
            b64_buffer = ""

        elif capturing:
            # สะสม Base64 string
            b64_buffer += line

        else:
            print(line)

    except serial.SerialException:
        print("⚠️  Disconnected — reconnecting...")
        try: ser.close()
        except: pass
        time.sleep(2)
        ser = connect()

    except KeyboardInterrupt:
        print("\nStopped.")
        ser.close()
        break