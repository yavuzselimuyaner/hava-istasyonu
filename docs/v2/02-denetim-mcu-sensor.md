# v1 Adım 2 — Denetim (Agent: denetçi)

> **Not:** Bu belge eski (v1) tasarım için yazıldı: cihaz ekranlıydı ve internetten veri çekiyordu. **Ekran, pin planı ve "internetten çekme" kısımları ESKİDİR.** MCU/sensör/regülatör seçimi ve datasheet bulguları v2 için de GEÇERLİDİR. Güncel gereksinim: `00-gereksinim.md`.


Kaynaklar: Espressif ESP32-C3-WROOM-02 datasheet (documentation.espressif.com), Bosch BME280 datasheet rev 1.24, Diodes AP2112 datasheet DS39724, JLCPCB parça sayfaları (arama sonuçları). Sonuçlar web aramasının özetlerine dayanır; kritik sayılar tasarım kilitlenmeden önce PDF'den elle teyit edilmelidir.

## Doğrulananlar
| Konu | Bulgu | Durum |
|---|---|---|
| C3 modül pinleri | 3V3=1, EN=2, IO4-7=3-6, IO8=7, IO9=8, GND=9, IO10=10, RXD/IO20=11, TXD/IO21=12, IO18(USB D-)=13, IO19(USB D+)=14, IO3=15, IO2=16, IO1=17, IO0=18, GND=19 | KiCad sembolü ve footprint ile TAM UYUMLU |
| Strapping | GPIO2, GPIO8, GPIO9 | Doğrulandı; bu üç pin sinyal olarak kullanılmayacak (GPIO9 = BOOT butonu) |
| USB | GPIO18/19 dahili USB Serial/JTAG; GPIO olarak yeniden atanırsa USB-JTAG kapanır | Doğrulandı; bu iki pin USB'ye ayrılmalı |
| EN devresi | Önerilen RC: 10 kΩ + 1 µF | Doğrulandı, taslakla aynı |
| BME280 I2C | CSB → VDDIO ile I2C modu; SDO GND ise 0x76, VDDIO ise 0x77; SDO bağlantısız bırakılamaz | Doğrulandı, taslakla aynı |
| AP2112 | 600 mA (min) sürekli akım; çıkışta 1 µF X7R/X5R önerilir | Doğrulandı; planlanan 10 µF ile uyumluluk (ESR/stabilite) datasheet'ten ayrıca kontrol edilecek |

## Bulunan hatalar (parça seçici agent'ın yanlışları)
1. **"22 GPIO" iddiası yanlış.** Çip 22 GPIO'ya sahip ama WROOM-02 modülünde 15 GPIO pini var (IO0-IO10, RXD/IO20, TXD/IO21, IO18, IO19).
2. **Güç marjı ince.** Datasheet dış kaynak için en az 0.5 A istiyor; AP2112K-3.3'ün garantili akımı 600 mA. Marj yalnızca 100 mA. Kabul edilebilir ama not düşülmeli: yeterli çıkış kondansatörü ve kısa yol; sorun çıkarsa daha güçlü LDO.
3. **Pin bütçesi sıkı.** Kullanılabilir sinyal pini: IO0,1,3,4,5,6,7,10 (8 pin) + UART pinleri IO20,IO21 (USB konsol kullanıldığı için serbest) = 10. Strapping (2,8,9) ve USB (18,19) hariç.

## Pin planı (v1, onaylanacak)
| Sinyal | Pin |
|---|---|
| I2C SDA / SCL | IO4 / IO5 |
| LCD SCK / MOSI | IO6 / IO7 |
| LCD DC / CS | IO10 / IO3 |
| LCD RST / BL | IO1 / IO0 |
| Durum LED | IO20 |
| Kullanıcı butonu | IO21 |
| BOOT butonu | IO9 (strapping, bilerek) |
| EN | modül pin 2 |
| USB D-/D+ | IO18 / IO19 |
Kullanılmayan: IO2, IO8 (strapping, bilerek boş).

## Doğrulanamayanlar (insan / ek adım gerekiyor)
- JLCPCB: ESP32-C3-WROOM-02-N4 (C2934560) ve AP2112K-3.3TRG1 (C51118) katalogda var; **stok ve Basic/Extended durumu doğrulanamadı**. BME280 ve USB-C konnektör arama sonuçlarında bulunamadı, ayrıca aranacak.
- GPIO8/GPIO9 önyükleme seviyeleri ve download modu koşulu (bu özetten net çıkmadı).
- BME280 bypass kondansatör değeri: 100 nF değeri BMP280 datasheet'inden geliyor, BME280'de doğrudan görülmedi.
- Anten keepout ölçüleri: datasheet "noktalı çizgi" diyor, milimetre alınmadı; Espressif hardware design guidelines'a bakılmalı.
- C3 footprint pad 19 (GND) altında termal via'lar var; delik çapı ve üretici kurallarıyla DRC'de kontrol edilecek.
