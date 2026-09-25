# v1 Adım 1 — Parça Seçimi (Agent: parça seçici)

Girdi: yalnızca 00-gereksinim.md. Kullanıcının elindeki donanım (T-Display, ESP32-S3) bilerek DİKKATE ALINMADI.
Kısıt notu: Ağ erişimi olmadan yazıldı; JLCPCB stok/fiyat ve datasheet değerleri DOĞRULANMADI. Bunlar denetçi adımının işidir (aşağıda işaretli).

## 1. MCU
| Aday | Artı | Eksi |
|---|---|---|
| ESP32-C3-WROOM-02 | Wi-Fi + BLE, sertifikalı anten modülü, tek çekirdek RISC-V yeterli, USB Serial/JTAG dahili (ek çip yok), ucuz, KiCad'de sembol+footprint var | 22 GPIO civarı; ihtiyaç için yeterli |
| ESP32-S3-WROOM-1 | Daha çok GPIO, daha güçlü | Bu iş için gereksiz, daha pahalı, daha yüksek akım |
| ESP32-S2-MINI-1 | Wi-Fi, USB OTG | BLE yok, C3'ten belirgin avantaj yok |
| RP2040 + ayrı Wi-Fi modülü | Ucuz MCU | İki çip, ek flash/kristal, karmaşıklık ve hata riski |

**Seçim: ESP32-C3-WROOM-02** (RF_Module:ESP32-C3-WROOM-02). Gerekçe: gereksinim yalnızca Wi-Fi, bir I2C sensörü ve bir SPI ekran; en az parçayla en düşük risk. Sertifikalı modül, anten tasarımı riskini kaldırır.
- Doğrulanacak: pin ataması (strapping GPIO2/8/9), USB pinleri GPIO18/19, tepe akım.

## 2. Sensör
| Aday | Not |
|---|---|
| BME280 | Sıcaklık+nem+basınç tek çipte, I2C, 2.5x2.5 mm LGA (elle lehimlenmez, montaj hizmetiyle olur) |
| SHT31/SHT4x + BMP280 | İki çip, daha iyi nem/sıcaklık doğruluğu, daha çok parça |
| AHT20 + BMP280 | Ucuz ama iki çip |

**Seçim: BME280** (Sensor:BME280). Gerekçe: gereksinim üç ölçümü istiyor, tek çip en az parça. Risk: kartın kendi ısısı sıcaklığı yükseltir, sensör ısı kaynaklarından uzağa ve kart kenarına konmalı; klon/sahte BME280 riski (BMP280 olarak çıkabilir).

## 3. Regülatör
| Aday | Not |
|---|---|
| AP2112K-3.3 | 600 mA, SOT-23-5, yaygın |
| ME6211C33M5 | 500 mA, çok yaygın ve ucuz |
| XC6220B331MR | 700 mA, daha pahalı |

**Seçim: AP2112K-3.3.** Gerekçe: Wi-Fi TX tepe akımı (~350 mA civarı C3 için) altında yeterli marj. Doğrulanacak: datasheet'te tepe akım ve dropout, çıkış kondansatörü gereksinimi.

## 4. USB-C
16 pinli USB 2.0 Type-C girişi (Connector:USB_C_Receptacle_USB2.0_16P), CC1/CC2 için 5.1 kΩ (5 V sink), D+/D− doğrudan C3'ün USB pinlerine. Ek ESD koruması (USBLC6-2SC6) eklenir.
- Doğrulanacak: JLCPCB'de montaj yapılan uygun bir 16P konnektör var mı, footprint uyumu.

## 5. Ekran (KARAR)
| Seçenek | Not |
|---|---|
| Harici 1.3" ST7789 SPI 240x240 modül, 8 pin header | Karta ekran flexi/FPC routing riski yok, modül ucuz ve yaygın |
| Karta doğrudan bağlı ekran (FPC) | Daha kompakt, ama FPC footprint ve sürücü riski yüksek |
| 0.96" OLED I2C | Sensörle aynı I2C hattı, az pin; ama küçük, hava verisi için yetersiz |

**Seçim: harici 1.3" ST7789 SPI modül, 8 pin header.** Gerekçe: yerleşim ve montaj riskini azaltır. Bu karar gereksinimde açık bırakıldığı için agent'a aittir.

## 6. Yardımcı parçalar
- Reset (EN) ve BOOT (GPIO9) butonları, 10 kΩ pull-up'lar, EN için 1 µF.
- I2C pull-up 4.7 kΩ ×2.
- Bypass kondansatörleri (MCU, sensör, regülatör giriş/çıkış).
- Durum LED'i + direnç.

## Denetçiye devredilen kontrol listesi
- [ ] ESP32-C3-WROOM-02 datasheet: pin isimleri, strapping, EN devresi, USB pinleri, anten keepout
- [ ] BME280 datasheet: adres seçimi (SDO), CSB pinini I2C modu için bağlama, güç/decoupling
- [ ] AP2112K datasheet: çıkış C değeri, EN kullanımı
- [ ] JLCPCB: parçaların montaj kataloğunda olup olmadığı, temel/genişletilmiş parça durumu
