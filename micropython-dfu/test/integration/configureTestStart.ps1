
$SourceFolder = "../../src"
$DestinationFolder = "src"

Set-Location -Path $PSScriptRoot


if (Test-Path $DestinationFolder) {
    Write-Host "Removing folder " $DestinationFolder
    Remove-Item -Path $DestinationFolder -Force -Recurse
}

mkdir $DestinationFolder

Copy-Item -Path $SourceFolder/*.py -Destination $DestinationFolder
Copy-Item -Path $SourceFolder/secrets.json -Destination $DestinationFolder


Set-Location -Path $PSScriptRoot/../..

wsl . generateTarFile.sh