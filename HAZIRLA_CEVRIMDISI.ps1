$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$report = Join-Path $PSScriptRoot 'RAPOR_HAZIRLIK.txt'
$lines = [System.Collections.Generic.List[string]]::new()
function Log([string]$s) { Write-Host $s; $lines.Add($s) }
function Download([string]$url,[string]$path) {
  Log "İndiriliyor: $url"
  Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
  if (!(Test-Path -LiteralPath $path) -or (Get-Item -LiteralPath $path).Length -lt 1024) { throw "Dosya eksik/boş görünüyor: $path" }
  Log "Tamamlandı: $path ($((Get-Item -LiteralPath $path).Length) bayt)"
}
try {
  $wheelRoot = Join-Path $PSScriptRoot 'wheelhouse'
  $ocrRoot = Join-Path $PSScriptRoot 'ocr_installer'
  New-Item -ItemType Directory -Force -Path $wheelRoot,$ocrRoot | Out-Null
  $req = Join-Path $PSScriptRoot 'requirements.txt'
  # Python 3.11 wheels are selected explicitly so this preparation host's bitness does not decide target wheels.
  $targets = @(
    @{Name='win_amd64_py311'; Platform='win_amd64'},
    @{Name='win32_py311'; Platform='win32'}
  )
  foreach ($t in $targets) {
    $dest = Join-Path $wheelRoot $t.Name
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Log "`n=== $($t.Name) hedefi ==="
    & py -3.11 -m pip download --disable-pip-version-check --only-binary=:all: --dest $dest --requirement $req --platform $t.Platform --python-version 311 --implementation cp --abi cp311 --abi abi3 --abi none
    if ($LASTEXITCODE -ne 0) {
      Log "UYARI: $($t.Name) için tüm wheel'ler indirilemedi. Bu mimari, mevcut paket sürümleriyle tam desteklenmeyebilir."
    } else {
      Log "Başarılı: $($t.Name)"
    }
  }
  $installer = Join-Path $ocrRoot 'tesseract-ocr-w64-setup-5.4.0.20240606.exe'
  if (!(Test-Path -LiteralPath $installer)) {
    Download 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe' $installer
  } else { Log 'Tesseract yükleyicisi zaten mevcut; yeniden indirilmedi.' }
  foreach ($lang in @('tur','eng','osd')) {
    $dest = Join-Path $ocrRoot "$lang.traineddata"
    if (!(Test-Path -LiteralPath $dest) -or (Get-Item -LiteralPath $dest).Length -lt 1024) {
      Download "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/$lang.traineddata" $dest
    } else { Log "Dil verisi zaten mevcut: $lang" }
  }
  # Create a SHA-256 inventory of all downloaded files, useful for transfer integrity checks.
  $hashLines = Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File | Where-Object { $_.FullName -notmatch '\\(__pycache__|ciktilar)\\' -and $_.Name -ne 'SHA256SUMS.txt' -and $_.Name -ne 'RAPOR_HAZIRLIK.txt' } | ForEach-Object {
    $h = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    "{0}  {1}" -f $h.Hash, (Resolve-Path -Relative $_.FullName)
  }
  $hashLines | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'SHA256SUMS.txt') -Encoding UTF8
  Log "`nSHA256 envanteri oluşturuldu: SHA256SUMS.txt"
  Log "Not: x86 klasöründe wheel eksikse 32-bit kurulum tam olmayabilir; raporda klasör durumunu doğrulayın."
  Log "OCR kurucusu yalnızca Windows x64 içindir. Windows x86 üzerinde Tesseract OCR ayrıca uyumlu bir 32-bit dağıtım gerektirir."
  Log "`nHazırlama işlemi tamamlandı. Bu rapor tüm paketlerin tüm hedeflerde başarılı olduğunu garanti etmez; her wheel klasörünü kontrol edin."
  $lines | Set-Content -LiteralPath $report -Encoding UTF8
  exit 0
} catch {
  Log "HATA: $($_.Exception.Message)"
  $lines | Set-Content -LiteralPath $report -Encoding UTF8
  exit 1
}
