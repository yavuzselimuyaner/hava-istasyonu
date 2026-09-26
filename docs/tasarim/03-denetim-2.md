# Adım 3 — İkinci datasheet denetimi (Agent: denetçi)

> **Not:** Bu belge eski (ekranlı) tasarım için yazıldı: cihaz ekranlıydı ve internetten veri çekiyordu. **Ekran, pin planı ve "internetten çekme" kısımları ESKİDİR.** MCU/sensör/regülatör seçimi ve datasheet bulguları güncel tasarım için de GEÇERLİDİR. Güncel gereksinim: `00-gereksinim.md`.


Yöntem: Datasheet PDF'leri araç tarafından diske kaydedildi ve `pdftotext` ile YEREL okundu. Web aracının özeti tek başına yeterli çıkmadı (aşağıdaki hata bölümüne bak).
Kaynaklar: ESP32-C3 Series Datasheet v2.4 (Espressif), BME280 Data sheet rev 1.23 (Bosch, BST-BME280-DS001-23), AP2112 DS39724 Rev 2-2 (Diodes), USBLC6-2 (ST, arama özeti).

## Bulunan tasarım hataları (düzeltildi)
| # | Bulgu | Kaynak | Düzeltme |
|---|---|---|---|
| 1 | **GPIO8 bağlantısız bırakılmıştı.** Joint Download Boot modu için GPIO8=1 şart; varsayılanı "floating" (belirsiz) | C3 datasheet Tablo 3-1 ve 3-3 | IO8'e 10 kΩ pull-up (R9) |
| 2 | **GPIO2 bağlantısız bırakılmıştı.** Datasheet, glitch'lere karşı yukarı çekilmesini öneriyor | Tablo 3-3 not 2 | IO2'ye 10 kΩ pull-up (R8) |
| 3 | **BME280 için tek 100 nF vardı.** Bosch VDD ve VDDIO için ayrı ayrı C1, C2 = 100 nF gösteriyor | Bosch şekil 17 ve notları | İkinci 100 nF (C7) eklendi |

Boot tablosu (Tablo 3-3): SPI boot: GPIO2=1, GPIO8=herhangi, GPIO9=1 · Joint download boot: GPIO2=1, GPIO8=1, GPIO9=0.

## Doğrulananlar
- **BME280 pinleri:** 1 GND, 2 CSB, 3 SDI, 4 SCK, 5 SDO, 6 VDDIO, 7 GND, 8 VDD. Bizim bağlantıyla birebir (CSB→VDDIO = I2C, SDO→GND = 0x76, pull-up 4.7 kΩ önerilen değer). Numaralandırma saat yönünde, alttan bakışta saat yönünün tersi (KiCad footprint'i "ClockwisePinNumbering", uyumlu).
- **BME280 besleme:** VDD 1.71-3.6 V (dalgalanma en çok 50 mVpp), VDDIO 1.2-3.6 V; 1 Hz zorlamalı modda ~3.6 µA. Sensörün ölçülen sıcaklığı "PCB sıcaklığına ve kendi ısınmasına bağlı, genelde ortamın üstünde" (dipnot 7): LDO'dan uzak yerleşimimiz mantıklı.
- **AP2112K (SOT25):** Pinler 1 VIN, 2 GND, 3 EN, 5 VOUT (KiCad sembolü uyumlu; 4. pin datasheet tablosunda tanımlı değil). 600 mA (min.) çıkış, 3.3 V sürümde dropout tipik 250 mV @600 mA. EN yüksek eşiği 1.5 V (VIN'e bağlamamız doğru). Çıkışta 1 µF ile kararlı (seramik/tantal); 1 µF seramik seçilirse X7R veya X5R. Bizim 10 µF için **BOM'da dielektrik X5R/X7R olmalı**.
- **Akım marjı:** C3 en yüksek Wi-Fi TX akımı çip datasheet'inde 335 mA, modül datasheet'inde 345 mA (802.11b); dış kaynak için en az 0.5 A isteniyor. AP2112K'nın 600 mA'si yeterli (önceki "ince marj" endişesi yumuşadı).
- **USBLC6-2SC6:** Pinler 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1 (arama özeti; netlist ile uyumlu).
- **USB:** GPIO18/19 varsayılan olarak USB Serial/JTAG denetleyicisine bağlı.

## Yeni açık riskler
- **LDO ısınması:** SOT25 θJA = 184 °C/W. 5 V → 3.3 V farkı 1.7 V; ortalama 100 mA'de ~0.17 W, yaklaşık 31 °C yükselme; 345 mA (modül) tepe akım kısa süreli. Kart ısınırsa BME280'in sıcaklığı yüksek ölçülebilir; gerçek kartta ölçülmeli.
- AP2112 mutlak azami giriş gerilimi 6.5 V (USB 5 V için yeterli, dalgalanma marjı dar).
- 4 numaralı AP2112 pini datasheet tablosunda tanımlı değil (NC olarak da yazılmamış); KiCad sembolünde yok, footprint'te pad var, bağlantısız kalır. Ayrıntı: `06-datasheet-kontrolu.md`.

## LLM'in yaptığı hata (kayda değer)
Web aracı (WebFetch) ESP32-C3 boot tablosunu **yanlış** özetledi: "SPI boot: GPIO8=1; Download: GPIO8=0, GPIO9=1" dedi. PDF'in kendisinde doğru değerler: SPI boot GPIO8=herhangi, Download GPIO8=1 ve GPIO9=0. Aracın özeti, tablo yapısı bozulmuş metni yanlış eşledi. Ders: sayısal tablo değerleri özetten değil, kaynak metinden doğrulanmalı. AP2112 ve BME280 PDF'lerini de araç okuyamadı, yerel `pdftotext` ile okundu.

## Hâlâ insan/donanım gerektirenler
- ESP32-C3-WROOM-02 modülünün kendi datasheet'i (WROOM-02 pin tablosu ve dahili bileşenler) ayrıca; buradaki tablolar çip datasheet'inden.
- JLCPCB stok ve kütüphane uyumu (bu turda kapsam dışı).
