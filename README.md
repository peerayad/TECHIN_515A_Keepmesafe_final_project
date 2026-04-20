# KeepMeSafe

**TECHIN 515A — final project**  
**Team 9** · **Register / ownership:** Bie Ku

KeepMeSafe is a **portable, self-contained, battery-powered** security device that monitors a **hotel room** for intrusion and emergencies. On alert it triggers a **local LED strobe and siren**—**no internet and no phone** required.

---

## Who it is for

**Solo and business travellers** who want passive, reliable room security **without** depending on hotel Wi‑Fi or a smartphone nearby.

---

## System boundary

| Layer | Description |
|--------|-------------|
| **Hardware** | XIAO Seed **ESP32-S3** (MCU + on-chip AI), **OV2640** 2 MP camera, **I²S MEMS** microphone, **MicroSD** module (32 GB), **WS2812** RGB LED, **piezo siren** (~90 dB), **TP4056** charger + **3.7 V LiPo**, custom PCB |
| **Software** | **Edge Impulse** ML models (audio classifier + image motion detector), **Arduino / ESP-IDF** firmware with **Away / Sleep** mode state machine. **No cloud. No app.** |
| **Data** | **On-device only:** PCM audio frames, JPEG snapshots (saved to 32 GB MicroSD), ML inference results, GPIO alarm output. **Nothing leaves the device.** The SD card stores event footage for review when the traveller returns. |

---

## Functional architecture

The system architecture is documented as a **functional architecture diagram** in the project register (see course submission / design package).

---

## Risk-reduction prototypes

Early work is split into three prototypes, each with a person in charge (PIC).

### Prototype 1 — Person detection (camera)

| | |
|--|--|
| **PIC** | Yan |
| **Assumption** | OV2640 + ESP32-S3 can classify whether a **moving object** in the room is a **person** vs **non-threat** (shadow, light, object) at **≥ 85%** accuracy in **typical hotel-room lighting**. |
| **Inputs** | OV2640 in hotel room. Dataset: **30+** images “person” vs **30+** “non-person”; **three** lighting levels: bright, dim, dark. |
| **Process** | Train **MobileNet-lite** on Edge Impulse; deploy to ESP32-S3; test with real person (walk, wave), shadows, light changes. |
| **Outputs** | Accuracy **≥ 85%**; inference under **500 ms**; false positive rate under **10%**; pass/fail **per lighting condition**. |

### Prototype 2 — Threat sound classification

| | |
|--|--|
| **PIC** | Proud |
| **Assumption** | MEMS microphone + ESP32-S3 can separate **Threat** sounds (loud knock, glass-break, impact) from **Normal** sounds (TV, talking, walking) at **≥ 85%** accuracy with **false alarm rate under 15%**. |
| **Inputs** | Audio dataset: **20+** clips per class at **16 kHz**. Threat: loud knock, glass-break, impact. Normal: TV, speech, walking, silence. |
| **Process** | **MFCC** features in Edge Impulse; train **2-class NN** (Threat / Normal); deploy to ESP32-S3; test in a real room. |
| **Outputs** | Accuracy **≥ 85%**; inference under **200 ms**; false alarm under **15%** (TV/speech must **not** trigger); confusion matrix. |

### Prototype 3 — Enclosure fit and alignment

| | |
|--|--|
| **PIC** | Mary |
| **Assumption** | A **3D-printed enclosure** can align all openings (camera lens, mic hole, LED diffuser, Mode button, Cancel button, SD slot, USB-C) with the PCB after assembly. |
| **Inputs** | Finalized PCB with camera, mic, LED, USB-C, SD slot, Mode and Cancel buttons. |
| **Process** | Measure component positions; model in **Fusion 360**; print draft enclosure; insert PCB and check every opening. |
| **Outputs** | All openings pass alignment; offset under **1 mm** per point; Cancel button reachable in the dark; revise print if needed. |

---

## Timeline

Planned milestones for the quarter (align with your course calendar as needed).

| Week | Milestone |
|------|-----------|
| **1** | BOM and schematic locked; ESP32-S3 + camera + mic breadboard bring-up; Edge Impulse projects created for image and audio |
| **2** | Collect starter datasets (person / non-person; threat / normal); begin **Prototype 1** (Yan) and **Prototype 2** (Proud) training iterations |
| **3** | Deploy image model to device; measure latency vs **500 ms** target; tune lighting robustness (bright / dim / dark) |
| **4** | Deploy audio model to device; MFCC pipeline stable; measure latency vs **200 ms** target; refine false-alarm rate vs TV / speech |
| **5** | **Prototype 3** (Mary): PCB measurements → Fusion 360 enclosure v1; first print and alignment check |
| **6** | Integrate both ML paths in firmware; define **Away / Sleep** state machine; local alarm path (WS2812 + siren) end-to-end |
| **7** | MicroSD logging: JPEG snapshots + metadata on events; verify “nothing leaves device” data boundary |
| **8** | Custom PCB assembly (if applicable); power path (TP4056 + LiPo) and runtime / standby budget |
| **9** | Enclosure revision if needed; full-room system tests; hit or document prototype pass/fail criteria |
| **10** | Demo rehearsal; final report; repo and handoff documentation |

---

## Repository status

This repository holds the **KeepMeSafe** course final project. Firmware, models, and hardware notes will be added here as the build progresses.
