Write-Host "Downloading new version of Cello"

Remove-Item "cello.exe"

wget "http://esox3.scilifelab.se:8084/dist/windows/cello.exe" -outfile "cello.exe"

Start-Process -Filepath "cello.exe"