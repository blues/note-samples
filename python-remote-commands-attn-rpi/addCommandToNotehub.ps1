$headers=@{}
$headers.Add("user-agent", "vscode-restclient")
$headers.Add("content-type", "application/json")
$headers.Add("x-session-token", "$env:NOTEHUB_ACCESS_TOKEN")
$body = '{"req":"note.add","file":"commands.qi","body":{"print":"hello","count":{"min":1,"inc":2,"max":7}},"device":"' + $env:DEVICE_UID + '","project":"' + $env:APP_UID + '"}'
$response = Invoke-WebRequest -Uri 'https://api.staging.blues.tools/req' -Method POST -Headers $headers -ContentType 'application/json' -Body $body

Write-Output $response.StatusCode
Write-Output $response.StatusDescription
Write-Output $response.RawContent