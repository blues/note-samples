// Copyright 2019 Blues Inc.  All rights reserved.
// Use of this source code is governed by licenses granted by the
// copyright holder including that found in the LICENSE file.

// Device Firmware Update support.  (Note that this is only currently supported on ESP32.)
// As a note to the reader: sometimes firmware update is referred to as "OTA" (Over The Air) or
// "FOTA" (Firmware Over The Air).  Technically, this code is reading the already-downloaded and
// already-verified firmware from the Notecard's storage in a fully-offline manner, which is why
// we use the more generic DFU (Device Firmware Update) term of art.

#include "main.h"
#include <Arduino.h>
#include <Notecard.h>
#include "esp_partition.h"
#include "esp_system.h"
#include "esp_ota_ops.h"
#include "esp_flash_partitions.h"

// The largest chunk a single dfu.get request will return.  Requests for more
// than this are rejected by the Notecard.
#define DFU_CHUNK_LEN 8192

// Whether this DFU had to put the Notecard into DFU mode.  Notecards that hold
// the downloaded image in onboard flash serve it without DFU mode, so we only
// enter (and therefore only need to leave) it when the Notecard asks us to.
static bool dfuModeEntered = false;

// Leave DFU mode, if we entered it.  Prefer "dfu-completed" over "-": it
// resumes whatever sync mode the Notecard was using beforehand, where "-"
// would reset it to the periodic default.
static void dfuExitDFUMode() {
    if (!dfuModeEntered) {
        return;
    }
    if (J *req = notecard.newRequest("hub.set")) {
        JAddStringToObject(req, "mode", "dfu-completed");
        notecard.sendRequest(req);
    }
    dfuModeEntered = false;
}

// Cleanly back out of DFU on any failure: release the ESP OTA handle (if open),
// release the Notecard's binary store, tell the Notecard to clear staged DFU
// state (with an optional error string that surfaces on Notehub), and leave DFU
// mode if we entered it.
static void dfuAbort(esp_ota_handle_t handle, const char *err) {
    if (handle != 0) {
        esp_ota_end(handle);
    }
    NoteBinaryStoreReset();
    if (J *req = notecard.newRequest("dfu.status")) {
        JAddBoolToObject(req, "stop", true);
        if (err != NULL) {
            JAddStringToObject(req, "err", err);
        }
        notecard.sendRequest(req);
    }
    dfuExitDFUMode();
}

// Display DFU partition information
void dfuShowPartitions() {
    const esp_partition_t *partition;

    APP_LOGF("ESP32 PARTITION SCHEME (should be two partitions to support OTA)\n");

    partition = esp_partition_find_first(ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_0, "app0");
    if (partition == NULL)
        APP_LOGF("   partition app0: not found\n");
    else
        APP_LOGF("   partition that should be 'app0' is '%s' at 0x%08lx (%lu bytes)\n", partition->label, (unsigned long)partition->address, (unsigned long)partition->size);

    partition = esp_partition_find_first(ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_1, "app1");
    if (partition == NULL)
        APP_LOGF("   partition app1: not found\n");
    else
        APP_LOGF("   partition that should be 'app1' is '%s' at 0x%08lx (%lu bytes)\n", partition->label, (unsigned long)partition->address, (unsigned long)partition->size);

}

// Process DFU
void dfuPoll(bool force) {
    static uint32_t dfuCheckMs = 0;
    static uint32_t serviceIdleCheckMs = 0;

    // Suppress how often we check
    if (!force && dfuCheckMs != 0 && millis() < dfuCheckMs + ms1Hour)
        return;

    // Even if DFU is ready, only check the notehub status once every 10s max
    if (!force && serviceIdleCheckMs != 0 && millis() < serviceIdleCheckMs + 10*ms1Sec)
        return;
    serviceIdleCheckMs = millis();

    // Check status, and determine both if there is an image ready, and if the image is NEW.
    bool imageIsReady = false;
    bool imageIsSameAsCurrent = false;
    char imageMD5[NOTE_MD5_HASH_STRING_SIZE] = {0};
    uint32_t imageLength = 0;
    if (J *rsp = notecard.requestAndResponse(notecard.newRequest("dfu.status"))) {
        if (strcmp(JGetString(rsp, "mode"), "ready") == 0) {
            imageIsReady = true;
            if (J *body = JGetObjectItem(rsp, "body")) {
                imageLength = JGetInt(body, "length");
                strlcpy(imageMD5, JGetString(body, "md5"), sizeof(imageMD5));
                imageIsSameAsCurrent = strcmp(JGetString(body, "version"), firmwareVersion()) == 0;
                if (!imageIsSameAsCurrent) {
                    APP_LOGF("dfu: replacing current image: %s\n", productVersion());
                    APP_LOGF("dfu:   with downloaded image: %s\n", JGetString(body, "name"));
                }
            }
        }
        notecard.deleteResponse(rsp);
    }

    // Exit if same version or no DFU to process
    if (!imageIsReady || imageIsSameAsCurrent || imageLength == 0) {
        dfuCheckMs = millis();
        APP_LOGF("dfu: no image is ready for firmware update\n");
        return;
    }

    // Prepare the partition that will receive the image BEFORE asking the
    // Notecard for anything.  Erasing a large flash region takes a while, and
    // on a Notecard that needs DFU mode that erase would otherwise run against
    // the Notecard's 15-minute DFU-mode timeout.
    esp_err_t err;
    // update handle : set by esp_ota_begin(), must be freed via esp_ota_end()
    esp_ota_handle_t update_handle = 0 ;
    const esp_partition_t *update_partition = NULL;
    const esp_partition_t *configured = esp_ota_get_boot_partition();
    const esp_partition_t *running = esp_ota_get_running_partition();
    if (configured != running) {
        APP_LOGF("dfu: configured OTA boot partition at offset 0x%08lx, but running from offset 0x%08lx\n",
                (unsigned long)configured->address, (unsigned long)running->address);
        APP_LOGF("     (This can happen if either the OTA boot data or preferred boot image become corrupted.)\n");
    }
    APP_LOGF("dfu: running partition type %d subtype %d (offset 0x%08lx)\n", running->type, running->subtype, (unsigned long)running->address);

    update_partition = esp_ota_get_next_update_partition(NULL);
    if (update_partition == NULL) {  // simply being defensive
        dfuAbort(0, "no OTA partition available");
        return;
    }

    APP_LOGF("dfu: writing to partition subtype %d at offset 0x%lx\n", update_partition->subtype, (unsigned long)update_partition->address);

    // Begin the update
    err = esp_ota_begin(update_partition, OTA_SIZE_UNKNOWN, &update_handle);
    if (err != ESP_OK) {
        APP_LOGF("esp_ota_begin failed (%s)\n", esp_err_to_name(err));
        dfuAbort(0, esp_err_to_name(err));
        return;
    }

    // Proceed with DFU
    dfuCheckMs = millis();
    dfuModeEntered = false;

    // Ask whether the Notecard can serve the image right now.  A zero-length
    // dfu.get checks readiness without transferring anything.  Notecards that
    // hold the downloaded image in onboard flash answer immediately, and can
    // stay connected and syncing for the whole update.
    bool readyToRead = false;
    if (J *rsp = notecard.requestAndResponse(notecard.newRequest("dfu.get"))) {
        readyToRead = !notecard.responseError(rsp);
        if (!readyToRead)
            APP_LOGF("dfu: not ready to read: %s\n", JGetString(rsp, "err"));
        notecard.deleteResponse(rsp);
    }

    // Notecards without onboard flash read the image out of the cellular
    // modem's file system, which they can only do once the network connection
    // is closed.  Entering DFU mode closes it, but the Notecard has to finish
    // whatever it was doing first, so poll rather than assuming a fixed delay.
    // Note that the Notecard leaves DFU mode on its own after 15m, so we don't
    // strand it in a bad state if we fail partway through.
    if (!readyToRead) {
        APP_LOGF("dfu: entering DFU mode\n");
        if (J *req = notecard.newRequest("hub.set")) {
            JAddStringToObject(req, "mode", "dfu");
            notecard.sendRequest(req);
        }
        dfuModeEntered = true;
        uint32_t beganDFUModeCheck = millis();
        while (!readyToRead && millis() < beganDFUModeCheck + (2 * ms1Min)) {
            delay(2500);
            if (J *rsp = notecard.requestAndResponse(notecard.newRequest("dfu.get"))) {
                readyToRead = !notecard.responseError(rsp);
                notecard.deleteResponse(rsp);
            }
        }
        if (!readyToRead) {
            dfuAbort(update_handle, "host failed to enter DFU mode");
            return;
        }
    }

    APP_LOGF("dfu: beginning firmware update\n");

    // Each chunk arrives through the Notecard's binary store rather than as
    // base64 in the response, so clear anything a previous operation left there.
    NoteBinaryStoreReset();

    // One buffer, reused for every chunk.  NoteBinaryStoreReceive() reads the
    // COBS-encoded bytes off the wire and decodes them in place, so the buffer
    // has to be big enough for the *encoded* form of a full chunk, plus the
    // terminating null it writes after the decoded data.
    uint32_t chunkBufLen = NoteBinaryCodecMaxEncodedLength(DFU_CHUNK_LEN) + 1;
    uint8_t *chunkBuf = (uint8_t *) malloc(chunkBufLen);
    if (chunkBuf == NULL) {
        APP_LOGF("dfu: can't allocate %lu-byte chunk buffer\n", (unsigned long)chunkBufLen);
        dfuAbort(update_handle, "out of memory");
        return;
    }

    // Loop over received chunks
    int offset = 0;
    int left = imageLength;
    NoteMD5Context md5Context;
    NoteMD5Init(&md5Context);
    while (left) {

        // Read next chunk from card
        int thislen = DFU_CHUNK_LEN;
        if (left < thislen)
            thislen = left;

        // If anywhere, this is the location of the highest probability of I/O error
        // on the I2C or serial bus, simply because of the amount of data being transferred.
        // As such, it's a conservative measure just to retry.
        bool chunkReceived = false;
        for (int retry=0; retry<5 && !chunkReceived; retry++) {
            APP_LOGF("dfu: reading chunk (offset:%d length:%d try:%d)\n", offset, thislen, retry+1);

            // Ask the Notecard to move this chunk into its binary store.  The
            // response describes what landed there -- decoded "length", encoded
            // "cobs", and an MD5 in "status" -- but carries no payload.
            J *req = notecard.newRequest("dfu.get");
            if (req == NULL) {
                APP_LOGF("dfu: insufficient memory\n");
                free(chunkBuf);
                dfuAbort(update_handle, "out of memory");
                return;
            }
            JAddNumberToObject(req, "offset", offset);
            JAddNumberToObject(req, "length", thislen);
            JAddBoolToObject(req, "binary", true);
            J *rsp = notecard.requestAndResponse(req);
            if (rsp == NULL) {
                APP_LOGF("dfu: insufficient memory\n");
                free(chunkBuf);
                dfuAbort(update_handle, "out of memory");
                return;
            }
            if (notecard.responseError(rsp)) {
                APP_LOGF("dfu: error on read: %s\n", JGetString(rsp, "err"));
                notecard.deleteResponse(rsp);
                continue;
            }

            // A Notecard that predates the binary argument ignores it and
            // answers with a payload instead.  Fail loudly rather than silently
            // reading an empty binary store.
            if (JGetObjectItem(rsp, "cobs") == NULL) {
                APP_LOGF("dfu: this Notecard does not support dfu.get with binary:true (requires firmware v9.1.1 or later)\n");
                notecard.deleteResponse(rsp);
                free(chunkBuf);
                dfuAbort(update_handle, "notecard firmware too old for binary DFU");
                return;
            }
            notecard.deleteResponse(rsp);

            // Pull the chunk out of the binary store.  This issues
            // card.binary.get, COBS-decodes in place, and verifies the chunk
            // against the MD5 the Notecard reported -- the same integrity check
            // the base64 path used to do by hand.
            const char *binErr = NoteBinaryStoreReceive(chunkBuf, chunkBufLen, 0, thislen);
            if (binErr != NULL) {
                APP_LOGF("dfu: error reading binary store: %s\n", binErr);
                continue;
            }

            chunkReceived = true;
        }
        if (!chunkReceived) {
            APP_LOGF("dfu: unrecoverable error on read\n");
            free(chunkBuf);
            dfuAbort(update_handle, "unrecoverable read error");
            return;
        }

        // MD5 the chunk
        NoteMD5Update(&md5Context, chunkBuf, thislen);

        // Write the chunk
        err = esp_ota_write(update_handle, (const void *)chunkBuf, thislen);
        if (err != ESP_OK) {
            free(chunkBuf);
            dfuAbort(update_handle, esp_err_to_name(err));
            return;
        }

        // Move to next chunk
        APP_LOGF("dfu: successfully transferred offset:%d len:%d\n", offset, thislen);
        offset += thislen;
        left -= thislen;
    }

    // The whole image is off the Notecard now.  Hand the binary store back to
    // the rest of the application, and leave DFU mode if we entered it.
    free(chunkBuf);
    NoteBinaryStoreReset();
    dfuExitDFUMode();

    // Done
    if (esp_ota_end(update_handle) != ESP_OK) {
        APP_LOGF("esp_ota_end failed!\n");
        dfuAbort(0, "esp_ota_end failed");
        return;
    }

    // Validate the MD5
    uint8_t md5Hash[NOTE_MD5_HASH_SIZE];
    NoteMD5Final(md5Hash, &md5Context);
    char md5HashString[NOTE_MD5_HASH_STRING_SIZE];
    NoteMD5HashToString(md5Hash, md5HashString, sizeof(md5HashString));
    APP_LOGF("dfu:    MD5 of image: %s\n", imageMD5);
    APP_LOGF("dfu: MD5 of download: %s\n", md5HashString);
    if (strcmp(imageMD5, md5HashString) != 0) {
        APP_LOGF("MD5 MISMATCH - ABANDONING DFU\n");
        dfuAbort(0, "MD5 mismatch");
        return;
    }

    // Set the boot partition and reboot
    err = esp_ota_set_boot_partition(update_partition);
    if (err != ESP_OK) {
        APP_LOGF("dfu: restart failure\n");
        dfuAbort(0, esp_err_to_name(err));
        return;
    }

    // Clear out the DFU image
    if (J *req = notecard.newRequest("dfu.status")) {
        JAddBoolToObject(req, "stop", true);
        notecard.sendRequest(req);
    }

    // Restart
    APP_LOGF("dfu: restart system\n");
    esp_restart();
}
