"""ESP32 OLMADAN calisan PC demosu.
 - Dis hava: Open-Meteo'dan GERCEK veri (firmware ile ayni istek).
 - Oda: BME280 yerine datasheet ornek ham verisi (--sim ile degistirilebilir).
 - Ekran ve sensor hesabi: firmware'in gercek C kodu (host_demo.c).
Kullanim:  python pc_demo.py            (tek sefer)      python pc_demo.py --loop 60   (60 sn'de bir yenile)"""
import argparse, json, os, subprocess, sys, time, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "host_demo.exe")

def build():
    subprocess.run(["gcc", "-Wall", "-DHOST_TEST", "-I../main", "-o", EXE, "host_demo.c"], cwd=HERE, check=True)

def fetch(lat, lon):
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
           "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code" % (lat, lon))
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)["current"]

def once(a):
    have_out = 1
    try:
        w = fetch(a.lat, a.lon)
        t, h, wind, code = w["temperature_2m"], w["relative_humidity_2m"], w["wind_speed_10m"], w["weather_code"]
    except Exception as e:
        print("Open-Meteo alinamadi:", e); have_out, t, h, wind, code = 0, 0, 0, 0, -1
    raw_p, raw_t, raw_h = a.sim
    ppm = os.path.join(HERE, "screen.ppm")
    r = subprocess.run([EXE, str(t), str(h), str(wind), str(have_out), str(raw_p), str(raw_t), str(raw_h), "1", ppm],
                       capture_output=True, text=True, check=True)
    Image.open(ppm).save(os.path.join(HERE, "screen.png"))
    print("DISARI (Open-Meteo, gercek): %.1f C  %%%d nem  %.1f km/h  kod %s" % (t, h, wind, code))
    print(r.stdout.strip()); print("ekran goruntusu: firmware/pc_demo/screen.png")

ap = argparse.ArgumentParser()
ap.add_argument("--lat", default="41.2867"); ap.add_argument("--lon", default="36.33")
ap.add_argument("--sim", nargs=3, type=int, default=[415148, 519888, 30000], metavar=("RAW_P", "RAW_T", "RAW_H"),
                help="benzetilmis BME280 ham degerleri (varsayilan: Bosch datasheet ornegi)")
ap.add_argument("--loop", type=int, default=0, help="saniye; 0 = tek sefer")
a = ap.parse_args()
build()
while True:
    once(a)
    if not a.loop: break
    time.sleep(a.loop)
