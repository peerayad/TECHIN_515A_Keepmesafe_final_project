//paste in main.cpp
#include <Arduino.h>
#include <I2S.h>

#define SAMPLE_RATE   16000
#define SAMPLE_BITS   16
#define RECORD_SEC    3
#define VOLUME_GAIN   2
#define RECORD_SIZE   (SAMPLE_RATE * SAMPLE_BITS / 8 * RECORD_SEC)

bool recording = false;

void setup() {
  Serial.begin(115200);
  delay(3000);

  // ── official Seeed pin config ─────────────────────
  I2S.setAllPins(-1, 42, 41, -1, -1);
  if (!I2S.begin(PDM_MONO_MODE, SAMPLE_RATE, SAMPLE_BITS)) {
    Serial.println("ERR:I2S");
    while (1);
  }

  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'p') Serial.println("READY");
    if (cmd == 'r' && !recording) {
      recording = true;

      // ── ใช้ PSRAM malloc ──────────────────────────
      uint8_t *rec_buffer = (uint8_t *)ps_malloc(RECORD_SIZE);
      if (rec_buffer == NULL) {
        Serial.println("ERR:PSRAM");
        recording = false;
        return;
      }

      Serial.println("START");

      // ── อ่านเสียงทีเดียว ──────────────────────────
      size_t sample_size = 0;
      esp_i2s::i2s_read(esp_i2s::I2S_NUM_0,
                        rec_buffer,
                        RECORD_SIZE,
                        &sample_size,
                        portMAX_DELAY);

      // ── เพิ่ม volume ──────────────────────────────
      for (uint32_t i = 0; i < sample_size; i += 2) {
        (*(uint16_t *)(rec_buffer + i)) <<= VOLUME_GAIN;
      }

      // ── ส่งข้อมูล ─────────────────────────────────
      Serial.write(rec_buffer, sample_size);

      free(rec_buffer);
      recording = false;
    }
  }
}