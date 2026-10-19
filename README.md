# Eğitim PDF Atölyesi — PWA / çevrimdışı Windows paketi

Mobil uyumlu web arayüzü ve yerel Python tabanlı PDF üretim motoru.

## Önerilen kurulum

Windows 10/11 x64 + Python 3.11 x64:

1. İnternetli Windows makinesinde `HAZIRLA_CEVRIMDISI.bat` çalıştırın.
2. `RAPOR_HAZIRLIK.txt` raporunu ve `wheelhouse/win_amd64_py311` içeriğini doğrulayın.
3. Proje klasörünü çevrimdışı hedef PC'ye kopyalayın.
4. `KURULUM_CEVRIMDISI.bat` çalıştırın.
5. `KURULUM_KONTROL.bat` ile bağımlılıkları doğrulayın.
6. `baslat.bat` çalıştırıp `http://127.0.0.1:8767` adresini açın.

## Windows 32-bit ve OCR notu

Hazırlama betiği `win32_py311` wheel'lerini de indirmeyi dener. Bazı güncel bağımlılıklar 32-bit Windows için ikili wheel sağlamadığından 32-bit kurulum garanti edilmez; raporu kontrol edin. Paketteki Tesseract yükleyicisi Windows x64 içindir. 32-bit Windows OCR için ayrıca uyumlu 32-bit Tesseract dağıtımı gerekir.

## Mobil erişim

`baslat_ag.bat`, arayüzü aynı yerel ağdaki telefon/tablet tarayıcısına açar. Windows'ta `ipconfig` ile PC'nin IPv4 adresini bulun ve telefonda `http://PC-IP:8767` açın. Bu mod kimlik doğrulamasızdır; yalnızca güvenilir özel Wi-Fi'da kullanın. Telefonlarda gerçek PWA kurulumu için HTTPS gerekir. Bu paket Python motorunu Android/iOS'a kurmaz.

Ayrıntılar: `MOBIL_VE_PWA_KURULUM.txt` ve `KULLANIM.txt`.

## Test ve GitHub deposu

Otomatik testleri yerel olarak çalıştırın:

```powershell
py -3.11 -m py_compile app.py tests\test_app.py
node --check app.js
py -3.11 -m unittest discover -s tests -v
```

Git ve GitHub CLI kuruluysa PowerShell'i proje klasöründe açıp `gh auth login` komutuyla oturum açın. Ardından aşağıdaki betik varsayılan olarak **özel (private)** bir GitHub deposu oluşturur ve kodu gönderir:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\POWERSHELL_GITHUB_YUKLE.ps1
```

Depo adını ve görünürlüğünü değiştirmek için:

```powershell
.\POWERSHELL_GITHUB_YUKLE.ps1 -RepoName egitim-pdf-atolyesi-pwa -Visibility private
```

`-Visibility public` seçeneği depoyu herkese açık yapar. GitHub'a Tesseract kurucusu, OCR dil dosyaları veya wheelhouse ikilileri gönderilmez; bunlar hazırlama bilgisayarında üretilip ayrıca güvenli şekilde aktarılmalıdır.

### Doğrulama

`tests/test_app.py` metin temizleme, metin/HTML/ZIP çıkarımı, çevrimdışı URL engelleme ve PDF+ZIP çıktı üretimini kapsar. GitHub Actions her push ve pull request'te Python sözdizimini, JavaScript sözdizimini ve testleri çalıştırır. Bu testler Windows x86/x64 üzerindeki kurulumları veya Tesseract OCR motorunu fiziksel olarak doğrulamaz.

Windows'ta aynı kontrolleri PowerShell üzerinden çalıştırmak için `./DOGRULA.ps1` komutunu kullanabilirsiniz. GitHub yükleme betiği bu doğrulamayı yüklemeden önce otomatik çalıştırır.
