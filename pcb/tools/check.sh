#!/bin/sh
# Kullanım: tools/check.sh <kart klasörü>  — şematik üret, ERC, netlist karşılaştır, PDF çıkar
set -e
K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
cd "$1"
../.venv/Scripts/python.exe gen_schematic.py
"$K" sch erc -o erc.rpt --severity-error --exit-code-violations hava.kicad_sch >/dev/null || { cat erc.rpt; exit 1; }
"$K" sch erc -o erc.rpt hava.kicad_sch >/dev/null      # rapor uyarıları da içersin
grep "ERC messages" erc.rpt; grep -A3 "^\[" erc.rpt || true
"$K" sch export netlist -o hava.net hava.kicad_sch >/dev/null
../.venv/Scripts/python.exe ../tools/net_compare.py hava_skidl.net hava.net
"$K" sch export pdf -o hava_sematik.pdf hava.kicad_sch >/dev/null
