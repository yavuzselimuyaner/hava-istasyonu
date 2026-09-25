"""v1 netlist: docs/v1/01-parca-secimi.md + 02-denetim.md pin planı. Çalıştır: ..\\.venv\\Scripts\\python.exe gen_netlist.py"""
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


def R(ref, val):
    return Part("Device", "R", ref=ref, value=val, footprint=R_FP, tag=ref)


def C(ref, val, fp=C_FP):
    return Part("Device", "C", ref=ref, value=val, footprint=fp, tag=ref)


gnd, v5, v3 = Net("GND"), Net("+5V"), Net("+3V3")
sda, scl = Net("I2C_SDA"), Net("I2C_SCL")
usb_dp, usb_dm = Net("USB_DP"), Net("USB_DM")
en, boot = Net("EN"), Net("BOOT")
lcd = {n: Net("LCD_" + n) for n in ("SCK", "MOSI", "CS", "DC", "RST", "BL")}
led_io, btn_io = Net("LED_IO"), Net("BTN_IO")
for n in (gnd, v5, v3):
    n.drive = POWER

# USB-C
j1 = Part("Connector", "USB_C_Receptacle_USB2.0_16P", ref="J1", tag="J1",
          footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal")
j1["VBUS"] += v5
j1["GND"] += gnd
j1["SHIELD"] += gnd
j1["D+"] += usb_dp
j1["D-"] += usb_dm
for i, cc in enumerate(("CC1", "CC2"), 1):
    r = R("R%d" % i, "5.1k")
    j1[cc] += r[1]
    r[2] += gnd

# USB ESD koruması (USBLC6-2SC6: 1,6=I/O1  3,4=I/O2  2=GND  5=VBUS)
u4 = Part("Power_Protection", "USBLC6-2SC6", ref="U4", tag="U4",
          footprint="Package_TO_SOT_SMD:SOT-23-6")
u4[1] += usb_dp
u4[6] += usb_dp
u4[3] += usb_dm
u4[4] += usb_dm
u4[2] += gnd
u4[5] += v5

# 3V3 regülatörü
u2 = Part("Regulator_Linear", "AP2112K-3.3", ref="U2", tag="U2",
          footprint="Package_TO_SOT_SMD:SOT-23-5")
u2["VIN"] += v5
u2["EN"] += v5
u2["VOUT"] += v3
u2["GND"] += gnd
for ref, n in (("C1", v5), ("C2", v3)):
    c = C(ref, "10uF", C10_FP)
    c[1] += n
    c[2] += gnd

# MCU: ESP32-C3-WROOM-02 (pin numaralarıyla)
u1 = Part("RF_Module", "ESP32-C3-WROOM-02", ref="U1", tag="U1",
          footprint="RF_Module:ESP32-C3-WROOM-02")
u1[1] += v3
u1[2] += en
u1[9] += gnd
u1[19] += gnd
u1[8] += boot          # IO9
u1[13] += usb_dm       # IO18
u1[14] += usb_dp       # IO19
u1[3] += sda           # IO4
u1[4] += scl           # IO5
u1[5] += lcd["SCK"]    # IO6
u1[6] += lcd["MOSI"]   # IO7
u1[10] += lcd["DC"]    # IO10
u1[15] += lcd["CS"]    # IO3
u1[17] += lcd["RST"]   # IO1
u1[18] += lcd["BL"]    # IO0
u1[11] += led_io       # IO20
u1[12] += btn_io       # IO21
c = C("C3", "10uF", C10_FP); c[1] += v3; c[2] += gnd
c = C("C4", "100nF"); c[1] += v3; c[2] += gnd

# EN devresi (10k + 1uF), BOOT pull-up, butonlar
r = R("R3", "10k"); r[1] += v3; r[2] += en
c = C("C5", "1uF"); c[1] += en; c[2] += gnd
r = R("R4", "10k"); r[1] += v3; r[2] += boot
for i, sig in enumerate((en, boot, btn_io), 1):
    sw = Part("Switch", "SW_Push", ref="SW%d" % i, tag="SW%d" % i, footprint=SW_FP)
    sw[1] += sig
    sw[2] += gnd

# BME280 (I2C 0x76)
u3 = Part("Sensor", "BME280", ref="U3", tag="U3",
          footprint="Package_LGA:Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering")
u3["VDD"] += v3
u3["VDDIO"] += v3
u3["GND"] += gnd
u3["CSB"] += v3
u3["SDI"] += sda
u3["SCK"] += scl
u3["SDO"] += gnd
c = C("C6", "100nF"); c[1] += v3; c[2] += gnd
for ref, sig in (("R5", sda), ("R6", scl)):
    r = R(ref, "4.7k"); r[1] += v3; r[2] += sig

# Harici ekran header'ı (ST7789 SPI modül)
j2 = Part("Connector_Generic", "Conn_01x08", ref="J2", tag="J2",
          footprint="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical")
for pin, net in enumerate((gnd, v3, lcd["SCK"], lcd["MOSI"], lcd["RST"], lcd["DC"], lcd["CS"], lcd["BL"]), 1):
    j2[pin] += net

# Durum LED
d1 = Part("Device", "LED", ref="D1", tag="D1", footprint="LED_SMD:LED_0603_1608Metric")
r = R("R7", "1k")
led_io += r[1]
r[2] += d1["A"]
d1["K"] += gnd

if __name__ == "__main__":
    ERC()
    generate_netlist(file_="hava.net")
