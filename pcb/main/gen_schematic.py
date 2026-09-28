"""hava_skidl.net -> hava.kicad_sch (ana kart sematigi).
Sonra: kicad-cli sch erc + kicad-cli sch export netlist -> hava.net -> build_board.py"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import sch_gen

COLUMNS = [
    [("USB-C input and ESD protection", [["J1"], ["R1", "R2", "U4"]]),
     ("3.3 V regulator", [["U2", "C1", "C2"]])],
    [("ESP32-C3 module", [["U1", "C3", "C4"]]),
     ("Status LED", [["R7", "D1"]]),
     ("Mounting holes", [["H1", "H2"]])],
    [("Reset / Boot buttons and strapping resistors", [["R3", "C5", "SW1"], ["R4", "SW2"], ["R8", "R9"]]),
     ("Remote sensor connector and I2C pull-ups", [["J2", "R5", "R6"]])],
]

if __name__ == "__main__":
    sch_gen.build(os.path.join(HERE, "hava_skidl.net"), os.path.join(HERE, "hava.kicad_sch"),
                  "hava", "Weather station - main board (ESP32-C3)", COLUMNS,
                  flags=("+5V", "GND"),
                  comments=("J2: 1=3V3  2=SDA  3=GND  4=SCL (same order as the sensor board)",
                            "Source: gen_netlist.py (SKiDL) -> gen_schematic.py"))
    print("yazildi: hava.kicad_sch")
