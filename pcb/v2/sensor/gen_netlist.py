"""v2 sensor karti: BME280 + 2x100nF + 4 pinli konnektor + 2 montaj deligi.
Konnektor sirasi ana kartla ayni: 1=3V3, 2=SDA, 3=GND, 4=SCL. I2C pull-up'lari ana kartta."""
import os
KI = r"C:\Program Files\KiCad\10.0\share\kicad"
for v in ("KICAD_SYMBOL_DIR", "KICAD9_SYMBOL_DIR", "KICAD10_SYMBOL_DIR"):
    os.environ[v] = KI + r"\symbols"
os.environ["KICAD_FOOTPRINT_DIR"] = KI + r"\footprints"
from skidl import *

gnd, v3, sda, scl = Net("GND"), Net("+3V3"), Net("I2C_SDA"), Net("I2C_SCL")
gnd.drive = POWER; v3.drive = POWER

u1 = Part("Sensor", "BME280", ref="U1", tag="U1",
          footprint="Package_LGA:Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering")
u1["VDD"] += v3; u1["VDDIO"] += v3; u1["GND"] += gnd; u1["CSB"] += v3
u1["SDI"] += sda; u1["SCK"] += scl; u1["SDO"] += gnd
for ref in ("C1", "C2"):     # Bosch: VDD ve VDDIO icin ayri 100 nF
    c = Part("Device", "C", ref=ref, value="100nF", footprint="Capacitor_SMD:C_0402_1005Metric", tag=ref)
    c[1] += v3; c[2] += gnd
j1 = Part("Connector_Generic", "Conn_01x04", ref="J1", tag="J1",
          footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
j1[1] += v3; j1[2] += sda; j1[3] += gnd; j1[4] += scl
for ref in ("H1", "H2"):
    Part("Mechanical", "MountingHole", ref=ref, tag=ref, footprint="MountingHole:MountingHole_2.2mm_M2")

if __name__ == "__main__":
    ERC()
    generate_netlist(file_="hava.net")
