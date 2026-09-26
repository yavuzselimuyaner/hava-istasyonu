# Denetim — sensör kartı, konnektör, kutu, DHT22 uyumu

Kapsam: bu tasarımda yeni olan parçalar (sensör kartı, 4 pinli konnektör, kutu ve siper). Ana kartın MCU/regülatör/USB kısımları önceki denetimlerde (docs/tasarim/02, 03) doğrulandı ve değişmedi.

## Doğrulananlar
| Konu | Sonuç | Kanıt |
|---|---|---|
| Sensör kartı devresi | BME280 pin bağlantısı (CSB→VDDIO = I2C, SDO→GND = 0x76) ve VDD/VDDIO için iki ayrı 100 nF Bosch şekil 17 ile birebir | Bosch BME280 datasheet rev 1.23 (yerel PDF okundu) |
| Pull-up yeri | Sensör kartında pull-up yok, ana kartta 4,7 kΩ (SDA ve SCL). Bosch da pull-up'ı bus tarafına bırakıyor ("normal değer 4.7 kΩ") | Aynı |
| Konnektör sırası | 1=3V3, 2=SDA, 3=GND, 4=SCL; ana kart ve sensör kartında aynı; netlist'te iki kartta da uyumlu (KiCad pad ağ adları kontrol edildi) | pcb/*/hava.net |
| DHT22 uyumu | DHT22 besleme 3,3–6 V (3,3 V uygun), örnekleme en az 2 sn, başlangıç sinyali ≥800 µs low, güç verdikten sonra 1 sn bekle, ~5 kΩ pull-up gerekir (bizim 4,7 kΩ SDA pull-up'ı bunu sağlıyor) | DHT22/AM2302 datasheet arama sonuçları (Adafruit, SparkFun, Waveshare, EDN) |
| Kart–kutu çakışması | Parçalı 3D kart modeli ile ana kutu ve siper arasında çakışma yok; Dupont fişi ve kablo yer tutucusu da temiz | case/check_fit.py çıktısı |
| Kontrolün güvenilirliği | Negatif kontrol: kart bilerek duvara 5,6 mm kaydırılınca 112,9 mm³ çakışma bulundu; ayrıca kutu 10 mm iken kapak çıtasının USB-C'ye 0,4 mm çarptığını (2,8 mm³) yakaladı, kutu 11 mm yapıldı | Aynı |

## I2C kablo yükü (hesap, bu oturumda kaynak açılmadı)
Standart mod I2C için yükselme süresi üst sınırı 1000 ns ve hat sığası üst sınırı 400 pF (NXP UM10204'ten bilgi, PDF açılmadı). 4,7 kΩ pull-up ile 1000 ns bütçesi ≈ 250 pF verir. Dupont kablo ~50 pF/m varsayımıyla 40 cm kablo yaklaşık 20 pF, iki cihaz girişi de birkaç on pF: bütçenin çok altında. Kablo 1 m'yi geçmemeli.

## Açık riskler ve sınırlar
- **DHT22 modül pin sırası standart değil.** Bazı modüller (+, OUT, −), bazıları (S, +, −) sıralı. Gerçek modülün serigrafisi kontrol edilmeli ve M-F jumper ile doğru pinlere bağlanmalı; konnektörün 1,2,3 sırası her modüle doğrudan uymayabilir.
- **DHT22 zamanlaması** yazılımla (bit-bang) okunur ve bu oturumda donanımda test edilemedi.
- **Siperin yağmur koruması sınırlı:** tavan ile en üst plaka arasında 12 mm açık boşluk var (havalandırma için). Yağmurlu rüzgârda sensöre su sıçrayabilir; gerçek dış mekân kullanımı için değerlendirilmeli.
- **Kablo demeti çıkışı:** siperin alt ortasından açık; su geçirmezlik yok.
- **Sensör kartı radyasyon siperi içinde 3D baskı gerektirir;** malzeme (UV dayanımı) seçimi yapılmadı.
- **Ana kutunun vida bağlantısı:** kart 2 M2 vida ile bağlanacak (vidalar modellenmedi), kapak sürtünmeli çıta ile oturur.
- Kutuda anten çevresinde ~2 mm plastik boşluk bırakıldı; plastiğin anten performansına etkisi ölçülmedi.
