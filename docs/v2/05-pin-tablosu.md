# v2 pin tablosu (karttan otomatik üretildi)

Bu tablo `pcb/v2/*/hava.net` dosyasından üretildi (`docs/v2/05-pin-tablosu.md`). Datasheet'teki pin tablosuyla yan yana koyup **kendi gözünle** karşılaştır: pin numarası, ad ve bağlı olduğu net uyuşuyor mu?
Net adları: `+3V3`, `+5V`, `GND` güç hatları; `I2C_SDA/SCL` sensör; `USB_DP/DM` USB; `EN`, `BOOT` reset ve boot.

## Ana kart

### U1 — ESP32-C3-WROOM-02 (karşılaştır: modül datasheet'i pin tablosu; çip datasheet'i Tablo 3-3 boot)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| 1 | 3V3 | +3V3 |
| 2 | EN | EN |
| 3 | IO4 | I2C_SDA |
| 4 | IO5 | I2C_SCL |
| 7 | IO8 | N$4 |
| 8 | IO9 | BOOT |
| 9 | GND | GND |
| 11 | IO20/RXD | LED_IO |
| 13 | IO18 | USB_DM |
| 14 | IO19 | USB_DP |
| 16 | IO2 | N$3 |
| 19 | GND | GND |

Strapping kontrolü: **IO2 (pin 16)** ve **IO8 (pin 7)** birer 10 kΩ ile +3V3'e, **IO9 (pin 8)** BOOT hattına (10 kΩ pull-up + buton) bağlı olmalı. Tablodaki `N$3` (IO2) ve `N$4` (IO8) otomatik adlı netlerdir: R8 ve R9 dirençlerinin diğer ucudur, aşağıdaki direnç tablosunda R8/R9 satırlarında pin 1 = +3V3 görmelisin.

### U2 — AP2112K-3.3 (karşılaştır: AP2112 datasheet 'Pin Descriptions', SOT25)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| 1 | VIN | +5V |
| 2 | GND | GND |
| 3 | EN | +5V |
| 5 | VOUT | +3V3 |

### U4 — USBLC6-2SC6 (USB koruması)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| 1 | I/O1 | USB_DP |
| 2 | GND | GND |
| 3 | I/O2 | USB_DM |
| 4 | I/O2 | USB_DM |
| 5 | VBUS | +5V |
| 6 | I/O1 | USB_DP |

### J2 — sensör konnektörü (4 pin)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| 1 | 1 | +3V3 |
| 2 | 2 | I2C_SDA |
| 3 | 3 | GND |
| 4 | 4 | I2C_SCL |

### J1 — USB-C (CC1/CC2 pinleri her biri 5,1 kΩ ile GND'ye bağlı olmalı)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| A1 |  | GND |
| A12 |  | GND |
| A4 |  | +5V |
| A5 |  | N$1 |
| A6 |  | USB_DP |
| A7 |  | USB_DM |
| A9 |  | +5V |
| B1 |  | GND |
| B12 |  | GND |
| B4 |  | +5V |
| B5 |  | N$2 |
| B6 |  | USB_DP |
| B7 |  | USB_DM |
| B9 |  | +5V |
| SH |  | GND |

### Dirençler ve kondansatörler (değer → bağlı net çiftleri)

| Ref | Değer | Pin 1 | Pin 2 |
|---|---|---|---|
| C1 | 10uF | +5V | GND |
| C2 | 10uF | +3V3 | GND |
| C3 | 10uF | +3V3 | GND |
| C4 | 100nF | +3V3 | GND |
| C5 | 1uF | EN | GND |
| R1 | 5.1k | N$1 | GND |
| R2 | 5.1k | N$2 | GND |
| R3 | 10k | +3V3 | EN |
| R4 | 10k | +3V3 | BOOT |
| R5 | 4.7k | +3V3 | I2C_SDA |
| R6 | 4.7k | +3V3 | I2C_SCL |
| R7 | 1k | LED_IO | N$5 |
| R8 | 10k | +3V3 | N$3 |
| R9 | 10k | +3V3 | N$4 |

## Sensör kartı

### U1 — BME280 (karşılaştır: Bosch datasheet Bölüm 7, Tablo 35 ve Şekil 17)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| 1 | GND | GND |
| 2 | CSB | +3V3 |
| 3 | SDI | I2C_SDA |
| 4 | SCK | I2C_SCL |
| 5 | SDO | GND |
| 6 | VDDIO | +3V3 |
| 7 | GND | GND |
| 8 | VDD | +3V3 |

Beklenen (I2C): **CSB → +3V3**, **SDO → GND** (adres 0x76), VDD ve VDDIO ikisi de +3V3, iki pin GND.

### J1 — sensör konnektörü (ana kartın J2'si ile aynı sırada olmalı)

| Pin | Adı (sembol) | Bağlı olduğu net |
|---|---|---|
| 1 | 1 | +3V3 |
| 2 | 2 | I2C_SDA |
| 3 | 3 | GND |
| 4 | 4 | I2C_SCL |

### Kondansatörler

| Ref | Değer | Pin 1 | Pin 2 |
|---|---|---|---|
| C1 | 100nF | +3V3 | GND |
| C2 | 100nF | +3V3 | GND |
