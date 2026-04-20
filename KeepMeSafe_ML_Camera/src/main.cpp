#include "Arduino.h"
#include "esp_camera.h"

// ── XIAO ESP32S3 Sense Camera Pins ──────────────────
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     10
#define SIOD_GPIO_NUM     40
#define SIOC_GPIO_NUM     39

#define Y9_GPIO_NUM       48
#define Y8_GPIO_NUM       11
#define Y7_GPIO_NUM       12
#define Y6_GPIO_NUM       14
#define Y5_GPIO_NUM       16
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       17
#define Y2_GPIO_NUM       15

#define VSYNC_GPIO_NUM    38
#define HREF_GPIO_NUM     47
#define PCLK_GPIO_NUM     13
// ────────────────────────────────────────────────────

bool streaming = false;

// ── Camera Init ──────────────────────────────────────
bool initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.grab_mode    = CAMERA_GRAB_LATEST;
    config.frame_size   = FRAMESIZE_VGA;
    config.jpeg_quality = 8;
    config.fb_count     = 2;
    config.fb_location  = CAMERA_FB_IN_PSRAM;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed: 0x%x\n", err);
        return false;
    }

    // ── Sensor Fine-Tuning ───────────────────────────
    sensor_t *s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_quality(s, 8);
        s->set_framesize(s, FRAMESIZE_VGA);

        // Auto exposure
        s->set_exposure_ctrl(s, 1);
        s->set_aec2(s, 1);
        s->set_ae_level(s, 0);

        // Auto white balance
        s->set_whitebal(s, 1);
        s->set_awb_gain(s, 1);
        s->set_wb_mode(s, 0);           // 0=auto, 1=sunny, 2=cloudy, 3=office, 4=home

        // Image quality
        s->set_sharpness(s, 1);         // -2 to 2
        s->set_contrast(s, 1);          // -2 to 2
        s->set_brightness(s, 0);        // -2 to 2
        s->set_saturation(s, 0);        // -2 to 2
        s->set_denoise(s, 1);

        // Disable effects
        s->set_special_effect(s, 0);    // 0=no effect
        s->set_colorbar(s, 0);          // disable test pattern
    }
    // ─────────────────────────────────────────────────

    return true;
}

// ── Send One Frame Over Serial ───────────────────────
void sendFrame() {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("ERR:FB");
        return;
    }

    // Send 4-byte little-endian frame size
    uint32_t size = fb->len;
    Serial.write((uint8_t *)&size, 4);

    // Send raw JPEG bytes
    Serial.write(fb->buf, fb->len);

    esp_camera_fb_return(fb);
}

// ── Setup ────────────────────────────────────────────
void setup() {
    Serial.begin(921600);
    delay(500);

    Serial.println("Initializing camera...");

    if (!initCamera()) {
        Serial.println("ERR:CAMERA_INIT_FAILED");
        while (true) delay(1000);   // halt
    }

    Serial.println("READY");
}

// ── Loop ─────────────────────────────────────────────
void loop() {
    // Handle serial commands
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        if (cmd == "s") {
            streaming = true;
            Serial.println("STREAMING");

        } else if (cmd == "x") {
            streaming = false;
            Serial.println("STOPPED");

        } else if (cmd == "p") {
            // Ping — Python uses this to wait for READY
            Serial.println("READY");

        } else if (cmd == "q") {
            // Dynamically change quality at runtime
            // Usage: send "q:5" to set quality to 5
            // (handled below)

        } else if (cmd.startsWith("q:")) {
            int q = cmd.substring(2).toInt();
            if (q >= 4 && q <= 63) {
                sensor_t *s = esp_camera_sensor_get();
                if (s) s->set_quality(s, q);
                Serial.printf("Quality set to %d\n", q);
            }

        } else if (cmd.startsWith("r:")) {
            // Dynamically change resolution
            // Usage: "r:vga" / "r:svga" / "r:qvga"
            sensor_t *s = esp_camera_sensor_get();
            if (s) {
                if      (cmd == "r:qvga") s->set_framesize(s, FRAMESIZE_QVGA);
                else if (cmd == "r:vga")  s->set_framesize(s, FRAMESIZE_VGA);
                else if (cmd == "r:svga") s->set_framesize(s, FRAMESIZE_SVGA);
                else if (cmd == "r:xga")  s->set_framesize(s, FRAMESIZE_XGA);
                Serial.println("Resolution updated");
            }
        }
    }

    // Stream frames
    if (streaming) {
        sendFrame();
    }
}