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

// Cleanly back out of DFU on any failure: release the ESP OTA handle (if open),
// tell the Notecard to clear staged DFU state (with an optional error string
// that surfaces on Notehub), and revert hub mode to whatever it was before DFU.
static void dfuAbort(esp_ota_handle_t handle, const char *err) {
    if (handle != 0) {
        esp_ota_end(handle);
    }
    if (J *req = notecard.newRequest("dfu.status")) {
        JAddBoolToObject(req, "stop", true);
        if (err != NULL) {
            JAddStringToObject(req, "err", err);
        }
        notecard.sendRequest(req);
    }
    if (J *req = notecard.newRequest("hub.set")) {
        JAddStringToObject(req, "mode", "-");
        notecard.sendRequest(req);
    }
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

    // Enter DFU mode.  Note that the Notecard will automatically switch us back out of
    // DFU mode after 15m, so we don't leave the notecard in a bad state if we had a problem here.
    if (J *req = notecard.newRequest("hub.set")) {
        JAddStringToObject(req, "mode", "dfu");
        notecard.sendRequest(req);
    }

    // Proceed with DFU
    dfuCheckMs = millis();

    // Wait until we have successfully entered the mode.  The fact that this loop isn't
    // just an infinite loop is simply defensive programming.  If for some odd reason
    // we don't enter DFU mode, we'll eventually come back here on the next DFU poll.
    bool inDFUMode = false;
    uint32_t beganDFUModeCheck = millis();
    while (!inDFUMode && millis() < beganDFUModeCheck + (2 * ms1Min)) {
        if (J *rsp = notecard.requestAndResponse(notecard.newRequest("dfu.get"))) {
            if (!notecard.responseError(rsp))
                inDFUMode = true;
            notecard.deleteResponse(rsp);
        }
        if (!inDFUMode)
            delay(2500);
    }

    // If we failed, leave DFU mode immediately
    if (!inDFUMode) {
        dfuAbort(0, "host failed to enter DFU mode");
        return;
    }

    // The image is ready.  If the version is the same as what's in memory, then of course don't
    // bother to do the update.
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

    APP_LOGF("dfu: beginning firmware update\n");

    // Loop over received chunks
    int offset = 0;
    int chunklen = 4096;
    int left = imageLength;
    NoteMD5Context md5Context;
    NoteMD5Init(&md5Context);
    while (left) {

        // Read next chunk from card
        int thislen = chunklen;
        if (left < thislen)
            thislen = left;

        // If anywhere, this is the location of the highest probability of I/O error
        // on the I2C or serial bus, simply because of the amount of data being transferred.
        // As such, it's a conservative measure just to retry.
        char *payload = NULL;
        for (int retry=0; retry<5; retry++) {
            APP_LOGF("dfu: reading chunk (offset:%d length:%d try:%d)\n", offset, thislen, retry+1);

            // Request the next chunk from the notecard
            J *req = notecard.newRequest("dfu.get");
            if (req == NULL) {
                APP_LOGF("dfu: insufficient memory\n");
                dfuAbort(update_handle, "out of memory");
                return;
            }
            JAddNumberToObject(req, "offset", offset);
            JAddNumberToObject(req, "length", thislen);
            J *rsp = notecard.requestAndResponse(req);
            if (rsp == NULL) {
                APP_LOGF("dfu: insufficient memory\n");
                dfuAbort(update_handle, "out of memory");
                return;
            }
            if (notecard.responseError(rsp)) {
                APP_LOGF("dfu: error on read: %s\n", JGetString(rsp, "err"));
            } else {
                char *payloadB64 = JGetString(rsp, "payload");
                if (payloadB64[0] == '\0') {
                    APP_LOGF("dfu: no payload\n");
                    notecard.deleteResponse(rsp);
                    dfuAbort(update_handle, "no payload");
                    return;
                }
                payload = (char *) malloc(JB64DecodeLen(payloadB64));
                if (payload == NULL) {
                    APP_LOGF("dfu: can't allocate payload decode buffer\n");
                    notecard.deleteResponse(rsp);
                    dfuAbort(update_handle, "out of memory");
                    return;
                }
                int actuallen = JB64Decode(payload, payloadB64);
                const char *expectedMD5 = JGetString(rsp, "status");
                char chunkMD5[NOTE_MD5_HASH_STRING_SIZE] = {0};
                NoteMD5HashString((uint8_t *)payload, actuallen, chunkMD5, sizeof(chunkMD5));
                if (actuallen == thislen && strcmp(chunkMD5, expectedMD5) == 0) {
                    notecard.deleteResponse(rsp);
                    break;
                }

                free(payload);
                payload = NULL;

                if (thislen != actuallen)
                    APP_LOGF("dfu: decoded data not the correct length (%d != actual %d)\n", thislen, actuallen);
                else
                    APP_LOGF("dfu: %d-byte decoded data MD5 mismatch (%s != actual %s)\n", actuallen, expectedMD5, chunkMD5);
            }

            notecard.deleteResponse(rsp);
        }
        if (payload == NULL) {
            APP_LOGF("dfu: unrecoverable error on read\n");
            dfuAbort(update_handle, "unrecoverable read error");
            return;
        }

        // MD5 the chunk
        NoteMD5Update(&md5Context, (uint8_t *)payload, thislen);

        // Write the chunk
        err = esp_ota_write(update_handle, (const void *)payload, thislen);
        if (err != ESP_OK) {
            free(payload);
            dfuAbort(update_handle, esp_err_to_name(err));
            return;
        }

        // Move to next chunk
        free(payload);
        APP_LOGF("dfu: successfully transferred offset:%d len:%d\n", offset, thislen);
        offset += thislen;
        left -= thislen;
    }

    // Exit DFU mode.  (Had we not done this, the Notecard exits DFU mode automatically after 15m.)
    if (J *req = notecard.newRequest("hub.set")) {
        JAddStringToObject(req, "mode", "-");
        notecard.sendRequest(req);
    }

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
