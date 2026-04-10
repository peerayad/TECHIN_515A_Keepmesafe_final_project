import serial
import wave
import time

PORT        = "/dev/cu.usbmodem1101"
BAUD        = 115200
SAMPLE_RATE = 16000
RECORD_SEC  = 3
TOTAL_BYTES = SAMPLE_RATE * RECORD_SEC * 2
OUTPUT      = "recording.wav"

ser = serial.Serial(PORT, BAUD, timeout=15)
time.sleep(2)
ser.reset_input_buffer()
print("Connected!")

print("Waiting for READY...")
ser.write(b'p\n')
while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if line: print(f">> {line}")
    if "READY" in line:
        print("✅ READY")
        break
    ser.write(b'p\n')

input("กด Enter เพื่อเริ่มอัด...")
ser.write(b'r\n')

while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if "START" in line:
        print(f"🎙️ Recording {RECORD_SEC} sec...")
        break
    if "ERR" in line:
        print(f"❌ Error: {line}")
        ser.close()
        exit()

audio_data = bytearray()
while len(audio_data) < TOTAL_BYTES:
    chunk = ser.read(min(256, TOTAL_BYTES - len(audio_data)))
    if chunk:
        audio_data.extend(chunk)
        pct = len(audio_data) / TOTAL_BYTES * 100
        print(f"\r{pct:.1f}%  {len(audio_data)}/{TOTAL_BYTES}",
              end="", flush=True)

print("\n✅ Done!")

with wave.open(OUTPUT, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(bytes(audio_data))

print(f"✅ Saved → {OUTPUT}")
ser.close()