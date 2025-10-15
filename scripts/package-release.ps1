param(
  [string]$Version = "v1.0.0"
)

$ErrorActionPreference = "Stop"

git status
git rev-parse --short HEAD | Out-Null

$zip = "Ags-AI-$Version.zip"
git archive --format zip --output $zip HEAD
Write-Host "Source package: $zip"

if (Test-Path requirements.lock) {
  Write-Host "requirements.lock detected (pinned)"
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker build -t ags-ai:$Version .
  docker save ags-ai:$Version | gzip > ags-ai-$Version.tar.gz
  Write-Host "Docker image saved: ags-ai-$Version.tar.gz"
} else {
  Write-Host "Docker not installed; skipping image build."
}

Write-Host "Done."

