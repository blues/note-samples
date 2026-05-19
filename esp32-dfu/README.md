# esp32-dfu

Arduino/ESP32 sketch demonstrating Notecard-orchestrated host firmware updates (DFU)
using the Notecard's IAP (In-Application Programming) flow. The Notecard downloads
the firmware image from Notehub, then this sketch reads it chunk-by-chunk via
`dfu.get`, writes it to the inactive OTA partition, validates MD5, sets the boot
partition, and reboots.

## Hardware

- An ESP32-based host (e.g. Adafruit HUZZAH32 Feather)
- A Blues Notecard on a Notecarrier F (or similar)
- A push button on `buttonPin` (default GPIO 21) — single press logs a simulated
  sensor reading, double press forces a DFU poll and `hub.sync`

The sketch defaults to I2C for the Notecard. To use serial instead, uncomment
`#define serialNotecard Serial1` near the top of [esp32-dfu.ino](esp32-dfu.ino).

## Setup

1. Claim a [ProductUID](https://dev.blues.io/notehub/notehub-walkthrough/#finding-a-productuid)
   in Notehub and hardcode `#define PRODUCT_UID "..."` in the sketch.
2. Open `esp32-dfu/esp32-dfu.ino` in the Arduino IDE (the sketch filename must
   match the directory name).
3. Install the **Blues Wireless Notecard** library via the Arduino Library Manager
   or `arduino-cli lib install "Blues Wireless Notecard"`.
4. Select an ESP32 board with an OTA-capable partition scheme.
5. Compile and upload.

## How DFU Works in This Sketch

- `setup()` reports the current firmware version to Notehub via `dfu.status`.
- `loop()` calls `dfuPoll(false)` periodically (rate-limited to once per hour
  unless forced via a double button press).
- When `dfu.status` reports `mode:"ready"` with a newer image, the sketch:
  1. Sets `hub.set, mode:"dfu"` to put the Notecard in DFU mode.
  2. Waits up to two minutes for DFU mode to actually engage (verified via
     `dfu.get`).
  3. Begins an `esp_ota_begin`/`esp_ota_write` sequence, reading 4 KB chunks
     via `dfu.get` and verifying each chunk's MD5.
  4. On success: reverts hub mode (`hub.set, mode:"-"`), validates the full-image
     MD5, sets the boot partition, clears DFU state (`dfu.status, stop:true`),
     and reboots.
  5. On any failure: cleanly releases the OTA handle, reports the error to
     Notehub via `dfu.status, stop:true, err:"..."`, and reverts hub mode.

## Files

- [esp32-dfu.ino](esp32-dfu.ino) — sketch entry point: setup, loop, button handling, version reporting.
- [dfu.cpp](dfu.cpp) — DFU state machine: partition discovery, chunked `dfu.get`, OTA write, MD5 validation.
- [main.h](main.h) — shared declarations.
