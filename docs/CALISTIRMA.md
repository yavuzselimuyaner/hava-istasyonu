# Çalıştırma ve yeniden üretme (Windows)

Gerekenler: KiCad 10 (`C:\Program Files\KiCad\10.0`), FreeCAD 1.1, Java 21, ESP-IDF v6.0.2, Python (SKiDL için `pcb/.venv`). Freerouting **v2.1.0** (Java 21 ile çalışan sürüm) `pcb/tools/` içinde olmalı (indirilmez, depoda yok).

## Kartlar (`pcb/main` veya `pcb/sensor` içinde)
```
..\.venv\Scripts\python.exe gen_netlist.py
"C:\Program Files\KiCad\10.0\bin\python.exe" build_board.py
"C:\Program Files\KiCad\10.0\bin\python.exe" route.py
```
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

## Web
`web/index.html`'i tarayıcıda aç (MQTT.js CDN'den yüklenir). Yerel sunucu ile: `cd web && python -m http.server`.

## Testler (`firmware/test`, gcc)
```
gcc -Wall -Imock -o bme280_mock_test bme280_mock_test.c -lm
gcc -o dht22_test dht22_test.c
gcc -o bme_test bme_test.c -lm
```
