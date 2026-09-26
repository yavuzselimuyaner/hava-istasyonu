# Gereksinim

Dışarıdaki bir sensörle sıcaklık, nem ve basıncı ölçen ve bu bilgiyi internete yayınlayan bir cihaz tasarla. Bilgi bir tarayıcı sayfasında görülebilmeli. Cihaz Wi-Fi ile bağlanacak, USB-C ile beslenecek. Sensör, cihazın ısınan parçalarından uzakta ve güneşten korunmuş olmalı: sensör ayrı küçük bir kartta, kabloyla bağlı olacak. Kartlar 2 katmanlı olacak. Çıktılar: KiCad kartları, kutu ve sensör koruması (radyasyon siperi), firmware ve basit bir web sayfası.

## Kısıtlar ve kararlar
- **Kablosuz bağlantı:** Wi-Fi (2,4 GHz). Anten performansı için hazır, sertifikalı bir modül kullanılır.
- **Güç:** USB-C, 5 V. Kart üzerinde 3,3 V'a indirilir.
- **Ölçüm:** Sıcaklık, bağıl nem, basınç; tek bir I2C sensörüyle.
- **Isıl ayrım:** İşlemci ve regülatör ısınır; sensör bu ısıdan ve doğrudan güneşten uzak durmalı. Bu yüzden sensör ana karttan ayrı, kabloyla bağlı bir kartta.
- **Haberleşme:** Ölçümler MQTT ile yayınlanır (WebSocket ve TLS üzerinden, 443 portu), tarayıcı sayfası aynı konuyu dinler.
- **Web sayfası:** Bilerek çok basit; tek dosya, sunucu ve veri tabanı yok.
- **Mekanik:** Kart kutuya vidayla sabitlenir (2 adet M2 montaj deliği); sensör kartı da kendi montaj deliklerine sahiptir.
