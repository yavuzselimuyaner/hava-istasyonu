idf_component_register(SRCS "main.c" "bme280.c" "bme280_comp.c" "dht22.c" "dht22_comp.c" "display.c" INCLUDE_DIRS "."
    PRIV_REQUIRES esp_wifi esp_event esp_netif nvs_flash mqtt esp-tls mbedtls
                  esp_driver_i2c esp_driver_gpio esp_timer esp_lcd)
