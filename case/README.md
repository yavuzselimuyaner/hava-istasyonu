# Kutu (FreeCAD, betikle üretildi)

Kart ölçüleri ve parça konumları doğrudan `pcb/v1/hava_routed.kicad_pcb` dosyasından okunur, ölçü elle yazılmadı.

## Çalıştırma
```
"C:\Program Files\KiCad\10.0\bin\python.exe" dump_board.py                       # karttan ölçüleri board_dims.json'a yazar
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" make_case.py                    # kutu altı + kapak (out/*.step, out/*.stl)
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export step --force --user-origin "100x100mm" -o out\board_with_parts.step ..\pcb\v1\hava_routed.kicad_pcb
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" check_fit.py                    # parçalı kart ile kutu çakışma kontrolü
python render_preview.py                                                           # kutu_kapali.png, kutu_acik.png, kutu_ustten.png
```

## Sonuç
- Dış ölçü: **55,3 x 68,6 x 18,0 mm** (kapak dahil). İç boşluk 51,3 x 64,6 x 14 mm.
- KiCad'in parçalı 3D modeli ile kutu arasında **çakışma hacmi 0** (taban ve kapak için ayrı ölçüldü). En yüksek parça (ekran header'ı) ile kapak arasında 0,87 mm boşluk var.
- Parçalar: 4 köşe destek direği (kart altı 3 mm), kapakta 4 bastırma direği, alt duvarda USB-C açıklığı, sağ duvarda BME280 için 3 havalandırma yuvası, kapakta 27x27 ekran penceresi, 3 buton deliği (Ø2,8 mm), 1 LED deliği.
- Kutunun üst kısmı, kartın dışına taşan ESP32 anteni için ~2 mm plastik boşlukla uzatıldı (metal yok).

## Varsayımlar ve sınırlar (dürüst liste)
- Ekran harici modül; kapağın altına yapıştırıldığı ve 27x27 mm pencerenin kartın ortasında (x=25, y=31) durduğu **varsayım**. Gerçek modül ölçüsü ve kablo yolu doğrulanmadı.
- Kartta **montaj deliği yok**. Kart, 4 köşe direği ve kapaktan basan direklerle sıkışarak tutuluyor. Bir sonraki kart revizyonunda montaj deliği eklemek daha sağlam olur.
- Buton delikleri kapaktan 9,4 mm aşağıdaki butonlara uzun bir çubukla dokunmak için; gerçek bir düğme kapağı tasarlanmadı.
- Çakışma kontrolü KiCad kütüphanesindeki 3D modellere dayanıyor; modeli olmayan parça varsa yüksekliği eksik olabilir.
- Anten çevresindeki plastik kalınlığının anten performansına etkisi ölçülmedi.
- Görüntüler kendi yazdığım basit bir işleyiciyle (z-buffer) üretildi; Blender klasörü kurulu ama `blender.exe` yok. Görüntü sadece önizleme, asıl kanıt sayısal çakışma kontrolü.
- 3D baskı, cıvata/vidalı kapak, snap-fit yok; kapak sürtünme ve direklerle oturur.
