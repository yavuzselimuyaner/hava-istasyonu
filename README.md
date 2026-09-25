# Hava İstasyonu (ESP32-C3) — tasarım ve kod

İnternetten hava durumunu çeken (Open-Meteo), kart üstündeki BME280 ile oda sıcaklık/nem/basıncını ölçen ve ikisini bir ekranda gösteren kart. Tasarım ve kod büyük ölçüde LLM ile üretildi. **Şu an yalnızca tasarım ve kod aşamasında; kart üretilmedi.**

Kararların, hataların ve düzeltmelerin tam kaydı: `docs/calisma-gunlugu.md`.

## Klasörler
| Yol | İçerik |
|---|---|
| `docs/SUREC-NOTLARI.md` | **Süreci baştan sona anlatan notlar** (önce bunu oku) |
| `docs/v1/` | Güncel tasarım: `00-gereksinim.md` (girdi), `01-parca-secimi.md`, `02-denetim.md` (datasheet denetimi + pin planı) |
| `docs/tasarim.md` | ESKİ v0 (ESP32-S3) özeti, yalnızca karşılaştırma için |
| `pcb/v1/` | Güncel kart: `gen_netlist.py` (SKiDL) → `build_board.py` (pcbnew) → `route.py` (Freerouting) |
| `pcb/` (kök) | ESKİ v0 kartı (ESP32-S3), karşılaştırma için |
| `case/` | Kutu (FreeCAD betiği): `dump_board.py` → `make_case.py` → `check_fit.py`; önizlemeler `kutu_*.png` |
| `firmware/` | ESP-IDF projesi (ESP32-C3): Wi-Fi + Open-Meteo, BME280 sürücüsü, ST7789 ekran |
| `firmware/pc_demo/` | **ESP32 olmadan çalışan PC demosu**: gerçek Open-Meteo verisi + firmware'in gerçek ekran/sensör kodu → `screen.png` |
| `firmware/test/host/` | Donanımsız testler: ekran çizimi (`render.c`) ve BME280 formülleri (`bme_test.c`) |

## Durum (2026-09-25)
| Alan | Durum | Kanıt |
|---|---|---|
| Şematik | ERC 0 hata | `pcb/v1/gen_netlist.py` çıktısı |
| Kart (50x56 mm, 2 katman) | DRC 0 ihlal, 0 bağlanmamış pad | `pcb/v1/drc_routed.rpt`, `routed_top.png` |
| Firmware derleme | ESP-IDF v6.0.2, hatasız | `docs/build.log` |
| Wi-Fi + HTTPS + JSON | Wokwi'de çalıştı (gerçek Samsun verisi geldi) | günlük adım 18 |
| BME280 formülleri | Bosch örneği ve referans formülle doğrulandı | `firmware/test/host/bme_test.c` |
| Ekran çizimi | Bilgisayarda önizleme doğrulandı | `firmware/test/host/preview.png` |
| Kutu (55,3x68,6x18 mm) | Parçalı 3D kart modeli ile çakışma 0 | `case/README.md`, `case/gosterim_iso.png` |
| ESP32'siz PC demosu | Gerçek dış hava + firmware kodu ile ekran görüntüsü | `firmware/pc_demo/pc_demo.py` |

## Doğrulanmadı (donanım veya insan gerekiyor)
- Parça ve pin bilgisinin datasheet'e karşı **insan kontrolü** (Yavuz yapacak).
- Ekranın gerçek renk/konumu (`LCD_INVERT`, `LCD_Y_GAP` ayarları tahmin).
- BME280'in gerçek I2C okuması, gerçek sıcaklık doğruluğu.
- Gerçek kartta TLS el sıkışma süresi (Wokwi'de ~5 sn sürdü).
- Anten performansı, USB izleri modül altından geçiyor (bilinen risk).
- Hocanın "delikler bir optimizasyon problemi" sözünün tam anlamı (via / montaj deliği / delme sırası) henüz netleşmedi.

## Sıfırdan yeniden üretme (Windows)
Gerekenler: KiCad 10 (`C:\Program Files\KiCad\10.0`), Java 21, ESP-IDF v6.0.2, Python. Freerouting **v2.1.0** (Java 21 ile çalışan son sürüm) `pcb/tools/` içinde olmalı.

Kart (`pcb/v1` içinde; SKiDL için `pcb/.venv` sanal ortamı):
```
..\.venv\Scripts\python.exe gen_netlist.py
"C:\Program Files\KiCad\10.0\bin\python.exe" build_board.py
"C:\Program Files\KiCad\10.0\bin\python.exe" route.py
```
Not: Freerouting deterministik değil, her çalıştırmada biraz farklı iz/via sayısı çıkar. Denemeden önce çalışan `hava_routed.kicad_pcb` dosyasının kopyasını al.

Firmware (`firmware/` içinde, ESP-IDF PowerShell'inde):
```
idf.py build                  # gerçek kart için
idf.py -B build_wokwi -D "SDKCONFIG=sdkconfig.wokwi" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.wokwi.defaults" build   # Wokwi için
```
Wi-Fi bilgileri: `idf.py menuconfig` → "Hava Istasyonu". Wokwi'de `wokwi.toml` + `diagram.json` kullanılır (Wokwi'de BME280/ST7789 yok).

PC demosu (ESP32 gerekmez; Python + gcc + Pillow):
```
cd firmware/pc_demo && python pc_demo.py          # tek sefer;  --loop 60 ile 60 sn'de bir yeniler
```

Host testleri (`firmware/test/host` içinde, gcc):
```
gcc -DHOST_TEST -I../../main -o render.exe render.c && ./render.exe
gcc -o bme_test.exe bme_test.c -lm && ./bme_test.exe
```

## Pin planı (v1, `firmware/main/pins.h`)
I2C SDA/SCL: IO4/IO5 · LCD SCK/MOSI/DC/CS/RST/BL: IO6/IO7/IO10/IO3/IO1/IO0 · LED: IO20 · Buton: IO21 · BOOT: IO9 · USB: IO18/IO19. IO2, IO8 bilerek boş (strapping).
