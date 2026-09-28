# Çalıştırma ve yeniden üretme (Windows)

Gerekenler: KiCad 10 (`C:\Program Files\KiCad\10.0`), FreeCAD 1.1, Java 21, ESP-IDF v6.0.2, Python (SKiDL için `pcb/.venv`). Freerouting **v2.1.0** (Java 21 ile çalışan sürüm) `pcb/tools/` içinde olmalı (indirilmez, depoda yok).

## Kartlar (`pcb/main` veya `pcb/sensor` içinde)
Akış: SKiDL devre tanımı → **KiCad şematiği** → şematikten netlist → PCB yerleşimi → yol çizimi.
```
..\.venv\Scripts\python.exe gen_netlist.py
sh ../tools/check.sh .
"C:\Program Files\KiCad\10.0\bin\python.exe" build_board.py
"C:\Program Files\KiCad\10.0\bin\python.exe" route.py
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --severity-error --schematic-parity -o drc_routed.rpt hava_routed.kicad_pcb
```
1. `gen_netlist.py`: devre tanımı (SKiDL) → `hava_skidl.net`.
2. `tools/check.sh` (Git Bash ile): `gen_schematic.py` ile `hava.kicad_sch` şematiğini üretir, KiCad ERC'sini çalıştırır (hata varsa durur), şematikten `hava.net` netlistini alır, bunun SKiDL netlistiyle bağlantı olarak birebir aynı olduğunu `tools/net_compare.py` ile doğrular ve `hava_sematik.pdf` çıktısını verir.
3. `build_board.py`: PCB'yi şematikten gelen `hava.net`'ten kurar; her footprint şematikteki sembolüne bağlanır.
4. `route.py`: Freerouting ile yollar → `hava_routed.kicad_pcb`.
5. DRC: `--schematic-parity` şematik ile kartın uyuştuğunu da kontrol eder.

Şematik KiCad'de `hava.kicad_pro` açılarak görülebilir. Sensör kartındaki tek ERC uyarısı beklenen bir durumdur: BME280'in SDO bacağı I2C adresini 0x76 yapmak için GND'ye bağlı; kütüphane bu bacağı "çift yönlü" tanımladığı için KiCad, GND'deki güç işaretiyle birlikte uyarı verir.
Freerouting deterministik değildir; sonuç her seferinde biraz farklı çıkar. Denemeden önce çalışan `hava_routed.kicad_pcb` dosyasını Git'e kaydet.

Pin tablosu (datasheet karşılaştırması için): `python pcb/pin_tablosu.py` çalıştırılınca `docs/tasarim/03-pin-tablosu.md` yeniden üretilir.

## Kutu ve siper (`case` içinde)
Sırasıyla `dump_board.py` (KiCad python), `make_main_case.py`, `make_shield.py`, `kicad-cli pcb export step ...`, `check_fit.py` (hepsi `freecadcmd` ile), `render_gorseller.py`. Komutlar betiklerin başındaki açıklamalarda.

## Firmware (`firmware` içinde, ESP-IDF PowerShell'inde)
```
idf.py -B build_c3 -D "SDKCONFIG=sdkconfig.c3" -D "IDF_TARGET=esp32c3" build
idf.py -B build_s3 -D "SDKCONFIG=sdkconfig.s3" -D "IDF_TARGET=esp32s3" build
idf.py -B build_wokwi -D "SDKCONFIG=sdkconfig.wokwi" -D "IDF_TARGET=esp32s3" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.defaults.esp32s3;sdkconfig.wokwi.defaults" build
```
Wi-Fi bilgileri: `idf.py menuconfig` → "Hava Sensor Dugumu" (bilgiler Git'e girmez). Wokwi için `firmware` klasörünü VS Code'da aç, "Wokwi: Start Simulator".

### T-Display-S3'e (gerçek donanım) yükleme
```
idf.py -B build_tdisplay -D "SDKCONFIG=sdkconfig.tdisplay" -D "IDF_TARGET=esp32s3" -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.defaults.esp32s3;sdkconfig.tdisplay.defaults" menuconfig
```
Menüde Wi-Fi SSID/şifresini gir (bilgiler Git'e girmez), sonra:
```
idf.py -B build_tdisplay flash monitor
```
DHT22 verisi GPIO10'a, VCC 3V3'e, GND GND'ye bağlanır (SDA-VCC arası 10 kΩ pull-up önerilir). Kartın dahili ekranı (ST7789) otomatik devreye girer; sıcaklık, nem ve varsa basınç üç satır olarak gösterilir.

## Web
`web/index.html`'i tarayıcıda aç (MQTT.js CDN'den yüklenir). Yerel sunucu ile: `cd web && python -m http.server`.

## Testler (`firmware/test`, gcc)
```
gcc -Wall -Imock -o bme280_mock_test bme280_mock_test.c -lm
gcc -o dht22_test dht22_test.c
gcc -o bme_test bme_test.c -lm
```
