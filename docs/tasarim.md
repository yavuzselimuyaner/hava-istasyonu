# Hava İstasyonu — Tasarım Özeti (v0.1, taslak)

Amaç: İnternetten hava durumunu çekip ekranda gösteren, yerel sıcaklık/nem/basınç da ölçen ESP32-S3 kartı.
Durum: Şematik yok. Bu belge şematiğin kaynağıdır; her parça datasheet'ten doğrulanmadan kilitlenmez.

## Blok şeması
USB-C (5 V + veri) -> LDO 3V3 -> ESP32-S3-WROOM-1 -> I2C: BME280
                                               -> SPI: ekran modülü (harici, 8 pin header)
                                               -> LED, 2 buton

## Parçalar (KiCad kütüphane adları doğrulandı)
| Ref | Parça | Sembol | Footprint |
|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N8 (PSRAM'siz) | RF_Module:ESP32-S3-WROOM-1 | RF_Module:ESP32-S3-WROOM-1 |
| U2 | AP2112K-3.3 (600 mA LDO) | Regulator_Linear:AP2112K-3.3 | Package_TO_SOT_SMD:SOT-23-5 |
| U3 | BME280 | Sensor:BME280 | Package_LGA:Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering |
| J1 | USB-C GCT USB4105 | Connector:USB_C_Receptacle_GCT_USB4105-xx-A | Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal |
| J2 | Ekran header 1x8 | Connector_Generic | 2.54 mm |
| R1,R2 | 5.1 k (USB-C CC) | | 0402 |
| R3,R4 | 4.7 k (I2C pull-up) | | 0402 |
| R5 | 10 k (EN pull-up) | | 0402 |
| C1..C5 | 10 uF (LDO giriş/çıkış, ESP 3V3), 100 nF (ESP, BME), 1 uF (EN) | | 0402/0603 |
| SW1,SW2 | RESET (EN), BOOT (IO0) | | SMD buton |
| D1 + R6 | Durum LED + 1 k | | 0603 |

## Pin ataması (ESP32-S3-WROOM-1 pin no)
| Sinyal | GPIO | Modül pini | Not |
|---|---|---|---|
| USB D- / D+ | 19 / 20 | 13 / 14 | Yerel USB; programlama + seri log |
| I2C SDA / SCL | IO8 / IO9 | 12 / 17 | BME280, adres 0x76 (SDO -> GND) |
| SPI MOSI / SCLK | IO11 / IO12 | 19 / 20 | Ekran |
| Ekran CS / DC / RST / BL | IO10 / IO13 / IO14 / IO21 | 18 / 21 / 22 / 23 | |
| BOOT | IO0 | 27 | 10 k pull-up + buton (strapping) |
| Kullanıcı butonu | IO4 | 4 | |
| LED | IO38 | 31 | |
| EN | EN | 3 | 10 k pull-up + 1 uF + buton |

Kaçınılacak: IO3, IO45, IO46 (strapping), IO26-IO32 (flash, modülde bağlı değil ama ayrılmış), N16R8 seçilirse IO35-IO37.

## Bilinen riskler / kontrol listesi
- [ ] AP2112K 600 mA sınırı Wi-Fi TX tepe akımında (~500 mA) marjinal; C çıkış >= 10 uF. Gerekirse daha güçlü LDO.
- [ ] BME280'i ESP modülünden ve LDO'dan uzağa koy, aralarına freze yuvası aç (kendi ısınması sıcaklığı yükseltir).
- [ ] Anten bölgesinin altında bakır ve parça yok; modülü kart kenarına koy.
- [ ] USB D+/D- 90 ohm diferansiyel, kısa; USB ESD koruması (USBLC6-2SC6) opsiyonel ekle.
- [ ] Tüm pin numaraları datasheet ile çapraz kontrol edilecek (LLM'e güvenme).
- [ ] Pil/şarj v0.1 kapsamında yok.

## Yöntem
1. `pcb/gen_netlist.py` (SKiDL) -> netlist
2. `pcb/build_board.py` (pcbnew) -> kart, footprint yerleşimi
3. `kicad-cli sch erc` / `pcb drc` ile otomatik denetim
4. Gerber + BOM/CPL çıkışı (JLCPCB)
