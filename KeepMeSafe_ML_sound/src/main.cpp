#include <Arduino.h>
#include <ML_sound_detection_Threat_non_threat__inferencing.h>
#include "driver/i2s.h"
#include "esp_camera.h"

// ── Camera config ──
camera_config_t camera_config = {
  .pin_pwdn     = -1,  .pin_reset    = -1,
  .pin_xclk     = 10,  .pin_sscb_sda = 40,
  .pin_sscb_scl = 39,
  .pin_d7=48, .pin_d6=11, .pin_d5=12, .pin_d4=14,
  .pin_d3=16, .pin_d2=18, .pin_d1=17, .pin_d0=15,
  .pin_vsync=38, .pin_href=47, .pin_pclk=13,
  .xclk_freq_hz = 20000000,
  .ledc_timer   = LEDC_TIMER_0,
  .ledc_channel = LEDC_CHANNEL_0,
  .pixel_format = PIXFORMAT_JPEG,
  .frame_size   = FRAMESIZE_VGA,
  .jpeg_quality = 12,
  .fb_count     = 2,
  .fb_location  = CAMERA_FB_IN_PSRAM,
  .grab_mode    = CAMERA_GRAB_LATEST
};

// ── Global buffers ──
static int16_t raw[EI_CLASSIFIER_RAW_SAMPLE_COUNT];
static float   features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];
int photoCount  = 0;
int windowCount = 0;

// ── Base64 encoder ──
static const char b64chars[] =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

void sendBase64(const uint8_t *data, size_t len) {
  for (size_t i = 0; i < len; i += 3) {
    uint8_t b0 = data[i];
    uint8_t b1 = (i+1 < len) ? data[i+1] : 0;
    uint8_t b2 = (i+2 < len) ? data[i+2] : 0;

    Serial.print(b64chars[b0 >> 2]);
    Serial.print(b64chars[((b0 & 0x3) << 4) | (b1 >> 4)]);
    Serial.print((i+1 < len) ? b64chars[((b1 & 0xf) << 2) | (b2 >> 6)] : '=');
    Serial.print((i+2 < len) ? b64chars[b2 & 0x3f] : '=');
  }
}

void setup_i2s() {
  i2s_config_t cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER|I2S_MODE_RX|I2S_MODE_PDM),
    .sample_rate          = 16000,
    .bits_per_sample      = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_PCM_SHORT,
    .intr_alloc_flags     = 0,
    .dma_buf_count        = 8,
    .dma_buf_len          = 512,
    .use_apll             = false,
  };
  i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL);

  i2s_pin_config_t pins = {
    .mck_io_num   = I2S_PIN_NO_CHANGE,
    .bck_io_num   = I2S_PIN_NO_CHANGE,
    .ws_io_num    = 42,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num  = 41,
  };
  i2s_set_pin(I2S_NUM_0, &pins);
}

void captureAndSend() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("CAM_FAIL");
    return;
  }

  photoCount++;
  // ส่ง marker + Base64
  Serial.printf("##IMG_START:%d##\n", photoCount);
  sendBase64(fb->buf, fb->len);
  Serial.printf("\n##IMG_END:%d##\n", photoCount);

  esp_camera_fb_return(fb);
}

void setup() {
  Serial.begin(921600);
  delay(1000);

  Serial.println("================================");
  Serial.println("   KeepMeSafe - Booting...      ");
  Serial.println("================================");

  Serial.print("🎥 Camera... ");
  if (esp_camera_init(&camera_config) == ESP_OK)
    Serial.println("OK ✅");
  else
    Serial.println("FAILED ❌");

  Serial.print("🎤 Mic... ");
  setup_i2s();
  Serial.println("OK ✅");

  Serial.println("================================");
  Serial.println("   Listening...                 ");
  Serial.println("================================\n");
}

void loop() {
  windowCount++;

  size_t bytes_read = 0;
  i2s_read(I2S_NUM_0, raw, sizeof(raw),
           &bytes_read, portMAX_DELAY);

  for (int i = 0; i < EI_CLASSIFIER_RAW_SAMPLE_COUNT; i++)
    features[i] = (float)raw[i] / 32768.0f;

  signal_t signal;
  numpy::signal_from_buffer(
    features, EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, &signal);

  ei_impulse_result_t result;
  EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
  if (err != EI_IMPULSE_OK) return;

  float threat = result.classification[0].value;
  float normal = result.classification[1].value;

  int tBar = (int)(threat * 20);
  int nBar = (int)(normal * 20);

  Serial.printf("[#%d] ", windowCount);
  Serial.print("T:[");
  for (int i=0; i<20; i++) Serial.print(i<tBar?"█":"-");
  Serial.printf("] %.1f%% ", threat*100);
  Serial.print("N:[");
  for (int i=0; i<20; i++) Serial.print(i<nBar?"█":"-");
  Serial.printf("] %.1f%%\n", normal*100);

  if (threat > 0.80) {
    Serial.println("🚨 THREAT! Capturing...");
    captureAndSend();
  } else if (threat > 0.50) {
    Serial.println("⚡ SUSPICIOUS");
  } else {
    Serial.println("✅ NORMAL");
  }
}