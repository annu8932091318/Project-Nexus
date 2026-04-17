param()

$bgKey = "HKCU:\Software\Classes\Directory\Background\shell\ProjectNexus"
$dirKey = "HKCU:\Software\Classes\Directory\shell\ProjectNexus"

if (Test-Path $bgKey) {
    Remove-Item -Path $bgKey -Recurse -Force
}

if (Test-Path $dirKey) {
    Remove-Item -Path $dirKey -Recurse -Force
}

Write-Host "Project Nexus context-menu entry removed."