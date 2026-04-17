param()

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
$mainPy = Join-Path $repoRoot "BACKEND\main.py"

$command = "cmd.exe /k \"cd /d \"\"%V\"\" && py -3 \"\"$mainPy\"\" shell --cwd \"\"%V\"\"\""

$bgKey = "HKCU:\Software\Classes\Directory\Background\shell\ProjectNexus"
$dirKey = "HKCU:\Software\Classes\Directory\shell\ProjectNexus"

New-Item -Path $bgKey -Force | Out-Null
Set-ItemProperty -Path $bgKey -Name "(default)" -Value "Open Project Nexus Here"
Set-ItemProperty -Path $bgKey -Name "Icon" -Value "cmd.exe"
New-Item -Path "$bgKey\command" -Force | Out-Null
Set-ItemProperty -Path "$bgKey\command" -Name "(default)" -Value $command

New-Item -Path $dirKey -Force | Out-Null
Set-ItemProperty -Path $dirKey -Name "(default)" -Value "Open Project Nexus Here"
Set-ItemProperty -Path $dirKey -Name "Icon" -Value "cmd.exe"
New-Item -Path "$dirKey\command" -Force | Out-Null
Set-ItemProperty -Path "$dirKey\command" -Name "(default)" -Value $command

Write-Host "Project Nexus context-menu entry installed."