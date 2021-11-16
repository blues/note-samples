
<<<<<<< HEAD
API_URL="${NOTEHUB_API_URL:-api.notefile.net}"

curl --request POST --url "https://${API_URL}/req" --header 'content-type: '\''application/json'\''' --header "x-session-token:${NOTEHUB_ACCESS_TOKEN}" --data "{\"req\":\"note.add\",\"file\":\"commands.qi\",\"body\":{\"print\":\"hello\",\"count\":{\"min\":1,\"inc\":2,\"max\":7}},\"device\":\"${DEVICE_UID}\",\"project\":\"${PROJECT_UID}\"}"
=======
curl --request POST --url 'https://api.staging.blues.tools/req' --header 'content-type: '\''application/json'\''' --header "x-session-token:${NOTEHUB_ACCESS_TOKEN}" --data "{\"req\":\"note.add\",\"file\":\"commands.qi\",\"body\":{\"print\":\"hello\",\"count\":{\"min\":1,\"inc\":2,\"max\":7}},\"device\":\"${DEVICE_UID}\",\"project\":\"${APP_UID}\"}"
>>>>>>> 0752e29a803fe8f0c8af511ead9ebbc2cfa35c6f

