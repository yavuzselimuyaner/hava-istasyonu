# Datasheet denetimi

Kartlardaki bağlantılar ve değerler, parçaların datasheet'leriyle karşılaştırıldı. Kartın pin ve bağlantı listesi `03-pin-tablosu.md` dosyasında (karttan otomatik üretilir).

## Yöntem
- Datasheet metinleri PDF'ten çıkarıldı; şemalar, çizimler ve tablo görüntüleri sayfa sayfa görüntüye çevrilip okundu.
- Sayısal değerler her zaman PDF'in kendisinden alındı. Bir boot tablosunun otomatik bir özetle yanlış aktarılması, bunun gerekli olduğunu gösterdi.
- Karttaki her pin ve değer, datasheet'teki ilgili tabloya karşı işaretlendi.

| Belge | Sürüm |
|---|---|
| ESP32-C3 Series Datasheet | v2.4 |
| ESP32-C3-WROOM-02 ve WROOM-02U Datasheet | v1.7 |
| BME280 Data sheet (Bosch Sensortec) | dosya revizyonu 1.24 (sayfa altbilgisi DS001-23 rev 1.23) |
| AP2112 (Diodes Inc.) | DS39724 Rev. 2-2, Haziran 2017 |
| GCT USB4105 Product Drawing | Rev B3 |

## Sonuçlar (5 kontrolün 5'i uyuşuyor)

### 1) Strapping pinleri ve açılış modu
- **Kaynak:** Çip datasheet Tablo 3-1 ve 3-3 (s.30-31); modül datasheet Tablo 4-3.
- **Datasheet:** SPI boot: GPIO2=1, GPIO8=herhangi, GPIO9=1. İndirme modu: GPIO2=1, **GPIO8=1**, GPIO9=0. Varsayılan durum: GPIO2 ve GPIO8 "floating", GPIO9 zayıf pull-up. GPIO2'nin glitch'lere karşı yukarı çekilmesi önerilir.
- **Kart:** IO2 → 10 kΩ → +3V3; IO8 → 10 kΩ → +3V3; IO9 → BOOT hattı (10 kΩ pull-up ve buton).
- **Referans tasarım:** Modül datasheet Şekil 9-1 (s.34): IO2 ve IO8 için 10 kΩ ile VDD33'e çekme, IO9 için "Boot Option" başlığı. Kart referansla aynı. Modülün kendi şematiğinde (Şekil 8-1) EN, IO2 ve IO8 için dahili direnç yok; dış pull-up gerekli.

### 2) ESP32-C3-WROOM-02 modülü
- **Kaynak:** Modül datasheet Tablo 3-1 (s.10-11), Tablo 6-2, 6-4, Şekil 9-1.
- **Pinler:** 1=3V3, 2=EN, 3=IO4 (SDA), 4=IO5 (SCL), 7=IO8, 8=IO9, 9 ve 19=GND, 11=RXD (IO20), 12=TXD (IO21), 13=IO18 (USB D−), 14=IO19 (USB D+), 16=IO2. Pin tablosuyla birebir aynı.
- **EN:** "EN pini floating bırakılmamalı"; önerilen RC 10 kΩ ve 1 µF (s.34 metni). Kartta 10 kΩ ve 1 µF. Aynı sayfadaki şekilde C4 = 0,1 µF yazıyor; metin ile şekil tutarsız, metne uyuldu.
- **Güç:** VDD33 3,0–3,6 V; harici kaynak en az 0,5 A (Tablo 6-2). Wi-Fi tepe akımı 345 mA (802.11b 1 Mbps @20,5 dBm, Tablo 6-4). 600 mA'lik regülatör yeterli.
- **Besleme kondansatörleri:** Referansta 10 µF ve 0,1 µF; kartta 10 µF ve 100 nF.
- **USB hatları:** Referans tasarımda D+ ve D− üzerinde 0 Ω seri direnç var; kartta seri direnç yok, USBLC6 koruması var. Datasheet ikisini de zorunlu kılmıyor.

### 3) BME280
- **Kaynak:** Bölüm 7, Tablo 35 (pin açıklaması), Şekil 17 (I2C bağlantısı), Şekil 21 (lehim deseni, s.43).
- **Pinler:** 1=GND, 2=CSB, 3=SDI, 4=SCK, 5=SDO, 6=VDDIO, 7=GND, 8=VDD. I2C için CSB→VDDIO, SDO→GND (adres 0x76), VDD ve VDDIO için ayrı 100 nF, pull-up için 4,7 kΩ. Kartlarla aynı.
- **Footprint:** Önerilen lehim deseni: pad 0,5 x 0,35 mm, aralık 0,65 mm, merkez ofseti 1,025 mm. KiCad footprint'i (Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering) aynı boyutlarda, 90° döndürülmüş ve pin 1 konumu doğru.

### 4) AP2112K-3.3 (SOT25)
- **Kaynak:** Sayfa 2 (Pin Descriptions ve Blok Şeması), Not 4, Mutlak Azami Değerler, Önerilen Çalışma Koşulları.
- **Pinler:** 1=VIN, 2=GND, 3=EN, 5=VOUT. Blok şemada (D = SOT25) aynı numaralar. 4. pin datasheet tablosunda tanımlı değil, bağlantısız bırakıldı.
- **Değerler:** Önerilen VIN 2,5–6,0 V, mutlak azami 6,5 V (USB 5 V için uygun). Tipik uygulama giriş ve çıkışta 1 µF; 1 µF seramikse X7R veya X5R (Not 4). θJA (SOT25) = 184 °C/W. EN yüksek eşiği 1,5 V (kartta EN, VIN'e bağlı).
- **Kondansatör:** Datasheet yalnızca 1 µF'ı örnekliyor, üst sınır vermiyor. Kartta 10 µF (X5R/X7R seçilmeli); bir tasarım tercihi, datasheet'le çelişmez.

### 5) USB-C alıcı (GCT USB4105)
- **Kaynak:** Product Drawing, sayfa 1, pin tablosu.
- **Pinler:** A1, A12, B1, B12 = GND; A4, A9, B4, B9 = VBUS; A5 = CC1; B5 = CC2; A6/B6 = D+; A7/B7 = D−; A8 = SBU1; B8 = SBU2; kabuk = GND. Karttaki bağlantılarla birebir aynı (SBU pinleri bağlantısız).
- **CC dirençleri:** Çizimde yok. USB Type-C kuralı: cihaz (sink) tarafında her CC pini ayrı ayrı 5,1 kΩ ile GND'ye bağlanır. Kartta iki ayrı 5,1 kΩ direnç.

## Denetimde bulunan ve düzeltilen hatalar
| Bulgu | Düzeltme |
|---|---|
| IO8 bağlantısız bırakılmıştı; indirme modu için GPIO8=1 şart, varsayılanı belirsiz (floating) | IO8'e 10 kΩ pull-up |
| IO2 bağlantısız; datasheet yukarı çekilmesini öneriyor | IO2'ye 10 kΩ pull-up |
| BME280 için tek 100 nF vardı; Bosch VDD ve VDDIO için ayrı ayrı gösteriyor | İkinci 100 nF eklendi |
| Modülün GPIO sayısı yanlış aktarılmıştı (22 yerine 15) | Düzeltildi |
| AP2112 SOT25 4. pini "NC" diye yazılmıştı; datasheet tanımlamıyor | Belgeler düzeltildi |
| Wi-Fi tepe akımı çip datasheet'inde 335 mA, modülde 345 mA | Modül değeri esas alındı |
| Anten kartın içinde kalmıştı; üretici anteni kart kenarından dışarı taşırmayı öneriyor | Modül kaydırıldı, anten kart dışında |

## Hesaplar
- **I2C kablo yükü:** Standart mod için yükselme süresi üst sınırı 1000 ns ve hat sığası üst sınırı 400 pF (I2C spesifikasyonundan bilgi; belge bu çalışmada açılmadı). 4,7 kΩ pull-up ile ~250 pF bütçe var. 40 cm kablo yaklaşık 20 pF, iki cihaz girişi birkaç on pF: bütçenin çok altında. Kablo 1 m'yi geçmemeli.
- **Regülatör ısınması:** SOT25 θJA = 184 °C/W, giriş-çıkış farkı 1,7 V. Ortalama 100 mA'de ~0,17 W, yaklaşık 31 °C yükselme; 345 mA tepe akım kısa süreli.
- **Kutu ve siper çakışması:** KiCad'in parçalı 3D kart modeli FreeCAD'de kutu ve siperle kesiştirildi: çakışma yok. Kontrolün doğruluğu, kartı bilerek duvara kaydırıp çakışmanın bulunmasıyla sınandı.

## Açıkta kalanlar ve bilinen sınırlar
- **USBLC6-2SC6:** ST datasheet'i bu denetimde kullanılmadı; pin sırası (1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1) ikincil kaynaktan.
- **USB4105 footprint ölçüleri:** Pin tablosu doğrulandı; ayak izi ölçüleri (kabuk delikleri, lehim alanları) çizimle sayısal karşılaştırılmadı.
- **USB Type-C 5,1 kΩ kuralı:** Birkaç ikincil kaynakla teyit edildi; USB-IF spesifikasyonunun kendisi açılmadı.
- **Anten yasak bölgesi:** Ölçü, footprint'in courtyard'ından alındı; Espressif donanım tasarım rehberinin ilgili bölümü ayrıca incelenmedi.
- **USB izleri:** Ana kartta modülün altından geçiyor; kritik hatlar için elle yönlendirme daha iyi olurdu.
- **Siper:** Yağmur koruması sınırlı (tavan ile en üst plaka arasında açık boşluk).
- **Kutu:** Vidalar modellenmedi; kapak sürtünmeli çıtayla oturur; anten çevresindeki plastiğin etkisi ölçülmedi.
