
curl --request POST --url 'https://api.staging.blues.tools/req' --header 'content-type: '\''application/json'\''' --header "x-session-token:${NOTEHUB_ACCESS_TOKEN}" --data "{\"req\":\"note.add\",\"file\":\"commands.qi\",\"body\":{\"print\":\"hello\",\"count\":{\"min\":1,\"inc\":2,\"max\":7}},\"device\":\"${DEVICE_UID}\",\"project\":\"${APP_UID}\"}"

