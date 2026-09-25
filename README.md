# Hava İstasyonu — dıştan ölçüp internete yayınlayan sensör düğümü

Dışarıdaki bir sensör sıcaklık, nem ve basıncı ölçer; cihaz Wi-Fi ile MQTT üzerinden yayınlar; bir tarayıcı sayfası değerleri gösterir. Kart, kutu, firmware ve web sayfası büyük ölçüde LLM ile üretildi. **Şu an tasarım ve simülasyon aşamasında; gerçek donanımda henüz denenmedi.**

Önce oku: `docs/SUREC-NOTLARI.md` (süreç ve kavramlar) · `docs/YAPILACAKLAR.md` (Yavuz'un yapacakları) · `docs/calisma-gunlugu.md` (adım adım kayıt, hatalar ve düzeltmeler).

## Parçalar
| Klasör | İçerik |
|---|---|
| `pcb/v2/main` | Ana kart, 32x41 mm: ESP32-C3-WROOM-02, USB-C, AP2112K regülatör, reset/boot, LED, dik açılı 4 pinli sensör konnektörü, 2 montaj deliği |
| `pcb/v2/sensor` | Sensör kartı, 14x16 mm: BME280, 2x100 nF, aynı konnektör, 2 montaj deliği. Kabloyla uzakta durur |
| `case/v2` | Ana kutu (FreeCAD) ve radyasyon siperi, parçalı 3D kart modelleriyle çakışma kontrolü (`check_fit_v2.py`) |
| `firmware_v2` | ESP-IDF: ölç ve MQTT (wss, 443) ile yayınla; sensör BME280 (ESP32-C3) ya da DHT22 (T-Display-S3 prototipi) |
| `web/index.html` | Tek dosyalık tarayıcı sayfası (MQTT.js) |
| `docs/v2` | Gereksinim, parça seçimi ve datasheet denetimleri |

Konnektör sırası (iki kartta aynı): 1=3V3, 2=SDA/DATA, 3=GND, 4=SCL. İlk üç pin DHT22 modülünün (VCC, DATA, GND) sırasına denk gelir.

## Durum
| Alan | Durum | Kanıt |
|---|---|---|
| Ana kart, sensör kartı | ERC 0 hata, DRC 0 ihlal, 0 bağlanmamış pad | `pcb/v2/*/drc_routed.rpt`, `routed_top.png` |
| Kutu ve siper | Parçalı 3D kart modeliyle çakışma 0; negatif kontrol de çalışıyor | `case/v2/check_fit_v2.py`, `case/v2/sistem_gorunumu.png` |
| Firmware derleme | ESP32-C3 (BME280), ESP32-S3 (DHT22) ve Wokwi hedefleri derleniyor | `docs/calisma-gunlugu.md` adım 26-27 |
| Uçtan uca (simülasyon) | Wokwi: ESP32-S3 + sanal DHT22 → Wi-Fi → MQTT → `web/index.html` aynı değeri gösterdi | adım 27 |
| BME280 sürücüsü | Sanal sensör testi + Bosch referans formül testi geçti | `firmware_v2/test/` |
| DHT22 kod çözme | Datasheet örnekleriyle test geçti | `firmware_v2/test/dht22_test.c` |

## Doğrulanmadı (donanım veya insan gerekiyor)
- Parça ve pin bilgisinin bir insan tarafından datasheet ile kontrolü (`docs/YAPILACAKLAR.md`).
- BME280'in gerçek I2C okuması, gerçek DHT22'nin zamanlama toleransı.
- T-Display-S3'te DHT22 için GPIO10 (varsayım).
- Siperin yağmur koruması sınırlı; anten çevresindeki plastiğin etkisi ölçülmedi.
- Ana kartta USB izleri modül gövdesinin altından geçiyor (bilinen risk).
- Hocanın "delikler bir optimizasyon problemi" sözünün tam anlamı.

## Yeniden üretme (Windows)
Gerekenler: KiCad 10 (`C:\Program Files\KiCad\10.0`), FreeCAD 1.1, Java 21, ESP-IDF v6.0.2, Python (SKiDL için `pcb/.venv`). Freerouting **v2.1.0** (Java 21 ile çalışan sürüm) `pcb/tools/` içinde olmalı (indirilmez, repo'da yok).

Kartlar (`pcb/v2/main` veya `pcb/v2/sensor` içinde):
```
..\..\.venv\Scripts\python.exe gen_netlist.py
"C:\Program Files\KiCad\10.0\bin\python.exe" build_board.py
"C:\Program Files\KiCad\10.0\bin\python.exe" route.py
```
Freerouting deterministik değildir; sonuç her seferinde biraz farklı çıkar. Denemeden önce çalışan `hava_routed.kicad_pcb` dosyasını Git'e kaydet.

Kutu ve siper (`case/v2` içinde): sırasıyla `dump_board.py` (KiCad python), `make_main_case.py`, `make_shield.py`, `kicad-cli pcb export step ...`, `check_fit_v2.py` (hepsi `freecadcmd` ile), `render_v2.py`. Komutlar betiklerin başındaki açıklamalarda.

Firmware (`firmware_v2` içinde, ESP-IDF PowerShell'inde):
```
idf.py -B build_c3 -D "SDKCONFIG=sdkconfig.c3" -D "IDF_TARGET=esp32c3" build
idf.py -B build_s3 -D "SDKCONFIG=sdkconfig.s3" -D "IDF_TARGET=esp32s3" build
idf.py -B build_wokwi -D "SDKCONFIG=sdkconfig.wokwi" -D "IDF_TARGET=esp32s3" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.defaults.esp32s3;sdkconfig.wokwi.defaults" build
```
Wi-Fi bilgileri: `idf.py menuconfig` → "Hava Sensor Dugumu" (bilgiler Git'e girmez). Wokwi için `firmware_v2` klasörünü VS Code'da aç, "Wokwi: Start Simulator".

Web: `web/index.html`'i tarayıcıda aç (MQTT.js CDN'den yüklenir). Yerel sunucu ile: `cd web && python -m http.server`.

Testler (`firmware_v2/test`, gcc): `gcc -Wall -Imock -o bme280_mock_test bme280_mock_test.c -lm`, `gcc -o dht22_test dht22_test.c`, `gcc -o bme_test bme_test.c -lm`.

## Geçmiş
Eski v0 (ESP32-S3) ve v1 (internetten veri çeken, ekranlı) sürümleri yanlış yönde yapıldığı için depodan kaldırıldı; Git geçmişinde `fbf8f51` kaydında duruyor. Ayrıntı: `docs/calisma-gunlugu.md` adım 25.
