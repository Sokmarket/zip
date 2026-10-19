$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
function Run-Step([string]$Label, [scriptblock]$Action) {
  Write-Host "`n=== $Label ===" -ForegroundColor Cyan
  & $Action
  if ($LASTEXITCODE -ne 0) { throw "Başarısız: $Label (exit=$LASTEXITCODE)" }
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python Launcher bulunamadı; Python 3.11 kurun.' }
Run-Step 'Python sözdizimi' { py -3.11 -m py_compile app.py tests\test_app.py }
if (Get-Command node -ErrorAction SilentlyContinue) {
  Run-Step 'JavaScript sözdizimi' { node --check app.js }
} else { Write-Host 'UYARI: Node.js bulunamadı; JavaScript sözdizimi kontrolü atlandı.' -ForegroundColor Yellow }
Run-Step 'Birim ve entegrasyon testleri' { py -3.11 -m unittest discover -s tests -v }
Write-Host "`nBaşarılı: yerel doğrulama tamamlandı." -ForegroundColor Green
