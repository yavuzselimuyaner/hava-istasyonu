import os
KI = r"C:\Program Files\KiCad\10.0\share\kicad"
for v in ("KICAD_SYMBOL_DIR", "KICAD9_SYMBOL_DIR", "KICAD10_SYMBOL_DIR"):
    os.environ[v] = KI + r"\symbols"
os.environ["KICAD_FOOTPRINT_DIR"] = KI + r"\footprints"

from skidl import *

R_FP = "Resistor_SMD:R_0402_1005Metric"
C_FP = "Capacitor_SMD:C_0402_1005Metric"
C10_FP = "Capacitor_SMD:C_0805_2012Metric"
SW_FP = "Button_Switch_SMD:SW_SPST_B3U-1000P"


def R(val):
    return Part("Device", "R", value=val, footprint=R_FP)


def C(val, fp=C_FP):
    return Part("Device", "C", value=val, footprint=fp)


gnd, v5, v3 = Net("GND"), Net("+5V"), Net("+3V3")
sda, scl = Net("I2C_SDA"), Net("I2C_SCL")
usb_dp, usb_dm = Net("USB_DP"), Net("USB_DM")
en, boot = Net("EN"), Net("BOOT")
lcd_sck, lcd_mosi, lcd_cs, lcd_dc, lcd_rst, lcd_bl = (
    Net(n) for n in ("LCD_SCK", "LCD_MOSI", "LCD_CS", "LCD_DC", "LCD_RST", "LCD_BL")
)
led_io, btn_io = Net("LED_IO"), Net("BTN_IO")
gnd.drive = POWER
v5.drive = POWER
v3.drive = POWER

# USB-C
j1 = Part("Connector", "USB_C_Receptacle_USB2.0_16P", ref="J1",
          footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal")
j1["VBUS"] += v5
j1["GND"] += gnd
j1["SHIELD"] += gnd
j1["D+"] += usb_dp
j1["D-"] += usb_dm
for cc in ("CC1", "CC2"):
    r = R("5.1k")
    j1[cc] += r[1]
    r[2] += gnd

# 3V3 regulator
u2 = Part("Regulator_Linear", "AP2112K-3.3", ref="U2", footprint="Package_TO_SOT_SMD:SOT-23-5")
u2["VIN"] += v5
u2["EN"] += v5
u2["VOUT"] += v3
u2["GND"] += gnd
for n in (v5, v3):
    c = C("10uF", C10_FP)
    c[1] += n
    c[2] += gnd

# MCU
u1 = Part("RF_Module", "ESP32-S3-WROOM-1", ref="U1",
          footprint="RF_Module:ESP32-S3-WROOM-1")
u1["3V3"] += v3
u1["GND"] += gnd
u1["EN"] += en
u1["IO0"] += boot
u1["USB_D+"] += usb_dp
u1["USB_D-"] += usb_dm
u1["IO8"] += sda
u1["IO9"] += scl
u1["IO11"] += lcd_mosi
u1["IO12"] += lcd_sck
u1["IO10"] += lcd_cs
u1["IO13"] += lcd_dc
u1["IO14"] += lcd_rst
u1["IO21"] += lcd_bl
u1["IO38"] += led_io
u1["IO4"] += btn_io
c = C("10uF", C10_FP); c[1] += v3; c[2] += gnd
c = C("100nF"); c[1] += v3; c[2] += gnd

# EN reset network and buttons
r = R("10k"); r[1] += v3; r[2] += en
c = C("1uF"); c[1] += en; c[2] += gnd
r = R("10k"); r[1] += v3; r[2] += boot
for sig in (en, boot, btn_io):
    sw = Part("Switch", "SW_Push", footprint=SW_FP)
    sw[1] += sig
    sw[2] += gnd

# BME280 (I2C, adres 0x76)
u3 = Part("Sensor", "BME280", ref="U3",
          footprint="Package_LGA:Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering")
u3["VDD"] += v3
u3["VDDIO"] += v3
u3["GND"] += gnd
u3["CSB"] += v3
u3["SDI"] += sda
u3["SCK"] += scl
u3["SDO"] += gnd
c = C("100nF"); c[1] += v3; c[2] += gnd
for sig in (sda, scl):
    r = R("4.7k"); r[1] += v3; r[2] += sig

# Ekran header
j2 = Part("Connector_Generic", "Conn_01x08", ref="J2",
          footprint="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical")
for pin, net in enumerate((gnd, v3, lcd_sck, lcd_mosi, lcd_rst, lcd_dc, lcd_cs, lcd_bl), 1):
    j2[pin] += net

# Durum LED
d1 = Part("Device", "LED", footprint="LED_SMD:LED_0603_1608Metric")
r = R("1k")
led_io += r[1]
r[2] += d1["A"]
d1["K"] += gnd

if __name__ == "__main__":
    ERC()
    generate_netlist(file_="hava.net")
