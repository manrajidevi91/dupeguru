Write-Host "Downloading Latest Visual Studio Build Tools..."

# Evergreen Microsoft installer (ALWAYS latest)
$installerUrl = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
$installerPath = "$env:TEMP\vs_BuildTools_latest.exe"

Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

Write-Host "Installing Latest C++ Build Tools (Silent Mode)..."

Start-Process -FilePath $installerPath -ArgumentList `
"--quiet --wait --norestart --nocache `
--installPath C:\BuildTools `
--add Microsoft.VisualStudio.Workload.VCTools `
--add Microsoft.VisualStudio.Component.Windows11SDK `
--includeRecommended" -NoNewWindow -Wait

Write-Host "Installation Completed ✅ (Latest Version Installed)"