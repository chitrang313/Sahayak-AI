$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Sahayak AI.lnk"
$targetPath = Join-Path $repoRoot "Launch Sahayak AI.bat"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $repoRoot
$shortcut.Description = "Launch Sahayak AI"
$shortcut.IconLocation = "%SystemRoot%\\System32\\SHELL32.dll,220"
$shortcut.Save()

Write-Output "Desktop shortcut created: $shortcutPath"
