"""hava_skidl.net -> hava.kicad_sch (sensor karti sematigi).
Sonra: kicad-cli sch erc + kicad-cli sch export netlist -> hava.net -> build_board.py"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import sch_gen

COLUMNS = [
    [("BME280 temperature / humidity / pressure sensor", [["U1", "C1", "C2"]])],
    [("Connector to main board", [["J1"]]),
     ("Mounting holes", [["H1", "H2"]])],
]

if __name__ == "__main__":
    sch_gen.build(os.path.join(HERE, "hava_skidl.net"), os.path.join(HERE, "hava.kicad_sch"),
                  "hava", "Weather station - sensor board (BME280)", COLUMNS,
                  flags=("+3V3", "GND"),
                  comments=("J1: 1=3V3  2=SDA  3=GND  4=SCL (same order as main board J2)",
                            "I2C address 0x76 (SDO=GND); pull-up resistors are on the main board",
                            "Source: gen_netlist.py (SKiDL) -> gen_schematic.py"))
    print("yazildi: hava.kicad_sch")
