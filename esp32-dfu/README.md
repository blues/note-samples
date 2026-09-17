# esp32-dfu

Arduino/ESP32 sketch demonstrating Notecard-orchestrated host firmware updates (DFU)
using the Notecard's IAP (In-Application Programming) flow. The Notecard downloads
the firmware image from Notehub, then this sketch reads it chunk-by-chunk via
`dfu.get`, writes it to the inactive OTA partition, validates MD5, sets the boot
partition, and reboots.

Chunks move through the Notecard's binary store rather than as base64 in the
response, which avoids the ~33% encoding overhead and is substantially faster —
the difference is most noticeable over I2C or a low-baud serial connection.

## Hardware

- An ESP32-based host (e.g. Adafruit HUZZAH32 Feather)
- A Blues Notecard on a Notecarrier F (or similar), running Notecard firmware
  **v9.1.1 or later** (`dfu.get` gained its `binary` argument in that release —
  check with `card.version`)
- A push button on `buttonPin` (default GPIO 21) — single press logs a simulated
  sensor reading, double press forces a DFU poll and `hub.sync`

The sketch defaults to I2C for the Notecard. To use serial instead, uncomment
`#define serialNotecard Serial1` near the top of [esp32-dfu.ino](esp32-dfu.ino).

## Setup

1. Claim a [ProductUID](https://dev.blues.io/notehub/notehub-walkthrough/#finding-a-productuid)
   in Notehub and hardcode `#define PRODUCT_UID "..."` in the sketch.
2. Open `esp32-dfu/esp32-dfu.ino` in the Arduino IDE (the sketch filename must
   match the directory name).
3. Install the **Blues Wireless Notecard** library (**v1.5.0 or later**, which is
   where the `NoteBinaryStore*` helpers landed) via the Arduino Library Manager
   or `arduino-cli lib install "Blues Wireless Notecard"`.
4. Select an ESP32 board with an OTA-capable partition scheme.
5. Compile and upload.

## How DFU Works in This Sketch

- `setup()` reports the current firmware version to Notehub via `dfu.status`.
- `loop()` calls `dfuPoll(false)` periodically (rate-limited to once per hour
  unless forced via a double button press).
- When `dfu.status` reports `mode:"ready"` with a newer image, the sketch:
  1. Opens the inactive OTA partition with `esp_ota_begin`. This happens *first*,
     because erasing a large partition is slow and would otherwise burn into the
     Notecard's 15-minute DFU-mode timeout.
  2. Issues a zero-length `dfu.get` to ask whether the Notecard can serve the
     image right now. Notecards that hold the downloaded image in onboard flash
     answer immediately and stay connected and syncing for the whole update.
  3. Only if that fails with `not currently in the DFU operating mode`: sets
     `hub.set, mode:"dfu"` and waits up to two minutes for DFU mode to engage.
  4. Clears the binary store, then for each 8 KB chunk issues
     `dfu.get, binary:true` — which parks the chunk in the binary store instead
     of the response — and reads it back with `NoteBinaryStoreReceive()`, which
     COBS-decodes it and verifies the Notecard's MD5. Each chunk goes straight
     to `esp_ota_write`.
  5. On success: releases the binary store, leaves DFU mode if it entered it
     (`hub.set, mode:"dfu-completed"`), validates the full-image MD5, sets the
     boot partition, clears DFU state (`dfu.status, stop:true`), and reboots.
  6. On any failure: cleanly releases the OTA handle and the binary store,
     reports the error to Notehub via `dfu.status, stop:true, err:"..."`, and
     leaves DFU mode if it entered it.

The binary store is a single shared resource. If your own application uses it
for `web.post` uploads or `note.add` payloads, make sure those have finished
before a DFU starts.

## Files

- [esp32-dfu.ino](esp32-dfu.ino) — sketch entry point: setup, loop, button handling, version reporting.
- [dfu.cpp](dfu.cpp) — DFU state machine: partition discovery, chunked `dfu.get` through the binary store, OTA write, MD5 validation.
- [main.h](main.h) — shared declarations.
