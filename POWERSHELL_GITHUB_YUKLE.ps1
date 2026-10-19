[CmdletBinding()]
param(
  [string]$RepoName = 'egitim-pdf-atolyesi-pwa',
  [ValidateSet('private','public')][string]$Visibility = 'private',
  [string]$Description = 'Mobil uyumlu, yerel kaynaklardan eğitim PDF paketi üreten PWA ve Python uygulaması'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

Write-Host '=== Eğitim PDF Atölyesi: GitHub yayınlama ===' -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'DOGRULA.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Yayınlama öncesi doğrulama başarısız.' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git bulunamadı. Git for Windows kurun: https://git-scm.com/download/win' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI (gh) bulunamadı. Kurun: winget install --id GitHub.cli' }
& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'GitHub oturumu açık değil. Önce gh auth login çalıştırın.' }

# Ensure that no offline binaries or secrets are accidentally committed.
$blocked = Get-ChildItem -Recurse -File | Where-Object {
  $_.FullName -notmatch '[\\/](\.git|\.venv|venv|__pycache__)[\\/]' -and
  ($_.Extension -in @('.exe','.traineddata','.whl') -or $_.Name -match '\.(pem|pfx|p12|key)$')
}
if ($blocked) {
  Write-Host 'Uyarı: şu ikili/anahtar dosyaları Git deposuna eklenmemeli:' -ForegroundColor Yellow
  $blocked | ForEach-Object { Write-Host $_.FullName }
  throw 'Güvenlik kontrolü durdurdu. .gitignore kurallarını gözden geçirin.'
}

if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.git'))) {
  git init -b main
  if ($LASTEXITCODE -ne 0) { throw 'git init başarısız.' }
}
if (-not (git config user.name)) { git config user.name ((gh api user --jq .login).Trim()) }
if (-not (git config user.email)) {
  $uid = (gh api user --jq .id).Trim()
  $ghlogin = (gh api user --jq .login).Trim()
  git config user.email "$uid+$ghlogin@users.noreply.github.com"
}
# Verify and stage only project source/documentation; never stage downloaded wheels or OCR binaries.
git add .
if ($LASTEXITCODE -ne 0) { throw 'git add başarısız.' }
$staged = git status --short
if (-not $staged) { Write-Host 'Değişiklik yok; mevcut çalışma ağacı temiz.' }
else {
  git diff --cached --check
  if ($LASTEXITCODE -ne 0) { throw 'Git whitespace kontrolü başarısız.' }
  git commit -m 'Prepare verified Eğitim PDF Atölyesi PWA'
  if ($LASTEXITCODE -ne 0) { throw 'git commit başarısız; git config user.name ve user.email değerlerini kontrol edin.' }
}

$login = (gh api user --jq .login).Trim()
$repoFull = "$login/$RepoName"
$existing = gh repo view $repoFull --json name --jq .name 2>$null
if ($LASTEXITCODE -eq 0 -and $existing) {
  Write-Host "Depo zaten mevcut: https://github.com/$repoFull" -ForegroundColor Yellow
  if (-not (git remote)) { git remote add origin "https://github.com/$repoFull.git" }
} else {
  gh repo create $RepoName "--$Visibility" --description $Description --source . --remote origin --push
  if ($LASTEXITCODE -ne 0) { throw 'GitHub deposu oluşturma/yükleme başarısız oldu.' }
}
if ((git remote) -notcontains 'origin') {
  git remote add origin "https://github.com/$repoFull.git"
  if ($LASTEXITCODE -ne 0) { throw 'origin remote eklenemedi.' }
}
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'git push başarısız. Uzak dal mevcutsa git pull --rebase origin main komutunu inceleyin.' }
Write-Host "Başarılı: https://github.com/$repoFull" -ForegroundColor Green
Write-Host 'Not: wheelhouse içeriği ve Tesseract kurucusu boyut/lisans/dağıtım nedenleriyle depoya dahil edilmez.'
