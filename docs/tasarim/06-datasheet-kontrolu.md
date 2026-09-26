# Datasheet kontrolü (indirilen PDF'lerle)

Kontrol, Yavuz'un indirdiği beş PDF ile yapıldı. Metinler `pdftotext` ile çıkarıldı; şemalar ve çizimler PyMuPDF ile görüntüye çevrilip tek tek okundu. Kartın değerleri `docs/tasarim/05-pin-tablosu.md` ile karşılaştırıldı.

| Belge | Sürüm |
|---|---|
| ESP32-C3 Series Datasheet | v2.4 |
| ESP32-C3-WROOM-02 & WROOM-02U Datasheet | v1.7 |
| BME280 Data sheet (Bosch) | dosya revizyonu 1.24 (sayfa altbilgisi DS001-23 rev 1.23) |
| AP2112 (Diodes) | DS39724 Rev. 2-2, Haziran 2017 |
| GCT USB4105 Product Drawing | Rev B3 (24/02/23) |

## Sonuç: 5 kontrolün 5'i uyuşuyor, 2 düzeltme yapıldı

### 1) Strapping pinleri ve açılış modu: UYUŞUYOR
- **Kaynak:** Çip datasheet Tablo 3-1 ve 3-3 (s.30-31); modül datasheet Tablo 4-3.
- **Datasheet:** SPI boot: GPIO2=1, GPIO8=herhangi, GPIO9=1. İndirme modu: GPIO2=1, **GPIO8=1**, GPIO9=0. Varsayılan: GPIO2 ve GPIO8 "floating", GPIO9 zayıf pull-up. Not: GPIO2 glitch'ler nedeniyle yukarı çekilmesi önerilir.
- **Kart:** IO2 → R8 (10 kΩ) → +3V3; IO8 → R9 (10 kΩ) → +3V3; IO9 → BOOT hattı (R4 10 kΩ pull-up + buton).
- **Ek doğrulama:** Modül datasheet Şekil 9-1 (s.34), Espressif'in referans tasarımı: **IO2 için R9 = 10K ve IO8 için R8 = 10K ile VDD33'e çekme** var; IO9 yalnızca "Boot Option" başlığına gidiyor (dahili zayıf pull-up'a güveniyor). Kartımız referansla aynı, IO9'daki ek 10 kΩ zararsız. Modülün kendi şematiğinde (Şekil 8-1) EN, IO2 ve IO8 için dahili direnç yok, yani dış pull-up gerekiyor.

### 2) ESP32-C3-WROOM-02 modülü: UYUŞUYOR
- **Kaynak:** Modül datasheet Tablo 3-1 (s.10-11), Tablo 6-2, 6-4, Şekil 9-1.
- **Pinler:** 1=3V3, 2=EN, 3=IO4, 4=IO5, 7=IO8, 8=IO9, 9 ve 19=GND, 11=RXD (IO20), 12=TXD (IO21), 13=IO18 (USB D−), 14=IO19 (USB D+), 16=IO2. Pin tablosundaki U1 satırlarıyla birebir aynı.
- **EN:** "EN floating bırakılmamalı"; önerilen RC 10 kΩ ve 1 µF (s.34 metni). Bizde R3 = 10 kΩ, C5 = 1 µF. **Not:** Aynı sayfadaki şekilde C4 = 0,1 µF yazıyor, yani Espressif'in kendi şekli ile metni tutarsız; biz metne uyduk.
- **Güç:** VDD33 3,0–3,6 V; harici kaynak en az **0,5 A** (Tablo 6-2). Wi-Fi tepe akımı **345 mA** (802.11b 1 Mbps @20,5 dBm, Tablo 6-4). AP2112K'nın 600 mA'si yeterli.
- **Besleme kondansatörleri:** Referansta C1 = 10 µF, C2 = 0,1 µF; bizde C3 = 10 µF ve C4 = 100 nF, aynı.
- **USB hatları:** Referans tasarımda D+ ve D− üzerinde 0 Ω seri direnç (ve yer tutucu ESD kondansatörü) var; bizde seri direnç yok, USBLC6 koruması var. Datasheet ikisini de zorunlu kılmıyor.

### 3) BME280: UYUŞUYOR
- **Kaynak:** Bölüm 7, Tablo 35 (pin açıklaması), Şekil 17 (I2C bağlantısı), Şekil 21 (lehim deseni önerisi, s.43).
- **Pinler:** 1=GND, 2=CSB, 3=SDI, 4=SCK, 5=SDO, 6=VDDIO, 7=GND, 8=VDD. I2C için CSB→VDDIO, SDO→GND (adres 0x76), VDD ve VDDIO için ayrı **C1, C2 = 100 nF**, pull-up R1, R2 için "normal değer 4,7 kΩ". Bizim sensör kartı ve ana kart (R5, R6 = 4,7 kΩ) ile aynı.
- **Footprint:** Önerilen lehim deseni: pad 0,5 x 0,35 mm, aralık 0,65 mm, merkez ofseti 1,025 mm, pin 1 üst sağda (Bosch çizimi). KiCad footprint'inin (Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering) pad boyutu, aralığı ve ofseti aynı; çizim yalnızca 90° dönük ve pin 1 konumu buna göre doğru.

### 4) AP2112K-3.3 (SOT25): UYUŞUYOR, 1 düzeltme
- **Kaynak:** Sayfa 2 (Pin Descriptions ve Blok Şeması), Not 4, Mutlak Azami Değerler, Önerilen Çalışma Koşulları.
- **Pinler (SOT25):** 1=VIN, 2=GND, 3=EN, 5=VOUT. Blok şemada (D = SOT25) aynı numaralar. Bizim U2 ile aynı.
- **Değerler:** Önerilen VIN 2,5–6,0 V, mutlak azami 6,5 V (USB 5 V için uygun). Tipik uygulama giriş ve çıkışta 1 µF; Not 4: 1 µF seramikse **X7R veya X5R** olmalı. θJA (SOT25) = 184 °C/W. EN yüksek eşiği 1,5 V (bizde EN, VIN'e bağlı).
- **Düzeltme:** Önceki belgelerimde "SOT25'te 4. pin NC" yazmıştım. Datasheet tablosunda NC satırında SOT25 sütunu "—" ve 4. pin tanımlı değil. Belgeler düzeltildi.
- **Not:** Datasheet yalnızca 1 µF'ı örnekliyor, üst sınır vermiyor. Bizdeki 10 µF (C1, C2) datasheet ile çelişmez ama datasheet tarafından da özellikle onaylanmış değil; bu bir tasarım tercihidir. Kondansatörler X5R/X7R seçilmeli.

### 5) USB-C (GCT USB4105): UYUŞUYOR
- **Kaynak:** Product Drawing, sayfa 1, pin tablosu.
- **Pinler:** A1, A12, B1, B12 = GND; A4, A9, B4, B9 = VBUS; A5 = CC1; B5 = CC2; A6/B6 = D+; A7/B7 = D−; A8 = SBU1; B8 = SBU2; SHELL = GND. Karttaki J1 net'leriyle birebir aynı (SBU pinleri bağlantısız).
- **CC dirençleri:** Bağlantı çiziminde yok. USB Type-C kuralı: cihaz (sink) tarafında **her CC pini ayrı ayrı 5,1 kΩ ile GND'ye** bağlanır, iki pin birbirine bağlanmaz (kaynaklar: Espressif ESP-IoT-Solution USB Type-C rehberi, ST TA0357, Infineon bilgi tabanı, Hackaday). Bizde R1 ve R2 ayrı, 5,1 kΩ, GND'ye.

## Açıkta kalanlar (bu PDF'lerle kontrol edilemeyenler)
- **USBLC6-2SC6 pin sırası:** ST datasheet'i indirilmedi; pin sırası (1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1) yalnızca web arama özetinden geliyor.
- **USB4105 footprint ölçüleri:** Pin tablosu doğrulandı; footprint'in ayak izi ölçülerinin (kabuk delikleri, lehim alanları) çizimle sayısal karşılaştırması yapılmadı.
- **USB Type-C 5,1 kΩ kuralı:** İkincil kaynaklarla teyit edildi; USB-IF spesifikasyonunun kendisi açılmadı.
- **Anten yasak bölgesi ölçüsü:** Espressif donanım tasarım rehberinden değil, footprint'in courtyard'ından alındı.
