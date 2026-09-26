"""Kutu ve siper gorselleri (basit z-buffer isleyici: render_preview.py). Calistir: python render_gorseller.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
import render_preview as rp
rp.OUT = os.path.join(HERE, "out"); rp.HERE = HERE
GRAY, LIDC, BRD = (215, 215, 220), (95, 115, 150), (30, 130, 70)
rp.render([("main_base", GRAY, 0), ("main_with_parts", BRD, 0), ("main_lid", LIDC, 0)], "ana_kutu_kapali.png", az=30, el=35)
rp.render([("main_base", GRAY, 0), ("main_with_parts", BRD, 0), ("main_lid", LIDC, 22)], "ana_kutu_acik.png", az=30, el=40)
rp.render([("shield", GRAY, 0)], "siper_dis.png", az=25, el=22, size=(1000, 1100))
rp.render([("shield_section", GRAY, 0), ("sensor_with_parts", BRD, 0)], "siper_kesit.png", az=180, el=12, size=(1000, 1100))
