# Parça seçimi

Her parça için seçilen ve elenen alternatifler ve gerekçe. Datasheet doğrulaması `02-datasheet-denetimi.md` içinde.

## İşlemci (MCU)
| Aday | Değerlendirme |
|---|---|
| **ESP32-C3-WROOM-02** | Seçildi. Wi-Fi ve BLE içinde, sertifikalı PCB anten modülü, USB Serial/JTAG dahili (ek çip gerekmez), ucuz, KiCad'de sembol ve footprint hazır. Modülde 15 GPIO pini var, bu iş için yeterli. |
| ESP32-S3-WROOM-1 | Bu iş için gereksiz güçlü, daha pahalı ve daha yüksek akımlı. |
| ESP32-S2-MINI-1 | Wi-Fi var, BLE yok, C3'e göre belirgin bir avantajı yok. |
| RP2040 + ayrı Wi-Fi modülü | İki çip, ek flash ve kristal gerekir; karmaşıklık ve hata riski artar. |

Çıplak çip yerine hazır modül seçildi: anten, kristal ve flash zaten entegre ve sertifikalı; RF tasarımı yeniden yapılmıyor.

## Sensör
| Aday | Değerlendirme |
|---|---|
| **BME280** | Seçildi. Sıcaklık, nem ve basınç tek çipte, I2C, 2,5 x 2,5 mm LGA. |
| SHT31 / SHT4x + BMP280 | Nem ve sıcaklık doğruluğu daha iyi olabilir ama iki çip gerekir. |
| AHT20 + BMP280 | İki çip. |
| DHT22 | Basınç yok, tek tel protokol; firmware'de alternatif sensör olarak desteklenir. |

BME280'in kendi ısınması ölçümü etkileyebilir; bu yüzden ısı kaynaklarından uzak, ayrı bir kartta.

## Regülatör
| Aday | Değerlendirme |
|---|---|
| **AP2112K-3.3** | Seçildi. 600 mA, SOT-23-5, yaygın. Modülün en yüksek Wi-Fi akımı ~345 mA, önerilen harici kaynak akımı 0,5 A: yeterli. |
| ME6211C33M5 | 500 mA; marj daha dar. |
| XC6220B331MR | 700 mA; daha pahalı. |

## USB
- **USB-C alıcı (GCT USB4105, 16 pin, USB 2.0):** Güç ve programlama/log.
- **CC1 ve CC2:** Her biri ayrı ayrı 5,1 kΩ ile GND'ye (cihaz tarafı, 5 V).
- **USBLC6-2SC6:** USB veri hatlarını ve VBUS'ı ESD'ye karşı korur.

## Diğer parçalar
- **EN devresi:** 10 kΩ pull-up ve 1 µF (üretici önerisi), reset butonu.
- **Boot:** IO9 için buton ve 10 kΩ pull-up.
- **Strapping pull-up'ları:** IO2 ve IO8 için 10 kΩ (açılış modunu belirleyen pinler).
- **I2C pull-up'ları:** SDA ve SCL için 4,7 kΩ.
- **Kondansatörler:** 3V3 hattında 10 µF ve 100 nF; regülatörde giriş ve çıkışta 10 µF; BME280 için iki adet 100 nF (VDD ve VDDIO).
- **Durum LED'i** ve 1 kΩ direnç.
- **Sensör konnektörü:** 1x4, 2,54 mm, dik açılı (kablo yandan çıksın, kutu alçak kalsın). Pin sırası: 1=3V3, 2=SDA/DATA, 3=GND, 4=SCL; ilk üç pin yaygın 3 telli sensör modüllerinin (VCC, DATA, GND) sırasına denk gelir.
- **Montaj delikleri:** Her kartta 2 adet M2.

## Sensör kartı
BME280, 2 x 100 nF, aynı 4 pinli konnektör ve 2 montaj deliği. I2C pull-up dirençleri ana kartta.
