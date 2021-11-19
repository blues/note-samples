
API_URL="${NOTEHUB_API_URL:-api.notefile.net}"

curl --request POST --url "https://${API_URL}/req" --header 'content-type: '\''application/json'\''' --header "x-session-token:${NOTEHUB_ACCESS_TOKEN}" --data "{\"req\":\"note.add\",\"file\":\"commands.qi\",\"body\":{\"print\":\"hello\",\"count\":{\"min\":1,\"inc\":2,\"max\":7}},\"device\":\"${DEVICE_UID}\",\"project\":\"${PROJECT_UID}\"}"

